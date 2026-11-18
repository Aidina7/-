"""HTML есеп: әр хост үшін бүгінгі трафик профильмен салыстырылады (графиктер + инциденттер).

Іске қосу (алдымен profile.py және detect.py):
  python report.py                       -> anomaly_report.html
  python report.py --metric connections
"""
import argparse
import csv
import html
import json
import os
from collections import defaultdict
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 560, 120


def svg(points, band, marks):
    top = max([v for _, v in points] + [b[1] for b in band] + [1]) * 1.1
    x = lambda i: 30 + i * (W - 40) / 287
    y = lambda v: H - 18 - v * (H - 30) / top
    up = " ".join("%.1f,%.1f" % (x(i), y(hi)) for i, (lo, hi) in enumerate(band))
    dn = " ".join("%.1f,%.1f" % (x(i), y(lo)) for i, (lo, hi) in reversed(list(enumerate(band))))
    line = " ".join("%.1f,%.1f" % (x(i), y(v)) for i, (_, v) in enumerate(points))
    red = "".join('<rect x="%.1f" y="8" width="%.1f" height="%d" fill="#c0392b" opacity=".12"/>' % (x(i), (W - 40) / 287 + 0.5, H - 26) for i in marks)
    ticks = "".join('<text x="%.1f" y="%d" font-size="9" fill="#5f6b7a">%02d</text>' % (x(h * 12) - 5, H - 4, h) for h in range(0, 24, 3))
    return ('<svg viewBox="0 0 %d %d" width="100%%"><rect width="100%%" height="100%%" fill="#fff"/>%s'
            '<polygon points="%s %s" fill="#0f6e6e" opacity=".15"/>'
            '<polyline points="%s" fill="none" stroke="#1d2733" stroke-width="1.2"/>%s'
            '<text x="2" y="14" font-size="9" fill="#5f6b7a">%.0f</text></svg>') % (W, H, red, up, dn, line, ticks, top)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--metric", default="bytes_out")
    ap.add_argument("--out", default=os.path.join(HERE, "anomaly_report.html"))
    args = ap.parse_args()
    with open(os.path.join(HERE, "profiles.json"), encoding="utf-8") as f:
        prof = json.load(f)
    rows = defaultdict(list)
    with open(os.path.join(HERE, "data", "today.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows[r["host"]].append(r)
    flagged = defaultdict(set)
    incidents = []
    if os.path.exists(os.path.join(HERE, "anomalies.csv")):
        with open(os.path.join(HERE, "anomalies.csv"), encoding="utf-8") as f:
            for a in csv.DictReader(f):
                flagged[a["host"]].add(a["time"])
        with open(os.path.join(HERE, "incidents.csv"), encoding="utf-8") as f:
            incidents = list(csv.DictReader(f))
    blocks = []
    for host in sorted(rows, key=lambda h: (-len(flagged[h]), h)):
        data = sorted(rows[host], key=lambda r: r["time"])
        pts, band, marks = [], [], []
        for i, r in enumerate(data):
            t = datetime.strptime(r["time"], "%Y-%m-%d %H:%M")
            p = prof.get("%s|%s|%02d" % (host, "weekend" if t.weekday() >= 5 else "workday", t.hour))
            pts.append((r["time"], float(r[args.metric])))
            band.append((0, p[args.metric]["p95"]) if p else (0, 0))
            if r["time"] in flagged[host]:
                marks.append(i)
        badge = '<span style="color:#c0392b;font-weight:600"> · %d аномал аралық</span>' % len(marks) if marks else ""
        blocks.append("<div class='h'><b>%s</b>%s%s</div>" % (html.escape(host), badge, svg(pts, band, marks)))
    inc_rows = "".join("<tr><td>%s</td><td>%s</td><td><b>%s</b></td><td>%s</td><td>%s</td><td>%s</td></tr>" % tuple(
        html.escape(c[k]) for k in ("start", "end", "host", "type", "metric", "max_score")) for c in incidents)
    page = """<!DOCTYPE html><html lang="kk"><head><meta charset="utf-8"><title>Желілік аномалиялар</title>
<style>body{font-family:system-ui,Arial;margin:24px;color:#1d2733}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:14px}
.h{border:1px solid #e3e7ec;border-radius:8px;padding:8px 10px}table{border-collapse:collapse;margin-bottom:20px}td,th{border:1px solid #e3e7ec;padding:5px 9px;font-size:14px}</style></head><body>
<h1>Желілік аномалиялар есебі</h1><p>Метрика: <b>%s</b> · сызық — бүгінгі мән, жасыл аймақ — профильдің p95 шегі, қызыл — табылған аномалия.</p>
<h2>Инциденттер (%d)</h2><table><tr><th>Басталуы</th><th>Соңы</th><th>Хост</th><th>Түрі</th><th>Метрика</th><th>Ұпай</th></tr>%s</table>
<h2>Хосттар</h2><div class="grid">%s</div></body></html>""" % (html.escape(args.metric), len(incidents), inc_rows, "".join(blocks))
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(page)
    print("Есеп дайын: %s (инциденттер: %d)" % (args.out, len(incidents)))


if __name__ == "__main__":
    main()
