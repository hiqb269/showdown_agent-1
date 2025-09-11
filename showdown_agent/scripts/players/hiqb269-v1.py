
from poke_env.battle import AbstractBattle, Move, Pokemon
from poke_env.player import Player

team = """
Necrozma-Dusk-Mane @ Rocky Helmet  
Ability: Prism Armor  
Tera Type: Water  
EVs: 252 HP / 252 Atk / 4 SpD  
Adamant Nature  
- Sunsteel Strike  
- Earthquake  
- Outrage  
- Morning Sun

Koraidon @ Choice Band  
Ability: Orichalcum Pulse  
Tera Type: Fire  
EVs: 252 Atk / 4 SpD / 252 Spe  
Jolly Nature  
- Flare Blitz  
- Close Combat  
- Outrage 
- Iron Head

Kyogre @ Choice Specs  
Ability: Drizzle  
Tera Type: Water  
EVs: 252 HP / 252 SpA / 4 Spe  
Hasty Nature  
- Water Spout  
- Rock Slide  
- Ice Beam  
- Thunder 

Zacian-Crowned @ Rusted Sword  
Ability: Intrepid Sword  
Tera Type: Fairy  
EVs: 8 HP / 248 Atk / 252 Spe  
Jolly Nature  
- Behemoth Blade  
- Play Rough  
- Close Combat  
- Wild Charge

Ho-Oh @ Heavy-Duty Boots  
Ability: Regenerator  
Tera Type: Flying  
EVs: 4 HP / 252 Atk / 252 SpD  
Careful Nature  
- Sacred Fire  
- Brave Bird  
- Earthquake  
- Recover 

Arceus-Ground @ Earth Plate  
Ability: Multitype  
Tera Type: Ground  
EVs: 252 HP / 4 SpA / 252 Spe  
Timid Nature  
IVs: 0 Atk  
- Judgment  
- Calm Mind  
- Recover  
- Ice Beam
"""

class CustomAgent(Player):
    def __init__(self, *args, **kwargs):
        super().__init__(team=team, *args, **kwargs)
        self.opponent_team_seen = set()

    def get_battle_state(self, battle: AbstractBattle):
        return {
            "my_pokemon": battle.active_pokemon,
            "opponent_pokemon": battle.opponent_active_pokemon,
            "available_moves": battle.available_moves,
            "available_switches": battle.available_switches,
            "opponent_team": battle.opponent_team,
    }

    def update_opponent_model(self, battle):
        opp_name = battle.opponent_active_pokemon.species
        self.opponent_team_seen.add(opp_name)

    def score_move(self, move: Move, opponent: Pokemon):
        score = 0
        score = opponent.damage_multiplier(move)
        return score
    
    def choose_action(self, battle):
        self.update_opponent_model(battle)
        state = self.get_battle_state(battle)

        best_move = None
        max_score = -float("inf")

        for move in state["available_moves"]:
            score = self.score_move(move, state["opponent_pokemon"])
            if score > max_score:
                max_score = score
                best_move = move

        if best_move:
            return self.create_order(best_move)
        elif state["available_switches"]:
            # If no good move is found, switch to a different Pokémon - we just pick the first available one
            return self.create_order(state["available_switches"][0])
        else:
            return self.choose_random_move(battle)
    
    def choose_move(self, battle: AbstractBattle):
         return self.choose_action(battle)