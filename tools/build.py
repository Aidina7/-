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

NAV = [("index.html", "тақырыптар"), ("games.html", "ойындар"), ("cabinet.html", "кабинет")]
FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700;800&display=swap" rel="stylesheet">'
BASE_JS = ("assets/config.js", "assets/games.js", "assets/ctf-data.js", "assets/terminal.js", "assets/app.js")
UPDATED = "19.11.2026"


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
        ("test", "Тест"), ("ctf", "CTF"), ("submit", "Тапсыру")]


def page(title, body, active="", extra_head="", scripts=BASE_JS, wide=False):
    nav = "".join('<a href="%s"%s>%s</a>' % (h, ' class="active"' if h == active else "", n) for h, n in NAV)
    js = "".join('<script src="%s?v=%s"></script>' % (s, ver(s)) for s in scripts)
    return """<!DOCTYPE html>
<html lang="kk">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#ffffff">
<title>%s | ИС 3-1 оқу практикасы</title>
%s
<link rel="stylesheet" href="assets/style.css?v=%s">
<link rel="icon" href="data:image/svg+xml,%%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%%3E%%3Crect width='32' height='32' rx='6' fill='%%230d1520'/%%3E%%3Ctext x='16' y='22' text-anchor='middle' font-family='monospace' font-weight='700' font-size='16' fill='%%2339e58c'%%3E&gt;_%%3C/text%%3E%%3C/svg%%3E">
%s
</head>
<body>
<header class="top"><div class="wrap top-in">
<a class="brand" href="index.html"><span class="u">student</span><span class="at">@</span><span class="h">is31</span><span class="p">:~$</span><i class="cur"></i></a>
<nav class="nav">%s</nav>
<div class="user" id="user"></div>
</div></header>
<main class="%s">
%s
</main>
<footer class="foot"><div class="wrap"><span># КМ 06 «Ақпараттық жүйелерді автоматтандыру», Алматы экономикалық колледжі</span><span>оқытушы: Каким А.Д. &nbsp;|&nbsp; <a href="https://github.com/Aidina7/-" target="_blank" rel="noopener">github</a> &nbsp;|&nbsp; <a href="admin.html">admin</a></span></div></footer>
%s
</body>
</html>
""" % (html.escape(title), FONTS, ver("assets/style.css"), extra_head, nav, "wrap wide" if wide else "wrap", body, js)


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
    ("19.11", "№9 «Желілік аномалиялар» және №10 «SLA» ашылды. Әр тақырыпта бейне бар."),
    ("18.11", "Тіркелу ашық. Тест, жұмыстар мен бағалар кабинетте сақталады."),
    ("18.11", "Тест: 16 сұрақтан кездейсоқ 10, 3 әрекет. Ең жақсы нәтиже есептеледі."),
]


