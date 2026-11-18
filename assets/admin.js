/* Оқытушы панелі: жұмыстарды қарау, бағалау, тест нәтижелері. */
(function () {
  const $ = (s, r) => (r || document).querySelector(s);
  const api = (a, d) => window.SiteApi(a, d);
  let PW = sessionStorage.getItem("adminPw") || "";
  let DATA = { submissions: [], tests: [] };
  let TAB = "subs";
  let CURRENT = null;

  const esc = v => String(v == null ? "" : v).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const fmt = t => { const d = new Date(t); return isNaN(d) ? esc(t) : d.toLocaleString("kk-KZ", { dateStyle: "short", timeStyle: "short" }); };
  const safeUrl = u => /^https?:\/\//i.test(String(u || "")) ? esc(u) : "";

  function statusTag(s) {
    const cls = s === "Тексерілді" ? "green" : s === "Қайта тапсыру" ? "red" : "amber";
    return '<span class="tag ' + cls + '">' + esc(s || "Тексерілмеген") + "</span>";
  }

  function show(id) {
    ["login", "panel"].forEach(x => $("#" + x).style.display = x === id ? "block" : "none");
  }

  async function login(pw) {
    const msg = $("#login-msg");
    msg.className = "msg show info"; msg.textContent = "Тексерілуде…";
    try {
      const r = await api("login", { password: pw });
      if (!r.ok) { msg.className = "msg show err"; msg.textContent = "Құпиясөз қате."; return; }
      PW = pw; sessionStorage.setItem("adminPw", pw);
      show("panel"); load();
    } catch (e) {
      msg.className = "msg show err";
      msg.textContent = e.message === "NO_API" ? "assets/config.js ішінде API_URL әлі жазылмаған (backend/ОРНАТУ.md қараңыз)." : "Байланыс қатесі: " + e.message;
    }
  }

  async function load() {
    $("#list").innerHTML = "<p>Жүктелуде…</p>";
    const r = await api("list", { password: PW });
    if (!r.ok) { sessionStorage.removeItem("adminPw"); show("login"); return; }
    DATA = r;
    fillFilters();
    render();
  }

  function fillFilters() {
    const topics = new Set(), groups = new Set();
    DATA.submissions.concat(DATA.tests).forEach(x => { topics.add(x.topic); groups.add(x.group); });
    const fill = (sel, vals) => {
      const cur = sel.value;
      sel.innerHTML = '<option value="">' + sel.dataset.all + "</option>" + [...vals].sort().map(v => '<option>' + esc(v) + "</option>").join("");
      sel.value = cur;
    };
    fill($("#f-topic"), topics); fill($("#f-group"), groups);
  }

  function filtered(list) {
    const t = $("#f-topic").value, g = $("#f-group").value, st = $("#f-status").value, q = $("#f-q").value.trim().toLowerCase();
    return list.filter(x => (!t || x.topic === t) && (!g || x.group === g) &&
      (!st || TAB !== "subs" || (x.status || "Тексерілмеген") === st) &&
      (!q || String(x.name).toLowerCase().includes(q)));
  }

  function render() {
    const subs = DATA.submissions, tests = DATA.tests;
    const unchecked = subs.filter(s => (s.status || "Тексерілмеген") === "Тексерілмеген").length;
    const avgTest = tests.length ? Math.round(tests.reduce((a, t) => a + Number(t.percent || 0), 0) / tests.length) : 0;
    $("#stats").innerHTML =
      '<div class="stat"><b>' + subs.length + "</b><span>тапсырылған жұмыс</span></div>" +
      '<div class="stat"><b style="color:#b7791f">' + unchecked + "</b><span>тексерілмеген</span></div>" +
      '<div class="stat"><b>' + tests.length + "</b><span>тест тапсырылды</span></div>" +
      '<div class="stat"><b>' + avgTest + "%</b><span>тесттің орташа нәтижесі</span></div>";
    $("#f-status").style.display = TAB === "subs" ? "" : "none";
    if (TAB === "subs") {
      const rows = filtered(subs).sort((a, b) => new Date(b.time) - new Date(a.time));
      $("#list").innerHTML = rows.length ? '<div class="table-wrap"><table><tr><th>Уақыты</th><th>Аты-жөні</th><th>Тобы</th><th>Тақырып</th><th>Нұсқа</th><th>Жұмыс</th><th>Күйі</th><th>Баға</th></tr>' +
        rows.map(s => '<tr class="clickable" data-id="' + esc(s.id) + '"><td>' + fmt(s.time) + "</td><td>" + esc(s.name) + "</td><td>" + esc(s.group) +
          "</td><td>" + esc(s.topic) + "</td><td>" + esc(s.variant) + "</td><td>" + (s.file ? "📎 файл " : "") + (s.link ? "🔗 сілтеме" : "") +
          "</td><td>" + statusTag(s.status) + "</td><td><b>" + esc(s.grade) + "</b></td></tr>").join("") + "</table></div>"
        : "<p>Жұмыс жоқ.</p>";
      $("#list").querySelectorAll("tr.clickable").forEach(tr => tr.addEventListener("click", () => openSub(tr.dataset.id)));
    } else {
      const rows = filtered(tests).sort((a, b) => new Date(b.time) - new Date(a.time));
      $("#list").innerHTML = rows.length ? '<div class="table-wrap"><table><tr><th>Уақыты</th><th>Аты-жөні</th><th>Тобы</th><th>Тақырып</th><th>Нәтиже</th><th>%</th></tr>' +
        rows.map(t => "<tr><td>" + fmt(t.time) + "</td><td>" + esc(t.name) + "</td><td>" + esc(t.group) + "</td><td>" + esc(t.topic) +
          "</td><td>" + esc(t.score) + " / " + esc(t.total) + '</td><td><span class="tag ' + (t.percent >= 80 ? "green" : t.percent >= 50 ? "amber" : "red") + '">' + esc(t.percent) + "%</span></td></tr>").join("") + "</table></div>"
        : "<p>Тест нәтижелері жоқ.</p>";
    }
  }

  function openSub(id) {
    const s = DATA.submissions.find(x => x.id === id);
    if (!s) return;
    CURRENT = s;
    $("#m-info").innerHTML =
      "<div>Аты-жөні</div><div><b>" + esc(s.name) + "</b></div>" +
      "<div>Тобы / нұсқа</div><div>" + esc(s.group) + " / " + esc(s.variant || "—") + "</div>" +
      "<div>Тақырып</div><div>" + esc(s.topic) + "</div>" +
      "<div>Тапсырылды</div><div>" + fmt(s.time) + "</div>" +
      "<div>Файл</div><div>" + (safeUrl(s.file) ? '<a href="' + safeUrl(s.file) + '" target="_blank" rel="noopener">Google Drive-та ашу ↗</a>' : "—") + "</div>" +
      "<div>Сілтеме</div><div>" + (safeUrl(s.link) ? '<a href="' + safeUrl(s.link) + '" target="_blank" rel="noopener">' + esc(s.link) + "</a>" : "—") + "</div>" +
      "<div>Студент түсініктемесі</div><div>" + (esc(s.comment) || "—") + "</div>" +
      "<div>Тексеру коды</div><div><code>" + esc(s.id) + "</code></div>";
    $("#m-grade").value = s.grade === "" || s.grade == null ? "" : s.grade;
    $("#m-status").value = s.status && s.status !== "Тексерілмеген" ? s.status : "Тексерілді";
    $("#m-comment").value = s.teacherComment || "";
    $("#m-msg").className = "msg";
    $("#modal").classList.add("show");
  }

  async function saveGrade() {
    const btn = $("#m-save"), msg = $("#m-msg");
    const g = $("#m-grade").value.trim();
    if (g !== "" && (isNaN(g) || g < 0 || g > 100)) { msg.className = "msg show err"; msg.textContent = "Баға 0–100 аралығында болуы керек."; return; }
    btn.disabled = true;
    try {
      const r = await api("grade", { password: PW, id: CURRENT.id, grade: g, status: $("#m-status").value, teacherComment: $("#m-comment").value });
      if (!r.ok) throw new Error(r.error);
      Object.assign(CURRENT, { grade: g === "" ? "" : Number(g), status: $("#m-status").value, teacherComment: $("#m-comment").value });
      $("#modal").classList.remove("show");
      render();
    } catch (e) {
      msg.className = "msg show err"; msg.textContent = "Сақталмады: " + e.message;
    } finally { btn.disabled = false; }
  }

  function exportCsv() {
    const list = TAB === "subs" ? filtered(DATA.submissions) : filtered(DATA.tests);
    const cols = TAB === "subs" ? ["time", "name", "group", "topic", "variant", "status", "grade", "teacherComment", "link", "file"] : ["time", "name", "group", "topic", "score", "total", "percent"];
    const csv = "﻿" + [cols.join(";")].concat(list.map(x => cols.map(c => '"' + String(x[c] == null ? "" : x[c]).replace(/"/g, '""') + '"').join(";"))).join("\n");
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
    a.download = (TAB === "subs" ? "жұмыстар" : "тесттер") + ".csv";
    a.click();
  }

  document.addEventListener("DOMContentLoaded", function () {
    $("#login-form").addEventListener("submit", e => { e.preventDefault(); login($("#pw").value); });
    ["#f-topic", "#f-group", "#f-status"].forEach(s => $(s).addEventListener("change", render));
    $("#f-q").addEventListener("input", render);
    $("#reload").addEventListener("click", load);
    $("#export").addEventListener("click", exportCsv);
    $("#logout").addEventListener("click", () => { sessionStorage.removeItem("adminPw"); PW = ""; show("login"); });
    document.querySelectorAll(".tabs button").forEach(b => b.addEventListener("click", () => {
      TAB = b.dataset.tab;
      document.querySelectorAll(".tabs button").forEach(x => x.classList.toggle("active", x === b));
      render();
    }));
    $("#m-save").addEventListener("click", saveGrade);
    $("#m-close").addEventListener("click", () => $("#modal").classList.remove("show"));
    if (PW) { show("panel"); load(); } else show("login");
  });
})();
