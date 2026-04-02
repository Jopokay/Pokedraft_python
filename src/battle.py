import random
from dataclasses import dataclass, field
from typing import List, Optional

from pokemon import Pokemon, Move


# ── Type chart ────────────────────────────────────────────────────────────────
TYPE_CHART = {
    ("Normal","Rock"):0.5,("Normal","Ghost"):0,("Normal","Steel"):0.5,
    ("Fire","Fire"):0.5,("Fire","Water"):0.5,("Fire","Grass"):2,("Fire","Ice"):2,
    ("Fire","Bug"):2,("Fire","Rock"):0.5,("Fire","Dragon"):0.5,("Fire","Steel"):2,
    ("Water","Fire"):2,("Water","Water"):0.5,("Water","Grass"):0.5,("Water","Ground"):2,
    ("Water","Rock"):2,("Water","Dragon"):0.5,
    ("Electric","Water"):2,("Electric","Electric"):0.5,("Electric","Grass"):0.5,
    ("Electric","Ground"):0,("Electric","Flying"):2,("Electric","Dragon"):0.5,
    ("Grass","Fire"):0.5,("Grass","Water"):2,("Grass","Grass"):0.5,("Grass","Poison"):0.5,
    ("Grass","Ground"):2,("Grass","Flying"):0.5,("Grass","Bug"):0.5,("Grass","Rock"):2,
    ("Grass","Dragon"):0.5,("Grass","Steel"):0.5,
    ("Ice","Fire"):0.5,("Ice","Water"):0.5,("Ice","Grass"):2,("Ice","Ice"):0.5,
    ("Ice","Ground"):2,("Ice","Flying"):2,("Ice","Dragon"):2,("Ice","Steel"):0.5,
    ("Fighting","Normal"):2,("Fighting","Ice"):2,("Fighting","Poison"):0.5,
    ("Fighting","Flying"):0.5,("Fighting","Psychic"):0.5,("Fighting","Bug"):0.5,
    ("Fighting","Rock"):2,("Fighting","Ghost"):0,("Fighting","Dark"):2,
    ("Fighting","Steel"):2,("Fighting","Fairy"):0.5,
    ("Poison","Grass"):2,("Poison","Poison"):0.5,("Poison","Ground"):0.5,
    ("Poison","Rock"):0.5,("Poison","Ghost"):0.5,("Poison","Steel"):0,("Poison","Fairy"):2,
    ("Ground","Fire"):2,("Ground","Electric"):2,("Ground","Grass"):0.5,("Ground","Poison"):2,
    ("Ground","Flying"):0,("Ground","Bug"):0.5,("Ground","Rock"):2,("Ground","Steel"):2,
    ("Flying","Electric"):0.5,("Flying","Grass"):2,("Flying","Fighting"):2,
    ("Flying","Bug"):2,("Flying","Rock"):0.5,("Flying","Steel"):0.5,
    ("Psychic","Fighting"):2,("Psychic","Poison"):2,("Psychic","Psychic"):0.5,
    ("Psychic","Dark"):0,("Psychic","Steel"):0.5,
    ("Bug","Fire"):0.5,("Bug","Grass"):2,("Bug","Fighting"):0.5,("Bug","Poison"):0.5,
    ("Bug","Flying"):0.5,("Bug","Psychic"):2,("Bug","Ghost"):0.5,("Bug","Dark"):2,
    ("Bug","Steel"):0.5,("Bug","Fairy"):0.5,
    ("Rock","Fire"):2,("Rock","Ice"):2,("Rock","Fighting"):0.5,("Rock","Ground"):0.5,
    ("Rock","Flying"):2,("Rock","Bug"):2,("Rock","Steel"):0.5,
    ("Ghost","Normal"):0,("Ghost","Psychic"):2,("Ghost","Ghost"):2,("Ghost","Dark"):0.5,
    ("Dragon","Dragon"):2,("Dragon","Steel"):0.5,("Dragon","Fairy"):0,
    ("Steel","Fire"):0.5,("Steel","Water"):0.5,("Steel","Electric"):0.5,("Steel","Ice"):2,
    ("Steel","Rock"):2,("Steel","Steel"):0.5,("Steel","Fairy"):2,
    ("Fairy","Fire"):0.5,("Fairy","Fighting"):2,("Fairy","Poison"):0.5,
    ("Fairy","Dragon"):2,("Fairy","Dark"):2,("Fairy","Steel"):0.5,
}


