#!/usr/bin/env python3
"""
fetch_sprites.py — Download Gen 1 Pokemon sprites from PokeAPI GitHub.

Usage:
    python fetch_sprites.py

Sprites are saved to assets/sprites/001.png ... 151.png
Source: https://github.com/PokeAPI/sprites (public domain / free to use)
"""

import urllib.request
import os
import time

SPRITE_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{id}.png"
OUTPUT_DIR = "assets/sprites"
TOTAL = 151


def fetch_sprites():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Downloading {TOTAL} sprites to {OUTPUT_DIR}/")
    print("Source: github.com/PokeAPI/sprites\n")

    success = 0
    failed = []

    for poke_id in range(1, TOTAL + 1):
        filename = f"{poke_id:03d}.png"
        filepath = os.path.join(OUTPUT_DIR, filename)

        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            print(f"  [{poke_id:3d}/{TOTAL}] {filename} — already exists, skipping")
            success += 1
            continue

        url = SPRITE_URL.format(id=poke_id)
        try:
            urllib.request.urlretrieve(url, filepath)
            size = os.path.getsize(filepath)
            print(f"  [{poke_id:3d}/{TOTAL}] {filename} — OK ({size} bytes)")
            success += 1
            time.sleep(0.05)  # gentle rate limit
        except Exception as e:
            print(f"  [{poke_id:3d}/{TOTAL}] {filename} — FAILED: {e}")
            failed.append(poke_id)

    print(f"\nDone! {success}/{TOTAL} sprites downloaded.")
    if failed:
        print(f"Failed IDs: {failed}")
        print("Re-run the script to retry failed downloads.")
    else:
        print("All sprites downloaded successfully!")


if __name__ == "__main__":
    fetch_sprites()
