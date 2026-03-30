import pygame
import random
from typing import List

from pokemon import Pokemon, Nature
from utils import load_natures_data


WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
LIGHT_GRAY = (200, 200, 200)
BLUE = (100, 100, 255)
GREEN = (50, 200, 50)
RED = (200, 50, 50)

SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
CARD_WIDTH = 280
CARD_HEIGHT = 200


class NaturePicker:
    def __init__(self, screen: pygame.Surface, team: List[Pokemon]):
        self.screen = screen
        self.font_title = pygame.font.Font(None, 48)
        self.font_name = pygame.font.Font(None, 28)
        self.font_small = pygame.font.Font(None, 22)
        self.font_tiny = pygame.font.Font(None, 18)

        self.team = team
        self.current_pokemon_index = 0

        self.natures_data = load_natures_data()
        self.selection_options: List[Nature] = []
        self.selection_rects: List[pygame.Rect] = []

        self.generate_options()

    def run(self):
        running = True
        clock = pygame.time.Clock()

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
                            self.select_nature(i)
                            break

            self.draw()

            if self.current_pokemon_index >= len(self.team):
                running = False

    def generate_options(self):
        options = random.sample(self.natures_data, min(3, len(self.natures_data)))
        self.selection_options = [Nature(**n) for n in options]
        self.selection_rects = []

    def select_nature(self, option_index: int):
        if 0 <= option_index < len(self.selection_options):
            nature = self.selection_options[option_index]
            self.team[self.current_pokemon_index].nature = nature
            self.current_pokemon_index += 1
            if self.current_pokemon_index < len(self.team):
                self.generate_options()

    def draw(self):
        self.screen.fill(BLACK)

        title = self.font_title.render("Select Nature", True, WHITE)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 30))

        if self.current_pokemon_index >= len(self.team):
            return

        pokemon = self.team[self.current_pokemon_index]

        name = self.font_name.render(f"Select nature for {pokemon.name}", True, WHITE)
        self.screen.blit(name, (SCREEN_WIDTH // 2 - name.get_width() // 2, 100))

        if pokemon.nature:
            nature_display = self.font_name.render(pokemon.nature.display, True, GREEN)
            self.screen.blit(nature_display, (50, 190))
        else:
            nature_display = self.font_name.render("Not selected yet", True, DARK_GRAY)
            self.screen.blit(nature_display, (50, 190))

        options_label = self.font_small.render("Select a nature:", True, WHITE)
        self.screen.blit(options_label, (SCREEN_WIDTH // 2 - options_label.get_width() // 2, 260))

        self.draw_nature_options()
        pygame.display.flip()

    def draw_nature_options(self):
        # FIX: clear rects each frame
        self.selection_rects = []
        start_x = (SCREEN_WIDTH - 3 * CARD_WIDTH) // 2 - 10

        for i, nature in enumerate(self.selection_options):
            x = start_x + i * (CARD_WIDTH + 20)
            rect = pygame.Rect(x, 320, CARD_WIDTH, CARD_HEIGHT)
            self.selection_rects.append(rect)
            self.draw_nature_card(rect, nature)

    def draw_nature_card(self, rect: pygame.Rect, nature: Nature):
        pygame.draw.rect(self.screen, LIGHT_GRAY, rect)
        pygame.draw.rect(self.screen, WHITE, rect, 3)

        name = self.font_title.render(nature.name, True, BLACK)
        self.screen.blit(name, (rect.centerx - name.get_width() // 2, rect.y + 15))

        y_offset = 70
        if nature.stat_up:
            boosted = self.font_name.render(f"+10% {nature.stat_up.upper()}", True, GREEN)
            self.screen.blit(boosted, (rect.centerx - boosted.get_width() // 2, rect.y + y_offset))
            y_offset += 35
        if nature.stat_down:
            lowered = self.font_name.render(f"-10% {nature.stat_down.upper()}", True, RED)
            self.screen.blit(lowered, (rect.centerx - lowered.get_width() // 2, rect.y + y_offset))
            y_offset += 35

        if not nature.stat_up and not nature.stat_down:
            neutral = self.font_small.render("No stat change (neutral)", True, GRAY)
            self.screen.blit(neutral, (rect.centerx - neutral.get_width() // 2, rect.y + 70))

        display = self.font_tiny.render(nature.display, True, DARK_GRAY)
        self.screen.blit(display, (rect.centerx - display.get_width() // 2, rect.y + 150))

        hint = self.font_small.render("Click to select", True, BLUE)
        self.screen.blit(hint, (rect.centerx - hint.get_width() // 2, rect.y + 175))
