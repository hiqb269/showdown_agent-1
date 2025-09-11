from poke_env.battle import AbstractBattle, Move, Pokemon, Weather, SideCondition, PokemonType
from poke_env.player import Player


# The full Hyper Offense team string for the agent.
team = """
Deoxys-Speed @ Focus Sash
Ability: Pressure
Tera Type: Psychic
EVs: 252 HP / 4 Def / 252 Spe
Jolly Nature
- Stealth Rock
- Spikes
- Taunt
- Thunder Wave

Koraidon @ Choice Band
Ability: Orichalcum Pulse
Tera Type: Fire
EVs: 252 Atk / 4 SpD / 252 Spe
Jolly Nature
- Collision Course
- Flare Blitz
- U-turn
- Dragon Claw

Walking Wake @ Choice Specs
Ability: Protosynthesis
Tera Type: Water
EVs: 252 SpA / 4 SpD / 252 Spe
Timid Nature
IVs: 0 Atk
- Hydro Steam
- Draco Meteor
- Flamethrower
- Dragon Pulse

Chi-Yu @ Choice Scarf
Ability: Beads of Ruin
Tera Type: Dark
EVs: 252 SpA / 4 SpD / 252 Spe
Timid Nature
IVs: 0 Atk
- Overheat
- Dark Pulse
- Flamethrower
- Flame Charge

Flutter Mane @ Booster Energy
Ability: Protosynthesis
Tera Type: Fairy
EVs: 252 SpA / 4 SpD / 252 Spe
Timid Nature
IVs: 0 Atk
- Moonblast
- Shadow Ball
- Psyshock
- Mystical Fire

Kingambit @ Life Orb
Ability: Supreme Overlord
Tera Type: Dark
EVs: 252 Atk / 4 SpD / 252 Spe
Adamant Nature
- Kowtow Cleave
- Iron Head
- Sucker Punch
- Swords Dance
"""