def get_type_effectiveness(move_type: str, target_types: List[str]) -> float:
    eff = 1.0
    for t in target_types:
        eff *= TYPE_CHART.get((move_type, t), 1.0)
    return eff


# ── TurnEvent ─────────────────────────────────────────────────────────────────

@dataclass
class TurnEvent:
    """
    One step in a battle turn, shown one at a time in the UI.

    msg           - text to display in the log box
    move_type     - type string of the move used (for sound), "" if N/A
    damage_side   - "player" or "ai": who takes damage after this msg is shown
    damage        - HP to subtract from damage_side
    crit          - was it a critical hit?
    effectiveness - float (for "super effective!" etc.)
    faint_side    - "player" or "ai" if someone faints after damage applied
    game_over     - True if battle ends after this event
    winner        - "player" or "ai" if game_over
    switch_msg    - message for new pokemon entering after faint (appended automatically)
    """
    msg:           str
    move_type:     str   = ""
    damage_side:   str   = ""
    damage:        int   = 0
    crit:          bool  = False
    effectiveness: float = 1.0
    faint_side:    str   = ""
    game_over:     bool  = False
    winner:        str   = ""


# ── BattleState ───────────────────────────────────────────────────────────────

class BattleState:
    def __init__(self, player_team: List[Pokemon], ai_team: List[Pokemon]):
        self.player_team   = player_team
        self.ai_team       = ai_team
        self.player_active = 0
        self.ai_active     = 0
        self.turn          = 1
        self.battle_log: List[str] = []
        self.game_over     = False
        self.winner: Optional[str] = None

    def get_player_pokemon(self) -> Pokemon:
        return self.player_team[self.player_active]

    def get_ai_pokemon(self) -> Pokemon:
        return self.ai_team[self.ai_active]

    def add_log(self, msg: str):
        self.battle_log.append(msg)
        if len(self.battle_log) > 10:
            self.battle_log.pop(0)

    def next_alive(self, team, current) -> Optional[int]:
        for i in range(len(team)):
            if i != current and not team[i].is_fainted():
                return i
        return None

    def all_player_fainted(self) -> bool:
        return all(p.is_fainted() for p in self.player_team)

    def all_ai_fainted(self) -> bool:
        return all(p.is_fainted() for p in self.ai_team)


# ── BattleEngine ──────────────────────────────────────────────────────────────

