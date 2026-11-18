/**
 * Оқу практикасы сайтының серверлік бөлігі (Google Apps Script), 2-нұсқа.
 *
 *  - студенттерді тіркеу және кіру (қолтаңбалы токен, 14 күн);
 *  - тестті СЕРВЕРДЕ тексеру (дұрыс жауаптар тек осы скриптте сақталады);
 *  - жұмыстарды қабылдау (файл → Google Drive), ойын ұпайлары, көшбасшылар кестесі;
 *  - оқытушы панелі: студенттер, әрекеттер, бағалау, құпиясөзді қалпына келтіру.
 *
 * Жаңартқаннан кейін: Deploy → Manage deployments → ✏️ → New version → Deploy (URL өзгермейді).
 */

// ↓↓↓ ОҚЫТУШЫ ҚҰПИЯСӨЗІ (кемінде 8 таңба) ↓↓↓
const ADMIN_PASSWORD = 'ӨЗГЕРТІҢІЗ-2026';

// Google кестесінің ID-і (кесте мекенжайындағы /d/ мен /edit арасындағы бөлік).
const SHEET_ID = '1O9CPuR3ijWFzybUpu_2nvapWnH_PXduXCsPbYhT37eo';

// Тест баптаулары
const QUIZ_SIZE = 10;        // бір әрекеттегі сұрақтар саны
const QUIZ_ATTEMPTS = 3;     // бір тақырыпқа ең көп әрекет
const TOKEN_DAYS = 14;

// Дұрыс жауаптар: { тақырып: { сұрақ_id: [дұрыс_нұсқа_индексі, "түсіндірме"] } }
// Бұл блокты жеке репозиторийдегі құрал толтырады — ашық репозиторийде ол бос.
// ANSWERS_START
const QUIZ_KEYS = {};
// ANSWERS_END

const SH = {
  students: ['Студенттер', ['Логин', 'Аты-жөні', 'Тобы', 'Тұз', 'Хэш', 'Тіркелген', 'Соңғы кіру', 'Белсенді']],
  subs: ['Тапсырылған жұмыстар', ['id', 'Уақыты', 'Аты-жөні', 'Тобы', 'Тақырып', 'Нұсқа', 'Сілтеме', 'Файл', 'Студент түсініктемесі', 'Күйі', 'Баға (ұпай)', 'Оқытушы түсініктемесі', 'Тексерілген уақыты', 'Логин']],
  tests: ['Тест нәтижелері', ['Уақыты', 'Аты-жөні', 'Тобы', 'Тақырып', 'Ұпай', 'Барлығы', 'Пайыз', 'Жауаптар', 'Логин', 'Әрекет №', 'Уақыт (сек)']],
  games: ['Ойындар', ['Уақыты', 'Логин', 'Аты-жөні', 'Тобы', 'Ойын', 'Ұпай', 'Дәлдік %', 'Мәлімет']]
};
const FOLDER_NAME = 'Оқу практикасы — студенттер жұмыстары';
const MAX_FILE_MB = 10;

function ss_() {
  return SHEET_ID ? SpreadsheetApp.openById(SHEET_ID) : SpreadsheetApp.getActive();
}

function sheet_(key) {
  const def = SH[key];
  const ss = ss_();
  let sh = ss.getSheetByName(def[0]);
  if (!sh) sh = ss.insertSheet(def[0]);
  const head = def[1];
  const cur = sh.getLastRow() ? sh.getRange(1, 1, 1, Math.max(sh.getLastColumn(), 1)).getValues()[0] : [];
  if (cur.length < head.length || cur[0] !== head[0]) {
    sh.getRange(1, 1, 1, head.length).setValues([head]).setFontWeight('bold');
    sh.setFrozenRows(1);
  }
  return sh;
}

function setup() {
  if (!ADMIN_PASSWORD || ADMIN_PASSWORD.length < 8 || ADMIN_PASSWORD === 'ӨЗГЕРТІҢІЗ-2026') {
    throw new Error('Алдымен ADMIN_PASSWORD мәнін өз құпиясөзіңізге ауыстырыңыз (кемінде 8 таңба).');
  }
  Object.keys(SH).forEach(sheet_);
  const props = PropertiesService.getScriptProperties();
  props.setProperty('ADMIN_HASH', hash_(ADMIN_PASSWORD));
  if (!props.getProperty('TOKEN_SECRET')) props.setProperty('TOKEN_SECRET', Utilities.getUuid() + Utilities.getUuid());
  if (!props.getProperty('FOLDER_ID')) props.setProperty('FOLDER_ID', DriveApp.createFolder(FOLDER_NAME).getId());
  Logger.log('Дайын. Deploy → Manage deployments → ✏️ → New version.');
}

