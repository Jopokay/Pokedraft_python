import pygame
import random
from typing import List

from pokemon import Pokemon, Nature
from utils import load_natures_data

WHITE      = (255, 255, 255)
BLACK      = (0,   0,   0  )
GRAY       = (140, 140, 140)
DARK_GRAY  = (60,  60,  60 )
CREAM      = (248, 248, 224)
GOLD       = (248, 208, 48 )
GREEN      = (72,  200, 88 )
RED        = (220, 56,  56 )

BG_DARK    = (22,  32,  62 )
BG_MED     = (30,  44,  88 )
HEADER_BG  = (16,  24,  50 )
CARD_BG    = (248, 248, 228)
CARD_BDR   = (60,  72,  44 )

SCREEN_WIDTH  = 1024
SCREEN_HEIGHT = 768
CARD_WIDTH    = 285
CARD_HEIGHT   = 220


def draw_poke_bg(screen):
    for y in range(SCREEN_HEIGHT):
        r_ratio = y / SCREEN_HEIGHT
        r = int(BG_DARK[0] + r_ratio * (BG_MED[0] - BG_DARK[0]))
        g = int(BG_DARK[1] + r_ratio * (BG_MED[1] - BG_DARK[1]))
        b = int(BG_DARK[2] + r_ratio * (BG_MED[2] - BG_DARK[2]))
        pygame.draw.line(screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))

    surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    for cx, cy in [(90,90),(SCREEN_WIDTH-90,90),(90,SCREEN_HEIGHT-90),(SCREEN_WIDTH-90,SCREEN_HEIGHT-90)]:
        pygame.draw.circle(surf, (255,255,255,18), (cx,cy), 74, 7)
        pygame.draw.line(surf, (255,255,255,18), (cx-74,cy), (cx+74,cy), 7)
        pygame.draw.circle(surf, (255,255,255,18), (cx,cy), 22, 7)
    screen.blit(surf, (0, 0))

    pygame.draw.rect(screen, HEADER_BG, (0, 0, SCREEN_WIDTH, 76))
    pygame.draw.rect(screen, GOLD, (0, 74, SCREEN_WIDTH, 4))


# Colori per ogni stat — abbinamento a tipo Pokémon per coerenza visiva
STAT_COLORS = {
    "hp":  (88,  200, 88 ),
    "atk": (240, 80,  56 ),
    "def": (240, 200, 48 ),
    "spa": (64,  120, 220),
    "spd": (88,  200, 208),
    "spe": (200, 80,  200),
}
STAT_LABELS = {"hp":"PS","atk":"Att","def":"Dif","spa":"SpA","spd":"SpD","spe":"Vel"}


