import urllib.request
import os
import threading
import numpy as np
import pygame
from typing import List, Optional

from pokemon import Pokemon
from battle import BattleEngine, TurnEvent
from utils import get_type_color

# ── Palette ───────────────────────────────────────────────────────────────────
WHITE      = (255, 255, 255)
BLACK      = (0,   0,   0  )
GRAY       = (128, 128, 128)
DARK_GRAY  = (64,  64,  64 )
GREEN      = (72,  200, 88 )
RED        = (220, 56,  56 )
YELLOW     = (240, 200, 48 )

SKY_TOP    = (148, 196, 228)
SKY_HOR    = (198, 228, 240)
GND_TOP    = (104, 168, 84 )
GND_BOT    = (72,  128, 60 )
GND_LINE   = (116, 180, 96 )
PLAT_SH    = (52,  84,  48 )
PLAT_MAIN  = (80,  132, 72 )
PLAT_EDGE  = (104, 160, 96 )

PANEL_BG   = (72,  82,  62 )
PANEL_HI   = (96, 108,  82 )
PANEL_BDR  = (220, 228, 200)
HP_BG      = (24,  24,  24 )
HP_GREEN   = (88,  208, 80 )
HP_YELLOW  = (248, 208, 40 )
HP_RED     = (248, 48,  48 )
EXP_COL    = (64,  160, 248)

BTM_BDR    = (72,  192, 168)
BTM_BG     = (255, 255, 255)
BTM_TEXT   = (32,  32,  32 )

BTN_FIGHT  = (192, 48,  48 )
BTN_BAG    = (56,  160, 72 )
BTN_POKE   = (48,  120, 208)
BTN_RUN    = (128, 72,  192)

MOVE_BG    = (240, 240, 220)
MOVE_SEL   = (255, 220, 40 )

SCREEN_WIDTH  = 1024
SCREEN_HEIGHT = 768
HORIZON_Y     = 338
BOTTOM_Y      = 610
BOTTOM_H      = SCREEN_HEIGHT - BOTTOM_Y

AI_PLAT  = (762, 252, 220, 52)
PL_PLAT  = (200, 500, 284, 70)

AI_SPR_W, AI_SPR_H = 150, 150
PL_SPR_W, PL_SPR_H = 204, 204

AI_PNL  = (10,  10,  310, 78,  24)
PL_PNL  = (570, 494, 444, 106, 28)

SOUNDS_DIR     = "assets/sounds"
HP_ANIM_RATE   = 3.0   # HP units per frame (scaled by max_hp)


# ── Audio ─────────────────────────────────────────────────────────────────────

def _gen_move_sound(move_type):
    sr  = 44100; dur = 0.22
    t   = np.linspace(0, dur, int(sr * dur), endpoint=False)
    PHYS = {"normal","fighting","ground","rock","steel","poison","bug"}
    SPEC = {"fire","water","electric","grass","ice","psychic","dragon","dark","ghost","fairy"}
    mt   = move_type.lower()
    if mt in PHYS:
        wave = np.random.uniform(-1, 1, len(t)) * np.exp(-t * 20)
    elif mt in SPEC:
        ph   = np.cumsum(2 * np.pi * np.linspace(380, 860, len(t)) / sr)
        wave = np.sin(ph) * np.exp(-t * 9)
    else:
        wave = np.sin(2 * np.pi * 560 * t) * np.exp(-t * 14)
    wave /= (np.max(np.abs(wave)) + 1e-9)
    s = (wave * 32767 * 0.45).astype(np.int16)
    return pygame.sndarray.make_sound(np.column_stack([s, s]))


