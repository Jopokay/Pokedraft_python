#!/usr/bin/env python3
"""
Pokemon Draft - A Pokemon battle application using Pygame
"""

import sys
import os
import pygame
import random
from typing import List

# Fix imports: let src/ files use bare 'from pokemon import ...' etc.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.pokemon import Pokemon, Nature, Move
from src.utils import (
    load_pokemon_data, load_moves_data, load_learnsets_data, load_natures_data
)
from src.draft import DraftScreen
from src.move_picker import MovePicker
from src.nature_picker import NaturePicker
from src.ev_picker import EVPicker
from src.battle_ui import BattleUI


SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768


def generate_ai_team() -> List[Pokemon]:
    """Generate a random AI team."""
    pokemon_data = load_pokemon_data()
    moves_data = load_moves_data()
    learnsets_data = load_learnsets_data()
    natures_data = load_natures_data()

    team = random.sample(pokemon_data, 6)

    result = []
    for p_data in team:
        move_ids = learnsets_data.get(str(p_data["id"]), [])
        all_moves = []
        for mid in move_ids:
            if mid in moves_data:
                all_moves.append(Move(**moves_data[mid]))

        # FIX: was pokemon_data["name"] (list) instead of p_data["name"]
        pokemon = Pokemon(
            id=p_data["id"],
            name=p_data["name"],
            types=p_data["types"],
            base_stats=p_data["base_stats"],
            moves=[]
        )

        nature_data = random.choice(natures_data)
        pokemon.nature = Nature(**nature_data)

        stats = ["hp", "atk", "def", "spa", "spd", "spe"]
        evs = {s: 0 for s in stats}
        remaining = 510
        while remaining > 0:
            stat = random.choice(stats)
            if evs[stat] < 252:
                add = random.randint(0, min(64, remaining, 252 - evs[stat]))
                evs[stat] += add
                remaining -= add

        pokemon.evs = evs
        pokemon.current_hp = pokemon.get_max_hp()

        if len(all_moves) >= 4:
            pokemon.moves = random.sample(all_moves, 4)
        else:
            pokemon.moves = all_moves

        result.append(pokemon)

    return result


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Pokemon Draft")

    running = True
    while running:
        draft_screen = DraftScreen(screen)
        player_team = draft_screen.run()

        if not player_team:
            running = False
            break

        MovePicker(screen, player_team).run()
        NaturePicker(screen, player_team).run()
        EVPicker(screen, player_team).run()

        ai_team = generate_ai_team()

        battle_ui = BattleUI(screen, player_team, ai_team)
        result = battle_ui.run()

        if result == "quit":
            running = False

    pygame.quit()


if __name__ == "__main__":
    main()
