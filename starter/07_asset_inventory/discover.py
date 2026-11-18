"""Жабдықтарды автоматты анықтау: сканерлеу нәтижесінен CMDB түгендеу тізімін жасайды.

Сканер құрылғы туралы тек «іздер» көреді: IP, MAC, TTL, ашық порттар, баннер.
Скрипт осы іздер бойынша құрылғының өндірушісін, ОЖ-сін, түрін және рөлін
ережелер арқылы анықтайды, содан кейін стандарт бойынша asset_tag береді.

Іске қосу:
  python discover.py --scan scans/scan_day1.json --out cmdb_day1.csv
  python discover.py --scan scans/scan_day2.json --out cmdb_day2.csv --prev cmdb_day1.csv
"""
import argparse
import csv
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# Порт -> қызмет атауы
SERVICES = {
    22: "ssh", 23: "telnet", 53: "dns", 80: "http", 88: "kerberos", 135: "msrpc",
    139: "netbios", 161: "snmp", 389: "ldap", 443: "https", 445: "smb", 515: "lpd",
    554: "rtsp", 631: "ipp", 1883: "mqtt", 3306: "mysql", 3389: "rdp", 5000: "upnp",
    5432: "postgresql", 5900: "vnc", 7000: "airplay", 8000: "http-alt", 8080: "http-proxy",
    9100: "jetdirect",
}
SERVER_PORTS = {53, 80, 88, 389, 443, 3306, 5432}

FIELDS = ["asset_tag", "type", "hostname", "ip", "mac", "vendor", "os", "role",
          "services", "owner", "location", "status", "approved", "criticality", "last_seen"]


def load_oui(path):
    table = {}
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            table[row["prefix"].upper()] = row["vendor"]
    return table


def vendor_by_mac(mac, oui):
    return oui.get(mac.upper()[:8], "Белгісіз")


def os_by_ttl(ttl, banner):
    """TTL бойынша ОЖ отбасын болжау, баннер болса — нақтылау."""
    b = banner.lower()
    for word, name in (("windows", "Windows"), ("macos", "macOS"), ("ubuntu", "Linux (Ubuntu)"),
                       ("cisco", "Cisco IOS")):
        if word in b:
            return banner if word in ("windows", "macos") else name
    if ttl <= 64:
        return "Linux/Unix"
    if ttl <= 128:
        return "Windows"
    return "Желілік ОЖ"


def classify(dev, vendor, os_name):
    """Құрылғы түрі (стандарттағы код) және рөлі. Ережелер реті маңызды!"""
    ports = set(dev["open_ports"])
    host = dev["hostname"].lower()
    if 161 in ports or 23 in ports or dev["ttl"] > 128 or vendor == "Ubiquiti":
        return "NET", "желілік жабдық"
    if ports & {9100, 631, 515}:
        return "PRN", "принтер"
    if 554 in ports:
        return "CAM", "бейнебақылау"
    if 1883 in ports:
        return "IOT", "датчик / IoT"
    if ports & SERVER_PORTS:
        if 389 in ports or 88 in ports:
            return "SRV", "домен контроллері"
        if ports & {5432, 3306}:
            return "SRV", "дерекқор сервері"
        if ports & {80, 443}:
            return "SRV", "веб-сервер"
        return "SRV", "сервер"
    if "Server" in os_name and 445 in ports:
        return "SRV", "файлдық сервер"
    if vendor == "Apple" or "macOS" in os_name:
        return "NB", "ноутбук"
    if "Windows" in os_name and ports & {135, 445}:
        return "PC", "жұмыс станциясы"
    return "UNK", "белгісіз"


def load_approved(path):
    approved = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                approved[row["hostname"]] = row
    return approved


def load_prev_tags(path):
    """Алдыңғы түгендеуден MAC -> asset_tag. Тег құрылғыға бір рет беріледі және өзгермейді."""
    tags = {}
    if path and os.path.exists(path):
        with open(path, encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                tags[row["mac"].upper()] = row["asset_tag"]
    return tags


def build_inventory(scan, oui, approved, standard, prev_tags=None):
    prev_tags = prev_tags or {}
    counters = {}
    for tag in prev_tags.values():          # бос нөмірден жалғастыру
        _, typ, num = tag.split("-")
        counters[typ] = max(counters.get(typ, 0), int(num))
    items = []
    for dev in sorted(scan["devices"], key=lambda d: [int(x) for x in d["ip"].split(".")]):
        vendor = vendor_by_mac(dev["mac"], oui)
        os_name = os_by_ttl(dev["ttl"], dev["banner"])
        typ, role = classify(dev, vendor, os_name)
        tag = prev_tags.get(dev["mac"].upper())
        if not tag:
            counters[typ] = counters.get(typ, 0) + 1
            tag = "%s-%s-%04d" % (standard["organization_code"], typ, counters[typ])
        appr = approved.get(dev["hostname"])
        items.append({
            "asset_tag": tag,
            "type": typ,
            "hostname": dev["hostname"] or "(атаусыз)",
            "ip": dev["ip"],
            "mac": dev["mac"],
            "vendor": vendor,
            "os": os_name,
            "role": role,
            "services": " ".join(SERVICES.get(p, str(p)) for p in dev["open_ports"]),
            "owner": appr["owner"] if appr else "",
            "location": appr["location"] if appr else "",
            "status": "in_use",
            "approved": "yes" if appr else "NO",
            "criticality": standard["criticality"].get(typ, "medium"),
            "last_seen": scan["scan_date"],
        })
    return items


def main():
    ap = argparse.ArgumentParser(description="Желі сканерлеу нәтижесінен CMDB жасау")
    ap.add_argument("--scan", default=os.path.join(HERE, "scans", "scan_day1.json"))
    ap.add_argument("--out", default=os.path.join(HERE, "cmdb.csv"))
    ap.add_argument("--prev", help="алдыңғы CMDB (asset_tag сақталуы үшін), мысалы cmdb_day1.csv")
    args = ap.parse_args()

    with open(os.path.join(HERE, "standard.json"), encoding="utf-8") as f:
        standard = json.load(f)
    with open(args.scan, encoding="utf-8") as f:
        scan = json.load(f)
    oui = load_oui(os.path.join(HERE, "oui.csv"))
    approved = load_approved(os.path.join(HERE, "approved.csv"))

    items = build_inventory(scan, oui, approved, standard, load_prev_tags(args.prev))

    with open(args.out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(items)
    with open(os.path.splitext(args.out)[0] + ".json", "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    print("Сканерлеу күні: %s, табылған құрылғылар: %d" % (scan["scan_date"], len(items)))
    print("%-15s %-4s %-15s %-14s %-18s %s" % ("asset_tag", "түрі", "hostname", "ip", "рөлі", "тіркелген"))
    for it in items:
        print("%-15s %-4s %-15s %-14s %-18s %s" % (it["asset_tag"], it["type"], it["hostname"][:15],
                                                    it["ip"], it["role"][:18], it["approved"]))
    by_type = {}
    for it in items:
        by_type[it["type"]] = by_type.get(it["type"], 0) + 1
    print("\nТүрлері бойынша:", ", ".join("%s=%d" % kv for kv in sorted(by_type.items())))
    unk = [it for it in items if it["approved"] == "NO"]
    if unk:
        print("НАЗАР АУДАРЫҢЫЗ: тіркелмеген құрылғылар: %s" % ", ".join(i["ip"] for i in unk))
    print("Сақталды: %s және .json" % args.out)


if __name__ == "__main__":
    main()