class SoundManager:
    def __init__(self):
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        os.makedirs(SOUNDS_DIR, exist_ok=True)
        self._cry = {}; self._move = {}; self._loading = set()

    def _cry_path(self, pid): return os.path.join(SOUNDS_DIR, f"{pid:03d}.ogg")

    def _dl_cry(self, pid):
        url = f"https://raw.githubusercontent.com/PokeAPI/cries/main/cries/pokemon/latest/{pid}.ogg"
        try:
            urllib.request.urlretrieve(url, self._cry_path(pid))
            self._cry[pid] = pygame.mixer.Sound(self._cry_path(pid))
        except Exception as e:
            print(f"[cry #{pid}] {e}"); self._cry[pid] = None
        finally: self._loading.discard(pid)

    def preload(self, pid):
        if pid in self._cry or pid in self._loading: return
        p = self._cry_path(pid)
        if os.path.exists(p):
            try: self._cry[pid] = pygame.mixer.Sound(p); return
            except: pass
        self._loading.add(pid)
        threading.Thread(target=self._dl_cry, args=(pid,), daemon=True).start()

    def play_cry(self, pid, faint=False):
        if pid not in self._cry: self.preload(pid); return
        s = self._cry[pid]
        if not s: return
        ch = pygame.mixer.find_channel(True)
        if ch: s.set_volume(0.18 if faint else 0.42); ch.play(s)

    def play_move(self, mt):
        if not mt: return
        k = mt.lower()
        if k not in self._move: self._move[k] = _gen_move_sound(k)
        self._move[k].set_volume(0.20); self._move[k].play()


# ── BattleUI ──────────────────────────────────────────────────────────────────

