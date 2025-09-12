from typing import Optional
from poke_env.battle import AbstractBattle, Move, Pokemon, PokemonType, SideCondition, Weather,MoveCategory
from poke_env.player import Player

team = """
Deoxys-Speed @ Focus Sash  
Ability: Pressure  
Tera Type: Psychic  
EVs: 248 HP / 8 SpD / 252 Spe  
Timid Nature  
IVs: 0 Atk  
- Stealth Rock  
- Spikes  
- Thunder Wave  
- Taunt

Koraidon @ Choice Band  
Ability: Orichalcum Pulse  
Tera Type: Fighting  
EVs: 252 Atk / 4 SpD / 252 Spe  
Jolly Nature  
- Dragon Claw  
- Collision Course  
- Flare Blitz  
- U-turn

Chi-Yu @ Choice Specs
Ability: Beads of Ruin
EVs: 4 Def / 252 SpA / 252 Spe
Tera Type: Fire
Timid Nature
- Overheat
- Flamethrower
- Fire Blast
- Dark Pulse

Walking Wake @ Choice Specs
Ability: Protosynthesis
EVs: 12 HP / 244 SpA / 252 Spe
Tera Type: Water
Timid Nature
- Hydro Steam
- Draco Meteor
- Flamethrower
- Dragon Pulse

Flutter Mane @ Booster Energy  
Ability: Protosynthesis  
Tera Type: Ghost  
EVs: 252 SpA / 4 SpD / 252 Spe  
Timid Nature  
IVs: 0 Atk  
- Moonblast  
- Shadow Ball  
- Mystical Fire  
- Psyshock

Kingambit @ Life Orb
Ability: Supreme Overlord
EVs: 252 Atk / 4 Def / 252 Spe
Tera Type: Ghost
Adamant Nature
- Swords Dance
- Sucker Punch
- Kowtow Cleave
- Iron Head
"""

class CustomAgent(Player):
    def __init__(self, *args, **kwargs):
        super().__init__(team=team, *args, **kwargs)
        self.game_phase = "early"
        self.tera_move = False
        self.debug = True

    def choose_move(self, battle: AbstractBattle):
        self.tera_move = False
        action = None

        if self.debug:
            print(f"\n=== Turn {battle.turn} - Phase: {self.game_phase} ===")
            print(f"Active: {battle.active_pokemon.species} ({battle.active_pokemon.current_hp_fraction:.2%}) vs {battle.opponent_active_pokemon.species} ({battle.opponent_active_pokemon.current_hp_fraction:.2%})")


        # Priority 1: Check for a winning move that overrides everything
        # If there are available moves, find the winning move and return it
    
        #if state["available_moves"]:
        #    winning_move = self.has_winning_move(state)
        #    if winning_move:
        #        if self.debug:
        #            print(f"Debug: Found a winning move: {winning_move.id}. OVERRIDING ALL LOGIC.")
        #        return self.create_order(winning_move)

        #Priority 2: If no moves available - switch - find the best switch

        #if not battle.available_moves:
        #    if self.debug: print("Debug: No moves available, must switch.")
        #    action = self.choose_best_switch(state)
        #if self.debug: print(f"Debug: Current HP fraction: {state['my_pokemon'].current_hp_fraction}")

        # Priority 3: If low HP or bad matchup - switch - find the best switch
        
        #elif state["my_pokemon"].current_hp_fraction <= 0.4:
        #    if self.debug: print("Debug: Low HP detected, evaluating switch options.")
        #    action = self.choose_best_switch(state)
        #elif self.is_bad_matchup(state["my_pokemon"], state["opponent_pokemon"]):
        #    if self.debug: print("Debug: Bad matchup detected, evaluating switch options.")
        #    action = self.choose_best_switch(state)
        #else:
        #    if self.game_phase == "early":
        #        action = self.choose_early_game_action(battle, state)
        #    elif self.game_phase == "mid":
        #        action = self.choose_mid_game_action(state)
        #    else:
        #        action = self.choose_late_game_action(battle, state)
        
        # Priority 4: No move found or preferred switch - choose best switch
        #if not action and state["available_switches"]:
        #    if self.debug: print("Debug: No suitable move found or switch is preferred, calculating best switch.")
        #    action = self.choose_best_switch(state)
        
        
        if self.debug: print(f"Debug: Final action is: {action} {'(TERA)' if self.tera_move else ''}")
        if action:
            if self.tera_move == True:
                self.tera_move = False
                return self.create_order(action, terastallize=True)
            else:
                return self.create_order(action)
        else:
            if self.debug: print("Debug: CRITICAL FALLBACK - Choosing random move.")
            return self.choose_random_move(battle)
