"""Оқу желісінің трафик метрикаларын жасайды (NetFlow/sFlow жинақтауышының экспортына ұқсас).

Әр 5 минут сайын әр хост үшін жиналатын метрикалар:
  bytes_out, bytes_in   — жіберілген / алынған байт
  connections           — жаңа қосылымдар саны
  dst_ports             — қосылған әртүрлі порттар саны
  dst_hosts             — қосылған әртүрлі хосттар саны
  external_mb           — сыртқы (интернет) мекенжайларға жіберілген МБ

Нәтиже:
  data/baseline.csv  — қалыпты 7 күн (2026-11-02 … 2026-11-08): профиль осыдан құрылады
  data/today.csv     — тексерілетін күн (2026-11-09): ішінде аномалиялар бар
  data/labels.csv    — «шынайы жауап»: аномалиялар қай уақытта болды (тек бағалау үшін!)

Іске қосу:  python gen_traffic.py
"""
import csv
import math
import os
import random
from datetime import datetime, timedelta

random.seed(42)
HERE = os.path.dirname(os.path.abspath(__file__))
STEP = 5  # минут

# хост: (рөлі, күндізгі орташа МБ/5мин шығыс, кіріс, қосылым)
HOSTS = {
    "srv-web-01":    ("веб-сервер", 40, 6, 300),
    "srv-db-01":     ("дерекқор", 15, 12, 60),
    "srv-file-01":   ("файлдық сервер", 20, 10, 40),
    "srv-backup-01": ("резервтік көшіру", 2, 2, 5),
    "pc-acc-01":     ("бухгалтерия", 2, 8, 25),
    "pc-acc-02":     ("бухгалтерия", 2, 8, 25),
    "pc-hr-01":      ("кадр бөлімі", 1.5, 6, 20),
    "pc-lab-05":     ("зертхана", 3, 15, 40),
    "pc-lab-07":     ("зертхана", 3, 15, 40),
    "pc-lab-09":     ("зертхана", 3, 15, 40),
    "nb-director":   ("ноутбук", 1.5, 10, 30),
    "prn-office-01": ("принтер", 0.1, 0.5, 3),
}
SERVERS = {"srv-web-01", "srv-db-01", "srv-file-01"}


def day_curve(host, minute_of_day, weekday):
    """Тәулік ішіндегі белсенділік коэффициенті 0..1."""
    h = minute_of_day / 60
    if host in SERVERS:
        base = 0.25 + 0.75 * math.exp(-((h - 13) / 4.5) ** 2)       # күндіз шың, түнде де жұмыс
    else:
        work = 1 if 8.5 <= h <= 17.5 else 0
        base = work * (0.6 + 0.4 * math.exp(-((h - 11) / 2.5) ** 2))
    if weekday >= 5:                                                   # демалыс
        base *= 0.15 if host not in SERVERS else 0.5
    return base


def sample(host, t):
    role, out_mb, in_mb, conns = HOSTS[host]
    m = t.hour * 60 + t.minute
    k = day_curve(host, m, t.weekday())
    noise = lambda: random.uniform(0.75, 1.25)
    bo = out_mb * k * noise()
    bi = in_mb * k * noise()
    cn = conns * k * noise()
    ports = 3 + 4 * k * noise() if k > 0 else 0
    hosts_n = 2 + 6 * k * noise() if k > 0 else 0
    ext = bo * (0.6 if host == "srv-web-01" else 0.2)
    if host == "srv-backup-01" and 60 <= m < 120:                      # түнгі backup — ҚАЛЫПТЫ
        bi, bo, cn, ports, hosts_n, ext = 900 * noise(), 5, 12, 2, 3, 0
    if host == "srv-backup-01" and 120 <= m < 135:                     # көшірмені бұлтқа жіберу — ҚАЛЫПТЫ
        bo, ext, cn, ports, hosts_n = 400 * noise(), 400 * noise(), 4, 1, 1
    return {"bytes_out": bo, "bytes_in": bi, "connections": cn, "dst_ports": ports,
            "dst_hosts": hosts_n, "external_mb": ext}


def inject(host, t, row, labels):
    """Бүгінгі күнге аномалиялар қосу."""
    m = t.hour * 60 + t.minute
    tag = None
    if host == "pc-lab-07" and 10 * 60 <= m < 10 * 60 + 20:             # порттарды сканерлеу
        row.update(connections=row["connections"] + random.randint(1500, 2500),
                   dst_ports=random.randint(700, 1000), dst_hosts=random.randint(150, 254))
        tag = "port_scan"
    if host == "srv-file-01" and 2 * 60 + 10 <= m < 3 * 60 + 30:         # деректерді сыртқа шығару
        x = random.uniform(250, 350)
        row.update(bytes_out=row["bytes_out"] + x, external_mb=row["external_mb"] + x, dst_hosts=row["dst_hosts"] + 1)
        tag = "exfiltration"
    if host == "srv-web-01" and 14 * 60 <= m < 14 * 60 + 25:            # DDoS
        row.update(bytes_in=row["bytes_in"] * random.uniform(25, 40),
                   connections=row["connections"] * random.uniform(30, 50))
        tag = "ddos"
    if host == "pc-acc-02" and (m < 6 * 60 or m >= 20 * 60):             # beaconing: түнде 5 минут сайын C2-ге
        row.update(connections=row["connections"] + 1, external_mb=row["external_mb"] + 0.02,
                   bytes_out=row["bytes_out"] + 0.02, dst_hosts=max(row["dst_hosts"], 1), dst_ports=max(row["dst_ports"], 1))
        tag = "beaconing"
    if host == "pc-hr-01" and 12 * 60 + 30 <= m < 12 * 60 + 45:          # үлкен файлды жүктеу — ЗИЯНСЫЗ (жалған дабыл тексеру)
        row.update(bytes_in=row["bytes_in"] + 120)
    if tag:
        labels.append({"time": t.strftime("%Y-%m-%d %H:%M"), "host": host, "type": tag})


def write(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def main():
    os.makedirs(os.path.join(HERE, "data"), exist_ok=True)
    start = datetime(2026, 11, 2)
    baseline, today, labels = [], [], []
    for day in range(8):
        for step in range(24 * 60 // STEP):
            t = start + timedelta(days=day, minutes=step * STEP)
            for host in HOSTS:
                v = sample(host, t)
                if day == 7:
                    inject(host, t, v, labels)
                row = {"time": t.strftime("%Y-%m-%d %H:%M"), "host": host}
                row.update({k: round(x, 2) if k.endswith(("out", "in", "_mb")) else int(round(x)) for k, x in v.items()})
                (today if day == 7 else baseline).append(row)
    write(os.path.join(HERE, "data", "baseline.csv"), baseline)
    write(os.path.join(HERE, "data", "today.csv"), today)
    write(os.path.join(HERE, "data", "labels.csv"), labels)
    print("Дайын: data/baseline.csv (%d жол), data/today.csv (%d жол), data/labels.csv"
          % (len(baseline), len(today)))
    print("Хосттар:", ", ".join("%s (%s)" % (h, r[0]) for h, r in HOSTS.items()))


if __name__ == "__main__":
    main()
