// Tintå: vastaanottaa reseptikuvat ja keittiön yhteiset muutokset.
// يستلم صور الوصفات الجديدة، وتعديلات الشيفات الي يشوفها الكل.
//
// ⚠️ هذا قالب بدون أسرار. النسخة الحقيقية (بيها الرمز السري) يعطيها Claude لصاحب المطعم بس.
// The real copy with the secret values is given privately to the owner only. Never commit it.
var PIN = '__PIN__';        // رمز المطبخ: الشيفات يكتبوه مرة وحدة بالتطبيق
var ADMIN = '__ADMIN__';    // مفتاح صاحب المطعم بس: لقراءة الصور ومسح الملاحظات
var FOLDER = 'Tintå uudet reseptit';
var DATA = 'tinta-muutokset.json';
var MAX_IMG = 4 * 1024 * 1024; // max ~4 MB per photo

function folder_(name, parent) {
  var it = parent ? parent.getFoldersByName(name) : DriveApp.getFoldersByName(name);
  return it.hasNext() ? it.next() : (parent ? parent.createFolder(name) : DriveApp.createFolder(name));
}
function out_(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}
function same_(a, b) {
  a = String(a || ''); b = String(b || '');
  if (!a || !b || a.length !== b.length) return false;
  var r = 0; for (var i = 0; i < a.length; i++) r |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return r === 0;
}
function dataFile_() {
  var f = folder_('Data', folder_(FOLDER)), it = f.getFilesByName(DATA);
  return it.hasNext() ? it.next() : f.createFile(DATA, '{"notes":{},"edits":{}}', 'application/json');
}
function readData_() {
  var d = {};
  try { d = JSON.parse(dataFile_().getBlob().getDataAsString() || '{}'); } catch (e) {}
  d.notes = d.notes || {}; d.edits = d.edits || {};
  return d;
}
function clean_(s, n) { return String(s || '').replace(/[<>]/g, '').slice(0, n); }

function doPost(e) {
  var d = {};
  try { d = JSON.parse(e.postData.contents); } catch (err) { return out_({ ok: false }); }
  var f = folder_(FOLDER);
  var admin = same_(d.key, ADMIN), chef = admin || same_(d.pin, PIN);

  // Vain omistaja. / بس صاحب المطعم.
  if (d.action === 'done') {
    if (!admin) return out_({ ok: false, err: 'key' });
    DriveApp.getFileById(d.id).moveTo(folder_('Lisätty', f));
    return out_({ ok: true });
  }

  // Keittiö (PIN). / الشيفات بالرمز.
  if (!chef) return out_({ ok: false, err: 'pin' });

  if (d.action === 'note' || d.action === 'edit' || d.action === 'delnote') {
    if (d.action === 'delnote' && !admin) return out_({ ok: false, err: 'key' });
    var lock = LockService.getScriptLock();
    lock.waitLock(15000);
    try {
      var data = readData_(), id = clean_(d.id, 80);
      var by = clean_(d.by, 40), at = new Date().toISOString();
      if (!/^[a-z0-9-]+$/.test(id)) return out_({ ok: false });
      if (d.action === 'delnote') {
        data.notes[id] = (data.notes[id] || []).filter(function (n) { return n.at !== d.at; });
      }
      if (d.action === 'edit') {
        data.edits[id] = data.edits[id] || {};
        Object.keys(d.q || {}).slice(0, 60).forEach(function (ref) {
          if (!/^\d+-\d+$/.test(ref)) return;
          var v = d.q[ref];
          if (v === null) delete data.edits[id][ref];
          else if (isFinite(Number(v)) && Number(v) >= 0 && Number(v) < 100000) data.edits[id][ref] = { q: Number(v), by: by, at: at };
        });
      }
      if ((d.action === 'note' || d.action === 'edit') && d.text) {
        (data.notes[id] = data.notes[id] || []).push({ t: clean_(d.text, 1000), by: by, at: at });
      }
      dataFile_().setContent(JSON.stringify(data));
      return out_({ ok: true, notes: data.notes, edits: data.edits });
    } finally {
      lock.releaseLock();
    }
  }

  // Uusi resepti kuvasta (kuvat pysyvät yksityisinä). / وصفة جديدة (الصور تبقى سرية).
  var stamp = Utilities.formatDate(new Date(), 'Europe/Helsinki', 'yyyy-MM-dd HH.mm.ss');
  var name = clean_(d.name, 80);
  var imgs = (d.images || []).slice(0, 6), n = 0;
  imgs.forEach(function (b64, i) {
    var bytes = Utilities.base64Decode(String(b64));
    if (bytes.length > MAX_IMG) return;
    var file = f.createFile(Utilities.newBlob(bytes, 'image/jpeg', stamp + ' ' + (name || 'resepti') + ' (' + (i + 1) + ').jpg'));
    file.setDescription(JSON.stringify({ group: stamp, name: name, page: i + 1, pages: imgs.length }));
    n++;
  });
  return out_({ ok: true, count: n });
}

function doGet(e) {
  var p = (e && e.parameter) || {};
  // Kaikille: keittiön muutokset. / للكل: تعديلات المطبخ.
  if (p.what === 'changes') {
    var data = readData_();
    return out_({ ok: true, notes: data.notes, edits: data.edits });
  }
  // Vain omistaja. / بس صاحب المطعم.
  if (!same_(p.key, ADMIN)) return out_({ ok: false, err: 'key' });
  if (p.what === 'file') {
    var file = DriveApp.getFileById(p.id);
    if (file.getParents().next().getName() !== FOLDER) return out_({ ok: false });
    return out_({ ok: true, b64: Utilities.base64Encode(file.getBlob().getBytes()) });
  }
  var it = folder_(FOLDER).getFiles(), list = [];
  while (it.hasNext()) {
    var x = it.next();
    if (String(x.getMimeType()).indexOf('image/') !== 0) continue;
    list.push({ id: x.getId(), name: x.getName(), desc: x.getDescription(), time: x.getDateCreated() });
  }
  return out_({ ok: true, files: list });
}

// Aja tämä kerran käsin. / شغّل هاي مرة وحدة.
function setup() {
  folder_('Lisätty', folder_(FOLDER));
  dataFile_();
}
