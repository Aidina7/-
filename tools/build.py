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
FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">'
BASE_JS = ("assets/config.js", "assets/games.js", "assets/ctf-data.js", "assets/terminal.js", "assets/app.js")


def inline(text):
    t = html.escape(text, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
    return t


def ver(rel):
    """Кэшті жаңарту үшін файлдың қысқа хэші (браузер ескі CSS/JS-ті қолданбауы үшін)."""
    import hashlib
    with open(os.path.join(ROOT, rel), "rb") as f:
        return hashlib.sha1(f.read()).hexdigest()[:8]


def page(title, body, active="", extra_head="", scripts=BASE_JS):
    nav = "".join('<a href="%s"%s>%s</a>' % (h, ' class="active"' if h == active else "", n) for h, n in NAV)
    js = "".join('<script src="%s?v=%s"></script>' % (s, ver(s)) for s in scripts)
    return """<!DOCTYPE html>
<html lang="kk">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s · oqu-praktikasy</title>
%s
<link rel="stylesheet" href="assets/style.css?v=%s">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' rx='7' fill='%%230b0f14'/><text x='5' y='22' font-family='monospace' font-size='16' fill='%%234fd1a5'>&gt;_</text></svg>">
%s
</head>
<body>
<header class="topbar"><div class="wrap">
<a class="brand" href="index.html"><span class="p">~/</span>oqu-praktikasy<span class="c"></span></a>
<nav class="nav">%s</nav>
<div class="user" id="user"></div>
</div></header>
%s
<footer><div class="wrap"><span>// Алматы экономикалық колледжі · ИС 3-1 · КМ 06 · ОН 6.4 · оқытушы: Каким А.Д.</span><span><a href="https://github.com/Aidina7/-" target="_blank" rel="noopener">github</a> · <a href="admin.html">оқытушы</a></span></div></footer>
%s
</body>
</html>
""" % (html.escape(title), FONTS, ver("assets/style.css"), extra_head, nav, body, js)


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


SIDE = [("theory", "theory.md"), ("video", "video.mp4"), ("files", "files.zip"), ("tasks", "tasks.md"),
        ("test", "test.json"), ("ctf", "soc.sh"), ("submit", "submit")]


def topic_page(t):
    spec = t["spec"]
    with open(os.path.join(ROOT, "content", t["slug"], "theory.html"), encoding="utf-8") as f:
        theory = f.read()
    quiz = strip_quiz(t["slug"])
    zsize = make_zip(t["starter"])
    ctfs = [c for c in CTF_IDS if c[1] == t["slug"]]
    side = "".join('<a href="#%s">%s</a>' % (a, n) for a, n in SIDE if a != "ctf" or ctfs)
    body = """
<div class="wrap"><div class="layout">
<aside class="side"><div class="root">{starter}/</div>{side}
<div class="meta">// №{num} · {hours}<br>// python 3.10+ · vs code<br>// тест: банкте {nq} сұрақ</div></aside>
<main>
<div class="page-head"><div class="path">~/oqu-praktikasy/{starter} $ cat README</div>
<h1>{title}</h1><p>{lead}</p>
<div class="tags" style="margin-top:12px">{outcomes}</div></div>

<div class="block" id="theory"><h2>түсіндірме <span class="fname">theory.md</span></h2>{theory}</div>

<div class="block" id="video"><h2>бейнетүсіндірме <span class="fname">video.mp4</span></h2><div class="video" id="video-box" data-topic="{slug}"></div></div>

<div class="block" id="files"><h2>файлдар <span class="fname">files/</span></h2>
<div class="files">
<a class="file" href="files/{starter}.zip" download><span class="ext">ZIP</span><span><b>{starter}.zip</b><span>бастапқы код · {zkb} КБ</span></span></a>
<a class="file" href="files/{pdf}" target="_blank"><span class="ext">PDF</span><span><b>тапсырмалар №{num}</b><span>басып шығаруға</span></span></a>
<a class="file" href="https://github.com/Aidina7/-/tree/main/starter/{starter}" target="_blank" rel="noopener"><span class="ext">GIT</span><span><b>кодты GitHub-та қарау</b><span>онлайн оқу</span></span></a>
</div>
<pre><code><span class="t-m"># бастау</span>
unzip {starter}.zip &amp;&amp; cd {starter}
code .                     <span class="t-m"># VS Code-та ашу</span>
cat README.txt             <span class="t-m"># командалар тізімі</span></code></pre>
</div>

<div class="block tasks" id="tasks"><h2>практикалық тапсырмалар №{num} <span class="fname">tasks.md</span></h2>{tasks}</div>

<div class="block" id="test"><h2>тест <span class="fname">test.json</span></h2>
<div id="quiz-head"></div><div id="quiz" data-topic="{slug}"></div><div class="msg" id="quiz-msg" style="margin-top:12px"></div></div>

{ctf_block}

<div class="block" id="submit"><h2>жұмысты тапсыру <span class="fname">submit</span></h2>
<p>Есепті (docx, pdf, zip) жүктеңіз немесе GitHub / Google Drive сілтемесін қалдырыңыз. Баға мен оқытушы түсініктемесі кабинетте шығады.</p>
<form id="submit-form" class="form" data-topic="{title_attr}">
<div class="row"><label class="f">нұсқа нөмірі<input name="variant" inputmode="numeric" placeholder="1–6"></label><label class="f">есеп файлы <small>10 МБ-қа дейін</small><input type="file" name="file" accept=".pdf,.docx,.doc,.zip,.png,.jpg,.jpeg,.pptx,.txt,.md,.py"></label></div>
<label class="f">немесе сілтеме<input name="link" type="url" placeholder="https://github.com/..."></label>
<label class="f">түсініктеме <small>міндетті емес</small><textarea name="comment"></textarea></label>
<div><button class="btn" type="submit">жіберу →</button></div><div class="msg" id="submit-msg"></div>
</form></div>
</main></div></div>
""".format(num=spec["number"], title=html.escape(spec["topic"]), title_attr=html.escape(spec["topic"], quote=True),
           lead=html.escape(t["lead"]), hours=t["hours"], nq=len(quiz), slug=t["slug"], side=side,
           outcomes="".join('<span class="tag g">%s</span>' % html.escape(o) for o in t["outcomes"]), theory=theory,
           starter=t["starter"], zkb=max(1, zsize // 1024), pdf=t["pdf"], tasks=tasks_html(spec),
           ctf_block=('<div class="block" id="ctf"><h2>SOC-терминал: челлендждер <span class="fname">soc.sh</span></h2>'
                      '<p>Нақты журналдарға ұқсас файлдар берілген. Терминалда <code>ls</code>, <code>cat</code>, <code>grep</code>, <code>sort</code>, <code>uniq</code>, <code>cut</code> командаларымен тергеу жүргізіп, жалауды тауып <code>submit flag{...}</code> жазыңыз. Командалар: <code>help</code>.</p>'
                      '<div data-ctf="%s"></div></div>' % t["slug"]) if ctfs else "")
    head = "<script>window.QUIZ = %s;</script>" % json.dumps(quiz, ensure_ascii=False)
    return page(spec["topic"], body, extra_head=head)


def index_page():
    cards = "".join("""<a class="tcard" href="{slug}.html"><div class="path">~/<b>{starter}</b> · №{num} · {hours}</div>
<h3>{title}</h3><p>{lead}</p><div class="tags"><span class="tag">theory</span><span class="tag">tasks</span><span class="tag g">test</span>{ctf}</div></a>""".format(
        slug=t["slug"], starter=t["starter"], num=t["spec"]["number"], hours=t["hours"], title=html.escape(t["spec"]["topic"]),
        lead=html.escape(t["lead"]), ctf='<span class="tag a">soc.sh</span>' if any(c[1] == t["slug"] for c in CTF_IDS) else "") for t in TOPICS)
    body = """
<div class="wrap">
<section class="hero"><div class="hero-grid">
<div><div class="eyebrow">// КМ 06 · ОН 6.4 · оқу практикасы · ИС 3-1</div>
<h1>Ақпараттық жүйелерді <em>автоматтандыру</em> — қолмен емес, кодпен.</h1>
<p>Түгендеу, лицензиялар, желілік аномалиялар, SLA. Әр тақырыпта: қысқа теория, Python бастапқы коды, нұсқалы тапсырмалар, серверде тексерілетін тест және SOC-терминалдағы челлендждер.</p>
<div class="cta"><a class="btn" href="login.html#register">тіркелу →</a><a class="btn ghost" href="games.html">ойындар</a></div></div>
<div class="win"><div class="win-bar"><i></i><i></i><i></i><span>analyst@aec: ~/oqu-praktikasy</span></div><pre id="hero-term"></pre></div>
</div></section>

<div class="section-title"><h2>жұмыс тәртібі</h2><span>әр тақырып бойынша</span></div>
<div class="steps">
<div class="step"><b><span>01</span> theory.md</b>теорияны оқу, бейне</div>
<div class="step"><b><span>02</span> files.zip</b>кодты VS Code-та ашу</div>
<div class="step"><b><span>03</span> tasks.md</b>өз нұсқаңды орындау</div>
<div class="step"><b><span>04</span> test.json</b>10 сұрақ, 3 әрекет</div>
<div class="step"><b><span>05</span> submit</b>есеп → баға кабинетте</div>
</div>

<div class="section-title"><h2>тақырыптар</h2><span>ls ~/oqu-praktikasy</span></div>
<div class="topic-list">%s</div>

<div class="section-title"><h2>ойындар</h2><span>ұпай → көшбасшылар кестесі</span></div>
<div class="topic-list">
<a class="tcard" href="games.html#sorter"><div class="path">~/games/<b>sorter</b></div><h3>Сортировщик</h3><p>75 секунд ішінде карточкаларды дұрыс санатқа жібер: құрылғыны таны, лицензия аудиті, SOC кезекшісі, SRE шешімі.</p></a>
<a class="tcard" href="games.html#ctf"><div class="path">~/games/<b>soc.sh</b></div><h3>SOC-терминал</h3><p>Журналдарды grep, sort, uniq арқылы тергеп, бөтен құрылғыны, брутфорсты, сканерді және деректердің жылыстауын тап.</p></a>
</div>
</div>
""" % cards
    return page("Басты бет", body, active="index.html")


def login_page():
    body = """
<div class="wrap"><div class="auth-box" id="auth">
<div class="tabs"><button data-t="login" class="active">кіру</button><button data-t="register">тіркелу</button></div>
<form id="f-login" class="form">
<label class="f">логин<input name="login" autocomplete="username" required></label>
<label class="f">құпиясөз<input name="password" type="password" autocomplete="current-password" required></label>
<div><button class="btn" type="submit">кіру →</button></div><div class="msg" id="m-login"></div>
<p class="muted" style="font-size:14px">Құпиясөзді ұмытсаңыз — оқытушыға айтыңыз, ол жаңасын береді.</p>
</form>
<form id="f-reg" class="form" style="display:none">
<label class="f">логин <small>латын әріптері, сан, _ . - (мысалы: asanov.ali)</small><input name="login" autocomplete="username" required></label>
<label class="f">аты-жөні <small>тегі және аты, журналдағыдай</small><input name="name" autocomplete="name" required></label>
<label class="f">топ<select name="group"></select></label>
<div class="row"><label class="f">құпиясөз <small>кемінде 6 таңба</small><input name="password" type="password" autocomplete="new-password" minlength="6" required></label>
<label class="f">қайталаңыз<input name="password2" type="password" autocomplete="new-password" minlength="6" required></label></div>
<div><button class="btn" type="submit">тіркелу →</button></div><div class="msg" id="m-reg"></div>
</form>
</div></div>"""
    return page("Кіру", body)


def cabinet_page():
    body = """
<div class="wrap" style="padding:30px 22px 70px">
<div class="page-head"><div class="path">~/oqu-praktikasy $ whoami</div><h1>Кабинет</h1><p id="hello" class="mono"></p></div>
<div id="cabinet"></div>
</div>"""
    return page("Кабинет", body, active="cabinet.html")


def games_page():
    opts = "".join('<option value="sort:%s">Сортировщик · %s</option>' % (k, v) for k, v in DECK_NAMES) + \
           "".join('<option value="ctf:%s">SOC-терминал · %s</option>' % (c[0], html.escape(c[2])) for c in CTF_IDS)
    body = """
<div class="wrap" style="padding:30px 22px 70px">
<div class="page-head"><div class="path">~/oqu-praktikasy/games $ ls</div><h1>Ойындар</h1>
<p>Ойнап үйрен: ұпайлар кабинетке және көшбасшылар кестесіне жазылады (алдымен <a href="login.html">кіріңіз</a>).</p></div>
<div class="block" id="sorter"><h2>сортировщик <span class="fname">sorter</span></h2><div class="deck-pick" data-pick></div><div data-sorter="all"></div></div>
<div class="block" id="ctf"><h2>SOC-терминал <span class="fname">soc.sh</span></h2>
<p>Әр челлендж — нақты инцидентке ұқсас тергеу. <code>help</code> — командалар, <code>hint</code> — кеңес (ұпай 30%%-ға азаяды), <code>submit flag{...}</code> — жауап.</p><div data-ctf="all"></div></div>
<div class="block" id="leaders"><h2>көшбасшылар <span class="fname">leaderboard</span></h2>
<div class="bar"><select id="board-game"><option value="">жалпы рейтинг (барлық ойын)</option>%s</select></div><div id="board"></div></div>
</div>""" % opts
    return page("Ойындар", body, active="games.html")


def grade_page():
    body = """
<div class="wrap"><div class="auth-box"><div class="page-head"><div class="path">$ check --code</div><h1>Бағаны кодпен тексеру</h1></div>
<form id="grade-form" class="form"><label class="f">тексеру коды<input name="code" maxlength="6" placeholder="K7M2QX" style="text-transform:uppercase;font-family:var(--mono);font-size:20px;letter-spacing:.12em"></label>
<div><button class="btn" type="submit">тексеру</button></div><div class="msg" id="grade-msg"></div></form>
<p class="muted">Тіркелген болсаңыз, барлық бағалар <a href="cabinet.html">кабинетте</a>.</p></div></div>"""
    return page("Бағамды тексеру", body)


def admin_page():
    body = """
<div class="wrap" style="padding:30px 22px 70px">
<div class="page-head"><div class="path">~/oqu-praktikasy $ sudo admin</div><h1>Оқытушы панелі</h1></div>
<div id="login" style="display:none" class="auth-box"><form id="login-form" class="form">
<label class="f">оқытушы құпиясөзі<input id="pw" type="password" autocomplete="current-password"></label>
<div><button class="btn" type="submit">кіру →</button></div><div class="msg" id="login-msg"></div></form></div>
<div id="panel" style="display:none">
<div class="stats" id="stats"></div>
<div class="tabs"><button class="active" data-tab="students">студенттер</button><button data-tab="subs">жұмыстар</button><button data-tab="tests">тесттер</button><button data-tab="games">ойындар</button></div>
<div class="bar">
<select id="f-group"></select><select id="f-topic"><option value="">барлық тақырыптар</option></select>
<select id="f-status"><option value="">барлық күйлер</option><option>Тексерілмеген</option><option>Тексерілді</option><option>Қайта тапсыру</option></select>
<input id="f-q" placeholder="аты немесе логин">
<button class="btn small ghost" id="reload">⟳ жаңарту</button><button class="btn small ghost" id="export">⬇ csv</button><button class="btn small ghost" id="logout-admin">шығу</button>
</div>
<div class="block" id="list" style="padding:12px 16px;margin-top:0"></div>
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
