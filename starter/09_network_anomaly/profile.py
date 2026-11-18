"""Желілік трафик профилін құру: әр хост үшін «қалыпты» мінез-құлық.

Профиль = хост × күн түрі (жұмыс күні / демалыс) × тәулік сағаты бойынша әр метриканың
орташа мәні (mean), стандартты ауытқуы (std), 95-перцентилі (p95) және максимумы.

Іске қосу:
  python profile.py                       -> profiles.json
  python profile.py --show srv-web-01     -> хост профилін экранда көрсету
  python profile.py --show pc-acc-02 --metric connections
"""
import argparse
import csv
import json
import os
import statistics
from collections import defaultdict
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
METRICS = ["bytes_out", "bytes_in", "connections", "dst_ports", "dst_hosts", "external_mb"]


def day_type(ts):
    return "weekend" if datetime.strptime(ts, "%Y-%m-%d %H:%M").weekday() >= 5 else "workday"


def percentile(values, p):
    s = sorted(values)
    k = (len(s) - 1) * p / 100
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def build(path):
    groups = defaultdict(list)
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            key = "%s|%s|%02d" % (r["host"], day_type(r["time"]), int(r["time"][11:13]))
            groups[key].append(r)
    profiles = {}
    for key, rows in groups.items():
        prof = {}
        for m in METRICS:
            vals = [float(r[m]) for r in rows]
            prof[m] = {"mean": round(statistics.mean(vals), 3),
                       "std": round(statistics.pstdev(vals), 3),
                       "p95": round(percentile(vals, 95), 3),
                       "max": round(max(vals), 3)}
        prof["samples"] = len(rows)
        profiles[key] = prof
    return profiles


def show(profiles, host, metric, dtype):
    print("Профиль: %s · %s · %s (сағат бойынша орташа мән, ▒ — p95)" % (host, metric, dtype))
    rows = [(h, profiles.get("%s|%s|%02d" % (host, dtype, h))) for h in range(24)]
    top = max((p[metric]["p95"] for _, p in rows if p), default=1) or 1
    for h, p in rows:
        if not p:
            continue
        mean, p95 = p[metric]["mean"], p[metric]["p95"]
        bar = "█" * int(40 * mean / top)
        bar += "▒" * max(0, int(40 * p95 / top) - len(bar))
        print("%02d:00 %-40s mean=%-9.2f std=%-8.2f p95=%.2f" % (h, bar, mean, p[metric]["std"], p95))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", default=os.path.join(HERE, "data", "baseline.csv"))
    ap.add_argument("--out", default=os.path.join(HERE, "profiles.json"))
    ap.add_argument("--show", help="хост атауы")
    ap.add_argument("--metric", default="bytes_out", choices=METRICS)
    ap.add_argument("--day", default="workday", choices=["workday", "weekend"])
    args = ap.parse_args()

    profiles = build(args.baseline)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(profiles, f, ensure_ascii=False, indent=1)
    hosts = sorted({k.split("|")[0] for k in profiles})
    print("Профиль құрылды: %d хост, %d топ (хост × күн түрі × сағат) -> %s" % (len(hosts), len(profiles), args.out))
    if args.show:
        print()
        show(profiles, args.show, args.metric, args.day)


if __name__ == "__main__":
    main()
