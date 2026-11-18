"""SLI есептеу, SLO / SLA тексеру, қателер бюджеті және burn rate.

  SLI (индикатор)  — нақты өлшенген мән: қолжетімділік %, жылдам жауаптар %
  SLO (мақсат)     — ішкі мақсат: мысалы 30 күнде қолжетімділік ≥ 99.5%
  SLA (келісім)    — клиентпен келісімшарт: бұзылса — айыппұл / өтемақы
  Қателер бюджеті  — SLO рұқсат ететін «жаман» сұраулар саны: (1 − SLO) × барлық сұраулар
  Burn rate        — бюджет қаншалықты тез жұмсалып жатыр: (жаман үлесі) / (1 − SLO).
                     1.0 — бюджет дәл терезе соңында бітеді; 14.4 — 2 күнде бітеді.

Іске қосу:
  python sli.py                          -> барлық қызмет, 30 күн
  python sli.py --service portal --daily -> күн сайынғы кесте
  python sli.py --html                   -> sla_report.html
Шығу коды: 0 — бәрі қалыпты, 2 — SLO бұзылды немесе шұғыл ескерту бар.
"""
import argparse
import csv
import html
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))


def load_rows(path):
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            for k in ("requests", "errors_5xx", "errors_4xx", "le_100", "le_300", "le_1000", "gt_1000"):
                r[k] = int(r[k])
            r["t"] = datetime.strptime(r["time"], "%Y-%m-%d %H:%M")
            yield r


def fast_count(r, latency_ms):
    """latency_ms шегінен жылдам жауаптар саны (гистограмма бойынша)."""
    if latency_ms >= 1000:
        return r["le_100"] + r["le_300"] + r["le_1000"]
    if latency_ms >= 300:
        return r["le_100"] + r["le_300"]
    return r["le_100"]


def p95_from_buckets(total, b):
    """Гистограммадан 95-перцентильді шамамен бағалау (бакет шекарасы)."""
    need = 0.95 * total
    acc = 0
    for edge, n in (("≤100 мс", b[0]), ("≤300 мс", b[1]), ("≤1000 мс", b[2]), (">1000 мс", b[3])):
        acc += n
        if acc >= need:
            return edge
    return ">1000 мс"


def summarize(rows, slo):
    tot = sum(r["requests"] for r in rows)
    bad = sum(r["errors_5xx"] for r in rows)
    fast = sum(fast_count(r, slo["latency_ms"]) for r in rows)
    buckets = [sum(r[k] for r in rows) for k in ("le_100", "le_300", "le_1000", "gt_1000")]
    avail = 100 * (tot - bad) / tot if tot else 100
    lat = 100 * fast / tot if tot else 100
    return {"requests": tot, "bad": bad, "availability": avail, "latency_sli": lat,
            "error_rate": 100 * bad / tot if tot else 0, "p95": p95_from_buckets(tot, buckets),
            "errors_4xx": sum(r["errors_4xx"] for r in rows)}


