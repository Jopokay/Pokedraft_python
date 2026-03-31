import os
import json
import urllib.request

# Cartella output
OUTPUT_DIR = "assets/sprites"

# File dati Pokémon
DATA_FILE = "data/pokemon_gen1.json"

# URL PokemonDB (Gen1 Red/Blue)
FRONT_URL = "https://img.pokemondb.net/sprites/red-blue/normal/{name}.png"
BACK_URL = "https://img.pokemondb.net/sprites/red-blue/back/{name}.png"

# Nomi speciali che PokemonDB usa diversi
SPECIAL_NAMES = {
    "mr. mime": "mr-mime",
    "farfetch'd": "farfetchd",
    "nidoran♀": "nidoran-f",
    "nidoran♂": "nidoran-m"
}


def normalize_name(name):
    name = name.lower()
    if name in SPECIAL_NAMES:
        return SPECIAL_NAMES[name]
    return name.replace(" ", "-")


def fetch_sprites():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        pokemon_list = json.load(f)

    print("Download sprite iniziato...\n")

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
            urllib.request.urlretrieve(front_url, front_path)
            print(f"{front_filename} ✔")
        except Exception:
            print(f"{front_filename} ✖ (FRONT FAILED: {front_url})")

        try:
            urllib.request.urlretrieve(back_url, back_path)
            print(f"{back_filename} ✔")
        except Exception:
            print(f"{back_filename} ✖ (BACK FAILED: {back_url})")

    print("\nDownload completato!")


if __name__ == "__main__":
    fetch_sprites()
