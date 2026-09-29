var BIAYA_TAB = "1_Anggaran_Biaya";
var INVEST_TAB = "3_Anggaran_Investasi";
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
  if (typeof v === "number") return v;
  var s = String(v).replace(/\./g, "").replace(/,/g, ".").trim();
  var n = parseFloat(s);
  return isNaN(n) ? 0 : n;
}

function sheetByName(ss, name) {
  return ss.getSheetByName(name);
}

function loadItems(ss, tabName, kelompok) {
  var sh = sheetByName(ss, tabName);
  var out = [];
  if (!sh) return out;
  var lastRow = sh.getLastRow();
  if (lastRow < 5) return out;
  var rows = sh.getRange(5, 1, lastRow - 4, 24).getValues();
  var grouped = {};
  for (var i = 0; i < rows.length; i++) {
    var r = rows[i];
    var uraian = String(r[5] || "").trim();
    var jumlah = toNum(r[11]);
    if (!uraian || !jumlah || uraian.toUpperCase() === "JUMLAH") continue;
    var kode = String(r[1] || "").trim() || "BELUM-TERKLASIFIKASI";
    var nama = r[2] || (kelompok === "Investasi" ? "Investasi — Belum Terklasifikasi" : "Biaya — Belum Terklasifikasi");
    var rowNum = 5 + i;
    var key = kode + "|" + nama;
    if (!grouped[key]) grouped[key] = {
      kode: kode, nama: nama, kelompok: kelompok, nilai: 0,
      row: rowNum,
      sheet_url: "https://docs.google.com/spreadsheets/d/" + ss.getId() + "/edit#gid=" + sh.getSheetId() + "&range=A" + rowNum,
      bulanan: {}, rincian: []
    };
    var item = grouped[key];
    item.nilai += jumlah;
    for (var mi = 0; mi < MONTHS.length; mi++) {
      var v = r[12 + mi];
      if (v !== "" && v !== null && v !== undefined) {
        item.bulanan[MONTHS[mi]] = (item.bulanan[MONTHS[mi]] || 0) + toNum(v);
      } else if (item.bulanan[MONTHS[mi]] === undefined) {
        item.bulanan[MONTHS[mi]] = 0;
      }
    }
    item.rincian.push({
      uraian: uraian, jenis: r[6], objek: r[7], satuan: r[8],
      volume: r[9], harga_satuan: Math.round(toNum(r[10])), jumlah: Math.round(jumlah),
      row: rowNum,
      sheet_url: "https://docs.google.com/spreadsheets/d/" + ss.getId() + "/edit#gid=" + sh.getSheetId() + "&range=A" + rowNum
    });
  }
  for (var k in grouped) out.push(grouped[k]);
  return out;
}

function getData() {
  var ss = SpreadsheetApp.getActive();
  var items = loadItems(ss, BIAYA_TAB, "Biaya")
    .concat(loadItems(ss, INVEST_TAB, "Investasi"));
  items.forEach(function (it) {
    it.nilai = Math.round(it.nilai);
    for (var m in it.bulanan) it.bulanan[m] = Math.round(it.bulanan[m]);
  });
  items.sort(function (a, b) { return b.nilai - a.nilai; });

  var byKelompok = {};
  items.forEach(function (it) {
    byKelompok[it.kelompok] = (byKelompok[it.kelompok] || 0) + it.nilai;
  });

  var total = 0;
  for (var k2 in byKelompok) total += byKelompok[k2];

  return {
    total: total,
    by_kelompok: byKelompok,
    items: items,
    top10: items.slice(0, 10),
    source_url: "https://docs.google.com/spreadsheets/d/" + ss.getId() + "/edit",
    generated_at: new Date().toISOString()
  };
}
