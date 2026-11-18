"""SLA-ны үздіксіз тексеру: қызметтерге белгілі аралықпен сұрау жіберіп (синтетикалық мониторинг),
қолжетімділік пен жауап уақытын өлшейді, жылжымалы терезеде SLO-мен салыстырады және ескерту береді.

Іске қосу:
  python test_server.py                       (бөлек терминалда)
  python check_sla.py --interval 2 --count 60 -> 2 секунд сайын, 60 рет
  python check_sla.py --url https://aidina7.github.io/-/ --interval 5 --count 20
  python check_sla.py --count 0               -> тоқтатқанша (Ctrl+C)
Нәтиже: probes.csv (әр тексеру), экранда ағымдағы SLI және ескертулер.
"""
import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections import deque
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))


def probe(url, timeout):
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            code = r.status
            r.read(1024)
    except urllib.error.HTTPError as e:
        code = e.code
    except Exception:
        code = 0                       # жауап жоқ: timeout немесе байланыс қатесі
    ms = int((time.perf_counter() - t0) * 1000)
    return code, ms


def p95(values):
    s = sorted(values)
    return s[min(len(s) - 1, int(0.95 * len(s)))] if s else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=float, default=5, help="тексерулер арасындағы секунд")
    ap.add_argument("--count", type=int, default=30, help="неше рет (0 — шексіз)")
    ap.add_argument("--window", type=int, default=20, help="жылжымалы терезе (соңғы N тексеру)")
    ap.add_argument("--timeout", type=float, default=3)
    ap.add_argument("--url", help="бір URL тексеру (services.json орнына)")
    args = ap.parse_args()

    with open(os.path.join(HERE, "services.json"), encoding="utf-8") as f:
        cfg = json.load(f)
    targets = [{"id": "custom", "name": args.url, "probe_url": args.url,
                "slo": {"availability": 99.0, "latency_ms": 1000}}] if args.url else cfg["services"]
    hist = {t["id"]: deque(maxlen=args.window) for t in targets}
    total = {t["id"]: [0, 0] for t in targets}          # [ok, all]
    out = os.path.join(HERE, "probes.csv")
    new = not os.path.exists(out)
    f = open(out, "a", newline="", encoding="utf-8")
    w = csv.writer(f)
    if new:
        w.writerow(["time", "service", "url", "status", "latency_ms", "ok"])
    alerts = 0
    i = 0
    try:
        while args.count == 0 or i < args.count:
            i += 1
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            parts = []
            for t in targets:
                code, ms = probe(t["probe_url"], args.timeout)
                ok = 200 <= code < 400
                hist[t["id"]].append((ok, ms))
                total[t["id"]][0] += ok
                total[t["id"]][1] += 1
                w.writerow([now, t["id"], t["probe_url"], code, ms, int(ok)])
                h = hist[t["id"]]
                avail = 100 * sum(o for o, _ in h) / len(h)
                lat = p95([m for _, m in h])
                status = "OK " if ok else "ҚАТЕ"
                parts.append("%s %s %4dмс | %5.1f%% p95=%dмс" % (t["id"][:11].ljust(11), status, ms, avail, lat))
                if len(h) >= min(5, args.window) and (avail < t["slo"]["availability"] or lat > t["slo"]["latency_ms"]):
                    alerts += 1
                    reason = "қолжетімділік %.1f%% < %.1f%%" % (avail, t["slo"]["availability"]) if avail < t["slo"]["availability"] \
                        else "p95 %d мс > %d мс" % (lat, t["slo"]["latency_ms"])
                    parts[-1] += "  ⚠ ЕСКЕРТУ: " + reason
            f.flush()
            print("[%s] #%d" % (now[11:], i))
            for p in parts:
                print("   " + p)
            if args.count == 0 or i < args.count:
                time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nТоқтатылды")
    finally:
        f.close()
    print("\nҚорытынды:")
    for t in targets:
        ok, n = total[t["id"]]
        print("  %-12s %d/%d сәтті = %.2f%% (SLO %.1f%%)" % (t["id"], ok, n, 100 * ok / n if n else 0, t["slo"]["availability"]))
    print("Ескертулер саны: %d · журнал: probes.csv" % alerts)
    sys.exit(2 if alerts else 0)


if __name__ == "__main__":
    main()
