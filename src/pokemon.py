import random
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class Move:
    id: int
    name: str
    type: str
    category: str
    power: int
    accuracy: int
    pp: int
    effect: Optional[str]
    max_pp: int = field(init=False)

    def __post_init__(self):
        self.max_pp = self.pp


@dataclass
class Nature:
    name: str
    stat_up: Optional[str]
    stat_down: Optional[str]
    display: str

    def get_multiplier(self, stat_name: str) -> float:
        if self.stat_up == stat_name:
            return 1.1
        elif self.stat_down == stat_name:
            return 0.9
        return 1.0


@dataclass
class Pokemon:
    id: int
    name: str
    types: List[str]
    base_stats: Dict[str, int]
    nature: Optional[Nature] = None
    evs: Dict[str, int] = field(default_factory=lambda: {"hp": 0, "atk": 0, "def": 0, "spa": 0, "spd": 0, "spe": 0})
    moves: List[Move] = field(default_factory=list)
    current_hp: int = 0
    status: Optional[str] = None
    level: int = 50

    def __post_init__(self):
        if self.current_hp == 0:
            self.current_hp = self.get_effective_stat("hp")

    def get_effective_stat(self, stat_name: str) -> int:
        """Calculate effective stat with nature and EV modifiers."""
        base = self.base_stats.get(stat_name, 0)

        # Nature multiplier
        nature_mult = 1.0
        if self.nature:
            nature_mult = self.nature.get_multiplier(stat_name)

        # EV modifier: floor((ev / 4) + base)
        ev_value = self.evs.get(stat_name, 0)
        ev_bonus = ev_value // 4

        effective = int((base + ev_bonus) * nature_mult)
        return max(1, effective)

    def get_max_hp(self) -> int:
        """Calculate max HP including level and EVs."""
        base = self.base_stats.get("hp", 0)
        ev_value = self.evs.get("hp", 0)
        ev_bonus = ev_value // 4
        return int((base + ev_bonus) * 2 + self.level + 10)

    def take_damage(self, damage: int) -> int:
        """Apply damage and return actual damage dealt."""
        self.current_hp = max(0, self.current_hp - damage)
        return damage

    def heal(self, amount: int) -> int:
        """Heal HP and return actual amount healed."""
        max_hp = self.get_max_hp()
        actual = min(amount, max_hp - self.current_hp)
        self.current_hp = min(max_hp, self.current_hp + amount)
        return actual

    def is_fainted(self) -> bool:
        return self.current_hp <= 0

    def get_stat_names(self) -> List[str]:
        return ["hp", "atk", "def", "spa", "spd", "spe"]

    def has_type(self, type_name: str) -> bool:
        return type_name in self.types

    def total_evs(self) -> int:
        return sum(self.evs.values())

    def can_add_ev(self, stat: str, amount: int) -> bool:
        """Check if adding EVs would be valid."""
        total = self.total_evs()
        current = self.evs.get(stat, 0)
        return (total + amount <= 510 and current + amount <= 252)


def create_pokemon_from_data(pokemon_data: Dict[str, Any], moves_data: Dict[int, Any],
                             learnsets_data: Dict[str, List[int]],
                             natures_data: List[Dict[str, Any]]) -> 'Pokemon':
    """Create a Pokemon instance from loaded JSON data."""
    # Convert moves list to Move objects
    moves = []
    move_ids = learnsets_data.get(str(pokemon_data["id"]), [])
    for move_id in move_ids:
        if move_id in moves_data:
            move_info = moves_data[move_id]
            moves.append(Move(**move_info))

    return Pokemon(
        id=pokemon_data["id"],
        name=pokemon_data["name"],
        types=pokemon_data["types"],
        base_stats=pokemon_data["base_stats"],
        moves=moves
    )