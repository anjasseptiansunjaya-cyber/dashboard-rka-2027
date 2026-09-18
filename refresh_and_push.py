#!/usr/bin/env python3
"""Refresh data dari Sheets lalu push ke GitHub Pages.
Jalankan: python3 refresh_and_push.py
"""
import subprocess, os

DIR = os.path.dirname(os.path.abspath(__file__))

def run(cmd):
    print("$", " ".join(cmd))
    r = subprocess.run(cmd, cwd=DIR, capture_output=True, text=True)
    print(r.stdout)
    if r.returncode != 0:
        print("ERROR:", r.stderr)
    return r.returncode == 0

def main():
    if not run(["python3", "fetch_data.py"]):
        return
    run(["git", "add", "data.json"])
    r = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=DIR)
    if r.returncode == 0:
        print("Tidak ada perubahan data.")
        return
    run(["git", "commit", "-m", "Update data RKA"])
    run(["git", "push"])
    print("Selesai. Dashboard: https://anjasseptiansunjaya-cyber.github.io/dashboard-rka-2027/")

if __name__ == "__main__":
    main()
