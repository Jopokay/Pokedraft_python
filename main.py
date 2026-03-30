#!/usr/bin/env python3
"""
Pokemon Draft — main entry point.
"""

import sys
import os
import pygame
import random
from typing import List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.pokemon import Pokemon, Nature, Move
from src.utils import load_pokemon_data, load_moves_data, load_learnsets_data, load_natures_data
from src.draft import DraftScreen
from src.move_picker import MovePicker
from src.nature_picker import NaturePicker
from src.ev_picker import EVPicker
from src.battle_ui import BattleUI
from src.transitions import phase_transition

SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768


def generate_ai_team() -> List[Pokemon]:
    pokemon_data = load_pokemon_data()
    moves_data   = load_moves_data()
    learnsets    = load_learnsets_data()
    natures_data = load_natures_data()

    team = random.sample(pokemon_data, 6)
    result = []

    for p_data in team:
        move_ids = learnsets.get(str(p_data["id"]), [])
        all_moves = [Move(**moves_data[mid]) for mid in move_ids if mid in moves_data]

        pokemon = Pokemon(
            id=p_data["id"],
            name=p_data["name"],
            types=p_data["types"],
            base_stats=p_data["base_stats"],
            moves=[]
        )
        pokemon.nature = Nature(**random.choice(natures_data))

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
        pokemon.moves = random.sample(all_moves, 4) if len(all_moves) >= 4 else all_moves

        result.append(pokemon)

    return result


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Pokemon Draft")
    clock = pygame.time.Clock()

    running = True
    while running:

        # ── Phase 1: Draft ──────────────────────────────────────────────
        draft_screen = DraftScreen(screen)
        player_team = draft_screen.run()

        if not player_team:
            break

        # ── Phase 2: Move Picker ────────────────────────────────────────
        phase_transition(screen, clock, "Move Selection", out_ms=300, hold_ms=500, in_ms=300)
        MovePicker(screen, player_team).run()

        # ── Phase 3: Nature Picker ──────────────────────────────────────
        phase_transition(screen, clock, "Nature Selection", out_ms=300, hold_ms=500, in_ms=300)
        NaturePicker(screen, player_team).run()

        # ── Phase 4: EV Picker ──────────────────────────────────────────
        phase_transition(screen, clock, "EV Spread Selection", out_ms=300, hold_ms=500, in_ms=300)
        EVPicker(screen, player_team).run()

        # ── Phase 5: Battle ─────────────────────────────────────────────
        phase_transition(screen, clock, "Battle!", out_ms=400, hold_ms=700, in_ms=400)
        ai_team = generate_ai_team()
        battle_ui = BattleUI(screen, player_team, ai_team)
        result = battle_ui.run()

        if result == "quit":
            running = False

    pygame.quit()


if __name__ == "__main__":
    main()
