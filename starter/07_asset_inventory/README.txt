07_asset_inventory — Активтер мен қызметтердің инвентаризациясы
================================================================

Қажет: Python 3.10+ (қосымша пакет орнатудың қажеті жоқ), VS Code.

Файлдар
  standard.json      колледждің түгендеу стандарты (міндетті өрістер, тег үлгісі, түрлер, статустар)
  oui.csv            MAC мекенжайының алғашқы 3 байты -> өндіруші (OUI кестесі)
  gen_network.py     оқу желісінің сканерлеу нәтижелерін жасайды (scans/, approved.csv)
  discover.py        жабдықтарды автоматты анықтау: сканерлеу -> CMDB (csv + json)
  validate.py        CMDB-ні стандартқа сәйкестікке тексеру
  diff_inventory.py  екі түгендеуді салыстыру -> changes.md
  report.py          HTML есеп -> inventory_report.html
  collect_local.py   өз компьютеріңіздің нақты түгендеу жазбасы -> local_asset.json

Жылдам старт
  python gen_network.py
  python discover.py --scan scans/scan_day1.json --out cmdb_day1.csv
  python discover.py --scan scans/scan_day2.json --out cmdb_day2.csv --prev cmdb_day1.csv
  python validate.py cmdb_day2.csv --today 2026-11-10
  python diff_inventory.py cmdb_day1.csv cmdb_day2.csv
  python report.py cmdb_day2.csv
  python collect_local.py --owner "Аты-жөніңіз" --location "Кабинет"

Маңызды: нақты желіні тек иесінің жазбаша рұқсатымен сканерлеуге болады.
Сабақта желі сканерлеу нәтижелері scans/ қалтасындағы файлдарда берілген.
Бәрін басынан бастау үшін: python gen_network.py
