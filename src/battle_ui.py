import urllib.request
import io
import os
import threading
import numpy as np
import pygame
from typing import List, Optional

from pokemon import Pokemon
from battle import BattleEngine
from utils import get_type_color

# Colori UI Aggiornati per stile Lotta
WHITE      = (255, 255, 255)
BLACK      = (0,   0,   0  )
GRAY       = (128, 128, 128)
DARK_GRAY  = (64,  64,  64 )
LIGHT_GRAY = (240, 240, 240)
BLUE       = (100, 140, 255)
GREEN      = (60,  220, 100)
RED        = (220, 60,  60 )
YELLOW     = (250, 200, 50 )
BG_SKY     = (160, 200, 230)   # Cielo sereno
BG_GROUND  = (120, 180, 120)   # Terreno erboso
PANEL_BORDER= (40, 40, 50)

SCREEN_WIDTH  = 1024
SCREEN_HEIGHT = 768

# Cartella locale dove salvare i cry scaricati
SOUNDS_DIR = "assets/sounds"


# ---------------------------------------------------------------------------
# Generazione suoni sintetici per le mosse (nessuna dipendenza esterna)
# ---------------------------------------------------------------------------

def _generate_move_sound(move_type: str) -> pygame.mixer.Sound:
    """
    Genera un suono sintetico diverso in base alla categoria della mossa.
    Restituisce sempre un Sound valido, mai None.
    """
    sample_rate = 44100
    duration    = 0.25   # secondi

    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

    # Mosse fisiche → suono d'impatto (burst noise + decay)
    PHYSICAL_TYPES = {"normal", "fighting", "ground", "rock", "steel", "poison", "bug"}
    # Mosse speciali → suono energetico (onda sinusoidale con sweep)
    SPECIAL_TYPES  = {"fire", "water", "electric", "grass", "ice", "psychic",
                      "dragon", "dark", "ghost", "fairy"}

    if move_type.lower() in PHYSICAL_TYPES:
        # Burst di rumore con decay rapido → suono di "colpo"
        noise   = np.random.uniform(-1, 1, len(t))
        decay   = np.exp(-t * 18)
        wave    = noise * decay
    elif move_type.lower() in SPECIAL_TYPES:
        # Sweep frequenza da 400 → 900 Hz → suono "energetico"
        freq    = np.linspace(400, 900, len(t))
        phase   = np.cumsum(2 * np.pi * freq / sample_rate)
        decay   = np.exp(-t * 8)
        wave    = np.sin(phase) * decay
    else:
        # Status / altro → tono puro breve
        wave    = np.sin(2 * np.pi * 600 * t) * np.exp(-t * 12)

    # Normalizza e converti in int16
    wave = wave / (np.max(np.abs(wave)) + 1e-9)
    samples = (wave * 32767 * 0.6).astype(np.int16)

    # pygame richiede array stereo
    stereo = np.column_stack([samples, samples])
    sound  = pygame.sndarray.make_sound(stereo)
    return sound


# ---------------------------------------------------------------------------
# SoundManager: gestisce cry Pokémon + suoni mosse
# ---------------------------------------------------------------------------

