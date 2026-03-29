import json
import random
from pathlib import Path
from typing import List, Dict, Any, Optional

# Type colors for UI rendering
TYPE_COLORS = {
    "Fire": (240, 128, 48),
    "Water": (104, 144, 240),
    "Grass": (120, 200, 80),
    "Electric": (248, 208, 48),
    "Psychic": (248, 88, 136),
    "Ice": (152, 216, 216),
    "Dragon": (112, 56, 248),
    "Normal": (168, 168, 152),
    "Fighting": (192, 48, 40),
    "Poison": (160, 64, 160),
    "Ground": (224, 192, 104),
    "Flying": (168, 144, 240),
    "Bug": (168, 184, 32),
    "Rock": (184, 160, 56),
    "Ghost": (112, 88, 152),
    "Steel": (184, 184, 208),
    "Dark": (112, 112, 112),
    "Fairy": (238, 153, 203)
}


def load_json(filepath: str) -> Any:
    """Load JSON data from file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def get_data_path(filename: str) -> Path:
    """Get path to data file."""
    return Path(__file__).parent.parent / "data" / filename


def load_pokemon_data() -> List[Dict[str, Any]]:
    """Load all Pokemon data."""
    return load_json(get_data_path("pokemon_gen1.json"))


def load_moves_data() -> Dict[int, Dict[str, Any]]:
    """Load all moves data as dict by ID."""
    moves_list = load_json(get_data_path("moves_gen1.json"))
    return {move["id"]: move for move in moves_list}


def load_learnsets_data() -> Dict[str, List[int]]:
    """Load Pokemon learnsets."""
    return load_json(get_data_path("learnsets_gen1.json"))


def load_natures_data() -> List[Dict[str, Any]]:
    """Load all natures data."""
    return load_json(get_data_path("natures.json"))


def get_random_pokemon(count: int, exclude_ids: List[int] = None,
                       pokemon_data: List[Dict] = None) -> List[Dict]:
    """Get random Pokemon from the dataset."""
    if exclude_ids is None:
        exclude_ids = []

    available = [p for p in pokemon_data if p["id"] not in exclude_ids]
    return random.sample(available, min(count, len(available)))


def get_random_moves(move_ids: List[int], count: int, exclude_ids: List[int] = None,
                     moves_data: Dict = None) -> List[Dict]:
    """Get random moves from learnable moves."""
    if exclude_ids is None:
        exclude_ids = []

    available = [mid for mid in move_ids if mid not in exclude_ids]
    if len(available) < count:
        available = available + exclude_ids[:count - len(available)]
    return random.sample(available, min(count, len(available)))


def get_random_natures(count: int, natures_data: List[Dict] = None) -> List[Dict]:
    """Get random natures from the dataset."""
    return random.sample(natures_data, min(count, len(natures_data)))


def get_type_color(type_name: str) -> tuple:
    """Get RGB color for a Pokemon type."""
    return TYPE_COLORS.get(type_name, (128, 128, 128))


def calculate_base_stat_total(pokemon_data: Dict) -> int:
    """Calculate total of base stats."""
    stats = pokemon_data.get("base_stats", {})
    return sum(stats.values())


def format_stat_name(stat: str) -> str:
    """Format stat name for display."""
    stat_map = {
        "hp": "HP", "atk": "Attack", "def": "Defense",
        "spa": "Sp. Atk", "spd": "Sp. Def", "spe": "Speed"
    }
    return stat_map.get(stat, stat.upper())