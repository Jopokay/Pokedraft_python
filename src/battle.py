import random
from typing import List, Optional

from pokemon import Pokemon, Move


TYPE_CHART = {
    ("Normal", "Rock"): 0.5, ("Normal", "Ghost"): 0, ("Normal", "Steel"): 0.5,
    ("Fire", "Fire"): 0.5, ("Fire", "Water"): 0.5, ("Fire", "Grass"): 2, ("Fire", "Ice"): 2,
    ("Fire", "Bug"): 2, ("Fire", "Rock"): 0.5, ("Fire", "Dragon"): 0.5, ("Fire", "Steel"): 2,
    ("Water", "Fire"): 2, ("Water", "Water"): 0.5, ("Water", "Grass"): 0.5, ("Water", "Ground"): 2,
    ("Water", "Rock"): 2, ("Water", "Dragon"): 0.5,
    ("Electric", "Water"): 2, ("Electric", "Electric"): 0.5, ("Electric", "Grass"): 0.5,
    ("Electric", "Ground"): 0, ("Electric", "Flying"): 2, ("Electric", "Dragon"): 0.5,
    ("Grass", "Fire"): 0.5, ("Grass", "Water"): 2, ("Grass", "Grass"): 0.5, ("Grass", "Poison"): 0.5,
    ("Grass", "Ground"): 2, ("Grass", "Flying"): 0.5, ("Grass", "Bug"): 0.5, ("Grass", "Rock"): 2,
    ("Grass", "Dragon"): 0.5, ("Grass", "Steel"): 0.5,
    ("Ice", "Fire"): 0.5, ("Ice", "Water"): 0.5, ("Ice", "Grass"): 2, ("Ice", "Ice"): 0.5,
    ("Ice", "Ground"): 2, ("Ice", "Flying"): 2, ("Ice", "Dragon"): 2, ("Ice", "Steel"): 0.5,
    ("Fighting", "Normal"): 2, ("Fighting", "Ice"): 2, ("Fighting", "Poison"): 0.5, ("Fighting", "Flying"): 0.5,
    ("Fighting", "Psychic"): 0.5, ("Fighting", "Bug"): 0.5, ("Fighting", "Rock"): 2, ("Fighting", "Ghost"): 0,
    ("Fighting", "Dark"): 2, ("Fighting", "Steel"): 2, ("Fighting", "Fairy"): 0.5,
    ("Poison", "Grass"): 2, ("Poison", "Poison"): 0.5, ("Poison", "Ground"): 0.5, ("Poison", "Rock"): 0.5,
    ("Poison", "Ghost"): 0.5, ("Poison", "Steel"): 0, ("Poison", "Fairy"): 2,
    ("Ground", "Fire"): 2, ("Ground", "Electric"): 2, ("Ground", "Grass"): 0.5, ("Ground", "Poison"): 2,
    ("Ground", "Flying"): 0, ("Ground", "Bug"): 0.5, ("Ground", "Rock"): 2, ("Ground", "Steel"): 2,
    ("Flying", "Electric"): 0.5, ("Flying", "Grass"): 2, ("Flying", "Fighting"): 2, ("Flying", "Bug"): 2,
    ("Flying", "Rock"): 0.5, ("Flying", "Steel"): 0.5,
    ("Psychic", "Fighting"): 2, ("Psychic", "Poison"): 2, ("Psychic", "Psychic"): 0.5, ("Psychic", "Dark"): 0,
    ("Psychic", "Steel"): 0.5,
    ("Bug", "Fire"): 0.5, ("Bug", "Grass"): 2, ("Bug", "Fighting"): 0.5, ("Bug", "Poison"): 0.5,
    ("Bug", "Flying"): 0.5, ("Bug", "Psychic"): 2, ("Bug", "Ghost"): 0.5, ("Bug", "Dark"): 2,
    ("Bug", "Steel"): 0.5, ("Bug", "Fairy"): 0.5,
    ("Rock", "Fire"): 2, ("Rock", "Ice"): 2, ("Rock", "Fighting"): 0.5, ("Rock", "Ground"): 0.5,
    ("Rock", "Flying"): 2, ("Rock", "Bug"): 2, ("Rock", "Steel"): 0.5,
    ("Ghost", "Normal"): 0, ("Ghost", "Psychic"): 2, ("Ghost", "Ghost"): 2, ("Ghost", "Dark"): 0.5,
    ("Dragon", "Dragon"): 2, ("Dragon", "Steel"): 0.5, ("Dragon", "Fairy"): 0,
    ("Steel", "Fire"): 0.5, ("Steel", "Water"): 0.5, ("Steel", "Electric"): 0.5, ("Steel", "Ice"): 2,
    ("Steel", "Rock"): 2, ("Steel", "Steel"): 0.5, ("Steel", "Fairy"): 2,
    ("Fairy", "Fire"): 0.5, ("Fairy", "Fighting"): 2, ("Fairy", "Poison"): 0.5, ("Fairy", "Dragon"): 2,
    ("Fairy", "Dark"): 2, ("Fairy", "Steel"): 0.5,
}


