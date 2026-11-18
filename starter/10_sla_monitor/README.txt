10_sla_monitor — Қызмет көрсету сапасын автоматты тексеру (SLA)
==============================================================

Қажет: Python 3.10+ (қосымша пакет қажет емес), VS Code, екі терминал.

Файлдар
  services.json    қызметтер, SLO (ішкі мақсат), SLA (келісімшарт), ескерту ережелері (burn rate)
  gen_metrics.py   30 күндік метрикалар (сұраулар, 5xx/4xx қателер, жауап уақыты гистограммасы) -> data/metrics.csv
  sli.py           SLI есептеу, SLO/SLA тексеру, қателер бюджеті, burn rate -> sla_report.md / .html
  test_server.py   тексеруге арналған жергілікті қызмет (http://127.0.0.1:8085), қателер мен баяулықты басқаруға болады
  check_sla.py     үздіксіз тексеру (синтетикалық мониторинг) -> probes.csv, ескертулер

Жылдам старт
  python gen_metrics.py
  python sli.py
  python sli.py --service portal --daily
  python sli.py --html
  # бөлек терминалда:  python test_server.py --errors 0.05 --slow 0.1
  python check_sla.py --interval 2 --count 30
  # тоқтауды имитациялау: браузерде http://127.0.0.1:8085/admin/break , қалпына келтіру: /admin/fix

Шығу коды: 0 — бәрі қалыпты, 2 — SLO бұзылды / ескерту бар (cron, CI үшін ыңғайлы).
