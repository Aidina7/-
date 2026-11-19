/* oqu-praktikasy · клиент: кіру, тест, челлендждер, ойындар, кабинет. */
(function () {
  const S = window.SITE || {};
  const $ = (s, r) => (r || document).querySelector(s);
  const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
  const esc = v => String(v == null ? "" : v).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const fmt = t => { const d = new Date(t); return isNaN(d) ? esc(t) : d.toLocaleString("ru-RU", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }); };

  /* ---------- API және сессия ---------- */
  function api(action, data) {
    if (!S.API_URL) return Promise.reject(new Error("Сервер әлі қосылмаған"));
    return fetch(S.API_URL, { method: "POST", body: JSON.stringify(Object.assign({ action: action }, data || {})) })
      .then(r => r.json())
      .then(r => { if (r && r.auth) { Auth.clear(); } return r; });
  }
  const Auth = {
    get() { try { return JSON.parse(localStorage.getItem("op_auth") || "null"); } catch (e) { return null; } },
    set(a) { try { localStorage.setItem("op_auth", JSON.stringify(a)); } catch (e) { } },
    clear() { try { localStorage.removeItem("op_auth"); } catch (e) { } },
    token() { const a = this.get(); return a && a.token; }
  };
  window.Site = { api: api, Auth: Auth, esc: esc, fmt: fmt };

  function msg(el, kind, html) { if (!el) return; el.className = "msg show " + kind; el.innerHTML = html; }
  function loginLink() { return "login.html?next=" + encodeURIComponent(location.pathname.split("/").pop() + location.hash); }

  function renderUser() {
    const box = $("#user");
    if (!box) return;
    const a = Auth.get();
    if (a) {
      box.innerHTML = '<a class="who" href="cabinet.html">' + esc(a.user.name.split(" ").slice(0, 2).join(" ")) + ' · <b>' + esc(a.user.login) + '</b></a><button id="logout">Шығу</button>';
      $("#logout").onclick = () => { Auth.clear(); location.href = "index.html"; };
    } else {
      box.innerHTML = '<a class="btn small ghost" href="' + loginLink() + '">Кіру</a><a class="btn small" href="login.html#register">Тіркелу</a>';
    }
  }

  /* ---------- кіру / тіркелу ---------- */
  function initLogin() {
    const root = $("#auth");
    if (!root) return;
    const groups = S.GROUPS || ["ИС 3-1"];
    $$("select[name=group]").forEach(s => groups.forEach(g => s.add(new Option(g, g))));
    const show = which => {
      $$(".tabs button", root).forEach(b => b.classList.toggle("active", b.dataset.t === which));
      $("#f-login").style.display = which === "login" ? "" : "none";
      $("#f-reg").style.display = which === "register" ? "" : "none";
    };
    $$(".tabs button", root).forEach(b => b.onclick = () => show(b.dataset.t));
    show(location.hash === "#register" ? "register" : "login");
    const next = new URLSearchParams(location.search).get("next") || "cabinet.html";
    const done = r => { Auth.set({ token: r.token, user: r.user }); location.href = /^[\w.-]+\.html(#[\w-]*)?$/.test(next) ? next : "cabinet.html"; };
    $("#f-login").onsubmit = async e => {
      e.preventDefault(); const f = e.target, m = $("#m-login");
      msg(m, "info", "Тексерілуде…");
      try { const r = await api("login", { login: f.login.value.trim(), password: f.password.value }); r.ok ? done(r) : msg(m, "err", esc(r.error)); }
      catch (err) { msg(m, "err", esc(err.message)); }
    };
    $("#f-reg").onsubmit = async e => {
      e.preventDefault(); const f = e.target, m = $("#m-reg");
      if (f.password.value !== f.password2.value) return msg(m, "err", "Құпиясөздер сәйкес емес");
      msg(m, "info", "Тіркелуде…");
      try {
        const r = await api("register", { login: f.login.value.trim(), name: f.name.value.trim(), group: f.group.value, password: f.password.value });
        r.ok ? done(r) : msg(m, "err", esc(r.error));
      } catch (err) { msg(m, "err", esc(err.message)); }
    };
  }

  /* ---------- бейне ---------- */
  function renderVideo() {
    const box = $("#video-box");
    if (!box) return;
    const url = (S.VIDEOS || {})[box.dataset.topic] || "";
    const m = url.match(/(?:youtu\.be\/|v=|embed\/|shorts\/)([\w-]{11})/);
    if (!url) box.innerHTML = '<div class="video-empty">Бейне жақында қосылады</div>';
    else if (m) box.innerHTML = '<iframe src="https://www.youtube-nocookie.com/embed/' + m[1] + '" title="Бейнетүсіндірме" allowfullscreen loading="lazy"></iframe>';
    else {
      const base = url.replace(/\.mp4$/, "");
      box.innerHTML = '<video controls preload="metadata" playsinline poster="' + esc(base) + '.jpg" src="' + esc(url) + '">' +
        '<track kind="subtitles" srclang="kk" label="Қазақша" src="' + esc(base) + '.vtt"></track></video>';
    }
  }

  /* ---------- тест (серверде тексеріледі) ---------- */
  function shuffle(a) { a = a.slice(); for (let k = a.length - 1; k > 0; k--) { const j = Math.floor(Math.random() * (k + 1)); [a[k], a[j]] = [a[j], a[k]]; } return a; }

  async function initQuiz() {
    const root = $("#quiz");
    if (!root || !window.QUIZ) return;
    const topic = root.dataset.topic, size = S.QUIZ_SIZE || 10;
    const head = $("#quiz-head"), m = $("#quiz-msg");
    if (!Auth.get()) {
      head.innerHTML = '<p>Тест нәтижесі оқытушыға жазылады, сондықтан алдымен <a href="' + loginLink() + '">кіріңіз</a> немесе <a href="login.html#register">тіркеліңіз</a>.</p>';
      return;
    }
    let used = 0, limit = 3, best = null;
    try {
      const me = await api("me", { token: Auth.token() });
      if (me.ok) {
        limit = me.attemptsLimit;
        const mine = me.tests.filter(t => t.topic === topic);
        used = mine.length; best = mine.reduce((b, t) => Math.max(b, Number(t.percent)), -1);
      } else if (me.auth) { renderUser(); return initQuiz(); }
    } catch (e) { /* желі жоқ */ }
    const info = () => '<div class="quiz-bar"><span>сұрақтар: <b>' + size + '</b> (банктен кездейсоқ)</span><span>әрекет: <b>' + used + '/' + limit + '</b></span>' + (best >= 0 ? '<span>ең жақсы: <b>' + best + '%</b></span>' : "") + '</div>';
    if (used >= limit) { head.innerHTML = info() + '<p class="muted">Әрекеттер бітті. Нәтижелер — <a href="cabinet.html">кабинетте</a>.</p>'; return; }
    head.innerHTML = info() + '<p class="muted">Әр әрекетте сұрақтар мен жауап нұсқалары араласады. Жауаптар серверде тексеріледі.</p><button class="btn" id="quiz-start">тестті бастау →</button>';
    $("#quiz-start").onclick = () => {
      const qs = shuffle(window.QUIZ).slice(0, size);
      const started = Date.now();
      root.innerHTML = qs.map((q, n) => '<div class="q" data-id="' + esc(q.id) + '"><div class="qt"><span>' + String(n + 1).padStart(2, "0") + '</span>' + esc(q.q) + '</div>' +
        shuffle(q.o.map((o, j) => [o, j])).map(([o, j]) => '<label><input type="radio" name="' + esc(q.id) + '" value="' + j + '"><span>' + esc(o) + '</span></label>').join("") +
        '<div class="exp"></div></div>').join("") + '<button class="btn" id="quiz-send">Жауаптарды жіберу</button>';
      head.innerHTML = info();
      $("#quiz-send").onclick = async function () {
        const answers = {};
        let miss = 0;
        qs.forEach(q => { const c = $('input[name="' + q.id + '"]:checked', root); if (c) answers[q.id] = +c.value; else miss++; });
        if (miss) return msg(m, "err", "Барлық сұраққа жауап беріңіз (қалды: " + miss + ")");
        this.disabled = true; msg(m, "info", "Тексерілуде…");
        try {
          const r = await api("quiz", { token: Auth.token(), topic: topic, answers: answers, seconds: Math.round((Date.now() - started) / 1000) });
          if (!r.ok) { this.disabled = false; return msg(m, "err", esc(r.error)); }
          qs.forEach(q => {
            const box = $('.q[data-id="' + q.id + '"]', root), res = r.result[q.id];
            if (!res) return;
            $$("label", box).forEach(l => {
              const inp = $("input", l), v = +inp.value; inp.disabled = true;
              if (v === res.correct) l.classList.add("right"); else if (v === answers[q.id]) l.classList.add("wrong");
            });
            $(".exp", box).textContent = res.e; box.classList.add("done");
          });
          this.remove();
          used = r.attempt;
          msg(m, r.percent >= 50 ? "ok" : "err", '<span class="big">' + r.score + "/" + r.total + "</span> · " + r.percent + "%<br>" +
            (r.left > 0 ? "Қалған әрекет: " + r.left + '. <a href="#test" onclick="location.reload()">қайта тапсыру</a>' : "Әрекеттер бітті.") + ' · <a href="cabinet.html">кабинет</a>');
        } catch (err) { this.disabled = false; msg(m, "err", esc(err.message)); }
      };
    };
  }

  /* ---------- челлендждер (SOC-терминал) ---------- */
  function solvedSet() { try { return new Set(JSON.parse(localStorage.getItem("op_ctf") || "[]")); } catch (e) { return new Set(); } }
  function markSolved(id) { const s = solvedSet(); s.add(id); try { localStorage.setItem("op_ctf", JSON.stringify([...s])); } catch (e) { } }

  function initCtf() {
    $$("[data-ctf]").forEach(root => {
      const topic = root.dataset.ctf;
      const list = (window.CTF || []).filter(c => !topic || topic === "all" || c.topic === topic);
      if (!list.length) { root.innerHTML = '<p class="muted">Бұл тақырыпқа челлендж жоқ.</p>'; return; }
      const solved = solvedSet();
      root.innerHTML = '<div class="ctf-list">' + list.map(c => '<button class="ctf' + (solved.has(c.id) ? " solved" : "") + '" data-id="' + c.id + '"><span class="pts">' + c.points + ' ұпай</span><b>' + esc(c.title) + '</b><span>' + esc(c.story.slice(0, 110)) + '…</span></button>').join("") +
        '</div><div data-term></div><div class="msg" data-cmsg style="margin-top:10px"></div>';
      const open = (id, focus) => {
        const c = list.find(x => x.id === id);
        $$(".ctf", root).forEach(b => b.classList.toggle("on", b.dataset.id === id));
        const t = window.mountTerminal($("[data-term]", root), c, async res => {
          markSolved(c.id);
          $('.ctf[data-id="' + c.id + '"]', root).classList.add("solved");
          const cm = $("[data-cmsg]", root);
          if (!Auth.get()) return msg(cm, "info", 'Шешілді! Ұпайды сақтау үшін <a href="' + loginLink() + '">кіріңіз</a>.');
          try {
            const r = await api("game", { token: Auth.token(), game: "ctf:" + c.id, score: res.points, accuracy: res.hint ? 70 : 100, detail: res.seconds + "s, tries " + res.tries + (res.hint ? ", hint" : "") });
            msg(cm, r.ok ? "ok" : "err", r.ok ? "+" + res.points + " ұпай сақталды." : esc(r.error));
          } catch (e) { msg(cm, "err", esc(e.message)); }
        });
        if (focus) t.focus();
      };
      $$(".ctf", root).forEach(b => b.onclick = () => open(b.dataset.id, true));
      open(list[0].id);
    });
  }

  /* ---------- сортировщик ойыны ---------- */
  function initSorters() {
    $$("[data-sorter]").forEach(root => {
      const ids = root.dataset.sorter === "all" ? Object.keys(window.DECKS) : [root.dataset.sorter];
      const pick = $("[data-pick]", root.parentElement);
      const run = id => window.mountSorter(root, id, async (res, saveBox) => {
        if (!Auth.get()) { saveBox.innerHTML = '<a href="' + loginLink() + '">Кіріңіз</a> — ұпай көшбасшылар кестесіне жазылады.'; return; }
        saveBox.textContent = "сақталуда…";
        try {
          const r = await api("game", { token: Auth.token(), game: "sort:" + id, score: res.score, accuracy: res.accuracy, detail: res.detail });
          saveBox.textContent = r.ok ? "✔ ұпай сақталды" : r.error;
          loadBoard();
        } catch (e) { saveBox.textContent = e.message; }
      });
      if (pick && ids.length > 1) {
        pick.innerHTML = ids.map(id => '<button class="ctf" data-deck="' + id + '"><b>' + esc(window.DECKS[id].title) + '</b><span>' + esc(window.DECKS[id].about) + '</span></button>').join("");
        $$("[data-deck]", pick).forEach(b => b.onclick = () => { $$("[data-deck]", pick).forEach(x => x.classList.toggle("on", x === b)); run(b.dataset.deck); });
        $("[data-deck]", pick).click();
      } else run(ids[0]);
    });
  }

  async function loadBoard() {
    const box = $("#board");
    if (!box) return;
    const sel = $("#board-game");
    try {
      const r = await api("leaderboard", { game: sel ? sel.value : "" });
      if (!r.ok) throw new Error(r.error);
      box.innerHTML = r.list.length ? '<table><tr><th>#</th><th>Студент</th><th>Топ</th><th>Ұпай</th></tr>' + r.list.map((x, i) =>
        '<tr><td class="mono">' + (i + 1) + '</td><td>' + esc(x.name) + '</td><td>' + esc(x.group) + '</td><td class="mono" style="font-weight:600">' + esc(x.score) + '</td></tr>').join("") + '</table>'
        : '<p class="muted">Әзірге ешкім ойнаған жоқ. Бірінші болыңыз!</p>';
    } catch (e) { box.innerHTML = '<p class="muted">' + esc(e.message) + '</p>'; }
  }

  /* ---------- жұмыс тапсыру ---------- */
  function readFile(file) {
    return new Promise((res, rej) => { const fr = new FileReader(); fr.onload = () => res(String(fr.result).split(",")[1]); fr.onerror = rej; fr.readAsDataURL(file); });
  }
  function initSubmit() {
    const form = $("#submit-form");
    if (!form) return;
    const m = $("#submit-msg");
    if (!Auth.get()) { form.innerHTML = '<p>Жұмысты тапсыру үшін <a href="' + loginLink() + '">кіріңіз</a>.</p>'; return; }
    form.onsubmit = async e => {
      e.preventDefault();
      const btn = $("button[type=submit]", form), f = form.file.files[0], link = form.link.value.trim();
      if (!f && !link) return msg(m, "err", "Файл жүктеңіз немесе сілтеме қалдырыңыз");
      if (f && f.size > 10 * 1024 * 1024) return msg(m, "err", "Файл 10 МБ-тан аспауы керек");
      btn.disabled = true; msg(m, "info", "Жіберілуде…");
      try {
        const data = { token: Auth.token(), topic: form.dataset.topic, variant: form.variant.value, link: link, comment: form.comment.value.trim() };
        if (f) data.file = { name: f.name, mime: f.type, data: await readFile(f) };
        const r = await api("submit", data);
        if (!r.ok) throw new Error(r.error);
        msg(m, "ok", "Қабылданды. Бағасын <a href='cabinet.html'>кабинеттен</a> көресіз. Код: <b class='mono'>" + esc(r.id) + "</b>");
        form.reset();
      } catch (err) { msg(m, "err", esc(err.message)); }
      finally { btn.disabled = false; }
    };
  }

  /* ---------- кабинет ---------- */
  async function initCabinet() {
    const root = $("#cabinet");
    if (!root) return;
    if (!Auth.get()) { location.href = loginLink(); return; }
    root.innerHTML = '<p class="muted">жүктелуде…</p>';
    try {
      const r = await api("me", { token: Auth.token() });
      if (!r.ok) { if (r.auth) location.href = loginLink(); else root.innerHTML = '<div class="msg show err">' + esc(r.error) + '</div>'; return; }
      const T = S.TOPICS || {};
      const best = {};
      r.tests.forEach(t => { best[t.topic] = best[t.topic] || { n: 0, best: 0 }; best[t.topic].n++; best[t.topic].best = Math.max(best[t.topic].best, Number(t.percent)); });
      const gbest = {};
      r.games.forEach(g => { gbest[g.game] = Math.max(gbest[g.game] || 0, Number(g.score)); });
      const points = Object.values(gbest).reduce((a, b) => a + b, 0);
      const graded = r.submissions.filter(s => s.grade !== "" && s.grade != null);
      $("#hello").textContent = r.user.name + " · " + r.user.group;
      root.innerHTML =
        '<div class="stats"><div class="stat"><b>' + Object.keys(best).length + '/' + Object.keys(T).length + '</b><span>тест тапсырылды</span></div>' +
        '<div class="stat"><b>' + r.submissions.length + '</b><span>жұмыс тапсырылды</span></div>' +
        '<div class="stat"><b>' + (graded.length ? Math.round(graded.reduce((a, s) => a + Number(s.grade), 0) / graded.length) : "—") + '</b><span>орташа баға</span></div>' +
        '<div class="stat"><b style="font-weight:600">' + points + '</b><span>ойын ұпайы</span></div></div>' +
        '<div class="block"><h2>Тесттер</h2><div class="table-wrap"><table><tr><th>Тақырып</th><th>Әрекет</th><th>Ең жақсы</th><th></th></tr>' +
        Object.keys(T).map(k => { const b = best[k]; return '<tr><td><a href="' + k + '.html#test">' + esc(T[k]) + '</a></td><td class="mono">' + (b ? b.n : 0) + '/' + r.attemptsLimit + '</td><td class="mono">' + (b ? b.best + "%" : "—") +
          '</td><td><div class="bar-mini"><i style="width:' + (b ? b.best : 0) + '%"></i></div></td></tr>'; }).join("") + '</table></div></div>' +
        '<div class="block"><h2>Жұмыстар</h2>' + (r.submissions.length ? '<div class="table-wrap"><table><tr><th>Уақыты</th><th>Тақырып</th><th>Күйі</th><th>Баға</th><th>Оқытушы түсініктемесі</th></tr>' +
          r.submissions.slice().reverse().map(s => '<tr><td class="mono">' + fmt(s.time) + '</td><td>' + esc(s.topic) + '</td><td>' + statusTag(s.status) + '</td><td class="mono" style="font-weight:600">' + esc(s.grade) + '</td><td>' + esc(s.comment) + '</td></tr>').join("") + '</table></div>'
          : '<p class="muted">Әзірге жұмыс тапсырылмаған.</p>') + '</div>' +
        '<div class="block"><h2>Ойындар мен челлендждер</h2>' + (Object.keys(gbest).length ? '<table><tr><th>Ойын</th><th>Ең жақсы ұпай</th></tr>' +
          Object.keys(gbest).sort().map(g => '<tr><td class="mono">' + esc(gameName(g)) + '</td><td class="mono" style="font-weight:600">' + gbest[g] + '</td></tr>').join("") + '</table>'
          : '<p class="muted">Әлі ойнаған жоқсыз. <a href="games.html">Ойындар →</a></p>') + '</div>';
    } catch (e) { root.innerHTML = '<div class="msg show err">' + esc(e.message) + '</div>'; }
  }
  function statusTag(s) { const c = s === "Тексерілді" ? "g" : s === "Қайта тапсыру" ? "r" : "a"; return '<span class="tag ' + c + '">' + esc(s || "Тексерілмеген") + '</span>'; }
  function gameName(g) {
    const [kind, id] = g.split(":");
    if (kind === "sort" && window.DECKS && window.DECKS[id]) return "Сортировщик · " + window.DECKS[id].title;
    if (kind === "ctf" && window.CTF) { const c = window.CTF.find(x => x.id === id); if (c) return "SOC-терминал · " + c.title; }
    return g;
  }
  window.Site.statusTag = statusTag; window.Site.gameName = gameName;

  /* ---------- шапка, бүйір мәзір, анимация ---------- */
  function initChrome() {
    const btn = $("#sb-btn");
    if (btn) {
      if (!$("#sb")) btn.style.display = "none";
      btn.addEventListener("click", () => document.body.classList.toggle("sb-open"));
      document.addEventListener("click", e => {
        if (document.body.classList.contains("sb-open") && !e.target.closest("#sb") && !e.target.closest("#sb-btn"))
          document.body.classList.remove("sb-open");
      });
    }
    const nav = $("#side-nav");
    if (nav && "IntersectionObserver" in window) {
      const links = [...nav.querySelectorAll("a")];
      const io = new IntersectionObserver(es => es.forEach(e => {
        if (!e.isIntersecting) return;
        links.forEach(a => a.classList.toggle("on", a.getAttribute("href") === "#" + e.target.id));
      }), { rootMargin: "-10% 0px -80% 0px" });
      links.forEach(a => { const el = document.querySelector(a.getAttribute("href")); if (el) io.observe(el); });
    }
  }

  /* ---------- басты беттегі «терминал» ---------- */
  function heroTyping() {
    const pre = $("#hero-term");
    if (!pre) return;
    const L = [
      ['<span class="t-g">$</span> ', "python discover.py --scan scans/today.json"],
      ['', '<span class="t-m">Табылған құрылғылар: 19 · </span><span class="t-r">тіркелмеген: 10.10.2.66</span>'],
      ['<span class="t-g">$</span> ', "python detect.py --method rules"],
      ['', '<span class="t-a">10:00 pc-lab-07   port_scan    dst_ports=912</span>'],
      ['', '<span class="t-a">03:10 srv-file-01 exfiltration external_mb=2875</span>'],
      ['<span class="t-g">$</span> ', "python sli.py --service lms"],
      ['', '<span class="t-r">🔴 PAGE: burn rate (1 сағ) = 17.5</span>'],
      ['<span class="t-g">$</span> ', "submit flag{...}"],
      ['', '<span class="t-g">✔ ДҰРЫС! +150 ұпай</span>']
    ];
    let i = 0, out = "";
    const next = () => {
      if (i >= L.length) return;
      const [p, t] = L[i++];
      if (p) {
        let k = 0; out += p;
        const typer = setInterval(() => { pre.innerHTML = out + esc(t.slice(0, ++k)) + '<span class="t-g">▌</span>'; if (k >= t.length) { clearInterval(typer); out += esc(t) + "\n"; setTimeout(next, 350); } }, 28);
      } else { out += t + "\n"; pre.innerHTML = out; setTimeout(next, 450); }
    };
    next();
  }

  /* ---------- бағаны кодпен тексеру ---------- */
  function initGrade() {
    const form = $("#grade-form");
    if (!form) return;
    form.onsubmit = async e => {
      e.preventDefault(); const m = $("#grade-msg");
      msg(m, "info", "іздеуде…");
      try {
        const r = await api("check", { id: form.code.value.trim().toUpperCase() });
        if (!r.found) return msg(m, "err", "Код табылмады");
        msg(m, "ok", "<b>" + esc(r.name) + "</b> · " + esc(r.topic) + "<br>Күйі: " + esc(r.status) + (r.grade !== "" ? "<br>Баға: <b>" + esc(r.grade) + "</b>" : "") + (r.comment ? "<br>" + esc(r.comment) : ""));
      } catch (err) { msg(m, "err", esc(err.message)); }
    };
  }

  document.addEventListener("DOMContentLoaded", () => {
    renderUser(); initLogin(); renderVideo(); initQuiz(); initCtf(); initSorters(); initSubmit(); initCabinet(); initGrade(); heroTyping(); initChrome();
    const bg = $("#board-game"); if (bg) { bg.onchange = loadBoard; loadBoard(); }
  });
})();
