"""CMDB бойынша HTML есеп: түрлері, ОЖ, өндірушілер, мәселелер және толық кесте.

Іске қосу:
  python report.py cmdb_day2.csv      -> inventory_report.html (браузерде ашыңыз)
"""
import argparse
import csv
import html
import os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))


def bar_rows(counter, total):
    rows = []
    for name, n in counter.most_common():
        pct = 100 * n / total
        rows.append('<tr><td>%s</td><td><div class="bar" style="width:%.0f%%"></div></td><td>%d</td></tr>'
                    % (html.escape(name), pct, n))
    return "\n".join(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmdb", nargs="?", default=os.path.join(HERE, "cmdb.csv"))
    ap.add_argument("--out", default=os.path.join(HERE, "inventory_report.html"))
    args = ap.parse_args()
    with open(args.cmdb, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    total = len(rows)
    by_type = Counter(r["type"] for r in rows)
    by_os = Counter(r["os"].split(" ")[0] for r in rows)
    by_vendor = Counter(r["vendor"] for r in rows)
    flagged = [r for r in rows if r["approved"] == "NO" or r["type"] == "UNK"]

    table = "\n".join(
        "<tr class='%s'>%s</tr>" % ("bad" if r in flagged else "",
                                    "".join("<td>%s</td>" % html.escape(r[k]) for k in
                                            ("asset_tag", "type", "hostname", "ip", "mac", "vendor", "os",
                                             "role", "services", "owner", "location", "approved")))
        for r in rows)
    page = """<!DOCTYPE html><html lang="kk"><head><meta charset="utf-8">
<title>IT-активтер түгендеуі</title>
<style>
body{font-family:system-ui,Arial,sans-serif;margin:24px;color:#1f2933}
h1{margin:0 0 4px}.sub{color:#616e7c;margin-bottom:20px}
.cards{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:20px}
.card{border:1px solid #e4e7eb;border-radius:8px;padding:12px 16px;min-width:140px}
.card b{display:block;font-size:28px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px;margin-bottom:20px}
table{border-collapse:collapse;width:100%%;font-size:13px}
td,th{border-bottom:1px solid #e4e7eb;padding:6px;text-align:left}
.bar{height:10px;background:#2f6fde;border-radius:4px}
tr.bad td{background:#fdecea}
</style></head><body>
<h1>IT-активтер түгендеуі</h1>
<div class="sub">Дереккөз: %s</div>
<div class="cards">
<div class="card"><b>%d</b>барлық актив</div>
<div class="card"><b>%d</b>сервер</div>
<div class="card"><b>%d</b>жұмыс орны</div>
<div class="card"><b style="color:#c0392b">%d</b>назар аудару керек</div>
</div>
<div class="grid">
<div><h3>Түрлері</h3><table>%s</table></div>
<div><h3>Операциялық жүйелер</h3><table>%s</table></div>
<div><h3>Өндірушілер</h3><table>%s</table></div>
</div>
<h3>Барлық активтер</h3>
<table><tr><th>Тег</th><th>Түрі</th><th>Атауы</th><th>IP</th><th>MAC</th><th>Өндіруші</th><th>ОЖ</th>
<th>Рөлі</th><th>Қызметтер</th><th>Жауапты</th><th>Орны</th><th>Тіркелген</th></tr>
%s</table></body></html>""" % (html.escape(os.path.basename(args.cmdb)), total, by_type.get("SRV", 0),
                                 by_type.get("PC", 0) + by_type.get("NB", 0), len(flagged),
                                 bar_rows(by_type, total), bar_rows(by_os, total), bar_rows(by_vendor, total),
                                 table)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(page)
    print("Есеп дайын: %s (%d актив, назар аудару керек: %d)" % (args.out, total, len(flagged)))


if __name__ == "__main__":
    main()
