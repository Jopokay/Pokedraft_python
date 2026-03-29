import pygame
import random
from typing import List, Optional, Tuple

from pokemon import Pokemon, Nature, Move
from utils import (
    load_pokemon_data, load_moves_data, load_learnsets_data, load_natures_data,
    get_type_color, calculate_base_stat_total, format_stat_name
)


# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
LIGHT_GRAY = (200, 200, 200)
BLUE = (100, 100, 255)
GREEN = (50, 200, 50)
RED = (200, 50, 50)
YELLOW = (255, 255, 0)

# UI Constants
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
SLOT_WIDTH = 140
SLOT_HEIGHT = 160
SLOT_SPACING = 20
CARD_WIDTH = 200
CARD_HEIGHT = 240


class DraftScreen:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.font_title = pygame.font.Font(None, 48)
        self.font_name = pygame.font.Font(None, 28)
        self.font_small = pygame.font.Font(None, 22)
        self.font_tiny = pygame.font.Font(None, 18)

        # Load data
        self.pokemon_data = load_pokemon_data()
        self.moves_data = load_moves_data()
        self.learnsets_data = load_learnsets_data()
        self.natures_data = load_natures_data()

        # Team state
        self.team: List[Optional[Pokemon]] = [None] * 6
        self.current_slot = 0

        # Selection popup state
        self.popup_active = False
        self.selection_options: List[dict] = []
        self.selection_rects: List[pygame.Rect] = []

        # Confirm button
        self.confirm_button = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 80, 200, 50)
        self.confirm_clicked = False

    def run(self) -> List[Pokemon]:
        """Run the draft screen and return the team."""
        running = True
        clock = pygame.time.Clock()

        while running:
            clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return []

                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = event.pos

                    if self.popup_active:
                        # Check selection clicks
                        for i, rect in enumerate(self.selection_rects):
                            if rect.collidepoint(pos):
                                self.select_pokemon(i)
                                break
                    else:
                        # Check slot clicks
                        for i in range(6):
                            slot_rect = self.get_slot_rect(i)
                            if slot_rect.collidepoint(pos) and self.team[i] is None:
                                self.open_selection(i)
                                break

                        # Check confirm button
                        if self.is_team_complete() and self.confirm_button.collidepoint(pos):
                            running = False
                            self.confirm_clicked = True

            self.draw()

        return self.build_team()

    def get_slot_rect(self, index: int) -> pygame.Rect:
        """Get the rectangle for a team slot."""
        total_width = 6 * SLOT_WIDTH + 5 * SLOT_SPACING
        start_x = (SCREEN_WIDTH - total_width) // 2
        x = start_x + index * (SLOT_WIDTH + SLOT_SPACING)
        y = 120
        return pygame.Rect(x, y, SLOT_WIDTH, SLOT_HEIGHT)

    def open_selection(self, slot_index: int):
        """Open the Pokemon selection popup for a slot."""
        self.current_slot = slot_index
        self.popup_active = True

        # Get Pokemon not already in team
        team_ids = [p.id for p in self.team if p is not None]
        available = [p for p in self.pokemon_data if p["id"] not in team_ids]

        # Random selection of 3
        self.selection_options = random.sample(available, min(3, len(available)))
        self.selection_rects = []

    def select_pokemon(self, option_index: int):
        """Select a Pokemon from the popup."""
        if 0 <= option_index < len(self.selection_options):
            p_data = self.selection_options[option_index]

            # Create Pokemon object
            move_ids = self.learnsets_data.get(str(p_data["id"]), [])
            moves = []
            for mid in move_ids:
                if mid in self.moves_data:
                    m = self.moves_data[mid]
                    moves.append(Move(**m))

            pokemon = Pokemon(
                id=p_data["id"],
                name=p_data["name"],
                types=p_data["types"],
                base_stats=p_data["base_stats"],
                moves=moves
            )

            self.team[self.current_slot] = pokemon
            self.popup_active = False

    def is_team_complete(self) -> bool:
        return all(p is not None for p in self.team)

    def build_team(self) -> List[Pokemon]:
        """Build the final team list."""
        return [p for p in self.team if p is not None]

    def draw(self):
        """Draw the draft screen."""
        self.screen.fill(BLACK)

        # Title
        title = self.font_title.render("Pokemon Draft", True, WHITE)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 30))

        # Draw slots
        for i in range(6):
            rect = self.get_slot_rect(i)
            self.draw_slot(rect, self.team[i], i == self.current_slot)

        # Draw confirm button if team complete
        if self.is_team_complete():
            pygame.draw.rect(self.screen, GREEN, self.confirm_button)
            text = self.font_name.render("Confirm Team", True, WHITE)
            self.screen.blit(text, (self.confirm_button.centerx - text.get_width() // 2,
                                     self.confirm_button.centery - text.get_height() // 2))

        # Draw popup if active
        if self.popup_active:
            self.draw_popup()

        pygame.display.flip()

    def draw_slot(self, rect: pygame.Rect, pokemon: Optional[Pokemon], highlighted: bool):
        """Draw a team slot."""
        color = BLUE if highlighted else DARK_GRAY
        if pokemon:
            color = GREEN

        pygame.draw.rect(self.screen, color, rect, 2)
        self.screen.fill(color, rect)

        if pokemon:
            # Draw placeholder for sprite
            sprite_rect = pygame.Rect(rect.x + 20, rect.y + 20, 100, 80)
            pygame.draw.rect(self.screen, get_type_color(pokemon.types[0]), sprite_rect)

            # Draw name
            name_text = self.font_small.render(pokemon.name, True, WHITE)
            self.screen.blit(name_text, (rect.centerx - name_text.get_width() // 2,
                                          rect.y + 110))

            # Draw types
            for j, ptype in enumerate(pokemon.types):
                type_color = get_type_color(ptype)
                type_rect = pygame.Rect(rect.x + 10 + j * 60, rect.y + 135, 55, 20)
                pygame.draw.rect(self.screen, type_color, type_rect)
                type_text = self.font_tiny.render(ptype[:3].upper(), True, BLACK)
                self.screen.blit(type_text, (type_rect.centerx - type_text.get_width() // 2,
                                               type_rect.centery - type_text.get_height() // 2))
        else:
            # Empty slot
            plus_text = self.font_title.render("+", True, GRAY)
            self.screen.blit(plus_text, (rect.centerx - plus_text.get_width() // 2,
                                          rect.centery - plus_text.get_height() // 2))

    def draw_popup(self):
        """Draw the Pokemon selection popup."""
        # Darken background
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        # Title
        title = self.font_name.render(f"Select Pokemon for Slot {self.current_slot + 1}", True, WHITE)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 100))

        # Draw options
        self.selection_rects = []
        start_x = (SCREEN_WIDTH - 3 * CARD_WIDTH) // 2
        for i, p_data in enumerate(self.selection_options):
            x = start_x + i * (CARD_WIDTH + 20)
            rect = pygame.Rect(x, 180, CARD_WIDTH, CARD_HEIGHT)
            self.selection_rects.append(rect)
            self.draw_pokemon_card(rect, p_data)

    def draw_pokemon_card(self, rect: pygame.Rect, p_data: dict):
        """Draw a Pokemon selection card."""
        pygame.draw.rect(self.screen, LIGHT_GRAY, rect)
        pygame.draw.rect(self.screen, WHITE, rect, 3)

        # Sprite placeholder
        sprite_rect = pygame.Rect(rect.x + 50, rect.y + 20, 100, 80)
        pygame.draw.rect(self.screen, get_type_color(p_data["types"][0]), sprite_rect)

        # Name
        name = self.font_name.render(p_data["name"], True, BLACK)
        self.screen.blit(name, (rect.centerx - name.get_width() // 2, rect.y + 110))

        # Types
        for j, ptype in enumerate(p_data["types"]):
            type_color = get_type_color(ptype)
            type_rect = pygame.Rect(rect.x + 20 + j * 90, rect.y + 140, 80, 25)
            pygame.draw.rect(self.screen, type_color, type_rect)
            type_text = self.font_small.render(ptype, True, BLACK)
            self.screen.blit(type_text, (type_rect.centerx - type_text.get_width() // 2,
                                          type_rect.centery - type_text.get_height() // 2))

        # BST
        bst = calculate_base_stat_total(p_data)
        bst_text = self.font_small.render(f"BST: {bst}", True, BLACK)
        self.screen.blit(bst_text, (rect.centerx - bst_text.get_width() // 2, rect.y + 180))

        # Hover hint
        hint = self.font_tiny.render("Click to select", True, DARK_GRAY)
        self.screen.blit(hint, (rect.centerx - hint.get_width() // 2, rect.y + 215))