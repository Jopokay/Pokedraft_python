import pygame
from typing import List, Optional

from pokemon import Pokemon, Move
from battle import BattleEngine
from utils import get_type_color


WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
LIGHT_GRAY = (200, 200, 200)
BLUE = (100, 100, 255)
GREEN = (50, 200, 50)
RED = (200, 50, 50)
YELLOW = (255, 255, 0)

SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768


class BattleUI:
    def __init__(self, screen: pygame.Surface, player_team: List[Pokemon], ai_team: List[Pokemon]):
        self.screen = screen
        self.font_title = pygame.font.Font(None, 48)
        self.font_name = pygame.font.Font(None, 28)
        self.font_small = pygame.font.Font(None, 22)
        self.font_tiny = pygame.font.Font(None, 18)

        self.engine = BattleEngine(player_team, ai_team)
        self.selected_move = 0
        self.next_turn_delay = 0
        self.game_over = False
        self.winner = None

        # Sprite cache
        self.sprite_cache = {}

    def load_sprite(self, pokemon: Pokemon) -> Optional[pygame.Surface]:
        """Load sprite from assets/sprites/, return None if missing."""
        if pokemon.id in self.sprite_cache:
            return self.sprite_cache[pokemon.id]

        # Try zero-padded filename e.g. 001.png
        path = f"assets/sprites/{pokemon.id:03d}.png"
        try:
            img = pygame.image.load(path).convert_alpha()
            # Scale to a consistent size
            img = pygame.transform.scale(img, (120, 120))
            self.sprite_cache[pokemon.id] = img
            return img
        except Exception:
            self.sprite_cache[pokemon.id] = None
            return None

    def run(self):
        running = True
        clock = pygame.time.Clock()

        while running:
            clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        self.selected_move = 0
                    elif event.key == pygame.K_2:
                        self.selected_move = 1
                    elif event.key == pygame.K_3:
                        self.selected_move = 2
                    elif event.key == pygame.K_4:
                        self.selected_move = 3

                if event.type == pygame.MOUSEBUTTONDOWN and not self.game_over and self.next_turn_delay == 0:
                    pos = event.pos
                    for i in range(4):
                        btn_rect = pygame.Rect(SCREEN_WIDTH - 255, 575 + i * 48, 240, 42)
                        if btn_rect.collidepoint(pos):
                            self.selected_move = i
                            self.execute_turn()
                            break

            self.draw()

            if self.game_over:
                return self.handle_game_over(clock)

            if self.next_turn_delay > 0:
                self.next_turn_delay -= 1

    def execute_turn(self):
        player_pokemon = self.engine.state.get_player_pokemon()
        ai_pokemon = self.engine.state.get_ai_pokemon()

        if self.selected_move >= len(player_pokemon.moves):
            self.selected_move = 0

        # FIX: get AI move and find its index in the AI pokemon's moves (not player's)
        ai_move = self.engine.get_ai_move()
        ai_move_index = 0
        if ai_move in ai_pokemon.moves:
            ai_move_index = ai_pokemon.moves.index(ai_move)

        self.engine.process_turn(self.selected_move, ai_move_index)

        if self.engine.state.game_over:
            self.game_over = True
            self.winner = self.engine.state.winner
        else:
            self.next_turn_delay = 30

    def handle_game_over(self, clock) -> str:
        play_again_btn = pygame.Rect(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2, 180, 60)
        quit_btn = pygame.Rect(SCREEN_WIDTH // 2 + 20, SCREEN_HEIGHT // 2, 180, 60)

        while True:
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if play_again_btn.collidepoint(event.pos):
                        return "play_again"
                    elif quit_btn.collidepoint(event.pos):
                        return "quit"

            self.draw_game_over(play_again_btn, quit_btn)

    def draw(self):
        self.screen.fill((30, 30, 50))  # dark blue-gray instead of pure black

        ai_pokemon = self.engine.state.get_ai_pokemon()
        player_pokemon = self.engine.state.get_player_pokemon()

        # AI pokemon: top-right
        self.draw_pokemon_sprite(ai_pokemon, SCREEN_WIDTH - 220, 60)
        # Player pokemon: bottom-left  
        self.draw_pokemon_sprite(player_pokemon, 100, SCREEN_HEIGHT - 280)

        # HP bars
        self.draw_hp_bar(ai_pokemon, 40, 60, 280, 32, label_above=True)
        self.draw_hp_bar(player_pokemon, 320, SCREEN_HEIGHT - 300, 330, 36, label_above=True)

        # Move buttons
        self.draw_move_buttons(player_pokemon)

        # Battle log
        self.draw_battle_log()

        # Turn info
        turn_text = self.font_small.render(f"Turn {self.engine.state.turn}", True, GRAY)
        self.screen.blit(turn_text, (SCREEN_WIDTH // 2 - turn_text.get_width() // 2, 10))

        # Team status dots
        self.draw_team_status()

        pygame.display.flip()

    def draw_pokemon_sprite(self, pokemon: Pokemon, x: int, y: int):
        sprite = self.load_sprite(pokemon)
        if sprite:
            self.screen.blit(sprite, (x, y))
        else:
            # Colored placeholder
            color = get_type_color(pokemon.types[0])
            pygame.draw.rect(self.screen, color, (x, y, 120, 120))
            # Draw pokemon initial
            initial = self.font_title.render(pokemon.name[0], True, WHITE)
            self.screen.blit(initial, (x + 60 - initial.get_width() // 2,
                                        y + 60 - initial.get_height() // 2))

    def draw_hp_bar(self, pokemon: Pokemon, x: int, y: int, width: int, height: int, label_above=False):
        max_hp = pokemon.get_max_hp()
        current_hp = max(0, pokemon.current_hp)
        hp_percent = current_hp / max_hp if max_hp > 0 else 0

        name_y = y - 28 if label_above else y + height + 5
        name_text = self.font_name.render(pokemon.name, True, WHITE)
        self.screen.blit(name_text, (x, name_y))

        # Status badge
        if pokemon.status:
            status_colors = {"burned": (255, 100, 0), "poisoned": (160, 0, 160),
                             "paralyzed": (255, 220, 0), "sleep": (100, 100, 200),
                             "frozen": (100, 200, 255)}
            sc = status_colors.get(pokemon.status, GRAY)
            s_surf = self.font_tiny.render(pokemon.status[:3].upper(), True, WHITE)
            s_rect = pygame.Rect(x + name_text.get_width() + 8, name_y + 2, 30, 18)
            pygame.draw.rect(self.screen, sc, s_rect)
            self.screen.blit(s_surf, (s_rect.x + 2, s_rect.y + 2))

        pygame.draw.rect(self.screen, DARK_GRAY, (x, y, width, height))

        if hp_percent > 0.5:
            hp_color = GREEN
        elif hp_percent > 0.2:
            hp_color = YELLOW
        else:
            hp_color = RED

        bar_width = int((width - 4) * hp_percent)
        if bar_width > 0:
            pygame.draw.rect(self.screen, hp_color, (x + 2, y + 2, bar_width, height - 4))

        pygame.draw.rect(self.screen, WHITE, (x, y, width, height), 2)

        hp_text = self.font_small.render(f"{current_hp}/{max_hp}", True, WHITE)
        self.screen.blit(hp_text, (x + width + 10, y + height // 2 - hp_text.get_height() // 2))

    def draw_move_buttons(self, pokemon: Pokemon):
        x = SCREEN_WIDTH - 255
        y = 560

        title = self.font_name.render("Choose a move:", True, WHITE)
        self.screen.blit(title, (x, y - 30))

        for i, move in enumerate(pokemon.moves[:4]):
            btn_rect = pygame.Rect(x, y + i * 48, 240, 42)
            color = get_type_color(move.type)

            if i == self.selected_move:
                pygame.draw.rect(self.screen, YELLOW, btn_rect, 4)

            pygame.draw.rect(self.screen, color, btn_rect)
            pygame.draw.rect(self.screen, WHITE, btn_rect, 2)

            name = self.font_small.render(move.name[:18], True, BLACK)
            self.screen.blit(name, (x + 8, y + i * 48 + 10))

            pp_text = self.font_tiny.render(f"PP {move.pp}", True, DARK_GRAY)
            self.screen.blit(pp_text, (x + 185, y + i * 48 + 14))

            key = self.font_tiny.render(f"[{i + 1}]", True, DARK_GRAY)
            self.screen.blit(key, (x + 220, y + i * 48 + 14))

    def draw_battle_log(self):
        log_rect = pygame.Rect(40, 430, 430, 140)
        pygame.draw.rect(self.screen, DARK_GRAY, log_rect)
        pygame.draw.rect(self.screen, WHITE, log_rect, 2)

        title = self.font_small.render("Battle Log", True, GRAY)
        self.screen.blit(title, (50, 436))

        log = self.engine.state.battle_log[-5:]
        for i, msg in enumerate(log):
            text = self.font_tiny.render(msg[:58], True, WHITE)
            self.screen.blit(text, (50, 458 + i * 22))

    def draw_team_status(self):
        """Show HP dots for both teams."""
        # Player team (bottom)
        for i, p in enumerate(self.engine.state.player_team):
            color = GREEN if not p.is_fainted() else RED
            pygame.draw.circle(self.screen, color, (40 + i * 20, SCREEN_HEIGHT - 20), 7)

        # AI team (top)
        for i, p in enumerate(self.engine.state.ai_team):
            color = GREEN if not p.is_fainted() else RED
            pygame.draw.circle(self.screen, color, (SCREEN_WIDTH - 40 - i * 20, 20), 7)

    def draw_game_over(self, play_again_btn, quit_btn):
        self.screen.fill(BLACK)

        if self.winner == "player":
            result = self.font_title.render("VICTORY!", True, GREEN)
        else:
            result = self.font_title.render("DEFEAT!", True, RED)

        self.screen.blit(result, (SCREEN_WIDTH // 2 - result.get_width() // 2, SCREEN_HEIGHT // 2 - 120))

        pygame.draw.rect(self.screen, GREEN, play_again_btn)
        pygame.draw.rect(self.screen, WHITE, play_again_btn, 2)
        pa_text = self.font_name.render("Play Again", True, WHITE)
        self.screen.blit(pa_text, (play_again_btn.centerx - pa_text.get_width() // 2,
                                    play_again_btn.centery - pa_text.get_height() // 2))

        pygame.draw.rect(self.screen, RED, quit_btn)
        pygame.draw.rect(self.screen, WHITE, quit_btn, 2)
        q_text = self.font_name.render("Quit", True, WHITE)
        self.screen.blit(q_text, (quit_btn.centerx - q_text.get_width() // 2,
                                   quit_btn.centery - q_text.get_height() // 2))

        pygame.display.flip()
