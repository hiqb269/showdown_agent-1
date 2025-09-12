
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
    """
    An expert system agent for Pokémon battles.
    This version uses a more advanced set of heuristics to make decisions.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(team=team, *args, **kwargs)

    def _estimate_damage(self, move: Move, attacker: Pokemon, defender: Pokemon) -> float:
        """
        Estimates the damage a move would deal.
        """
        if move.base_power == 0:
            return 0
        
        if defender is None or defender.fainted:
            multiplier = 1.0
        else:
            multiplier = defender.damage_multiplier(move)
        
        if move.type in attacker.types:
            multiplier *= 1.5 # STAB
            
        damage = move.base_power * multiplier
        return damage

    def find_best_move(self, battle: AbstractBattle):
        """
        Finds the best damaging move to use, returning the move and its estimated damage.
        """
        best_move = None
        max_damage = -1

        if not battle.available_moves:
            return None, 0

        for move in battle.available_moves:
            if move.base_power > 0:
                damage = self._estimate_damage(move, battle.active_pokemon, battle.opponent_active_pokemon)
                if damage > max_damage:
                    max_damage = damage
                    best_move = move
            
        return best_move, max_damage
    #same function as above - with just difference in order of parameters
    def _find_opponent_best_move(self, battle: AbstractBattle):
        """
        Estimates the opponent's best damaging move against our active Pokemon.
        """
        best_move = None
        max_damage = -1

        for move in battle.opponent_active_pokemon.moves.values():
            if move.base_power > 0:
                damage = self._estimate_damage(move, battle.opponent_active_pokemon, battle.active_pokemon)
                if damage > max_damage:
                    max_damage = damage
                    best_move = move
        
        return best_move, max_damage

    def find_best_switch(self, battle: AbstractBattle):
        """
        Finds the best Pokémon to switch into based on a matchup score.
        """
        best_switch = None
        best_score = -float('inf')

        if not battle.available_switches:
            return None
        #resistance score is how much damage the switch-in can resist from the all of opponent's moves
        for pokemon in battle.available_switches:
            resistance_score = 0
            for move in battle.opponent_active_pokemon.moves.values():
                 resistance_score -= self._estimate_damage(move, battle.opponent_active_pokemon, pokemon)
            #offensive score is how much damage the switch-in can deal to the opponent with its best move
            offensive_score = 0
            for move in pokemon.moves.values():
                offensive_score = max(offensive_score, self._estimate_damage(move, pokemon, battle.opponent_active_pokemon))

            total_score = resistance_score + offensive_score
            
            if total_score > best_score:
                best_score = total_score #simplistic
                best_switch = pokemon
        
        return best_switch
    
    def choose_move(self, battle: AbstractBattle):

        active = battle.active_pokemon
        opponent = battle.opponent_active_pokemon

        if battle.force_switch:
            best_switch = self.find_best_switch(battle)
            return self.create_order(best_switch) if best_switch else self.choose_random_move(battle)

        best_move, estimated_damage = self.find_best_move(battle)

        # Rule 1: Check for a guaranteed knockout
        if best_move and estimated_damage >= opponent.current_hp:
            return self.create_order(best_move)

        # Rule 2: Check if we are in immediate danger of being knocked out
        _, opponent_damage = self._find_opponent_best_move(battle)
        if opponent_damage >= active.current_hp and battle.available_switches:
            best_switch = self.find_best_switch(battle)
            if best_switch:
                return self.create_order(best_switch)

        # Rule 3: Use strategic healing moves if health is low
        if active.current_hp_fraction < 0.5:
            healing_moves = ['morningsun', 'recover']
            for move_id in healing_moves:
                if move_id in [m.id for m in battle.available_moves]:
                    return self.create_order(Move(move_id, gen=battle.gen))
            #switch if no healing move available
            if battle.available_switches:
                best_switch = self.find_best_switch(battle)
                if best_switch:
                    return self.create_order(best_switch)

        # Rule 4: None available for the current team - keeping in case team changes
        pivoting_moves = ['uturn', 'voltswitch']
        for move_id in pivoting_moves:
            if move_id in [m.id for m in battle.available_moves]:
                return self.create_order(Move(move_id, gen=battle.gen))

        # Rule 5: If no other rule applies, use the best damaging move
        if best_move:
            return self.create_order(best_move)

        # Rule 6: Failsafe
        return self.choose_random_move(battle)
