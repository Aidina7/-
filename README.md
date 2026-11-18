# Оқу практикасы — студенттерге арналған сайт

**Алматы экономикалық колледжі · ИС 3-1 · КМ 06, ОН 6.4** · оқытушы: Каким А.Д.

Сайт: https://aidina7.github.io/-/

## Тақырыптар
| № | Тақырып | Бет | Бастапқы файлдар |
|---|---|---|---|
| 7 | Активтер мен қызметтердің инвентаризациясын жасау | `inventory.html` | `starter/07_asset_inventory` |
| 8 | Лицензиялар мен бағдарламаларды бақылау жүйесі | `licenses.html` | `starter/08_license_control` |
| 9 | Желілік аномалияларды автоматты түрде анықтау | `anomaly.html` | `starter/09_network_anomaly` |
| 10 | Қызмет көрсету сапасын автоматты тексеру (SLA) | `sla.html` | `starter/10_sla_monitor` |

## Құрылымы
- `content/<тақырып>/theory.html` — түсіндірме, `quiz.json` — тест
- `tools/tasks_content.py` — практикалық тапсырмалар (Word құжатымен бірдей мәтін)
- `tools/build.py` — беттерді жасайды: `python tools/build.py`
- `assets/config.js` — баптаулар: API мекенжайы, топтар, бейнелер
- `backend/Code.gs` — Google Apps Script (жұмыстарды қабылдау, бағалау); орнату: `backend/ОРНАТУ.md`
- `admin.html` — оқытушы панелі (құпиясөзбен)
