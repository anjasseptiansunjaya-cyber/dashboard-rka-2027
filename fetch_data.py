#!/usr/bin/env python3
"""Tarik data RKA 2027 Engineering & PMO dari Google Sheets -> data.json
Jalankan ulang script ini tiap mau refresh dashboard (data 'live' on-demand)."""
import json, subprocess, sys, os

SPREADSHEET_ID = "1WUAK7S3Wpzqe9RyZBLaPQMeot6OiM5wW3tjyQMXFRcc"
REKAP_GID = "963284163"       # tab 4_Rekap
BIAYA_GID = "272950377"       # tab 1_Anggaran_Biaya
INVEST_GID = "513411873"      # tab 3_Anggaran_Investasi
SCRIPT = os.path.expandvars("$HERMES_HOME/skills/productivity/google-workspace/scripts/google_api.py")
PY = "/opt/data/.gvenv/bin/python"
MONTHS = ["Januari","Februari","Maret","April","Mei","Juni","Juli","Agustus","September","Oktober","November","Desember"]

def sheet_get(rng):
    out = subprocess.run([PY, SCRIPT, "sheets", "get", SPREADSHEET_ID, rng],
                          capture_output=True, text=True, check=True)
    return json.loads(out.stdout)

def to_num(s):
    if not s:
        return 0
    return int(str(s).replace(".", "").replace(",", "").strip() or 0)

def load_detail_items(tab_name, gid, last_row):
    """Kolom: No, Kode Akun, Nama Akun, Kelompok Laporan, Kode Dept, Uraian Kegiatan,
    Jenis Kegiatan, Objek Biaya, Satuan, Volume, Harga Satuan, Jumlah Setahun, Januari..."""
    rows = sheet_get(f"{tab_name}!A5:M{last_row}")
    by_kode = {}
    for i, r in enumerate(rows):
        if not r or len(r) < 6:
            continue
        r = (r + [""] * 13)[:13]
        _no, kode, _nama, _kel, _dept, uraian, jenis, objek, satuan, volume, harga, jumlah, _jan = r
        if not kode or not uraian:
            continue
        row_num = 5 + i
        by_kode.setdefault(kode, []).append({
            "uraian": uraian,
            "jenis": jenis,
            "objek": objek,
            "satuan": satuan,
            "volume": volume,
            "harga_satuan": to_num(harga),
            "jumlah": to_num(jumlah),
            "row": row_num,
            "sheet_url": f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={gid}&range=A{row_num}",
        })
    return by_kode

def main():
    rows = sheet_get("4_Rekap!A4:P200")
    header, *data = rows
    items = []
    total = 0
    start_row = 5

    detail_biaya = load_detail_items("1_Anggaran_Biaya", BIAYA_GID, 165)
    detail_invest = load_detail_items("3_Anggaran_Investasi", INVEST_GID, 90)

    for i, r in enumerate(data):
        row_num = start_row + i
        if not r or len(r) < 4:
            continue
        kode, nama, kelompok, jumlah = (r + ["", "", "", ""])[:4]
        if nama == "TOTAL":
            total = to_num(jumlah)
            continue
        if not nama or not kelompok:
            continue
        val = to_num(jumlah)
        if val == 0:
            continue
        bulanan = {}
        for mi, mname in enumerate(MONTHS):
            col = 5 + mi
            if col < len(r):
                bulanan[mname] = to_num(r[col])

        rincian = detail_biaya.get(kode, []) + detail_invest.get(kode, [])

        items.append({
            "kode": kode, "nama": nama, "kelompok": kelompok, "nilai": val,
            "row": row_num,
            "sheet_url": f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={REKAP_GID}&range=A{row_num}",
            "bulanan": bulanan,
            "rincian": rincian,
        })

    by_kelompok = {}
    for it in items:
        by_kelompok.setdefault(it["kelompok"], 0)
        by_kelompok[it["kelompok"]] += it["nilai"]

    items_sorted = sorted(items, key=lambda x: -x["nilai"])

    out = {
        "total": total or sum(by_kelompok.values()),
        "by_kelompok": by_kelompok,
        "items": items_sorted,
        "top10": items_sorted[:10],
        "source_url": f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={REKAP_GID}",
    }
    with open(os.path.join(os.path.dirname(__file__), "data.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    n_rincian = sum(len(it["rincian"]) for it in items)
    print(f"OK: {len(items)} akun, {n_rincian} item rincian, total Rp {out['total']:,}".replace(",", "."))

if __name__ == "__main__":
    main()