/* ---------- көмекші ---------- */
function hex_(bytes) {
  return bytes.map(function (b) { return ('0' + (b & 0xff).toString(16)).slice(-2); }).join('');
}
function hash_(s) {
  return hex_(Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, s, Utilities.Charset.UTF_8));
}
function pwHash_(pw, salt) {
  let h = salt + '|' + pw;
  for (let i = 0; i < 300; i++) h = hash_(h + salt);
  return h;
}
function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}
function clean_(v, max) {
  return String(v == null ? '' : v).replace(/[\u0000-\u001f]/g, ' ').trim().slice(0, max || 200);
}
function isAdmin_(pw) {
  const h = PropertiesService.getScriptProperties().getProperty('ADMIN_HASH');
  return !!h && !!pw && hash_(String(pw)) === h;
}
function newId_() {
  const abc = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  let s = '';
  for (let i = 0; i < 6; i++) s += abc.charAt(Math.floor(Math.random() * abc.length));
  return s;
}
function rows_(key) {
  return sheet_(key).getDataRange().getValues().slice(1);
}

/* ---------- токен ---------- */
function sign_(payload) {
  const secret = PropertiesService.getScriptProperties().getProperty('TOKEN_SECRET');
  return hex_(Utilities.computeHmacSha256Signature(payload, secret)).slice(0, 40);
}
function makeToken_(login) {
  const p = login + '.' + (Date.now() + TOKEN_DAYS * 864e5);
  return Utilities.base64EncodeWebSafe(p) + '.' + sign_(p);
}
function student_(token) {
  if (!token) throw new Error('AUTH');
  const parts = String(token).split('.');
  if (parts.length !== 2) throw new Error('AUTH');
  const p = Utilities.newBlob(Utilities.base64DecodeWebSafe(parts[0])).getDataAsString();
  if (sign_(p) !== parts[1]) throw new Error('AUTH');
  const dot = p.lastIndexOf('.');
  const login = p.slice(0, dot), exp = Number(p.slice(dot + 1));
  if (Date.now() > exp) throw new Error('AUTH');
  const r = rows_('students').filter(function (x) { return x[0] === login; })[0];
  if (!r || r[7] === 'жоқ') throw new Error('AUTH');
  return { login: r[0], name: r[1], group: r[2] };
}

/* ---------- кіру нүктелері ---------- */
function doGet() {
  return json_({ ok: true, service: 'oqu-praktikasy', version: 2 });
}

function doPost(e) {
  let req;
  try { req = JSON.parse(e.postData.contents); } catch (err) { return json_({ ok: false, error: 'Сұрау форматы қате' }); }
  try {
    const A = {
      register: register_, login: login_, me: me_,
      quiz: quiz_, game: game_, submit: submit_, leaderboard: leaderboard_, check: check_,
      adminLogin: function (r) { return { ok: isAdmin_(r.password) }; },
      list: list_, grade: grade_, resetPassword: resetPassword_, setActive: setActive_
    };
    if (!A[req.action]) return json_({ ok: false, error: 'Белгісіз әрекет' });
    return json_(A[req.action](req));
  } catch (err) {
    const m = String(err.message || err);
    return json_({ ok: false, error: m === 'AUTH' ? 'Қайта кіріңіз' : m, auth: m === 'AUTH' });
  }
}

/* ---------- студент ---------- */
function register_(req) {
  const login = clean_(req.login, 30).toLowerCase();
  const name = clean_(req.name, 120), group = clean_(req.group, 40), pw = String(req.password || '');
  if (!/^[a-z0-9_.-]{3,30}$/.test(login)) return { ok: false, error: 'Логин: 3–30 латын әрпі, сан немесе _ . -' };
  if (name.split(/\s+/).length < 2) return { ok: false, error: 'Аты-жөніңізді толық жазыңыз (тегі және аты)' };
  if (!group) return { ok: false, error: 'Топты таңдаңыз' };
  if (pw.length < 6) return { ok: false, error: 'Құпиясөз кемінде 6 таңба' };
  const lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    if (rows_('students').some(function (x) { return x[0] === login; })) return { ok: false, error: 'Бұл логин бос емес' };
    const salt = Utilities.getUuid();
    sheet_('students').appendRow([login, name, group, salt, pwHash_(pw, salt), new Date(), new Date(), 'иә']);
  } finally {
    lock.releaseLock();
  }
  return { ok: true, token: makeToken_(login), user: { login: login, name: name, group: group } };
}

function login_(req) {
  const login = clean_(req.login, 30).toLowerCase();
  const sh = sheet_('students');
  const v = sh.getDataRange().getValues();
  for (let i = 1; i < v.length; i++) {
    if (v[i][0] === login) {
      if (v[i][7] === 'жоқ') return { ok: false, error: 'Аккаунт бұғатталған — оқытушыға хабарласыңыз' };
      if (pwHash_(String(req.password || ''), v[i][3]) !== v[i][4]) break;
      sh.getRange(i + 1, 7).setValue(new Date());
      return { ok: true, token: makeToken_(login), user: { login: login, name: v[i][1], group: v[i][2] } };
    }
  }
  Utilities.sleep(700);
  return { ok: false, error: 'Логин немесе құпиясөз қате' };
}