def get_type_effectiveness(move_type: str, target_types: List[str]) -> float:
    effectiveness = 1.0
    for target_type in target_types:
        effectiveness *= TYPE_CHART.get((move_type, target_type), 1.0)
    return effectiveness


class BattleState:
    def __init__(self, player_team: List[Pokemon], ai_team: List[Pokemon]):
        self.player_team = player_team
        self.ai_team = ai_team
        self.player_active = 0
        self.ai_active = 0
        self.turn = 1
        self.battle_log: List[str] = []
        self.game_over = False
        self.winner: Optional[str] = None
        # Faint animation state: set to "player" or "ai" while animating a KO
        self.pending_faint: Optional[str] = None

    def get_player_pokemon(self) -> Pokemon:
        return self.player_team[self.player_active]

    def get_ai_pokemon(self) -> Pokemon:
        return self.ai_team[self.ai_active]

    def add_log(self, message: str):
        self.battle_log.append(message)
        if len(self.battle_log) > 8:
            self.battle_log.pop(0)

    def next_alive(self, team: List[Pokemon], current: int) -> Optional[int]:
        """Return index of next alive pokemon after current, or None if all fainted."""
        for i in range(len(team)):
            if i != current and not team[i].is_fainted():
                return i
        return None

    def all_player_fainted(self) -> bool:
        return all(p.is_fainted() for p in self.player_team)

    def all_ai_fainted(self) -> bool:
        return all(p.is_fainted() for p in self.ai_team)

    def advance_player(self) -> bool:
        """Switch player to next alive pokemon. Returns True if switch happened."""
        nxt = self.next_alive(self.player_team, self.player_active)
        if nxt is not None:
            self.player_active = nxt
            self.add_log(f"Go, {self.player_team[nxt].name}!")
            return True
        return False

    def advance_ai(self) -> bool:
        """Switch AI to next alive pokemon. Returns True if switch happened."""
        nxt = self.next_alive(self.ai_team, self.ai_active)
        if nxt is not None:
            self.ai_active = nxt
            self.add_log(f"Foe sent out {self.ai_team[nxt].name}!")
            return True
        return False


