#!/usr/bin/env python3
"""Serve this directory locally: python3 serve.py [port]"""
import http.server
import socketserver
import sys
import webbrowser
from pathlib import Path

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8420

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(Path(__file__).parent), **kw)
    def log_message(self, fmt, *args):
        pass  # keep it quiet

def main():
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
        url = f"http://127.0.0.1:{PORT}/"
        print(f"Serving ClickHouse blog archive at {url}  (Ctrl+C to stop)")
        try:
            webbrowser.open(url)
        except Exception:
            pass
        httpd.serve_forever()

if __name__ == "__main__":
    main()
