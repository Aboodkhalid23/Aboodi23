// Tintå: vastaanottaa reseptikuvat ja keittiön yhteiset muutokset.
// يستلم صور الوصفات الجديدة، وتعديلات الشيفات الي يشوفها الكل.
var FOLDER = 'Tintå uudet reseptit';
var DATA = 'tinta-muutokset.json';

function folder_(name, parent) {
  var it = parent ? parent.getFoldersByName(name) : DriveApp.getFoldersByName(name);
  return it.hasNext() ? it.next() : (parent ? parent.createFolder(name) : DriveApp.createFolder(name));
}
function out_(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
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

function doPost(e) {
  var d = JSON.parse(e.postData.contents);
  var f = folder_(FOLDER);

  // Kuva käsitelty. / الصورة انضافت.
  if (d.action === 'done') {
    DriveApp.getFileById(d.id).moveTo(folder_('Lisätty', f));
    return out_({ ok: true });
  }

  // Keittiön yhteiset muistiinpanot ja muutetut määrät. / ملاحظات وتعديلات الشيفات.
  if (d.action === 'note' || d.action === 'edit' || d.action === 'delnote') {
    var lock = LockService.getScriptLock();
    lock.waitLock(15000);
    try {
      var data = readData_(), id = String(d.id || '').slice(0, 80);
      var by = String(d.by || '').slice(0, 40), at = new Date().toISOString();
      if (!id) return out_({ ok: false });
      if (d.action === 'delnote') {
        data.notes[id] = (data.notes[id] || []).filter(function (n) { return n.at !== d.at; });
      }
      if (d.action === 'edit') {
        data.edits[id] = data.edits[id] || {};
        Object.keys(d.q || {}).forEach(function (ref) {
          var v = d.q[ref];
          if (v === null) delete data.edits[id][ref];
          else if (isFinite(Number(v)) && Number(v) >= 0) data.edits[id][ref] = { q: Number(v), by: by, at: at };
        });
      }
      if ((d.action === 'note' || d.action === 'edit') && d.text) {
        (data.notes[id] = data.notes[id] || []).push({ t: String(d.text).slice(0, 1000), by: by, at: at });
      }
      dataFile_().setContent(JSON.stringify(data));
      return out_({ ok: true, notes: data.notes, edits: data.edits });
    } finally {
      lock.releaseLock();
    }
  }

  // Uusi resepti kuvasta. / وصفة جديدة من صورة.
  var stamp = Utilities.formatDate(new Date(), 'Europe/Helsinki', 'yyyy-MM-dd HH.mm.ss');
  var name = String(d.name || '').slice(0, 80);
  var imgs = (d.images || []).slice(0, 6);
  imgs.forEach(function (b64, i) {
    var blob = Utilities.newBlob(Utilities.base64Decode(b64), 'image/jpeg', stamp + ' ' + (name || 'resepti') + ' (' + (i + 1) + ').jpg');
    var file = f.createFile(blob);
    file.setDescription(JSON.stringify({ group: stamp, name: name, page: i + 1, pages: imgs.length }));
    file.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
  });
  return out_({ ok: true, count: imgs.length });
}

function doGet(e) {
  if (e && e.parameter && e.parameter.what === 'changes') {
    var data = readData_();
    return out_({ ok: true, notes: data.notes, edits: data.edits });
  }
  // Odottavat reseptikuvat. / الصور الي تنتظر.
  var it = folder_(FOLDER).getFiles(), list = [];
  while (it.hasNext()) {
    var x = it.next();
    if (String(x.getMimeType()).indexOf('image/') !== 0) continue;
    list.push({ id: x.getId(), name: x.getName(), desc: x.getDescription(), time: x.getDateCreated() });
  }
  return out_({ ok: true, files: list });
}

// Aja tämä kerran käsin, niin Google kysyy luvat. / شغّل هاي مرة وحدة حتى گوگل يطلب الموافقة.
function setup() {
  folder_('Lisätty', folder_(FOLDER));
  dataFile_();
}
