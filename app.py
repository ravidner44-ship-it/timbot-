import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# Import Telegram Bot runner
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "execution"))
import tg_bot

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Tell Tims Telegram Bot by SIDHU (@deep_xd5) is Running OK!")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_health_server():
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    print(f"[*] Health check server listening on port {port}...")
    server.serve_forever()

if __name__ == "__main__":
    # 1. Start HTTP Health check in background thread for Render/Koyeb
    t = threading.Thread(target=run_health_server, daemon=True)
    t.start()

    # 2. Start Telegram Bot main loop
    tg_bot.start_bot()
