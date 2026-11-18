"""Ұйымның компьютерлеріндегі орнатылған бағдарламалар тізімін жасайды (оқу деректері).

Шын мәнінде бұл тізімді түгендеу агенті (SCCM, Intune, GLPI, OCS Inventory т.б.) жинайды.
Сабақта сол агенттің экспорты ретінде installs.csv және 1С сессиялар журналы
sessions_1c.csv қолданылады.

Іске қосу:  python gen_installs.py
"""
import csv
import os
import random

random.seed(2026)
HERE = os.path.dirname(os.path.abspath(__file__))

HOSTS = (
    [("pc-acc-%02d" % i, "buh%d" % i, "Бухгалтерия") for i in range(1, 4)] +
    [("pc-hr-01", "kadr1", "Кадр бөлімі"), ("pc-office-01", "secretary", "Қабылдау")] +
    [("pc-lab-%02d" % i, "student%02d" % i, "Зертхана 305") for i in range(1, 15)] +
    [("pc-design-%02d" % i, "design%d" % i, "Дизайн зертханасы") for i in range(1, 5)] +
    [("nb-director", "director", "Әкімшілік"), ("nb-zavuch", "zavuch", "Әкімшілік")]
)
RAW = {
    "office2021": "Microsoft Office Standard 2021",
    "m365": "Microsoft 365 Apps for business",
    "win": "Windows 11 Pro",
    "kas": "Kaspersky Endpoint Security 12",
    "1c": "1С:Бухгалтерия для Казахстана 3.0",
    "ps": "Adobe Photoshop 2025",
    "acad": "AutoCAD LT 2025",
    "pyc": "PyCharm Professional 2025.2",
    "vsc": "Visual Studio Code",
    "py": "Python 3.12.6",
    "git": "Git for Windows 2.47",
    "7z": "7-Zip 24.08",
    "rar": "WinRAR 7.01",
    "chrome": "Google Chrome",
    "tv": "TeamViewer 15",
    "lo": "LibreOffice 24.8",
}


def days(a, b):
    return random.randint(a, b)


def main():
    rows = []

    def add(host, user, key, last_used):
        rows.append({"hostname": host, "user": user, "software": RAW[key],
                     "version": RAW[key].split()[-1], "install_date": "2025-%02d-%02d" % (days(1, 12), days(1, 28)),
                     "last_used_days": last_used})

    for host, user, dept in HOSTS:
        mac = host.startswith("nb-")
        if not mac:
            add(host, user, "win", 0)
        add(host, user, "chrome", days(0, 3))
        if dept == "Бухгалтерия":
            add(host, user, "office2021", days(0, 5))
            add(host, user, "1c", days(0, 2))
            add(host, user, "rar", days(10, 200))
        if dept in ("Кадр бөлімі", "Қабылдау"):
            add(host, user, "office2021", days(0, 5))
            add(host, user, "rar", days(30, 300))
        if dept == "Зертхана 305":
            add(host, user, "vsc", days(0, 7))
            add(host, user, "py", days(0, 7))
            add(host, user, "git", days(0, 14))
            add(host, user, "pyc", days(0, 30))
            add(host, user, "7z", days(5, 60))
            if host <= "pc-lab-10":
                add(host, user, "office2021", days(1, 40))
            else:
                add(host, user, "lo", days(1, 40))
        if dept == "Дизайн зертханасы":
            add(host, user, "office2021", days(1, 30))
            add(host, user, "ps", days(0, 10))
            if host in ("pc-design-01", "pc-design-02"):
                add(host, user, "acad", 0 if host == "pc-design-01" else 140)
        if mac:
            add(host, user, "m365", days(0, 3))
            add(host, user, "tv", days(1, 20))
        if not mac and host not in ("pc-lab-13", "pc-lab-14"):   # 2 компьютерде антивирус жоқ!
            add(host, user, "kas", 0)

    # Әдейі жасалған «олқылықтар»
    extra = [
        ("pc-acc-02", "buh2", "TeamViewer 15", "15", 3),
        ("pc-lab-07", "student07", "uTorrent 3.6", "3.6", 1),
        ("pc-lab-12", "student12", "KMSAuto Net 1.8", "1.8", 40),
        ("pc-hr-01", "kadr1", "Microsoft 365 Apps for business", "365", 2),
        ("pc-office-01", "secretary", "Microsoft 365 Apps for business", "365", 1),
        ("pc-acc-01", "buh1", "Microsoft 365 Apps for business", "365", 0),
        ("pc-acc-03", "buh3", "Microsoft 365 Apps for business", "365", 4),
        ("pc-lab-09", "student09", "Minecraft Launcher", "2.4", 0),
        ("pc-lab-03", "student03", "AnyDesk 9", "9", 12),
    ]
    for host, user, sw, ver, last in extra:
        rows.append({"hostname": host, "user": user, "software": sw, "version": ver,
                     "install_date": "2026-%02d-%02d" % (days(1, 10), days(1, 28)), "last_used_days": last})

    with open(os.path.join(HERE, "installs.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    # 1С бір мезгілдегі қосылымдар журналы (5 жұмыс күні, сағат сайын)
    with open(os.path.join(HERE, "sessions_1c.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["timestamp", "active_sessions"])
        for d in range(17, 22):
            for h in range(9, 19):
                n = random.choice([1, 2, 2, 3, 3])
                if (d, h) in ((19, 11), (19, 12), (21, 16)):   # ай соңындағы есеп — шың
                    n = 4
                w.writerow(["2026-11-%02d %02d:00" % (d, h), n])

    print("Дайын: installs.csv (%d жазба, %d компьютер), sessions_1c.csv" % (len(rows), len(HOSTS)))


if __name__ == "__main__":
    main()
