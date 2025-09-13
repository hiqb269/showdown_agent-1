from __future__ import annotations

from typing import Dict, List, Optional, Tuple
import random

from poke_env.battle import AbstractBattle,Weather, MoveCategory
from poke_env.battle.pokemon import Pokemon
from poke_env.battle.move import Move
from poke_env.battle.pokemon_type import PokemonType
from poke_env.player import Player

#Similar team but with hazards and faster
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

# Only multipliers != 1.0 are listed to keep it compact; lookup defaults to 1.0.
TYPE_CHART: Dict[str, Dict[str, float]] = {
    "Normal": {"Rock": 0.5, "Ghost": 0.0, "Steel": 0.5},
    "Fire": {"Fire": 0.5, "Water": 0.5, "Grass": 2.0, "Ice": 2.0, "Bug": 2.0, "Rock": 0.5, "Dragon": 0.5, "Steel": 2.0},
    "Water": {"Fire": 2.0, "Water": 0.5, "Grass": 0.5, "Ground": 2.0, "Rock": 2.0, "Dragon": 0.5},
    "Electric": {"Water": 2.0, "Electric": 0.5, "Grass": 0.5, "Ground": 0.0, "Flying": 2.0, "Dragon": 0.5},
    "Grass": {"Fire": 0.5, "Water": 2.0, "Grass": 0.5, "Poison": 0.5, "Ground": 2.0, "Flying": 0.5, "Bug": 0.5, "Rock": 2.0, "Dragon": 0.5, "Steel": 0.5},
    "Ice": {"Water": 0.5, "Grass": 2.0, "Ice": 0.5, "Ground": 2.0, "Flying": 2.0, "Dragon": 2.0, "Steel": 0.5, "Fire": 0.5},
    "Fighting": {"Normal": 2.0, "Ice": 2.0, "Rock": 2.0, "Dark": 2.0, "Steel": 2.0, "Poison": 0.5, "Flying": 0.5, "Psychic": 0.5, "Bug": 0.5, "Fairy": 0.5, "Ghost": 0.0},
    "Poison": {"Grass": 2.0, "Poison": 0.5, "Ground": 0.5, "Rock": 0.5, "Ghost": 0.5, "Steel": 0.0, "Fairy": 2.0},
    "Ground": {"Fire": 2.0, "Electric": 2.0, "Grass": 0.5, "Poison": 2.0, "Flying": 0.0, "Bug": 0.5, "Rock": 2.0, "Steel": 2.0},
    "Flying": {"Electric": 0.5, "Grass": 2.0, "Fighting": 2.0, "Bug": 2.0, "Rock": 0.5, "Steel": 0.5},
    "Psychic": {"Fighting": 2.0, "Poison": 2.0, "Psychic": 0.5, "Steel": 0.5, "Dark": 0.0},
    "Bug": {"Fire": 0.5, "Grass": 2.0, "Fighting": 0.5, "Poison": 0.5, "Flying": 0.5, "Psychic": 2.0, "Ghost": 0.5, "Dark": 2.0, "Steel": 0.5, "Fairy": 0.5},
    "Rock": {"Fire": 2.0, "Ice": 2.0, "Flying": 2.0, "Bug": 2.0, "Fighting": 0.5, "Ground": 0.5, "Steel": 0.5},
    "Ghost": {"Normal": 0.0, "Psychic": 2.0, "Ghost": 2.0, "Dark": 0.5},
    "Dragon": {"Dragon": 2.0, "Steel": 0.5, "Fairy": 0.0},
    "Dark": {"Fighting": 0.5, "Psychic": 2.0, "Ghost": 2.0, "Dark": 0.5, "Fairy": 0.5},
    "Steel": {"Fire": 0.5, "Water": 0.5, "Electric": 0.5, "Ice": 2.0, "Rock": 2.0, "Fairy": 2.0, "Steel": 0.5},
    "Fairy": {"Fire": 0.5, "Poison": 0.5, "Steel": 0.5, "Fighting": 2.0, "Dragon": 2.0, "Dark": 2.0},
}