def topic_page(t):
    spec = t["spec"]
    with open(os.path.join(ROOT, "content", t["slug"], "theory.html"), encoding="utf-8") as f:
        theory = f.read()
    quiz = strip_quiz(t["slug"])
    zsize = make_zip(t["starter"])
    ctfs = [c for c in CTF_IDS if c[1] == t["slug"]]
    tabs = [x for x in SIDE if x[0] != "ctf" or ctfs]
    vlen = ""
    try:
        import subprocess
        secs = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                     os.path.join(ROOT, "files/video_%s.mp4" % t["slug"])], capture_output=True, text=True).stdout.strip())
        vlen = "%d:%02d" % divmod(round(secs), 60)
    except Exception:
        pass
    folder = "%02d_%s" % (int(spec["number"]), t["slug"])
    i = TOPICS.index(t)
    other = "".join('<a href="%s.html"%s>%s</a>' % (x["slug"], ' class="on"' if x is t else "", "%02d" % int(x["spec"]["number"])) for x in TOPICS)

    def nxt(k):
        if k + 1 < len(tabs):
            return '<div class="next"><a class="btn ghost" href="#%s">Келесі қадам: %s</a></div>' % (tabs[k + 1][0], tabs[k + 1][1])
        if i + 1 < len(TOPICS):
            return '<div class="next"><a class="btn ghost" href="%s.html">Келесі тақырып: №%s</a></div>' % (TOPICS[i + 1]["slug"], TOPICS[i + 1]["spec"]["number"])
        return ""
    k = {a: n for n, (a, _) in enumerate(tabs)}
    tabbar = "".join('<a href="#%s" data-tab="%s"><span>%d</span>%s</a>' % (a, a, n + 1, lab) for n, (a, lab) in enumerate(tabs))
    body = """
<div class="path"><a href="index.html">~/practicum</a>/<b>{folder}</b><span class="jump">{other}</span></div>
<div class="thead">
<div><p class="tag-n">ПРАКТИКАЛЫҚ ЖҰМЫС №{num}</p>
<h1>{title}</h1>
<p class="lead">{lead}</p></div>
<ul class="meta"><li><span>уақыты</span>{hours}</li><li><span>бейне</span>{vlen}</li><li><span>тест</span>10 сұрақ, 3 әрекет</li><li><span>тіл</span>Python 3.10+</li></ul>
</div>
<div class="goals"><span>Сабақтан кейін сен:</span>{outcomes}</div>

<nav class="tabs-t" id="tabs">{tabbar}</nav>

<section class="pane" id="theory"><div class="theory">{theory}</div>{n_theory}</section>

<section class="pane" id="video"><div class="video" id="video-box" data-topic="{slug}"></div>
<p class="note">Бейне дыбыссыз, субтитрлері бар ({vlen}).</p>{n_video}</section>

<section class="pane" id="files">
<div class="files">
<a class="file" href="files/{starter}.zip" download><b>{starter}.zip</b><span>бастапқы код, {zkb} КБ</span><em>жүктеу</em></a>
<a class="file" href="files/{pdf}" target="_blank"><b>{pdf}</b><span>тапсырмалар PDF</span><em>ашу</em></a>
<a class="file" href="https://github.com/Aidina7/-/tree/main/starter/{starter}" target="_blank" rel="noopener"><b>starter/{starter}</b><span>кодты GitHub-та қарау</span><em>ашу</em></a>
</div>
<div class="howto"><p>Қалай іске қосу керек:</p>
<pre><code><span class="c"># 1. архивті ашып, VS Code-та File → Open Folder → {starter}</span>
<span class="c"># 2. VS Code ішінде терминал ашыңыз: Terminal → New Terminal</span>
<span class="c"># 3. README.txt ішіндегі командаларды орындаңыз, мысалы:</span>
python main.py        <span class="c"># Mac-та: python3 main.py</span></code></pre></div>
{n_files}</section>

<section class="pane" id="tasks"><div class="tasks">{tasks}</div>{n_tasks}</section>

<section class="pane" id="test"><div id="quiz-head"></div><div id="quiz" data-topic="{slug}"></div><div class="msg" id="quiz-msg"></div>{n_test}</section>

{ctf_block}

<section class="pane" id="submit">
<p>Есепті (docx, pdf немесе zip) жүктеңіз немесе GitHub / Google Drive сілтемесін қалдырыңыз. Баға мен оқытушының пікірі <a href="cabinet.html">кабинетте</a> шығады.</p>
<form id="submit-form" class="form" data-topic="{title_attr}">
<div class="row"><label class="f">Нұсқа нөмірі<input name="variant" inputmode="numeric" placeholder="1–6"></label><label class="f">Есеп файлы (10 МБ-қа дейін)<input type="file" name="file" accept=".pdf,.docx,.doc,.zip,.png,.jpg,.jpeg,.pptx,.txt,.md,.py"></label></div>
<label class="f">немесе сілтеме<input name="link" type="url" placeholder="https://github.com/..."></label>
<label class="f">Пікір (міндетті емес)<textarea name="comment"></textarea></label>
<div><button class="btn" type="submit">Жұмысты жіберу</button></div><div class="msg" id="submit-msg"></div>
</form>{n_submit}</section>
""".format(num=spec["number"], folder=folder, other=other, title=html.escape(spec["topic"]),
           title_attr=html.escape(spec["topic"], quote=True), lead=html.escape(t["lead"]),
           hours=t["hours"].split(" · ")[0], vlen=vlen, slug=t["slug"], tabbar=tabbar,
           outcomes="".join("<b>%s</b>" % html.escape(o) for o in t["outcomes"]),
           theory=theory, starter=t["starter"], zkb=max(1, zsize // 1024), pdf=t["pdf"], tasks=tasks_html(spec),
           n_theory=nxt(k["theory"]), n_video=nxt(k["video"]), n_files=nxt(k["files"]), n_tasks=nxt(k["tasks"]),
           n_test=nxt(k["test"]), n_submit=nxt(k["submit"]),
           ctf_block=('<section class="pane" id="ctf"><p>Журнал файлдары берілген. <code>ls</code>, <code>cat</code>, <code>grep</code>, <code>sort</code>, <code>uniq</code>, <code>cut</code> командаларымен тергеу жүргізіп, жауапты <code>submit flag{...}</code> түрінде жіберіңіз. Командалар тізімі: <code>help</code>.</p>'
                      '<div data-ctf="%s"></div>%s</section>' % (t["slug"], nxt(k["ctf"]))) if ctfs else "")
    head = "<script>window.QUIZ = %s;</script>" % json.dumps(quiz, ensure_ascii=False)
    return page(spec["topic"], body, extra_head=head)


BANNER = """ ███    ███   █   █       ████   ████    ███   █   █  █████  ███  █   █   ███
█   █  █   █  █   █       █   █  █   █  █   █  █  █     █     █   █  █   █   █
█   █  █   █  █   █  ███  ████   ████   █████  ███      █     █   ███    █████
█   █  █  ██  █   █       █      █  █   █   █  █  █     █     █   █  █   █   █
 ███    ████   ███        █      █   █  █   █  █   █    █    ███  █   █  █   █"""


def index_page():
    rows = "".join("""<a class="ls" href="{slug}.html"><span class="perm">drwxr-xr-x</span><span class="dir">{folder}/</span><span class="nm">{title}</span><span class="hr">{hours}</span><span class="go">ашу</span></a>""".format(
        slug=t["slug"], folder="%02d_%s" % (int(t["spec"]["number"]), t["slug"]), hours=t["hours"].split(" · ")[0].replace(" сағат", " сағ"),
        title=html.escape(t["spec"]["topic"])) for t in TOPICS)
    news = "".join('<li><span class="d">[%s]</span> %s</li>' % (d, html.escape(x)) for d, x in NEWS)
    body = """
<section class="hero">
<pre class="banner" aria-hidden="true">%s</pre>
<h1>КМ 06 оқу практикасы: <span>ақпараттық жүйелерді автоматтандыру</span></h1>
<p class="lead">ИС 3-1 тобы. Әр тақырыпта теория, бейне, Python коды, тест және журналдарды тергейтін CTF-челлендж бар.</p>
<div class="cta"><a class="btn" href="login.html#register">Тіркелу</a><a class="btn ghost" href="#ls">Тақырыптарды ашу</a></div>
</section>

<section class="win" id="ls">
<div class="win-bar"><i></i><i></i><i></i><span>student@is31: ~/practicum</span></div>
<div class="win-body">
<p class="cmd"><span class="ps">student@is31:~/practicum$</span> ls -l</p>
%s
<p class="cmd"><span class="ps">student@is31:~/practicum$</span> <i class="cur"></i></p>
</div></section>

<div class="grid3">
<section class="box"><h2>Қалай бастау керек</h2>
<ol class="todo">
<li><a href="login.html#register">Тіркел</a>: логин латынша, аты-жөнің журналдағыдай.</li>
<li>Тақырыпты аш. Қадамдар ретімен жүр: теория, бейне, файлдар, тапсырма.</li>
<li>Тест тапсыр. 3 әрекет бар.</li>
<li>CTF челленджін шеш, рейтингке ұпай жина.</li>
<li>Есепті жібер. Баға кабинетте шығады.</li>
</ol></section>
<section class="box"><h2>cat news.log</h2><ul class="log">%s</ul></section>
<section class="box"><h2>Рейтинг</h2><div id="board" class="board-mini"></div><a class="more" href="games.html#leaders">толық рейтинг</a></section>
</div>

<section class="box games-row">
<h2>Ойындар</h2>
<div class="g2">
<a class="game" href="games.html#ctf"><b>SOC-терминал</b><span>Журналдардан шабуылдаушыны тап: бөтен құрылғы, SSH брутфорс, сканерлеу, деректердің жылыстауы. 6 челлендж.</span></a>
<a class="game" href="games.html#sorter"><b>Сортировщик</b><span>75 секундта карточкаларды санатқа жібер. 4 колода: құрылғылар, лицензиялар, SOC, SRE.</span></a>
</div></section>
""" % (html.escape(BANNER), rows, news)
    return page("Тақырыптар", body, active="index.html")


def login_page():
    body = """
<div class="auth" id="auth">
<p class="cmd"><span class="ps">$</span> sudo login</p>
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
<div class="path"><a href="index.html">~</a>/<b>cabinet</b></div>
<h1>Жеке кабинет</h1><p class="lead" id="hello"></p>
<div id="cabinet"></div>"""
    return page("Кабинет", body, active="cabinet.html")


def games_page():
    opts = "".join('<option value="sort:%s">Сортировщик: %s</option>' % (k, v) for k, v in DECK_NAMES) + \
           "".join('<option value="ctf:%s">SOC-терминал: %s</option>' % (c[0], html.escape(c[2])) for c in CTF_IDS)
    body = """
<div class="path"><a href="index.html">~</a>/<b>games</b></div>
<h1>Ойындар</h1>
<p class="lead">Ұпайлар кабинетке және рейтингке жазылады. Алдымен <a href="login.html">кіріңіз</a>.</p>
<nav class="tabs-t static"><a href="#ctf"><span>1</span>SOC-терминал</a><a href="#sorter"><span>2</span>Сортировщик</a><a href="#leaders"><span>3</span>Рейтинг</a></nav>
<section class="sec" id="ctf"><h2>SOC-терминал</h2>
<p>Әр челлендж нақты инцидентке ұқсас тергеу. <code>help</code> командалар тізімі, <code>hint</code> кеңес (ұпай 30%%-ға азаяды), <code>submit flag{...}</code> жауап.</p><div data-ctf="all"></div></section>
<section class="sec" id="sorter"><h2>Сортировщик</h2>
<p>75 секунд ішінде карточкаларды дұрыс санатқа жіберіңіз. 1–4 пернелерімен де ойнауға болады.</p>
<div class="deck-pick" data-pick></div><div data-sorter="all"></div></section>
<section class="sec" id="leaders"><h2>Рейтинг</h2>
<div class="bar"><select id="board-game"><option value="">Жалпы рейтинг (барлық ойын)</option>%s</select></div><div id="board"></div></section>""" % opts
    return page("Ойындар", body, active="games.html")


def grade_page():
    body = """
<div class="auth">
<p class="cmd"><span class="ps">$</span> grade --check</p>
<h1>Бағаны кодпен тексеру</h1>
<p>Тіркелген болсаңыз, барлық бағалар <a href="cabinet.html">кабинетте</a>.</p>
<form id="grade-form" class="form"><label class="f">Тексеру коды<input name="code" maxlength="6" placeholder="K7M2QX" style="text-transform:uppercase;font-family:var(--mono);letter-spacing:.1em"></label>
<div><button class="btn" type="submit">Тексеру</button></div><div class="msg" id="grade-msg"></div></form></div>"""
    return page("Бағамды тексеру", body)


def admin_page():
    body = """
<div class="path"><a href="index.html">~</a>/<b>admin</b></div>
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
