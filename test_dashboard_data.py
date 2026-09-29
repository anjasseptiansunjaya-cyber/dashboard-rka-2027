#!/usr/bin/env python3
"""Regression checks for published RKA dashboard data.

Angka acuan TIDAK di-hardcode: dibandingkan langsung dengan Google Sheets
via fetch_data pada saat test. Test gagal hanya jika data.json tidak cocok
dengan sheet (bukan karena angka berubah).
"""
import json
import subprocess
import sys
from pathlib import Path

DIR = Path(__file__).parent
DATA = DIR / "data.json"


def to_num(v):
    try:
        return float(str(v).replace(",", "")) if str(v).strip() != "" else 0.0
    except (ValueError, TypeError):
        return 0.0


def sheet_totals():
    sys.path.insert(0, str(DIR))
    import fetch_data  # build_service dsb sudah siap
    biaya = fetch_data.load_items("1_Anggaran_Biaya", fetch_data.BIAYA_GID, "Biaya", 165)
    inv = fetch_data.load_items("3_Anggaran_Investasi", fetch_data.INVEST_GID, "Investasi", 90)
    return int(round(sum(i["nilai"] for i in biaya))), int(round(sum(i["nilai"] for i in inv)))


def main():
    d = json.loads(DATA.read_text(encoding="utf-8"))
    biaya, inv = sheet_totals()

    assert d["by_kelompok"].get("Biaya") == biaya, (d["by_kelompok"], biaya)
    assert d["by_kelompok"].get("Investasi") == inv, (d["by_kelompok"], inv)
    assert d["total"] == biaya + inv, d["total"]
    assert any(i["kelompok"] == "Investasi" for i in d["items"]), "investasi absent"
    assert any(i["kode"] == "BELUM-TERKLASIFIKASI" for i in d["items"]), "uncoded investment bucket absent"
    assert sum(i["nilai"] for i in d["items"]) == d["total"], "item total mismatch"
    for item in d["items"]:
        assert abs(sum(item.get("bulanan", {}).values()) - item["nilai"]) <= 2, (item["kode"], item["nilai"], item.get("bulanan"))
    print(f"PASS: data.json == Google Sheet (Biaya {biaya:,} | Investasi {inv:,} | total {d['total']:,})")


if __name__ == "__main__":
    main()
