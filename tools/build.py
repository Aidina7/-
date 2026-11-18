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
]

NAV = [("index.html", "Тақырыптар"), ("grade.html", "Бағамды тексеру")]


def inline(text):
    t = html.escape(text, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
    return t


def page(title, body, active="", extra_head="", scripts=("assets/config.js", "assets/app.js")):
    nav = "".join('<a href="%s"%s>%s</a>' % (h, ' class="active"' if h == active else "", n) for h, n in NAV)
    js = "".join('<script src="%s"></script>' % s for s in scripts)
    return """<!DOCTYPE html>
<html lang="kk">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s · Оқу практикасы</title>
<link rel="stylesheet" href="assets/style.css">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🧩</text></svg>">
%s
</head>
<body>
<header class="topbar"><div class="wrap">
<a class="brand" href="index.html"><span class="logo">ОП</span><span>Оқу практикасы<small>Алматы экономикалық колледжі · ИС 3-1</small></span></a>
<nav class="nav">%s</nav>
</div></header>
%s
<footer><div class="wrap"><span>© Каким А.Д. · КМ 06 «Ақпараттық жүйелерді автоматтандыру» · ОН 6.4</span><a href="admin.html">Оқытушыға кіру</a></div></footer>
%s
</body>
</html>
""" % (html.escape(title), extra_head, nav, body, js)


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


def topic_page(t):
    spec = t["spec"]
    with open(os.path.join(ROOT, "content", t["slug"], "theory.html"), encoding="utf-8") as f:
        theory = f.read()
    with open(os.path.join(ROOT, "content", t["slug"], "quiz.json"), encoding="utf-8") as f:
        quiz = json.load(f)
    zsize = make_zip(t["starter"])
    body = """
<div class="hero"><div class="wrap">
<div class="kicker">Практикалық жұмыс №{num}</div>
<h1>{title}</h1>
<p>{lead}</p>
<div class="meta"><span class="pill">⏱ {hours}</span><span class="pill">🐍 Python 3.10+ · VS Code</span><span class="pill">📝 {nq} сұрақтық тест</span></div>
</div></div>
<nav class="subnav"><div class="wrap">
<a href="#theory">📖 Түсіндірме</a><a href="#video">🎬 Бейне</a><a href="#files">📦 Файлдар</a><a href="#tasks">🛠 Тапсырмалар</a><a href="#test">✅ Тест</a><a href="#submit">📤 Жұмысты тапсыру</a>
</div></nav>
<main><div class="wrap">
<div class="block" id="outcomes"><h2><span class="ico">🎯</span>Оқыту нәтижелері</h2><ol>{outcomes}</ol></div>
<div class="block" id="theory"><h2><span class="ico">📖</span>Түсіндірме</h2>{theory}</div>
<div class="block" id="video"><h2><span class="ico">🎬</span>Бейнетүсіндірме</h2><div class="video" id="video-box" data-topic="{slug}"></div></div>
<div class="block" id="files"><h2><span class="ico">📦</span>Файлдар</h2>
<div class="files">
<a class="file" href="files/{starter}.zip" download><span class="fi">🗂</span><span><b>{starter}.zip</b><span>Бастапқы файлдар · {zkb} КБ</span></span></a>
<a class="file" href="files/{pdf}" target="_blank"><span class="fi">📄</span><span><b>Практикалық тапсырмалар №{num}</b><span>PDF · басып шығаруға</span></span></a>
<a class="file" href="https://github.com/Aidina7/-/tree/main/starter/{starter}" target="_blank" rel="noopener"><span class="fi">💻</span><span><b>Кодты GitHub-та қарау</b><span>файлдарды онлайн оқу</span></span></a>
</div>
<p><b>Қалай бастау:</b> zip-ті ашыңыз → VS Code-та <code>File → Open Folder</code> → <code>{starter}</code> қалтасын таңдаңыз → <code>Terminal → New Terminal</code> → README.txt бойынша командаларды іске қосыңыз.</p>
</div>
<div class="block tasks" id="tasks"><h2><span class="ico">🛠</span>Практикалық тапсырмалар №{num}</h2>{tasks}</div>
<div class="block" id="test"><h2><span class="ico">✅</span>Өзіңізді тексеріңіз</h2>
<form id="quiz-form" class="form" onsubmit="return false">
<div class="row"><label>Аты-жөні<input name="name" autocomplete="name" placeholder="Мысалы: Асанов Әли"></label><label>Тобы<select name="group"></select></label></div>
</form>
<div id="quiz" data-topic="{title_attr}"></div>
<button class="btn" id="quiz-check" type="button">Жауаптарды тексеру</button>
<div class="msg" id="quiz-msg" style="margin-top:14px"></div>
</div>
<div class="block" id="submit"><h2><span class="ico">📤</span>Жұмысты тапсыру</h2>
<p>Есепті (Word, PDF немесе zip) жүктеңіз немесе GitHub / Google Drive сілтемесін қалдырыңыз. Тапсырған соң <b>код</b> беріледі — сол арқылы бағаңызды көресіз.</p>
<form id="submit-form" class="form" data-topic="{title_attr}">
<div class="row"><label>Аты-жөні<input name="name" required autocomplete="name"></label><label>Тобы<select name="group"></select></label></div>
<div class="row"><label>Нұсқа нөмірі<input name="variant" inputmode="numeric" placeholder="1–6"></label><label>Есеп файлы <small>(10 МБ-қа дейін)</small><input type="file" name="file" accept=".pdf,.docx,.doc,.zip,.png,.jpg,.jpeg,.pptx,.txt,.md,.py"></label></div>
<label>немесе сілтеме <small>(GitHub, Google Drive)</small><input name="link" type="url" placeholder="https://"></label>
<label>Түсініктеме <small>(міндетті емес)</small><textarea name="comment"></textarea></label>
<div><button class="btn" type="submit">Жіберу</button></div>
<div class="msg" id="submit-msg"></div>
</form>
</div>
</div></main>
""".format(num=spec["number"], title=html.escape(spec["topic"]), title_attr=html.escape(spec["topic"], quote=True),
           lead=html.escape(t["lead"]), hours=t["hours"], nq=len(quiz), slug=t["slug"],
           outcomes="".join("<li>%s</li>" % html.escape(o) for o in t["outcomes"]), theory=theory,
           starter=t["starter"], zkb=max(1, zsize // 1024), pdf=t["pdf"], tasks=tasks_html(spec))
    head = "<script>window.QUIZ = %s;</script>" % json.dumps(quiz, ensure_ascii=False)
    return page(spec["topic"], body, extra_head=head)


def index_page():
    cards = "".join("""<a class="topic-card" href="{slug}.html"><span class="num">Практикалық жұмыс №{num} · {hours}</span>
<h3>{title}</h3><p style="margin:0;color:#5f6b7a">{lead}</p><ul>{out}</ul></a>""".format(
        slug=t["slug"], num=t["spec"]["number"], hours=t["hours"], title=html.escape(t["spec"]["topic"]),
        lead=html.escape(t["lead"]), out="".join("<li>%s</li>" % html.escape(o) for o in t["outcomes"])) for t in TOPICS)
    body = """
<div class="hero"><div class="wrap">
<div class="kicker">КМ 06 · ОН 6.4 · 3 курс</div>
<h1>Ақпараттық жүйелерді автоматтандыру: оқу практикасы</h1>
<p>Әр тақырыпта: қысқа түсіндірме, бейне, бастапқы файлдар, практикалық тапсырмалар, өзін-өзі тексеру тесті және жұмысты онлайн тапсыру.</p>
</div></div>
<main><div class="wrap">
<div class="block"><h2><span class="ico">🧭</span>Қалай оқимыз?</h2>
<div class="flow"><div>1. Түсіндірме<small>оқу немесе бейне</small></div><span>→</span><div>2. Файлдар<small>zip → VS Code</small></div><span>→</span><div>3. Тапсырмалар<small>өз нұсқаңыз</small></div><span>→</span><div>4. Тест<small>өзіңізді тексеру</small></div><span>→</span><div>5. Тапсыру<small>есеп + код</small></div></div>
<p style="margin:0">Қажет: компьютер, <a href="https://code.visualstudio.com/" target="_blank" rel="noopener">VS Code</a> және <a href="https://www.python.org/downloads/" target="_blank" rel="noopener">Python 3.10+</a>. Қосымша пакет орнатудың қажеті жоқ.</p>
</div>
<h2 style="margin:28px 0 14px">Тақырыптар</h2>
<div class="topics">%s</div>
<p style="color:#5f6b7a;margin-top:18px">Оқу практикасының басқа тақырыптары жақында қосылады.</p>
</div></main>
""" % cards
    return page("Басты бет", body, active="index.html")


def grade_page():
    body = """
<div class="hero"><div class="wrap"><div class="kicker">Студентке</div><h1>Бағамды тексеру</h1>
<p>Жұмысты тапсырғанда берілген 6 таңбалы кодты енгізіңіз.</p></div></div>
<main><div class="wrap"><div class="block">
<form id="grade-form" class="form"><label>Тексеру коды<input name="code" maxlength="6" placeholder="Мысалы: K7M2QX" style="text-transform:uppercase;font-size:20px;letter-spacing:.1em"></label>
<div><button class="btn" type="submit">Тексеру</button></div><div class="msg" id="grade-msg"></div></form>
</div></div></main>"""
    return page("Бағамды тексеру", body, active="grade.html")


def admin_page():
    body = """
<div class="hero"><div class="wrap"><div class="kicker">Оқытушыға</div><h1>Әкімші панелі</h1>
<p>Студенттердің тапсырған жұмыстары, бағалар және тест нәтижелері.</p></div></div>
<main><div class="wrap">
<div class="block" id="login" style="display:none;max-width:460px">
<h2><span class="ico">🔐</span>Кіру</h2>
<form id="login-form" class="form"><label>Құпиясөз<input id="pw" type="password" autocomplete="current-password"></label>
<div><button class="btn" type="submit">Кіру</button></div><div class="msg" id="login-msg"></div></form>
</div>
<div id="panel" style="display:none">
<div class="stats" id="stats"></div>
<div class="tabs"><button class="active" data-tab="subs">Жұмыстар</button><button data-tab="tests">Тест нәтижелері</button></div>
<div class="admin-bar">
<select id="f-topic" data-all="Барлық тақырыптар"></select>
<select id="f-group" data-all="Барлық топтар"></select>
<select id="f-status"><option value="">Барлық күйлер</option><option>Тексерілмеген</option><option>Тексерілді</option><option>Қайта тапсыру</option></select>
<input id="f-q" placeholder="Аты бойынша іздеу">
<button class="btn small secondary" id="reload" type="button">⟳ Жаңарту</button>
<button class="btn small secondary" id="export" type="button">⬇ Excel (CSV)</button>
<button class="btn small secondary" id="logout" type="button">Шығу</button>
</div>
<div class="block" id="list" style="padding:16px"></div>
</div>
</div></main>
<div class="modal-bg" id="modal"><div class="modal">
<h3>Жұмысты бағалау</h3>
<div class="kv" id="m-info"></div>
<div class="form">
<div class="row"><label>Баға (0–100 ұпай)<input id="m-grade" type="number" min="0" max="100"></label>
<label>Күйі<select id="m-status"><option>Тексерілді</option><option>Қайта тапсыру</option><option>Тексерілмеген</option></select></label></div>
<label>Түсініктеме (студент көреді)<textarea id="m-comment"></textarea></label>
<div class="msg" id="m-msg"></div>
<div style="display:flex;gap:10px"><button class="btn" id="m-save" type="button">Сақтау</button><button class="btn secondary" id="m-close" type="button">Жабу</button></div>
</div></div></div>"""
    return page("Әкімші панелі", body, extra_head='<meta name="robots" content="noindex">',
                scripts=("assets/config.js", "assets/app.js", "assets/admin.js"))


def main():
    pages = {"index.html": index_page(), "grade.html": grade_page(), "admin.html": admin_page()}
    for t in TOPICS:
        pages[t["slug"] + ".html"] = topic_page(t)
    for name, content in pages.items():
        with open(os.path.join(ROOT, name), "w", encoding="utf-8") as f:
            f.write(content)
        print("жасалды:", name)


if __name__ == "__main__":
    main()
