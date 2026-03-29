#!/usr/bin/env python3
"""
Pokemon Draft - A Pokemon battle application using Pygame
"""

import pygame
import random
from typing import List

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

    # Pick 6 random Pokemon
    team = random.sample(pokemon_data, 6)

    result = []
    for p_data in team:
        move_ids = learnsets_data.get(str(p_data["id"]), [])
        moves = []

        for mid in move_ids:
            if mid in moves_data:
                moves.append(Move(**moves_data[mid]))

        # Create Pokemon
        pokemon = Pokemon(
            id=p_data["id"],
            name=pokemon_data["name"],
            types=pokemon_data["types"],
            base_stats=pokemon_data["base_stats"],
            moves=moves
        )

        # Random nature
        nature_data = random.choice(natures_data)
        pokemon.nature = Nature(**nature_data)

        # Random EVs
        stats = ["hp", "atk", "def", "spa", "spd", "spe"]
        evs = {s: 0 for s in stats}
        remaining = 510
        while remaining > 0:
            stat = random.choice(stats)
            if evs[stat] < 252:
                add = random.randint(0, min(64, remaining))
                evs[stat] = min(252, evs[stat] + add)
                remaining -= add

        pokemon.evs = evs
        pokemon.current_hp = pokemon.get_max_hp()

        # Select 4 random moves
        if len(pokemon.moves) >= 4:
            pokemon.moves = random.sample(pokemon.moves, 4)

        result.append(pokemon)

    return result


def main():
    """Main entry point."""
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Pokemon Draft")
    clock = pygame.time.Clock()

    running = True

    while running:
        # Phase 1: Draft
        draft_screen = DraftScreen(screen)
        player_team = draft_screen.run()

        if not player_team:
            running = False
            break

        # Phase 2: Move Picker
        move_picker = MovePicker(screen, player_team)
        move_picker.run()

        # Phase 3: Nature Picker
        nature_picker = NaturePicker(screen, player_team)
        nature_picker.run()

        # Phase 4: EV Picker
        ev_picker = EVPicker(screen, player_team)
        ev_picker.run()

        # Phase 5: Generate AI team
        ai_team = generate_ai_team()

        # Phase 6: Battle
        battle_ui = BattleUI(screen, player_team, ai_team)
        result = battle_ui.run()

        if result == "quit":
            running = False

    pygame.quit()


if __name__ == "__main__":
    main()