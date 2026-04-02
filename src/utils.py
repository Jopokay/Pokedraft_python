import json
import random
from pathlib import Path
from typing import List, Dict, Any, Optional

TYPE_COLORS = {
    "Fire": (240, 128, 48), "Water": (104, 144, 240), "Grass": (120, 200, 80),
    "Electric": (248, 208, 48), "Psychic": (248, 88, 136), "Ice": (152, 216, 216),
    "Dragon": (112, 56, 248), "Normal": (168, 168, 152), "Fighting": (192, 48, 40),
    "Poison": (160, 64, 160), "Ground": (224, 192, 104), "Flying": (168, 144, 240),
    "Bug": (168, 184, 32), "Rock": (184, 160, 56), "Ghost": (112, 88, 152),
    "Steel": (184, 184, 208), "Dark": (112, 112, 112), "Fairy": (238, 153, 203),
}

_STAT_MAP = {
    "hp": "hp", "attack": "atk", "defense": "def",
    "special-attack": "spa", "special-defense": "spd", "speed": "spe",
    "atk": "atk", "def": "def", "spa": "spa", "spd": "spd", "spe": "spe",
}


def load_json(filepath: str) -> Any:
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def get_data_path(filename: str) -> Path:
    return Path(__file__).parent.parent / "data" / filename


def get_gen1_folder() -> Path:
    return Path(__file__).parent.parent / "Pokemon_Gen1"


# ── Legacy loaders ────────────────────────────────────────────────────────────

def load_pokemon_data() -> List[Dict[str, Any]]:
    return load_json(get_data_path("pokemon_gen1.json"))

def load_moves_data() -> Dict[int, Dict[str, Any]]:
    moves_list = load_json(get_data_path("moves_gen1.json"))
    return {m["id"]: m for m in moves_list}

def load_learnsets_data() -> Dict[str, List[int]]:
    return load_json(get_data_path("learnsets_gen1.json"))

def load_natures_data() -> List[Dict[str, Any]]:
    return load_json(get_data_path("natures.json"))


# ── Gen1 folder loaders ───────────────────────────────────────────────────────

def load_moves_by_name() -> Dict[str, Dict[str, Any]]:
    """Return moves_gen1 keyed by lowercase-hyphenated name."""
    moves_list = load_json(get_data_path("moves_gen1.json"))
    return {m["name"].lower().replace(" ", "-"): m for m in moves_list}


def load_pokemon_gen1_folder() -> List[Dict[str, Any]]:
    """Load all 151 Pokemon from Pokemon_Gen1/ with normalised fields."""
    folder = get_gen1_folder()
    result = []
    for path in sorted(folder.glob("*.json")):
        raw = load_json(str(path))
        bs_raw = raw.get("Statistiche_Base", {})
        base_stats = {_STAT_MAP[k]: v for k, v in bs_raw.items() if k in _STAT_MAP}
        types = [t.capitalize() for t in raw.get("Tipi", [])]
        result.append({
            "id":         raw["ID"],
            "name":       raw["Nome"],
            "types":      types,
            "base_stats": base_stats,
            "abilities":  raw.get("Abilita", []),
            "move_names": raw.get("Mosse_Apprendibili", []),
        })
    return result


def build_moves_for_pokemon(p_data: Dict, moves_by_name: Dict, count: int = 4) -> List[Dict]:
    """Pick up to count moves from a Gen1 folder entry."""
    available = [moves_by_name[n] for n in p_data["move_names"] if n.lower() in moves_by_name]
    offensive = [m for m in available if m["power"] > 0]
    support   = [m for m in available if m["power"] == 0]
    if len(offensive) >= count:
        return random.sample(offensive, count)
    need = min(count - len(offensive), len(support))
    return offensive + random.sample(support, need) if offensive or need else \
           random.sample(available, min(count, len(available)))


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_type_color(type_name: str) -> tuple:
    return TYPE_COLORS.get(type_name, (128, 128, 128))

def calculate_base_stat_total(pokemon_data: Dict) -> int:
    return sum(pokemon_data.get("base_stats", {}).values())

def format_stat_name(stat: str) -> str:
    return {"hp":"HP","atk":"Attack","def":"Defense",
            "spa":"Sp. Atk","spd":"Sp. Def","spe":"Speed"}.get(stat, stat.upper())

def get_random_pokemon(count, exclude_ids=None, pokemon_data=None):
    if exclude_ids is None: exclude_ids = []
    available = [p for p in pokemon_data if p["id"] not in exclude_ids]
    return random.sample(available, min(count, len(available)))

def get_random_moves(move_ids, count, exclude_ids=None, moves_data=None):
    if exclude_ids is None: exclude_ids = []
    available = [mid for mid in move_ids if mid not in exclude_ids]
    if len(available) < count:
        available = available + exclude_ids[:count - len(available)]
    return random.sample(available, min(count, len(available)))

def get_random_natures(count, natures_data=None):
    return random.sample(natures_data, min(count, len(natures_data)))
