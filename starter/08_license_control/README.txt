08_license_control — Лицензиялар мен бағдарламаларды бақылау жүйесі
=====================================================================

Қажет: Python 3.10+ (қосымша пакет орнатудың қажеті жоқ), VS Code.

Файлдар
  licenses.json      сатып алынған лицензиялар (entitlements), тегін және тыйым салынған бағдарламалар
  catalog.csv        бағдарламаның «шикі» атауы -> өнім коды (нормализация каталогы)
  gen_installs.py    25 компьютердегі орнатылған бағдарламалар (installs.csv) және 1С сессиялары (sessions_1c.csv)
  license_check.py   лицензиялар сәйкестігін тексеру -> license_report.md, license_report.csv
  scan_software.py   өз компьютеріңіздегі нақты бағдарламалар тізімі -> my_software.csv

Жылдам старт
  python gen_installs.py
  python license_check.py
  python license_check.py --today 2026-11-30 --warn-days 60
  python scan_software.py
  python license_check.py --installs my_software.csv

license_check.py шығу коды: 0 — сәйкес, 2 — сәйкес емес (CI/CD немесе cron тексеруіне ыңғайлы).
Бәрін басынан бастау үшін: python gen_installs.py
