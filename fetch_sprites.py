import os
import json
import urllib.request

OUTPUT_DIR = "assets/sprites"
DATA_FILE = "data/pokemon_gen1.json"

# NUOVI URL (colorati)
FRONT_URL = "https://img.pokemondb.net/sprites/diamond-pearl/normal/{name}.png"
BACK_URL = "https://img.pokemondb.net/sprites/heartgold-soulsilver/back-normal/{name}.png"

SPECIAL_NAMES = {
    "mr. mime": "mr-mime",
    "farfetch'd": "farfetchd"
}


def normalize_name(name):
    name = name.lower().strip()

    # CASI SPECIALI DAL TUO JSON
    if name == "nidoranf":
        return "nidoran-f"
    if name == "nidoranm":
        return "nidoran-m"
    if name == "mrmime":
        return "mr-mime"
    if name == "farfetchd":
        return "farfetchd"

    return name.replace(" ", "-")


def download_image(url, path):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    req = urllib.request.Request(url, headers=headers)

    with urllib.request.urlopen(req) as response, open(path, 'wb') as out_file:
        out_file.write(response.read())


def fetch_sprites():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        pokemon_list = json.load(f)

    print("Download sprite GEN4 iniziato...\n")

    for poke in pokemon_list:
        poke_id = poke["id"]
        raw_name = poke["name"]
        name = normalize_name(raw_name)

        front_filename = f"{poke_id:03d}.png"
        back_filename = f"{poke_id:03d}_back.png"

        front_path = os.path.join(OUTPUT_DIR, front_filename)
        back_path = os.path.join(OUTPUT_DIR, back_filename)

        front_url = FRONT_URL.format(name=name)
        back_url = BACK_URL.format(name=name)

        try:
            download_image(front_url, front_path)
            print(f"{front_filename} ✔ FRONT")
        except Exception as e:
            print(f"{front_filename} ✖ FRONT ({e})")

        try:
            download_image(back_url, back_path)
            print(f"{back_filename} ✔ BACK")
        except Exception as e:
            print(f"{back_filename} ✖ BACK ({e})")

    print("\n✅ Download completato!")


if __name__ == "__main__":
    fetch_sprites()
