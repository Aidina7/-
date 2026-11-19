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

NAV = [("index.html", "Курс туралы"), ("games.html", "Ойындар"), ("cabinet.html", "Кабинет")]
FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">'
BASE_JS = ("assets/config.js", "assets/games.js", "assets/ctf-data.js", "assets/terminal.js", "assets/app.js")
UPDATED = "19.11.2026"
GH = '<svg width="20" height="20" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>'


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


SHORT = {"inventory": "Активтер инвентаризациясы", "licenses": "Лицензияларды бақылау",
         "anomaly": "Желілік аномалиялар", "sla": "SLA тексеру"}
SIDE = [("theory", "Теория"), ("video", "Бейне"), ("files", "Файлдар"), ("tasks", "Тапсырмалар"),
        ("test", "Тест"), ("ctf", "Челлендж"), ("submit", "Жұмысты тапсыру")]


def sidebar(cur):
    def a(href, text, key):
        return '<a href="%s"%s>%s</a>' % (href, ' class="on"' if key == cur else "", text)
    out = ['<div class="sb-group"><p>Бастау</p>', a("index.html", "Курс туралы", "index"),
           a("index.html#how", "Қалай жұмыс істеу керек", "-"), a("login.html#register", "Тіркелу", "login"), "</div>",
           '<div class="sb-group"><p>Практикалық жұмыстар</p>']
    for t in TOPICS:
        out.append(a(t["slug"] + ".html", "<span class=\"n\">%s</span>%s" % (t["spec"]["number"], SHORT[t["slug"]]), t["slug"]))
    out += ["</div>", '<div class="sb-group"><p>Ойындар</p>', a("games.html#sorter", "Сортировщик", "games"),
            a("games.html#ctf", "SOC-терминал", "-"), a("games.html#leaders", "Көшбасшылар", "-"), "</div>",
            '<div class="sb-group"><p>Менің нәтижелерім</p>', a("cabinet.html", "Кабинет", "cabinet"),
            a("grade.html", "Бағаны кодпен тексеру", "grade"), "</div>"]
    return "".join(out)


def page(title, body, active="", extra_head="", scripts=BASE_JS, cur=None, toc=None, wide=False):
    nav = "".join('<a href="%s"%s>%s</a>' % (h, ' class="active"' if h == active else "", n) for h, n in NAV)
    js = "".join('<script src="%s?v=%s"></script>' % (s, ver(s)) for s in scripts)
    if cur is not None:
        tocs = ""
        if toc:
            tocs = '<aside class="toc"><p>Бұл бетте</p><nav id="side-nav">%s</nav></aside>' % "".join(
                '<a href="#%s">%s</a>' % x for x in toc)
        main = ('<div class="docs%s"><aside class="sb" id="sb">%s</aside><main class="doc">%s</main>%s</div>'
                % (" has-toc" if toc else "", sidebar(cur), body, tocs))
    else:
        main = '<main class="plain%s">%s</main>' % (" wide" if wide else "", body)
    return """<!DOCTYPE html>
<html lang="kk">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s | Оқу практикасы ИС 3-1</title>
%s
<link rel="stylesheet" href="assets/style.css?v=%s">
<link rel="icon" href="data:image/svg+xml,%%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%%3E%%3Crect width='32' height='32' rx='6' fill='%%23213547'/%%3E%%3Ctext x='16' y='22' text-anchor='middle' font-family='monospace' font-weight='700' font-size='16' fill='%%2342b883'%%3E&gt;_%%3C/text%%3E%%3C/svg%%3E">
%s
</head>
<body>
<header class="top"><div class="top-in">
<button class="sb-btn" id="sb-btn" aria-label="Мәзір"><span></span><span></span><span></span></button>
<a class="brand" href="index.html"><span class="prompt">&gt;_</span> oqu-praktika <span class="grp">ИС 3-1</span></a>
<nav class="nav">%s<a class="gh" href="https://github.com/Aidina7/-" target="_blank" rel="noopener" title="GitHub">%s</a></nav>
<div class="user" id="user"></div>
</div></header>
%s
<footer class="foot"><span>КМ 06 «Ақпараттық жүйелерді автоматтандыру», Алматы экономикалық колледжі, 2026</span><span>Оқытушы: Каким А.Д. &nbsp;|&nbsp; <a href="admin.html">Оқытушыға кіру</a></span></footer>
%s
</body>
</html>
""" % (html.escape(title), FONTS, ver("assets/style.css"), extra_head, nav, GH, main, js)


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


NEWS = [
    ("19.11.2026", "№9 «Желілік аномалиялар» және №10 «SLA» тақырыптары қосылды. Әр тақырыпта бейнетүсіндірме бар."),
    ("18.11.2026", "Сайтқа тіркелу ашық. Тест нәтижелері, жұмыстар мен бағалар кабинетте сақталады."),
    ("18.11.2026", "Тест: 16 сұрақтың ішінен кездейсоқ 10 сұрақ, 3 әрекет. Ең жақсы нәтиже есептеледі."),
]


