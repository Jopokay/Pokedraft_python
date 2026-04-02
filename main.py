#!/usr/bin/env python3
"""Pokemon Draft — main entry point."""

import sys
import os
import pygame
import random
from typing import List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.pokemon import Pokemon, Nature, Move
from src.utils import (
    load_pokemon_gen1_folder, load_moves_by_name, build_moves_for_pokemon,
    load_natures_data,
    # legacy loaders (used by draft/pickers)
    load_pokemon_data, load_moves_data, load_learnsets_data,
)
from src.draft import DraftScreen
from src.move_picker import MovePicker
from src.nature_picker import NaturePicker
from src.ev_picker import EVPicker
from src.battle_ui import BattleUI
from src.transitions import phase_transition

SCREEN_WIDTH  = 1024
SCREEN_HEIGHT = 768


def generate_ai_team() -> List[Pokemon]:
    """Generate AI team using the accurate Pokemon_Gen1/ data."""
    gen1_data   = load_pokemon_gen1_folder()
    moves_by_nm = load_moves_by_name()
    natures_data = load_natures_data()

    team_data = random.sample(gen1_data, 6)
    result    = []

    for p_data in team_data:
        move_dicts = build_moves_for_pokemon(p_data, moves_by_nm, count=4)
        moves = [Move(**m) for m in move_dicts]

        pokemon = Pokemon(
            id=p_data["id"],
            name=p_data["name"],
            types=p_data["types"],
            base_stats=p_data["base_stats"],
            moves=moves,
        )

        pokemon.nature = Nature(**random.choice(natures_data))

        # Random EV spread biased toward offensive/defensive/balanced
        stats = ["hp","atk","def","spa","spd","spe"]
        evs   = {s: 0 for s in stats}
        spread_type = random.choice(["offensive","defensive","balanced"])
        if spread_type == "offensive":
            # Best offensive stat + speed
            if p_data["base_stats"].get("atk",0) >= p_data["base_stats"].get("spa",0):
                evs["atk"] = 252
            else:
                evs["spa"] = 252
            evs["spe"] = 252; evs["hp"] = 6
        elif spread_type == "defensive":
            evs["hp"] = 252; evs["def"] = 128; evs["spd"] = 128
        else:
            for s in stats: evs[s] = 85

        pokemon.evs       = evs
        pokemon.current_hp = pokemon.get_max_hp()
        result.append(pokemon)

    return result


def main():
    pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
    pygame.init()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Pokedraft")
    clock = pygame.time.Clock()

    running = True
    while running:

        # Phase 1: Draft ───────────────────────────────────────────────
        draft_screen = DraftScreen(screen)
        player_team  = draft_screen.run()
        if not player_team:
            break

        # Phase 2: Move Picker ────────────────────────────────────────
        phase_transition(screen, clock, "Selezione Mosse", out_ms=300, hold_ms=500, in_ms=300)
        MovePicker(screen, player_team).run()

        # Phase 3: Nature Picker ──────────────────────────────────────
        phase_transition(screen, clock, "Selezione Natura", out_ms=300, hold_ms=500, in_ms=300)
        NaturePicker(screen, player_team).run()

        # Phase 4: EV Picker ──────────────────────────────────────────
        phase_transition(screen, clock, "Distribuzione EV", out_ms=300, hold_ms=500, in_ms=300)
        EVPicker(screen, player_team).run()

        # Phase 5: Battle ─────────────────────────────────────────────
        phase_transition(screen, clock, "Lotta!", out_ms=400, hold_ms=700, in_ms=400)
        ai_team    = generate_ai_team()
        battle_ui  = BattleUI(screen, player_team, ai_team)
        result     = battle_ui.run()

        if result == "quit":
            running = False

    pygame.quit()


if __name__ == "__main__":
    main()