function me_(req) {
  const u = student_(req.token);
  const subs = rows_('subs').filter(function (r) { return r[13] === u.login; }).map(function (r) {
    return { id: r[0], time: r[1], topic: r[4], variant: r[5], status: r[9], grade: r[10], comment: r[11] };
  });
  const tests = rows_('tests').filter(function (r) { return r[8] === u.login; }).map(function (r) {
    return { time: r[0], topic: r[3], score: r[4], total: r[5], percent: r[6], attempt: r[9] };
  });
  const games = rows_('games').filter(function (r) { return r[1] === u.login; }).map(function (r) {
    return { time: r[0], game: r[4], score: r[5], accuracy: r[6] };
  });
  return { ok: true, user: u, submissions: subs, tests: tests, games: games, attemptsLimit: QUIZ_ATTEMPTS };
}

function quiz_(req) {
  const u = student_(req.token);
  const topic = clean_(req.topic, 30);
  const keys = QUIZ_KEYS[topic];
  if (!keys) return { ok: false, error: 'Тест табылмады' };
  const done = rows_('tests').filter(function (r) { return r[8] === u.login && r[3] === topic; }).length;
  if (done >= QUIZ_ATTEMPTS) return { ok: false, error: 'Әрекеттер саны бітті (' + QUIZ_ATTEMPTS + ')' };
  const ans = req.answers || {};
  const ids = Object.keys(ans).filter(function (id) { return keys[id]; }).slice(0, QUIZ_SIZE);
  if (ids.length < Math.min(QUIZ_SIZE, Object.keys(keys).length)) return { ok: false, error: 'Барлық сұраққа жауап беріңіз' };
  let score = 0;
  const result = {};
  ids.forEach(function (id) {
    const ok = Number(ans[id]) === keys[id][0];
    if (ok) score++;
    result[id] = { correct: keys[id][0], ok: ok, e: keys[id][1] };
  });
  const pct = Math.round(100 * score / ids.length);
  sheet_('tests').appendRow([new Date(), u.name, u.group, topic, score, ids.length, pct,
    ids.map(function (id) { return id + ':' + ans[id] + (result[id].ok ? '✓' : '✗'); }).join(' '),
    u.login, done + 1, Math.max(0, Math.min(36000, Number(req.seconds) || 0))]);
  return { ok: true, score: score, total: ids.length, percent: pct, result: result, attempt: done + 1, left: QUIZ_ATTEMPTS - done - 1 };
}

function game_(req) {
  const u = student_(req.token);
  const game = clean_(req.game, 40);
  if (!/^[a-z0-9:_-]+$/.test(game)) return { ok: false, error: 'Ойын атауы қате' };
  const score = Math.max(0, Math.min(100000, Math.round(Number(req.score) || 0)));
  const acc = Math.max(0, Math.min(100, Math.round(Number(req.accuracy) || 0)));
  sheet_('games').appendRow([new Date(), u.login, u.name, u.group, game, score, acc, clean_(req.detail, 300)]);
  return { ok: true };
}

function leaderboard_(req) {
  const game = clean_(req.game, 40);
  const best = {};
  rows_('games').forEach(function (r) {
    if (game && r[4] !== game) return;
    const key = game ? r[1] : r[1];
    if (!game) {   // жалпы рейтинг: әр ойындағы ең жақсы ұпайлардың қосындысы
      best[key] = best[key] || { name: short_(r[2]), group: r[3], per: {}, score: 0 };
      best[key].per[r[4]] = Math.max(best[key].per[r[4]] || 0, r[5]);
      return;
    }
    if (!best[key] || r[5] > best[key].score) best[key] = { name: short_(r[2]), group: r[3], score: r[5] };
  });
  let list = Object.keys(best).map(function (k) { return best[k]; });
  if (!game) list.forEach(function (x) { x.score = Object.keys(x.per).reduce(function (a, g) { return a + x.per[g]; }, 0); delete x.per; });
  list = list.sort(function (a, b) { return b.score - a.score; }).slice(0, 15);
  return { ok: true, list: list };
}

function short_(name) {
  const parts = String(name).split(/\s+/);
  return parts[0] + (parts[1] ? ' ' + parts[1].charAt(0) + '.' : '');
}

