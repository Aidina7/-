"""Сайт беттерін жасайды: python tools/build.py

Мазмұн көздері:
  content/<slug>/theory.html  — түсіндірме
  content/<slug>/quiz.json    — тест
  tools/tasks_content.py      — практикалық тапсырмалар (Word құжатымен бірдей)
  starter/<папка>             — бастапқы файлдар (zip болып жиналады)
"""
import html
import json
import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import tasks_content as T  # noqa: E402

TOPICS = [
    {"slug": "inventory", "spec": T.INV, "hours": "6 сағат · 3 сабақ", "starter": "07_asset_inventory",
     "pdf": "praktikalyk_7_inventory.pdf",
     "lead": "IT-активтерді түгендеу стандарттары, желідегі жабдықтарды автоматты анықтау және инвентаризация скрипті.",
     "outcomes": ["IT-активтерді түгендеу стандарттарын сипаттайды", "Жабдықтарды автоматты анықтауды түсіндіреді", "Инвентаризация жасайтын скрипт жазады"]},
    {"slug": "licenses", "spec": T.LIC, "hours": "2 сағат · 1 сабақ", "starter": "08_license_control",
     "pdf": "praktikalyk_8_licenses.pdf",
     "lead": "Бағдарлама лицензияларының түрлері мен шектеулері, лицензияларды бақылау (SAM) және есепке алу скрипті.",
     "outcomes": ["ПО лицензияларының шектеулерін сипаттайды", "Софт-лицензияларды бақылауды түсіндіреді", "Лицензияларды есепке алатын скрипт жазады"]},
    {"slug": "anomaly", "spec": T.NET, "hours": "6 сағат · 3 сабақ", "starter": "09_network_anomaly",
     "pdf": "praktikalyk_9_anomaly.pdf",
     "lead": "Желілік трафик профилі, аномалия түрлері (сканерлеу, DDoS, деректерді шығару, beaconing) және оларды автоматты табатын сценарий.",
     "outcomes": ["Желілік трафик профильдерін сипаттайды", "Трафиктегі аномалияларды сараптауды түсіндіреді", "Аномалияларды табатын сценарий әзірлейді"]},
    {"slug": "sla", "spec": T.SLA, "hours": "6 сағат · 3 сабақ", "starter": "10_sla_monitor",
     "pdf": "praktikalyk_10_sla.pdf",
     "lead": "SLA, SLO, SLI, жауап уақыты мен қателерді есептеу, қателер бюджеті, burn rate және қызметтерді үздіксіз тексеру.",
     "outcomes": ["SLA/SLO/SLI метрикаларын сипаттайды", "Сервис жауабы мен қателерді есептеуді түсіндіреді", "SLA-ны үздіксіз тексеретін скрипт жазады"]},
]

NAV = [("index.html", "Басты бет"), ("games.html", "Ойындар"), ("cabinet.html", "Кабинет")]
FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Onest:wght@400;500;600;700&family=Unbounded:wght@500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">'
BASE_JS = ("assets/config.js", "assets/games.js", "assets/ctf-data.js", "assets/terminal.js", "assets/app.js")