class SoundManager:
    """
    Gestisce tutti i suoni di battaglia:
    - Cry del Pokémon (scaricato da PokeAPI, salvato in assets/sounds/)
    - Suoni sintetici per le mosse (fisiche / speciali / status)
    - Suono faint (cry rallentato via pitch pitching emulato)
    """

    def __init__(self):
        # Assicurati che il mixer sia inizializzato
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

        os.makedirs(SOUNDS_DIR, exist_ok=True)

        self._cry_cache:  dict = {}   # id_pokemon → pygame.mixer.Sound | None
        self._move_cache: dict = {}   # move_type  → pygame.mixer.Sound
        self._loading:    set  = set() # id in download async

    # ------------------------------------------------------------------
    # CRY
    # ------------------------------------------------------------------

    def _cry_path(self, pokemon_id: int) -> str:
        return os.path.join(SOUNDS_DIR, f"{pokemon_id:03d}.ogg")

    def _download_cry(self, pokemon_id: int):
        """Scarica il cry .ogg da PokeAPI in background e lo mette in cache."""
        url  = f"https://raw.githubusercontent.com/PokeAPI/cries/main/cries/pokemon/latest/{pokemon_id}.ogg"
        path = self._cry_path(pokemon_id)
        try:
            urllib.request.urlretrieve(url, path)
            sound = pygame.mixer.Sound(path)
            self._cry_cache[pokemon_id] = sound
            print(f"[Audio] Cry scaricato: #{pokemon_id:03d}")
        except Exception as e:
            print(f"[Audio] Errore download cry #{pokemon_id:03d}: {e}")
            self._cry_cache[pokemon_id] = None
        finally:
            self._loading.discard(pokemon_id)

    def preload_cry(self, pokemon_id: int):
        """
        Avvia il download del cry in background se non è già in cache.
        Chiamalo quando il Pokémon entra in campo.
        """
        if pokemon_id in self._cry_cache or pokemon_id in self._loading:
            return

        # Prima controlla se già salvato su disco
        path = self._cry_path(pokemon_id)
        if os.path.exists(path):
            try:
                self._cry_cache[pokemon_id] = pygame.mixer.Sound(path)
                return
            except Exception:
                pass  # file corrotto → riscaricare

        # Scarica in background per non bloccare il gioco
        self._loading.add(pokemon_id)
        t = threading.Thread(target=self._download_cry, args=(pokemon_id,), daemon=True)
        t.start()

    def play_cry(self, pokemon_id: int, faint: bool = False):
        """
        Suona il cry del Pokémon.
        faint=True → volume più basso + canale dedicato (simula il cry di morte).
        Se il cry non è ancora pronto, avvia preload e non fa nulla (non blocca).
        """
        if pokemon_id not in self._cry_cache:
            self.preload_cry(pokemon_id)
            return  # non ancora pronto, skip

        sound = self._cry_cache[pokemon_id]
        if sound is None:
            return

        # Usa un canale dedicato così non taglia altre cose
        ch = pygame.mixer.find_channel(True)
        if ch is None:
            return

        vol = 0.35 if faint else 0.75
        sound.set_volume(vol)
        ch.play(sound)

    # ------------------------------------------------------------------
    # SUONI MOSSE
    # ------------------------------------------------------------------

    def play_move_sound(self, move_type: str):
        """Suona il suono sintetico corrispondente al tipo della mossa."""
        key = move_type.lower()
        if key not in self._move_cache:
            self._move_cache[key] = _generate_move_sound(key)
        sound = self._move_cache[key]
        sound.set_volume(0.5)
        sound.play()

    # ------------------------------------------------------------------
    # UTILITÀ
    # ------------------------------------------------------------------

    def stop_all(self):
        pygame.mixer.stop()


# ---------------------------------------------------------------------------
# BattleUI
# ---------------------------------------------------------------------------