class NaturePicker:
    def __init__(self, screen: pygame.Surface, team: List[Pokemon]):
        self.screen = screen
        self.font_title = pygame.font.Font(None, 50)
        self.font_name  = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        self.font_tiny  = pygame.font.Font(None, 20)

        self.team = team
        self.current_pokemon_index = 0
        self.natures_data = load_natures_data()
        self.selection_options: List[Nature] = []
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
                            self.select_nature(i)
                            break
            self.draw()
            if self.current_pokemon_index >= len(self.team):
                running = False

    def generate_options(self):
        options = random.sample(self.natures_data, min(3, len(self.natures_data)))
        self.selection_options = [Nature(**n) for n in options]
        self.selection_rects = []

    def select_nature(self, idx: int):
        if 0 <= idx < len(self.selection_options):
            self.team[self.current_pokemon_index].nature = self.selection_options[idx]
            self.current_pokemon_index += 1
            if self.current_pokemon_index < len(self.team):
                self.generate_options()

    def draw(self):
        draw_poke_bg(self.screen)

        title = self.font_title.render("Selezione Natura", True, WHITE)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 16))

        if self.current_pokemon_index >= len(self.team):
            return

        pokemon = self.team[self.current_pokemon_index]
        sub = self.font_name.render(f"Scegli la natura per  {pokemon.name}", True, GOLD)
        self.screen.blit(sub, (SCREEN_WIDTH//2 - sub.get_width()//2, 92))

        # Natura attuale
        if pokemon.nature:
            cur = self.font_small.render(
                f"Natura attuale: {pokemon.nature.name}", True, (180,220,180))
            self.screen.blit(cur, (SCREEN_WIDTH//2 - cur.get_width()//2, 126))
        
        pygame.draw.rect(self.screen, GOLD, (40, 158, SCREEN_WIDTH-80, 2))

        self.draw_nature_options()
        pygame.display.flip()

    def draw_nature_options(self):
        self.selection_rects = []
        total_w = 3 * CARD_WIDTH + 2 * 24
        start_x = (SCREEN_WIDTH - total_w) // 2

        for i, nature in enumerate(self.selection_options):
            x    = start_x + i * (CARD_WIDTH + 24)
            rect = pygame.Rect(x, 178, CARD_WIDTH, CARD_HEIGHT)
            self.selection_rects.append(rect)
            self._draw_nature_card(rect, nature)

    def _draw_nature_card(self, rect: pygame.Rect, nature: Nature):
        # Colore header basato su stat_up
        hdr_col = STAT_COLORS.get(nature.stat_up, (80,100,160)) if nature.stat_up else (80,100,140)

        pygame.draw.rect(self.screen, (10,15,35), rect.move(5,5), border_radius=14)
        pygame.draw.rect(self.screen, CARD_BG, rect, border_radius=14)

        stripe = pygame.Rect(rect.x, rect.y, rect.width, 44)
        pygame.draw.rect(self.screen, hdr_col, stripe, border_radius=14)
        pygame.draw.rect(self.screen, hdr_col,
                         pygame.Rect(rect.x, rect.y + 28, rect.width, 16))
        pygame.draw.rect(self.screen, CARD_BDR, rect, 3, border_radius=14)

        # Nome natura
        name_surf = self.font_name.render(nature.name, True, WHITE)
        self.screen.blit(name_surf, (rect.centerx - name_surf.get_width()//2, rect.y + 10))

        # Stat up / down con mini barre
        y = rect.y + 58
        all_stats = ["hp","atk","def","spa","spd","spe"]
        for stat in all_stats:
            lbl   = STAT_LABELS.get(stat, stat.upper())
            lbl_s = self.font_tiny.render(lbl, True, DARK_GRAY)
            self.screen.blit(lbl_s, (rect.x + 14, y))

            # Mini barra (base sempre = 50%)
            bar_x, bar_y, bar_w, bar_h = rect.x + 48, y + 3, rect.width - 62, 10
            pygame.draw.rect(self.screen, (200, 205, 185), (bar_x, bar_y, bar_w, bar_h), border_radius=4)

            # +10% o -10%
            if stat == nature.stat_up:
                fill_w = int(bar_w * 0.68)
                fill_col = (72, 200, 88)
                plus = self.font_tiny.render("+10%", True, (40, 160, 60))
                self.screen.blit(plus, (bar_x + bar_w + 4, y))
            elif stat == nature.stat_down:
                fill_w = int(bar_w * 0.36)
                fill_col = (220, 60, 60)
                plus = self.font_tiny.render("-10%", True, (180, 40, 40))
                self.screen.blit(plus, (bar_x + bar_w + 4, y))
            else:
                fill_w = int(bar_w * 0.50)
                fill_col = STAT_COLORS.get(stat, (120,140,180))

            if fill_w > 0:
                pygame.draw.rect(self.screen, fill_col,
                                 (bar_x, bar_y, fill_w, bar_h), border_radius=4)
            pygame.draw.rect(self.screen, (160,165,145),
                             (bar_x, bar_y, bar_w, bar_h), 1, border_radius=4)
            y += 22

        if not nature.stat_up and not nature.stat_down:
            neu = self.font_tiny.render("Nessun cambiamento", True, GRAY)
            self.screen.blit(neu, (rect.centerx - neu.get_width()//2, rect.y + 168))

        hint = self.font_tiny.render("▶ Clicca per scegliere", True, hdr_col)
        self.screen.blit(hint, (rect.centerx - hint.get_width()//2, rect.y + 200))