function submit_(req) {
  const u = student_(req.token);
  const topic = clean_(req.topic, 120);
  const link = clean_(req.link, 500);
  if (link && !/^https?:\/\//i.test(link)) return { ok: false, error: 'Сілтеме http:// немесе https:// деп басталуы керек' };
  let fileUrl = '';
  if (req.file && req.file.data) {
    const bytes = Utilities.base64Decode(req.file.data);
    if (bytes.length > MAX_FILE_MB * 1024 * 1024) return { ok: false, error: 'Файл ' + MAX_FILE_MB + ' МБ-тан аспауы керек' };
    const ext = (clean_(req.file.name, 120).match(/\.(pdf|docx|doc|zip|png|jpg|jpeg|pptx|txt|md|py)$/i) || [])[0];
    if (!ext) return { ok: false, error: 'Рұқсат етілген түрлер: pdf, docx, zip, png, jpg, pptx, txt, md, py' };
    const folder = DriveApp.getFolderById(PropertiesService.getScriptProperties().getProperty('FOLDER_ID'));
    fileUrl = folder.createFile(Utilities.newBlob(bytes, req.file.mime || 'application/octet-stream',
      u.group + '_' + u.name + '_' + topic + ext)).getUrl();
  }
  if (!link && !fileUrl) return { ok: false, error: 'Файл жүктеңіз немесе сілтеме қалдырыңыз' };
  const id = newId_();
  sheet_('subs').appendRow([id, new Date(), u.name, u.group, topic, clean_(req.variant, 10), link, fileUrl,
    clean_(req.comment, 1000), 'Тексерілмеген', '', '', '', u.login]);
  return { ok: true, id: id };
}

function check_(req) {
  const id = clean_(req.id, 10).toUpperCase();
  const r = rows_('subs').filter(function (x) { return x[0] === id; })[0];
  if (!r) return { ok: true, found: false };
  return { ok: true, found: true, name: r[2], topic: r[4], status: r[9], grade: r[10], comment: r[11] };
}

/* ---------- оқытушы ---------- */
function list_(req) {
  if (!isAdmin_(req.password)) return { ok: false, error: 'Құпиясөз қате' };
  return {
    ok: true,
    students: rows_('students').map(function (r) { return { login: r[0], name: r[1], group: r[2], created: r[5], last: r[6], active: r[7] !== 'жоқ' }; }),
    submissions: rows_('subs').map(function (r) {
      return { id: r[0], time: r[1], name: r[2], group: r[3], topic: r[4], variant: r[5], link: r[6], file: r[7],
        comment: r[8], status: r[9], grade: r[10], teacherComment: r[11], checkedAt: r[12], login: r[13] };
    }),
    tests: rows_('tests').map(function (r) {
      return { time: r[0], name: r[1], group: r[2], topic: r[3], score: r[4], total: r[5], percent: r[6], answers: r[7], login: r[8], attempt: r[9], seconds: r[10] };
    }),
    games: rows_('games').map(function (r) { return { time: r[0], login: r[1], name: r[2], group: r[3], game: r[4], score: r[5], accuracy: r[6], detail: r[7] }; })
  };
}

function grade_(req) {
  if (!isAdmin_(req.password)) return { ok: false, error: 'Құпиясөз қате' };
  const sh = sheet_('subs');
  const ids = sh.getRange(2, 1, Math.max(sh.getLastRow() - 1, 1), 1).getValues();
  for (let i = 0; i < ids.length; i++) {
    if (ids[i][0] === req.id) {
      sh.getRange(i + 2, 10, 1, 4).setValues([[clean_(req.status, 40) || 'Тексерілді',
        req.grade === '' || req.grade == null ? '' : Number(req.grade), clean_(req.teacherComment, 1000), new Date()]]);
      return { ok: true };
    }
  }
  return { ok: false, error: 'Жұмыс табылмады' };
}

function resetPassword_(req) {
  if (!isAdmin_(req.password)) return { ok: false, error: 'Құпиясөз қате' };
  const sh = sheet_('students');
  const v = sh.getDataRange().getValues();
  for (let i = 1; i < v.length; i++) {
    if (v[i][0] === req.login) {
      const pw = String(Math.floor(100000 + Math.random() * 900000));
      const salt = Utilities.getUuid();
      sh.getRange(i + 1, 4, 1, 2).setValues([[salt, pwHash_(pw, salt)]]);
      return { ok: true, newPassword: pw };
    }
  }
  return { ok: false, error: 'Студент табылмады' };
}

function setActive_(req) {
  if (!isAdmin_(req.password)) return { ok: false, error: 'Құпиясөз қате' };
  const sh = sheet_('students');
  const v = sh.getDataRange().getValues();
  for (let i = 1; i < v.length; i++) {
    if (v[i][0] === req.login) {
      sh.getRange(i + 1, 8).setValue(req.active ? 'иә' : 'жоқ');
      return { ok: true };
    }
  }
  return { ok: false, error: 'Студент табылмады' };
}
