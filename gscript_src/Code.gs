var REKAP_GID = 963284163;
var BIAYA_GID = 272950377;
var INVEST_GID = 513411873;
var MONTHS = ["Januari","Februari","Maret","April","Mei","Juni","Juli","Agustus","September","Oktober","November","Desember"];

function doGet(e) {
  if (e && e.parameter && e.parameter.data === "1") {
    return ContentService.createTextOutput(JSON.stringify(getData()))
      .setMimeType(ContentService.MimeType.JSON);
  }
  return HtmlService.createTemplateFromFile("Index").evaluate()
    .setTitle("Dashboard RKA 2027")
    .addMetaTag("viewport", "width=device-width, initial-scale=1");
}

function toNum(v) {
  if (v === "" || v === null || v === undefined) return 0;
  if (typeof v === "number") return Math.round(v);
  var s = String(v).replace(/\./g, "").replace(/,/g, "").trim();
  var n = parseInt(s, 10);
  return isNaN(n) ? 0 : n;
}

function sheetByGid(ss, gid) {
  var sheets = ss.getSheets();
  for (var i = 0; i < sheets.length; i++) {
    if (sheets[i].getSheetId() === gid) return sheets[i];
  }
  return null;
}

function loadDetailItems(ss, gid) {
  var sh = sheetByGid(ss, gid);
  var byKode = {};
  if (!sh) return byKode;
  var lastRow = sh.getLastRow();
  if (lastRow < 5) return byKode;
  var rows = sh.getRange(5, 1, lastRow - 4, 13).getValues();
  for (var i = 0; i < rows.length; i++) {
    var r = rows[i];
    var kode = r[1], uraian = r[5], jenis = r[6], objek = r[7],
        satuan = r[8], volume = r[9], harga = r[10], jumlah = r[11];
    if (!kode || !uraian) continue;
    var rowNum = 5 + i;
    if (!byKode[kode]) byKode[kode] = [];
    byKode[kode].push({
      uraian: uraian, jenis: jenis, objek: objek, satuan: satuan,
      volume: volume, harga_satuan: toNum(harga), jumlah: toNum(jumlah),
      row: rowNum,
      sheet_url: "https://docs.google.com/spreadsheets/d/" + ss.getId() + "/edit#gid=" + gid + "&range=A" + rowNum
    });
  }
  return byKode;
}

function getData() {
  var ss = SpreadsheetApp.getActive();
  var rekap = sheetByGid(ss, REKAP_GID);
  var lastRow = rekap.getLastRow();
  var rows = rekap.getRange(4, 1, lastRow - 3, 16).getValues();
  var header = rows[0];

  var detailBiaya = loadDetailItems(ss, BIAYA_GID);
  var detailInvest = loadDetailItems(ss, INVEST_GID);

  var items = [];
  var total = 0;
  var startRow = 5;
  for (var i = 1; i < rows.length; i++) {
    var r = rows[i];
    var rowNum = startRow + (i - 1);
    var kode = r[0], nama = r[1], kelompok = r[2], jumlah = r[3];
    if (nama === "TOTAL") { total = toNum(jumlah); continue; }
    if (!nama || !kelompok) continue;
    var val = toNum(jumlah);
    if (val === 0) continue;
    var bulanan = {};
    for (var mi = 0; mi < MONTHS.length; mi++) {
      var col = 4 + mi;
      if (col < r.length) bulanan[MONTHS[mi]] = toNum(r[col]);
    }
    var rincian = (detailBiaya[kode] || []).concat(detailInvest[kode] || []);
    items.push({
      kode: kode, nama: nama, kelompok: kelompok, nilai: val, row: rowNum,
      sheet_url: "https://docs.google.com/spreadsheets/d/" + ss.getId() + "/edit#gid=" + REKAP_GID + "&range=A" + rowNum,
      bulanan: bulanan, rincian: rincian
    });
  }

  var byKelompok = {};
  items.forEach(function (it) {
    byKelompok[it.kelompok] = (byKelompok[it.kelompok] || 0) + it.nilai;
  });
  items.sort(function (a, b) { return b.nilai - a.nilai; });

  var sumBK = 0;
  for (var k in byKelompok) sumBK += byKelompok[k];

  return {
    total: total || sumBK,
    by_kelompok: byKelompok,
    items: items,
    top10: items.slice(0, 10),
    source_url: "https://docs.google.com/spreadsheets/d/" + ss.getId() + "/edit#gid=" + REKAP_GID,
    generated_at: new Date().toISOString()
  };
}
