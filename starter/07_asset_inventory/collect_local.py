"""Өз компьютеріңіздің түгендеу жазбасын автоматты жинау (агент тәсілі).

Тек стандартты Python кітапханасы қолданылады; Windows, macOS және Linux-та жұмыс істейді.
Скрипт жинайды: атауы, ОЖ, процессор, жедел жад, диск, IP, MAC, сериялық нөмір,
модель, жергілікті ашық порттар (қызметтер).

Іске қосу:
  python collect_local.py                 -> local_asset.json
  python collect_local.py --owner "Асанов Ә." --location "305 каб."
"""
import argparse
import ctypes
import json
import os
import platform
import shutil
import socket
import subprocess
import uuid
from datetime import date, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
COMMON_PORTS = {22: "ssh", 80: "http", 135: "msrpc", 443: "https", 445: "smb", 1433: "mssql",
                3000: "dev-server", 3306: "mysql", 3389: "rdp", 5000: "flask/upnp",
                5432: "postgresql", 5900: "vnc", 6379: "redis", 8000: "http-alt", 8080: "http-proxy",
                27017: "mongodb"}


def run(cmd):
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=8, shell=isinstance(cmd, str))
        return out.stdout.strip()
    except Exception:
        return ""


def ram_gb():
    system = platform.system()
    try:
        if system == "Windows":
            class MEM(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            m = MEM()
            m.dwLength = ctypes.sizeof(MEM)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            return round(m.ullTotalPhys / 1024 ** 3, 1)
        if system == "Darwin":
            return round(int(run(["sysctl", "-n", "hw.memsize"])) / 1024 ** 3, 1)
        return round(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1024 ** 3, 1)
    except Exception:
        return None


def serial_and_model():
    system = platform.system()
    if system == "Windows":
        ps = 'powershell -NoProfile -Command "(Get-CimInstance Win32_BIOS).SerialNumber; (Get-CimInstance Win32_ComputerSystem).Model"'
        parts = run(ps).splitlines()
        return (parts[0] if parts else ""), (parts[1] if len(parts) > 1 else "")
    if system == "Darwin":
        info = run(["system_profiler", "SPHardwareDataType"])
        serial = model = ""
        for line in info.splitlines():
            if "Serial Number" in line:
                serial = line.split(":", 1)[1].strip()
            if "Model Name" in line:
                model = line.split(":", 1)[1].strip()
        return serial, model
    serial = run("cat /sys/class/dmi/id/product_serial 2>/dev/null")
    model = run("cat /sys/class/dmi/id/product_name 2>/dev/null")
    return serial, model


def local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))   # пакет жіберілмейді, тек маршрут таңдалады
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def open_local_ports():
    found = []
    for port, name in COMMON_PORTS.items():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.2)
            if s.connect_ex(("127.0.0.1", port)) == 0:
                found.append("%s(%d)" % (name, port))
    return found


def mac_address():
    node = uuid.getnode()
    return ":".join("%02X" % ((node >> i) & 0xFF) for i in range(40, -1, -8))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--owner", default="")
    ap.add_argument("--location", default="")
    ap.add_argument("--out", default=os.path.join(HERE, "local_asset.json"))
    args = ap.parse_args()

    system = platform.system()
    typ = "NB" if system == "Darwin" else "PC"
    disk = shutil.disk_usage(os.path.abspath(os.sep))
    serial, model = serial_and_model()
    asset = {
        "asset_tag": "AEC-%s-%s" % (typ, "9" + mac_address().replace(":", "")[-3:].translate(
            str.maketrans("ABCDEF", "012345"))),
        "type": typ,
        "hostname": socket.gethostname(),
        "ip": local_ip(),
        "mac": mac_address(),
        "vendor": "",
        "model": model or "белгісіз",
        "serial_number": serial or "белгісіз",
        "os": "%s %s" % (system, platform.release()),
        "os_version": platform.version(),
        "cpu": platform.processor() or platform.machine(),
        "cpu_cores": os.cpu_count(),
        "ram_gb": ram_gb(),
        "disk_total_gb": round(disk.total / 1024 ** 3, 1),
        "disk_free_gb": round(disk.free / 1024 ** 3, 1),
        "services": open_local_ports(),
        "role": "жұмыс станциясы",
        "owner": args.owner,
        "location": args.location,
        "status": "in_use",
        "last_seen": date.today().isoformat(),
        "collected_at": datetime.now().isoformat(timespec="seconds"),
        "collected_by": "collect_local.py (агент)",
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(asset, f, ensure_ascii=False, indent=2)
    width = max(len(k) for k in asset)
    for k, v in asset.items():
        print("%s : %s" % (k.ljust(width), ", ".join(v) if isinstance(v, list) else v))
    print("\nСақталды:", args.out)


if __name__ == "__main__":
    main()
