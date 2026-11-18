/* Студент бөлімі: тест, жұмыс тапсыру, бағаны тексеру, бейне. */
(function () {
  const S = window.SITE || {};
  const $ = (sel, root) => (root || document).querySelector(sel);
  const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));

  function api(action, data) {
    if (!S.API_URL) return Promise.reject(new Error("NO_API"));
    return fetch(S.API_URL, { method: "POST", body: JSON.stringify(Object.assign({ action: action }, data)) })
      .then(r => r.json());
  }
  window.SiteApi = api;

  function esc(v) {
    return String(v == null ? "" : v).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }

  function showMsg(el, kind, html) {
    el.className = "msg show " + kind;
    el.innerHTML = html;
  }

  function student() {
    try { return JSON.parse(localStorage.getItem("student") || "{}"); } catch (e) { return {}; }
  }
  function saveStudent(s) {
    try { localStorage.setItem("student", JSON.stringify(s)); } catch (e) { /* жоқ */ }
  }

  function fillGroups() {
    $$("select[name=group]").forEach(sel => {
      (S.GROUPS || ["ИС 3-1"]).forEach(g => sel.add(new Option(g, g)));
    });
    const st = student();
    $$("input[name=name]").forEach(i => { if (st.name) i.value = st.name; });
    $$("select[name=group]").forEach(i => { if (st.group) i.value = st.group; });
  }

  /* ---------- бейне ---------- */
  function renderVideo() {
    const box = $("#video-box");
    if (!box) return;
    const url = (S.VIDEOS || {})[box.dataset.topic] || "";
    if (!url) {
      box.innerHTML = '<div class="video-empty"><div><div style="font-size:42px">🎬</div>Бейнетүсіндірме жақында қосылады.<br>Әзірге «Түсіндірме» бөлімін оқыңыз.</div></div>';
      return;
    }
    let m = url.match(/(?:youtu\.be\/|v=|embed\/|shorts\/)([\w-]{11})/);
    if (m) {
      box.innerHTML = '<iframe src="https://www.youtube-nocookie.com/embed/' + m[1] + '" title="Бейнетүсіндірме" allowfullscreen loading="lazy"></iframe>';
    } else {
      box.innerHTML = '<video controls preload="metadata" src="' + url.replace(/"/g, "") + '"></video>';
    }
  }

  /* ---------- тест ---------- */
  function renderQuiz() {
    const root = $("#quiz");
    if (!root || !window.QUIZ) return;
    const quiz = window.QUIZ;
    root.innerHTML = quiz.map((q, i) =>
      '<div class="q" data-i="' + i + '"><div class="qt">' + (i + 1) + ". " + q.q + "</div>" +
      q.o.map((o, j) => '<label><input type="radio" name="q' + i + '" value="' + j + '"> <span>' + o + "</span></label>").join("") +
      '<div class="exp">💡 ' + q.e + "</div></div>").join("");
    $("#quiz-check").addEventListener("click", function () {
      const form = $("#quiz-form");
      const name = form.name.value.trim(), group = form.group.value;
      const msg = $("#quiz-msg");
      const unanswered = quiz.filter((q, i) => !$('input[name=q' + i + ']:checked', root)).length;
      if (unanswered) { showMsg(msg, "err", "Барлық сұраққа жауап беріңіз (қалды: " + unanswered + ")."); return; }
      if (!name) { showMsg(msg, "err", "Аты-жөніңізді жазыңыз."); return; }
      saveStudent({ name: name, group: group });
      const sf = $("#submit-form");
      if (sf && !sf.name.value) { sf.name.value = name; sf.group.value = group; }
      let score = 0;
      const answers = [];
      quiz.forEach((q, i) => {
        const box = $('.q[data-i="' + i + '"]', root);
        const chosen = Number($('input[name=q' + i + ']:checked', root).value);
        answers.push(chosen + 1);
        if (chosen === q.a) score++;
        $$("label", box).forEach((lab, j) => {
          if (j === q.a) lab.classList.add("right");
          else if (j === chosen) lab.classList.add("wrong");
          $("input", lab).disabled = true;
        });
        box.classList.add("done");
      });
      this.disabled = true;
      const pct = Math.round(100 * score / quiz.length);
      let text = '<span class="score">' + score + " / " + quiz.length + " (" + pct + "%)</span><br>";
      text += pct >= 80 ? "Керемет! Тақырыпты жақсы түсіндіңіз." : pct >= 50 ? "Жаман емес. Қате жауаптардың түсіндірмесін оқыңыз." : "«Түсіндірме» бөлімін қайта оқып шығыңыз.";
      showMsg(msg, pct >= 50 ? "ok" : "info", text);
      api("test", { name: name, group: group, topic: root.dataset.topic, score: score, total: quiz.length, answers: answers.join(",") })
        .then(r => { if (r.ok) msg.innerHTML += "<br><small>Нәтиже оқытушыға жіберілді ✔</small>"; })
        .catch(() => { msg.innerHTML += "<br><small>Нәтиже оқытушыға жіберілмеді (жүйе әлі қосылмаған).</small>"; });
    });
  }

  /* ---------- жұмыс тапсыру ---------- */
  function readFile(file) {
    return new Promise((resolve, reject) => {
      const fr = new FileReader();
      fr.onload = () => resolve(String(fr.result).split(",")[1]);
      fr.onerror = reject;
      fr.readAsDataURL(file);
    });
  }

  function initSubmit() {
    const form = $("#submit-form");
    if (!form) return;
    const msg = $("#submit-msg");
    if (!S.API_URL) showMsg(msg, "info", "Жұмыс тапсыру жүйесі әлі қосылмаған. Оқытушының нұсқауын күтіңіз.");
    form.addEventListener("submit", async function (e) {
      e.preventDefault();
      const btn = $("button[type=submit]", form);
      const data = {
        name: form.name.value.trim(), group: form.group.value, topic: form.dataset.topic,
        variant: form.variant.value, link: form.link.value.trim(), comment: form.comment.value.trim()
      };
      if (!data.name) return showMsg(msg, "err", "Аты-жөніңізді жазыңыз.");
      const f = form.file.files[0];
      if (!f && !data.link) return showMsg(msg, "err", "Есеп файлын жүктеңіз немесе сілтеме қалдырыңыз.");
      if (f && f.size > 10 * 1024 * 1024) return showMsg(msg, "err", "Файл 10 МБ-тан аспауы керек.");
      saveStudent({ name: data.name, group: data.group });
      btn.disabled = true;
      showMsg(msg, "info", "Жіберілуде… күте тұрыңыз.");
      try {
        if (f) data.file = { name: f.name, mime: f.type, data: await readFile(f) };
        const r = await api("submit", data);
        if (!r.ok) throw new Error(r.error || "Қате");
        showMsg(msg, "ok", "Жұмысыңыз қабылданды! Бағаны тексеру коды:<div class='code-big'>" + esc(r.id) +
          "</div>Кодты жазып алыңыз — оны <a href='grade.html'>«Бағамды тексеру»</a> бетінде енгізесіз.");
        form.reset();
        fillGroups();
      } catch (err) {
        showMsg(msg, "err", err.message === "NO_API" ? "Жүйе әлі қосылмаған — оқытушыға хабарлаңыз." : "Жіберу сәтсіз: " + err.message);
      } finally {
        btn.disabled = false;
      }
    });
  }

  /* ---------- бағаны тексеру ---------- */
  function initGrade() {
    const form = $("#grade-form");
    if (!form) return;
    const msg = $("#grade-msg");
    form.addEventListener("submit", async function (e) {
      e.preventDefault();
      const id = form.code.value.trim().toUpperCase();
      if (!id) return;
      showMsg(msg, "info", "Іздеуде…");
      try {
        const r = await api("check", { id: id });
        if (!r.found) return showMsg(msg, "err", "Мұндай код табылмады. Кодты тексеріңіз.");
        const graded = r.grade !== "" && r.grade != null;
        showMsg(msg, graded ? "ok" : "info",
          "<b>" + esc(r.name) + "</b> · " + esc(r.topic) + "<br>Күйі: " + esc(r.status) +
          (graded ? "<br>Баға: <span class='score'>" + esc(r.grade) + " ұпай</span>" : "") +
          (r.comment ? "<br>Оқытушы түсініктемесі: " + esc(r.comment) : ""));
      } catch (err) {
        showMsg(msg, "err", err.message === "NO_API" ? "Жүйе әлі қосылмаған." : "Қате: " + err.message);
      }
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    fillGroups();
    renderVideo();
    renderQuiz();
    initSubmit();
    initGrade();
  });
})();