# Common set priors (knowledge acquisition): predicted coverage for selected species
COMMON_SETS: Dict[str, List[str]] = {
    # Gen 9 Ubers box legends
    "Koraidon": ["flareblitz", "closecombat", "dragonclaw", "uturn", "collisioncourse", "outrage"],
    "Miraidon": ["electrodrift", "dracometeor", "voltswitch", "overheat", "calmmind", "paraboliccharge"],

    # Zacian (still Uber)
    "Zacian-Crowned": ["behemothblade", "closecombat", "playrough", "wildcharge", "crunch"],

    # Common Paradox / Gen 9 Ubers bans
    "Flutter Mane": ["shadowball", "moonblast", "calmmind", "substitute", "taunt"],
    "Chi-Yu": ["overheat", "darkpulse", "taunt", "nastyplot", "terablast"],
    "Chien-Pao": ["icespinner", "suckerpunch", "swordsdance", "sacredsword", "crunch"],
    "Iron Bundle": ["hydropump", "freezedry", "flipturn", "icespinner", "taunt"],
    "Palafin-Hero": ["wavecrash", "jetpunch", "flipturn", "taunt", "icepunch"],

    # Ubers defensive staples (Gen 9 OU mons usable in Ubers)
    "Great Tusk": ["headlongrush", "closecombat", "rapidspin", "knockoff", "icespinner"],
    "Ting-Lu": ["ruination", "earthquake", "stealthrock", "whirlwind", "spikes"],
    "Hatterene": ["drainingkiss", "psyshock", "mysticalfire", "calmmind"],
    "Skeledirge": ["torchsong", "slackoff", "shadowball", "willowisp", "earthpower"],
    "Garganacl": ["saltcure", "recover", "irondefense", "bodypress", "stealthrock"],
    "Glimmora": ["mortalspin", "stealthrock", "earthpower", "sludgewave", "spikes"],
    "Roaring Moon": ["dragonclaw", "acrobatic", "uturn", "jawlock", "dragondance"],

    # Arceus forms (biggest staples in SV Ubers)
    "Arceus-Normal": ["extremespeed", "swordsdance", "earthquake", "recover"],
    "Arceus-Ghost": ["judgment", "calmmind", "recover", "focusblast"],
    "Arceus-Dark": ["judgment", "calmmind", "recover", "earthpower"],
    "Arceus-Grass": ["judgment", "toxic", "recover", "earthpower"],
    "Arceus-Ground": ["judgment", "calmmind", "recover", "earthpower", "icebeam"],
    "Arceus-Water": ["judgment", "toxic", "recover", "calmmind", "icebeam"],
    "Arceus-Fairy": ["judgment", "calmmind", "recover", "earthpower", "moonblast"],

    # Legacy Ubers that are still staples
    "Necrozma-Dusk-Mane": ["sunsteelstrike", "earthquake", "morningsun", "stealthrock", "dragonclaw"],
    "Eternatus": ["sludgebomb", "flamethrower", "recover", "toxicspikes", "dynamaxcannon"],
    "Calyrex-Shadow": ["astralbarrage", "psyshock", "nastyplot", "substitute", "drainingkiss"],
    "Calyrex-Ice": ["glaciallance", "highhorsepower", "trickroom", "swordsdance"],
    "Ho-Oh": ["sacredfire", "bravebird", "recover", "defog", "earthquake"],
    "Lugia": ["toxic", "whirlwind", "recover", "icebeam", "aeroblast"],
    "Giratina": ["dragontail", "toxic", "defog", "rest", "willowisp"],
    "Giratina-Origin": ["dracometeor", "shadowball", "aurasphere", "defog"],
    "Dialga-Origin": ["dracometeor", "flashcannon", "stealthrock", "fireblast"],
    "Rayquaza": ["dragondance", "earthquake", "outrage", "extremespeed", "vcreate"],
    "Darkrai": ["darkpulse", "nastyplot", "sludgebomb", "focusblast", "hypnosis"],
    "Groudon": ["precipiceblades", "stealthrock", "stoneedge", "dragontail", "heatcrash"],

    # Primals/Restricted legends still legal in NatDex Ubers
    "Kyogre": ["waterspout", "thunder", "icebeam", "originpulse", "calmmind", "surf"],
}




def type_name(t: Optional[PokemonType]) -> Optional[str]:
    if t is None:
        return None
    return getattr(t, "name", str(t))


def move_type_name(m: Move) -> Optional[str]:
    return type_name(m.type) if hasattr(m, "type") else None

def predict_effectiveness(atk_type: Optional[str], def_types: List[str]) -> float:
    if not atk_type or not def_types:
        return 1.0
    mult = 1.0
    chart_row = TYPE_CHART.get(atk_type, {})
    for dt in def_types:
        mult *= chart_row.get(dt, 1.0)
    return mult


def effectiveness(move: Move, defender: Pokemon) -> float:
    if not move or not defender.types:
        return 1.0
    mult = 1.0
    mult = defender.damage_multiplier(move) 
    return mult


def has_stab(move: Move, attacker: Pokemon) -> bool:
    if not move.type:
        return False
    move_type = move.type.name if hasattr(move.type, "name") else str(move.type)
    return move_type in attacker.types


def approx_speed(p: Pokemon) -> int:
    # EV/IV unknown: assume max speed if fast archetype, else neutral
    base = float(getattr(p, "base_speed", 0) or 0)
    #base = BASE_SPEED.get(p.species, 80)
    # Rough boost handling
    boost = p.boosts.get("spe", 0) if p.boosts else 0
    # +1 ~ x1.5, -1 ~ x0.67; we translate to an integer multiplier
    mult = { -6: 2/8, -5: 2/7, -4: 2/6, -3: 2/5, -2: 2/4, -1: 2/3,
              0: 1.0, 1: 3/2, 2: 4/2, 3: 5/2, 4: 6/2, 5: 7/2, 6: 8/2 }.get(boost, 1.0)
    #TODO: account for items/abilities that modify speed
    return int(base * mult)

