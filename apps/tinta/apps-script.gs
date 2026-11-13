// Tintå: vastaanottaa reseptikuvat sovelluksesta ja tallentaa ne Driveen.
// يستلم صور الوصفات من التطبيق ويحفظها بمجلد بالدرايف.
var FOLDER = 'Tintå uudet reseptit';

function folder_(name, parent) {
  var it = parent ? parent.getFoldersByName(name) : DriveApp.getFoldersByName(name);
  return it.hasNext() ? it.next() : (parent ? parent.createFolder(name) : DriveApp.createFolder(name));
}
function out_(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}

// Sovellus lähettää kuvat tänne. / التطبيق يدز الصور هنا.
function doPost(e) {
  var d = JSON.parse(e.postData.contents);
  var f = folder_(FOLDER);
  if (d.action === 'done') {
    DriveApp.getFileById(d.id).moveTo(folder_('Lisätty', f));
    return out_({ ok: true });
  }
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

// Lista odottavista kuvista. / قائمة الصور الي تنتظر.
function doGet() {
  var it = folder_(FOLDER).getFiles(), list = [];
  while (it.hasNext()) {
    var x = it.next();
    list.push({ id: x.getId(), name: x.getName(), desc: x.getDescription(), time: x.getDateCreated() });
  }
  return out_({ ok: true, files: list });
}

// Aja tämä kerran käsin, niin Google kysyy luvat. / شغّل هاي مرة وحدة حتى گوگل يطلب الموافقة.
function setup() {
  folder_('Lisätty', folder_(FOLDER));
}
