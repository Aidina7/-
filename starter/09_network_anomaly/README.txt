09_network_anomaly — Желілік аномалияларды автоматты түрде анықтау
===================================================================

Қажет: Python 3.10+ (қосымша пакет қажет емес), VS Code, браузер.

Файлдар
  gen_traffic.py   трафик метрикалары: data/baseline.csv (7 қалыпты күн), data/today.csv (тексерілетін күн), data/labels.csv
  profile.py       трафик профилі (хост × күн түрі × сағат: mean, std, p95, max) -> profiles.json
  detect.py        аномалияларды анықтау: threshold / zscore / rules / all -> anomalies.csv, incidents.csv
  evaluate.py      әдістерді салыстыру: Precision, Recall, F1
  report.py        HTML есеп графиктермен -> anomaly_report.html

Жылдам старт
  python gen_traffic.py
  python profile.py --show srv-web-01
  python detect.py --method threshold
  python detect.py --method zscore --k 4
  python detect.py --method rules
  python evaluate.py
  python detect.py --method all
  python report.py

Ескерту: data/labels.csv — «шынайы жауаптар», оны тек evaluate.py қолданады.
Нақты желі трафигін тек ұйымның рұқсатымен жинауға және талдауға болады.