class BattleUI:
    def __init__(self, screen: pygame.Surface,
                 player_team: List[Pokemon], ai_team: List[Pokemon]):
        self.screen = screen
        self.font_title = pygame.font.Font(None, 48)
        self.font_name  = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        self.font_tiny  = pygame.font.Font(None, 20)

        self.engine = BattleEngine(player_team, ai_team)
        self.selected_move  = 0
        self.turn_delay     = 0
        self.game_over      = False
        self.winner         = None

        self.faint_flash_side   : Optional[str] = None
        self.faint_flash_frames : int = 0
        self.FAINT_FLASH_TOTAL  : int = 40

        self.sprite_cache: dict = {}

        # ---- Audio ----
        self.sound = SoundManager()

        # Precarica i cry dei Pokémon in campo all'inizio
        s = self.engine.state
        self.sound.preload_cry(s.get_player_pokemon().id)
        self.sound.preload_cry(s.get_ai_pokemon().id)

        # Traccia l'ultimo Pokémon in campo per sapere quando cambia
        self._last_player_id = s.get_player_pokemon().id
        self._last_ai_id     = s.get_ai_pokemon().id

        # Suona i cry di entrata iniziali (con piccolo ritardo per il caricamento)
        self._entry_cry_delay: dict = {
            "player": 90,   # frame di attesa prima di suonare (≈1.5s a 60fps)
            "ai":     120,
        }

    # ------------------------------------------------------------------

    def _draw_text_with_shadow(self, text: str, font: pygame.font.Font, color: tuple, x: int, y: int, shadow_col=DARK_GRAY):
        shadow_surf = font.render(text, True, shadow_col)
        text_surf   = font.render(text, True, color)
        self.screen.blit(shadow_surf, (x + 2, y + 2))
        self.screen.blit(text_surf,   (x, y))

    # ------------------------------------------------------------------

    def load_sprite(self, pokemon: Pokemon, is_player: bool) -> Optional[pygame.Surface]:
        cache_key = f"{pokemon.id}_{'back' if is_player else 'front'}"

        if cache_key in self.sprite_cache:
            return self.sprite_cache[cache_key]

        try:
            poke_id  = int(pokemon.id)
            filename = f"{poke_id:03d}_back.png" if is_player else f"{poke_id:03d}.png"
            path     = f"assets/sprites/{filename}"
            img      = pygame.image.load(path).convert_alpha()
            img      = pygame.transform.scale(img, (160, 160))
            self.sprite_cache[cache_key] = img
        except Exception as e:
            print(f"Errore sprite ID {pokemon.id}: {e}")
            self.sprite_cache[cache_key] = None

        return self.sprite_cache[cache_key]

    # ------------------------------------------------------------------

    def run(self) -> str:
        clock = pygame.time.Clock()

        while True:
            clock.tick(60)

            # Gestione ritardo cry di entrata iniziali
            for side, frames in list(self._entry_cry_delay.items()):
                if frames > 0:
                    self._entry_cry_delay[side] -= 1
                    if self._entry_cry_delay[side] == 0:
                        s = self.engine.state
                        pk = s.get_player_pokemon() if side == "player" else s.get_ai_pokemon()
                        self.sound.play_cry(pk.id)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"

                if event.type == pygame.KEYDOWN and not self.game_over:
                    if event.key == pygame.K_1: self.selected_move = 0
                    elif event.key == pygame.K_2: self.selected_move = 1
                    elif event.key == pygame.K_3: self.selected_move = 2
                    elif event.key == pygame.K_4: self.selected_move = 3

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

            if self.faint_flash_frames > 0:
                self.faint_flash_frames -= 1

            if self.turn_delay > 0 and self.faint_flash_frames == 0:
                self.turn_delay -= 1

            self._draw()

            if self.game_over:
                return self._game_over_screen(clock)

    # ------------------------------------------------------------------

    def _execute_turn(self):
        s      = self.engine.state
        player = s.get_player_pokemon()
        ai     = s.get_ai_pokemon()

        if self.selected_move >= len(player.moves):
            self.selected_move = 0

        # Mossa scelta dal giocatore e dalla AI
        player_move = player.moves[self.selected_move]
        ai_move     = self.engine.get_ai_move()
        ai_move_idx = ai.moves.index(ai_move) if ai_move in ai.moves else 0

        prev_player_active = s.player_active
        prev_ai_active     = s.ai_active

        # ---- Suono della mossa del giocatore ----
        self.sound.play_move_sound(player_move.type)

        self.engine.process_turn(self.selected_move, ai_move_idx)

        # ---- Suono della mossa dell'AI (piccolo sfasamento non necessario,
        #      process_turn è istantaneo, ma il log mostra entrambe) ----
        self.sound.play_move_sound(ai_move.type)

        # ---- Faint player ----
        if s.player_active != prev_player_active:
            self.faint_flash_side   = "player"
            self.faint_flash_frames = self.FAINT_FLASH_TOTAL
            # Cry faint del Pokémon che è appena svenuto
            fainted_id = s.player_team[prev_player_active].id
            self.sound.play_cry(fainted_id, faint=True)
            # Precarica il cry del nuovo Pokémon che entrerà
            new_pk = s.get_player_pokemon()
            self.sound.preload_cry(new_pk.id)
            self._last_player_id = new_pk.id
            # Cry di entrata del nuovo pokémon dopo il flash
            self._entry_cry_delay["player"] = self.FAINT_FLASH_TOTAL + 30

        # ---- Faint AI ----
        if s.ai_active != prev_ai_active:
            self.faint_flash_side   = "ai"
            self.faint_flash_frames = self.FAINT_FLASH_TOTAL
            fainted_id = s.ai_team[prev_ai_active].id
            self.sound.play_cry(fainted_id, faint=True)
            new_pk = s.get_ai_pokemon()
            self.sound.preload_cry(new_pk.id)
            self._last_ai_id = new_pk.id
            self._entry_cry_delay["ai"] = self.FAINT_FLASH_TOTAL + 30

        if s.game_over:
            self.game_over = True
            self.winner    = s.winner
        else:
            self.turn_delay = 20

    # ------------------------------------------------------------------

    def _draw(self):
        self.screen.fill(BG_SKY)
        pygame.draw.rect(self.screen, BG_GROUND, (0, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT // 2))

        pygame.draw.ellipse(self.screen, (90, 140, 90), (SCREEN_WIDTH - 280, 150, 240, 70))
        pygame.draw.ellipse(self.screen, (90, 140, 90), (50, SCREEN_HEIGHT - 220, 280, 80))

        s  = self.engine.state
        ai = s.get_ai_pokemon()
        pl = s.get_player_pokemon()

        self._draw_sprite(ai,  SCREEN_WIDTH - 240, 30,  faint_side="ai",     is_player=False)
        self._draw_hp_bar(ai,  40, 55, 300, 60, is_player=False)

        self._draw_sprite(pl, 110, SCREEN_HEIGHT - 320, faint_side="player", is_player=True)
        self._draw_hp_bar(pl, 350, SCREEN_HEIGHT - 330, 340, 70, is_player=True)

        self._draw_move_buttons(pl)
        self._draw_battle_log()
        self._draw_team_dots()

        turn_str = f"Turno {s.turn}"
        tw = self.font_small.size(turn_str)[0]
        self._draw_text_with_shadow(turn_str, self.font_small, WHITE, SCREEN_WIDTH // 2 - tw // 2, 10, shadow_col=BLACK)

        if self.turn_delay > 0:
            hint = self.font_tiny.render("Attendere…", True, BLACK)
            self.screen.blit(hint, (SCREEN_WIDTH - 250, 545))

        pygame.display.flip()

    # ------------------------------------------------------------------

    def _draw_sprite(self, pokemon: Pokemon, x: int, y: int, faint_side: str, is_player: bool):
        sprite   = self.load_sprite(pokemon, is_player)
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
            color = WHITE if flashing else get_type_color(pokemon.types[0])
            rect  = pygame.Rect(x, y + 20, 120, 120)
            pygame.draw.rect(self.screen, color, rect, border_radius=10)
            pygame.draw.rect(self.screen, PANEL_BORDER, rect, 3, border_radius=10)
            if not flashing:
                self._draw_text_with_shadow(pokemon.name[0], self.font_title, WHITE, x + 45, y + 65)

    # ------------------------------------------------------------------

    def _draw_hp_bar(self, pokemon: Pokemon, x: int, y: int, width: int, height: int, is_player: bool):
        max_hp = pokemon.get_max_hp()
        cur_hp = max(0, pokemon.current_hp)
        pct    = cur_hp / max_hp if max_hp > 0 else 0

        panel_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, DARK_GRAY, panel_rect.move(4, 4), border_radius=15)
        pygame.draw.rect(self.screen, LIGHT_GRAY, panel_rect, border_radius=15)
        pygame.draw.rect(self.screen, PANEL_BORDER, panel_rect, 3, border_radius=15)

        self._draw_text_with_shadow(pokemon.name, self.font_name, BLACK, x + 15, y + 10, shadow_col=WHITE)

        if pokemon.status:
            badge_colors = {
                "burned":    (250, 100, 50 ),
                "poisoned":  (160, 60,  160),
                "paralyzed": (240, 200, 30 ),
                "sleep":     (140, 140, 200),
                "frozen":    (100, 210, 250),
            }
            bc = badge_colors.get(pokemon.status, GRAY)
            bx = x + width - 60
            pygame.draw.rect(self.screen, bc, (bx, y + 10, 45, 22), border_radius=8)
            pygame.draw.rect(self.screen, BLACK, (bx, y + 10, 45, 22), 1, border_radius=8)
            bs = self.font_tiny.render(pokemon.status[:3].upper(), True, WHITE)
            self.screen.blit(bs, (bx + 6, y + 14))

        bar_x, bar_y = x + 40, y + 38 if not is_player else y + 42
        bar_w, bar_h = width - 60, 10

        hp_sym = self.font_tiny.render("HP", True, (220, 200, 50))
        self.screen.blit(hp_sym, (bar_x - 25, bar_y - 2))

        pygame.draw.rect(self.screen, DARK_GRAY, (bar_x, bar_y, bar_w, bar_h), border_radius=5)

        fill_w = int(bar_w * pct)
        if fill_w > 0:
            hp_col = GREEN if pct > 0.5 else YELLOW if pct > 0.2 else RED
            pygame.draw.rect(self.screen, hp_col, (bar_x, bar_y, fill_w, bar_h), border_radius=5)

        pygame.draw.rect(self.screen, PANEL_BORDER, (bar_x, bar_y, bar_w, bar_h), 2, border_radius=5)

        if is_player:
            hp_txt = f"{cur_hp} / {max_hp}"
            self._draw_text_with_shadow(hp_txt, self.font_small, BLACK, x + 40, y + 55, shadow_col=WHITE)

    # ------------------------------------------------------------------

    def _draw_move_buttons(self, pokemon: Pokemon):
        x, y = SCREEN_WIDTH - 255, 555
        self._draw_text_with_shadow("Seleziona mossa:", self.font_name, WHITE, x, y - 35, shadow_col=BLACK)

        for i, move in enumerate(pokemon.moves[:4]):
            btn = pygame.Rect(x, y + i * 48, 240, 42)
            col = get_type_color(move.type)

            if move.pp == 0:
                col = DARK_GRAY

            pygame.draw.rect(self.screen, DARK_GRAY, btn.move(2, 2), border_radius=8)
            pygame.draw.rect(self.screen, LIGHT_GRAY, btn, border_radius=8)
            pygame.draw.rect(self.screen, col, btn.inflate(-6, -6), border_radius=6)

            if i == self.selected_move:
                pygame.draw.rect(self.screen, RED, btn, 3, border_radius=8)
            else:
                pygame.draw.rect(self.screen, PANEL_BORDER, btn, 2, border_radius=8)

            self._draw_text_with_shadow(move.name[:18], self.font_small, WHITE, x + 12, y + i * 48 + 12)

            pp_str = f"PP {move.pp}"
            self._draw_text_with_shadow(pp_str, self.font_tiny, WHITE, x + 183, y + i * 48 + 14)

    # ------------------------------------------------------------------

    def _draw_battle_log(self):
        log_rect = pygame.Rect(20, 540, 720, 200)
        pygame.draw.rect(self.screen, PANEL_BORDER, log_rect, border_radius=12)
        pygame.draw.rect(self.screen, WHITE, log_rect.inflate(-8, -8), border_radius=10)
        pygame.draw.rect(self.screen, (200, 50, 50), log_rect.inflate(-16, -16), 2, border_radius=8)

        for i, msg in enumerate(self.engine.state.battle_log[-6:]):
            col = BLACK if i == 5 else DARK_GRAY
            txt = self.font_small.render(msg[:70], True, col)
            self.screen.blit(txt, (40, 555 + i * 28))

    # ------------------------------------------------------------------

    def _draw_team_dots(self):
        s = self.engine.state

        pygame.draw.rect(self.screen, (0, 0, 0, 100), (20, SCREEN_HEIGHT - 35, 160, 25), border_radius=12)
        pygame.draw.rect(self.screen, (0, 0, 0, 100), (SCREEN_WIDTH - 180, 15, 160, 25), border_radius=12)

        for i, p in enumerate(s.player_team):
            col = GREEN if not p.is_fainted() else RED
            cx  = 35 + i * 24
            cy  = SCREEN_HEIGHT - 22
            pygame.draw.circle(self.screen, col, (cx, cy), 8)
            pygame.draw.circle(self.screen, BLACK, (cx, cy), 8, 1)
            if i == s.player_active:
                pygame.draw.circle(self.screen, WHITE, (cx, cy), 8, 2)

        for i, p in enumerate(s.ai_team):
            col = GREEN if not p.is_fainted() else RED
            cx  = SCREEN_WIDTH - 35 - i * 24
            cy  = 27
            pygame.draw.circle(self.screen, col, (cx, cy), 8)
            pygame.draw.circle(self.screen, BLACK, (cx, cy), 8, 1)
            if i == s.ai_active:
                pygame.draw.circle(self.screen, WHITE, (cx, cy), 8, 2)

    # ------------------------------------------------------------------

    def _game_over_screen(self, clock) -> str:
        pa_btn   = pygame.Rect(SCREEN_WIDTH // 2 - 210, SCREEN_HEIGHT // 2 + 40, 200, 60)
        quit_btn = pygame.Rect(SCREEN_WIDTH // 2 +  10, SCREEN_HEIGHT // 2 + 40, 200, 60)

        while True:
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if pa_btn.collidepoint(event.pos):   return "play_again"
                    if quit_btn.collidepoint(event.pos): return "quit"

            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            self.screen.blit(overlay, (0, 0))

            if self.winner == "player":
                msg = "VITTORIA!"
                col = (100, 255, 100)
            else:
                msg = "SCONFITTA!"
                col = (255, 100, 100)

            mw = self.font_title.size(msg)[0]
            self._draw_text_with_shadow(msg, self.font_title, col, SCREEN_WIDTH // 2 - mw // 2, SCREEN_HEIGHT // 2 - 80)

            for btn, testo, b_col in [(pa_btn, "Rigioca", GREEN), (quit_btn, "Esci", RED)]:
                pygame.draw.rect(self.screen, DARK_GRAY, btn.move(4, 4), border_radius=12)
                pygame.draw.rect(self.screen, b_col, btn, border_radius=12)
                pygame.draw.rect(self.screen, WHITE, btn, 3, border_radius=12)
                tw, th = self.font_name.size(testo)
                self._draw_text_with_shadow(testo, self.font_name, WHITE, btn.centerx - tw // 2, btn.centery - th // 2)

            pygame.display.flip()
