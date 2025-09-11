from typing import List, Optional
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
        self.opponent_team_seen = set()
        self.game_phase = "early"  # early, mid, late
        self.hazards_set = {"stealthrock": False, "spikes": 0}
        self.sun_active = False
        self.tera_move = False
        self.debug = True

    def get_battle_state(self, battle: AbstractBattle):
        return {
            "my_pokemon": battle.active_pokemon,
            "opponent_pokemon": battle.opponent_active_pokemon,
            "available_moves": battle.available_moves,
            "available_switches": battle.available_switches,
            "opponent_team": battle.opponent_team,
            "my_team": battle.team,
            "weather": battle.weather,
            "side_conditions": battle.side_conditions,
            "opponent_side_conditions": battle.opponent_side_conditions,
            "can_tera": battle.can_tera,
    }

    def update_game_state(self, battle):
        # Update opponent team knowledge
        if battle.opponent_active_pokemon:
            self.opponent_team_seen.add(battle.opponent_active_pokemon.species)
        
        # Check if sun is active (from Koraidon's ability)
        weather = getattr(battle, 'weather', None)
        wname = ""
        if weather:
            wname = str(next(iter(weather.keys()))).lower() if weather else ""  
            self.sun_active =  "sun" in wname
        
        # Update hazards tracking
        if battle.opponent_side_conditions:
            self.hazards_set["stealthrock"] = "stealthrock" in battle.opponent_side_conditions
            spikes_count = 0
            if "spikes" in battle.opponent_side_conditions:
                spikes_count = battle.opponent_side_conditions["spikes"]
                self.hazards_set["spikes"] = spikes_count

        # Determine game phase based on team status
        alive_count = len([p for p in battle.team.values() if not p.fainted])
        if alive_count >= 5:  # and battle.active_pokemon.species == "deoxysspeed"
            self.game_phase = "early"
        elif alive_count >= 3:
            self.game_phase = "mid"
        else:
            self.game_phase = "late"
        print(f"Debug: Game phase: {self.game_phase}, Hazards: {self.hazards_set}, Sun: {self.sun_active}")
    

    def has_magic_bounce(self, opponent: Pokemon) -> bool:
        if opponent.ability:
            print(f"Debug: Checking for Magic Bounce on {opponent.species} with ability {opponent.ability}")
        return opponent.ability and "magic bounce" in opponent.ability.lower()

    def is_setup_threat(self, opponent: Pokemon) -> bool:
        setup_threats = {
            "arceus", "dialga", "palkia", "giratina", "rayquaza", "groudon", "kyogre",
            "necrozma-dusk-mane", "necrozma-dawn-wings", "zacian", "eternatus"
        }
        return any(threat in opponent.species.lower() for threat in setup_threats)
    
    def choose_early_game_action(self, state):
        my_pokemon = state["my_pokemon"]
        opponent = state["opponent_pokemon"]

        if my_pokemon.species != "deoxysspeed":
            # Should switch to Deoxys if available
            for switch in state["available_switches"]:
                if switch.species == "deoxysspeed":
                    print("Debug: Switching to Deoxysspeed to start hazard setting")
                    return switch
        
        # Deoxys-Speed decision tree
        if self.has_magic_bounce(opponent):
            # Use Taunt against Magic Bounce
            for move in state["available_moves"]:
                if move.id == "taunt":
                    if self.debug:
                        print("Using Taunt against Magic Bounce")
                    return move
                        
        # Priority: Stealth Rock > Spikes > Thunder Wave for threats > more Spikes
        if not self.hazards_set["stealthrock"]:
            for move in state["available_moves"]:
                if move.id == "stealthrock":
                    if self.debug:
                        print("Setting Stealth Rock")
                    self.hazards_set["stealthrock"] = True
                    return move
        
        if self.hazards_set["spikes"] < 2:  # Set up to 2 layers of spikes
            for move in state["available_moves"]:
                if move.id == "spikes":
                    if self.debug:
                        print(f"Setting Spikes (layer {self.hazards_set['spikes'] + 1})")
                    self.hazards_set["spikes"] += 1
                    return move
        
        if self.is_setup_threat(opponent):
            for move in state["available_moves"]:
                if move.id == "thunderwave":
                    if self.debug:
                        print("Using Thunder Wave on setup threat")
                    return move
        
        return self.choose_best_attack(state)

    def choose_mid_game_action(self, state):
        my_pokemon = state["my_pokemon"]
        opponent = state["opponent_pokemon"]
        
        wallbreakers = ["koraidon", "walkingwake", "chiyu"]
        
        if my_pokemon.species not in wallbreakers:
            # Switch to appropriate wallbreaker
            best_switch = self.choose_best_wallbreaker(state, opponent)
            if best_switch:
                if self.debug:
                    print(f"Switching to wallbreaker: {best_switch.species}")
                return best_switch

        # Wallbreaker-specific logic
        if my_pokemon.species == "koraidon":
            return self.choose_koraidon_move(state)
        #elif my_pokemon.species == "walkingwake":
        #    return self.choose_walking_wake_move(state)
        #elif my_pokemon.species == "chiyu":
        #    return self.choose_chi_yu_move(state)
        
        return self.choose_best_attack(state)

    def choose_late_game_action(self, battle, state):
        my_pokemon = state["my_pokemon"]
        opponent = state["opponent_pokemon"]   
        cleaners = ["fluttermane", "kingambit"]   
        if my_pokemon.species not in cleaners:
            # Switch to appropriate cleaner
            best_cleaner = self.choose_best_cleaner(state, opponent)
            if best_cleaner:
                if self.debug:
                    print(f"Switching to cleaner: {best_cleaner.species}")
                return best_cleaner
        
        #if my_pokemon.species == "fluttermane":
        #    return self.choose_flutter_mane_move(state)
        if my_pokemon.species == "kingambit":
            return self.choose_kingambit_move(state, battle)
        return self.choose_best_attack(state)

    def choose_best_wallbreaker(self, state, opponent: Pokemon) -> Optional[Pokemon]:
        """Choose the best wallbreaker for the current opponent"""
        available_wallbreakers = []
        wallbreaker_names = ["koraidon", "walking-wake", "chiyu"]
        
        for switch in state["available_switches"]:
            if any(name in switch.species for name in wallbreaker_names):
                available_wallbreakers.append(switch)
        
        if not available_wallbreakers:
            return None
            
        # Simple heuristic: Koraidon for physical walls, special attackers for special walls
        # In real implementation, you'd want more sophisticated type matchup logic
        return available_wallbreakers[0]

    def choose_best_cleaner(self, state, opponent: Pokemon) -> Optional[Pokemon]:
        """Choose the best cleaner for late game"""
        for switch in state["available_switches"]:
            if "fluttermane" in switch.species or "kingambit" in switch.species:
                return switch
        return None

    def choose_koraidon_move(self, state):
        opponent = state["opponent_pokemon"]
        for move in state["available_moves"]:
            if move.id == "uturn":
                # A simple heuristic: U-turn if the opponent is a threat
                if opponent.damage_multiplier(PokemonType.FIGHTING) > 1 or opponent.damage_multiplier(PokemonType.DRAGON) > 1:
                     if self.debug:
                         print("Koraidon running away with U-turn against a threat")
                     return move
        # If not pivoting, find the best attacking move
        return self.choose_best_attack(state)
    

    def choose_walking_wake_move(self, state):
        return self.choose_best_attack(state)


    def choose_chi_yu_move(self, state):
        return self.choose_best_attack(state)

    def choose_flutter_mane_move(self, state):
        return self.choose_best_attack(state)

    def choose_kingambit_move(self, state, battle):
        opponent = state["opponent_pokemon"]
        my_pokemon = state["my_pokemon"]
        best_attack = self.choose_best_attack(state)
        # Consider Tera activation for securing KO
        if battle.can_tera and self.should_tera_kingambit(opponent, my_pokemon):
            if self.debug:
                print("Kingambit considering Tera activation")
            if best_attack:
                normal_damage_estimate = self.estimate_damage(best_attack, state)
                tera_damage_estimate = normal_damage_estimate * (2 / 1.5) # Approximate Tera Dark boost
            if normal_damage_estimate < opponent.current_hp and tera_damage_estimate >= opponent.current_hp:
                if self.debug:
                    print("Kingambit: Activating Offensive Tera to secure KO!")
                self.tera_move = True
                return best_attack

        # Defensive Tera: If facing a lethal Fighting-type threat.
        if "koraidon" in opponent.species.lower() or "ironvaliant" in opponent.species.lower():
             if self.debug:
                print("Kingambit: Activating Defensive Tera to survive!")
             self.tera_move = True
             return best_attack

        return best_attack
    
    def estimate_damage(self, move: Move, state) -> float:
        opponent = state["opponent_pokemon"]
        my_pokemon = state["my_pokemon"]
        if not move.base_power or move.base_power == 0:
            return 0
        # Simplified damage formula
        attack_stat = my_pokemon.stats['atk'] if move.category == MoveCategory.PHYSICAL else my_pokemon.stats['spa']
        defense_stat = opponent.stats['def'] if move.category == MoveCategory.PHYSICAL else opponent.stats['spd']
        type_multiplier = opponent.damage_multiplier(move)
        stab = 1.5 if move.type in my_pokemon.types else 1.0
        if not attack_stat:
            attack_stat = 1
        if not defense_stat:
            defense_stat = 1
        damage = (((2 * my_pokemon.level / 5 + 2) * move.base_power * attack_stat / defense_stat) / 50 + 2)
        damage *= stab * type_multiplier
        return damage


    def is_bulky_wall(self, opponent: Pokemon) -> bool:
        if not opponent or not opponent.species:
            return False
        known_walls = ["blissey", "chansey", "toxapex", "ferrothorn", "skarmory", "dondozo", "garganacl"]
        if any(wall in opponent.species.lower() for wall in known_walls):
            return True
        if not opponent.base_stats:
            return False
        hp = opponent.base_stats.get("hp", 0)
        defense = opponent.base_stats.get("def", 0)
        special_defense = opponent.base_stats.get("spd", 0)
        return hp > 100 and (defense > 120 or special_defense > 120)


    def is_special_wall(self, opponent: Pokemon) -> bool:
        if not opponent or not opponent.base_stats:
            return False
        known_special_walls = [
            "blissey", "chansey", "clodsire", "goodra", "goodra-hisui",
            "umbreon", "florges", "snorlax"
        ]
        if any(wall in opponent.species.lower() for wall in known_special_walls):
            return True
        hp = opponent.base_stats.get("hp", 0)
        special_defense = opponent.base_stats.get("spd", 0)
        if hp >= 90 and special_defense >= 120:
            return True
        if special_defense >= 140:
            return True
        return False
    
    def can_setup_kingambit_safely(self, opponent: Pokemon, my_pokemon: Pokemon) -> bool:
        if self.is_passive_forkinga(opponent):
            return True
        if (PokemonType.FIGHTING in opponent.types and opponent.damage_multiplier(PokemonType.FIGHTING) >= 2):
            return False

        dangerous_species = ["iron valiant", "great tusk", "annihilape", "volcarona","koraidon", "zamazenta", "marshadow"]
        if any(d in opponent.species.lower() for d in dangerous_species):
            return False
        
        we_threaten_them = opponent.damage_multiplier(PokemonType.DARK) > 1 or opponent.damage_multiplier(PokemonType.STEEL) > 1
        they_threaten_us = False
        for move in opponent.moves.values():
            if my_pokemon.damage_multiplier(move) > 1:
                they_threaten_us = True
                break
    
        if we_threaten_them and not they_threaten_us:
            return True
        is_weakened = opponent.current_hp_fraction < 0.4
        can_survive = my_pokemon.current_hp_fraction > 0.5
        return is_weakened and can_survive


    def is_passive_forkinga(self, opponent: Pokemon) -> bool:
        if not opponent or not opponent.species:
            return False  
        passive_species = ["blissey", "chansey", "toxapex", "dondozo", "clodsire", "corviknight"]
        if any(p in opponent.species.lower() for p in passive_species):
            return True
        return opponent.base_stats.get("atk", 100) < 85 and opponent.base_stats.get("spa", 100) < 85


    def is_kingaopponent_faster(self, opponent: Pokemon, my_pokemon: Pokemon) -> bool:
        # Known setup or pivot Pokémon that often don't attack immediately??
        setup_or_pivot = ["flutter mane", "grimmsnarl", "gliscor", "ho-oh"]
        if any(name in opponent.species.lower() for name in setup_or_pivot):
            return False
        opponent_speed = opponent.stats.get("spe") if opponent.stats.get("spe") else 0
        my_speed = my_pokemon.stats.get("spe") if my_pokemon.stats.get("spe") else 0
        return opponent_speed > my_speed


    def should_tera_kingambit(self, opponent: Pokemon, my_pokemon: Pokemon) -> bool:
        """Determine when to Tera Kingambit"""
        # If Kingambit has Tera'd into Ghost
        threatening_types = [PokemonType.GHOST, PokemonType.DARK]
        if any(opponent.damage_multiplier(threat) > 1.5 for threat in threatening_types):
            return True #Defensive Tera
        # for move in opponent.moves.values():
        #     if my_pokemon.damage_multiplier(move) > 1.5:
        #         return True
        # Tera Dark for securing KO or surviving crucial hit
        #TODO: Add more logic here to ensure KO
        return (opponent.current_hp_fraction < 0.6 and my_pokemon.current_hp_fraction > 0.3)  

    def score_move(self, move: Move, state):
        me = state["my_pokemon"]
        opponent = state["opponent_pokemon"]
        weather = state.get("weather")
        if not move or not opponent:
            return -float("inf")
            
        score = 0.0
        score += move.base_power if move.base_power else 0
        type_multiplier = opponent.damage_multiplier(move)
        if(type_multiplier > 1):
            score *= type_multiplier
      
        # STAB bonus
        if move.type in me.types:
            score *= 1.5
        
        if weather:
            is_sun = Weather.SUNNYDAY in weather or Weather.DESOLATELAND in weather
            is_rain = Weather.RAINDANCE in weather or Weather.PRIMORDIALSEA in weather
            if is_sun:
                if move.id == "hydrosteam": 
                    score *= 1.5
                elif move.type == PokemonType.FIRE:
                    score *= 1.5
                elif move.type == PokemonType.WATER:
                    score *= 0.5 # For non-Hydro Steam water moves
            elif is_rain and move.type == PokemonType.WATER:
                    score *= 1.5

        # Prioritize status moves in early game
        if move.category.name == MoveCategory.STATUS:
            if self.game_phase == "early" and move.id in ["stealthrock", "spikes", "thunderwave", "taunt"]:
                 score += 150 # Decide how to give numbers for priority     
        if move.id == "swordsdance" and self.game_phase == "late" and self.can_setup_kingambit_safely(opponent, me):
            if me.boosts.get('atk', 0) < 6:
                score += 200
        if move.id == "suckerpunch":
            if self.is_kingaopponent_faster(opponent, me):
                score += 100  # great vs faster mons
            if opponent.current_hp_fraction < 0.3:
                score += 120  # excellent cleanup tool
            if self.is_passive_forkinga(opponent):
                score -= 50 #Don't waste on passive 
        if move.id == "overheat" and self.is_bulky_wall(opponent) and type_multiplier > 1:
            score *= 1.2 # Give a 20% score bonus for bulky walls not resitant to fire
        # Add a bonus for using Mystical Fire against a Steel-type
        if move.id == "mysticalfire" and PokemonType.STEEL in state["opponent_pokemon"].types:
            score *= 1.5 
        if move.id == "psyshock" and self.is_special_wall(state["opponent_pokemon"]):
            score *= 1.8 
        if move.id == "dracometeor" and self.is_bulky_wall(opponent) and not self.is_special_wall(opponent) \
            and type_multiplier >= 1.0:
            score *= 1.2 # Give a 20% bonus to encourage nuking bulky walls with Draco Meteor
        return score

    

    def choose_best_attack(self, state):
        best_move = None
        max_score = -float("inf")

        #if not state["available_moves"] or state["available_moves"] == []:

         # Evaluate each move and pick the best one
        
        for move in state["available_moves"]:
            score = self.score_move(move, state)
            if score > max_score:
                max_score = score
                best_move = move
        
        if best_move:
            if self.debug:
                print(f"Choosing best attack: {best_move.id}")
            return best_move
        
        return None
    

    def score_switch(self, pokemon: Pokemon, state) -> float:
        opponent = state["opponent_pokemon"]
        if pokemon.fainted:
            return -float("inf")

        score = 100.0

        # Offensive score: How well can this Pokemon threaten the opponent?
        offensive_multiplier = 0
        for move_type in pokemon.types:
            offensive_multiplier = max(offensive_multiplier, opponent.damage_multiplier(move_type))
        
        if offensive_multiplier > 1:
            score += 150 * offensive_multiplier
        elif offensive_multiplier < 1:
            score -= 50

        # Defensive score: How well can this Pokemon take a hit?
        defensive_multiplier = 0
        for opp_type in opponent.types:
             defensive_multiplier = max(defensive_multiplier, pokemon.damage_multiplier(opp_type))

        if defensive_multiplier == 0: # Immunity
            score += 300
        elif defensive_multiplier < 1: # Resistance
            score += 200
        elif defensive_multiplier > 1: # Weakness
            score -= 400
        
        # Hazard damage penalty
        sr_dmg = pokemon.damage_multiplier(PokemonType.ROCK) * 0.125
        is_grounded = True
        if PokemonType.FLYING in pokemon.types:
            is_grounded = False
        if pokemon.ability and "levitate" in pokemon.ability.lower():
            is_grounded = False
        if pokemon.item and "airballoon" in pokemon.item.lower():
            is_grounded = False
        spikes_dmg = 0
        if is_grounded:
            spikes_dmg = [0, 1/8, 1/6, 1/4][self.hazards_set["spikes"]]
        
        total_hazard_dmg_fraction = sr_dmg + spikes_dmg
        if pokemon.current_hp_fraction <= total_hazard_dmg_fraction:
             return -float("inf") # This switch is a KO, avoid at all costs
        
        score -= total_hazard_dmg_fraction * 200 # Penalize based on hazard damage taken

        # Sun bonus for Protosynthesis/Orichalcum Pulse
        if self.sun_active and (pokemon.ability == "Protosynthesis" or pokemon.ability == "Orichalcum Pulse"):
            score += 75

        # Health modifier: prefer switching in healthier Pokemon
        score *= pokemon.current_hp_fraction

        return score


    def choose_best_switch(self, state) -> Optional[Pokemon]:
        best_switch = None
        max_score = -float("inf")

        if not state["available_switches"]:
            return None

        for pokemon in state["available_switches"]:
            score = self.score_switch(pokemon, state)
            if self.debug:
                print(f"Debug: Switch score for {pokemon.species}: {score:.2f}")
            if score > max_score:
                max_score = score
                best_switch = pokemon
        
        if self.debug and best_switch:
            print(f"Debug: Best switch chosen is {best_switch.species} with score {max_score:.2f}")
        
        return best_switch
    
    
    def teampreview(self, battle: AbstractBattle) -> str:

        deoxys_position = None
        # Find the position of Deoxys-Speed in your team list
        for i, p in enumerate(battle.team.values()):
            if "deoxys" in p.species.lower() and p.base_stats['spe'] == 180:
                deoxys_position = i + 1
                break
        
        # If found, construct the team order string to make it the lead
        if deoxys_position:
            team_order = [str(deoxys_position)]
            for i in range(1, len(battle.team) + 1):
                if i != deoxys_position:
                    team_order.append(str(i))
            print(f"Debug: Teampreview order: {team_order}")
            return "/team " + "".join(team_order)

        # Fallback if Deoxys-Speed is not found for some reason
        return "/team " + "".join(str(i) for i in range(1, len(battle.team) + 1))


    def choose_move(self, battle: AbstractBattle):
        self.update_game_state(battle)
        state = self.get_battle_state(battle)
        self.tera_move = False
        if battle.turn == 0:
            return self.teampreview(battle)

        if self.debug:
            print(f"=== Turn {battle.turn} - Phase: {self.game_phase} ===")
            print(f"Active: {state['my_pokemon'].species} vs {state['opponent_pokemon'].species}")
            print("Available moves:", [move.id for move in battle.available_moves])
            print(f"Hazards: {self.hazards_set}, Sun: {self.sun_active}")
        
        action = None
        if not battle.available_moves:
            if self.debug:
                print("Debug: No moves available, must switch.")
            action = self.choose_best_switch(state)
        else:
            if self.game_phase == "early":
                action = self.choose_early_game_action(state)
            elif self.game_phase == "mid":
                action = self.choose_mid_game_action(state)
            else:  # late game
                action = self.choose_late_game_action(battle, state)

        print(f"Debug: Chosen action: {action}" if action else "None")
        if not action and state["available_switches"]:
            print("Debug: No action chosen, switching")
            action = self.choose_best_switch(state)
        if action:
            if self.tera_move == True:
                return self.create_order(action, terastallize=True)
            else:
                return self.create_order(action)
        else:
            return self.choose_random_move(battle)
