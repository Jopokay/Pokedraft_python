import random
from typing import List, Dict, Tuple, Optional

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
TYPE_CHART_DEFAULT = 1.0


def get_type_effectiveness(move_type: str, target_types: List[str]) -> float:
    effectiveness = 1.0
    for target_type in target_types:
        key = (move_type, target_type)
        effectiveness *= TYPE_CHART.get(key, TYPE_CHART_DEFAULT)
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

    def get_player_pokemon(self) -> Pokemon:
        return self.player_team[self.player_active]

    def get_ai_pokemon(self) -> Pokemon:
        return self.ai_team[self.ai_active]

    def is_player_fainted(self) -> bool:
        return self.get_player_pokemon().is_fainted()

    def is_ai_fainted(self) -> bool:
        return self.get_ai_pokemon().is_fainted()

    def check_faints(self) -> Optional[str]:
        if self.is_player_fainted():
            return "player"
        if self.is_ai_fainted():
            return "ai"
        return None

    def add_log(self, message: str):
        self.battle_log.append(message)
        if len(self.battle_log) > 5:
            self.battle_log.pop(0)


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
            result += " It's super effective!"
        elif effectiveness < 1 and effectiveness > 0:
            result += " It's not very effective..."
        elif effectiveness == 0:
            result += " It had no effect!"

        return result

    def process_status_turn(self, pokemon: Pokemon, name: str) -> List[str]:
        messages = []

        if pokemon.status == "poisoned":
            damage = pokemon.get_max_hp() // 8
            pokemon.take_damage(damage)
            messages.append(f"{name} is hurt by poison!")
        elif pokemon.status == "burned":
            damage = pokemon.get_max_hp() // 8
            pokemon.take_damage(damage)
            messages.append(f"{name} is hurt by its burn!")
        elif pokemon.status == "paralyzed":
            if random.random() < 0.25:
                messages.append(f"{name} is paralyzed and can't move!")
                return ["paralyzed"]
        elif pokemon.status == "sleep":
            pokemon.sleep_turns -= 1
            if pokemon.sleep_turns <= 0:
                pokemon.status = None
                messages.append(f"{name} woke up!")
            else:
                messages.append(f"{name} is asleep!")
                return ["asleep"]

        return messages

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
                effectiveness = get_type_effectiveness(move.type, player_pokemon.types)
                score = damage * effectiveness

                if ai_pokemon.has_type(move.type):
                    score *= 1.5

            if score > best_score:
                best_score = score
                best_move = move

        return best_move

    def process_turn(self, player_move_index: int, ai_move_index: int):
        player_pokemon = self.state.get_player_pokemon()
        ai_pokemon = self.state.get_ai_pokemon()

        player_move = player_pokemon.moves[player_move_index]
        ai_move = ai_pokemon.moves[ai_move_index]

        player_speed = player_pokemon.get_effective_stat("spe")
        ai_speed = ai_pokemon.get_effective_stat("spe")

        if player_pokemon.status == "paralyzed":
            player_speed //= 2
        if ai_pokemon.status == "paralyzed":
            ai_speed //= 2

        if player_speed >= ai_speed:
            first, second = "player", "ai"
            first_move, second_move = player_move, ai_move
            first_pokemon, second_pokemon = player_pokemon, ai_pokemon
            first_name = player_pokemon.name
            second_name = "AI " + ai_pokemon.name
        else:
            first, second = "ai", "player"
            first_move, second_move = ai_move, player_move
            first_pokemon, second_pokemon = ai_pokemon, player_pokemon
            first_name = "AI " + ai_pokemon.name
            second_name = player_pokemon.name

        status_msgs = self.process_status_turn(first_pokemon, first_name)
        if status_msgs and status_msgs[0] in ["paralyzed", "asleep"]:
            self.state.add_log(status_msgs[1] if len(status_msgs) > 1 else status_msgs[0])
        else:
            for msg in status_msgs:
                self.state.add_log(msg)

            result = self.execute_move(first_move, first_pokemon, second_pokemon, first_name)
            self.state.add_log(result)

        if second_pokemon.is_fainted():
            self.state.add_log(f"{second_name} fainted!")
            fainted = self.state.check_faints()
            if fainted:
                return

        if not second_pokemon.is_fainted():
            status_msgs = self.process_status_turn(second_pokemon, second_name)
            if status_msgs and status_msgs[0] in ["paralyzed", "asleep"]:
                self.state.add_log(status_msgs[1] if len(status_msgs) > 1 else status_msgs[0])
            else:
                for msg in status_msgs:
                    self.state.add_log(msg)

                result = self.execute_move(second_move, second_pokemon, first_pokemon, second_name)
                self.state.add_log(result)

        fainted = self.state.check_faints()
        if fainted:
            if fainted == "player":
                self.state.add_log(f"{player_pokemon.name} fainted!")
            else:
                self.state.add_log(f"{ai_pokemon.name} fainted!")

        if all(p.is_fainted() for p in self.state.player_team):
            self.state.winner = "ai"
            self.state.game_over = True
            self.state.add_log("You lost!")
        elif all(p.is_fainted() for p in self.state.ai_team):
            self.state.winner = "player"
            self.state.game_over = True
            self.state.add_log("You won!")

        self.state.turn += 1