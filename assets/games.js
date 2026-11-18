/* «Сортировщик» ойыны: карточкаларды уақытқа қарсы дұрыс санатқа жіберу. */
window.DECKS = {
  devices: {
    title: "Құрылғыны таны", topic: "inventory",
    about: "Сканер көрсеткен «іздер» бойынша құрылғы түрін анықтаңыз.",
    cats: ["Сервер", "Жұмыс станциясы", "Принтер", "IP-камера", "Желілік жабдық", "IoT"],
    cards: [
      ["TTL 64 · порттар 22, 80, 443 · nginx/1.24 Ubuntu", 0, "Веб порттар + Linux баннері — веб-сервер."],
      ["TTL 128 · порттар 135, 445 · Dell", 1, "Windows (TTL 128), тек SMB/RPC — жұмыс станциясы."],
      ["TTL 64 · порттар 9100, 631, 515 · HP", 2, "9100 JetDirect, 631 IPP — принтер."],
      ["TTL 64 · порттар 80, 554 · Hikvision", 3, "554 RTSP — бейне ағыны, камера."],
      ["TTL 255 · порттар 22, 161 · Cisco", 4, "TTL 255 және SNMP — желілік жабдық."],
      ["TTL 64 · порттар 22, 1883 · Raspberry Pi", 5, "1883 — MQTT, IoT датчиктер хаттамасы."],
      ["TTL 128 · порттар 53, 88, 389, 445 · Windows Server", 0, "DNS + Kerberos + LDAP — домен контроллері."],
      ["TTL 64 · порт 5432 · PostgreSQL 16", 0, "Дерекқор сервері."],
      ["TTL 128 · порттар 135, 445, 3389 · Lenovo", 1, "Windows жұмыс станциясы, RDP қосулы."],
      ["TTL 64 · порттар 80, 443, 22 · Ubiquiti", 4, "Ubiquiti — Wi-Fi нүктесі, веб-интерфейсі бар желілік жабдық."],
      ["TTL 64 · порттар 80, 631, 9100 · Brother", 2, "Принтер."],
      ["TTL 64 · порттар 80, 554, 8000 · Dahua", 3, "554 RTSP — камера."],
      ["TTL 255 · порт 23 (telnet) · MikroTik", 4, "Маршрутизатор; telnet ашық — тәуекел!"],
      ["TTL 64 · порттар 5000, 7000 · Apple", 1, "macOS ноутбук (AirPlay порттары)."],
      ["TTL 64 · порттар 22, 8883 · Espressif", 5, "8883 — шифрланған MQTT, IoT."],
      ["TTL 128 · порттар 1433, 3389 · Windows Server", 0, "1433 — MS SQL Server."]
    ]
  },
  licenses: {
    title: "Лицензия аудиті", topic: "licenses",
    about: "Аудитор әр жағдай бойынша шешім қабылдайды.",
    cats: ["Заңды — OK", "Сатып алу / ауыстыру", "Жою (тыйым салынған)", "Қайта бөлу (shelfware)"],
    cards: [
      ["Office 2021: лицензия 15, орнатылған 19", 1, "Тапшылық 4 — сатып алу немесе LibreOffice."],
      ["7-Zip 25 компьютерде", 0, "LGPL, тегін."],
      ["KMSAuto Net pc-lab-12-де", 2, "Заңсыз белсендіргіш — жою, компьютерді тексеру."],
      ["Photoshop: 3 лицензия, 2-і 120 күн қолданылмаған", 3, "Қолданылмайтын лицензияны басқа адамға беру."],
      ["WinRAR 5 компьютерде, лицензия 0", 1, "Shareware — сатып алу немесе 7-Zip."],
      ["uTorrent зертхана компьютерінде", 2, "P2P клиент — тыйым салынған."],
      ["VS Code 30 компьютерде", 0, "Тегін, коммерциялық қолдануға рұқсат."],
      ["TeamViewer Free бухгалтерияда", 1, "Тегін нұсқа тек жеке мақсатқа — ұйымдық лицензия немесе балама."],
      ["Kaspersky: лицензия 25, орнатылған 23", 0, "Жеткілікті."],
      ["M365: 10 лицензия, 6 адам қолданады", 3, "4 лицензияны қайта бөлу немесе азайту."],
      ["Windows 11 Pro OEM жаңа ноутбукпен келді", 0, "OEM — сол құрылғыда заңды."],
      ["OEM Windows ескі ПК-дан жаңасына көшірілген", 1, "OEM көшірілмейді — жаңа лицензия керек."],
      ["«Photoshop crack» файлы табылды", 2, "Бұзылған бағдарлама — жою."],
      ["1С: concurrent 3, шыңы 4", 1, "Лицензия қосу немесе жүктемені бөлу."],
      ["Git (GPL-2.0) әзірлеушілерде", 0, "Қолдануға шектеусіз."],
      ["AutoCAD LT: 2 лицензия, біреуі 140 күн бос", 3, "Ұзартпау немесе басқаға беру."]
    ]
  },
  soc: {
    title: "SOC кезекшісі", topic: "anomaly",
    about: "Трафик оқиғасын жіктеңіз: қалыпты ма, әлде шабуыл ма?",
    cats: ["Қалыпты", "Сканерлеу", "DDoS", "Деректерді шығару", "Beaconing"],
    cards: [
      ["pc-lab-07: 10 минутта 900 түрлі порт, 200 хост", 1, "Көп порт/хост — сканерлеу."],
      ["srv-backup-01: әр түні 01:00-де 900 МБ кіріс", 0, "Жоспарлы backup — профильде бар."],
      ["srv-web-01: 14:00-де қосылымдар 40 есе өсті, кіріс 30 есе", 2, "Кіріс қосылымдар жарылысы — DDoS."],
      ["srv-file-01: 03:00-де сыртқы IP-ге 2,8 ГБ", 3, "Түнде сыртқа көп дерек — жылыстау."],
      ["pc-acc-02: түні бойы әр 5 минутта 1 қосылым, 20 КБ, бір сыртқы IP", 4, "Тұрақты аралық, аз көлем — C2 beaconing."],
      ["pc-hr-01: түсте 120 МБ жүктеу (кіріс)", 0, "Бір реттік файл жүктеу — зиянсыз."],
      ["pc-lab-03: 250 хостқа тек 445 порт", 1, "Горизонталды сканерлеу (құрт)."],
      ["srv-db-01: күндіз 15 МБ шығыс (ішкі желіге)", 0, "Профиль шегінде."],
      ["nb-director: әр 60 сек сайын бір доменге DNS сұрау, түнде де", 4, "DNS beaconing."],
      ["srv-web-01: 50 000 SYN, бірақ handshake аяқталмайды", 2, "SYN flood — DDoS түрі."],
      ["pc-acc-01: түнгі 02:00-де Dropbox-қа 1,5 ГБ", 3, "Әдеттен тыс уақыт + сыртқа көп — тексеру."],
      ["pc-lab-05: сабақ уақытында 40 қосылым, 3 МБ", 0, "Қалыпты."],
      ["10.10.2.45: бір серверге 1–1024 порттар DENY", 1, "Вертикалды сканерлеу."],
      ["prn-office-01: түнде 0 трафик", 0, "Принтер түнде тыныш — қалыпты."]
    ]
  },
  sre: {
    title: "SRE шешімі", topic: "sla",
    about: "Жағдай бойынша ескерту деңгейін таңдаңыз.",
    cats: ["Бәрі қалыпты", "TICKET — жұмыс уақытында", "PAGE — дереу"],
    cards: [
      ["Burn rate (1 сағ) = 20", 2, "≥ 14,4 — PAGE."],
      ["Burn rate (6 сағ) = 7, (1 сағ) = 3", 1, "6 сағаттық ≥ 6 — TICKET."],
      ["Burn rate (1 сағ) = 0,8", 0, "Бюджет қалыпты жұмсалып жатыр."],
      ["SLO 99,9%, 30 күнде 20 мин тоқтау", 0, "Рұқсат 43 мин — норма."],
      ["Портал толық тоқтады, 503 — 100%", 2, "Дереу."],
      ["404 қателері 3% (бот іздеп жүр)", 0, "4xx SLI-ге кірмейді."],
      ["p95 бір апта бойы 280 → 420 мс өсті (SLO 300)", 1, "Баяу деградация — TICKET."],
      ["Бюджеттің 95%-ы жұмсалды, айдың 10-ы", 1, "Жаңа релиздерді тоқтатып, тұрақтылыққа көшу."],
      ["5xx 1 сағатта 2%, SLO 99,9%", 2, "Burn rate = 20 — PAGE."],
      ["Health check OK, бірақ «бағалар» беті 500 қайтарады", 2, "Нақты пайдаланушы жолы құлады."],
      ["SLA 99%, нақты 99,4%, SLO 99,5%", 1, "SLO бұзылды, SLA сақталды — түзету жоспары."],
      ["Түнгі 03:00, 5 минут 30% қате, қазір 0%", 1, "Өтіп кетті, бірақ себебін талдау керек."],
      ["Сертификат 3 күнде бітеді", 1, "Жоспарлы жұмыс — TICKET."],
      ["ДҚ диск 99% толды, жазу баяулады", 2, "Жақында толық тоқтайды — PAGE."]
    ]
  }
};

