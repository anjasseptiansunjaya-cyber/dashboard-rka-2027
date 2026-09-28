#!/usr/bin/env python3
"""Regression checks for published RKA dashboard data."""
import json
from pathlib import Path

DATA = Path(__file__).with_name("data.json")


def main():
    d = json.loads(DATA.read_text(encoding="utf-8"))
    assert d["by_kelompok"].get("Biaya") == 6_724_129_542, d["by_kelompok"]
    assert d["by_kelompok"].get("Investasi") == 12_321_503_244, d["by_kelompok"]
    assert d["total"] == 19_045_632_786, d["total"]
    assert any(i["kelompok"] == "Investasi" for i in d["items"]), "investasi absent"
    assert any(i["kode"] == "BELUM-TERKLASIFIKASI" for i in d["items"]), "uncoded investment bucket absent"
    assert sum(i["nilai"] for i in d["items"]) == d["total"], "item total mismatch"
    for item in d["items"]:
        assert abs(sum(item.get("bulanan", {}).values()) - item["nilai"]) <= 2, (item["kode"], item["nilai"], item.get("bulanan"))
    print("PASS: biaya, investasi, total, klasifikasi, dan bulanan konsisten")


if __name__ == "__main__":
    main()
