#!/usr/bin/env python3
"""Tarik data RKA 2027 Engineering & PMO dari Google Sheets -> data.json."""
import json, os, sys

SPREADSHEET_ID = "1WUAK7S3Wpzqe9RyZBLaPQMeot6OiM5wW3tjyQMXFRcc"
BIAYA_GID = "272950377"
INVEST_GID = "513411873"
SCRIPTS = os.path.join(os.path.expandvars("$HERMES_HOME"), "skills", "productivity", "google-workspace", "scripts")
sys.path.insert(0, SCRIPTS)
import google_api as _g  # noqa: E402

_sheets = _g.build_service("sheets", "v4")
MONTHS = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]


def sheet_get(rng):
    result = _sheets.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=rng, valueRenderOption="UNFORMATTED_VALUE"
    ).execute()
    return result.get("values", [])


def to_num(s):
    if s in (None, ""):
        return 0.0
    if isinstance(s, (int, float)):
        return float(s)
    return float(str(s).replace(".", "").replace(",", ".").strip() or 0)


def load_items(tab_name, gid, kelompok, last_row):
    rows = sheet_get(f"{tab_name}!A5:X{last_row}")
    grouped = {}
    for i, raw in enumerate(rows):
        r = (raw + [""] * 24)[:24]
        _no, kode, nama, _kel, _dept, uraian, jenis, objek, satuan, volume, harga, jumlah, *bulan = r
        jumlah = to_num(jumlah)
        uraian = str(uraian or "").strip()
        if not uraian or not jumlah or uraian.upper() == "JUMLAH":
            continue
        kode = str(kode).strip() if kode else "BELUM-TERKLASIFIKASI"
        nama = nama or ("Investasi — Belum Terklasifikasi" if kelompok == "Investasi" else "Biaya — Belum Terklasifikasi")
        row_num = 5 + i
        key = (kode, nama)
        item = grouped.setdefault(key, {
            "kode": kode, "nama": nama, "kelompok": kelompok, "nilai": 0,
            "row": row_num,
            "sheet_url": f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={gid}&range=A{row_num}",
            "bulanan": {m: 0 for m in MONTHS}, "rincian": [],
        })
        item["nilai"] += jumlah
        for m, value in zip(MONTHS, bulan):
            if value != "":
                item["bulanan"][m] += to_num(value)
        item["rincian"].append({
            "uraian": uraian, "jenis": jenis, "objek": objek, "satuan": satuan,
            "volume": volume, "harga_satuan": to_num(harga), "jumlah": jumlah,
            "row": row_num,
            "sheet_url": f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={gid}&range=A{row_num}",
        })
    return list(grouped.values())


def main():
    items = load_items("1_Anggaran_Biaya", BIAYA_GID, "Biaya", 165)
    items += load_items("3_Anggaran_Investasi", INVEST_GID, "Investasi", 90)
    items.sort(key=lambda x: -x["nilai"])

    by_kelompok = {}
    for item in items:
        by_kelompok[item["kelompok"]] = by_kelompok.get(item["kelompok"], 0) + item["nilai"]

    out = {
        "total": round(sum(by_kelompok.values())),
        "by_kelompok": {k: round(v) for k, v in by_kelompok.items()},
        "items": [{**it, "nilai": round(it["nilai"]),
                   "bulanan": {m: round(v) for m, v in it["bulanan"].items()},
                   "rincian": [{**r, "harga_satuan": round(r["harga_satuan"]), "jumlah": round(r["jumlah"])} for r in it["rincian"]]}
                  for it in items],
        "top10": items[:10],
        "source_url": f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit",
    }
    with open(os.path.join(os.path.dirname(__file__), "data.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    n_rincian = sum(len(it["rincian"]) for it in items)
    print(f"OK: {len(items)} kelompok akun, {n_rincian} item rincian, total Rp {out['total']:,}".replace(",", "."))


if __name__ == "__main__":
    main()