class BattleEngine:
    def __init__(self, player_team: List[Pokemon], ai_team: List[Pokemon]):
        self.state = BattleState(player_team, ai_team)

    def calculate_damage(self, move: Move, attacker: Pokemon, defender: Pokemon) -> int:
        if move.power == 0:
            return 0
        level = attacker.level
        power = move.power
        if move.category == "Physical":
            atk = attacker.get_effective_stat("atk")
            if attacker.status == "burned":
                atk //= 2
            defense = defender.get_effective_stat("def")
        else:
            atk = attacker.get_effective_stat("spa")
            defense = defender.get_effective_stat("spd")
        stab = 1.5 if attacker.has_type(move.type) else 1.0
        effectiveness = get_type_effectiveness(move.type, defender.types)
        random_factor = random.uniform(0.85, 1.0)
        damage = ((2 * level / 5 + 2) * power * (atk / defense) / 50 + 2) * effectiveness * stab * random_factor
        return max(1, int(damage))

    def execute_move(self, move: Move, attacker: Pokemon, defender: Pokemon, attacker_name: str) -> str:
        if random.randint(1, 100) > move.accuracy:
            return f"{attacker_name}'s {move.name} missed!"
        damage = self.calculate_damage(move, attacker, defender)
        defender.take_damage(damage)
        result = f"{attacker_name} used {move.name}!"
        effectiveness = get_type_effectiveness(move.type, defender.types)
        if effectiveness > 1:
            result += " Super effective!"
        elif 0 < effectiveness < 1:
            result += " Not very effective..."
        elif effectiveness == 0:
            result += " No effect!"
        return result

    def process_status_turn(self, pokemon: Pokemon, name: str) -> List[str]:
        """Returns list of messages. Special sentinel 'skip' means pokemon can't move."""
        if pokemon.status == "poisoned":
            damage = pokemon.get_max_hp() // 8
            pokemon.take_damage(damage)
            return [f"{name} is hurt by poison!"]
        elif pokemon.status == "burned":
            damage = pokemon.get_max_hp() // 8
            pokemon.take_damage(damage)
            return [f"{name} is hurt by its burn!"]
        elif pokemon.status == "paralyzed":
            if random.random() < 0.25:
                return ["skip", f"{name} is paralyzed and can't move!"]
        elif pokemon.status == "sleep":
            pokemon.sleep_turns -= 1
            if pokemon.sleep_turns <= 0:
                pokemon.status = None
                return [f"{name} woke up!"]
            else:
                return ["skip", f"{name} is fast asleep!"]
        return []

    def get_ai_move(self) -> Move:
        ai_pokemon = self.state.get_ai_pokemon()
        player_pokemon = self.state.get_player_pokemon()
        if random.random() < 0.2:
            return random.choice(ai_pokemon.moves)
        best_move = ai_pokemon.moves[0]
        best_score = -1
        for move in ai_pokemon.moves:
            if move.power == 0:
                score = 10
            else:
                damage = self.calculate_damage(move, ai_pokemon, player_pokemon)
                score = damage * get_type_effectiveness(move.type, player_pokemon.types)
                if ai_pokemon.has_type(move.type):
                    score *= 1.5
            if score > best_score:
                best_score = score
                best_move = move
        return best_move

    def _handle_faint(self, who: str):
        """Log the faint and advance to next pokemon. Sets game_over if team wiped."""
        s = self.state
        if who == "player":
            s.add_log(f"{s.get_player_pokemon().name} fainted!")
            if s.all_player_fainted():
                s.game_over = True
                s.winner = "ai"
                s.add_log("You lost!")
            else:
                s.advance_player()
        else:
            s.add_log(f"{s.get_ai_pokemon().name} fainted!")
            if s.all_ai_fainted():
                s.game_over = True
                s.winner = "player"
                s.add_log("You won!")
            else:
                s.advance_ai()

    def process_turn(self, player_move_index: int, ai_move_index: int):
        s = self.state
        player = s.get_player_pokemon()
        ai = s.get_ai_pokemon()

        player_move = player.moves[min(player_move_index, len(player.moves) - 1)]
        ai_move = ai.moves[min(ai_move_index, len(ai.moves) - 1)]

        # Determine turn order by speed
        p_speed = player.get_effective_stat("spe") // (2 if player.status == "paralyzed" else 1)
        a_speed = ai.get_effective_stat("spe") // (2 if ai.status == "paralyzed" else 1)

        if p_speed >= a_speed:
            order = [("player", player, player_move, ai),
                     ("ai",     ai,     ai_move,     player)]
        else:
            order = [("ai",     ai,     ai_move,     player),
                     ("player", player, player_move, ai)]

        for attacker_side, attacker, move, defender in order:
            # Skip if attacker already fainted (e.g. died to poison this turn)
            if attacker.is_fainted():
                continue

            defender_side = "ai" if attacker_side == "player" else "player"
            attacker_name = attacker.name if attacker_side == "player" else f"Foe {attacker.name}"

            # Status pre-move check
            status_msgs = self.process_status_turn(attacker, attacker_name)
            skip = False
            for msg in status_msgs:
                if msg == "skip":
                    skip = True
                else:
                    s.add_log(msg)

            # Check if attacker fainted from status damage
            if attacker.is_fainted():
                self._handle_faint(attacker_side)
                if s.game_over:
                    return
                continue

            if skip:
                continue

            # Execute the move
            result = self.execute_move(move, attacker, defender, attacker_name)
            s.add_log(result)

            # Reduce PP
            move.pp = max(0, move.pp - 1)

            # Check if defender fainted
            if defender.is_fainted():
                self._handle_faint(defender_side)
                if s.game_over:
                    return
                # Don't break — the other pokemon may still attack next

        s.turn += 1