def pager(prev, nxt):
    def one(x, cls, lab):
        if not x:
            return "<span></span>"
        return '<a class="pg %s" href="%s"><small>%s</small>%s</a>' % (cls, x[0], lab, x[1])
    return '<nav class="pager">%s%s</nav>' % (one(prev, "prev", "Алдыңғы"), one(nxt, "next", "Келесі"))


def topic_page(t):
    spec = t["spec"]
    with open(os.path.join(ROOT, "content", t["slug"], "theory.html"), encoding="utf-8") as f:
        theory = f.read()
    quiz = strip_quiz(t["slug"])
    zsize = make_zip(t["starter"])
    ctfs = [c for c in CTF_IDS if c[1] == t["slug"]]
    toc = [x for x in SIDE if x[0] != "ctf" or ctfs]
    vlen = ""
    try:
        import subprocess
        secs = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                     os.path.join(ROOT, "files/video_%s.mp4" % t["slug"])], capture_output=True, text=True).stdout.strip())
        vlen = "%d:%02d" % divmod(round(secs), 60)
    except Exception:
        pass
    i = TOPICS.index(t)
    prev = (TOPICS[i - 1]["slug"] + ".html", "№%s %s" % (TOPICS[i - 1]["spec"]["number"], SHORT[TOPICS[i - 1]["slug"]])) if i else ("index.html", "Курс туралы")
    nxt = (TOPICS[i + 1]["slug"] + ".html", "№%s %s" % (TOPICS[i + 1]["spec"]["number"], SHORT[TOPICS[i + 1]["slug"]])) if i + 1 < len(TOPICS) else ("games.html", "Ойындар")
    body = """
<p class="kicker">Практикалық жұмыс №{num}</p>
<h1>{title}</h1>
<p class="lead">{lead}</p>
<table class="facts"><tr><td>Көлемі</td><td>{hours}</td></tr><tr><td>Не істейміз</td><td>теорияны оқу, бейне ({vlen}), Python скрипті, тест, есеп</td></tr>
<tr><td>Оқыту нәтижелері</td><td>{outcomes}</td></tr></table>

<h2 id="theory">Теория</h2>
<div class="theory">{theory}</div>

<h2 id="video">Бейнетүсіндірме</h2>
<div class="video" id="video-box" data-topic="{slug}"></div>
<p class="note">Бейне дыбыссыз, субтитрлері бар. Ұзақтығы {vlen}.</p>

<h2 id="files">Файлдар</h2>
<ul class="dl">
<li><a href="files/{starter}.zip" download>{starter}.zip</a> бастапқы код, {zkb} КБ</li>
<li><a href="files/{pdf}" target="_blank">{pdf}</a> тапсырмалар, басып шығаруға</li>
<li><a href="https://github.com/Aidina7/-/tree/main/starter/{starter}" target="_blank" rel="noopener">starter/{starter}</a> кодты GitHub-та қарау</li>
</ul>
<div class="tip"><b>Қалай ашу керек:</b> архивті ашып, VS Code-та <b>File → Open Folder</b> арқылы <code>{starter}</code> қалтасын ашыңыз. Іске қосу командалары <code>README.txt</code> файлында.</div>

<h2 id="tasks">Тапсырмалар</h2>
<div class="tasks">{tasks}</div>

<h2 id="test">Тест</h2>
<div id="quiz-head"></div><div id="quiz" data-topic="{slug}"></div><div class="msg" id="quiz-msg"></div>

{ctf_block}

<h2 id="submit">Жұмысты тапсыру</h2>
<p>Есепті (docx, pdf немесе zip) жүктеңіз немесе GitHub / Google Drive сілтемесін қалдырыңыз. Баға мен оқытушының пікірі <a href="cabinet.html">кабинетте</a> шығады.</p>
<form id="submit-form" class="form" data-topic="{title_attr}">
<div class="row"><label class="f">Нұсқа нөмірі<input name="variant" inputmode="numeric" placeholder="1–6"></label><label class="f">Есеп файлы (10 МБ-қа дейін)<input type="file" name="file" accept=".pdf,.docx,.doc,.zip,.png,.jpg,.jpeg,.pptx,.txt,.md,.py"></label></div>
<label class="f">немесе сілтеме<input name="link" type="url" placeholder="https://github.com/..."></label>
<label class="f">Пікір (міндетті емес)<textarea name="comment"></textarea></label>
<div><button class="btn" type="submit">Жіберу</button></div><div class="msg" id="submit-msg"></div>
</form>

<div class="edit"><a href="https://github.com/Aidina7/-/blob/main/content/{slug}/theory.html" target="_blank" rel="noopener">Қате таптыңыз ба? GitHub-та көрсетіңіз</a><span>Жаңартылды: {upd}</span></div>
{pager}
""".format(num=spec["number"], title=html.escape(spec["topic"]), title_attr=html.escape(spec["topic"], quote=True),
           lead=html.escape(t["lead"]), hours=t["hours"].replace(" · ", ", "), vlen=vlen, slug=t["slug"],
           outcomes="<br>".join("%d. %s" % (k + 1, html.escape(o)) for k, o in enumerate(t["outcomes"])),
           theory=theory, starter=t["starter"], zkb=max(1, zsize // 1024), pdf=t["pdf"], tasks=tasks_html(spec),
           upd=UPDATED, pager=pager(prev, nxt),
           ctf_block=('<h2 id="ctf">Челлендж: SOC-терминал</h2>'
                      '<p>Журнал файлдары берілген. <code>ls</code>, <code>cat</code>, <code>grep</code>, <code>sort</code>, <code>uniq</code>, <code>cut</code> командаларымен тергеу жүргізіп, жауапты <code>submit flag{...}</code> түрінде жіберіңіз. Барлық командалар: <code>help</code>.</p>'
                      '<div data-ctf="%s"></div>' % t["slug"]) if ctfs else "")
    head = "<script>window.QUIZ = %s;</script>" % json.dumps(quiz, ensure_ascii=False)
    return page(spec["topic"], body, extra_head=head, cur=t["slug"], toc=toc)


def index_page():
    rows = "".join("""<tr><td>{num}</td><td><a href="{slug}.html">{title}</a></td><td>{hours}</td><td>{ctf}</td></tr>""".format(
        slug=t["slug"], num=t["spec"]["number"], hours=t["hours"].split(" · ")[0], title=html.escape(t["spec"]["topic"]),
        ctf="бар" if any(c[1] == t["slug"] for c in CTF_IDS) else "—") for t in TOPICS)
    news = "".join('<li><b>%s</b> %s</li>' % (d, html.escape(x)) for d, x in NEWS)
    body = """
<p class="kicker">КМ 06, ОН 6.4</p>
<h1>Оқу практикасы: ақпараттық жүйелерді автоматтандыру</h1>
<p class="lead">ИС 3-1 тобына арналған материалдар. Әр практикалық жұмыста теория, бейне, Python-дағы бастапқы код, нұсқалы тапсырмалар, тест және жұмысты тапсыру формасы бар.</p>
<table class="facts"><tr><td>Топ</td><td>ИС 3-1, 3 курс</td></tr><tr><td>Оқытушы</td><td>Каким А.Д.</td></tr><tr><td>Колледж</td><td>Алматы экономикалық колледжі</td></tr></table>

<h2 id="news">Хабарландырулар</h2>
<ul class="news">%s</ul>

<h2 id="topics">Практикалық жұмыстар</h2>
<div class="table-wrap"><table class="list"><tr><th>№</th><th>Тақырып</th><th>Сағат</th><th>Челлендж</th></tr>%s</table></div>

<h2 id="how">Қалай жұмыс істеу керек</h2>
<ol class="steps">
<li><a href="login.html#register">Тіркеліңіз</a>. Логинді латынша жазыңыз, аты-жөніңізді журналдағыдай көрсетіңіз.</li>
<li>Тақырыпты ашып, алдымен «Теория» бөлімін оқыңыз, содан кейін бейнені қараңыз.</li>
<li>«Файлдар» бөлімінен бастапқы кодты жүктеп, өз нұсқаңызды орындаңыз.</li>
<li>Тест тапсырыңыз. 3 әрекет бар, ең жақсы нәтиже есептеледі.</li>
<li>Есепті «Жұмысты тапсыру» формасы арқылы жіберіңіз. Баға кабинетте шығады.</li>
</ol>

<h2 id="grading">Бағалау</h2>
<ul>
<li><b>Практикалық жұмыс</b>: 100 баллдық шкала, критерийлері әр тапсырманың соңында.</li>
<li><b>Тест</b>: 10 сұрақ, ең жақсы әрекет есептеледі.</li>
<li><b>Ойындар мен челлендждер</b>: қосымша ұпай, топ рейтингіне шығады.</li>
</ul>

<h2 id="soft">Қажетті бағдарламалар</h2>
<ul>
<li><a href="https://www.python.org/downloads/" target="_blank" rel="noopener">Python 3.10</a> немесе жоғары (орнатқанда <code>Add Python to PATH</code> белгісін қойыңыз)</li>
<li><a href="https://code.visualstudio.com/" target="_blank" rel="noopener">Visual Studio Code</a> және Python кеңейтімі</li>
</ul>
<p>Тексеру үшін терминалда: <code>python --version</code> (Mac-та <code>python3 --version</code>).</p>
%s
""" % (news, rows, pager(None, (TOPICS[0]["slug"] + ".html", "№%s %s" % (TOPICS[0]["spec"]["number"], SHORT[TOPICS[0]["slug"]]))))
    toc = [("news", "Хабарландырулар"), ("topics", "Практикалық жұмыстар"), ("how", "Қалай жұмыс істеу керек"),
           ("grading", "Бағалау"), ("soft", "Бағдарламалар")]
    return page("Курс туралы", body, active="index.html", cur="index", toc=toc)


def login_page():
    body = """
<div class="auth" id="auth">
<h1>Кіру</h1>
<div class="tabs"><button data-t="login" class="active">Кіру</button><button data-t="register">Тіркелу</button></div>
<form id="f-login" class="form">
<label class="f">Логин<input name="login" autocomplete="username" required></label>
<label class="f">Құпиясөз<input name="password" type="password" autocomplete="current-password" required></label>
<div><button class="btn" type="submit">Кіру</button></div><div class="msg" id="m-login"></div>
<p class="note">Құпиясөзді ұмытсаңыз, оқытушыға айтыңыз, ол жаңасын береді.</p>
</form>
<form id="f-reg" class="form" style="display:none">
<label class="f">Логин <small>латын әріптері, сан, _ . - (мысалы: asanov.ali)</small><input name="login" autocomplete="username" required></label>
<label class="f">Аты-жөні <small>тегі және аты, журналдағыдай</small><input name="name" autocomplete="name" required></label>
<label class="f">Топ<select name="group"></select></label>
<div class="row"><label class="f">Құпиясөз <small>кемінде 6 таңба</small><input name="password" type="password" autocomplete="new-password" minlength="6" required></label>
<label class="f">Қайталаңыз<input name="password2" type="password" autocomplete="new-password" minlength="6" required></label></div>
<div><button class="btn" type="submit">Тіркелу</button></div><div class="msg" id="m-reg"></div>
</form>
</div>"""
    return page("Кіру", body)


def cabinet_page():
    body = """
<h1>Жеке кабинет</h1><p class="lead" id="hello"></p>
<div id="cabinet"></div>"""
    return page("Кабинет", body, active="cabinet.html", cur="cabinet")


def games_page():
    opts = "".join('<option value="sort:%s">Сортировщик: %s</option>' % (k, v) for k, v in DECK_NAMES) + \
           "".join('<option value="ctf:%s">SOC-терминал: %s</option>' % (c[0], html.escape(c[2])) for c in CTF_IDS)
    body = """
<h1>Ойындар</h1>
<p class="lead">Ұпайлар кабинетке және көшбасшылар кестесіне жазылады. Алдымен <a href="login.html">кіріңіз</a>.</p>
<h2 id="sorter">Сортировщик</h2>
<p>75 секунд ішінде карточкаларды дұрыс санатқа жіберіңіз. Пернетақтадағы 1–4 сандарымен де ойнауға болады.</p>
<div class="deck-pick" data-pick></div><div data-sorter="all"></div>
<h2 id="ctf">SOC-терминал</h2>
<p>Әр челлендж нақты инцидентке ұқсас тергеу. <code>help</code> командалар тізімі, <code>hint</code> кеңес (ұпай 30%%-ға азаяды), <code>submit flag{...}</code> жауап жіберу.</p><div data-ctf="all"></div>
<h2 id="leaders">Көшбасшылар</h2>
<div class="bar"><select id="board-game"><option value="">Жалпы рейтинг (барлық ойын)</option>%s</select></div><div id="board"></div>""" % opts
    return page("Ойындар", body, active="games.html", cur="games")


def grade_page():
    body = """
<h1>Бағаны кодпен тексеру</h1>
<p class="lead">Жұмысты тіркелмей жіберген болсаңыз, алған кодыңызды енгізіңіз. Тіркелген болсаңыз, барлық бағалар <a href="cabinet.html">кабинетте</a>.</p>
<form id="grade-form" class="form" style="max-width:360px"><label class="f">Тексеру коды<input name="code" maxlength="6" placeholder="K7M2QX" style="text-transform:uppercase;font-family:var(--mono);letter-spacing:.1em"></label>
<div><button class="btn" type="submit">Тексеру</button></div><div class="msg" id="grade-msg"></div></form>"""
    return page("Бағамды тексеру", body, cur="grade")


def admin_page():
    body = """
<h1>Оқытушы панелі</h1>
<div id="login" style="display:none" class="auth"><form id="login-form" class="form">
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
</div>
<div class="modal-bg" id="modal"><div class="modal" id="modal-body"></div></div>"""
    return page("Оқытушы панелі", body, extra_head='<meta name="robots" content="noindex">',
                scripts=BASE_JS + ("assets/admin.js",), wide=True)


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