class CustomAgent(Player):
    """
    An expert system agent for Pokémon battles, designed to pilot a specific
    Hyper Offense team based on a detailed, multi-phase game plan.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(team=team, *args, **kwargs)
        # A simple knowledge base of known threats for specific logic.
        self.knowledge_base = {
            "magic_bouncers": ["hatterene", "espeon"],
            "special_walls": ["blissey", "clodsire"],
            "fighting_threats": ["koraidon", "iron hands", "great tusk"]
        }

    def get_move_power(self, move: Move, me: Pokemon, opponent: Pokemon, weather: Weather) -> float:
        """
        Calculates the effective power of a move, considering various battle dynamics.
        """
        power = move.base_power

        # Apply STAB bonus
        if move.type in me.types:
            power *= 1.5

        # Apply weather modifications
        if weather:
            if weather is Weather.SUNNYDAY or weather is Weather.DESOLATELAND:
                if move.type == PokemonType.FIRE:
                    power *= 1.5
                elif move.type == PokemonType.WATER:
                    power *= 0.5
            elif weather is Weather.RAINDANCE or weather is Weather.PRIMORDIALSEA:
                 if move.type == PokemonType.WATER:
                    power *= 1.5
                 elif move.type == PokemonType.FIRE:
                    power *= 0.5
        
        # Special move considerations from our team
        if me.species == "koraidon" and move.id == "collisioncourse" and opponent.damage_multiplier(move) > 1:
            power *= 1.33
        if me.species == "walkingwake" and move.id == "hydrosteam" and (weather is Weather.SUNNYDAY or weather is Weather.DESOLATELAND):
            power *= 1.5

        return power

    def get_deoxys_move(self, battle: AbstractBattle):
        """Phase 1 Logic: Deoxys-Speed as the suicide lead."""
        opponent = battle.opponent_active_pokemon
        
        # Turn 1 Logic: Counter Magic Bounce, otherwise set Stealth Rock.
        if battle.turn == 1:
            if opponent.species in self.knowledge_base["magic_bouncers"]:
                if "taunt" in [m.id for m in battle.available_moves]:
                    return self.create_order(battle.available_moves[[m.id for m in battle.available_moves].index("taunt")])
            if SideCondition.STEALTH_ROCK not in battle.opponent_side_conditions:
                 if "stealthrock" in [m.id for m in battle.available_moves]:
                    return self.create_order(battle.available_moves[[m.id for m in battle.available_moves].index("stealthrock")])

        # Subsequent Turns: Layer hazards or disrupt.
        if SideCondition.STEALTH_ROCK not in battle.opponent_side_conditions:
             if "stealthrock" in [m.id for m in battle.available_moves]:
                return self.create_order(battle.available_moves[[m.id for m in battle.available_moves].index("stealthrock")])
        
        if SideCondition.SPIKES not in battle.opponent_side_conditions or battle.opponent_side_conditions[SideCondition.SPIKES] < 3:
             if "spikes" in [m.id for m in battle.available_moves]:
                return self.create_order(battle.available_moves[[m.id for m in battle.available_moves].index("spikes")])

        if "thunderwave" in [m.id for m in battle.available_moves]:
            return self.create_order(battle.available_moves[[m.id for m in battle.available_moves].index("thunderwave")])
        
        return self.choose_random_move(battle)

    def get_wallbreaker_move(self, battle: AbstractBattle):
        """Phase 2 Logic: For Choice item wallbreakers like Koraidon, Walking Wake, Chi-Yu."""
        me = battle.active_pokemon
        opponent = battle.opponent_active_pokemon
        
        best_move = None
        max_score = -1

        for move in battle.available_moves:
            # Avoid "nuke" moves on frail targets, save them for walls.
            if move.id in ["dracometeor", "overheat"] and opponent.current_hp_fraction < 0.6:
                continue

            # Prioritize U-turn for pivoting if in a bad matchup
            if move.id == "uturn" and opponent.damage_multiplier(me.types[0]) > 1:
                 return self.create_order(move)

            score = self.get_move_power(move, me, opponent, battle.weather) * opponent.damage_multiplier(move)
            if score > max_score:
                max_score = score
                best_move = move
        
        if best_move:
            return self.create_order(best_move)
        return self.choose_random_move(battle)

    def get_sweeper_move(self, battle: AbstractBattle):
        """Phase 3 Logic: For Flutter Mane."""
        me = battle.active_pokemon
        opponent = battle.opponent_active_pokemon

        # Special case for special walls like Blissey
        if opponent.species in self.knowledge_base["special_walls"]:
            if "psyshock" in [m.id for m in battle.available_moves]:
                 return self.create_order(battle.available_moves[[m.id for m in battle.available_moves].index("psyshock")])
        
        # Default to highest damage
        best_move = None
        max_score = -1
        for move in battle.available_moves:
            score = self.get_move_power(move, me, opponent, battle.weather) * opponent.damage_multiplier(move)
            if score > max_score:
                max_score = score
                best_move = move
        
        if best_move:
            return self.create_order(best_move)
        return self.choose_random_move(battle)

    def get_kingambit_move(self, battle: AbstractBattle):
        """Phase 3 Logic: Kingambit, the complex late-game cleaner."""
        me = battle.active_pokemon
        opponent = battle.opponent_active_pokemon
        opponentattack = opponent.stats['atk'] if opponent.stats['atk'] else 0
        opponentspa = opponent.stats['spa'] if opponent.stats['spa'] else 0
        meboostattack = me.boosts['atk'] if me.boosts['atk'] else 0
        
        # Swords Dance Logic: Set up if safe.
        can_survive = True 
        for move in opponent.moves.values():
            if me.damage_multiplier(move) > 1 and (move.base_power > 80 or opponentattack > 100 or opponentspa > 100):
                 can_survive = False
                 break
        if can_survive and meboostattack < 2 and "swordsdance" in [m.id for m in battle.available_moves]:
            return self.create_order(battle.available_moves[[m.id for m in battle.available_moves].index("swordsdance")], terastallize=False)

        # Tera Logic: Use offensively to secure a KO or defensively to survive.
        can_tera = battle.can_tera
        
        # Defensive Tera
        if can_tera and opponent.species in self.knowledge_base["fighting_threats"]:
            return self.create_order(battle.available_moves[[m.id for m in battle.available_moves].index("kowtowcleave")], terastallize=True)

        # Offensive Tera
        best_tera_move = None
        best_regular_move = None
        max_tera_damage = -1
        max_regular_damage = -1

        for move in battle.available_moves:
             if move.category.name != "STATUS":
                regular_damage = self.get_move_power(move, me, opponent, battle.weather) * opponent.damage_multiplier(move)
                
                # Assume Tera Dark for calculation
                tera_power = move.base_power * (2 if move.type == PokemonType.DARK else 1.5 if move.type == PokemonType.STEEL else 1)
                tera_damage = tera_power * opponent.damage_multiplier(move)

                if regular_damage > max_regular_damage:
                    max_regular_damage = regular_damage
                    best_regular_move = move
                if tera_damage > max_tera_damage:
                    max_tera_damage = tera_damage
                    best_tera_move = move

        if can_tera and max_tera_damage > opponent.current_hp and max_regular_damage < opponent.current_hp:
            return self.create_order(best_tera_move, terastallize=True)

        # Sucker Punch Prediction Logic
        myspeed, oppspeed = 0, 0
        myspeed = me.stats['spe'] if me.stats['spe'] else 0
        oppspeed = opponent.stats['spe'] if opponent.stats['spe'] else 0
        if oppspeed > myspeed and opponent.current_hp_fraction < 0.5:
            if "suckerpunch" in [m.id for m in battle.available_moves]:
                return self.create_order(battle.available_moves[[m.id for m in battle.available_moves].index("suckerpunch")])

        # Default to best regular move
        if best_regular_move:
            return self.create_order(best_regular_move)
        return self.choose_random_move(battle)

    def choose_move(self, battle: AbstractBattle):
        """
        Main decision-making function that delegates logic based on the active Pokémon.
        """
        me = battle.active_pokemon
        mespeed = me.base_stats['spe'] if me.base_stats['spe'] else 0
        
        if me.fainted:
            # If our Pokémon fainted, we must switch
            return self.choose_best_switch(battle)

        # Delegate logic based on the active Pokémon's role
        if me.species == "deoxys" and mespeed == 180: # Deoxys-Speed
            return self.get_deoxys_move(battle)
        elif me.species in ["koraidon", "walkingwake", "chiyu"]:
            return self.get_wallbreaker_move(battle)
        elif me.species == "fluttermane":
            return self.get_sweeper_move(battle)
        elif me.species == "kingambit":
            return self.get_kingambit_move(battle)

        # Fallback for any unexpected situation
        return self.choose_random_move(battle)

    def choose_best_switch(self, battle: AbstractBattle):
        """
        Chooses the best Pokémon to switch into.
        """
        best_switch = None
        max_score = -float('inf')
        opponent = battle.opponent_active_pokemon

        for pokemon in battle.available_switches:
            # Score based on type advantage and resistance
            score = -opponent.damage_multiplier(pokemon.types[0])
            if len(pokemon.types) > 1:
                score -= opponent.damage_multiplier(pokemon.types[1])
            
            # Add bonus for super-effective STAB potential
            for move in pokemon.moves.values():
                if move.type in pokemon.types and opponent.damage_multiplier(move) > 1:
                    score += opponent.damage_multiplier(move)

            if score > max_score:
                max_score = score
                best_switch = pokemon
        
        if best_switch:
            return self.create_order(best_switch)
        
        # If no good switch, choose the first available
        return self.choose_random_switch(battle)
