"""Қызметтердің 30 күндік метрикаларын жасайды (Prometheus / веб-сервер журналының жинақтамасына ұқсас).

Әр 5 минут сайын әр қызмет үшін:
  requests        — сұраулар саны
  errors_5xx      — сервер қателері (SLI-ге кіреді)
  errors_4xx      — клиент қателері (404, 401: әдетте SLI-ге кірмейді)
  le_100 … le_1000, gt_1000 — жауап уақыты гистограммасы (неше сұрау ≤100 мс, ≤300 мс, ≤1000 мс, >1000 мс)

Нәтиже: data/metrics.csv  (2026-10-10 00:00 … 2026-11-08 23:55)
Іске қосу: python gen_metrics.py
"""
import csv
import math
import os
import random
from datetime import datetime, timedelta

random.seed(7)
HERE = os.path.dirname(os.path.abspath(__file__))
START = datetime(2026, 10, 10)
DAYS = 30
BASE = {"portal": 900, "journal_api": 1500, "lms": 600}   # күндізгі сұраулар / 5 мин


def load(service, t):
    h = t.hour + t.minute / 60
    k = 0.08 + 0.92 * math.exp(-((h - 12) / 3.8) ** 2)
    if t.weekday() >= 5:
        k *= 0.3
    return max(1, int(BASE[service] * k * random.uniform(0.85, 1.15)))


def split_latency(n, slow_share, very_slow_share):
    gt = int(n * very_slow_share)
    le1000 = int(n * slow_share)
    rest = n - gt - le1000
    le100 = int(rest * random.uniform(0.55, 0.7))
    le300 = rest - le100
    return le100, le300, le1000, gt


def main():
    os.makedirs(os.path.join(HERE, "data"), exist_ok=True)
    rows = []
    for step in range(DAYS * 288):
        t = START + timedelta(minutes=5 * step)
        day = (t - START).days + 1
        hm = t.hour * 60 + t.minute
        for s in BASE:
            n = load(s, t)
            err = sum(1 for _ in range(n) if random.random() < 0.0008)
            e4 = int(n * random.uniform(0.01, 0.03))
            slow, very = random.uniform(0.01, 0.025), random.uniform(0.0, 0.005)
            if s == "lms":
                slow, very = random.uniform(0.04, 0.07), random.uniform(0.005, 0.01)
            # --- инциденттер ---
            if s == "portal" and day == 12 and 10 * 60 <= hm < 11 * 60 + 30:      # толық тоқтау 90 мин
                err = n
            if s == "portal" and day == 26 and 15 * 60 <= hm < 15 * 60 + 40:      # жартылай: 30% қате
                err = int(n * 0.3)
            if s == "journal_api" and day == 20 and 9 * 60 <= hm < 15 * 60:       # ДҚ баяу: жауап уақыты өсті
                slow, very = 0.35, 0.10
            if s == "journal_api" and day == 21 and 11 * 60 <= hm < 11 * 60 + 25:  # деплойдан кейінгі қателер
                err = int(n * 0.2)
            if s == "lms" and day == 30 and hm >= 21 * 60:                         # дәл қазір: қателер 20%
                err = int(n * 0.2)
            le100, le300, le1000, gt = split_latency(n, slow, very)
            rows.append({"time": t.strftime("%Y-%m-%d %H:%M"), "service": s, "requests": n,
                         "errors_5xx": min(err, n), "errors_4xx": e4,
                         "le_100": le100, "le_300": le300, "le_1000": le1000, "gt_1000": gt})
    with open(os.path.join(HERE, "data", "metrics.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("Дайын: data/metrics.csv (%d жол, %d күн, қызметтер: %s)" % (len(rows), DAYS, ", ".join(BASE)))


if __name__ == "__main__":
    main()