window.mountSorter = function (root, deckId, onEnd) {
  const deck = window.DECKS[deckId];
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  let cards, i, score, streak, right, wrong, timer, left, busy;
  const DURATION = 75;

  function shuffle(a) { a = a.slice(); for (let k = a.length - 1; k > 0; k--) { const j = Math.floor(Math.random() * (k + 1)); [a[k], a[j]] = [a[j], a[k]]; } return a; }

  function intro() {
    root.innerHTML = '<div class="sorter"><div class="sorter-head"><b>' + esc(deck.title) + '</b><span>' + esc(deck.about) +
      '</span></div><div class="sorter-intro"><p>' + DURATION + ' секунд. Дұрыс жауап <b>+10</b>, қатарынан 3 дұрыс — <b>+5 бонус</b>, қате <b>−5</b>.<br>Пернетақта: 1–' + deck.cats.length +
      ' сандары.</p><button class="btn" data-start>Бастау</button></div></div>';
    root.querySelector("[data-start]").onclick = start;
  }

  function start() {
    cards = shuffle(deck.cards); i = 0; score = 0; streak = 0; right = 0; wrong = 0; left = DURATION; busy = false;
    root.innerHTML = '<div class="sorter"><div class="sorter-head"><b>' + esc(deck.title) + '</b><span class="hud"><span data-time></span><span data-score></span><span data-streak></span></span></div>' +
      '<div class="card-stage"><div class="gcard" data-card></div><div class="gfb" data-fb></div></div>' +
      '<div class="cats">' + deck.cats.map((c, k) => '<button class="cat" data-k="' + k + '"><kbd>' + (k + 1) + '</kbd>' + esc(c) + '</button>').join("") + '</div></div>';
    root.querySelectorAll(".cat").forEach(b => b.onclick = () => answer(+b.dataset.k));
    document.addEventListener("keydown", onKey);
    show(); hud();
    timer = setInterval(() => { left--; hud(); if (left <= 0) end(); }, 1000);
  }

  function onKey(e) { if (/INPUT|TEXTAREA|SELECT/.test(e.target.tagName)) return; const k = parseInt(e.key, 10); if (k >= 1 && k <= deck.cats.length && root.isConnected) answer(k - 1); }
  function hud() {
    root.querySelector("[data-time]").textContent = "⏱ " + left + "с";
    root.querySelector("[data-score]").textContent = "ұпай " + score;
    root.querySelector("[data-streak]").textContent = streak >= 3 ? "🔥 ×" + streak : "қатар " + streak;
  }
  function show() {
    if (i >= cards.length) { cards = cards.concat(shuffle(deck.cards)); }
    const c = root.querySelector("[data-card]");
    c.className = "gcard in"; c.textContent = cards[i][0];
  }
  function answer(k) {
    if (busy || left <= 0) return;
    busy = true;
    const card = cards[i], ok = k === card[1];
    const fb = root.querySelector("[data-fb]");
    if (ok) { streak++; right++; score += 10 + (streak >= 3 ? 5 : 0); fb.className = "gfb ok"; fb.textContent = "✔ " + card[2]; }
    else { streak = 0; wrong++; score = Math.max(0, score - 5); fb.className = "gfb bad"; fb.textContent = "✘ Дұрысы: " + deck.cats[card[1]] + ". " + card[2]; }
    root.querySelector("[data-card]").className = "gcard " + (ok ? "ok" : "bad");
    hud();
    setTimeout(() => { i++; busy = false; if (left > 0) show(); }, ok ? 450 : 1400);
  }
  function end() {
    clearInterval(timer); document.removeEventListener("keydown", onKey);
    const acc = right + wrong ? Math.round(100 * right / (right + wrong)) : 0;
    root.innerHTML = '<div class="sorter"><div class="sorter-head"><b>' + esc(deck.title) + '</b><span>Ойын аяқталды</span></div><div class="sorter-intro">' +
      '<div class="big">' + score + '</div><p>дұрыс: ' + right + ' · қате: ' + wrong + ' · дәлдік: ' + acc + '%</p><div data-save class="muted"></div>' +
      '<button class="btn" data-start>Қайта ойнау</button></div></div>';
    root.querySelector("[data-start]").onclick = start;
    onEnd && onEnd({ score: score, accuracy: acc, detail: right + "/" + (right + wrong) }, root.querySelector("[data-save]"));
  }
  intro();
};