import random
from typing import List, Optional

from pokemon import Pokemon, Move


TYPE_CHART = {
    ("Normal", "Rock"): 0.5, ("Normal", "Ghost"): 0, ("Normal", "Steel"): 0.5,
    ("Fire", "Fire"): 0.5, ("Fire", "Water"): 0.5, ("Fire", "Grass"): 2, ("Fire", "Ice"): 2,
    ("Fire", "Bug"): 2, ("Fire", "Rock"): 0.5, ("Fire", "Dragon"): 0.5, ("Fire", "Steel"): 2,
    ("Water", "Fire"): 2, ("Water", "Water"): 0.5, ("Water", "Grass"): 0.5, ("Water", "Ground"): 2,
    ("Water", "Rock"): 2, ("Water", "Dragon"): 0.5,
    ("Electric", "Water"): 2, ("Electric", "Electric"): 0.5, ("Electric", "Grass"): 0.5,
    ("Electric", "Ground"): 0, ("Electric", "Flying"): 2, ("Electric", "Dragon"): 0.5,
    ("Grass", "Fire"): 0.5, ("Grass", "Water"): 2, ("Grass", "Grass"): 0.5, ("Grass", "Poison"): 0.5,
    ("Grass", "Ground"): 2, ("Grass", "Flying"): 0.5, ("Grass", "Bug"): 0.5, ("Grass", "Rock"): 2,
    ("Grass", "Dragon"): 0.5, ("Grass", "Steel"): 0.5,
    ("Ice", "Fire"): 0.5, ("Ice", "Water"): 0.5, ("Ice", "Grass"): 2, ("Ice", "Ice"): 0.5,
    ("Ice", "Ground"): 2, ("Ice", "Flying"): 2, ("Ice", "Dragon"): 2, ("Ice", "Steel"): 0.5,
    ("Fighting", "Normal"): 2, ("Fighting", "Ice"): 2, ("Fighting", "Poison"): 0.5, ("Fighting", "Flying"): 0.5,
    ("Fighting", "Psychic"): 0.5, ("Fighting", "Bug"): 0.5, ("Fighting", "Rock"): 2, ("Fighting", "Ghost"): 0,
    ("Fighting", "Dark"): 2, ("Fighting", "Steel"): 2, ("Fighting", "Fairy"): 0.5,
    ("Poison", "Grass"): 2, ("Poison", "Poison"): 0.5, ("Poison", "Ground"): 0.5, ("Poison", "Rock"): 0.5,
    ("Poison", "Ghost"): 0.5, ("Poison", "Steel"): 0, ("Poison", "Fairy"): 2,
    ("Ground", "Fire"): 2, ("Ground", "Electric"): 2, ("Ground", "Grass"): 0.5, ("Ground", "Poison"): 2,
    ("Ground", "Flying"): 0, ("Ground", "Bug"): 0.5, ("Ground", "Rock"): 2, ("Ground", "Steel"): 2,
    ("Flying", "Electric"): 0.5, ("Flying", "Grass"): 2, ("Flying", "Fighting"): 2, ("Flying", "Bug"): 2,
    ("Flying", "Rock"): 0.5, ("Flying", "Steel"): 0.5,
    ("Psychic", "Fighting"): 2, ("Psychic", "Poison"): 2, ("Psychic", "Psychic"): 0.5, ("Psychic", "Dark"): 0,
    ("Psychic", "Steel"): 0.5,
    ("Bug", "Fire"): 0.5, ("Bug", "Grass"): 2, ("Bug", "Fighting"): 0.5, ("Bug", "Poison"): 0.5,
    ("Bug", "Flying"): 0.5, ("Bug", "Psychic"): 2, ("Bug", "Ghost"): 0.5, ("Bug", "Dark"): 2,
    ("Bug", "Steel"): 0.5, ("Bug", "Fairy"): 0.5,
    ("Rock", "Fire"): 2, ("Rock", "Ice"): 2, ("Rock", "Fighting"): 0.5, ("Rock", "Ground"): 0.5,
    ("Rock", "Flying"): 2, ("Rock", "Bug"): 2, ("Rock", "Steel"): 0.5,
    ("Ghost", "Normal"): 0, ("Ghost", "Psychic"): 2, ("Ghost", "Ghost"): 2, ("Ghost", "Dark"): 0.5,
    ("Dragon", "Dragon"): 2, ("Dragon", "Steel"): 0.5, ("Dragon", "Fairy"): 0,
    ("Steel", "Fire"): 0.5, ("Steel", "Water"): 0.5, ("Steel", "Electric"): 0.5, ("Steel", "Ice"): 2,
    ("Steel", "Rock"): 2, ("Steel", "Steel"): 0.5, ("Steel", "Fairy"): 2,
    ("Fairy", "Fire"): 0.5, ("Fairy", "Fighting"): 2, ("Fairy", "Poison"): 0.5, ("Fairy", "Dragon"): 2,
    ("Fairy", "Dark"): 2, ("Fairy", "Steel"): 0.5,
}


