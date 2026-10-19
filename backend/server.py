"""Single-process loopback app; no public deployment or secret entry through UI."""
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import argparse
import json
import secrets
from workflow import Workflow

ROOT = Path(__file__).resolve().parent


def make_server(port=8766, workflow=None):
    app = workflow or Workflow()
    token = secrets.token_urlsafe(32)

    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(10)

        def log_message(self, *args):
            pass  # Do not log public taste queries or local session capabilities.

        def reply(self, status, body, content_type='application/json'):
            if not isinstance(body, bytes):
                body = json.dumps(body, allow_nan=False).encode()
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('Content-Security-Policy', "default-src 'self'; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def safe_host(self):
            return self.headers.get('Host') in {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}

        def do_GET(self):
            if not self.safe_host():
                return self.reply(403, {'error':'host_rejected'})
            if self.path == '/':
                return self.reply(200,(ROOT/'index.html').read_bytes(),'text/html; charset=utf-8')
            if self.path == '/app.js':
                return self.reply(200,(ROOT/'app.js').read_bytes(),'text/javascript; charset=utf-8')
            if self.path == '/api/status':
                return self.reply(200, {'csrf':token, 'version':'0.2.2', **app.availability()})
            return self.reply(404, {'error':'not_found'})

        def do_POST(self):
            allowed = {f'http://127.0.0.1:{self.server.server_port}', f'http://localhost:{self.server.server_port}'}
            if not self.safe_host() or self.headers.get('Origin', '') not in allowed | {''} or not secrets.compare_digest(self.headers.get('X-TasteBridge-Token', ''), token):
                return self.reply(403, {'error':'origin_or_token_rejected'})
            if self.path != '/api/tool':
                return self.reply(404, {'error':'not_found'})
            try:
                n = int(self.headers.get('Content-Length', '0'))
                if not 0 < n <= 16000 or self.headers.get('Content-Type','').split(';')[0] != 'application/json':
                    return self.reply(413, {'error':'invalid_body_limit_or_type'})
                data = json.loads(self.rfile.read(n))
                if not isinstance(data, dict) or set(data) != {'action', 'arguments'}:
                    raise ValueError('Use action and arguments')
                result = app.call(data['action'], data['arguments'])
                return self.reply(200, result)
            except (ValueError, TypeError, KeyError, OverflowError):
                return self.reply(400, {'error':'invalid_request_or_stale_revision', 'hint':'Reload session and check the required input fields.'})

    server = HTTPServer(('127.0.0.1', port), Handler)
    server.timeout = 20
    return server


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8766)
    args=parser.parse_args()
    server=make_server(args.port)
    print(f'TasteBridge 0.2.2 local app: http://127.0.0.1:{server.server_port}', flush=True)
    server.serve_forever()