def estimate_speed(pokemon):
    base_speed = pokemon.base_stats.get('spe', 0)
    # Assume level 100 and common investment: max for base >= 100, else neutral
    if base_speed >= 100:
        # Max investment: 31 IV, 252 EV, beneficial nature (1.1x)
        raw_speed = (2 * base_speed + 31 + 63) + 5  # 63 from floor(252/4)
        estimated_speed = int(raw_speed * 1.1)
    else:
        # Neutral investment: 31 IV, 0 EV, neutral nature (1.0x)
        estimated_speed = (2 * base_speed + 31 + 0) + 5

    # Apply boosts/drops (from moves like Dragon Dance)
    boost = pokemon.boosts.get('spe', 0) if hasattr(pokemon, 'boosts') else 0
    multiplier = {
        -6: 0.25, -5: 2/7, -4: 2/6, -3: 0.4, -2: 0.5, -1: 2/3,
        0: 1.0, 1: 1.5, 2: 2.0, 3: 2.5, 4: 3.0, 5: 3.5, 6: 4.0
    }.get(boost, 1.0)
    estimated_speed *= multiplier

    # Account for common items and abilities if possible
    if hasattr(pokemon, 'item'):
        if pokemon.item == 'choicescarf':
            estimated_speed *= 1.5
    if hasattr(pokemon, 'ability'): # TODO: check for speed abilities
        if pokemon.ability == 'speedboost':
            # Speed Boost adds +1 boost per turn, but you might need to track turns
            # For simplicity, assume no extra boosts unless known
            pass  # You might add a boost here if you know it activated

    return int(estimated_speed)


def is_first_one_faster(p1: Pokemon, p2: Pokemon) -> bool:
    #return approx_speed(p1) > approx_speed(p2)
    return estimate_speed(p1) > estimate_speed(p2)


def current_hp_fraction(p: Pokemon) -> float:
    if p.max_hp == 0:
        return 1.0
    return max(0.0, min(1.0, p.current_hp / p.max_hp))


def pokemon_types(p: Pokemon) -> List[str]:
    return [t.name for t in p.types if t is not None]


def is_status_move(m: Move) -> bool:
    return str(m.category).lower() == "status"


def is_hazard_move(m: Move) -> bool:
    name = m.id
    return name in {"stealthrock", "spikes", "toxicspikes", "stickyweb"}


def is_removal_move(m: Move) -> bool:
    name = m.id
    return name in {"rapidspin", "defog", "mortalspin"}



def would_be_ineffective(move: Move, defender: Pokemon) -> bool:
    atk_type = move_type_name(move)
    #eff = effectiveness(atk_type, pokemon_types(defender))
    eff = defender.damage_multiplier(move)  # use built-in method if available
    return eff == 0.0


def has_our_hazards(battle: AbstractBattle) -> bool:
    side = battle.side_conditions
    return any(k in side for k in ["spikes", "toxicspikes", "stealthrock", "stickyweb"])


def has_opp_hazards(battle: AbstractBattle) -> bool:
    opp = battle.opponent_side_conditions
    return any(k in opp for k in ["spikes", "toxicspikes", "stealthrock", "stickyweb"])


def rocks_up_for_opp(battle: AbstractBattle) -> bool:
    return "stealthrock" in battle.opponent_side_conditions


class OpponentModel:
    def __init__(self):
        # species -> set of revealed moves
        self.revealed: Dict[str, set] = {}
        # species -> plausible moves (start with priors)
        self.plausible: Dict[str, set] = {}

    def update_with_battle(self, battle: AbstractBattle):
        opp = battle.opponent_active_pokemon
        if not opp:
            return
        # Add the opponent to the model if not already present
        if opp.species not in self.revealed:
            self.revealed[opp.species] = set()
            self.plausible[opp.species] = set(COMMON_SETS.get(opp.species, []))  # should fill like this or not?

        # Add revealed moves if present
        for m in opp.moves.values():
            if m and m.id:
                self.revealed[opp.species].add(m.id)
                # Keep plausible set in sync
                if m.id not in self.plausible[opp.species]:
                    self.plausible[opp.species].add(m.id)

    def likely_strong_moves(self, species: str, defender: Pokemon) -> List[str]:
        # Rank plausible moves by predicted effectiveness vs defender
        moves = list(self.plausible.get(species, []))
        if not defender or not moves:
            return []
        ranked = []
        for move_id in moves:
            # Fake Move-like object for type lookup; we only want type-effectiveness guess
            # Without a full dex, infer type from common move names (minimal heuristic)
            # You can expand this mapping for better predictions.
            name_lower = move_id.lower()
            guessed_type = None
            # Simple keywords to type mapping (extend over time)
            if "draco" in name_lower or "dragon" in name_lower:
                guessed_type = "Dragon"
            elif "electro" in name_lower or "volt" in name_lower or "thunder" in name_lower or "charge" in name_lower:
                guessed_type = "Electric"
            elif "flare" in name_lower or "overheat" in name_lower or "fire" in name_lower or "blitz" in name_lower:
                guessed_type = "Fire"
            elif "earth" in name_lower or "quake" in name_lower or "headlong" in name_lower:
                guessed_type = "Ground"
            elif "play" in name_lower or "kiss" in name_lower or "gleam" in name_lower or "fairy" in name_lower:
                guessed_type = "Fairy"
            elif "close combat" in name_lower or "collision" in name_lower or "low kick" in name_lower:
                guessed_type = "Fighting"
            elif "psy" in name_lower:
                guessed_type = "Psychic"
            elif "shadow" in name_lower or "hex" in name_lower:
                guessed_type = "Ghost"
            elif "hydro" in name_lower or "surf" in name_lower or "water" in name_lower:
                guessed_type = "Water"
            elif "leaf" in name_lower or "grass" in name_lower or "seed" in name_lower:
                guessed_type = "Grass"
            elif "ice" in name_lower or "freeze" in name_lower:
                guessed_type = "Ice"
            elif "rock" in name_lower or "stone" in name_lower:
                guessed_type = "Rock"
            elif "bug" in name_lower or "u-turn" in name_lower:
                guessed_type = "Bug"
            elif "dark" in name_lower or "crunch" in name_lower or "knock" in name_lower:
                guessed_type = "Dark"
            elif "steel" in name_lower or "iron" in name_lower:
                guessed_type = "Steel"

            eff = predict_effectiveness(guessed_type, pokemon_types(defender)) if guessed_type else 1.0
            #eff = defender.damage_multiplier(Move(move_id, 0, None, None))  # use built-in method if available
            if(eff > 1.0):  # only consider super-effective moves
                ranked.append((eff, move_id))
        ranked.sort(reverse=True)
        return ranked
        #return [n for _, n in ranked]