def get_type_effectiveness(move_type: str, target_types: List[str]) -> float:
    effectiveness = 1.0
    for target_type in target_types:
        effectiveness *= TYPE_CHART.get((move_type, target_type), 1.0)
    return effectiveness


class BattleState:
    def __init__(self, player_team: List[Pokemon], ai_team: List[Pokemon]):
        self.player_team = player_team
        self.ai_team = ai_team
        self.player_active = 0
        self.ai_active = 0
        self.turn = 1
        self.battle_log: List[str] = []
        self.game_over = False
        self.winner: Optional[str] = None
        # Faint animation state: set to "player" or "ai" while animating a KO
        self.pending_faint: Optional[str] = None

    def get_player_pokemon(self) -> Pokemon:
        return self.player_team[self.player_active]

    def get_ai_pokemon(self) -> Pokemon:
        return self.ai_team[self.ai_active]

    def add_log(self, message: str):
        self.battle_log.append(message)
        if len(self.battle_log) > 8:
            self.battle_log.pop(0)

    def next_alive(self, team: List[Pokemon], current: int) -> Optional[int]:
        """Return index of next alive pokemon after current, or None if all fainted."""
        for i in range(len(team)):
            if i != current and not team[i].is_fainted():
                return i
        return None

    def all_player_fainted(self) -> bool:
        return all(p.is_fainted() for p in self.player_team)

    def all_ai_fainted(self) -> bool:
        return all(p.is_fainted() for p in self.ai_team)

    def advance_player(self) -> bool:
        """Switch player to next alive pokemon. Returns True if switch happened."""
        nxt = self.next_alive(self.player_team, self.player_active)
        if nxt is not None:
            self.player_active = nxt
            self.add_log(f"Go, {self.player_team[nxt].name}!")
            return True
        return False

    def advance_ai(self) -> bool:
        """Switch AI to next alive pokemon. Returns True if switch happened."""
        nxt = self.next_alive(self.ai_team, self.ai_active)
        if nxt is not None:
            self.ai_active = nxt
            self.add_log(f"Foe sent out {self.ai_team[nxt].name}!")
            return True
        return False


