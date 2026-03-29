import pygame
from typing import List

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

    def run(self):
        """Run the battle."""
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
                    # Check move buttons
                    for i in range(4):
                        btn_rect = pygame.Rect(SCREEN_WIDTH - 250, 580 + i * 45, 230, 40)
                        if btn_rect.collidepoint(pos):
                            self.selected_move = i
                            self.execute_turn()
                            break

            self.draw()

            if self.game_over:
                return self.handle_game_over(clock)

            # Auto-continue after delay
            if self.next_turn_delay > 0:
                self.next_turn_delay -= 1
                if self.next_turn_delay == 0:
                    self.execute_turn()

    def execute_turn(self):
        """Execute a turn."""
        player_pokemon = self.engine.state.get_player_pokemon()

        if self.selected_move >= len(player_pokemon.moves):
            self.selected_move = 0

        ai_move = self.engine.get_ai_move()
        ai_move_index = player_pokemon.moves.index(ai_move) if ai_move in player_pokemon.moves else 0

        self.engine.process_turn(self.selected_move, ai_move_index)

        if self.engine.state.game_over:
            self.game_over = True
            self.winner = self.engine.state.winner
        else:
            self.next_turn_delay = 30  # ~0.5 second delay

    def handle_game_over(self, clock) -> str:
        """Handle game over screen."""
        running = True

        # Draw buttons
        play_again_btn = pygame.Rect(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2, 180, 60)
        quit_btn = pygame.Rect(SCREEN_WIDTH // 2 + 20, SCREEN_HEIGHT // 2, 180, 60)

        while running:
            clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"

                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = event.pos
                    if play_again_btn.collidepoint(pos):
                        return "play_again"
                    elif quit_btn.collidepoint(pos):
                        return "quit"

            self.draw_game_over(play_again_btn, quit_btn)

    def draw(self):
        """Draw the battle screen."""
        self.screen.fill(BLACK)

        # Draw opponent Pokemon (top right)
        ai_pokemon = self.engine.state.get_ai_pokemon()
        self.draw_pokemon(ai_pokemon, SCREEN_WIDTH - 200, 80, "ai", True)

        # Draw player Pokemon (bottom left)
        player_pokemon = self.engine.state.get_player_pokemon()
        self.draw_pokemon(player_pokemon, 150, SCREEN_HEIGHT - 250, "player", False)

        # Draw HP bars
        self.draw_hp_bar(ai_pokemon, 50, 80, 250, 30, "ai")
        self.draw_hp_bar(player_pokemon, 350, SCREEN_HEIGHT - 280, 300, 35, "player")

        # Draw move buttons
        self.draw_move_buttons(player_pokemon)

        # Draw battle log
        self.draw_battle_log()

        pygame.display.flip()

    def draw_pokemon(self, pokemon: Pokemon, x: int, y: int, trainer: str, is_front: bool):
        """Draw a Pokemon sprite (placeholder)."""
        # Draw placeholder rect
        sprite_size = 120
        sprite_rect = pygame.Rect(x, y, sprite_size, sprite_size)

        color = get_type_color(pokemon.types[0])
        pygame.draw.rect(self.screen, color, sprite_rect)

        # Draw name
        name = self.font_name.render(pokemon.name, True, WHITE)
        self.screen.blit(name, (x, y - 35))

    def draw_hp_bar(self, pokemon: Pokemon, x: int, y: int, width: int, height: int, trainer: str):
        """Draw an HP bar."""
        max_hp = pokemon.get_max_hp()
        current_hp = pokemon.current_hp

        # Background
        pygame.draw.rect(self.screen, DARK_GRAY, (x, y, width, height))

        # HP color based on percentage
        hp_percent = current_hp / max_hp if max_hp > 0 else 0
        if hp_percent > 0.5:
            hp_color = GREEN
        elif hp_percent > 0.2:
            hp_color = YELLOW
        else:
            hp_color = RED

        # HP bar
        bar_width = int((width - 4) * hp_percent)
        if bar_width > 0:
            pygame.draw.rect(self.screen, hp_color, (x + 2, y + 2, bar_width, height - 4))

        # Border
        pygame.draw.rect(self.screen, WHITE, (x, y, width, height), 2)

        # HP text
        hp_text = self.font_small.render(f"{current_hp}/{max_hp}", True, WHITE)
        self.screen.blit(hp_text, (x + width + 10, y + 5))

        # Name for player
        if trainer == "player":
            name = self.font_name.render(pokemon.name, True, WHITE)
            self.screen.blit(name, (x, y - 30))

    def draw_move_buttons(self, pokemon: Pokemon):
        """Draw move selection buttons."""
        x = SCREEN_WIDTH - 250
        y = 580

        title = self.font_name.render("Moves:", True, WHITE)
        self.screen.blit(title, (x, y - 35))

        for i, move in enumerate(pokemon.moves[:4]):
            btn_rect = pygame.Rect(x, y + i * 45, 230, 40)

            # Highlight selected
            color = get_type_color(move.type)
            if i == self.selected_move:
                pygame.draw.rect(self.screen, YELLOW, btn_rect, 4)

            pygame.draw.rect(self.screen, color, btn_rect)
            pygame.draw.rect(self.screen, WHITE, btn_rect, 2)

            # Move name
            name = self.font_small.render(move.name[:20], True, BLACK)
            self.screen.blit(name, (x + 10, y + i * 45 + 10))

            # PP
            pp_text = self.font_tiny.render(f"PP: {move.pp}", True, BLACK)
            self.screen.blit(pp_text, (x + 150, y + i * 45 + 15))

            # Key hint
            key = self.font_tiny.render(f"[{i + 1}]", True, DARK_GRAY)
            self.screen.blit(key, (x + 205, y + i * 45 + 15))

    def draw_battle_log(self):
        """Draw the battle log."""
        log_rect = pygame.Rect(50, 450, 400, 120)
        pygame.draw.rect(self.screen, DARK_GRAY, log_rect)
        pygame.draw.rect(self.screen, WHITE, log_rect, 2)

        title = self.font_small.render("Battle Log:", True, GRAY)
        self.screen.blit(title, (60, 455))

        # Draw last 4 log entries
        log = self.engine.state.battle_log[-4:]
        for i, msg in enumerate(log):
            text = self.font_tiny.render(msg[:50], True, WHITE)
            self.screen.blit(text, (60, 480 + i * 25))

    def draw_game_over(self, play_again_btn, quit_btn):
        """Draw game over screen."""
        self.screen.fill(BLACK)

        # Result
        if self.winner == "player":
            result = self.font_title.render("VICTORY!", True, GREEN)
        else:
            result = self.font_title.render("DEFEAT!", True, RED)

        self.screen.blit(result, (SCREEN_WIDTH // 2 - result.get_width() // 2, SCREEN_HEIGHT // 2 - 100))

        # Buttons
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