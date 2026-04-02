import pygame
import random
from typing import List, Dict

from pokemon import Pokemon, Move
from utils import get_type_color, format_stat_name

# ── Palette condivisa stile Pokémon ──────────────────────────────────────────
WHITE      = (255, 255, 255)
BLACK      = (0,   0,   0  )
GRAY       = (140, 140, 140)
DARK_GRAY  = (60,  60,  60 )
CREAM      = (248, 248, 224)
GOLD       = (248, 208, 48 )
GREEN      = (72,  200, 88 )
RED        = (220, 56,  56 )
BLUE_PILL  = (64,  120, 200)

# Sfondo navy Pokémon
BG_DARK    = (22,  32,  62 )   # navy scuro
BG_MED     = (30,  44,  88 )   # navy medio
HEADER_BG  = (16,  24,  50 )   # header strip
CARD_BG    = (248, 248, 228)   # card crema
CARD_BDR   = (60,  72,  44 )   # bordo oliva

SCREEN_WIDTH  = 1024
SCREEN_HEIGHT = 768
CARD_WIDTH    = 220
CARD_HEIGHT   = 210


def draw_poke_bg(screen: pygame.Surface):
    """Sfondo navy stile Pokémon con pokéball decorative."""
    # Gradiente verticale navy
    for y in range(SCREEN_HEIGHT):
        r_ratio = y / SCREEN_HEIGHT
        r = int(BG_DARK[0] + r_ratio * (BG_MED[0] - BG_DARK[0]))
        g = int(BG_DARK[1] + r_ratio * (BG_MED[1] - BG_DARK[1]))
        b = int(BG_DARK[2] + r_ratio * (BG_MED[2] - BG_DARK[2]))
        pygame.draw.line(screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))

    # Pokéball silhouette decorativa (4 angoli)
    surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    for cx, cy in [(90,90),(SCREEN_WIDTH-90,90),(90,SCREEN_HEIGHT-90),(SCREEN_WIDTH-90,SCREEN_HEIGHT-90)]:
        pygame.draw.circle(surf, (255, 255, 255, 18), (cx, cy), 74, 7)
        pygame.draw.line(surf, (255, 255, 255, 18), (cx-74, cy), (cx+74, cy), 7)
        pygame.draw.circle(surf, (255, 255, 255, 18), (cx, cy), 22, 7)
    screen.blit(surf, (0, 0))

    # Header strip
    pygame.draw.rect(screen, HEADER_BG, (0, 0, SCREEN_WIDTH, 76))
    pygame.draw.rect(screen, GOLD, (0, 74, SCREEN_WIDTH, 4))


