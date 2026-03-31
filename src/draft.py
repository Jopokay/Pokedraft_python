import pygame
import random
from typing import List, Optional, Tuple

from pokemon import Pokemon, Nature, Move
from utils import (
    load_pokemon_data, load_moves_data, load_learnsets_data, load_natures_data,
    get_type_color, calculate_base_stat_total, format_stat_name
)

# Colori UI (Rinnovati per un look più "Pokémon")
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
LIGHT_GRAY = (220, 225, 230)
BLUE_BG = (180, 210, 240)    # Sfondo azzurro stile Box PC
UI_BORDER = (45, 55, 65)
GREEN_BTN = (70, 200, 110)
YELLOW_SEL = (255, 220, 50)

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
        # Font leggermente ingranditi/riorganizzati per leggibilità
        self.font_title = pygame.font.Font(None, 52)
        self.font_name = pygame.font.Font(None, 30)
        self.font_small = pygame.font.Font(None, 24)
        self.font_tiny = pygame.font.Font(None, 20)

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
        self.confirm_button = pygame.Rect(SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT - 90, 240, 55)
        self.confirm_clicked = False

        # Sprite cache
        self.sprite_cache: dict = {}

    def load_sprite(self, pokemon_id: int, size: Tuple[int, int] = (96, 96)) -> Optional[pygame.Surface]:
        """Carica lo sprite frontale dal percorso locale assets/sprites/."""
        cache_key = f"{pokemon_id}_front_{size[0]}x{size[1]}"
        if cache_key in self.sprite_cache:
            return self.sprite_cache[cache_key]
        try:
            path = f"assets/sprites/{pokemon_id:03d}.png"
            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.scale(img, size)
            self.sprite_cache[cache_key] = img
        except Exception as e:
            print(f"Errore sprite ID {pokemon_id}: {e}")
            self.sprite_cache[cache_key] = None
        return self.sprite_cache[cache_key]

    def _draw_text_with_shadow(self, text: str, font: pygame.font.Font, color: Tuple, x: int, y: int, shadow_color=DARK_GRAY):
        """Disegna il testo con una classica ombra in stile Pokémon."""
        shadow_surf = font.render(text, True, shadow_color)
        text_surf = font.render(text, True, color)
        self.screen.blit(shadow_surf, (x + 2, y + 2))
        self.screen.blit(text_surf, (x, y))

    def run(self) -> List[Pokemon]:
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
                        for i, rect in enumerate(self.selection_rects):
                            if rect.collidepoint(pos):
                                self.select_pokemon(i)
                                break
                    else:
                        for i in range(6):
                            slot_rect = self.get_slot_rect(i)
                            if slot_rect.collidepoint(pos) and self.team[i] is None:
                                self.open_selection(i)
                                break

                        if self.is_team_complete() and self.confirm_button.collidepoint(pos):
                            running = False
                            self.confirm_clicked = True

            self.draw()

        return self.build_team()

    def get_slot_rect(self, index: int) -> pygame.Rect:
        total_width = 6 * SLOT_WIDTH + 5 * SLOT_SPACING
        start_x = (SCREEN_WIDTH - total_width) // 2
        x = start_x + index * (SLOT_WIDTH + SLOT_SPACING)
        y = 150
        return pygame.Rect(x, y, SLOT_WIDTH, SLOT_HEIGHT)

    def open_selection(self, slot_index: int):
        self.current_slot = slot_index
        self.popup_active = True
        team_ids = [p.id for p in self.team if p is not None]
        available = [p for p in self.pokemon_data if p["id"] not in team_ids]
        self.selection_options = random.sample(available, min(3, len(available)))
        self.selection_rects = []

    def select_pokemon(self, option_index: int):
        if 0 <= option_index < len(self.selection_options):
            p_data = self.selection_options[option_index]
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
        return [p for p in self.team if p is not None]

    def draw(self):
        # Sfondo morbido per il draft
        self.screen.fill(BLUE_BG)
        
        # Effetto "Strisce" sullo sfondo (opzionale, aggiunge profondità)
        for i in range(0, SCREEN_HEIGHT, 40):
            pygame.draw.line(self.screen, (190, 220, 250), (0, i), (SCREEN_WIDTH, i), 2)

        # Title
        title_text = "Seleziona la tua Squadra"
        title_w = self.font_title.size(title_text)[0]
        self._draw_text_with_shadow(title_text, self.font_title, WHITE, SCREEN_WIDTH // 2 - title_w // 2, 40)

        # Draw slots
        for i in range(6):
            rect = self.get_slot_rect(i)
            self.draw_slot(rect, self.team[i], i == self.current_slot)

        # Draw confirm button
        if self.is_team_complete():
            # Ombra pulsante
            shadow_rect = self.confirm_button.copy()
            shadow_rect.y += 4
            pygame.draw.rect(self.screen, DARK_GRAY, shadow_rect, border_radius=12)
            # Pulsante vero
            pygame.draw.rect(self.screen, GREEN_BTN, self.confirm_button, border_radius=12)
            pygame.draw.rect(self.screen, WHITE, self.confirm_button, 3, border_radius=12)
            
            text_w = self.font_name.size("Conferma Team")[0]
            text_h = self.font_name.size("Conferma Team")[1]
            self._draw_text_with_shadow("Conferma Team", self.font_name, WHITE, 
                                        self.confirm_button.centerx - text_w // 2, 
                                        self.confirm_button.centery - text_h // 2)

        if self.popup_active:
            self.draw_popup()

        pygame.display.flip()

    def draw_slot(self, rect: pygame.Rect, pokemon: Optional[Pokemon], highlighted: bool):
        # Ombra della card
        shadow_rect = rect.copy()
        shadow_rect.x += 4
        shadow_rect.y += 4
        pygame.draw.rect(self.screen, (150, 180, 210), shadow_rect, border_radius=15)

        # Colore card
        bg_color = WHITE
        border_color = YELLOW_SEL if highlighted else UI_BORDER
        if pokemon:
            bg_color = (245, 255, 245)

        pygame.draw.rect(self.screen, bg_color, rect, border_radius=15)
        pygame.draw.rect(self.screen, border_color, rect, 4 if highlighted else 2, border_radius=15)

        if pokemon:
            # Sprite frontale nello slot del team
            sprite = self.load_sprite(pokemon.id, size=(100, 80))
            sprite_rect = pygame.Rect(rect.x + 20, rect.y + 10, 100, 80)
            if sprite:
                self.screen.blit(sprite, sprite_rect)
            else:
                # Fallback: rettangolo colorato se lo sprite non c'è
                pygame.draw.rect(self.screen, get_type_color(pokemon.types[0]), sprite_rect, border_radius=8)

            name_w = self.font_small.size(pokemon.name)[0]
            self._draw_text_with_shadow(pokemon.name, self.font_small, BLACK, 
                                        rect.centerx - name_w // 2, rect.y + 105, shadow_color=LIGHT_GRAY)

            # Tipi con pillole smussate
            for j, ptype in enumerate(pokemon.types):
                type_color = get_type_color(ptype)
                type_rect = pygame.Rect(rect.x + 15 + j * 55, rect.y + 130, 50, 20)
                pygame.draw.rect(self.screen, type_color, type_rect, border_radius=10)
                pygame.draw.rect(self.screen, BLACK, type_rect, 1, border_radius=10)
                
                type_str = ptype[:3].upper()
                tw, th = self.font_tiny.size(type_str)
                # Testo senza ombra per maggiore pulizia qui
                type_text = self.font_tiny.render(type_str, True, WHITE) 
                self.screen.blit(type_text, (type_rect.centerx - tw // 2, type_rect.centery - th // 2))
        else:
            plus_text = self.font_title.render("+", True, LIGHT_GRAY)
            self.screen.blit(plus_text, (rect.centerx - plus_text.get_width() // 2,
                                          rect.centery - plus_text.get_height() // 2))

    def draw_popup(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        # Pannello del Pokédex per la selezione
        panel_rect = pygame.Rect(50, 80, SCREEN_WIDTH - 100, SCREEN_HEIGHT - 160)
        pygame.draw.rect(self.screen, (220, 40, 40), panel_rect, border_radius=20) # Bordo Rosso Pokedex
        pygame.draw.rect(self.screen, WHITE, panel_rect.inflate(-16, -16), border_radius=15)

        title_str = f"Scegli un Pokémon per lo Slot {self.current_slot + 1}"
        title_w = self.font_name.size(title_str)[0]
        self._draw_text_with_shadow(title_str, self.font_name, WHITE, SCREEN_WIDTH // 2 - title_w // 2, 95)

        self.selection_rects = []
        start_x = (SCREEN_WIDTH - 3 * CARD_WIDTH) // 2
        for i, p_data in enumerate(self.selection_options):
            x = start_x + i * (CARD_WIDTH + 20)
            rect = pygame.Rect(x, 220, CARD_WIDTH, CARD_HEIGHT)
            self.selection_rects.append(rect)
            self.draw_pokemon_card(rect, p_data)

    def draw_pokemon_card(self, rect: pygame.Rect, p_data: dict):
        # Effetto "Hover/Card"
        shadow_rect = rect.copy()
        shadow_rect.x += 5
        shadow_rect.y += 5
        pygame.draw.rect(self.screen, GRAY, shadow_rect, border_radius=12)

        pygame.draw.rect(self.screen, LIGHT_GRAY, rect, border_radius=12)
        pygame.draw.rect(self.screen, UI_BORDER, rect, 3, border_radius=12)

        # Sprite frontale nella card del popup
        sprite = self.load_sprite(p_data["id"], size=(120, 90))
        sprite_rect = pygame.Rect(rect.x + 40, rect.y + 15, 120, 90)
        if sprite:
            self.screen.blit(sprite, sprite_rect)
        else:
            # Fallback: rettangolo colorato se lo sprite non c'è
            pygame.draw.rect(self.screen, get_type_color(p_data["types"][0]), sprite_rect, border_radius=8)
            pygame.draw.rect(self.screen, WHITE, sprite_rect, 2, border_radius=8)

        name_w = self.font_name.size(p_data["name"])[0]
        self._draw_text_with_shadow(p_data["name"], self.font_name, BLACK, rect.centerx - name_w // 2, rect.y + 120, shadow_color=WHITE)

        for j, ptype in enumerate(p_data["types"]):
            type_color = get_type_color(ptype)
            type_rect = pygame.Rect(rect.x + 20 + j * 85, rect.y + 155, 75, 24)
            pygame.draw.rect(self.screen, type_color, type_rect, border_radius=12)
            pygame.draw.rect(self.screen, UI_BORDER, type_rect, 1, border_radius=12)
            
            tw, th = self.font_small.size(ptype)
            tt = self.font_small.render(ptype, True, WHITE)
            self.screen.blit(tt, (type_rect.centerx - tw // 2, type_rect.centery - th // 2))

        bst = calculate_base_stat_total(p_data)
        bst_str = f"BST: {bst}"
        bw = self.font_small.size(bst_str)[0]
        self._draw_text_with_shadow(bst_str, self.font_small, UI_BORDER, rect.centerx - bw // 2, rect.y + 195, shadow_color=WHITE)

        hint = self.font_tiny.render("Clicca per scegliere", True, DARK_GRAY)
        self.screen.blit(hint, (rect.centerx - hint.get_width() // 2, rect.y + 220))
