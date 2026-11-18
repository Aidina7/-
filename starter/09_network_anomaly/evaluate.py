"""Анықтау сапасын бағалау: data/labels.csv («шынайы жауап») бойынша.

  TP — аномалия болған және табылған аралық
  FP — аномалия жоқ, бірақ дабыл берілген (жалған дабыл)
  FN — аномалия болған, бірақ табылмаған (өткізіп алу)
  Precision = TP / (TP + FP) — дабылдардың қаншасы шын
  Recall    = TP / (TP + FN) — аномалиялардың қаншасы табылды
  F1        = 2·P·R / (P + R)

Іске қосу:
  python evaluate.py                    -> threshold, zscore, rules, all әдістерін салыстыру
  python evaluate.py --k 3 --k 6        -> z-score шегін өзгерту
"""
import argparse
import csv
import json
import os
import subprocess
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))


def load_pairs(path):
    with open(path, encoding="utf-8") as f:
        return {(r["host"], r["time"]) for r in csv.DictReader(f)}


def score(pred, truth):
    tp = len(pred & truth)
    fp = len(pred - truth)
    fn = len(truth - pred)
    p = tp / (tp + fp) if tp + fp else 0
    r = tp / (tp + fn) if tp + fn else 0
    f1 = 2 * p * r / (p + r) if p + r else 0
    return tp, fp, fn, p, r, f1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=float, action="append", help="z-score шегі (бірнеше рет беруге болады)")
    args = ap.parse_args()
    ks = args.k or [4.0]

    labels_path = os.path.join(HERE, "data", "labels.csv")
    truth = load_pairs(labels_path)
    by_type = defaultdict(set)
    with open(labels_path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            by_type[r["type"]].add((r["host"], r["time"]))

    if not os.path.exists(os.path.join(HERE, "profiles.json")):
        subprocess.run([sys.executable, os.path.join(HERE, "profile.py")], check=True, capture_output=True)

    runs = [("threshold", None), ("rules", None), ("all", 4.0)] + [("zscore", k) for k in ks]
    print("%-14s %5s %5s %5s %10s %8s %6s   табылған шабуыл түрлері" % ("әдіс", "TP", "FP", "FN", "Precision", "Recall", "F1"))
    for method, k in runs:
        out = os.path.join(HERE, "_eval_%s.csv" % method)
        cmd = [sys.executable, os.path.join(HERE, "detect.py"), "--method", method, "--out", out]
        if k:
            cmd += ["--k", str(k)]
        subprocess.run(cmd, check=True, capture_output=True)
        pred = load_pairs(out)
        tp, fp, fn, p, r, f1 = score(pred, truth)
        types = ", ".join("%s %d%%" % (t, round(100 * len(pred & s) / len(s))) for t, s in sorted(by_type.items()))
        name = method if not k or method != "zscore" else "zscore k=%g" % k
        print("%-14s %5d %5d %5d %10.2f %8.2f %6.2f   %s" % (name, tp, fp, fn, p, r, f1, types))
        os.remove(out)
    print("\nЕскерту: бағалау 5 минуттық аралықтар бойынша жүргізіледі; labels.csv тек бағалау үшін — анықтауда қолданылмайды.")


if __name__ == "__main__":
    main()
