"""Желілік аномалияларды автоматты анықтау.

Үш әдіс:
  threshold — тұрақты шектер (қарапайым, бірақ «қалыпты» шыңдарда жалған дабыл береді);
  zscore    — профильден ауытқу: z = (мән - орташа) / std; |z| > k болса — аномалия;
  rules     — шабуыл түрлеріне арналған ережелер (сканерлеу, деректерді шығару, DDoS, beaconing).
  all       — үшеуі бірге.

Нәтиже: anomalies.csv (әр 5 минуттық аралық) және incidents.csv (біріктірілген оқиғалар).

Іске қосу:
  python profile.py
  python detect.py --method zscore --k 4
  python detect.py --method rules
  python detect.py --method all
"""
import argparse
import csv
import json
import os
from collections import defaultdict
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
METRICS = ["bytes_out", "bytes_in", "connections", "dst_ports", "dst_hosts", "external_mb"]

# тұрақты шектер (5 минутқа)
STATIC = {"bytes_out": 100, "bytes_in": 200, "connections": 1000, "dst_ports": 100}
# std өте кіші болса (түнде 0), z шексіз үлкен болмауы үшін ең кіші std
STD_FLOOR = {"bytes_out": 1.0, "bytes_in": 1.0, "connections": 3, "dst_ports": 3, "dst_hosts": 2, "external_mb": 0.5}


def key_of(r):
    t = datetime.strptime(r["time"], "%Y-%m-%d %H:%M")
    dtype = "weekend" if t.weekday() >= 5 else "workday"
    return "%s|%s|%02d" % (r["host"], dtype, t.hour)


def m_threshold(r, prof):
    out = []
    for m, lim in STATIC.items():
        v = float(r[m])
        if v > lim:
            out.append(("threshold", m, v, lim, round(v / lim, 1)))
    return out


def m_zscore(r, prof, k):
    out = []
    p = prof.get(key_of(r))
    if not p:
        return out
    for m in METRICS:
        v = float(r[m])
        std = max(p[m]["std"], STD_FLOOR[m])
        z = (v - p[m]["mean"]) / std
        if z > k:
            out.append(("zscore", m, v, p[m]["mean"], round(z, 1)))
    return out


def m_rules(r, prof, state):
    out = []
    p = prof.get(key_of(r))
    v = {m: float(r[m]) for m in METRICS}
    if v["dst_ports"] > 100 or v["dst_hosts"] > 50:
        out.append(("port_scan", "dst_ports", v["dst_ports"], 100, round(v["dst_ports"] / 100, 1)))
    if p:
        ext_lim = max(p["external_mb"]["p95"] * 5, 50)
        if v["external_mb"] > ext_lim:
            out.append(("exfiltration", "external_mb", v["external_mb"], round(ext_lim, 1), round(v["external_mb"] / ext_lim, 1)))
        conn_lim = max(p["connections"]["p95"] * 10, 500)
        if v["connections"] > conn_lim and v["bytes_in"] > p["bytes_in"]["p95"] * 5:
            out.append(("ddos", "connections", v["connections"], round(conn_lim), round(v["connections"] / conn_lim, 1)))
        # beaconing: профиль бойынша «тыныш» сағатта аз, бірақ үздіксіз сыртқы қосылым
        idle = p["connections"]["max"] == 0
        host = r["host"]
        if idle and 0 < v["connections"] <= 5 and v["external_mb"] > 0:
            state[host] = state.get(host, 0) + 1
            if state[host] >= 6:       # кемінде 30 минут қатарынан
                out.append(("beaconing", "connections", v["connections"], 0, state[host]))
        else:
            state[host] = 0
    return out


def merge(rows):
    """Бір хосттағы бір түрлі, қатар келген аралықтарды бір инцидентке біріктіру."""
    inc = []
    open_ = {}
    for a in sorted(rows, key=lambda x: (x["host"], x["type"], x["time"])):
        t = datetime.strptime(a["time"], "%Y-%m-%d %H:%M")
        k = (a["host"], a["type"])
        cur = open_.get(k)
        if cur and t - cur["_last"] <= timedelta(minutes=5):
            cur["_last"] = t
            cur["end"] = (t + timedelta(minutes=5)).strftime("%H:%M")
            cur["intervals"] += 1
            cur["max_score"] = max(cur["max_score"], a["score"])
        else:
            cur = {"host": a["host"], "type": a["type"], "metric": a["metric"], "start": a["time"],
                   "end": (t + timedelta(minutes=5)).strftime("%H:%M"), "intervals": 1,
                   "max_score": a["score"], "_last": t}
            open_[k] = cur
            inc.append(cur)
    for c in inc:
        c.pop("_last")
    return sorted(inc, key=lambda c: c["start"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.path.join(HERE, "data", "today.csv"))
    ap.add_argument("--profiles", default=os.path.join(HERE, "profiles.json"))
    ap.add_argument("--method", default="all", choices=["threshold", "zscore", "rules", "all"])
    ap.add_argument("--k", type=float, default=4.0, help="z-score шегі")
    ap.add_argument("--out", default=os.path.join(HERE, "anomalies.csv"))
    args = ap.parse_args()

    with open(args.profiles, encoding="utf-8") as f:
        prof = json.load(f)
    with open(args.data, encoding="utf-8") as f:
        data = list(csv.DictReader(f))

    found, state = [], {}
    for r in sorted(data, key=lambda x: (x["host"], x["time"])):
        hits = []
        if args.method in ("threshold", "all"):
            hits += m_threshold(r, prof)
        if args.method in ("zscore", "all"):
            hits += m_zscore(r, prof, args.k)
        if args.method in ("rules", "all"):
            hits += m_rules(r, prof, state)
        for typ, metric, value, expected, score in hits:
            found.append({"time": r["time"], "host": r["host"], "type": typ, "metric": metric,
                          "value": round(value, 2), "expected": expected, "score": score})

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["time", "host", "type", "metric", "value", "expected", "score"])
        w.writeheader()
        w.writerows(found)
    incidents = merge(found)
    inc_path = os.path.join(os.path.dirname(args.out), "incidents.csv")
    with open(inc_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["start", "end", "host", "type", "metric", "intervals", "max_score"])
        w.writeheader()
        w.writerows(incidents)

    print("Әдіс: %s · аномал аралықтар: %d · инциденттер: %d" % (args.method, len(found), len(incidents)))
    print("%-16s %-6s %-14s %-13s %-12s %s" % ("басталуы", "соңы", "хост", "түрі", "метрика", "ұпай"))
    for c in incidents:
        print("%-16s %-6s %-14s %-13s %-12s %s" % (c["start"], c["end"], c["host"], c["type"], c["metric"], c["max_score"]))
    print("Сақталды: %s, %s" % (os.path.basename(args.out), os.path.basename(inc_path)))


if __name__ == "__main__":
    main()