class BattleUI:
    def __init__(self, screen, player_team, ai_team):
        self.screen = screen
        self.fn  = pygame.font.Font(None, 28)
        self.flg = pygame.font.Font(None, 38)
        self.fmd = pygame.font.Font(None, 24)
        self.fsm = pygame.font.Font(None, 22)
        self.ftn = pygame.font.Font(None, 19)

        self.engine = BattleEngine(player_team, ai_team)
        self.selected_move  = 0
        self.game_over      = False
        self.winner         = None
        self.battle_mode    = "menu"   # "menu" | "fight"

        self.faint_flash_side   = None
        self.faint_flash_frames = 0
        self.FAINT_FLASH_TOTAL  = 40

        self.sprite_cache = {}

        s = self.engine.state
        self._anim_pl = float(s.get_player_pokemon().current_hp)
        self._anim_ai = float(s.get_ai_pokemon().current_hp)

        # ── Event queue ───────────────────────────────────────────────
        # After a turn is computed, events are queued here.
        # The UI shows one event at a time; player advances with SPACE/click.
        self._events:       List[TurnEvent] = []
        self._event_idx:    int  = 0
        self._waiting:      bool = False  # waiting for player to advance
        self._hp_animating: bool = False  # True while HP bar is in motion

        # ── Audio ─────────────────────────────────────────────────────
        self.sound = SoundManager()
        self.sound.preload(s.get_player_pokemon().id)
        self.sound.preload(s.get_ai_pokemon().id)
        self._entry_delay = {"player": 90, "ai": 120}

    # ── helpers ───────────────────────────────────────────────────────────────

    def _t(self, text, font, color, x, y, sh=None):
        if sh: self.screen.blit(font.render(text, True, sh), (x+1, y+1))
        self.screen.blit(font.render(text, True, color), (x, y))

    def _tc(self, text, font, color, cx, y):
        s = font.render(text, True, color)
        self.screen.blit(s, (cx - s.get_width()//2, y))

    def load_sprite(self, pokemon, is_player):
        key = f"{pokemon.id}_{'back' if is_player else 'front'}"
        if key in self.sprite_cache: return self.sprite_cache[key]
        try:
            pid = int(pokemon.id)
            fn  = f"{pid:03d}_back.png" if is_player else f"{pid:03d}.png"
            img = pygame.image.load(f"assets/sprites/{fn}").convert_alpha()
            w, h = (PL_SPR_W, PL_SPR_H) if is_player else (AI_SPR_W, AI_SPR_H)
            self.sprite_cache[key] = pygame.transform.scale(img, (w, h))
        except Exception as e:
            print(f"Sprite err {pokemon.id}: {e}"); self.sprite_cache[key] = None
        return self.sprite_cache[key]

    # ── current log message ───────────────────────────────────────────────────

    @property
    def _current_event(self) -> Optional[TurnEvent]:
        if self._events and self._event_idx < len(self._events):
            return self._events[self._event_idx]
        return None

    def _current_log_line(self) -> str:
        ev = self._current_event
        if ev:
            return ev.msg
        return ""

    # ── main loop ─────────────────────────────────────────────────────────────

    def run(self):
        clock = pygame.time.Clock()
        while True:
            clock.tick(60)

            # Entry cry delays
            for side, frames in list(self._entry_delay.items()):
                if frames > 0:
                    self._entry_delay[side] -= 1
                    if self._entry_delay[side] == 0:
                        s  = self.engine.state
                        pk = s.get_player_pokemon() if side == "player" else s.get_ai_pokemon()
                        self.sound.play_cry(pk.id)

            for event in pygame.event.get():
                if event.type == pygame.QUIT: return "quit"

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE and self.battle_mode == "fight":
                        self.battle_mode = "menu"

                    # Advance through events with SPACE or ENTER
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        self._try_advance()

                    if self.battle_mode == "fight" and not self._waiting:
                        for k, v in {pygame.K_1:0,pygame.K_2:1,pygame.K_3:2,pygame.K_4:3}.items():
                            if event.key == k: self.selected_move = v

                if event.type == pygame.MOUSEBUTTONDOWN and not self.game_over:
                    if self._waiting:
                        self._try_advance()
                    elif not self._events:
                        self._handle_click(event.pos)

            # Faint flash countdown
            if self.faint_flash_frames > 0:
                self.faint_flash_frames -= 1

            self._draw()

            if self.game_over:
                return self._game_over_screen(clock)

    # ── event queue management ────────────────────────────────────────────────

    def _try_advance(self):
        """Advance to next event. Called on SPACE/click."""
        if not self._events or self._event_idx >= len(self._events):
            return
        # If HP bar still animating for current event, snap it to final value
        ev = self._current_event
        if ev and ev.damage_side:
            s = self.engine.state
            if ev.damage_side == "player":
                self._anim_pl = float(max(0, s.get_player_pokemon().current_hp))
            else:
                self._anim_ai = float(max(0, s.get_ai_pokemon().current_hp))

        self._event_idx += 1
        if self._event_idx >= len(self._events):
            # All events consumed — clear queue
            self._events   = []
            self._event_idx = 0
            self._waiting  = False
            # Check if game over was signalled in last event
            if self.game_over:
                return
        else:
            # Show next event
            self._show_current_event()

    def _show_current_event(self):
        """Process the current event: play sounds, trigger flash, set waiting."""
        ev = self._current_event
        if not ev:
            return

        # Play move sound on move-use events
        if ev.move_type:
            self.sound.play_move(ev.move_type)

        # Faint flash
        if ev.faint_side:
            self.faint_flash_side   = ev.faint_side
            self.faint_flash_frames = self.FAINT_FLASH_TOTAL
            self.sound.play_cry(
                self.engine.state.player_team[self.engine.state.player_active].id
                if ev.faint_side == "player"
                else self.engine.state.ai_team[self.engine.state.ai_active - 1
                     if self.engine.state.ai_active > 0 else 0].id,
                faint=True
            )

        if ev.game_over:
            self.game_over = True
            self.winner    = ev.winner

        self._waiting = True   # wait for player input

    def _start_events(self, events):
        """Load a fresh event list and show the first one."""
        self._events    = events
        self._event_idx = 0
        self._waiting   = False
        if events:
            self._show_current_event()

    # ── click handling ────────────────────────────────────────────────────────

    def _action_rects(self):
        bx=516; by=BOTTOM_Y+10; w=238; h=68; gx=12; gy=8
        return [(bx,by),(bx+w+gx,by),(bx,by+h+gy),(bx+w+gx,by+h+gy)]

    def _fight_rects(self):
        bx=516; by=BOTTOM_Y+8; w=240; h=65; gx=12; gy=8
        rects=[]
        for i in range(4):
            r,c=divmod(i,2); rects.append((bx+c*(w+gx), by+r*(h+gy)))
        return rects

    def _handle_click(self, pos):
        if self.battle_mode == "menu":
            for i,(bx,by) in enumerate(self._action_rects()):
                if pygame.Rect(bx,by,238,68).collidepoint(pos):
                    if i==0: self.battle_mode="fight"
                    break
        elif self.battle_mode == "fight":
            pl = self.engine.state.get_player_pokemon()
            for i,(bx,by) in enumerate(self._fight_rects()):
                if i >= len(pl.moves): break
                if pygame.Rect(bx,by,240,65).collidepoint(pos):
                    self.selected_move = i
                    self._execute_turn()
                    self.battle_mode = "menu"
                    break

    # ── execute turn ──────────────────────────────────────────────────────────

    def _execute_turn(self):
        ai_move     = self.engine.get_ai_move()
        ai_move_idx = self.engine.state.get_ai_pokemon().moves.index(ai_move) \
                      if ai_move in self.engine.state.get_ai_pokemon().moves else 0

        events = self.engine.process_turn(self.selected_move, ai_move_idx)
        self._start_events(events)

    # ── draw ─────────────────────────────────────────────────────────────────

    def _draw(self):
        s  = self.engine.state
        ai = s.get_ai_pokemon(); pl = s.get_player_pokemon()

        # HP animation — smoothly approach target
        tpl = float(max(0, pl.current_hp)); tai = float(max(0, ai.current_hp))
        rate_pl = max(pl.get_max_hp() / (60 * 2.5), 0.5)   # drain over ~2.5s
        rate_ai = max(ai.get_max_hp() / (60 * 2.5), 0.5)
        self._anim_pl = max(tpl, self._anim_pl - rate_pl) if self._anim_pl > tpl else tpl
        self._anim_ai = max(tai, self._anim_ai - rate_ai) if self._anim_ai > tai else tai

        self._bg()

        cx,cy,pw,ph = AI_PLAT
        self._draw_sprite(ai, cx-AI_SPR_W//2, cy-AI_SPR_H, "ai", False)
        cx,cy,pw,ph = PL_PLAT
        self._draw_sprite(pl, cx-PL_SPR_W//2, cy-PL_SPR_H, "player", True)

        self._hp_ai(ai)
        self._hp_pl(pl)
        self._bottom(pl)
        self._dots()
        pygame.display.flip()

    def _bg(self):
        for y in range(HORIZON_Y):
            t   = y/HORIZON_Y
            col = tuple(int(SKY_TOP[i]+t*(SKY_HOR[i]-SKY_TOP[i])) for i in range(3))
            pygame.draw.line(self.screen, col, (0,y),(SCREEN_WIDTH,y))
        gh = BOTTOM_Y - HORIZON_Y
        for y in range(gh):
            t   = y/gh
            col = tuple(int(GND_TOP[i]+t*(GND_BOT[i]-GND_TOP[i])) for i in range(3))
            pygame.draw.line(self.screen, col, (0,HORIZON_Y+y),(SCREEN_WIDTH,HORIZON_Y+y))
        for y in range(HORIZON_Y, BOTTOM_Y, 28):
            pygame.draw.line(self.screen, GND_LINE, (0,y),(SCREEN_WIDTH,y),1)
        pygame.draw.rect(self.screen,(80,140,68),(0,HORIZON_Y-1,SCREEN_WIDTH,4))
        for (cx,cy,pw,ph) in [AI_PLAT,PL_PLAT]:
            rx=cx-pw//2; ry=cy-ph//2
            pygame.draw.ellipse(self.screen,PLAT_SH,  (rx+4,ry+4,pw,ph))
            pygame.draw.ellipse(self.screen,PLAT_MAIN,(rx,  ry,  pw,ph))
            pygame.draw.ellipse(self.screen,PLAT_EDGE,(rx,  ry,  pw,ph),2)

    def _draw_sprite(self,poke,x,y,faint_side,is_player):
        sprite   = self.load_sprite(poke,is_player)
        flashing = (self.faint_flash_side==faint_side
                    and self.faint_flash_frames>0
                    and self.faint_flash_frames%8<4)
        if sprite:
            surf = sprite.copy()
            if flashing:
                ov=pygame.Surface(surf.get_size(),pygame.SRCALPHA)
                ov.fill((255,255,255,200)); surf.blit(ov,(0,0))
            self.screen.blit(surf,(x,y))
        else:
            w=PL_SPR_W if is_player else AI_SPR_W
            h=PL_SPR_H if is_player else AI_SPR_H
            col=WHITE if flashing else get_type_color(poke.types[0])
            rect=pygame.Rect(x,y,w,h)
            pygame.draw.rect(self.screen,col,rect,border_radius=12)
            if not flashing:
                lbl=self.flg.render(poke.name[0],True,WHITE)
                self.screen.blit(lbl,(rect.centerx-lbl.get_width()//2,rect.centery-lbl.get_height()//2))

    def _trap(self,x,y,w,h,cut,side,color):
        if side=='R': pts=[(x,y),(x+w,y),(x+w-cut,y+h),(x,y+h)]
        else:         pts=[(x+cut,y),(x+w,y),(x+w,y+h),(x,y+h)]
        pygame.draw.polygon(self.screen,color,pts)
        return pts

    def _hp_bar(self,bx,by,bw,bh,cur,maxhp):
        pygame.draw.rect(self.screen,HP_BG,(bx-1,by-1,bw+2,bh+2))
        pct=cur/maxhp if maxhp>0 else 0
        fill=int(bw*pct)
        if fill>0:
            col=HP_GREEN if pct>0.5 else HP_YELLOW if pct>0.2 else HP_RED
            pygame.draw.rect(self.screen,col,(bx,by,fill,bh))
        pygame.draw.rect(self.screen,WHITE,(bx-1,by-1,bw+2,bh+2),1)

    def _hp_ai(self,poke):
        x,y,w,h,cut=AI_PNL
        self._trap(x+3,y+3,w,h,cut,'R',(24,28,18))
        pts=self._trap(x,y,w,h,cut,'R',PANEL_BG)
        pygame.draw.rect(self.screen,PANEL_HI,(x,y,w-cut-int(cut*28/h),28))
        pygame.draw.polygon(self.screen,PANEL_BDR,pts,2)
        self._t(poke.name.upper(),self.fn,WHITE,x+10,y+7,sh=BLACK)
        self._t("♂",self.fsm,(80,170,255),x+w-cut-32,y+7)
        self._t("L.50",self.fsm,WHITE,x+w-cut-24,y+24)
        self._t("PS",self.ftn,(190,215,170),x+10,y+46)
        self._hp_bar(x+30,y+48,w-cut-44,10,self._anim_ai,poke.get_max_hp())

    def _hp_pl(self,poke):
        x,y,w,h,cut=PL_PNL
        self._trap(x+3,y+3,w,h,cut,'L',(24,28,18))
        pts=self._trap(x,y,w,h,cut,'L',PANEL_BG)
        hi_start=x+cut-int(cut*30/h)
        pygame.draw.rect(self.screen,PANEL_HI,(hi_start,y,w-(hi_start-x),30))
        pygame.draw.polygon(self.screen,PANEL_BDR,pts,2)
        self._t(poke.name.upper(),self.fn,WHITE,x+cut+8,y+7,sh=BLACK)
        self._t("♀",self.fsm,(255,100,100),x+w-44,y+7)
        self._t("L.50",self.fsm,WHITE,x+w-36,y+24)
        if poke.status:
            BADGE={"burned":(250,100,50),"poisoned":(160,60,160),
                   "paralyzed":(240,200,30),"sleep":(140,140,200),"frozen":(100,210,250)}
            bc=BADGE.get(poke.status,GRAY)
            pygame.draw.rect(self.screen,bc,(x+cut+8,y+30,44,16),border_radius=4)
            self._t(poke.status[:3].upper(),self.ftn,WHITE,x+cut+12,y+32)
        self._t("PS",self.ftn,(190,215,170),x+cut+8,y+52)
        bar_w=w-cut-110
        self._hp_bar(x+cut+28,y+54,bar_w,10,self._anim_pl,poke.get_max_hp())
        hp_str=f"{max(0,poke.current_hp)}/{poke.get_max_hp()}"
        hs=self.fsm.render(hp_str,True,WHITE)
        self.screen.blit(hs,(x+w-hs.get_width()-8,y+54))
        ex=x+cut; ey=y+h-8; ew=w-cut
        pygame.draw.rect(self.screen,(20,20,20),(ex,ey,ew,6))
        pygame.draw.rect(self.screen,EXP_COL,(ex,ey,ew//2,6))
        pygame.draw.rect(self.screen,WHITE,(ex,ey,ew,6),1)

    # ── Bottom panel ─────────────────────────────────────────────────────────

    def _pokeball(self,cx,cy,r=9):
        pygame.draw.circle(self.screen,(220,48,48),(cx,cy),r)
        pygame.draw.rect(self.screen,WHITE,(cx-r,cy,r*2+1,r))
        pygame.draw.line(self.screen,BLACK,(cx-r,cy),(cx+r,cy),2)
        pygame.draw.circle(self.screen,BLACK,(cx,cy),r,2)
        pygame.draw.circle(self.screen,BLACK,(cx,cy),r//3+1)
        pygame.draw.circle(self.screen,WHITE,(cx,cy),r//3)

    def _bottom(self,pl):
        bdr=6
        pygame.draw.rect(self.screen,BTM_BG,(0,BOTTOM_Y,SCREEN_WIDTH,BOTTOM_H))
        pygame.draw.rect(self.screen,BTM_BDR,(0,BOTTOM_Y,SCREEN_WIDTH,BOTTOM_H),bdr)
        pygame.draw.rect(self.screen,(48,152,128),(bdr+2,BOTTOM_Y+bdr+2,
                          SCREEN_WIDTH-bdr*2-4,BOTTOM_H-bdr*2-4),2)
        off=bdr+11
        for bx,by in [(off,BOTTOM_Y+off),(SCREEN_WIDTH-off,BOTTOM_Y+off),
                      (off,SCREEN_HEIGHT-off),(SCREEN_WIDTH-off,SCREEN_HEIGHT-off)]:
            self._pokeball(bx,by)

        if self._waiting:
            # Show current event message + advance prompt
            self._draw_event_text(pl)
        elif self.battle_mode == "menu":
            self._menu_actions(pl)
        else:
            self._menu_fight(pl)

    def _draw_event_text(self, pl):
        """Show current event msg left, advance prompt bottom right."""
        msg = self._current_log_line()
        # Wrap into two lines of ~36 chars
        if len(msg) > 36:
            split = msg.rfind(" ", 0, 36)
            if split == -1: split = 36
            line1, line2 = msg[:split], msg[split:].strip()
        else:
            line1, line2 = msg, ""

        tx = 36; ty = BOTTOM_Y + BOTTOM_H//2 - 22
        self._t(line1, self.fn, BTM_TEXT, tx, ty)
        if line2:
            self._t(line2, self.fn, BTM_TEXT, tx, ty+34)

        # Blinking arrow
        if pygame.time.get_ticks() % 1000 < 600:
            arr = self.ftn.render("▼ Clicca o SPAZIO", True, GRAY)
            self.screen.blit(arr, (SCREEN_WIDTH-arr.get_width()-14, SCREEN_HEIGHT-20))

    def _menu_actions(self,pl):
        tx=36; ty=BOTTOM_Y+BOTTOM_H//2-28
        s=self.engine.state
        self._t("Cosa deve fare",self.fn,BTM_TEXT,tx,ty)
        self._t(f"{pl.name}?",self.fn,BTM_TEXT,tx,ty+36)
        labels=["LOTTA","ZAINO","POKÉMON","FUGA"]
        colors=[BTN_FIGHT,BTN_BAG,BTN_POKE,BTN_RUN]
        for i,((bx,by),lbl,col) in enumerate(zip(self._action_rects(),labels,colors)):
            btn=pygame.Rect(bx,by,238,68)
            pygame.draw.rect(self.screen,(20,20,20),btn.move(3,3),border_radius=10)
            pygame.draw.rect(self.screen,col,btn,border_radius=10)
            sh=pygame.Surface((btn.width-8,btn.height//3),pygame.SRCALPHA)
            sh.fill((255,255,255,38)); self.screen.blit(sh,(bx+4,by+4))
            pygame.draw.rect(self.screen,WHITE,btn,2,border_radius=10)
            ls=self.fn.render(lbl,True,WHITE)
            self.screen.blit(ls,(btn.centerx-ls.get_width()//2,btn.centery-ls.get_height()//2))

    def _menu_fight(self,pl):
        tx=36; ty=BOTTOM_Y+BOTTOM_H//2-24
        self._t("Scegli una",self.fn,BTM_TEXT,tx,ty)
        self._t("mossa:",self.fn,BTM_TEXT,tx,ty+36)
        esc=self.ftn.render("ESC = indietro",True,GRAY)
        self.screen.blit(esc,(tx,SCREEN_HEIGHT-20))
        for i,((bx,by),move) in enumerate(zip(self._fight_rects(),pl.moves[:4])):
            btn=pygame.Rect(bx,by,240,65)
            tc=get_type_color(move.type) if move.pp>0 else (72,72,72)
            pygame.draw.rect(self.screen,(20,20,20),btn.move(3,3),border_radius=10)
            pygame.draw.rect(self.screen,MOVE_BG,btn,border_radius=10)
            strip=pygame.Surface((6,btn.height-4)); strip.fill(tc)
            self.screen.blit(strip,(bx+2,by+2))
            bc=MOVE_SEL if i==self.selected_move else (88,88,72)
            bw=3 if i==self.selected_move else 2
            pygame.draw.rect(self.screen,bc,btn,bw,border_radius=10)
            self._t(move.name[:16],self.fn,BLACK,bx+14,by+7,sh=(200,200,188))
            pill=pygame.Rect(bx+14,by+38,66,18)
            pygame.draw.rect(self.screen,tc,pill,border_radius=8)
            tn=self.ftn.render(move.type[:7].upper(),True,WHITE)
            self.screen.blit(tn,(pill.centerx-tn.get_width()//2,pill.centery-tn.get_height()//2))
            pp=self.ftn.render(f"PP {move.pp}/{move.max_pp}",True,DARK_GRAY)
            self.screen.blit(pp,(bx+btn.width-pp.get_width()-8,by+40))

    def _dots(self):
        s=self.engine.state
        for i,p in enumerate(s.player_team):
            col=GREEN if not p.is_fainted() else RED
            cx,cy=30+i*22,SCREEN_HEIGHT-18
            pygame.draw.circle(self.screen,col,(cx,cy),7)
            pygame.draw.circle(self.screen,BLACK,(cx,cy),7,1)
            if i==s.player_active: pygame.draw.circle(self.screen,WHITE,(cx,cy),7,2)
        for i,p in enumerate(s.ai_team):
            col=GREEN if not p.is_fainted() else RED
            cx,cy=SCREEN_WIDTH-30-i*22,14
            pygame.draw.circle(self.screen,col,(cx,cy),7)
            pygame.draw.circle(self.screen,BLACK,(cx,cy),7,1)
            if i==s.ai_active: pygame.draw.circle(self.screen,WHITE,(cx,cy),7,2)

    def _game_over_screen(self,clock):
        pa=pygame.Rect(SCREEN_WIDTH//2-210,SCREEN_HEIGHT//2+40,200,60)
        quit=pygame.Rect(SCREEN_WIDTH//2+10,SCREEN_HEIGHT//2+40,200,60)
        while True:
            clock.tick(60)
            for event in pygame.event.get():
                if event.type==pygame.QUIT: return "quit"
                if event.type==pygame.MOUSEBUTTONDOWN:
                    if pa.collidepoint(event.pos):   return "play_again"
                    if quit.collidepoint(event.pos): return "quit"
            ov=pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT),pygame.SRCALPHA)
            ov.fill((0,0,0,210)); self.screen.blit(ov,(0,0))
            msg="VITTORIA!" if self.winner=="player" else "SCONFITTA!"
            col=(88,255,88) if self.winner=="player" else (255,88,88)
            mw=self.flg.size(msg)[0]
            self._t(msg,self.flg,col,SCREEN_WIDTH//2-mw//2,SCREEN_HEIGHT//2-80,sh=BLACK)
            for btn,txt,bc in [(pa,"Rigioca",GREEN),(quit,"Esci",RED)]:
                pygame.draw.rect(self.screen,DARK_GRAY,btn.move(4,4),border_radius=12)
                pygame.draw.rect(self.screen,bc,btn,border_radius=12)
                pygame.draw.rect(self.screen,WHITE,btn,3,border_radius=12)
                ls=self.fn.render(txt,True,WHITE)
                self.screen.blit(ls,(btn.centerx-ls.get_width()//2,btn.centery-ls.get_height()//2))
            pygame.display.flip()
