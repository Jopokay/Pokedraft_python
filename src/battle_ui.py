import pygame
from typing import List, Optional

from pokemon import Pokemon
from battle import BattleEngine
from utils import get_type_color


WHITE      = (255, 255, 255)
BLACK      = (0,   0,   0  )
GRAY       = (128, 128, 128)
DARK_GRAY  = (64,  64,  64 )
LIGHT_GRAY = (200, 200, 200)
BLUE       = (100, 100, 255)
GREEN      = (50,  200, 50 )
RED        = (200, 50,  50 )
YELLOW     = (255, 255, 0  )
BG_COLOR   = (20,  24,  40 )   # dark navy background

SCREEN_WIDTH  = 1024
SCREEN_HEIGHT = 768


class BattleUI:
    def __init__(self, screen: pygame.Surface,
                 player_team: List[Pokemon], ai_team: List[Pokemon]):
        self.screen = screen
        self.font_title = pygame.font.Font(None, 48)
        self.font_name  = pygame.font.Font(None, 28)
        self.font_small = pygame.font.Font(None, 22)
        self.font_tiny  = pygame.font.Font(None, 18)

        self.engine = BattleEngine(player_team, ai_team)
        self.selected_move  = 0
        self.turn_delay     = 0   # frames to wait before accepting input
        self.game_over      = False
        self.winner         = None

        # Faint flash state
        self.faint_flash_side   : Optional[str] = None   # "player" or "ai"
        self.faint_flash_frames : int = 0
        self.FAINT_FLASH_TOTAL  : int = 40   # ~0.66 s at 60 fps

        self.sprite_cache: dict = {}

    # ── sprite loading ───────────────────────────────────────────────────

    def load_sprite(self, pokemon: Pokemon) -> Optional[pygame.Surface]:
        if pokemon.id in self.sprite_cache:
            return self.sprite_cache[pokemon.id]
        path = f"assets/sprites/{pokemon.id:03d}.png"
        try:
            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.scale(img, (120, 120))
            self.sprite_cache[pokemon.id] = img
        except Exception:
            self.sprite_cache[pokemon.id] = None
        return self.sprite_cache[pokemon.id]

    # ── main loop ────────────────────────────────────────────────────────

    def run(self) -> str:
        clock = pygame.time.Clock()

        while True:
            clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"

                if event.type == pygame.KEYDOWN and not self.game_over:
                    if event.key == pygame.K_1: self.selected_move = 0
                    elif event.key == pygame.K_2: self.selected_move = 1
                    elif event.key == pygame.K_3: self.selected_move = 2
                    elif event.key == pygame.K_4: self.selected_move = 3

                # Accept click only when not animating and not waiting
                if (event.type == pygame.MOUSEBUTTONDOWN
                        and not self.game_over
                        and self.turn_delay == 0
                        and self.faint_flash_frames == 0):
                    for i in range(4):
                        btn = pygame.Rect(SCREEN_WIDTH - 255, 570 + i * 48, 240, 42)
                        if btn.collidepoint(event.pos):
                            self.selected_move = i
                            self._execute_turn()
                            break

            # Faint flash countdown
            if self.faint_flash_frames > 0:
                self.faint_flash_frames -= 1

            # Turn delay countdown (post-turn pause)
            if self.turn_delay > 0 and self.faint_flash_frames == 0:
                self.turn_delay -= 1

            self._draw()

            if self.game_over:
                return self._game_over_screen(clock)

    # ── turn execution ───────────────────────────────────────────────────

    def _execute_turn(self):
        s = self.engine.state
        player = s.get_player_pokemon()
        ai     = s.get_ai_pokemon()

        if self.selected_move >= len(player.moves):
            self.selected_move = 0

        ai_move     = self.engine.get_ai_move()
        ai_move_idx = ai.moves.index(ai_move) if ai_move in ai.moves else 0

        # Remember who was active before the turn
        prev_player_active = s.player_active
        prev_ai_active     = s.ai_active

        self.engine.process_turn(self.selected_move, ai_move_idx)

        # Did anyone faint and switch?
        if s.player_active != prev_player_active:
            # Player pokemon fainted → flash the old slot position
            self.faint_flash_side   = "player"
            self.faint_flash_frames = self.FAINT_FLASH_TOTAL

        if s.ai_active != prev_ai_active:
            self.faint_flash_side   = "ai"
            self.faint_flash_frames = self.FAINT_FLASH_TOTAL

        if s.game_over:
            self.game_over = True
            self.winner    = s.winner
        else:
            self.turn_delay = 20   # ~0.33 s pause between turns

    # ── drawing ──────────────────────────────────────────────────────────

    def _draw(self):
        self.screen.fill(BG_COLOR)

        s  = self.engine.state
        ai = s.get_ai_pokemon()
        pl = s.get_player_pokemon()

        # Opponent pokemon — top right
        self._draw_sprite(ai,  SCREEN_WIDTH - 210, 55,  faint_side="ai")
        self._draw_hp_bar(ai,  40, 55, 280, 32)

        # Player pokemon — bottom left
        self._draw_sprite(pl, 90, SCREEN_HEIGHT - 280, faint_side="player")
        self._draw_hp_bar(pl, 310, SCREEN_HEIGHT - 295, 330, 36)

        self._draw_move_buttons(pl)
        self._draw_battle_log()
        self._draw_team_dots()

        turn_surf = self.font_small.render(f"Turn {s.turn}", True, GRAY)
        self.screen.blit(turn_surf, (SCREEN_WIDTH // 2 - turn_surf.get_width() // 2, 8))

        # "Waiting…" hint during delay
        if self.turn_delay > 0:
            hint = self.font_tiny.render("…", True, GRAY)
            self.screen.blit(hint, (SCREEN_WIDTH - 255, 555))

        pygame.display.flip()

    def _draw_sprite(self, pokemon: Pokemon, x: int, y: int, faint_side: str):
        sprite = self.load_sprite(pokemon)

        # Flash white when this side just fainted
        flashing = (self.faint_flash_side == faint_side
                    and self.faint_flash_frames > 0
                    and self.faint_flash_frames % 8 < 4)

        if sprite:
            surf = sprite.copy()
            if flashing:
                white_overlay = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
                white_overlay.fill((255, 255, 255, 180))
                surf.blit(white_overlay, (0, 0))
            self.screen.blit(surf, (x, y))
        else:
            color = (255, 255, 255) if flashing else get_type_color(pokemon.types[0])
            pygame.draw.rect(self.screen, color, (x, y, 120, 120))
            if not flashing:
                letter = self.font_title.render(pokemon.name[0], True, WHITE)
                self.screen.blit(letter, (x + 60 - letter.get_width() // 2,
                                          y + 60 - letter.get_height() // 2))

    def _draw_hp_bar(self, pokemon: Pokemon, x: int, y: int, width: int, height: int):
        max_hp = pokemon.get_max_hp()
        cur_hp = max(0, pokemon.current_hp)
        pct    = cur_hp / max_hp if max_hp > 0 else 0

        name_surf = self.font_name.render(pokemon.name, True, WHITE)
        self.screen.blit(name_surf, (x, y - 28))

        # Status badge
        if pokemon.status:
            badge_colors = {
                "burned":    (255, 90,  0  ),
                "poisoned":  (160, 0,   160),
                "paralyzed": (230, 200, 0  ),
                "sleep":     (80,  80,  180),
                "frozen":    (80,  200, 255),
            }
            bc = badge_colors.get(pokemon.status, GRAY)
            bx = x + name_surf.get_width() + 8
            pygame.draw.rect(self.screen, bc, (bx, y - 26, 34, 18))
            bs = self.font_tiny.render(pokemon.status[:3].upper(), True, WHITE)
            self.screen.blit(bs, (bx + 2, y - 25))

        pygame.draw.rect(self.screen, DARK_GRAY, (x, y, width, height))
        bar_w = int((width - 4) * pct)
        if bar_w > 0:
            hp_col = GREEN if pct > 0.5 else YELLOW if pct > 0.2 else RED
            pygame.draw.rect(self.screen, hp_col, (x + 2, y + 2, bar_w, height - 4))
        pygame.draw.rect(self.screen, WHITE, (x, y, width, height), 2)

        hp_txt = self.font_small.render(f"{cur_hp}/{max_hp}", True, WHITE)
        self.screen.blit(hp_txt, (x + width + 10,
                                   y + height // 2 - hp_txt.get_height() // 2))

    def _draw_move_buttons(self, pokemon: Pokemon):
        x, y = SCREEN_WIDTH - 255, 555
        hdr = self.font_name.render("Choose move:", True, WHITE)
        self.screen.blit(hdr, (x, y - 28))

        for i, move in enumerate(pokemon.moves[:4]):
            btn = pygame.Rect(x, y + i * 48, 240, 42)
            col = get_type_color(move.type)

            # Highlight selected
            if i == self.selected_move:
                pygame.draw.rect(self.screen, YELLOW, btn.inflate(6, 6), 3)

            # Grey-out if no PP
            if move.pp == 0:
                col = DARK_GRAY

            pygame.draw.rect(self.screen, col, btn)
            pygame.draw.rect(self.screen, WHITE, btn, 2)

            name_s = self.font_small.render(move.name[:18], True, BLACK)
            self.screen.blit(name_s, (x + 8, y + i * 48 + 12))

            pp_s = self.font_tiny.render(f"PP {move.pp}", True, DARK_GRAY)
            self.screen.blit(pp_s, (x + 183, y + i * 48 + 15))

            key_s = self.font_tiny.render(f"[{i+1}]", True, DARK_GRAY)
            self.screen.blit(key_s, (x + 218, y + i * 48 + 15))

    def _draw_battle_log(self):
        log_rect = pygame.Rect(40, 420, 450, 155)
        pygame.draw.rect(self.screen, (30, 30, 50), log_rect)
        pygame.draw.rect(self.screen, (80, 80, 120), log_rect, 2)

        hdr = self.font_small.render("Battle Log", True, GRAY)
        self.screen.blit(hdr, (50, 425))

        for i, msg in enumerate(self.engine.state.battle_log[-6:]):
            alpha = 180 + int(75 * i / 5)   # older lines slightly dimmer
            col = (alpha, alpha, alpha)
            txt = self.font_tiny.render(msg[:62], True, col)
            self.screen.blit(txt, (50, 445 + i * 22))

    def _draw_team_dots(self):
        s = self.engine.state
        for i, p in enumerate(s.player_team):
            col = GREEN if not p.is_fainted() else RED
            cx  = 42 + i * 22
            cy  = SCREEN_HEIGHT - 14
            pygame.draw.circle(self.screen, col, (cx, cy), 8)
            if i == s.player_active:
                pygame.draw.circle(self.screen, WHITE, (cx, cy), 8, 2)

        for i, p in enumerate(s.ai_team):
            col = GREEN if not p.is_fainted() else RED
            cx  = SCREEN_WIDTH - 42 - i * 22
            cy  = 14
            pygame.draw.circle(self.screen, col, (cx, cy), 8)
            if i == s.ai_active:
                pygame.draw.circle(self.screen, WHITE, (cx, cy), 8, 2)

    # ── game over ────────────────────────────────────────────────────────

    def _game_over_screen(self, clock) -> str:
        pa_btn   = pygame.Rect(SCREEN_WIDTH // 2 - 205, SCREEN_HEIGHT // 2 + 20, 190, 60)
        quit_btn = pygame.Rect(SCREEN_WIDTH // 2 +  15, SCREEN_HEIGHT // 2 + 20, 190, 60)

        while True:
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if pa_btn.collidepoint(event.pos):
                        return "play_again"
                    if quit_btn.collidepoint(event.pos):
                        return "quit"

            self.screen.fill(BLACK)

            if self.winner == "player":
                msg = self.font_title.render("VICTORY!", True, GREEN)
            else:
                msg = self.font_title.render("DEFEAT!", True, RED)
            self.screen.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2,
                                    SCREEN_HEIGHT // 2 - 80))

            pygame.draw.rect(self.screen, GREEN, pa_btn)
            pygame.draw.rect(self.screen, WHITE, pa_btn, 2)
            pa_t = self.font_name.render("Play Again", True, WHITE)
            self.screen.blit(pa_t, (pa_btn.centerx - pa_t.get_width() // 2,
                                     pa_btn.centery - pa_t.get_height() // 2))

            pygame.draw.rect(self.screen, RED, quit_btn)
            pygame.draw.rect(self.screen, WHITE, quit_btn, 2)
            q_t = self.font_name.render("Quit", True, WHITE)
            self.screen.blit(q_t, (quit_btn.centerx - q_t.get_width() // 2,
                                    quit_btn.centery - q_t.get_height() // 2))

            pygame.display.flip()
