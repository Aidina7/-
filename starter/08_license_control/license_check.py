"""Лицензияларды есепке алу және сәйкестікті тексеру (Software Asset Management).

Кезеңдер:
  1) нормализация: орнатылған бағдарламаның «шикі» атауын каталог арқылы өнімге сәйкестендіру;
  2) есептеу: әр өнім үшін қолданылуы (құрылғы / пайдаланушы / бір мезгілдегі қосылым);
  3) салыстыру: сатып алынған лицензиялар саны (entitlement) мен қолданылуы;
  4) тәуекелдер: мерзімі өтетін жазылымдар, қолданылмайтын лицензиялар (shelfware),
     тыйым салынған және каталогта жоқ бағдарламалар, лицензия шектеулері.

Іске қосу:
  python license_check.py
  python license_check.py --today 2026-11-18 --warn-days 30 --unused-days 90
Нәтиже: экранға + license_report.md + license_report.csv
"""
import argparse
import csv
import json
import os
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))


def load_catalog(path):
    with open(path, encoding="utf-8") as f:
        return [(r["pattern"].lower(), r["product"]) for r in csv.DictReader(f)]


def normalize(raw, catalog):
    low = raw.lower()
    for pattern, product in catalog:
        if pattern in low:
            return product
    return None


def peak_sessions(path):
    if not os.path.exists(path):
        return 0, []
    peak, when = 0, []
    with open(path, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            n = int(r["active_sessions"])
            if n > peak:
                peak, when = n, [r["timestamp"]]
            elif n == peak:
                when.append(r["timestamp"])
    return peak, when


def money(x):
    return "{:,}".format(int(x)).replace(",", " ") + " ₸"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--installs", default=os.path.join(HERE, "installs.csv"))
    ap.add_argument("--today", default="2026-11-18")
    ap.add_argument("--warn-days", type=int, default=30, help="мерзімі осы күн ішінде өтетін жазылымдар")
    ap.add_argument("--unused-days", type=int, default=90, help="осынша күн қолданылмаса — shelfware")
    args = ap.parse_args()

    today = date.fromisoformat(args.today)
    with open(os.path.join(HERE, "licenses.json"), encoding="utf-8") as f:
        lic = json.load(f)
    catalog = load_catalog(os.path.join(HERE, "catalog.csv"))
    with open(args.installs, encoding="utf-8-sig") as f:
        installs = list(csv.DictReader(f))

    hosts = sorted({r["hostname"] for r in installs})
    # Тегін, бірақ ұйымда қолдануға болмайтын бағдарламалар (commercial_use = false)
    personal_only = {fs["product"]: fs for fs in lic["free_software"] if fs.get("commercial_use") is False}
    usage = {}          # product -> {"devices": set, "users": set, "unused": set}
    unknown, forbidden, restricted = [], [], []
    for r in installs:
        raw = r["software"]
        bad = next((fb for fb in lic["forbidden"] if fb["pattern"] in raw.lower()), None)
        if bad:
            forbidden.append((r["hostname"], r["user"], raw, bad["reason"]))
            continue
        product = normalize(raw, catalog)
        if not product:
            unknown.append((r["hostname"], r["user"], raw))
            continue
        u = usage.setdefault(product, {"devices": set(), "users": set(), "unused": set()})
        u["devices"].add(r["hostname"])
        u["users"].add(r["user"])
        if int(r["last_used_days"]) > args.unused_days:
            u["unused"].add(r["user"] if product in ("autocad_lt", "photoshop", "m365", "pycharm_edu") else r["hostname"])
        if product in personal_only:
            restricted.append((r["hostname"], r["user"], raw, personal_only[product]["note"]))

    peak, peak_when = peak_sessions(os.path.join(HERE, "sessions_1c.csv"))

    results = []
    risk_money = 0
    for L in lic["licenses"]:
        u = usage.get(L["product"], {"devices": set(), "users": set(), "unused": set()})
        if L["metric"] == "device":
            used = len(u["devices"])
        elif L["metric"] == "user":
            used = len(u["users"])
        else:
            used = peak
        diff = L["count"] - used
        status = []
        if diff < 0:
            status.append("ТАПШЫ %d" % -diff)
            risk_money += -diff * L["cost_per_unit"]
        if u["unused"]:
            status.append("қолданылмайды: %d" % len(u["unused"]))
        if L["expires"]:
            left = (date.fromisoformat(L["expires"]) - today).days
            if left < 0:
                status.append("МЕРЗІМІ ӨТКЕН")
            elif left <= args.warn_days:
                status.append("мерзімі %d күнде өтеді" % left)
        results.append({"product": L["product"], "name": L["name"], "metric": L["metric"],
                        "licensed": L["count"], "used": used, "balance": diff,
                        "expires": L["expires"] or "—", "status": "; ".join(status) or "OK",
                        "unused": ", ".join(sorted(u["unused"]))})

    kas = usage.get("kaspersky", {"devices": set()})["devices"]
    win = usage.get("windows11pro", {"devices": set()})["devices"]
    no_av = sorted(win - kas)

    # --- экранға және файлға ---
    out = []
    out.append("# Лицензиялар бойынша сәйкестік есебі")
    out.append("")
    out.append("Тексеру күні: %s · компьютерлер: %d · орнатулар: %d" % (args.today, len(hosts), len(installs)))
    out.append("")
    out.append("| Өнім | Есептеу | Сатып алынған | Қолданылуы | Қалдық | Мерзімі | Күйі |")
    out.append("|---|---|---|---|---|---|---|")
    for r in results:
        out.append("| %s | %s | %d | %d | %d | %s | %s |" % (r["name"], r["metric"], r["licensed"], r["used"],
                                                          r["balance"], r["expires"], r["status"]))
    out.append("")
    if peak:
        out.append("1С: бір мезгілдегі қосылымдардың шыңы = %d (%s)" % (peak, ", ".join(peak_when)))
        out.append("")
    out.append("## Тыйым салынған бағдарламалар (%d)" % len(forbidden))
    out += ["- %s (%s): %s — %s" % f for f in forbidden]
    out.append("")
    out.append("## Лицензия шектеулерін бұзу (%d)" % len(restricted))
    out += ["- %s (%s): %s — %s" % f for f in restricted]
    out.append("")
    out.append("## Каталогта жоқ бағдарламалар — жіктеу керек (%d)" % len(unknown))
    out += ["- %s (%s): %s" % f for f in unknown]
    out.append("")
    out.append("## Антивирусы жоқ Windows компьютерлер (%d)" % len(no_av))
    out += ["- %s" % h for h in no_av]
    out.append("")
    over = [r for r in results if r["balance"] < 0]
    out.append("## Қорытынды")
    out.append("- Лицензиясы жетіспейтін өнімдер: %d; заңдастыруға қажет шамамен: %s" % (len(over), money(risk_money)))
    shelf = [r for r in results if r["unused"]]
    out.append("- Қайта бөлуге болатын (shelfware) лицензиялары бар өнімдер: %d" % len(shelf))
    compliant = not over and not forbidden and not restricted
    out.append("- Жалпы күйі: %s" % ("СӘЙКЕС" if compliant else "СӘЙКЕС ЕМЕС — шара қолдану керек"))

    text = "\n".join(out) + "\n"
    print(text)
    with open(os.path.join(HERE, "license_report.md"), "w", encoding="utf-8") as f:
        f.write(text)
    with open(os.path.join(HERE, "license_report.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        w.writeheader()
        w.writerows(results)
    print("Сақталды: license_report.md, license_report.csv")
    sys.exit(0 if compliant else 2)


if __name__ == "__main__":
    main()
