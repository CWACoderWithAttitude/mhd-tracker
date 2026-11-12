from http.server import BaseHTTPRequestHandler, HTTPServer
class H(BaseHTTPRequestHandler):
    def do_POST(self):
        a = self.headers.get('Authorization')
        print(self.path, '| auth present:', a is not None, '| len:', len(a or ''), flush=True)
        self.send_response(500); self.end_headers()
    do_GET = do_POST
HTTPServer(('127.0.0.1', 9999), H).serve_forever()