class BattleEngine:
    def __init__(self, player_team: List[Pokemon], ai_team: List[Pokemon]):
        self.state = BattleState(player_team, ai_team)

    def calculate_damage(self, move: Move, attacker: Pokemon, defender: Pokemon) -> int:
        if move.power == 0:
            return 0
        level = attacker.level
        power = move.power
        if move.category == "Physical":
            atk = attacker.get_effective_stat("atk")
            if attacker.status == "burned":
                atk //= 2
            defense = defender.get_effective_stat("def")
        else:
            atk = attacker.get_effective_stat("spa")
            defense = defender.get_effective_stat("spd")
        stab = 1.5 if attacker.has_type(move.type) else 1.0
        effectiveness = get_type_effectiveness(move.type, defender.types)
        random_factor = random.uniform(0.85, 1.0)
        damage = ((2 * level / 5 + 2) * power * (atk / defense) / 50 + 2) * effectiveness * stab * random_factor
        return max(1, int(damage))

    def execute_move(self, move: Move, attacker: Pokemon, defender: Pokemon, attacker_name: str) -> str:
        if random.randint(1, 100) > move.accuracy:
            return f"{attacker_name}'s {move.name} missed!"
        damage = self.calculate_damage(move, attacker, defender)
        defender.take_damage(damage)
        result = f"{attacker_name} used {move.name}!"
        effectiveness = get_type_effectiveness(move.type, defender.types)
        if effectiveness > 1:
            result += " Super effective!"
        elif 0 < effectiveness < 1:
            result += " Not very effective..."
        elif effectiveness == 0:
            result += " No effect!"
        return result

    def process_status_turn(self, pokemon: Pokemon, name: str) -> List[str]:
        """Returns list of messages. Special sentinel 'skip' means pokemon can't move."""
        if pokemon.status == "poisoned":
            damage = pokemon.get_max_hp() // 8
            pokemon.take_damage(damage)
            return [f"{name} is hurt by poison!"]
        elif pokemon.status == "burned":
            damage = pokemon.get_max_hp() // 8
            pokemon.take_damage(damage)
            return [f"{name} is hurt by its burn!"]
        elif pokemon.status == "paralyzed":
            if random.random() < 0.25:
                return ["skip", f"{name} is paralyzed and can't move!"]
        elif pokemon.status == "sleep":
            pokemon.sleep_turns -= 1
            if pokemon.sleep_turns <= 0:
                pokemon.status = None
                return [f"{name} woke up!"]
            else:
                return ["skip", f"{name} is fast asleep!"]
        return []

    def get_ai_move(self) -> Move:
        ai_pokemon = self.state.get_ai_pokemon()
        player_pokemon = self.state.get_player_pokemon()
        if random.random() < 0.2:
            return random.choice(ai_pokemon.moves)
        best_move = ai_pokemon.moves[0]
        best_score = -1
        for move in ai_pokemon.moves:
            if move.power == 0:
                score = 10
            else:
                damage = self.calculate_damage(move, ai_pokemon, player_pokemon)
                score = damage * get_type_effectiveness(move.type, player_pokemon.types)
                if ai_pokemon.has_type(move.type):
                    score *= 1.5
            if score > best_score:
                best_score = score
                best_move = move
        return best_move

    def _handle_faint(self, who: str):
        """Log the faint and advance to next pokemon. Sets game_over if team wiped."""
        s = self.state
        if who == "player":
            s.add_log(f"{s.get_player_pokemon().name} fainted!")
            if s.all_player_fainted():
                s.game_over = True
                s.winner = "ai"
                s.add_log("You lost!")
            else:
                s.advance_player()
        else:
            s.add_log(f"{s.get_ai_pokemon().name} fainted!")
            if s.all_ai_fainted():
                s.game_over = True
                s.winner = "player"
                s.add_log("You won!")
            else:
                s.advance_ai()

    def process_turn(self, player_move_index: int, ai_move_index: int):
        s = self.state
        player = s.get_player_pokemon()
        ai = s.get_ai_pokemon()

        player_move = player.moves[min(player_move_index, len(player.moves) - 1)]
        ai_move = ai.moves[min(ai_move_index, len(ai.moves) - 1)]

        # Determine turn order by speed
        p_speed = player.get_effective_stat("spe") // (2 if player.status == "paralyzed" else 1)
        a_speed = ai.get_effective_stat("spe") // (2 if ai.status == "paralyzed" else 1)

        if p_speed >= a_speed:
            order = [("player", player, player_move, ai),
                     ("ai",     ai,     ai_move,     player)]
        else:
            order = [("ai",     ai,     ai_move,     player),
                     ("player", player, player_move, ai)]

        for attacker_side, attacker, move, defender in order:
            # Skip if attacker already fainted (e.g. died to poison this turn)
            if attacker.is_fainted():
                continue

            defender_side = "ai" if attacker_side == "player" else "player"
            attacker_name = attacker.name if attacker_side == "player" else f"Foe {attacker.name}"

            # Status pre-move check
            status_msgs = self.process_status_turn(attacker, attacker_name)
            skip = False
            for msg in status_msgs:
                if msg == "skip":
                    skip = True
                else:
                    s.add_log(msg)

            # Check if attacker fainted from status damage
            if attacker.is_fainted():
                self._handle_faint(attacker_side)
                if s.game_over:
                    return
                continue

            if skip:
                continue

            # Execute the move
            result = self.execute_move(move, attacker, defender, attacker_name)
            s.add_log(result)

            # Reduce PP
            move.pp = max(0, move.pp - 1)

            # Check if defender fainted
            if defender.is_fainted():
                self._handle_faint(defender_side)
                if s.game_over:
                    return
                # Don't break — the other pokemon may still attack next

        s.turn += 1
