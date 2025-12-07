# Minimal human-review API using Python standard library http.server
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from src import db

HOST = '127.0.0.1'
PORT = 8081

class Handler(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(obj).encode('utf-8'))

    def do_GET(self):
        p = urlparse(self.path)
        if p.path == '/human-review/pending':
            conn = db.init_db()
            items = db.list_pending(conn)
            resp = {'items': items}
            self._send(200, resp)
            return
        self._send(404, {'error': 'not found'})

    def do_POST(self):
        p = urlparse(self.path)
        if p.path == '/human-review/decision':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            payload = json.loads(body.decode('utf-8'))
            checkpoint_id = payload.get('checkpoint_id')
            decision = payload.get('decision')
            reviewer_id = payload.get('reviewer_id', 'api_user')
            conn = db.init_db()
            db.save_decision(conn, checkpoint_id, reviewer_id, decision)
            db.mark_completed(conn, checkpoint_id)
            resp = {'resume_token': checkpoint_id, 'next_stage': 'RECONCILE'}
            self._send(200, resp)
            return
        self._send(404, {'error': 'not found'})


def run_server():
    print(f'Listening on http://{HOST}:{PORT}')
    server = HTTPServer((HOST, PORT), Handler)
    server.serve_forever()

if __name__ == '__main__':
    run_server()
