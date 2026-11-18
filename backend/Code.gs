/**
 * Оқу практикасы сайтының серверлік бөлігі (Google Apps Script).
 * Деректер осы Google кестесінде сақталады, файлдар — Google Drive қалтасында.
 *
 * Орнату (бір рет): backend/ОРНАТУ.md файлын қараңыз.
 *   1) ADMIN_PASSWORD мәнін өз құпиясөзіңізге ауыстырыңыз.
 *   2) setup функциясын іске қосыңыз (Run ▶ setup).
 *   3) Deploy → New deployment → Web app → Execute as: Me, Who has access: Anyone.
 */

// ↓↓↓ ӨЗ ҚҰПИЯСӨЗІҢІЗДІ ЖАЗЫҢЫЗ (кемінде 8 таңба) ↓↓↓
const ADMIN_PASSWORD = 'ӨЗГЕРТІҢІЗ-2026';

const SUBMISSIONS = 'Тапсырылған жұмыстар';
const TESTS = 'Тест нәтижелері';
const FOLDER_NAME = 'Оқу практикасы — студенттер жұмыстары';
const MAX_FILE_MB = 10;
const SUB_HEADERS = ['id', 'Уақыты', 'Аты-жөні', 'Тобы', 'Тақырып', 'Нұсқа', 'Сілтеме', 'Файл', 'Студент түсініктемесі', 'Күйі', 'Баға (ұпай)', 'Оқытушы түсініктемесі', 'Тексерілген уақыты'];
const TEST_HEADERS = ['Уақыты', 'Аты-жөні', 'Тобы', 'Тақырып', 'Ұпай', 'Барлығы', 'Пайыз', 'Жауаптар'];

function setup() {
  if (!ADMIN_PASSWORD || ADMIN_PASSWORD.length < 8 || ADMIN_PASSWORD === 'ӨЗГЕРТІҢІЗ-2026') {
    throw new Error('Алдымен Code.gs файлының басындағы ADMIN_PASSWORD мәнін өз құпиясөзіңізге ауыстырыңыз (кемінде 8 таңба).');
  }
  const ss = SpreadsheetApp.getActive();
  ensureSheet_(ss, SUBMISSIONS, SUB_HEADERS);
  ensureSheet_(ss, TESTS, TEST_HEADERS);
  const props = PropertiesService.getScriptProperties();
  props.setProperty('ADMIN_HASH', hash_(ADMIN_PASSWORD));
  if (!props.getProperty('FOLDER_ID')) {
    const folder = DriveApp.createFolder(FOLDER_NAME);
    props.setProperty('FOLDER_ID', folder.getId());
  }
  Logger.log('Дайын! Енді Deploy → New deployment → Web app жасаңыз.');
}

function ensureSheet_(ss, name, headers) {
  let sh = ss.getSheetByName(name);
  if (!sh) sh = ss.insertSheet(name);
  if (sh.getLastRow() === 0) {
    sh.appendRow(headers);
    sh.getRange(1, 1, 1, headers.length).setFontWeight('bold');
    sh.setFrozenRows(1);
  }
  return sh;
}

function hash_(s) {
  const bytes = Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, s, Utilities.Charset.UTF_8);
  return bytes.map(function (b) { return ('0' + (b & 0xff).toString(16)).slice(-2); }).join('');
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

function doGet() {
  return json_({ ok: true, service: 'oqu-praktikasy', time: new Date().toISOString() });
}

function doPost(e) {
  let req;
  try {
    req = JSON.parse(e.postData.contents);
  } catch (err) {
    return json_({ ok: false, error: 'Сұрау форматы қате' });
  }
  try {
    switch (req.action) {
      case 'submit': return json_(submit_(req));
      case 'test': return json_(saveTest_(req));
      case 'check': return json_(check_(req));
      case 'login': return json_({ ok: isAdmin_(req.password) });
      case 'list': return json_(list_(req));
      case 'grade': return json_(grade_(req));
      default: return json_({ ok: false, error: 'Белгісіз әрекет' });
    }
  } catch (err) {
    return json_({ ok: false, error: String(err.message || err) });
  }
}