class CustomAgent(Player):
    def __init__(self, *args, **kwargs):
        super().__init__(team=team, *args, **kwargs)
        self.opp_model = OpponentModel()
        self.debug = True  # Turn off to silence reasoning logs

        # Track our nominated win conditions (species we want to preserve)???
        self.win_cons: List[str] = ["Zacian-Crowned", "Kyogre", "Arceus-Fairy"]

    # ---- Explanation module ----
    def log(self, battle: AbstractBattle, msg: str):
        if self.debug:
            print(f"[Turn {battle.turn}] {msg}")

    # ---- Core decision logic ----
    def choose_move(self, battle: AbstractBattle):
        # Update opponent model from current state
        self.log(battle, f"Active: {battle.active_pokemon.species if battle.active_pokemon else 'None'} \
                 ({battle.active_pokemon.current_hp_fraction:.2%} HP) vs \
                    {battle.opponent_active_pokemon.species if battle.opponent_active_pokemon else 'None'} \
                        ({battle.opponent_active_pokemon.current_hp_fraction:.2%} HP) with available moves \
                            {', '.join([m.id for m in battle.available_moves]) if battle.available_moves else 'None'}")
        self.opp_model.update_with_battle(battle)
        me = battle.active_pokemon
        opp = battle.opponent_active_pokemon

        # If we must force a random choice (e.g., struggle), fallback
        if battle.force_switch or (me.current_hp < 30 or me.current_hp_fraction < 0.3 ): #switch out at low hp
            self.log(battle, f"Forced switch required. Current pokemon: {battle.active_pokemon.species if battle.active_pokemon \
        else 'None'} and current pokemon hp is {battle.active_pokemon.current_hp if battle.active_pokemon else 'None'} \
        and available moves are {', '.join([m.id for m in battle.available_moves]) if battle.available_moves else 'None'}")
            choice = self._choose_best_switch(battle)
            if choice:
                self.log(battle, f"Forced switch -> {choice.species}")
                return self.create_order(choice)
            else:
                self.log(battle, "No valid switch available for forced switch, choosing random move.")
                return self.choose_random_move(battle)
            #return self.choose_random_switch(battle) #why random switch?

        # Early hazard plan
        if self._should_set_rocks(battle):
            for m in battle.available_moves:
                if (m.id == "stealthrock") and not rocks_up_for_opp(battle):
                    self.log(battle, "Setting Stealth Rock (early-game hazard priority).")
                    return self.create_order(m)

        # Hazard removal if pressured
        if self._should_remove_hazards(battle):
            for m in battle.available_moves:
                if is_removal_move(m):
                    self.log(battle, "Removing hazards from our side.")
                    return self.create_order(m)
                
        is_opponent_faster_and_lethal = False
        _, opp_is_ko, opp_attack_move_exists = self._select_best_move(battle, False)
        opp_faster = is_first_one_faster(opp, me) 
        opp_dangerous =predict_effectiveness(pokemon_types(opp)[0], pokemon_types(me)) >=2.0
        if opp_faster and (opp_is_ko or opp_dangerous):
            is_opponent_faster_and_lethal = True
            self.log(battle, f"Opponent {opp.species} is faster and likely dangerous.")
            choice = self._choose_best_switch(battle)
            if choice:
                self.log(battle, f"Switching to {choice.species} to avoid KO threat.")
                return self.create_order(choice)
            else:
                self.log(battle, "No valid switch available to avoid KO threat, proceeding with attack.")

        # Evaluate attacking options
        if battle.available_moves:
            #best_move, best_score, rationale = self._best_attacking_move(battle)
            best_move, is_ko, attack_move_exists = self._select_best_move(battle, True)
            if best_move and is_ko:
                self.log(battle, f"Move chosen: {best_move.id} | Potential KO move")
                return self.create_order(best_move)
            elif best_move and attack_move_exists:
                best_score = 10  # placeholder
            else:
                best_score = 1.00
            rationale = "Best estimated damage move"
        else:
            best_move, best_score, rationale = (None, -1.0, "No moves available")

        # Evaluate switching options for safety
        if opp.moves:
            if opp_is_ko and battle.available_switches:
                self.log(battle, f"Opponent likely has a KO move ({', '.join(opp.moves.keys())}), considering switch.")
                choice = self._choose_best_switch(battle)
                if choice:
                    self.log(battle, f"Switching to {choice.species} to avoid KO threat.")
                    return self.create_order(choice)
                else:
                    self.log(battle, "No valid switch available to avoid KO threat, proceeding with attack.")

        elif(predict_effectiveness(pokemon_types(opp)[0], pokemon_types(me)) >=2.0): 
            #switch if opponent is super effective and we don't have a good move
            choice = self._choose_best_switch(battle)
            if choice:
                self.log(battle, f"Switching to {choice.species} to avoid super-effective hit.")
                return self.create_order(choice)
            else:
                self.log(battle, "No valid switch available to avoid super-effective hit, proceeding with attack.")
        best_switch, switch_score, switch_reason = self.choose_best_switch(battle)

        # Final decision: compare best move vs best switch
        if best_move:
            if attack_move_exists: #and (best_score >= switch_score or not best_switch):
                self.log(battle, f"Move chosen: {best_move.id} | {rationale}")
                # Optional: add simple tera logic (very conservative)
                # if battle.can_tera and self._tera_secures_ko(battle, best_move):
                #     self.log(battle, "Terastallizing to secure KO.")
                #     return self.create_order(best_move, terastallize=True)
                return self.create_order(best_move)
            elif best_switch:
                if switch_score >= opp.current_hp:
                    self.log(battle, "No valid attack move available, considering switch.")
                    return self.create_order(best_switch)
                else:
                    self.log(battle, f"Choosing to move over switch :{best_switch.species} Move chosen: {best_move }")
                    return self.create_order(best_move)

        if best_switch:
            self.log(battle, f"Switch chosen: {best_switch.species} | {switch_reason}")
            return self.create_order(best_switch)

        # Fallback
        self.log(battle, "Fallback: random choice.")
        return self.choose_random_move(battle)


    def get_weather_multiplier(self, weathers: list[Weather], move: Move) -> float:
        mult: float = 1.0
        for weather in weathers:
            if weather == Weather.SUNNYDAY:
                if move.type == PokemonType.FIRE:
                    mult = mult * 1.5
                elif move.type == PokemonType.WATER:
                    mult = mult * 0.5
            elif weather == Weather.RAINDANCE:
                    if move.type == PokemonType.FIRE:
                        mult = mult * 0.5
                    elif move.type == PokemonType.WATER:
                        mult = mult * 1.5
        return mult

    def estimate_damage(self, move: Move, attacker: Pokemon, defender: Pokemon, weather: Weather) -> Tuple[float, float, float]:
        # Very rough expected-damage heuristic combining base power, STAB, effectiveness, and boosts
        if is_status_move(move) or move.base_power is None or move.base_power <= 0:
            return 0.0, 0.0, 0.0  # status moves do no damage but may be needed

        eff = defender.damage_multiplier(move)  
        stab = 1.5 if has_stab(move, attacker) else 1.0

        weather_mult = self.get_weather_multiplier([weather], move) if weather else 1.0

        # Boost factor: account for attacker offensive boosts and defender defensive boosts
        off_key = "atk" if str(move.category).lower() == "physical" else "spa"
        def_key = "def" if str(move.category).lower() == "physical" else "spd"

        off_boost = (attacker.boosts.get(off_key, 0) if attacker.boosts else 0)
        def_boost = (defender.boosts.get(def_key, 0) if defender.boosts else 0)

        # Translate stat stages to multipliers (2+n)/2 for positive, 2/(2-n) for negative
        # https://www.smogon.com/dp/articles/damage_formula
        def stage_mult(stage: int) -> float:
            if stage >= 0:
                return (2 + stage) / 2
            return 2 / (2 - stage)

        off_mult = stage_mult(off_boost)
        def_mult = stage_mult(def_boost)

        base = move.base_power or 0
        #TODO: consider items, abilities and terrain
        # Randomness & miscellaneous (items, abilities) folded into a conservative factor
        rng_factor = 0.92  # slightly conservative

        multiplier = eff * stab * weather_mult * (off_mult / def_mult) 
        score = base * multiplier * rng_factor

        # Small priority bonus to accurate moves
        if move.accuracy is not None:
            acc = move.accuracy
            # Normalize only if value looks like a percentage
            if acc > 1.5:  # e.g. 100 instead of 1.0
                acc = acc / 100.0
            score *= acc

        recoildamage = 0;
        if getattr(move, "recoil", 0):
            recoil = move.recoil;
            recoildamage = float(score * recoil);
            #score *= 0.95

        return multiplier, score, recoildamage

    def _assign_move_ranks(self, battle: AbstractBattle, for_me: bool = True) -> Optional[List[Dict]]:
        attacker, defender, moves = None, None, None
        if for_me:
            attacker = battle.active_pokemon
            defender = battle.opponent_active_pokemon
            moves = battle.available_moves
        else:
            attacker = battle.opponent_active_pokemon
            defender = battle.active_pokemon
            moves = battle.opponent_active_pokemon.moves.values()
        if not attacker or not defender or not moves:
            return None
        
        damage = 0.0
        recoildamage = 0.0
        #TEST
        move_ids = [m.id for m in moves if hasattr(m, "id")]
        self.log(battle, f"Evaluating moves {', '.join(move_ids)} for {attacker.species} vs {defender.species}")
         # Rank moves by estimated damage and other factors
        move_ranks = []
        for move in moves:
            if move.base_power > 0:
                eff = defender.damage_multiplier(move)
                eff_2, damage, recoildamage= self.estimate_damage(move, attacker, defender, battle.weather)
                move_info = {
                    "move": move,
                    "base_power": move.base_power,
                    "effectiveness": eff,
                    "damage": damage, 
                    "recoildamage": recoildamage,
                    "can_KO": self.is_possible_KO(eff,damage, defender),
                    "can_recoil_KO": self.is_possible_KO(1.5, recoildamage, attacker),
                    "is_super_effective": eff > 1.0,
                    "is_resisted": eff < 1.0,
                    "is_neutral": eff == 1.0,
                    "is_status": is_status_move(move),
                }
                move_ranks.append(move_info)
        return move_ranks
    
    def is_possible_KO(self, eff:float, damage: float, target: Pokemon) -> bool:
        if not target or target.current_hp is None:
            return False
        #def_max_hp = target.max_hp if target.max_hp and target.max_hp > 0 else 200.0
        #est_fraction = min(1.0, damage / def_max_hp)  
        #if est_fraction >= current_hp_fraction(target):
        #    return True
        if eff > 1.0 and damage >= target.current_hp:
            return True
        return False

    def _select_best_move(self, battle: AbstractBattle, for_me: bool) -> Tuple[Optional[Move], bool, bool]:
        move_ranks = self._assign_move_ranks(battle, for_me)
        best_move, is_ko, attack_move_exists = self.choose_best_move(move_ranks, battle)
        return best_move, is_ko, attack_move_exists


    def choose_best_move(self, move_ranks: List[Dict], battle: AbstractBattle) -> Tuple[Optional[Move], bool, bool]:
        if not move_ranks or len(move_ranks) == 0:
            return None, False, False
        print(move_ranks)
        komove = None
        bestmove = None
        # If any move can KO, pick the highest scoring KO move
        if exists := [m for m in move_ranks if m["can_KO"]]:
            self.log(battle, f"Found {len(exists)} moves that can KO the opponent.")
            exists.sort(key=lambda x: x["damage"], reverse=True)
            komove = exists[0]["move"]
            self.log(battle, f"Choosing KO move {komove.id} with damage {exists[0]['damage']:.1f}.")
            return komove, True, True
        # Sort moves by damage descending
        move_ranks.sort(key=lambda x: x["damage"], reverse=True)
        attack_move_exists = True
        if not move_ranks[0]["is_super_effective"]:  # No super effective move
            attack_move_exists = False
            self.log(battle, "No effective attacking move found, choosing next best")
        #TODO: choose healing move or neutral move?
        bestmove = move_ranks[0]["move"]
        return bestmove, False, attack_move_exists

    def choose_best_switch(self, battle: AbstractBattle) -> Tuple[Optional[Pokemon], float, str]:
        me = battle.active_pokemon
        opp = battle.opponent_active_pokemon
        if not opp or not battle.available_switches:
            return None, -1.0, "No switches"
        
        if opp.moves is None or len(opp.moves) < 4:
            self.log(battle, f"All moves for {opp.species} not yet known; guess likely STABs")
            
        # Evaluate switches by how well they resist likely moves and threaten back
        candidates = []
        likely = self.opp_model.likely_strong_moves(opp.species, me)  # may be empty #only bring strong moves
        for sw in battle.available_switches:
            # Defensive merit: count resistances to opponent's STABs (approx via species priors)
            # Simple: if switch resists opp's primary STAB (guess by species), score higher
            resist_score = 0.0
            if opp.moves is None or len(opp.moves) < 4:
                stab_types = self._guess_stab_types(opp.species)
                for t in stab_types:
                    resist_score += {0.5: 8.0, 0.0: 12.0, 2.0: -10.0, 1.0: 0.0}.get(predict_effectiveness(t, pokemon_types(sw)), 0.0)
                if likely:
                    for ef, _ in likely:
                        resist_score += {0.5: 8.0, 0.0: 12.0, 2.0: -10.0, 1.0: 0.0}.get(ef, 0.0)
            if opp.moves:
                for mv in opp.moves.values():
                    if not mv or not mv.id:
                        continue
                    eff = self.estimate_damage(mv,opp, sw, battle.weather)[0]
                    if eff <= 0.0:
                        bucket = 0.0  # immune
                    elif eff < 0.75:
                        bucket = 0.5  # resist
                    elif eff < 1.5:
                        bucket = 1.0  # neutral
                    else:
                        bucket = 2.0  # super-effective

                    resist_score += {0.5: 8.0, 0.0: 12.0, 2.0: -10.0, 1.0: 0.0}.get(bucket, 0.0)
                    #resist_score += {0.5: 8.0, 0.0: 12.0, 2.0: -10.0, 1.0: 0.0}.get(eff, 0.0)
            # Offensive threat after switch: check our best immediate move
            threat = 0.0
            threatmult = 0.0
            if sw.moves:
                # Synthesize a rough "best move" vs opp
                for m in sw.moves.values():
                    if not m:
                        continue
                    if not is_status_move(m):
                        #threat = max(threat, effectiveness(m, opp) * (1.5 if has_stab(m, sw) else 1.0))
                        threat = max(threat, self.estimate_damage(m,sw, opp, battle.weather)[1])
                        threatmult = max(threatmult, self.estimate_damage(m,sw, opp, battle.weather)[0])
            # Health consideration
            hp_factor = current_hp_fraction(sw) * 10.0
            hp_factor= sw.current_hp_fraction
            self.log(battle, f"Switch candidate {sw.species}: resist_score {resist_score:.1f}, threat {threat:.1f}, hp_factor {hp_factor:.1f}")
            score = resist_score + threat + hp_factor #TOO simplisitic?
            candidates.append((sw, threat, threatmult, hp_factor, resist_score))

        if not candidates:
            return None, -1.0, "No candidates"
        # Sort by: highest resist_score, then highest threat, then highest current_hp_fraction
        candidates_sorted = sorted(
            candidates,
            key=lambda x: (x[4], x[1], x[3]),  # x[4]=resist_score, x[1]=threat, x[3]=current_hp_fraction
            reverse=True
        )
        #candidates.sort(reverse=True, key=lambda x: x[0])
        best_sw = candidates_sorted[0][0]
        #best_score = candidates_sorted[0][2] + candidates_sorted[0][3] + candidates_sorted[0][4]
        high_threat = candidates_sorted[0][1] 

        reason = f"Resists predicted STABs and can threaten back (score {high_threat:.1f})."
        return best_sw, high_threat, reason

    def _guess_stab_types(self, species: str) -> List[str]:
        # Minimal mapping to primary typing for key threats
        # Extend with more species as needed.
        guess = {
            "Koraidon": ["Fighting", "Dragon"],
            "Zacian-Crowned": ["Fairy", "Steel"],
            "Flutter Mane": ["Ghost", "Fairy"],
            "Great Tusk": ["Ground", "Fighting"],
            "Ting-Lu": ["Ground", "Dark"],
        }
        return guess.get(species, [])

    def _choose_best_switch(self, battle: AbstractBattle) -> Optional[Pokemon]:
        sw, _, _ = self.choose_best_switch(battle)
        return sw

    # Optional: very conservative tera usage example (disabled by default)
    def _tera_secures_ko(self, battle: AbstractBattle, move: Move) -> bool:
        # Heuristic: if tera grants STAB where we didn't have it and bumps predicted KO, allow
        me = battle.active_pokemon
        opp = battle.opponent_active_pokemon
        if not battle.can_tera or not me or not opp:
            return False
        atk_type = move_type_name(move)
        if not atk_type:
            return False
        already_stab = has_stab(move, me)
        if already_stab:
            return False
        # Assume tera type equals move type if possible (Showdown requires choosing team tera; poke_env tracks available)
        # Without exact tera info here, return False to avoid misuse.
        return False
    

    #unused functions here
    def _should_set_rocks(self, battle: AbstractBattle) -> bool:
        # Prefer to set rocks early if:
        # - We have a healthy setter in vs. a passive or forced target
        # - Opponent hasn't got HDB spam (we can't know reliably; still good baseline)
        me = battle.active_pokemon
        opp = battle.opponent_active_pokemon
        if not me or not opp:
            return False
        if rocks_up_for_opp(battle):
            return False
        # If we are Ting-Lu and relatively safe, set rocks
        if me.species == "Ting-Lu" and current_hp_fraction(me) > 0.6:
            # Avoid setting into obvious threatening super-effective hits
            # If opp likely to KO us with a strong SE hit, don't set
            if not self._opp_can_threaten_heavily(battle, me):
                return True
        return False

    def _should_remove_hazards(self, battle: AbstractBattle) -> bool:
        # Remove hazards if we have multiple hazards up and a spinner in safely
        if not has_our_hazards(battle):
            return False
        me = battle.active_pokemon
        if not me:
            return False
        # Great Tusk is our remover; remove if we're not about to be KO'd
        if me.species == "Great Tusk":
            if not self._opp_can_threaten_heavily(battle, me):
                return True
        return False

    def _opp_can_threaten_heavily(self, battle: AbstractBattle, target: Pokemon) -> bool:
        opp = battle.opponent_active_pokemon
        if not opp or not target:
            return False
        likely = self.opp_model.likely_strong_moves(opp.species, target)
        # If any likely move is super-effective, consider threatened
        for mv in likely[:2]:
            # quick type guess already done in model via effectiveness
            # If we have no likely list yet, be conservative iff target < 60%
            pass
        # Conservative fallback: if we're below 60% vs a known breaker, consider threatened
        if opp.species in {"Koraidon", "Miraidon", "Zacian-Crowned", "Flutter Mane"} and current_hp_fraction(target) < 0.6:
            return True
        return False

    
    def _best_attacking_move(self, battle: AbstractBattle) -> Tuple[Optional[Move], float, str]:
        me = battle.active_pokemon
        opp = battle.opponent_active_pokemon
        if not me or not opp or not battle.available_moves:
            return None, -1.0, "No valid attacker/defender"

        # Speed awareness: if we're slower and at risk, favor safer plays
        my_speed = approx_speed(me)
        opp_speed = approx_speed(opp)
        we_outspeed = my_speed >= opp_speed
        self.log(battle, f"Speed check: we {my_speed} vs opp {opp_speed} -> {'outspeed' if we_outspeed else 'underspeed or tie'}")  

        best = None
        best_score = -1.0
        rationale = ""
        for m in battle.available_moves:
            status_move = is_status_move(m)
            ineffective_move = would_be_ineffective(m, opp)
            self.log(battle, f"Evaluating move {m.id}: {'status' if status_move else 'not status.move'}, {'ineffective' if ineffective_move else 'potentially effective'}")
            if not status_move and ineffective_move:
                continue

            _,score, _ = self.estimate_damage(m, me, opp, battle.weather)
            self.log(battle, f"Move {m.id} rough damage score: {score}")

            def_max_hp = opp.max_hp if opp.max_hp and opp.max_hp > 0 else 200.0

            # Priority heuristic: prefer KO lines
            # Estimate % damage by normalizing score to a rough scale
            # We don't have a true calc; use a soft cap for ranking
            est_fraction = min(1.0, score / def_max_hp)  # tune this as you test
            if est_fraction >= current_hp_fraction(opp) - 0.05:
                score += 120.0  # KO bonus

            # Prefer pivoting (U-turn/Volt Switch) when we don't KO and we are faster
            if we_outspeed and m.id in {"uturn", "voltswitch"} and est_fraction < 0.5:
                score += 35.0

            # Prefer accurate moves when close
            if m.accuracy is not None and (m.accuracy >= 90 or m.accuracy >= 0.9):
                score += 8.0

            # Strategic biases per role
            if me.species in self.win_cons and current_hp_fraction(me) > 0.5:
                # Preserve wincons: avoid recoil if not needed
                if getattr(m, "recoil", 0):
                    score *= 0.97

            # Status utility (situational)
            if is_status_move(m):
                # E.g., Whirlwind on Ting-Lu vs setup, Calm Mind on Hatterene in safe spots
                if me.species == "Ting-Lu" and (m.id == "whirlwind"):
                    score = 40.0
                elif me.species == "Hatterene" and (m.id == "calmmind") and current_hp_fraction(me) > 0.6:
                    score = 45.0
                elif is_hazard_move(m) and not rocks_up_for_opp(battle):
                    score = 50.0
                else:
                    score = max(score, 5.0)

            self.log(battle, f"Move {m.id} final score: {score} best so far: {best_score}")

            if score > best_score:
                self.log(battle, f"New best move candidate: {m.id} with score {score}")
                best_score = score
                best = m

        if best is None:
            # If all were ineffective, pick any status/neutral
            best = random.choice(battle.available_moves)
            best_score = 0.0
            rationale = "All moves ineffective; choosing fallback."
        else:
            rationale = self._explain_move_choice(best, me, opp)

        return best, best_score, rationale

    def _explain_move_choice(self, move: Move, me: Pokemon, opp: Pokemon) -> str:
        atk_type = move_type_name(move) or "Unknown"
        eff= opp.damage_multiplier(move)  # use built-in method if available
        stab = "with STAB" if has_stab(move, me) else "without STAB"
        details = []
        if eff == 0.0:
            details.append("ineffective (coverage bait)")
        elif eff > 1.0:
            details.append("super-effective")
        elif eff < 1.0:
            details.append("resisted")
        if is_status_move(move):
            details.append("utility")
        if move.accuracy is not None:
            details.append(f"{move.accuracy} acc")
        return f"{move.id} ({atk_type}) chosen: {'; '.join(details)} {stab}."