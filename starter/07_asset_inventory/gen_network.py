"""Оқу желісінің синтетикалық сканерлеу нәтижелерін жасайды.

Нақты желіні рұқсатсыз сканерлеуге болмайды, сондықтан сабақта
«желі сканері» нәтижесі файлдарға жазылған:
  scans/scan_day1.json  — бірінші күнгі сканерлеу
  scans/scan_day2.json  — бір аптадан кейінгі сканерлеу (өзгерістермен)
  approved.csv          — бекітілген (тіркелген) құрылғылар тізімі

Әр құрылғы үшін сканер көретін мәліметтер: ip, mac, hostname (DNS атауы),
ttl (ping жауабындағы TTL), open_ports (ашық порттар), banner (қызмет жауабы).

Іске қосу:  python gen_network.py
"""
import csv
import json
import os

DEVICES = [
    # ip, mac, hostname, ttl, ports, banner
    ("10.10.1.1", "00:1A:2B:10:01:01", "core-sw-01", 255, [22, 161], "Cisco IOS 15.2"),
    ("10.10.1.2", "E0:63:DA:10:01:02", "wifi-ap-01", 64, [22, 80, 443], "UniFi AP"),
    ("10.10.1.10", "F4:8E:38:10:01:10", "srv-web-01", 64, [22, 80, 443], "nginx/1.24 Ubuntu"),
    ("10.10.1.11", "F4:8E:38:10:01:11", "srv-db-01", 64, [22, 5432], "PostgreSQL 16"),
    ("10.10.1.12", "00:0C:29:10:01:12", "srv-file-01", 128, [135, 139, 445, 3389], "Windows Server 2022"),
    ("10.10.1.13", "00:15:5D:10:01:13", "srv-ad-01", 128, [53, 88, 389, 445, 3389], "Windows Server 2019 AD DS"),
    ("10.10.2.21", "50:9A:4C:10:02:21", "pc-acc-01", 128, [135, 445], "Windows 11 Pro"),
    ("10.10.2.22", "50:9A:4C:10:02:22", "pc-acc-02", 128, [135, 445], "Windows 11 Pro"),
    ("10.10.2.23", "54:EE:75:10:02:23", "pc-hr-01", 128, [135, 445, 3389], "Windows 10 Pro"),
    ("10.10.2.24", "D4:BE:D9:10:02:24", "pc-lab-01", 128, [135, 445], "Windows 11 Edu"),
    ("10.10.2.25", "D4:BE:D9:10:02:25", "pc-lab-02", 128, [135, 445], "Windows 11 Edu"),
    ("10.10.2.31", "F0:18:98:10:02:31", "nb-director", 64, [5000, 7000], "macOS 15"),
    ("10.10.2.32", "AC:DE:48:10:02:32", "nb-teacher-07", 64, [], "macOS 14"),
    ("10.10.3.40", "3C:52:82:10:03:40", "prn-office-01", 64, [80, 515, 631, 9100], "HP LaserJet MFP"),
    ("10.10.3.41", "30:05:5C:10:03:41", "prn-lab-01", 64, [80, 631, 9100], "Brother HL-L2350"),
    ("10.10.3.50", "44:19:B6:10:03:50", "cam-entrance", 64, [80, 554, 8000], "Hikvision DS-2CD"),
    ("10.10.3.51", "00:12:17:10:03:51", "cam-hall", 64, [80, 554], "Hikvision DS-2CD"),
    ("10.10.3.60", "B8:27:EB:10:03:60", "iot-temp-01", 64, [22, 1883], "Mosquitto MQTT"),
]

# Бір аптадан кейін: 2 жаңа құрылғы, 1 құрылғы жоғалды, 2 құрылғыда өзгеріс
DAY2_NEW = [
    ("10.10.2.66", "DC:A6:32:66:66:66", "", 64, [22, 8080], "Python http.server"),
    ("10.10.2.26", "D4:BE:D9:10:02:26", "pc-lab-03", 128, [135, 445], "Windows 11 Edu"),
]
DAY2_REMOVED = {"10.10.2.23"}           # pc-hr-01 желіде жоқ
DAY2_PORT_CHANGE = {"10.10.2.22": [135, 445, 3389, 5900]}  # RDP және VNC ашылды
DAY2_HOST_CHANGE = {"10.10.1.12": "srv-file-02"}            # атауы өзгерді

APPROVED = [d[2] for d in DEVICES] + ["pc-lab-03"]


def as_dict(d):
    ip, mac, host, ttl, ports, banner = d
    return {"ip": ip, "mac": mac, "hostname": host, "ttl": ttl,
            "open_ports": ports, "banner": banner}


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(os.path.join(here, "scans"), exist_ok=True)

    day1 = [as_dict(d) for d in DEVICES]
    day2 = []
    for d in DEVICES:
        rec = as_dict(d)
        if rec["ip"] in DAY2_REMOVED:
            continue
        if rec["ip"] in DAY2_PORT_CHANGE:
            rec["open_ports"] = DAY2_PORT_CHANGE[rec["ip"]]
        if rec["ip"] in DAY2_HOST_CHANGE:
            rec["hostname"] = DAY2_HOST_CHANGE[rec["ip"]]
        day2.append(rec)
    day2 += [as_dict(d) for d in DAY2_NEW]

    for name, data, date in (("scan_day1.json", day1, "2026-11-02"),
                             ("scan_day2.json", day2, "2026-11-09")):
        with open(os.path.join(here, "scans", name), "w", encoding="utf-8") as f:
            json.dump({"scan_date": date, "network": "10.10.0.0/16", "devices": data},
                      f, ensure_ascii=False, indent=2)

    with open(os.path.join(here, "approved.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["hostname", "owner", "location"])
        owners = {"srv": ("IT бөлімі", "Серверлік"), "pc-acc": ("Бухгалтерия", "201 каб."),
                  "pc-hr": ("Кадр бөлімі", "105 каб."), "pc-lab": ("Оқу бөлімі", "305 зертхана"),
                  "nb-": ("Әкімшілік", "Мобильді"), "prn": ("IT бөлімі", "Кеңсе"),
                  "cam": ("Күзет қызметі", "Ғимарат"), "iot": ("Шаруашылық бөлімі", "Серверлік"),
                  "core": ("IT бөлімі", "Серверлік"), "wifi": ("IT бөлімі", "Дәліз")}
        for h in APPROVED:
            owner, loc = next((v for k, v in owners.items() if h.startswith(k)), ("—", "—"))
            w.writerow([h, owner, loc])

    print("Дайын: scans/scan_day1.json (%d құрылғы), scans/scan_day2.json (%d құрылғы), approved.csv"
          % (len(day1), len(day2)))


if __name__ == "__main__":
    main()
