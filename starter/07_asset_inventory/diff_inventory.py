"""Екі түгендеуді салыстыру: не қосылды, не жоғалды, не өзгерді.

Құрылғыны MAC мекенжайы бойынша сәйкестендіреміз (IP және атау өзгеруі мүмкін).
Нәтиже экранға және changes.md файлына жазылады.

Іске қосу:
  python diff_inventory.py cmdb_day1.csv cmdb_day2.csv
"""
import argparse
import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
WATCH = ["hostname", "ip", "os", "services", "type", "approved"]
RISKY_SERVICES = {"telnet", "rdp", "vnc", "http-proxy"}


def load(path):
    with open(path, encoding="utf-8-sig") as f:
        return {r["mac"].upper(): r for r in csv.DictReader(f)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("old")
    ap.add_argument("new")
    ap.add_argument("--out", default=os.path.join(HERE, "changes.md"))
    args = ap.parse_args()

    old, new = load(args.old), load(args.new)
    added = [new[m] for m in new if m not in old]
    removed = [old[m] for m in old if m not in new]
    changed = []
    for m in new:
        if m in old:
            diffs = [(k, old[m][k], new[m][k]) for k in WATCH if old[m][k] != new[m][k]]
            if diffs:
                changed.append((new[m], diffs))

    lines = ["# Түгендеудегі өзгерістер", "",
             "Салыстырылды: `%s` → `%s`" % (os.path.basename(args.old), os.path.basename(args.new)), ""]
    lines.append("## Жаңа құрылғылар (%d)" % len(added))
    for r in added:
        flag = " — ТІРКЕЛМЕГЕН!" if r["approved"] == "NO" else ""
        lines.append("- %s %s (%s, %s, %s)%s" % (r["asset_tag"], r["hostname"], r["ip"], r["vendor"], r["role"], flag))
    lines.append("")
    lines.append("## Жоғалған құрылғылар (%d)" % len(removed))
    for r in removed:
        lines.append("- %s %s (%s) — желіде жоқ: өшірілген бе, ауыстырылған ба, ұрланған ба?" % (r["asset_tag"], r["hostname"], r["ip"]))
    lines.append("")
    lines.append("## Өзгерген құрылғылар (%d)" % len(changed))
    for r, diffs in changed:
        for k, a, b in diffs:
            lines.append("- %s %s: **%s** `%s` → `%s`" % (r["asset_tag"], r["hostname"], k, a, b))
    lines.append("")
    risky = []
    for r in new.values():
        bad = RISKY_SERVICES & set(r["services"].split())
        if bad:
            risky.append("- %s %s (%s): %s" % (r["asset_tag"], r["hostname"], r["ip"], ", ".join(sorted(bad))))
    lines.append("## Қауіпті қызметтер (%d)" % len(risky))
    lines += risky

    text = "\n".join(lines) + "\n"
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(text)
    print(text)
    print("Сақталды:", args.out)


if __name__ == "__main__":
    main()
