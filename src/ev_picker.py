import pygame
from typing import List, Dict

from pokemon import Pokemon

WHITE      = (255, 255, 255)
BLACK      = (0,   0,   0  )
GRAY       = (140, 140, 140)
DARK_GRAY  = (60,  60,  60 )
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
CARD_HEIGHT   = 360

STAT_COLORS = {
    "hp":  (88,  200, 88 ),
    "atk": (240, 80,  56 ),
    "def": (240, 200, 48 ),
    "spa": (64,  120, 220),
    "spd": (88,  200, 208),
    "spe": (200, 80,  200),
}
STAT_LABELS = {"hp":"PS","atk":"Att","def":"Dif","spa":"SpA","spd":"SpD","spe":"Vel"}
STAT_ORDER  = ["hp","atk","def","spa","spd","spe"]

# Header colors per spread
SPREAD_COLORS = {
    "Offensivo":  (220, 80,  48 ),
    "Difensivo":  (64,  120, 220),
    "Bilanciato": (72,  200, 88 ),
}


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


def generate_offensive_spread(pokemon: Pokemon) -> Dict[str, int]:
    evs = {"hp":0,"atk":0,"def":0,"spa":0,"spd":0,"spe":0}
    if pokemon.base_stats["atk"] >= pokemon.base_stats["spa"]:
        evs["atk"] = 252
    else:
        evs["spa"] = 252
    evs["spe"] = 252
    evs["hp"]  = 6
    return evs


def generate_defensive_spread(pokemon: Pokemon) -> Dict[str, int]:
    return {"hp":252,"def":128,"spd":128,"atk":0,"spa":0,"spe":0}


def generate_balanced_spread(pokemon: Pokemon) -> Dict[str, int]:
    return {"hp":85,"atk":85,"def":85,"spa":85,"spd":85,"spe":85}


class EVPicker:
    def __init__(self, screen: pygame.Surface, team: List[Pokemon]):
        self.screen = screen
        self.font_title = pygame.font.Font(None, 50)
        self.font_name  = pygame.font.Font(None, 30)
        self.font_small = pygame.font.Font(None, 23)
        self.font_tiny  = pygame.font.Font(None, 19)

        self.team = team
        self.current_pokemon_index = 0
        self.spread_options: List[Dict[str, int]] = []
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
                            self.select_spread(i)
                            break
            self.draw()
            if self.current_pokemon_index >= len(self.team):
                running = False

    def generate_options(self):
        pokemon = self.team[self.current_pokemon_index]
        self.spread_options = [
            generate_offensive_spread(pokemon),
            generate_defensive_spread(pokemon),
            generate_balanced_spread(pokemon),
        ]
        self.selection_rects = []

    def select_spread(self, idx: int):
        if 0 <= idx < len(self.spread_options):
            pokemon = self.team[self.current_pokemon_index]
            pokemon.evs = self.spread_options[idx]
            pokemon.current_hp = pokemon.get_max_hp()
            self.current_pokemon_index += 1
            if self.current_pokemon_index < len(self.team):
                self.generate_options()

    def draw(self):
        draw_poke_bg(self.screen)

        title = self.font_title.render("Selezione EV", True, WHITE)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 16))

        if self.current_pokemon_index >= len(self.team):
            return

        pokemon = self.team[self.current_pokemon_index]
        sub = self.font_name.render(f"Scegli la distribuzione EV per  {pokemon.name}", True, GOLD)
        self.screen.blit(sub, (SCREEN_WIDTH//2 - sub.get_width()//2, 92))

        pygame.draw.rect(self.screen, GOLD, (40, 126, SCREEN_WIDTH-80, 2))

        self.draw_ev_options()
        pygame.display.flip()

    def draw_ev_options(self):
        self.selection_rects = []
        spread_names = ["Offensivo", "Difensivo", "Bilanciato"]
        total_w = 3 * CARD_WIDTH + 2 * 24
        start_x = (SCREEN_WIDTH - total_w) // 2

        for i, evs in enumerate(self.spread_options):
            x    = start_x + i * (CARD_WIDTH + 24)
            rect = pygame.Rect(x, 144, CARD_WIDTH, CARD_HEIGHT)
            self.selection_rects.append(rect)
            self._draw_ev_card(rect, evs, spread_names[i])

    def _draw_ev_card(self, rect: pygame.Rect, evs: Dict[str, int], spread_name: str):
        hdr_col = SPREAD_COLORS.get(spread_name, (80, 100, 160))

        pygame.draw.rect(self.screen, (10,15,35), rect.move(5,5), border_radius=14)
        pygame.draw.rect(self.screen, CARD_BG, rect, border_radius=14)

        stripe = pygame.Rect(rect.x, rect.y, rect.width, 44)
        pygame.draw.rect(self.screen, hdr_col, stripe, border_radius=14)
        pygame.draw.rect(self.screen, hdr_col,
                         pygame.Rect(rect.x, rect.y + 28, rect.width, 16))
        pygame.draw.rect(self.screen, CARD_BDR, rect, 3, border_radius=14)

        # Nome spread
        name_surf = self.font_name.render(spread_name, True, WHITE)
        self.screen.blit(name_surf, (rect.centerx - name_surf.get_width()//2, rect.y + 10))

        # Totale EV
        total = sum(evs.values())
        tcol  = (72,200,88) if total <= 510 else (220,56,56)
        tot_s = self.font_tiny.render(f"EV totali: {total}/510", True, tcol)
        self.screen.blit(tot_s, (rect.centerx - tot_s.get_width()//2, rect.y + 50))

        # Stats con barre
        pokemon = self.team[self.current_pokemon_index]
        orig_evs = pokemon.evs.copy()
        pokemon.evs = evs.copy()

        y = rect.y + 72
        for stat in STAT_ORDER:
            ev       = evs[stat]
            eff      = pokemon.get_effective_stat(stat)
            lbl      = STAT_LABELS.get(stat, stat.upper())
            stat_col = STAT_COLORS.get(stat, GRAY)

            # Label stat
            lbl_s = self.font_tiny.render(lbl, True, DARK_GRAY)
            self.screen.blit(lbl_s, (rect.x + 12, y + 2))

            # Barra EV (max 252)
            bar_x = rect.x + 44
            bar_y = y + 4
            bar_w = rect.width - 100
            bar_h = 10
            pct   = ev / 252 if ev > 0 else 0
            pygame.draw.rect(self.screen, (200, 205, 185),
                             (bar_x, bar_y, bar_w, bar_h), border_radius=4)
            if pct > 0:
                pygame.draw.rect(self.screen, stat_col,
                                 (bar_x, bar_y, int(bar_w * pct), bar_h), border_radius=4)
            pygame.draw.rect(self.screen, (160,165,145),
                             (bar_x, bar_y, bar_w, bar_h), 1, border_radius=4)

            # EV value
            ev_s = self.font_tiny.render(str(ev), True, DARK_GRAY)
            self.screen.blit(ev_s, (bar_x + bar_w + 4, y + 2))

            # Stat effettiva
            eff_s = self.font_small.render(str(eff), True, BLACK)
            self.screen.blit(eff_s, (rect.right - eff_s.get_width() - 10, y))

            y += 42

        pokemon.evs = orig_evs

        hint = self.font_tiny.render("▶ Clicca per scegliere", True, hdr_col)
        self.screen.blit(hint, (rect.centerx - hint.get_width()//2, rect.y + 338))
