"""CMDB тізімін түгендеу стандартына (standard.json) сәйкестікке тексеру.

Тексерулер:
  1) міндетті өрістер толтырылған ба;
  2) asset_tag үлгіге сай ма (AEC-ТҮР-0000);
  3) type және status стандартта бар ма;
  4) asset_tag, ip, mac қайталанбай ма;
  5) құрылғы ұзақ уақыт көрінбей ме (max_days_not_seen);
  6) тіркелмеген (approved=NO) және белгісіз (UNK) құрылғылар.

Іске қосу:
  python validate.py cmdb_day1.csv
  python validate.py cmdb_day2.csv --today 2026-12-20
"""
import argparse
import csv
import json
import os
import re
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmdb", nargs="?", default=os.path.join(HERE, "cmdb.csv"))
    ap.add_argument("--today", default=None, help="тексеру күні, ЖЖЖЖ-АА-КК")
    args = ap.parse_args()

    with open(os.path.join(HERE, "standard.json"), encoding="utf-8") as f:
        std = json.load(f)
    with open(args.cmdb, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    today = date.fromisoformat(args.today) if args.today else date.today()
    pattern = re.compile(std["asset_tag_pattern"])
    problems = []  # (деңгей, asset_tag, мәтін)

    seen = {"asset_tag": {}, "ip": {}, "mac": {}}
    for r in rows:
        tag = r.get("asset_tag", "?")
        for field in std["required_fields"]:
            if not r.get(field, "").strip():
                problems.append(("ОРТА", tag, "'%s' өрісі бос" % field))
        if not pattern.match(tag):
            problems.append(("ЖОҒАРЫ", tag, "asset_tag үлгіге сай емес"))
        if r.get("type") not in std["types"]:
            problems.append(("ЖОҒАРЫ", tag, "белгісіз type: %s" % r.get("type")))
        if r.get("status") not in std["statuses"]:
            problems.append(("ОРТА", tag, "белгісіз status: %s" % r.get("status")))
        for key in seen:
            val = r.get(key, "").upper()
            if val and val in seen[key]:
                problems.append(("ЖОҒАРЫ", tag, "%s қайталанады (%s)" % (key, seen[key][val])))
            seen[key][val] = tag
        try:
            days = (today - date.fromisoformat(r["last_seen"])).days
            if days > std["max_days_not_seen"]:
                problems.append(("ОРТА", tag, "%d күн бойы көрінбеген" % days))
        except (KeyError, ValueError):
            problems.append(("ОРТА", tag, "last_seen күні қате"))
        if r.get("approved") == "NO":
            problems.append(("ЖОҒАРЫ", tag, "тіркелмеген құрылғы (%s, %s)" % (r.get("ip"), r.get("hostname"))))
        if r.get("type") == "UNK":
            problems.append(("ЖОҒАРЫ", tag, "құрылғы түрі анықталмады — қолмен тексеру керек"))

    total = len(rows)
    bad_tags = {p[1] for p in problems}
    score = round(100 * (total - len(bad_tags)) / total) if total else 0
    print("Тексерілді: %d жазба, мәселесі бар жазбалар: %d" % (total, len(bad_tags)))
    for level in ("ЖОҒАРЫ", "ОРТА"):
        for p in problems:
            if p[0] == level:
                print("  [%s] %-14s %s" % p)
    print("Стандартқа сәйкестік: %d%%" % score)
    sys.exit(1 if any(p[0] == "ЖОҒАРЫ" for p in problems) else 0)


if __name__ == "__main__":
    main()