class MovePicker:
    def __init__(self, screen: pygame.Surface, team: List[Pokemon]):
        self.screen = screen
        self.font_title = pygame.font.Font(None, 50)
        self.font_name  = pygame.font.Font(None, 30)
        self.font_small = pygame.font.Font(None, 23)
        self.font_tiny  = pygame.font.Font(None, 19)

        self.team = team
        self.current_pokemon_index = 0
        self.current_move_index    = 0

        self.available_pool: Dict[int, List[Move]] = {}
        for i, pokemon in enumerate(team):
            self.available_pool[i] = list(pokemon.moves)
            pokemon.moves = []

        self.selection_options: List[Move] = []
        self.selection_rects: List[pygame.Rect] = []
        self.generate_options()

    def run(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for i, rect in enumerate(self.selection_rects):
                        if rect.collidepoint(event.pos):
                            self.select_move(i)
                            break
            self.draw()
            if self.current_pokemon_index >= len(self.team):
                running = False

    def generate_options(self):
        if self.current_pokemon_index >= len(self.team):
            return
        pokemon = self.team[self.current_pokemon_index]
        pool = self.available_pool[self.current_pokemon_index]
        selected_ids = {m.id for m in pokemon.moves}
        available = [m for m in pool if m.id not in selected_ids]
        if len(available) >= 3:
            self.selection_options = random.sample(available, 3)
        elif available:
            self.selection_options = available[:]
        else:
            self.selection_options = random.sample(pool, min(3, len(pool)))
        self.selection_rects = []

    def select_move(self, idx: int):
        if 0 <= idx < len(self.selection_options):
            move = self.selection_options[idx]
            self.team[self.current_pokemon_index].moves.append(move)
            self.current_move_index += 1
            if len(self.team[self.current_pokemon_index].moves) >= 4:
                self.current_pokemon_index += 1
                self.current_move_index = 0
            if self.current_pokemon_index < len(self.team):
                self.generate_options()

    def draw(self):
        draw_poke_bg(self.screen)

        # Titolo nell'header
        title = self.font_title.render("Selezione Mosse", True, WHITE)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 16))

        if self.current_pokemon_index >= len(self.team):
            return

        pokemon = self.team[self.current_pokemon_index]

        # Sottotitolo
        sub = self.font_name.render(
            f"{pokemon.name}  —  Mossa {self.current_move_index + 1} / 4", True, GOLD)
        self.screen.blit(sub, (SCREEN_WIDTH//2 - sub.get_width()//2, 92))

        # Slot mosse già scelte
        slot_y = 124
        total_w = 4 * 218 + 3 * 8
        start_x = (SCREEN_WIDTH - total_w) // 2
        lbl = self.font_tiny.render("Mosse selezionate:", True, (180, 190, 220))
        self.screen.blit(lbl, (start_x, slot_y))

        for i in range(4):
            move = pokemon.moves[i] if i < len(pokemon.moves) else None
            sx   = start_x + i * 226
            sy   = slot_y + 22
            slot = pygame.Rect(sx, sy, 218, 44)

            # Sfondo slot
            col = get_type_color(move.type) if move else (50, 62, 100)
            pygame.draw.rect(self.screen, (30, 30, 30), slot.move(3, 3), border_radius=8)
            pygame.draw.rect(self.screen, col, slot, border_radius=8)
            pygame.draw.rect(self.screen, WHITE if move else GRAY, slot, 2, border_radius=8)

            if move:
                mn = self.font_small.render(move.name[:14], True, WHITE)
                self.screen.blit(mn, (slot.centerx - mn.get_width()//2,
                                      slot.centery - mn.get_height()//2))
            else:
                plus = self.font_name.render("+", True, GRAY)
                self.screen.blit(plus, (slot.centerx - plus.get_width()//2,
                                        slot.centery - plus.get_height()//2))

        # Divider
        pygame.draw.rect(self.screen, GOLD, (40, 196, SCREEN_WIDTH - 80, 2))

        # Label scegli
        sel_lbl = self.font_small.render("Scegli una mossa:", True, (200, 210, 240))
        self.screen.blit(sel_lbl, (SCREEN_WIDTH//2 - sel_lbl.get_width()//2, 206))

        self.draw_move_options()
        pygame.display.flip()

    def draw_move_options(self):
        self.selection_rects = []
        total_w = 3 * CARD_WIDTH + 2 * 24
        start_x = (SCREEN_WIDTH - total_w) // 2

        for i, move in enumerate(self.selection_options):
            x    = start_x + i * (CARD_WIDTH + 24)
            rect = pygame.Rect(x, 230, CARD_WIDTH, CARD_HEIGHT)
            self.selection_rects.append(rect)
            self._draw_move_card(rect, move)

    def _draw_move_card(self, rect: pygame.Rect, move: Move):
        type_col = get_type_color(move.type)

        # Ombra
        pygame.draw.rect(self.screen, (10, 15, 35),
                         rect.move(5, 5), border_radius=14)
        # Card background
        pygame.draw.rect(self.screen, CARD_BG, rect, border_radius=14)
        # Striscia superiore colorata per tipo
        stripe = pygame.Rect(rect.x, rect.y, rect.width, 36)
        pygame.draw.rect(self.screen, type_col, stripe, border_radius=14)
        # Ricopri angoli inferiori della striscia per non arrotondarli
        pygame.draw.rect(self.screen, type_col,
                         pygame.Rect(rect.x, rect.y + 22, rect.width, 14))
        # Bordo
        pygame.draw.rect(self.screen, CARD_BDR, rect, 3, border_radius=14)

        # Tipo + Categoria
        type_txt = self.font_small.render(move.type.upper(), True, WHITE)
        self.screen.blit(type_txt, (rect.x + 10, rect.y + 10))

        CAT_COLORS = {"Physical":(220,80,40),"Special":(60,120,220),"Status":(120,100,160)}
        cat_col = CAT_COLORS.get(move.category, GRAY)
        cat_pill = pygame.Rect(rect.right - 72, rect.y + 8, 64, 20)
        pygame.draw.rect(self.screen, cat_col, cat_pill, border_radius=8)
        cat_txt = self.font_tiny.render(move.category[:4].upper(), True, WHITE)
        self.screen.blit(cat_txt, (cat_pill.centerx - cat_txt.get_width()//2,
                                   cat_pill.centery - cat_txt.get_height()//2))

        # Nome mossa
        name_surf = self.font_name.render(move.name[:16], True, BLACK)
        self.screen.blit(name_surf, (rect.centerx - name_surf.get_width()//2, rect.y + 46))

        # Stats
        y = rect.y + 80
        for label, value in [
            ("Potenza", f"{move.power}" if move.power > 0 else "—"),
            ("Precisione", f"{move.accuracy}%"),
            ("PP", f"{move.pp}"),
        ]:
            lbl_s = self.font_tiny.render(label, True, DARK_GRAY)
            val_s = self.font_small.render(value, True, BLACK)
            self.screen.blit(lbl_s, (rect.x + 14, y))
            self.screen.blit(val_s, (rect.right - val_s.get_width() - 14, y))
            pygame.draw.line(self.screen, (210, 210, 190),
                             (rect.x+10, y+18), (rect.right-10, y+18), 1)
            y += 28

        # Effetto
        if move.effect:
            eff = self.font_tiny.render(move.effect[:30], True, GRAY)
            self.screen.blit(eff, (rect.x + 10, rect.y + 168))

        # Hint
        hint = self.font_tiny.render("▶ Clicca per scegliere", True, type_col)
        self.screen.blit(hint, (rect.centerx - hint.get_width()//2, rect.y + 192))