function submit_(req) {
  const name = clean_(req.name, 120), group = clean_(req.group, 40), topic = clean_(req.topic, 120);
  if (!name || !group || !topic) return { ok: false, error: 'Аты-жөні, тобы және тақырып міндетті' };
  const link = clean_(req.link, 500);
  if (link && !/^https?:\/\//i.test(link)) return { ok: false, error: 'Сілтеме http:// немесе https:// деп басталуы керек' };
  let fileUrl = '';
  if (req.file && req.file.data) {
    const bytes = Utilities.base64Decode(req.file.data);
    if (bytes.length > MAX_FILE_MB * 1024 * 1024) return { ok: false, error: 'Файл ' + MAX_FILE_MB + ' МБ-тан аспауы керек' };
    const ext = (clean_(req.file.name, 120).match(/\.(pdf|docx|doc|zip|png|jpg|jpeg|pptx|txt|md|py)$/i) || [])[0];
    if (!ext) return { ok: false, error: 'Рұқсат етілген файл түрлері: pdf, docx, zip, png, jpg, pptx, txt, md, py' };
    const folder = DriveApp.getFolderById(PropertiesService.getScriptProperties().getProperty('FOLDER_ID'));
    const blob = Utilities.newBlob(bytes, req.file.mime || 'application/octet-stream', group + '_' + name + '_' + topic + ext);
    fileUrl = folder.createFile(blob).getUrl();
  }
  if (!link && !fileUrl) return { ok: false, error: 'Файл жүктеңіз немесе сілтеме қалдырыңыз' };
  const id = newId_();
  const lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    SpreadsheetApp.getActive().getSheetByName(SUBMISSIONS).appendRow([
      id, new Date(), name, group, topic, clean_(req.variant, 10), link, fileUrl,
      clean_(req.comment, 1000), 'Тексерілмеген', '', '', ''
    ]);
  } finally {
    lock.releaseLock();
  }
  return { ok: true, id: id };
}

function saveTest_(req) {
  const name = clean_(req.name, 120), group = clean_(req.group, 40), topic = clean_(req.topic, 120);
  if (!name || !group) return { ok: false, error: 'Аты-жөні мен тобы міндетті' };
  const score = Number(req.score) || 0, total = Number(req.total) || 0;
  SpreadsheetApp.getActive().getSheetByName(TESTS).appendRow([
    new Date(), name, group, topic, score, total, total ? Math.round(100 * score / total) : 0, clean_(req.answers, 500)
  ]);
  return { ok: true };
}

function rows_(sheetName) {
  const sh = SpreadsheetApp.getActive().getSheetByName(sheetName);
  const values = sh.getDataRange().getValues();
  return values.slice(1);
}

function check_(req) {
  const id = clean_(req.id, 10).toUpperCase();
  const r = rows_(SUBMISSIONS).filter(function (x) { return x[0] === id; })[0];
  if (!r) return { ok: true, found: false };
  return { ok: true, found: true, name: r[2], topic: r[4], status: r[9], grade: r[10], comment: r[11] };
}

function list_(req) {
  if (!isAdmin_(req.password)) return { ok: false, error: 'Құпиясөз қате' };
  const subs = rows_(SUBMISSIONS).map(function (r) {
    return { id: r[0], time: r[1], name: r[2], group: r[3], topic: r[4], variant: r[5], link: r[6], file: r[7],
             comment: r[8], status: r[9], grade: r[10], teacherComment: r[11], checkedAt: r[12] };
  });
  const tests = rows_(TESTS).map(function (r) {
    return { time: r[0], name: r[1], group: r[2], topic: r[3], score: r[4], total: r[5], percent: r[6] };
  });
  return { ok: true, submissions: subs, tests: tests };
}

function grade_(req) {
  if (!isAdmin_(req.password)) return { ok: false, error: 'Құпиясөз қате' };
  const sh = SpreadsheetApp.getActive().getSheetByName(SUBMISSIONS);
  const ids = sh.getRange(2, 1, Math.max(sh.getLastRow() - 1, 1), 1).getValues();
  for (let i = 0; i < ids.length; i++) {
    if (ids[i][0] === req.id) {
      const row = i + 2;
      sh.getRange(row, 10, 1, 4).setValues([[
        clean_(req.status, 40) || 'Тексерілді',
        req.grade === '' || req.grade == null ? '' : Number(req.grade),
        clean_(req.teacherComment, 1000),
        new Date()
      ]]);
      return { ok: true };
    }
  }
  return { ok: false, error: 'Жұмыс табылмады' };
}