def inline(text):
    t = html.escape(text, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
    return t


def ver(rel):
    """Кэшті жаңарту үшін файлдың қысқа хэші."""
    import hashlib
    with open(os.path.join(ROOT, rel), "rb") as f:
        return hashlib.sha1(f.read()).hexdigest()[:8]


LOGO = ('<svg width="34" height="34" viewBox="0 0 34 34" aria-hidden="true"><rect width="34" height="34" rx="11" fill="#5b45ff"/>'
        '<path d="M10 23 L17 11 L24 23 Z" fill="none" stroke="#fff" stroke-width="2" stroke-linejoin="round" opacity=".55"/>'
        '<circle cx="17" cy="11" r="3.4" fill="#fff"/><circle cx="10" cy="23" r="3.4" fill="#fff"/><circle cx="24" cy="23" r="3.4" fill="#f2a516"/></svg>')

ICONS = {
    "inventory": '<svg width="44" height="44" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="8" y="7" width="32" height="11" rx="3"/><rect x="8" y="22" width="32" height="11" rx="3"/><path d="M14 12.5h6M14 27.5h6"/><circle cx="33" cy="12.5" r="1.5" fill="currentColor"/><circle cx="33" cy="27.5" r="1.5" fill="currentColor"/><path d="M24 33v6M14 41h20"/></svg>',
    "licenses": '<svg width="44" height="44" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 6h17l9 9v27H12z"/><path d="M29 6v9h9"/><path d="M18 29l4 4 9-9"/></svg>',
    "anomaly": '<svg width="44" height="44" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 34h7l4-6 4 4 5-22 5 30 4-10h9"/><path d="M5 42h38" opacity=".4"/></svg>',
    "sla": '<svg width="44" height="44" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 34a16 16 0 1 1 32 0"/><path d="M24 34l8-10"/><circle cx="24" cy="34" r="3" fill="currentColor"/><path d="M12 20l2 2M24 14v3M36 20l-2 2"/></svg>',
}
COLORS = {"inventory": "#0fa58f", "licenses": "#e0479e", "anomaly": "#ff5a4e", "sla": "#f2a516"}
SHORT = {"inventory": "Инвентаризация", "licenses": "Лицензиялар", "anomaly": "Аномалиялар", "sla": "SLA мониторинг"}


def page(title, body, active="", extra_head="", scripts=BASE_JS, body_cls="", top_cls=""):
    nav = "".join('<a href="%s"%s>%s</a>' % (h, ' class="active"' if h == active else "", n) for h, n in NAV)
    js = "".join('<script src="%s?v=%s"></script>' % (s, ver(s)) for s in scripts)
    return """<!DOCTYPE html>
<html lang="kk">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s — Оқу практикасы, ИС 3-1</title>
%s
<link rel="stylesheet" href="assets/style.css?v=%s">
<link rel="icon" href="data:image/svg+xml,%s">
%s
</head>
<body class="%s">
<header class="topbar %s" id="topbar"><div class="wrap">
<a class="brand" href="index.html">%s<span>Оқу практикасы</span></a>
<nav class="nav">%s</nav>
<div class="user" id="user"></div>
</div></header>
%s
<footer><div class="wrap"><span>Алматы экономикалық колледжі, КМ 06 «Ақпараттық жүйелерді автоматтандыру». Оқытушы: Каким А.Д.</span><span><a href="https://github.com/Aidina7/-" target="_blank" rel="noopener">GitHub</a> &nbsp; <a href="admin.html">Оқытушыға</a></span></div></footer>
%s
</body>
</html>
""" % (html.escape(title), FONTS, ver("assets/style.css"), LOGO.replace('"', "'").replace("#", "%23").replace("<", "%3C").replace(">", "%3E"),
       extra_head, body_cls, top_cls, LOGO, nav, body, js)



def tasks_html(spec):
    out = ['<table class="task-info">']
    for k, v in spec["info"]:
        v = "<br>".join(inline(x) for x in v) if isinstance(v, list) else inline(v)
        out.append("<tr><td>%s</td><td>%s</td></tr>" % (inline(k), v))
    out.append("</table>")
    for blk in spec["blocks"]:
        kind = blk[0]
        if kind == "h1":
            out.append("<h3>%s</h3>" % inline(blk[1]))
        elif kind == "h2":
            out.append("<h4>%s</h4>" % inline(blk[1]))
        elif kind == "p" or kind == "scale":
            out.append("<p>%s</p>" % inline(blk[1]))
        elif kind == "note":
            out.append('<div class="callout">%s</div>' % inline(blk[1]))
        elif kind == "report":
            out.append('<p class="report-note"><b>Есепке:</b> %s</p>' % inline(blk[1]))
        elif kind in ("ol", "ul"):
            out.append("<%s>%s</%s>" % (kind, "".join("<li>%s</li>" % inline(i) for i in blk[1]), kind))
        elif kind == "table":
            head = "".join("<th>%s</th>" % inline(h) for h in blk[2])
            rows = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % inline(c) for c in r) for r in blk[3])
            out.append('<div class="table-wrap"><table><tr>%s</tr>%s</table></div>' % (head, rows))
        elif kind == "grade":
            rows = "".join("<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % tuple(inline(c) for c in r) for r in blk[1])
            out.append('<div class="table-wrap"><table><tr><th>№</th><th>Критерий</th><th>Ұпай</th></tr>%s'
                       '<tr><td></td><td><b>Барлығы</b></td><td><b>100</b></td></tr></table></div>' % rows)
    return "\n".join(out)


def make_zip(folder):
    src = os.path.join(ROOT, "starter", folder)
    dst = os.path.join(ROOT, "files", folder + ".zip")
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
        for base, dirs, files in os.walk(src):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for f in sorted(files):
                full = os.path.join(base, f)
                z.write(full, os.path.join(folder, os.path.relpath(full, src)))
            if not files and base != src:
                z.writestr(os.path.join(folder, os.path.relpath(base, src)) + "/", "")
    return os.path.getsize(dst)


def strip_quiz(slug):
    """Жеке банктен (жауаптарымен) ашық quiz.json жасау; QUIZ_BANK болмаса — бар файлды қолдану."""
    pub = os.path.join(ROOT, "content", slug, "quiz.json")
    bank_path = os.environ.get("QUIZ_BANK")
    if bank_path and os.path.exists(bank_path):
        with open(bank_path, encoding="utf-8") as f:
            bank = json.load(f)[slug]
        with open(pub, "w", encoding="utf-8") as f:
            json.dump([{"id": q["id"], "q": q["q"], "o": q["o"]} for q in bank], f, ensure_ascii=False, indent=1)
    with open(pub, encoding="utf-8") as f:
        return json.load(f)


SIDE = [("theory", "Теория"), ("video", "Бейне"), ("files", "Файлдар"), ("tasks", "Тапсырмалар"),
        ("test", "Тест"), ("ctf", "Челлендж"), ("submit", "Жұмысты тапсыру")]

NEWS = [
    ("18.11.2026", "№9 «Желілік аномалиялар» және №10 «SLA» тақырыптары қосылды. Әр тақырыпқа бейнетүсіндірме жүктелді."),
    ("18.11.2026", "Сайтқа тіркелу ашық. Тест нәтижелері, тапсырылған жұмыстар мен бағалар жеке кабинетте сақталады."),
    ("18.11.2026", "Тест: әр тақырыпта 16 сұрақтан кездейсоқ 10 сұрақ, 3 әрекет. Ең жақсы нәтиже есептеледі."),
]


def netmap():
    pos = {"inventory": (118, 96), "licenses": (402, 96), "anomaly": (118, 330), "sla": (402, 330)}
    hub = (260, 213)
    devs = [(30, 210), (190, 30), (330, 30), (490, 210), (190, 410), (330, 410)]
    links, packets, nodes = [], [], []
    for i, (slug, (x, y)) in enumerate(pos.items()):
        pid = "p" + slug
        links.append('<path id="%s" class="lnk" d="M%d %d L%d %d"/>' % (pid, hub[0], hub[1], x, y))
        packets.append('<circle r="5" fill="%s"><animateMotion dur="%.1fs" begin="-%.1fs" repeatCount="indefinite" keyPoints="1;0" keyTimes="0;1" calcMode="linear"><mpath href="#%s"/></animateMotion></circle>'
                       % (COLORS[slug], 2.6 + i * .35, i * .6, pid))
        t = next(t for t in TOPICS if t["slug"] == slug)
        icon = ICONS[slug].replace('width="44" height="44"', 'x="%d" y="%d" width="34" height="34"' % (x - 17, y - 17)).replace("currentColor", "#fff")
        nodes.append('<a href="%s.html" class="node" aria-label="%s"><circle class="ring" cx="%d" cy="%d" r="44" fill="none" stroke="%s" stroke-width="2" opacity=".5"/>'
                     '<circle cx="%d" cy="%d" r="36" fill="%s"/>%s<text x="%d" y="%d" text-anchor="middle">%s</text><text class="sub" x="%d" y="%d" text-anchor="middle">№%s · %s</text></a>'
                     % (slug, html.escape(t["spec"]["topic"]), x, y, COLORS[slug], x, y, COLORS[slug], icon, x, y + 66, SHORT[slug], x, y + 84, t["spec"]["number"], t["hours"].split(" · ")[0]))
    for j, (dx, dy) in enumerate(devs):
        near = min(pos.values(), key=lambda p: (p[0] - dx) ** 2 + (p[1] - dy) ** 2)
        links.append('<path class="lnk" d="M%d %d L%d %d" stroke-dasharray="3 6"/>' % (dx, dy, near[0], near[1]))
        nodes.append('<rect class="dev" x="%d" y="%d" width="18" height="14" rx="4"/>' % (dx - 9, dy - 7))
    hubsvg = ('<circle cx="%d" cy="%d" r="30" fill="#5b45ff"/><circle cx="%d" cy="%d" r="40" fill="none" stroke="#5b45ff" stroke-width="2" opacity=".45"/>'
              '<text x="%d" y="%d" text-anchor="middle" style="font:700 13px var(--disp);fill:#fff">ИС 3-1</text>' % (hub + hub + (hub[0], hub[1] + 5)))
    return ('<svg class="netmap" id="netmap" viewBox="0 0 520 440" role="img" aria-label="Тақырыптар картасы">%s%s%s<g>%s</g></svg>'
            % ("".join(links), "".join(packets), hubsvg, "".join(nodes)))


def topic_page(t):
    spec = t["spec"]
    with open(os.path.join(ROOT, "content", t["slug"], "theory.html"), encoding="utf-8") as f:
        theory = f.read()
    quiz = strip_quiz(t["slug"])
    zsize = make_zip(t["starter"])
    ctfs = [c for c in CTF_IDS if c[1] == t["slug"]]
    side = "".join('<a href="#%s">%s</a>' % (a, n) for a, n in SIDE if a != "ctf" or ctfs)
    vfile = "files/video_%s.mp4" % t["slug"]
    vlen = "—"
    try:
        import subprocess
        secs = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                     os.path.join(ROOT, vfile)], capture_output=True, text=True).stdout.strip())
        vlen = "%d:%02d" % divmod(round(secs), 60)
    except Exception:
        pass
    body = """
<div class="thead"><div class="wrap">
<div><div class="crumbs"><a href="index.html">Басты бет</a> / <span class="num">Практикалық жұмыс №{num}</span></div>
<h1>{title}</h1><p>{lead}</p>
<div class="chips">{outcomes}</div></div>
<div class="bigpic">{icon}</div>
</div></div>
<div class="wrap"><div class="layout">
<aside class="side"><nav id="side-nav">{side}</nav>
<div class="meta"><div><span>Көлемі</span>{hours}</div><div><span>Бейне</span>{vlen}</div><div><span>Тест</span>10 / {nq} сұрақ</div><div><span>Тіл</span>Python 3.10+</div></div></aside>
<main>
<div class="block" id="theory"><h2>Теория</h2>{theory}</div>

<div class="block" id="video"><h2>Бейнетүсіндірме</h2><div class="video" id="video-box" data-topic="{slug}"></div>
<div class="video-note">Қысқа шолу, субтитрлері бар ({vlen}). Толығырақ — «Теория» бөлімінде.</div></div>

<div class="block" id="files"><h2>Файлдар</h2>
<div class="files">
<a class="file" href="files/{starter}.zip" download><span class="ext">ZIP</span><span><b>Бастапқы код</b><span>{starter}.zip, {zkb} КБ</span></span></a>
<a class="file" href="files/{pdf}" target="_blank"><span class="ext">PDF</span><span><b>Тапсырмалар №{num}</b><span>басып шығаруға</span></span></a>
<a class="file" href="https://github.com/Aidina7/-/tree/main/starter/{starter}" target="_blank" rel="noopener"><span class="ext">GIT</span><span><b>GitHub-та қарау</b><span>кодты онлайн оқу</span></span></a>
</div>
<p>Архивті ашып, VS Code-та <b>File → Open Folder</b> арқылы <code>{starter}</code> қалтасын ашыңыз. Іске қосу командалары <code>README.txt</code> файлында.</p>
</div>

<div class="block tasks" id="tasks"><h2>Практикалық тапсырмалар</h2>{tasks}</div>

<div class="block" id="test"><h2>Тест</h2>
<div id="quiz-head"></div><div id="quiz" data-topic="{slug}"></div><div class="msg" id="quiz-msg" style="margin-top:12px"></div></div>

{ctf_block}

<div class="block" id="submit"><h2>Жұмысты тапсыру</h2>
<p>Есепті (docx, pdf немесе zip) жүктеңіз немесе GitHub / Google Drive сілтемесін қалдырыңыз. Баға мен оқытушының пікірі кабинетте шығады.</p>
<form id="submit-form" class="form" data-topic="{title_attr}">
<div class="row"><label class="f">Нұсқа нөмірі<input name="variant" inputmode="numeric" placeholder="1–6"></label><label class="f">Есеп файлы <small>10 МБ-қа дейін</small><input type="file" name="file" accept=".pdf,.docx,.doc,.zip,.png,.jpg,.jpeg,.pptx,.txt,.md,.py"></label></div>
<label class="f">немесе сілтеме<input name="link" type="url" placeholder="https://github.com/..."></label>
<label class="f">Пікір <small>міндетті емес</small><textarea name="comment"></textarea></label>
<div><button class="btn" type="submit">Жұмысты жіберу</button></div><div class="msg" id="submit-msg"></div>
</form></div>
</main></div></div>
""".format(num=spec["number"], title=html.escape(spec["topic"]), title_attr=html.escape(spec["topic"], quote=True),
           lead=html.escape(t["lead"]), hours=t["hours"].split(" · ")[0], vlen=vlen, nq=len(quiz), slug=t["slug"], side=side,
           icon=ICONS[t["slug"]], outcomes="".join('<span class="chip">%s</span>' % html.escape(o) for o in t["outcomes"]),
           theory=theory, starter=t["starter"], zkb=max(1, zsize // 1024), pdf=t["pdf"], tasks=tasks_html(spec),
           ctf_block=('<div class="block" id="ctf"><h2>Челлендж: SOC-терминал</h2>'
                      '<p>Журнал файлдары берілген. Терминалда <code>ls</code>, <code>cat</code>, <code>grep</code>, <code>sort</code>, <code>uniq</code>, <code>cut</code> командаларымен тергеу жүргізіп, жауапты <code>submit flag{...}</code> түрінде жіберіңіз. Командалар тізімі: <code>help</code>.</p>'
                      '<div data-ctf="%s"></div></div>' % t["slug"]) if ctfs else "")
    head = "<script>window.QUIZ = %s;</script>" % json.dumps(quiz, ensure_ascii=False)
    return page(spec["topic"], body, extra_head=head, body_cls="t-" + t["slug"])


def index_page():
    cards = "".join("""<a class="topic t-{slug}" href="{slug}.html"><div class="pic">{icon}</div><div>
<div class="num">Практикалық жұмыс №{num}</div><h3>{title}</h3><p>{lead}</p>
<div class="foot"><span class="chip tc">{hours}</span><span class="chip">теория</span><span class="chip">бейне</span><span class="chip">тест</span>{ctf}</div></div></a>""".format(
        slug=t["slug"], num=t["spec"]["number"], hours=t["hours"], title=html.escape(t["spec"]["topic"]), icon=ICONS[t["slug"]],
        lead=html.escape(t["lead"]), ctf='<span class="chip">челлендж</span>' if any(c[1] == t["slug"] for c in CTF_IDS) else "") for t in TOPICS)
    news = "".join('<li><time>%s</time><span>%s</span></li>' % (d, html.escape(x)) for d, x in NEWS)
    body = """
<section class="hero"><div class="wrap">
<div>
<h1>Ақпараттық жүйелерді автоматтандыру: оқу практикасы</h1>
<p class="lead">Құрылғыларды түгендеу, лицензияларды бақылау, желідегі шабуылдарды табу және сервис сапасын өлшеу. Әр тақырыпта теория, бейне, Python-дағы бастапқы код, тест және тергеу ойыны бар.</p>
<div class="who-line">ИС 3-1 тобы, КМ 06 модулі. Оқытушы — Каким А.Д.</div>
<div class="cta"><a class="btn light" href="login.html#register">Тіркелу</a><a class="btn line" href="#topics">Тақырыптарды көру</a></div>
</div>
<div>%s</div>
</div></section>

<div class="wrap">
<section class="sec" id="topics"><div class="sec-h"><div><h2>Тақырыптар</h2><p>Рет-ретімен орындаңыз: әр жұмыс алдыңғы тақырыптың скриптіне сүйенеді.</p></div></div>
<div class="topics">%s</div></section>

<section class="sec" id="games"><div class="sec-h"><div><h2>Ойындар</h2><p>Ұпайлар кабинетке және топтың рейтингіне жазылады.</p></div><a class="btn ghost" href="games.html">Барлық ойындар</a></div>
<div class="games-band">
<a class="game" href="games.html#sorter"><div class="shot sort"><div class="pc b1">MAC 00:1A:2B…</div><div class="pc b2">port 9100 open</div><div class="pc">TTL=128, 3389 ашық</div>
<div class="bins"><span>Принтер</span><span class="hit">Windows ДК</span><span>Linux сервер</span><span>Камера</span></div></div>
<h3>Сортировщик</h3><p>75 секунд ішінде карточкаларды дұрыс санатқа жіберіңіз. Қатарынан дұрыс жауап бонус береді.</p></a>
<a class="game" href="games.html#ctf"><div class="shot term-shot"><b>student@soc</b>:~$ grep "Failed" auth.log | cut -d' ' -f11 \\
  | sort | uniq -c | sort -rn | head -3
    412 <i>185.220.101.7</i>
     38 10.10.2.14
      3 10.10.2.31
<b>student@soc</b>:~$ submit flag{...}</div>
<h3>SOC-терминал</h3><p>Журналдарды grep, sort, uniq арқылы тергеп, инцидентті табыңыз: бөтен құрылғы, SSH брутфорс, деректердің жылыстауы.</p></a>
</div></section>

<section class="sec"><div class="two">
<div class="panel"><h2>Хабарландырулар</h2><ul class="news">%s</ul></div>
<div class="panel"><h2>Қалай бастау керек</h2><ol class="steps">
<li><span><a href="login.html#register">Тіркеліңіз</a>: логин, аты-жөні, топ.</span></li>
<li>Тақырыпты ашып, теорияны оқып, бейнені қараңыз.</li>
<li>Бастапқы кодты жүктеп, өз нұсқаңызды орындаңыз.</li>
<li>Тест тапсырыңыз — 3 әрекет бар.</li>
<li>Есепті жіберіңіз, баға кабинетте шығады.</li></ol>
<div class="tools">Қажет: <a href="https://code.visualstudio.com/" target="_blank" rel="noopener">VS Code</a> және <a href="https://www.python.org/downloads/" target="_blank" rel="noopener">Python 3.10+</a>. Қосымша пакеттер керек емес.</div></div>
</div></section>
</div>
""" % (netmap(), cards, news)
    return page("Басты бет", body, active="index.html", top_cls="dark")


def login_page():
    body = """
<div class="wrap"><div class="auth-wrap"><div class="auth-side"><h1>Кабинетке кіріңіз</h1><p>Тест нәтижелері, тапсырылған жұмыстар, бағалар мен ойын ұпайлары бір жерде сақталады.</p></div><div class="auth-box" id="auth">
<div class="tabs"><button data-t="login" class="active">Кіру</button><button data-t="register">Тіркелу</button></div>
<form id="f-login" class="form">
<label class="f">Логин<input name="login" autocomplete="username" required></label>
<label class="f">Құпиясөз<input name="password" type="password" autocomplete="current-password" required></label>
<div><button class="btn" type="submit">Кіру</button></div><div class="msg" id="m-login"></div>
<p class="muted" style="font-size:13px;margin:0">Құпиясөзді ұмытсаңыз, оқытушыға айтыңыз — ол жаңасын береді.</p>
</form>
<form id="f-reg" class="form" style="display:none">
<label class="f">Логин <small>латын әріптері, сан, _ . - (мысалы: asanov.ali)</small><input name="login" autocomplete="username" required></label>
<label class="f">Аты-жөні <small>тегі және аты, журналдағыдай</small><input name="name" autocomplete="name" required></label>
<label class="f">Топ<select name="group"></select></label>
<div class="row"><label class="f">Құпиясөз <small>кемінде 6 таңба</small><input name="password" type="password" autocomplete="new-password" minlength="6" required></label>
<label class="f">Қайталаңыз<input name="password2" type="password" autocomplete="new-password" minlength="6" required></label></div>
<div><button class="btn" type="submit">Тіркелу</button></div><div class="msg" id="m-reg"></div>
</form>
</div></div></div>"""
    return page("Кіру", body)


def cabinet_page():
    body = """
<div class="wrap page">
<div class="page-head"><div class="crumbs"><a href="index.html">Басты бет</a> / Кабинет</div><h1>Жеке кабинет</h1><p id="hello"></p></div>
<div id="cabinet"></div>
</div>"""
    return page("Кабинет", body, active="cabinet.html")


def games_page():
    opts = "".join('<option value="sort:%s">Сортировщик: %s</option>' % (k, v) for k, v in DECK_NAMES) + \
           "".join('<option value="ctf:%s">SOC-терминал: %s</option>' % (c[0], html.escape(c[2])) for c in CTF_IDS)
    body = """
<div class="wrap page">
<div class="page-head"><div class="crumbs"><a href="index.html">Басты бет</a> / Ойындар</div><h1>Ойындар</h1>
<p>Ұпайлар кабинетке және көшбасшылар кестесіне жазылады (алдымен <a href="login.html">кіріңіз</a>).</p></div>
<div class="block" id="sorter"><h2>Сортировщик</h2><div class="deck-pick" data-pick></div><div data-sorter="all"></div></div>
<div class="block" id="ctf"><h2>SOC-терминал</h2>
<p>Әр челлендж — нақты инцидентке ұқсас тергеу. <code>help</code> — командалар, <code>hint</code> — кеңес (ұпай 30%%-ға азаяды), <code>submit flag{...}</code> — жауап.</p><div data-ctf="all"></div></div>
<div class="block" id="leaders"><h2>Көшбасшылар</h2>
<div class="bar"><select id="board-game"><option value="">Жалпы рейтинг (барлық ойын)</option>%s</select></div><div id="board"></div></div>
</div>""" % opts
    return page("Ойындар", body, active="games.html")


def grade_page():
    body = """
<div class="wrap"><div class="auth-box solo"><h2 style="margin-bottom:16px">Бағаны кодпен тексеру</h2>
<form id="grade-form" class="form"><label class="f">Тексеру коды<input name="code" maxlength="6" placeholder="K7M2QX" style="text-transform:uppercase;font-family:var(--mono);letter-spacing:.1em"></label>
<div><button class="btn" type="submit">Тексеру</button></div><div class="msg" id="grade-msg"></div></form>
<p class="muted" style="font-size:13px">Тіркелген болсаңыз, барлық бағалар <a href="cabinet.html">кабинетте</a>.</p></div></div>"""
    return page("Бағамды тексеру", body)


def admin_page():
    body = """
<div class="wrap page">
<div class="page-head"><h1>Оқытушы панелі</h1></div>
<div id="login" style="display:none" class="auth-box solo"><form id="login-form" class="form">
<label class="f">Оқытушы құпиясөзі<input id="pw" type="password" autocomplete="current-password"></label>
<div><button class="btn" type="submit">Кіру</button></div><div class="msg" id="login-msg"></div></form></div>
<div id="panel" style="display:none">
<div class="stats" id="stats"></div>
<div class="tabs"><button class="active" data-tab="students">Студенттер</button><button data-tab="subs">Жұмыстар</button><button data-tab="tests">Тесттер</button><button data-tab="games">Ойындар</button></div>
<div class="bar">
<select id="f-group"></select><select id="f-topic"><option value="">барлық тақырыптар</option></select>
<select id="f-status"><option value="">барлық күйлер</option><option>Тексерілмеген</option><option>Тексерілді</option><option>Қайта тапсыру</option></select>
<input id="f-q" placeholder="аты немесе логин">
<button class="btn small ghost" id="reload">Жаңарту</button><button class="btn small ghost" id="export">Excel (CSV)</button><button class="btn small ghost" id="logout-admin">Шығу</button>
</div>
<div id="list"></div>
</div></div>
<div class="modal-bg" id="modal"><div class="modal" id="modal-body"></div></div>"""
    return page("Оқытушы панелі", body, extra_head='<meta name="robots" content="noindex">',
                scripts=BASE_JS + ("assets/admin.js",))


def load_ctf_ids():
    txt = open(os.path.join(ROOT, "assets", "ctf-data.js"), encoding="utf-8").read()
    data = json.loads(txt[txt.index("["):txt.rindex("]") + 1])
    return [(c["id"], c["topic"], c["title"]) for c in data]


CTF_IDS = []
DECK_NAMES = [("devices", "Құрылғыны таны"), ("licenses", "Лицензия аудиті"), ("soc", "SOC кезекшісі"), ("sre", "SRE шешімі")]


def main():
    global CTF_IDS
    CTF_IDS = load_ctf_ids()
    pages = {"index.html": index_page(), "login.html": login_page(), "cabinet.html": cabinet_page(),
             "games.html": games_page(), "grade.html": grade_page(), "admin.html": admin_page()}
    for t in TOPICS:
        pages[t["slug"] + ".html"] = topic_page(t)
    for name, content in pages.items():
        with open(os.path.join(ROOT, name), "w", encoding="utf-8") as f:
            f.write(content)
        print("жасалды:", name)


if __name__ == "__main__":
    main()