def burn_rate(rows, slo_avail):
    tot = sum(r["requests"] for r in rows)
    bad = sum(r["errors_5xx"] for r in rows)
    if not tot:
        return 0.0
    return (bad / tot) / (1 - slo_avail / 100)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.path.join(HERE, "data", "metrics.csv"))
    ap.add_argument("--service")
    ap.add_argument("--now", default="2026-11-08 23:55", help="«қазір» деп есептелетін уақыт")
    ap.add_argument("--daily", action="store_true", help="күн сайынғы қолжетімділік кестесі")
    ap.add_argument("--html", action="store_true")
    args = ap.parse_args()

    with open(os.path.join(HERE, "services.json"), encoding="utf-8") as f:
        cfg = json.load(f)
    now = datetime.strptime(args.now, "%Y-%m-%d %H:%M")
    rows_by = defaultdict(list)
    for r in load_rows(args.data):
        if r["t"] <= now:
            rows_by[r["service"]].append(r)

    problems = False
    md = ["# Қызмет көрсету сапасы (SLA) есебі", "", "Есеп уақыты: %s" % args.now, ""]
    html_blocks = []
    for svc in cfg["services"]:
        if args.service and svc["id"] != args.service:
            continue
        slo = svc["slo"]
        start = now - timedelta(days=slo["window_days"])
        rows = [r for r in rows_by[svc["id"]] if r["t"] > start]
        s = summarize(rows, slo)
        budget = (1 - slo["availability"] / 100) * s["requests"]
        used = 100 * s["bad"] / budget if budget else 0
        last = lambda hours: [r for r in rows if r["t"] > now - timedelta(hours=hours)]
        br1 = burn_rate(last(cfg["alerts"]["fast_burn"]["window_hours"]), slo["availability"])
        br6 = burn_rate(last(cfg["alerts"]["slow_burn"]["window_hours"]), slo["availability"])
        ok_av = s["availability"] >= slo["availability"]
        ok_lat = s["latency_sli"] >= slo["latency_target"]
        ok_sla = s["availability"] >= svc["sla"]["availability"]
        alerts = []
        if br1 >= cfg["alerts"]["fast_burn"]["burn_rate"]:
            alerts.append("🔴 %s (1 сағ burn rate = %.1f)" % (cfg["alerts"]["fast_burn"]["action"], br1))
        elif br6 >= cfg["alerts"]["slow_burn"]["burn_rate"]:
            alerts.append("🟠 %s (6 сағ burn rate = %.1f)" % (cfg["alerts"]["slow_burn"]["action"], br6))
        if not ok_av or alerts:
            problems = True

        mark = lambda ok: "✅" if ok else "❌"
        lines = [
            "## %s (%s)" % (svc["name"], svc["id"]),
            "",
            "| Көрсеткіш | Нақты (SLI) | Мақсат | Күйі |",
            "|---|---|---|---|",
            "| Қолжетімділік, %d күн | %.3f%% | SLO ≥ %.1f%% | %s |" % (slo["window_days"], s["availability"], slo["availability"], mark(ok_av)),
            "| Жауаптар < %d мс | %.2f%% | ≥ %.1f%% | %s |" % (slo["latency_ms"], s["latency_sli"], slo["latency_target"], mark(ok_lat)),
            "| SLA (келісімшарт) | %.3f%% | ≥ %.1f%% | %s |" % (s["availability"], svc["sla"]["availability"], mark(ok_sla) + ("" if ok_sla else " айыппұл: " + svc["sla"]["penalty"])),
            "",
            "- Сұраулар: %d, сервер қателері (5xx): %d (%.3f%%), клиент қателері (4xx, SLI-ге кірмейді): %d"
            % (s["requests"], s["bad"], s["error_rate"], s["errors_4xx"]),
            "- Жауап уақытының p95 бағасы: %s" % s["p95"],
            "- Қателер бюджеті: %d сұрау; жұмсалды %.0f%%, қалды %.0f%%" % (budget, used, max(0, 100 - used)),
            "- Burn rate: соңғы 1 сағ = %.2f, соңғы 6 сағ = %.2f" % (br1, br6),
        ]
        lines += ["- ЕСКЕРТУ: " + a for a in alerts] or ["- Ескертулер жоқ"]
        if args.daily:
            lines += ["", "| Күн | Сұраулар | 5xx | Қолжетімділік | Жылдам % |", "|---|---|---|---|---|"]
            days = defaultdict(list)
            for r in rows:
                days[r["time"][:10]].append(r)
            for d in sorted(days):
                ds = summarize(days[d], slo)
                flag = " ⚠" if ds["availability"] < slo["availability"] or ds["latency_sli"] < slo["latency_target"] else ""
                lines.append("| %s | %d | %d | %.3f%% | %.1f%%%s |" % (d, ds["requests"], ds["bad"], ds["availability"], ds["latency_sli"], flag))
        lines.append("")
        md += lines
        if args.html:
            days = defaultdict(list)
            for r in rows:
                days[r["time"][:10]].append(r)
            bars = ""
            for i, d in enumerate(sorted(days)):
                ds = summarize(days[d], slo)
                color = "#1e8a4c" if ds["availability"] >= slo["availability"] else ("#d9822b" if ds["availability"] >= svc["sla"]["availability"] else "#c0392b")
                bars += '<div title="%s: %.3f%%" style="background:%s"></div>' % (d, ds["availability"], color)
            html_blocks.append("<div class='svc'><h2>%s</h2><div class='bars'>%s</div><pre>%s</pre></div>" % (
                html.escape(svc["name"]), bars, html.escape("\n".join(lines[2:]))))

    text = "\n".join(md)
    print(text)
    with open(os.path.join(HERE, "sla_report.md"), "w", encoding="utf-8") as f:
        f.write(text)
    if args.html:
        page = ("<!DOCTYPE html><html lang='kk'><head><meta charset='utf-8'><title>SLA есебі</title><style>"
                "body{font-family:system-ui,Arial;margin:24px;color:#1d2733}.svc{border:1px solid #e3e7ec;border-radius:10px;padding:12px 16px;margin-bottom:16px}"
                ".bars{display:flex;gap:3px;height:34px;margin:8px 0}.bars div{flex:1;border-radius:3px}pre{white-space:pre-wrap;font-size:13px}"
                "</style></head><body><h1>Қызмет көрсету сапасы</h1><p>Әр жолақ — бір күн: жасыл — SLO орындалды, сары — SLO бұзылды бірақ SLA сақталды, қызыл — SLA бұзылды.</p>%s</body></html>") % "".join(html_blocks)
        with open(os.path.join(HERE, "sla_report.html"), "w", encoding="utf-8") as f:
            f.write(page)
        print("HTML: sla_report.html")
    print("Сақталды: sla_report.md")
    sys.exit(2 if problems else 0)


if __name__ == "__main__":
    main()
