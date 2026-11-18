"""Тексеруге арналған жергілікті «қызмет»: кейде баяулайды, кейде қате қайтарады.

Іске қосу (бөлек терминалда):
  python test_server.py                         -> http://127.0.0.1:8085
  python test_server.py --errors 0.1 --slow 0.2 -> қателер 10%, баяу жауаптар 20%

Мекенжайлар: /health (портал), /api/grades (журнал API), /lms (LMS).
Жұмыс кезінде режимді ауыстыруға болады:  /admin/break  (бәрі 503)  ·  /admin/fix  (қалпына келтіру)
"""
import argparse
import json
import random
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

STATE = {"broken": False}


def make_handler(err_rate, slow_rate):
    class H(BaseHTTPRequestHandler):
        def _send(self, code, obj):
            body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/admin/break":
                STATE["broken"] = True
                return self._send(200, {"mode": "broken"})
            if self.path == "/admin/fix":
                STATE["broken"] = False
                return self._send(200, {"mode": "ok"})
            if self.path not in ("/health", "/api/grades", "/lms"):
                return self._send(404, {"error": "not found"})
            delay = random.uniform(0.02, 0.12)
            if random.random() < slow_rate:
                delay = random.uniform(0.4, 1.5)
            time.sleep(delay)
            if STATE["broken"] or random.random() < err_rate:
                return self._send(503, {"status": "error"})
            return self._send(200, {"status": "ok", "path": self.path, "ms": int(delay * 1000)})

        def log_message(self, fmt, *a):
            pass
    return H


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8085)
    ap.add_argument("--errors", type=float, default=0.02, help="қате үлесі (0..1)")
    ap.add_argument("--slow", type=float, default=0.05, help="баяу жауап үлесі (0..1)")
    args = ap.parse_args()
    srv = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(args.errors, args.slow))
    print("Тест қызметі: http://127.0.0.1:%d  (қателер %.0f%%, баяу %.0f%%). Тоқтату: Ctrl+C"
          % (args.port, args.errors * 100, args.slow * 100))
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nТоқтатылды")


if __name__ == "__main__":
    main()
