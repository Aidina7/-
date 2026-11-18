/* Оқытушы панелі: студенттер, тесттер, жұмыстар, ойындар. */
(function () {
  const $ = (s, r) => (r || document).querySelector(s);
  const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
  const { api, esc, fmt, statusTag, gameName } = window.Site;
  const T = (window.SITE || {}).TOPICS || {};
  let PW = sessionStorage.getItem("op_admin") || "";
  let D = { students: [], submissions: [], tests: [], games: [] };
  let TAB = "students", CUR = null;
  const safeUrl = u => /^https?:\/\//i.test(String(u || "")) ? esc(u) : "";
  const topicName = k => T[k] || k;

  function show(id) { ["login", "panel"].forEach(x => $("#" + x).style.display = x === id ? "" : "none"); }

  async function login(pw) {
    const m = $("#login-msg");
    m.className = "msg show info"; m.textContent = "тексерілуде…";
    try {
      const r = await api("adminLogin", { password: pw });
      if (!r.ok) { m.className = "msg show err"; m.textContent = "Құпиясөз қате"; return; }
      PW = pw; sessionStorage.setItem("op_admin", pw); show("panel"); load();
    } catch (e) { m.className = "msg show err"; m.textContent = e.message; }
  }

  async function load() {
    $("#list").innerHTML = '<p class="muted">жүктелуде…</p>';
    const r = await api("list", { password: PW });
    if (!r.ok) { sessionStorage.removeItem("op_admin"); show("login"); return; }
    D = r; fillFilters(); render();
  }

  function fillFilters() {
    const g = new Set(D.students.map(s => s.group).concat(D.submissions.map(s => s.group)));
    const sel = $("#f-group"), cur = sel.value;
    sel.innerHTML = '<option value="">барлық топтар</option>' + [...g].filter(Boolean).sort().map(x => "<option>" + esc(x) + "</option>").join("");
    sel.value = cur;
    const ts = $("#f-topic");
    if (ts.options.length <= 1) ts.innerHTML = '<option value="">барлық тақырыптар</option>' + Object.keys(T).map(k => '<option value="' + k + '">' + esc(T[k]) + "</option>").join("");
  }

  const fGroup = x => !$("#f-group").value || x.group === $("#f-group").value;
  const fQ = x => { const q = $("#f-q").value.trim().toLowerCase(); return !q || String(x.name).toLowerCase().includes(q) || String(x.login || "").includes(q); };
  const fTopic = (x, key) => { const t = $("#f-topic").value; return !t || x[key] === t || x[key] === T[t]; };

  function bestTests(login) {
    const b = {};
    D.tests.filter(t => t.login === login).forEach(t => { b[t.topic] = Math.max(b[t.topic] || 0, Number(t.percent)); });
    return b;
  }
  function gamePoints(login) {
    const b = {};
    D.games.filter(g => g.login === login).forEach(g => { b[g.game] = Math.max(b[g.game] || 0, Number(g.score)); });
    return Object.values(b).reduce((a, c) => a + c, 0);
  }

  function render() {
    const unchecked = D.submissions.filter(s => (s.status || "Тексерілмеген") === "Тексерілмеген").length;
    const avg = D.tests.length ? Math.round(D.tests.reduce((a, t) => a + Number(t.percent), 0) / D.tests.length) : 0;
    $("#stats").innerHTML = '<div class="stat"><b>' + D.students.length + '</b><span>студент тіркелді</span></div><div class="stat"><b style="color:var(--amber)">' + unchecked +
      '</b><span>тексерілмеген жұмыс</span></div><div class="stat"><b>' + D.tests.length + '</b><span>тест әрекеті</span></div><div class="stat"><b>' + avg + '%</b><span>тесттің орташа нәтижесі</span></div>';
    $("#f-status").style.display = TAB === "subs" ? "" : "none";
    const L = $("#list");
    if (TAB === "students") {
      const rows = D.students.filter(s => fGroup(s) && fQ(s));
      L.innerHTML = rows.length ? '<div class="table-wrap"><table><tr><th>студент</th><th>логин</th><th>топ</th>' + Object.keys(T).map(k => "<th>" + esc(k) + "</th>").join("") +
        '<th>жұмыс</th><th>ұпай</th><th>соңғы кіру</th></tr>' + rows.map(s => {
          const b = bestTests(s.login), subs = D.submissions.filter(x => x.login === s.login);
          return '<tr class="click" data-login="' + esc(s.login) + '"><td>' + esc(s.name) + (s.active ? "" : ' <span class="tag r">бұғатталған</span>') + '</td><td class="mono">' + esc(s.login) + '</td><td>' + esc(s.group) + '</td>' +
            Object.keys(T).map(k => '<td class="mono">' + (b[k] != null ? b[k] + "%" : "—") + "</td>").join("") +
            '<td class="mono">' + subs.length + '</td><td class="mono" style="color:var(--amber)">' + gamePoints(s.login) + '</td><td class="mono">' + fmt(s.last) + "</td></tr>";
        }).join("") + "</table></div>" : '<p class="muted">Студенттер әлі тіркелмеген.</p>';
      $$("tr.click", L).forEach(tr => tr.onclick = () => openStudent(tr.dataset.login));
    } else if (TAB === "subs") {
      const st = $("#f-status").value;
      const rows = D.submissions.filter(s => fGroup(s) && fQ(s) && fTopic(s, "topic") && (!st || (s.status || "Тексерілмеген") === st)).sort((a, b) => new Date(b.time) - new Date(a.time));
      L.innerHTML = rows.length ? '<div class="table-wrap"><table><tr><th>уақыты</th><th>студент</th><th>топ</th><th>тақырып</th><th>нұсқа</th><th>жұмыс</th><th>күйі</th><th>баға</th></tr>' +
        rows.map(s => '<tr class="click" data-id="' + esc(s.id) + '"><td class="mono">' + fmt(s.time) + "</td><td>" + esc(s.name) + "</td><td>" + esc(s.group) + "</td><td>" + esc(s.topic) +
          '</td><td class="mono">' + esc(s.variant) + "</td><td>" + (s.file ? "файл " : "") + (s.link ? "сілтеме" : "") + "</td><td>" + statusTag(s.status) + '</td><td class="mono" style="color:var(--acc)">' + esc(s.grade) + "</td></tr>").join("") + "</table></div>"
        : '<p class="muted">Жұмыс жоқ.</p>';
      $$("tr.click", L).forEach(tr => tr.onclick = () => openSub(tr.dataset.id));
    } else if (TAB === "tests") {
      const rows = D.tests.filter(t => fGroup(t) && fQ(t) && fTopic(t, "topic")).sort((a, b) => new Date(b.time) - new Date(a.time));
      L.innerHTML = rows.length ? '<div class="table-wrap"><table><tr><th>уақыты</th><th>студент</th><th>топ</th><th>тақырып</th><th>№</th><th>нәтиже</th><th>уақыт</th><th>жауаптар (id:нұсқа ✓/✗)</th></tr>' +
        rows.map(t => '<tr><td class="mono">' + fmt(t.time) + "</td><td>" + esc(t.name) + "</td><td>" + esc(t.group) + "</td><td>" + esc(topicName(t.topic)) + '</td><td class="mono">' + esc(t.attempt) +
          '</td><td><span class="tag ' + (t.percent >= 80 ? "g" : t.percent >= 50 ? "a" : "r") + '">' + esc(t.score) + "/" + esc(t.total) + " · " + esc(t.percent) + '%</span></td><td class="mono">' + Math.round((t.seconds || 0) / 60) + ' мин</td><td class="ans">' + esc(t.answers) + "</td></tr>").join("") + "</table></div>"
        : '<p class="muted">Тест нәтижелері жоқ.</p>';
    } else {
      const rows = D.games.filter(g => fGroup(g) && fQ(g)).sort((a, b) => new Date(b.time) - new Date(a.time));
      L.innerHTML = rows.length ? '<div class="table-wrap"><table><tr><th>уақыты</th><th>студент</th><th>топ</th><th>ойын</th><th>ұпай</th><th>дәлдік</th><th>мәлімет</th></tr>' +
        rows.map(g => '<tr><td class="mono">' + fmt(g.time) + "</td><td>" + esc(g.name) + "</td><td>" + esc(g.group) + "</td><td>" + esc(gameName(g.game)) + '</td><td class="mono" style="color:var(--amber)">' + esc(g.score) +
          '</td><td class="mono">' + esc(g.accuracy) + '%</td><td class="ans">' + esc(g.detail) + "</td></tr>").join("") + "</table></div>"
        : '<p class="muted">Ойын нәтижелері жоқ.</p>';
    }
  }

  function openStudent(login) {
    const s = D.students.find(x => x.login === login);
    if (!s) return;
    const tests = D.tests.filter(t => t.login === login), subs = D.submissions.filter(x => x.login === login), games = D.games.filter(g => g.login === login);
    $("#modal-body").innerHTML = '<h3>' + esc(s.name) + '</h3><div class="kv"><div>логин</div><div class="mono">' + esc(s.login) + '</div><div>топ</div><div>' + esc(s.group) +
      '</div><div>тіркелген</div><div>' + fmt(s.created) + '</div><div>соңғы кіру</div><div>' + fmt(s.last) + '</div><div>ойын ұпайы</div><div class="mono" style="color:var(--amber)">' + gamePoints(login) + '</div></div>' +
      '<h4>тест әрекеттері</h4>' + (tests.length ? '<table><tr><th>уақыты</th><th>тақырып</th><th>№</th><th>нәтиже</th><th>жауаптар</th></tr>' + tests.map(t => '<tr><td class="mono">' + fmt(t.time) + "</td><td>" + esc(topicName(t.topic)) + '</td><td class="mono">' + esc(t.attempt) + '</td><td class="mono">' + esc(t.percent) + '%</td><td class="ans">' + esc(t.answers) + "</td></tr>").join("") + "</table>" : '<p class="muted">жоқ</p>') +
      '<h4>жұмыстар</h4>' + (subs.length ? '<table><tr><th>тақырып</th><th>күйі</th><th>баға</th></tr>' + subs.map(x => "<tr><td>" + esc(x.topic) + "</td><td>" + statusTag(x.status) + '</td><td class="mono">' + esc(x.grade) + "</td></tr>").join("") + "</table>" : '<p class="muted">жоқ</p>') +
      '<h4>ойындар</h4>' + (games.length ? '<table><tr><th>ойын</th><th>ұпай</th><th>дәлдік</th></tr>' + games.map(g => "<tr><td>" + esc(gameName(g.game)) + '</td><td class="mono">' + esc(g.score) + '</td><td class="mono">' + esc(g.accuracy) + "%</td></tr>").join("") + "</table>" : '<p class="muted">жоқ</p>') +
      '<div class="msg" id="st-msg"></div><div class="bar" style="margin-top:14px"><button class="btn small ghost" id="st-reset">құпиясөзді қалпына келтіру</button><button class="btn small danger" id="st-block">' + (s.active ? "бұғаттау" : "бұғаттан шығару") + '</button><button class="btn small ghost" data-close>жабу</button></div>';
    $("#st-reset").onclick = async () => {
      if (!confirm(s.name + " үшін жаңа құпиясөз жасалсын ба?")) return;
      const r = await api("resetPassword", { password: PW, login: login });
      const m = $("#st-msg"); m.className = "msg show " + (r.ok ? "ok" : "err");
      m.innerHTML = r.ok ? "Жаңа құпиясөз: <b class='mono'>" + esc(r.newPassword) + "</b> — студентке беріңіз." : esc(r.error);
    };
    $("#st-block").onclick = async () => {
      const r = await api("setActive", { password: PW, login: login, active: !s.active });
      if (r.ok) { s.active = !s.active; closeModal(); render(); }
    };
    openModal();
  }

  function openSub(id) {
    const s = D.submissions.find(x => x.id === id);
    if (!s) return;
    CUR = s;
    $("#modal-body").innerHTML = '<h3>жұмысты бағалау</h3><div class="kv"><div>студент</div><div><b>' + esc(s.name) + "</b> · " + esc(s.group) + '</div><div>тақырып / нұсқа</div><div>' + esc(s.topic) + " / " + esc(s.variant || "—") +
      '</div><div>тапсырылды</div><div>' + fmt(s.time) + '</div><div>файл</div><div>' + (safeUrl(s.file) ? '<a href="' + safeUrl(s.file) + '" target="_blank" rel="noopener">Google Drive-та ашу ↗</a>' : "—") +
      '</div><div>сілтеме</div><div>' + (safeUrl(s.link) ? '<a href="' + safeUrl(s.link) + '" target="_blank" rel="noopener">' + esc(s.link) + "</a>" : "—") + '</div><div>студент түсініктемесі</div><div>' + (esc(s.comment) || "—") + '</div></div>' +
      '<div class="form"><div class="row"><label class="f">баға (0–100)<input id="m-grade" type="number" min="0" max="100" value="' + esc(s.grade) + '"></label><label class="f">күйі<select id="m-status"><option>Тексерілді</option><option>Қайта тапсыру</option><option>Тексерілмеген</option></select></label></div>' +
      '<label class="f">түсініктеме (студент көреді)<textarea id="m-comment">' + esc(s.teacherComment) + '</textarea></label><div class="msg" id="m-msg"></div><div class="bar"><button class="btn" id="m-save">сақтау</button><button class="btn ghost" data-close>жабу</button></div></div>';
    $("#m-status").value = s.status && s.status !== "Тексерілмеген" ? s.status : "Тексерілді";
    $("#m-save").onclick = async function () {
      const g = $("#m-grade").value.trim(), m = $("#m-msg");
      if (g !== "" && (isNaN(g) || g < 0 || g > 100)) { m.className = "msg show err"; m.textContent = "Баға 0–100"; return; }
      this.disabled = true;
      const r = await api("grade", { password: PW, id: s.id, grade: g, status: $("#m-status").value, teacherComment: $("#m-comment").value });
      this.disabled = false;
      if (!r.ok) { m.className = "msg show err"; m.textContent = r.error; return; }
      Object.assign(s, { grade: g === "" ? "" : Number(g), status: $("#m-status").value, teacherComment: $("#m-comment").value });
      closeModal(); render();
    };
    openModal();
  }

  function openModal() { $("#modal").classList.add("show"); $$("[data-close]", $("#modal")).forEach(b => b.onclick = closeModal); }
  function closeModal() { $("#modal").classList.remove("show"); }

  function exportCsv() {
    let cols, list;
    if (TAB === "students") {
      cols = ["name", "login", "group"].concat(Object.keys(T)).concat(["points"]);
      list = D.students.filter(s => fGroup(s) && fQ(s)).map(s => Object.assign({ points: gamePoints(s.login) }, s, bestTests(s.login)));
    } else if (TAB === "subs") { cols = ["time", "name", "group", "topic", "variant", "status", "grade", "teacherComment", "file", "link"]; list = D.submissions; }
    else if (TAB === "tests") { cols = ["time", "name", "group", "topic", "attempt", "score", "total", "percent", "seconds"]; list = D.tests; }
    else { cols = ["time", "name", "group", "game", "score", "accuracy", "detail"]; list = D.games; }
    const csv = "﻿" + [cols.join(";")].concat(list.map(x => cols.map(c => '"' + String(x[c] == null ? "" : x[c]).replace(/"/g, '""') + '"').join(";"))).join("\n");
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
    a.download = TAB + ".csv"; a.click();
  }

  document.addEventListener("DOMContentLoaded", () => {
    $("#login-form").onsubmit = e => { e.preventDefault(); login($("#pw").value); };
    ["#f-group", "#f-topic", "#f-status"].forEach(s => $(s).onchange = render);
    $("#f-q").oninput = render;
    $("#reload").onclick = load;
    $("#export").onclick = exportCsv;
    $("#logout-admin").onclick = () => { sessionStorage.removeItem("op_admin"); PW = ""; show("login"); };
    $$(".tabs button").forEach(b => b.onclick = () => { TAB = b.dataset.tab; $$(".tabs button").forEach(x => x.classList.toggle("active", x === b)); render(); });
    $("#modal").onclick = e => { if (e.target.id === "modal") closeModal(); };
    if (PW) { show("panel"); load(); } else show("login");
  });
})();
