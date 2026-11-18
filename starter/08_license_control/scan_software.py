"""Өз компьютеріңізде орнатылған бағдарламалар тізімін жинау (түгендеу агенті).

  Windows : тізілім (registry) Uninstall кілттері
  macOS   : /Applications ішіндегі .app бумалары (Info.plist)
  Linux   : dpkg-query немесе rpm

Нәтиже installs.csv форматында: my_software.csv. Оны тексеруге болады:
  python scan_software.py
  python license_check.py --installs my_software.csv
"""
import csv
import getpass
import os
import platform
import plistlib
import socket
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))


def windows_apps():
    import winreg
    apps = {}
    roots = [(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
             (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
             (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")]
    for hive, path in roots:
        try:
            key = winreg.OpenKey(hive, path)
        except OSError:
            continue
        for i in range(winreg.QueryInfoKey(key)[0]):
            try:
                sub = winreg.OpenKey(key, winreg.EnumKey(key, i))
                name = winreg.QueryValueEx(sub, "DisplayName")[0]
                try:
                    ver = winreg.QueryValueEx(sub, "DisplayVersion")[0]
                except OSError:
                    ver = ""
                apps[name] = ver
            except OSError:
                continue
    return apps


def mac_apps():
    apps = {}
    for folder in ("/Applications", os.path.expanduser("~/Applications")):
        if not os.path.isdir(folder):
            continue
        for item in os.listdir(folder):
            if item.endswith(".app"):
                ver = ""
                try:
                    with open(os.path.join(folder, item, "Contents", "Info.plist"), "rb") as f:
                        ver = plistlib.load(f).get("CFBundleShortVersionString", "")
                except Exception:
                    pass
                apps[item[:-4]] = ver
    return apps


def linux_apps():
    try:
        out = subprocess.run(["dpkg-query", "-W", "-f=${Package}\t${Version}\n"],
                             capture_output=True, text=True, timeout=30).stdout
    except FileNotFoundError:
        out = subprocess.run(["rpm", "-qa", "--qf", "%{NAME}\t%{VERSION}\n"],
                             capture_output=True, text=True, timeout=30).stdout
    return dict(line.split("\t", 1) for line in out.splitlines() if "\t" in line)


def main():
    system = platform.system()
    apps = {"Windows": windows_apps, "Darwin": mac_apps}.get(system, linux_apps)()
    host, user = socket.gethostname(), getpass.getuser()
    out = os.path.join(HERE, "my_software.csv")
    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["hostname", "user", "software", "version", "install_date", "last_used_days"])
        for name, ver in sorted(apps.items(), key=lambda kv: kv[0].lower()):
            w.writerow([host, user, name, ver, "", 0])
    print("%s (%s): %d бағдарлама табылды -> %s" % (host, system, len(apps), out))
    for name in sorted(apps, key=str.lower)[:15]:
        print("  -", name, apps[name])
    if len(apps) > 15:
        print("  ... толық тізім файлда")


if __name__ == "__main__":
    main()