class BattleEngine:
    def __init__(self, player_team: List[Pokemon], ai_team: List[Pokemon]):
        self.state = BattleState(player_team, ai_team)

    # ── damage calc ───────────────────────────────────────────────────────────

    def calculate_damage(self, move: Move, attacker: Pokemon,
                         defender: Pokemon) -> tuple[int, bool]:
        """Returns (damage, is_crit)."""
        if move.power == 0:
            return 0, False
        level = attacker.level
        if move.category == "Physical":
            atk = attacker.get_effective_stat("atk")
            if attacker.status == "burned":
                atk //= 2
            dfn = defender.get_effective_stat("def")
        else:
            atk = attacker.get_effective_stat("spa")
            dfn = defender.get_effective_stat("spd")

        stab        = 1.5 if attacker.has_type(move.type) else 1.0
        eff         = get_type_effectiveness(move.type, defender.types)
        rand        = random.uniform(0.85, 1.0)
        crit        = random.random() < 0.0625   # 1/16 crit chance
        crit_mult   = 1.5 if crit else 1.0
        dmg = ((2*level/5 + 2) * move.power * (atk/dfn) / 50 + 2) * eff * stab * rand * crit_mult
        return max(1, int(dmg)), crit

    # ── AI move choice ────────────────────────────────────────────────────────

    def get_ai_move(self) -> Move:
        ai  = self.state.get_ai_pokemon()
        pl  = self.state.get_player_pokemon()
        if random.random() < 0.15:
            return random.choice(ai.moves)
        best, best_score = ai.moves[0], -1
        for m in ai.moves:
            if m.pp <= 0:
                continue
            dmg, _ = self.calculate_damage(m, ai, pl)
            score  = dmg * get_type_effectiveness(m.type, pl.types)
            if ai.has_type(m.type):
                score *= 1.5
            if score > best_score:
                best_score, best = score, m
        return best

    # ── process_turn  →  List[TurnEvent] ─────────────────────────────────────
    #
    #  This method builds a complete list of events for the whole turn, each
    #  event representing ONE thing the player needs to read before advancing.
    #  It also mutates the state (HP, status, active index) so the HP bars
    #  start animating immediately as each event is applied by the UI.
    #
    #  The UI calls apply_event(event) after showing each message to actually
    #  commit the HP/faint changes.  This gives us step-by-step animation.
    # ─────────────────────────────────────────────────────────────────────────

    def build_turn_events(self, player_move_idx: int, ai_move_idx: int) -> List[TurnEvent]:
        s      = self.state
        player = s.get_player_pokemon()
        ai     = s.get_ai_pokemon()

        # Guard against out-of-range move index
        player_move = player.moves[min(player_move_idx, len(player.moves)-1)]
        ai_move     = ai.moves[min(ai_move_idx, len(ai.moves)-1)]

        # Speed order (paralysis halves speed)
        p_spd = player.get_effective_stat("spe") // (2 if player.status == "paralyzed" else 1)
        a_spd = ai.get_effective_stat("spe")     // (2 if ai.status == "paralyzed" else 1)

        if p_spd >= a_spd:
            order = [("player", player, player_move, "ai",     ai),
                     ("ai",     ai,     ai_move,     "player", player)]
        else:
            order = [("ai",     ai,     ai_move,     "player", player),
                     ("player", player, player_move, "ai",     ai)]

        events: List[TurnEvent] = []

        for att_side, attacker, move, def_side, defender in order:
            if attacker.is_fainted():
                continue

            att_name = attacker.name if att_side == "player" else f"Avversario {attacker.name}"
            def_name = defender.name if def_side == "player" else f"Avversario {defender.name}"

            # ── Status pre-move ────────────────────────────────────────
            skip = False
            if attacker.status == "poisoned":
                dmg = attacker.get_max_hp() // 8
                attacker.take_damage(dmg)
                ev = TurnEvent(msg=f"{att_name} soffre per il veleno!",
                               damage_side=att_side, damage=dmg)
                if attacker.is_fainted():
                    ev, events = self._apply_faint(ev, att_side, s, events)
                    if s.game_over:
                        return events
                events.append(ev)
                if attacker.is_fainted():
                    continue

            elif attacker.status == "burned":
                dmg = attacker.get_max_hp() // 8
                attacker.take_damage(dmg)
                ev = TurnEvent(msg=f"{att_name} soffre per la bruciatura!",
                               damage_side=att_side, damage=dmg)
                if attacker.is_fainted():
                    ev, events = self._apply_faint(ev, att_side, s, events)
                    if s.game_over:
                        return events
                events.append(ev)
                if attacker.is_fainted():
                    continue

            elif attacker.status == "paralyzed" and random.random() < 0.25:
                events.append(TurnEvent(msg=f"{att_name} è paralizzato e non riesce a muoversi!"))
                skip = True

            elif attacker.status == "sleep":
                attacker.sleep_turns -= 1
                if attacker.sleep_turns <= 0:
                    attacker.status = None
                    events.append(TurnEvent(msg=f"{att_name} si è svegliato!"))
                else:
                    events.append(TurnEvent(msg=f"{att_name} sta dormendo profondamente!"))
                    skip = True

            if skip:
                continue

            # ── Move execution ─────────────────────────────────────────
            if move.pp <= 0:
                # Struggle fallback
                events.append(TurnEvent(msg=f"{att_name} non ha più PP! Usa Lotta!",
                                        move_type="Normal"))
                dmg = max(1, attacker.get_effective_stat("atk") // 4)
                attacker.take_damage(dmg // 4)  # recoil
                defender.take_damage(dmg)
                ev = TurnEvent(msg=f"{att_name} usa Lotta!",
                               move_type="Normal",
                               damage_side=def_side, damage=dmg,
                               effectiveness=1.0)
                if defender.is_fainted():
                    ev, events = self._apply_faint(ev, def_side, s, events)
                    if s.game_over:
                        return events
                events.append(ev)
                continue

            # Miss check
            if random.randint(1, 100) > move.accuracy:
                events.append(TurnEvent(
                    msg=f"{att_name} usa {move.name}... ma manca!",
                    move_type=move.type))
                move.pp = max(0, move.pp - 1)
                continue

            # Reduce PP
            move.pp = max(0, move.pp - 1)

            # Status moves (power == 0)
            if move.power == 0:
                status_ev = self._handle_status_move(move, attacker, defender,
                                                     att_name, def_name, def_side)
                events.extend(status_ev)
                continue

            # Damage
            dmg, crit = self.calculate_damage(move, attacker, defender)
            eff       = get_type_effectiveness(move.type, defender.types)

            # "X usa Y!"  event — no HP change yet, just the animation trigger
            use_ev = TurnEvent(
                msg=f"{att_name} usa {move.name}!",
                move_type=move.type,
                damage_side=def_side,
                damage=dmg,
                crit=crit,
                effectiveness=eff,
            )

            # Immediately apply HP to trigger bar animation
            defender.take_damage(dmg)

            # Effectiveness message event (separate step)
            if crit:
                events.append(use_ev)
                events.append(TurnEvent(msg="Colpo critico!"))
            else:
                events.append(use_ev)

            if eff > 1.5:
                events.append(TurnEvent(msg="È superefficace!"))
            elif 0 < eff < 0.9:
                events.append(TurnEvent(msg="Non è molto efficace..."))
            elif eff == 0:
                events.append(TurnEvent(msg="Non ha effetto!"))
                continue

            # Faint check
            if defender.is_fainted():
                faint_ev = TurnEvent(msg=f"{def_name} è esausto!")
                faint_ev, events = self._apply_faint(faint_ev, def_side, s, events)
                events.append(faint_ev)
                if s.game_over:
                    return events

        s.turn += 1
        return events

    # ── faint helper ──────────────────────────────────────────────────────────

    def _apply_faint(self, ev: TurnEvent, faint_side: str,
                     s: BattleState, events: List[TurnEvent]) -> tuple:
        """Set faint_side on ev, advance team, attach game_over / winner."""
        ev.faint_side = faint_side
        if faint_side == "player":
            if s.all_player_fainted():
                ev.game_over = True
                ev.winner    = "ai"
                s.game_over  = True
                s.winner     = "ai"
            else:
                nxt = s.next_alive(s.player_team, s.player_active)
                if nxt is not None:
                    s.player_active = nxt
                    events.append(ev)
                    return TurnEvent(msg=f"Vai, {s.player_team[nxt].name}!"), events
        else:
            if s.all_ai_fainted():
                ev.game_over = True
                ev.winner    = "player"
                s.game_over  = True
                s.winner     = "player"
            else:
                nxt = s.next_alive(s.ai_team, s.ai_active)
                if nxt is not None:
                    s.ai_active = nxt
                    events.append(ev)
                    return TurnEvent(msg=f"L'avversario manda {s.ai_team[nxt].name}!"), events
        return ev, events

    # ── status move handler ───────────────────────────────────────────────────

    def _handle_status_move(self, move, attacker, defender,
                             att_name, def_name, def_side) -> List[TurnEvent]:
        evs: List[TurnEvent] = []
        evs.append(TurnEvent(msg=f"{att_name} usa {move.name}!", move_type=move.type))

        name_lower = move.name.lower()

        # Sleep moves
        if "powder" in name_lower or "spore" in name_lower or name_lower in ("hypnosis","sing","lovely-kiss","yawn"):
            if defender.status is None:
                defender.status = "sleep"
                defender.sleep_turns = random.randint(1, 3)
                evs.append(TurnEvent(msg=f"{def_name} si è addormentato!"))
            else:
                evs.append(TurnEvent(msg="Non ha avuto effetto!"))

        # Poison
        elif "poison" in name_lower or name_lower in ("toxic","sludge","sludge-bomb","venoshock"):
            if defender.status is None:
                defender.status = "poisoned"
                evs.append(TurnEvent(msg=f"{def_name} è stato avvelenato!"))
            else:
                evs.append(TurnEvent(msg="Non ha avuto effetto!"))

        # Burn (Will-O-Wisp etc.)
        elif "will-o" in name_lower or "ember" in name_lower:
            if defender.status is None and "Fire" not in defender.types:
                defender.status = "burned"
                evs.append(TurnEvent(msg=f"{def_name} si è scottato!"))

        # Paralysis
        elif "thunder-wave" in name_lower or "stun" in name_lower or "glare" in name_lower:
            if defender.status is None:
                defender.status = "paralyzed"
                evs.append(TurnEvent(msg=f"{def_name} è paralizzato!"))

        # Healing
        elif name_lower in ("rest","recover","softboiled","moonlight","synthesis","morning-sun"):
            heal = attacker.get_max_hp() // 2
            attacker.heal(heal)
            evs.append(TurnEvent(msg=f"{att_name} si è ripreso!"))

        else:
            evs.append(TurnEvent(msg=f"Non sembra aver fatto molto..."))

        return evs

    # ── legacy-compat wrapper ─────────────────────────────────────────────────

    def process_turn(self, player_move_idx: int, ai_move_idx: int) -> List[TurnEvent]:
        """Alias kept for compatibility. Returns event list."""
        return self.build_turn_events(player_move_idx, ai_move_idx)
