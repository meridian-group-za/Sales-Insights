#!/usr/bin/env python3
"""Local dev API server for the Sales Insights dashboard.

Static mock-data/*.json dumps were exported once with no filters applied,
so changing a filter in the dashboard had zero effect on the data shown --
that's the bug Carin flagged ("THE FILTERS ARE NOT WIRED UP"). This server
calls sales_queries.dispatch_path() live against sales.duckdb for every
request, passing through whatever query-string params the dashboard sends
(client/month/category/brand/region/product/dimension/etc), so filters
actually filter. Same functions the real Azure Function route will call --
nothing here is reimplemented, just exposed over local HTTP with CORS so
index.html (served by a separate http.server) can call it directly.

Run: python local_api_server.py [port]   (defaults to 8792)
"""
import json
import sys
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

import duckdb

sys.path.insert(0, str(Path.home() / 'Downloads' / 'Workflow automation portal (2)' / 'backend' / 'azure-function'))
import sales_queries as sq

DB_PATH = Path.home() / 'OneDrive - Meridian Group' / 'Meridian Nexus - Documents' / 'Sales Insights' / 'data' / 'sales.duckdb'
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8792

import threading
_LOCK = threading.Lock()
_CON = duckdb.connect(str(DB_PATH), read_only=True)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _send(self, status, payload):
        body = json.dumps(payload, default=str).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.lstrip('/')
        if path.startswith('api/'):
            path = path[len('api/'):]
        params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
        # One shared connection behind a lock, not a fresh connect() per
        # request: loadCore() fires ~21 requests in parallel and opening
        # that many concurrent DuckDB handles on the same file failed,
        # which surfaced in the browser as "local api 500 on summary" and
        # took the whole page's data down (loadCore has no per-route
        # fallback). Serialising is fine for a single-developer dev server.
        try:
            with _LOCK:
                result = sq.dispatch_path(_CON, path, None, params)
        except Exception as exc:
            import traceback; traceback.print_exc()
            self._send(500, {'error': str(exc)})
            return
        if result is None:
            self._send(404, {'error': f'unknown route: {path}'})
            return
        self._send(200, result)


def main():
    server = ThreadingHTTPServer(('127.0.0.1', PORT), Handler)
    print(f'Local Sales Insights API on http://127.0.0.1:{PORT}/api/<route>?client=&month=&category=&brand=&region=&product=')
    server.serve_forever()


if __name__ == '__main__':
    main()
