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
        self.opponent_team_seen = set()
        self.game_phase = "early"
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

    def is_sun_active(self, weather: Weather) -> bool:
        if weather:
            wname = str(next(iter(weather.keys()))).lower() if weather else ""  
            return "sun" in wname
        return False

    def update_game_state(self, battle):
        if battle.opponent_active_pokemon:
            self.opponent_team_seen.add(battle.opponent_active_pokemon.species)

        alive_count = len([p for p in battle.team.values() if not p.fainted])
        if alive_count >= 5:
            self.game_phase = "early"
        elif alive_count >= 3:
            self.game_phase = "mid"
        else:
            self.game_phase = "late"
        sun_active = self.is_sun_active(getattr(battle, 'weather', None))
        
        if self.debug:
            print(f"Debug: Game phase: {self.game_phase}, Opponent Hazards: {battle.opponent_side_conditions}, Sun: {sun_active}")

    def has_magic_bounce(self, opponent: Pokemon) -> bool:
        if opponent.ability:
            if self.debug:
                print(f"Debug: Checking for Magic Bounce on {opponent.species} with ability {opponent.ability}")
        return opponent.ability and "magic bounce" in opponent.ability.lower()

    ## NEW HELPER: Checks if we are in a bad matchup
    def is_bad_matchup(self, my_pokemon: Pokemon, opponent: Pokemon) -> bool:
        # It's a bad matchup if they have a super-effective STAB against us
        for opp_type in opponent.types:
            if my_pokemon.damage_multiplier(opp_type) > 1:
                return True
        
        # It's a bad matchup if we can't deal at least neutral damage
        can_hit_neutrally = False
        for move in my_pokemon.moves.values():
            if opponent.damage_multiplier(move) >= 1:
                can_hit_neutrally = True
                break
        if not can_hit_neutrally:
            return True
            
        return False
    
    ## NEW HELPER: Checks for a winning move to override all other logic
    def has_winning_move(self, state) -> Optional[Move]:
        my_pokemon = state["my_pokemon"]
        opponent = state["opponent_pokemon"]
        
        for move in state["available_moves"]:
            if move.category == MoveCategory.STATUS:
                continue
            
            # Check for super-effective moves first
            if opponent.damage_multiplier(move) > 1:
                damage = self.estimate_damage(move, state)
                if opponent.current_hp and damage >= opponent.current_hp:
                    if self.debug:
                        print(f"Debug: Found potential KO move: {move.id} with estimated damage {damage:.2f} vs opponent HP {opponent.current_hp}")
                    return move
        return None
    
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

    
    ## FIXED LOGIC for Deoxys hazard setting
    def choose_early_game_action(self, battle: AbstractBattle, state):
        my_pokemon = state["my_pokemon"]
        opponent = state["opponent_pokemon"]

        if my_pokemon.species != "deoxysspeed":
            deoxys = next((p for p in state["available_switches"] if p.species == "deoxysspeed"), None)
            if deoxys:
                if self.debug:
                    print("Debug: Switching to Deoxys-Speed to start hazard setting")
                return deoxys

        if self.has_magic_bounce(opponent):
            taunt = next((m for m in state["available_moves"] if m.id == "taunt"), None)
            if taunt:
                if self.debug:
                    print("Using Taunt against Magic Bounce")
                return taunt
        
        # Priority list for setting hazards
        # 1. Set Stealth Rock if not present
        if SideCondition.STEALTH_ROCK not in battle.opponent_side_conditions:
            stealth_rock = next((m for m in state["available_moves"] if m.id == "stealthrock"), None)
            if stealth_rock:
                if self.debug:
                    print("Setting Stealth Rock")
                return stealth_rock
        
        # 2. Set Spikes up to 3 layers
        spikes_layers = battle.opponent_side_conditions.get(SideCondition.SPIKES, 0)
        if spikes_layers < 3:
            spikes = next((m for m in state["available_moves"] if m.id == "spikes"), None)
            if spikes:
                if self.debug:
                    print(f"Setting Spikes (layer {spikes_layers + 1})")
                return spikes
        
        # If hazards are fully set, resort to best available attack/status
        return self.choose_best_attack(state)


    def choose_mid_game_action(self, state):
        my_pokemon = state["my_pokemon"]
        opponent = state["opponent_pokemon"]
        
        wallbreakers = ["koraidon", "walkingwake", "chiyu"]
        
        # If not a wallbreaker, check if we're in a bad spot before switching
        if my_pokemon.species not in wallbreakers:
            if self.is_bad_matchup(my_pokemon, opponent):
                if self.debug:
                    print(f"Debug: {my_pokemon.species} is not a wallbreaker AND is in a bad matchup. Looking to switch.")
                return self.choose_best_switch(state)
            else:
                if self.debug:
                    print(f"Debug: Matchup is favorable for {my_pokemon.species}, staying in to attack.")
                return self.choose_best_attack(state)

        return self.choose_best_attack(state)

    ## FIXED LOGIC to be more flexible
    def choose_late_game_action(self, battle: AbstractBattle, state):
        my_pokemon = state["my_pokemon"]
        opponent = state["opponent_pokemon"]   
        cleaners = ["fluttermane", "kingambit"]
        
        if my_pokemon.species == "kingambit":
            return self.choose_kingambit_move(state, battle)
        
        # If not a cleaner, check if we're in a bad spot before switching
        if my_pokemon.species not in cleaners:
            if self.is_bad_matchup(my_pokemon, opponent):
                if self.debug:
                    print(f"Debug: {my_pokemon.species} is not a cleaner AND is in a bad matchup. Looking to switch.")
                return self.choose_best_switch(state)
            else:
                if self.debug:
                    print(f"Debug: Matchup is favorable for {my_pokemon.species}, staying in to attack.")
                return self.choose_best_attack(state)

        return self.choose_best_attack(state)

    def choose_kingambit_move(self, state, battle):
        my_pokemon = state["my_pokemon"]
        opponent = state["opponent_pokemon"]
        
        swords_dance_move = next((m for m in state["available_moves"] if m.id == "swordsdance"), None)
        if swords_dance_move and my_pokemon.boosts.get('atk', 0) < 2:
            if not self.is_bad_matchup(my_pokemon, opponent) and opponent.current_hp_fraction > 0.5:
                 if self.debug:
                    print("Kingambit sees a safe opportunity to use Swords Dance.")
                 return swords_dance_move

        best_attack = self.choose_best_attack(state)
        if not best_attack:
            return self.choose_best_switch(state)

        if battle.can_tera and not my_pokemon.is_terastallized:
            # Simple Tera logic: Tera offensively if it secures a KO on a key threat.
            normal_damage = self.estimate_damage(best_attack, state)
            if best_attack.type in my_pokemon.types: # If it's a STAB move
                tera_damage = normal_damage * (2 / 1.5) # Approximate boost from Tera STAB
                if opponent.current_hp and normal_damage < opponent.current_hp and tera_damage >= opponent.current_hp:
                    if self.debug:
                        print("Kingambit: Activating Offensive Tera to secure KO!")
                    self.tera_move = True
                    
        return best_attack
    

    def estimate_damage(self, move: Move, state) -> float:
        opponent = state["opponent_pokemon"]
        my_pokemon = state["my_pokemon"]
        if not move.base_power or move.base_power == 0:
            return 0
    
        attack_stat = my_pokemon.stats['atk'] if move.category == MoveCategory.PHYSICAL else my_pokemon.stats['spa']
        defense_stat = opponent.stats['def'] if move.category == MoveCategory.PHYSICAL else opponent.stats['spd']
    
        # These factors are always known, so we define them early.
        type_multiplier = opponent.damage_multiplier(move)
        stab = 1.5 if move.type in my_pokemon.types else 1.0

        # If stats are unknown, calculate damage with a neutral Atk/Def ratio.
        if not attack_stat or not defense_stat:
            if self.debug:
                print("Debug: Unknown stats, using conservative damage estimate.")
            # Simplified formula assuming Atk/Def ratio is 1.
            estimated_defense = 100  # Arbitrary average defense value
            damage = (((2 * my_pokemon.level / 5 + 2) * move.base_power/estimated_defense) / 50 + 2)
            damage *= stab * type_multiplier
            return damage

    # --- If stats are known, proceed with the full calculation ---

    # Apply boosts
        attack_boost = my_pokemon.boosts.get('atk', 0) if move.category == MoveCategory.PHYSICAL else my_pokemon.boosts.get('spa', 0)
        defense_boost = opponent.boosts.get('def', 0) if move.category == MoveCategory.PHYSICAL else opponent.boosts.get('spd', 0)
    
        boost_multiplier = [1, 1.5, 2, 2.5, 3, 3.5, 4]
    
        if attack_boost >= 0:
            attack_stat *= boost_multiplier[attack_boost]
        else:
            attack_stat /= boost_multiplier[-attack_boost]

        if defense_boost >= 0:
            defense_stat *= boost_multiplier[defense_boost]
        else:
            defense_stat /= boost_multiplier[-defense_boost]
        
        # Full formula
        damage = (((2 * my_pokemon.level / 5 + 2) * move.base_power * attack_stat / defense_stat) / 50 + 2)
        damage *= stab * type_multiplier
        return damage

    def score_move(self, move: Move, state):
        me = state["my_pokemon"]
        opponent = state["opponent_pokemon"]
        weather = state.get("weather", None)
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

    def score_switch(self, pokemon: Pokemon, state) -> float:
        opponent = state["opponent_pokemon"]
        if pokemon.fainted:
            return -float("inf")
        score = 100.0
        offensive_multiplier = 0
        if pokemon.types:
            for move_type in pokemon.types:
                offensive_multiplier = max(offensive_multiplier, opponent.damage_multiplier(move_type))
        if offensive_multiplier > 1: score += 150 * offensive_multiplier
        elif offensive_multiplier < 1: score -= 50
        defensive_multiplier = 0
        if opponent.types:
            for opp_type in opponent.types:
                defensive_multiplier = max(defensive_multiplier, pokemon.damage_multiplier(opp_type))
        if defensive_multiplier == 0: score += 300
        elif defensive_multiplier < 1: score += 200
        elif defensive_multiplier > 1: score -= 400
        sr_dmg = pokemon.damage_multiplier(PokemonType.ROCK) * 0.125
        is_grounded = PokemonType.FLYING not in pokemon.types and pokemon.ability != "levitate" and pokemon.item != "airballoon"
        spikes_dmg = 0
        if is_grounded:
            spikes_layers = state["opponent_side_conditions"].get(SideCondition.SPIKES, 0)
            spikes_dmg = [0, 1/8, 1/6, 1/4][spikes_layers]
        total_hazard_dmg_fraction = sr_dmg + spikes_dmg
        if pokemon.current_hp_fraction <= total_hazard_dmg_fraction:
             return -float("inf")
        score -= total_hazard_dmg_fraction * 200

        sun_active = self.is_sun_active(state["weather"])
        if sun_active and pokemon.ability and ("protosynthesis" in pokemon.ability.lower() or "orichal" in pokemon.ability.lower()):
            score += 75
        score *= pokemon.current_hp_fraction
        return score

    def choose_best_switch(self, state) -> Optional[Pokemon]:
        best_switch = None
        max_score = -float("inf")
        if not state["available_switches"]:
            return None
        for pokemon in state["available_switches"]:
            score = self.score_switch(pokemon, state)
            if self.debug: print(f"Debug: Switch score for {pokemon.species}: {score:.2f}")
            if score > max_score:
                max_score = score
                best_switch = pokemon
        if self.debug and best_switch: print(f"Debug: Best switch chosen is {best_switch.species} with score {max_score:.2f}")
        return best_switch

    def choose_best_attack(self, state):
        best_move = None
        max_score = -float("inf")
        if not state["available_moves"]: return None
        for move in state["available_moves"]:
            score = self.score_move(move, state)
            if self.debug: print(f"Debug: Move score for {move.id}: {score:.2f}")
            if score > max_score:
                max_score = score
                best_move = move
        if best_move:
            if self.debug: print(f"Choosing best attack: {best_move.id} with score {max_score:.2f}")
            return best_move
        return None

    def teampreview(self, battle: AbstractBattle) -> str:
        # Simple teampreview: lead with Deoxys-Speed
        deoxys_position = next((i + 1 for i, p in enumerate(battle.team.values()) if "deoxysspeed" in p.species), None)
        if deoxys_position:
            team_order = [str(deoxys_position)]
            team_order.extend([str(i) for i in range(1, len(battle.team) + 1) if i != deoxys_position])
            return "/team " + "".join(team_order)
        return super().teampreview(battle)

    def choose_move(self, battle: AbstractBattle):
        self.update_game_state(battle)
        state = self.get_battle_state(battle)
        self.tera_move = False

        if self.debug:
            print(f"\n=== Turn {battle.turn} - Phase: {self.game_phase} ===")
            print(f"Active: {state['my_pokemon'].species} ({state['my_pokemon'].current_hp_fraction:.2%}) vs {state['opponent_pokemon'].species} ({state['opponent_pokemon'].current_hp_fraction:.2%})")

        # Priority 1: Check for a winning move that overrides everything
        if state["available_moves"]:
            winning_move = self.has_winning_move(state)
            if winning_move:
                if self.debug:
                    print(f"Debug: Found a winning move: {winning_move.id}. OVERRIDING ALL LOGIC.")
                return self.create_order(winning_move)

        action = None
        if not battle.available_moves:
            if self.debug: print("Debug: No moves available, must switch.")
            action = self.choose_best_switch(state)
        #if self.debug: print(f"Debug: Current HP fraction: {state['my_pokemon'].current_hp_fraction}")
        elif state["my_pokemon"].current_hp_fraction <= 0.4:
            if self.debug: print("Debug: Low HP detected, evaluating switch options.")
            action = self.choose_best_switch(state)
        elif self.is_bad_matchup(state["my_pokemon"], state["opponent_pokemon"]):
            if self.debug: print("Debug: Bad matchup detected, evaluating switch options.")
            action = self.choose_best_switch(state)
        else:
            if self.game_phase == "early":
                action = self.choose_early_game_action(battle, state)
            elif self.game_phase == "mid":
                action = self.choose_mid_game_action(state)
            else:
                action = self.choose_late_game_action(battle, state)
        
        if not action and state["available_switches"]:
            if self.debug: print("Debug: No suitable move found or switch is preferred, calculating best switch.")
            action = self.choose_best_switch(state)
        
        if not action:
            if self.debug: print("Debug: CRITICAL FALLBACK - Choosing random move.")
            return self.choose_random_move(battle)
        
        if self.debug: print(f"Debug: Final action is: {action} {'(TERA)' if self.tera_move else ''}")
        if action:
            if self.tera_move == True:
                self.tera_move = False
                return self.create_order(action, terastallize=True)
            else:
                return self.create_order(action)
        else:
            if self.debug: print("Debug: No action determined, choosing random move as last resort.")
            return self.choose_random_move(battle)