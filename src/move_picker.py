import pygame
import random
from typing import List

from pokemon import Pokemon, Move
from utils import get_type_color, format_stat_name


# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
LIGHT_GRAY = (200, 200, 200)
BLUE = (100, 100, 255)
GREEN = (50, 200, 50)
YELLOW = (255, 255, 0)

# UI Constants
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
CARD_WIDTH = 220
CARD_HEIGHT = 200


class MovePicker:
    def __init__(self, screen: pygame.Surface, team: List[Pokemon]):
        self.screen = screen
        self.font_title = pygame.font.Font(None, 48)
        self.font_name = pygame.font.Font(None, 28)
        self.font_small = pygame.font.Font(None, 22)
        self.font_tiny = pygame.font.Font(None, 18)

        self.team = team
        self.current_pokemon_index = 0
        self.current_move_index = 0

        # Selection state
        self.selection_options: List[Move] = []
        self.selection_rects: List[pygame.Rect] = []

    def run(self):
        """Run the move picker for all Pokemon."""
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
                            self.select_move(i)
                            break

            self.draw()

            # Check if done
            if self.current_pokemon_index >= len(self.team):
                running = False

    def get_remaining_moves(self) -> List[int]:
        """Get move IDs not yet selected for current Pokemon."""
        pokemon = self.team[self.current_pokemon_index]
        selected_ids = [m.id for m in pokemon.moves]
        all_move_ids = [m.id for m in pokemon.moves]
        return [mid for mid in all_move_ids if mid not in selected_ids]

    def select_move(self, option_index: int):
        """Select a move from the options."""
        if 0 <= option_index < len(self.selection_options):
            move = self.selection_options[option_index]
            self.team[self.current_pokemon_index].moves.append(move)

            self.current_move_index += 1

            # Check if Pokemon has 4 moves
            if len(self.team[self.current_pokemon_index].moves) >= 4:
                self.current_pokemon_index += 1
                self.current_move_index = 0

            # Generate new options for next slot
            if self.current_pokemon_index < len(self.team):
                self.generate_options()

    def generate_options(self):
        """Generate 3 random move options for current slot."""
        pokemon = self.team[self.current_pokemon_index]
        selected_ids = [m.id for m in pokemon.moves]
        available = [m for m in pokemon.moves if m.id not in selected_ids]

        if len(available) >= 3:
            self.selection_options = random.sample(available, 3)
        else:
            # Fill remaining with random moves from learnset
            self.selection_options = available[:]
            remaining = [m for m in pokemon.moves if m not in self.selection_options]
            needed = 3 - len(self.selection_options)
            if remaining and needed > 0:
                self.selection_options.extend(random.sample(remaining, min(needed, len(remaining))))

        self.selection_rects = []

    def draw(self):
        """Draw the move picker screen."""
        self.screen.fill(BLACK)

        # Title
        title = self.font_title.render("Select Moves", True, WHITE)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 30))

        if self.current_pokemon_index >= len(self.team):
            return

        pokemon = self.team[self.current_pokemon_index]

        # Pokemon info
        name = self.font_name.render(f"{pokemon.name} - Move {self.current_move_index + 1}/4", True, WHITE)
        self.screen.blit(name, (SCREEN_WIDTH // 2 - name.get_width() // 2, 100))

        # Current moves
        moves_label = self.font_small.render("Current Moves:", True, GRAY)
        self.screen.blit(moves_label, (50, 160))

        for i in range(4):
            move = pokemon.moves[i] if i < len(pokemon.moves) else None
            slot_rect = pygame.Rect(50 + i * 180, 190, 160, 50)

            color = GREEN if move else DARK_GRAY
            pygame.draw.rect(self.screen, color, slot_rect, 2)
            self.screen.fill(color, slot_rect)

            if move:
                move_name = self.font_small.render(move.name[:12], True, WHITE)
                self.screen.blit(move_name, (slot_rect.centerx - move_name.get_width() // 2,
                                              slot_rect.centery - move_name.get_height() // 2))
            else:
                plus_text = self.font_name.render("+", True, GRAY)
                self.screen.blit(plus_text, (slot_rect.centerx - plus_text.get_width() // 2,
                                              slot_rect.centery - plus_text.get_height() // 2))

        # Move options
        options_label = self.font_small.render("Select a move:", True, WHITE)
        self.screen.blit(options_label, (SCREEN_WIDTH // 2 - options_label.get_width() // 2, 280))

        # Generate options if needed
        if not self.selection_options and self.current_pokemon_index < len(self.team):
            self.generate_options()

        self.draw_move_options()

        pygame.display.flip()

    def draw_move_options(self):
        """Draw move selection options."""
        start_x = (SCREEN_WIDTH - 3 * CARD_WIDTH) // 2

        for i, move in enumerate(self.selection_options):
            x = start_x + i * (CARD_WIDTH + 20)
            rect = pygame.Rect(x, 330, CARD_WIDTH, CARD_HEIGHT)
            self.selection_rects.append(rect)
            self.draw_move_card(rect, move)

    def draw_move_card(self, rect: pygame.Rect, move: Move):
        """Draw a move selection card."""
        pygame.draw.rect(self.screen, LIGHT_GRAY, rect)
        pygame.draw.rect(self.screen, WHITE, rect, 3)

        # Type badge
        type_color = get_type_color(move.type)
        type_rect = pygame.Rect(rect.x + 10, rect.y + 10, 60, 25)
        pygame.draw.rect(self.screen, type_color, type_rect)
        type_text = self.font_small.render(move.type, True, BLACK)
        self.screen.blit(type_text, (type_rect.centerx - type_text.get_width() // 2,
                                       type_rect.centery - type_text.get_height() // 2))

        # Category badge
        cat_color = GREEN if move.category == "Physical" else BLUE if move.category == "Special" else GRAY
        cat_rect = pygame.Rect(rect.x + 80, rect.y + 10, 80, 25)
        pygame.draw.rect(self.screen, cat_color, cat_rect)
        cat_text = self.font_small.render(move.category[:4], True, WHITE)
        self.screen.blit(cat_text, (cat_rect.centerx - cat_text.get_width() // 2,
                                      cat_rect.centery - cat_text.get_height() // 2))

        # Move name
        name = self.font_name.render(move.name, True, BLACK)
        self.screen.blit(name, (rect.centerx - name.get_width() // 2, rect.y + 50))

        # Stats
        y_offset = 85

        if move.power > 0:
            power_text = self.font_small.render(f"Power: {move.power}", True, BLACK)
            self.screen.blit(power_text, (rect.x + 20, rect.y + y_offset))
        else:
            power_text = self.font_small.render("Power: --", True, GRAY)
            self.screen.blit(power_text, (rect.x + 20, rect.y + y_offset))

        y_offset += 25
        acc_text = self.font_small.render(f"Accuracy: {move.accuracy}%", True, BLACK)
        self.screen.blit(acc_text, (rect.x + 20, rect.y + y_offset))

        y_offset += 25
        pp_text = self.font_small.render(f"PP: {move.pp}/{move.max_pp}", True, BLACK)
        self.screen.blit(pp_text, (rect.x + 20, rect.y + y_offset))

        # Effect hint
        if move.effect:
            effect_text = self.font_tiny.render(f"Effect: {move.effect}", True, DARK_GRAY)
            self.screen.blit(effect_text, (rect.x + 20, rect.y + 155))

        # Click hint
        hint = self.font_tiny.render("Click to select", True, BLUE)
        self.screen.blit(hint, (rect.centerx - hint.get_width() // 2, rect.y + 175))