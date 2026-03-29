import pygame
import random
from typing import List, Dict

from pokemon import Pokemon


# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
LIGHT_GRAY = (200, 200, 200)
BLUE = (100, 100, 255)
GREEN = (50, 200, 50)
RED = (200, 50, 50)

# UI Constants
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
CARD_WIDTH = 280
CARD_HEIGHT = 320


def generate_ev_spread(pokemon: Pokemon) -> Dict[str, int]:
    """Generate a valid EV spread."""
    stats = ["hp", "atk", "def", "spa", "spd", "spe"]
    evs = {s: 0 for s in stats}

    remaining = 510
    while remaining > 0:
        stat = random.choice(stats)
        if evs[stat] < 252:
            add = min(random.randint(0, 64), remaining, 252 - evs[stat])
            evs[stat] += add
            remaining -= add

    return evs


def generate_offensive_spread(pokemon: Pokemon) -> Dict[str, int]:
    """Generate an offensive EV spread."""
    evs = {"hp": 0, "atk": 0, "def": 0, "spa": 0, "spd": 0, "spe": 0}

    if pokemon.base_stats["atk"] >= pokemon.base_stats["spa"]:
        evs["atk"] = 252
    else:
        evs["spa"] = 252

    evs["spe"] = 252
    evs["hp"] = 6

    return evs


def generate_defensive_spread(pokemon: Pokemon) -> Dict[str, int]:
    """Generate a defensive EV spread."""
    evs = {"hp": 252, "def": 128, "spd": 128, "atk": 0, "spa": 0, "spe": 0}
    return evs


def generate_balanced_spread(pokemon: Pokemon) -> Dict[str, int]:
    """Generate a balanced EV spread."""
    evs = {"hp": 85, "atk": 85, "def": 85, "spa": 85, "spd": 85, "spe": 85}
    return evs


class EVPicker:
    def __init__(self, screen: pygame.Surface, team: List[Pokemon]):
        self.screen = screen
        self.font_title = pygame.font.Font(None, 48)
        self.font_name = pygame.font.Font(None, 28)
        self.font_small = pygame.font.Font(None, 22)
        self.font_tiny = pygame.font.Font(None, 18)

        self.team = team
        self.current_pokemon_index = 0
        self.spread_options: List[Dict[str, int]] = []
        self.selection_rects: List[pygame.Rect] = []

    def run(self):
        """Run the EV picker for all Pokemon."""
        running = True
        clock = pygame.time.Clock()
        self.generate_options()

        while running:
            clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    return

                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = event.pos
                    for i, rect in enumerate(self.selection_rects):
                        if rect.collidepoint(pos):
                            self.select_spread(i)
                            break

            self.draw()

            if self.current_pokemon_index >= len(self.team):
                running = False

    def generate_options(self):
        """Generate 3 EV spread options."""
        pokemon = self.team[self.current_pokemon_index]
        self.spread_options = [
            generate_offensive_spread(pokemon),
            generate_defensive_spread(pokemon),
            generate_balanced_spread(pokemon)
        ]
        self.selection_rects = []

    def select_spread(self, option_index: int):
        """Select an EV spread from the options."""
        if 0 <= option_index < len(self.spread_options):
            evs = self.spread_options[option_index]
            self.team[self.current_pokemon_index].evs = evs

            pokemon = self.team[self.current_pokemon_index]
            pokemon.current_hp = pokemon.get_max_hp()

            self.current_pokemon_index += 1

            if self.current_pokemon_index < len(self.team):
                self.generate_options()

    def draw(self):
        """Draw the EV picker screen."""
        self.screen.fill(BLACK)

        title = self.font_title.render("Select EV Spread", True, WHITE)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 30))

        if self.current_pokemon_index >= len(self.team):
            return

        pokemon = self.team[self.current_pokemon_index]

        name = self.font_name.render(f"Select EV spread for {pokemon.name}", True, WHITE)
        self.screen.blit(name, (SCREEN_WIDTH // 2 - name.get_width() // 2, 100))

        options_label = self.font_small.render("Select an EV spread:", True, WHITE)
        self.screen.blit(options_label, (SCREEN_WIDTH // 2 - options_label.get_width() // 2, 150))

        self.draw_ev_options()
        pygame.display.flip()

    def draw_ev_options(self):
        """Draw EV spread selection options."""
        start_x = (SCREEN_WIDTH - 3 * CARD_WIDTH) // 2
        spread_names = ["Offensive", "Defensive", "Balanced"]

        for i, evs in enumerate(self.spread_options):
            x = start_x + i * (CARD_WIDTH + 20)
            rect = pygame.Rect(x, 190, CARD_WIDTH, CARD_HEIGHT)
            self.selection_rects.append(rect)
            self.draw_ev_card(rect, evs, spread_names[i])

    def draw_ev_card(self, rect: pygame.Rect, evs: Dict[str, int], spread_name: str):
        """Draw an EV spread card."""
        pygame.draw.rect(self.screen, LIGHT_GRAY, rect)
        pygame.draw.rect(self.screen, WHITE, rect, 3)

        name = self.font_title.render(spread_name, True, BLACK)
        self.screen.blit(name, (rect.centerx - name.get_width() // 2, rect.y + 15))

        total_evs = sum(evs.values())
        total = self.font_small.render(f"Total: {total_evs}/510", True, GREEN if total_evs <= 510 else RED)
        self.screen.blit(total, (rect.centerx - total.get_width() // 2, rect.y + 50))

        y_offset = 80
        stat_names = ["HP", "Atk", "Def", "SpA", "SpD", "Spe"]

        pokemon = self.team[self.current_pokemon_index]
        original_evs = pokemon.evs.copy()
        pokemon.evs = evs.copy()

        for j, stat in enumerate(["hp", "atk", "def", "spa", "spd", "spe"]):
            ev = evs[stat]
            eff = pokemon.get_effective_stat(stat)
            stat_line = f"{stat_names[j]}: {ev} EV -> {eff}"
            stat_text = self.font_tiny.render(stat_line, True, BLACK)
            self.screen.blit(stat_text, (rect.x + 20, rect.y + y_offset))
            y_offset += 30

        pokemon.evs = original_evs

        hint = self.font_small.render("Click to select", True, BLUE)
        self.screen.blit(hint, (rect.centerx - hint.get_width() // 2, rect.y + 285))