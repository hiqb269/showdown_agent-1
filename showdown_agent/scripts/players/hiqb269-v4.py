from __future__ import annotations

from typing import Dict, List, Optional, Tuple
import random

from poke_env.battle import AbstractBattle,Weather, MoveCategory
from poke_env.battle.pokemon import Pokemon
from poke_env.battle.move import Move
from poke_env.battle.pokemon_type import PokemonType
from poke_env.player import Player

team = """
Necrozma-Dusk-Mane @ Rocky Helmet  
Ability: Prism Armor  
Tera Type: Water  
EVs: 252 HP / 252 Def / 4 SpD  
Impish Nature  
- Sunsteel Strike  
- Earthquake  
- Stealth Rock  
- Morning Sun  

Koraidon @ Choice Band  
Ability: Orichalcum Pulse  
Tera Type: Fire  
EVs: 252 Atk / 4 SpD / 252 Spe  
Jolly Nature  
- Flare Blitz  
- Close Combat  
- Outrage  
- U-turn  

Kyogre @ Choice Specs  
Ability: Drizzle  
Tera Type: Water  
EVs: 252 SpA / 4 SpD / 252 Spe  
Modest Nature  
- Water Spout  
- Origin Pulse  
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
EVs: 248 HP / 200 SpD / 60 Atk  
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
    "normal": {"rock": 0.5, "ghost": 0.0, "steel": 0.5},
    "fire": {"fire": 0.5, "water": 0.5, "grass": 2.0, "ice": 2.0, "bug": 2.0, "rock": 0.5, "dragon": 0.5, "steel": 2.0},
    "water": {"fire": 2.0, "water": 0.5, "grass": 0.5, "ground": 2.0, "rock": 2.0, "dragon": 0.5},
    "electric": {"water": 2.0, "electric": 0.5, "grass": 0.5, "ground": 0.0, "flying": 2.0, "dragon": 0.5},
    "grass": {"fire": 0.5, "water": 2.0, "grass": 0.5, "poison": 0.5, "ground": 2.0, "flying": 0.5, "bug": 0.5, "rock": 2.0, "dragon": 0.5, "steel": 0.5},
    "ice": {"water": 0.5, "grass": 2.0, "ice": 0.5, "ground": 2.0, "flying": 2.0, "dragon": 2.0, "steel": 0.5, "fire": 0.5},
    "fighting": {"normal": 2.0, "ice": 2.0, "rock": 2.0, "dark": 2.0, "steel": 2.0, "poison": 0.5, "flying": 0.5, "psychic": 0.5, "bug": 0.5, "fairy": 0.5, "ghost": 0.0},
    "poison": {"grass": 2.0, "poison": 0.5, "ground": 0.5, "rock": 0.5, "ghost": 0.5, "steel": 0.0, "fairy": 2.0},
    "ground": {"fire": 2.0, "electric": 2.0, "grass": 0.5, "poison": 2.0, "flying": 0.0, "bug": 0.5, "rock": 2.0, "steel": 2.0},
    "flying": {"electric": 0.5, "grass": 2.0, "fighting": 2.0, "bug": 2.0, "rock": 0.5, "steel": 0.5},
    "psychic": {"fighting": 2.0, "poison": 2.0, "psychic": 0.5, "steel": 0.5, "dark": 0.0},
    "bug": {"fire": 0.5, "grass": 2.0, "fighting": 0.5, "poison": 0.5, "flying": 0.5, "psychic": 2.0, "ghost": 0.5, "dark": 2.0, "steel": 0.5, "fairy": 0.5},
    "rock": {"fire": 2.0, "ice": 2.0, "flying": 2.0, "bug": 2.0, "fighting": 0.5, "ground": 0.5, "steel": 0.5},
    "ghost": {"normal": 0.0, "psychic": 2.0, "ghost": 2.0, "dark": 0.5},
    "dragon": {"dragon": 2.0, "steel": 0.5, "fairy": 0.0},
    "dark": {"fighting": 0.5, "psychic": 2.0, "ghost": 2.0, "dark": 0.5, "fairy": 0.5},
    "steel": {"fire": 0.5, "water": 0.5, "electric": 0.5, "ice": 2.0, "rock": 2.0, "fairy": 2.0, "steel": 0.5},
    "fairy": {"fire": 0.5, "poison": 0.5, "steel": 0.5, "fighting": 2.0, "dragon": 2.0, "dark": 2.0},
}


# Common set priors (knowledge acquisition): predicted coverage for selected species
COMMON_SETS: Dict[str, List[Dict[str, str]]] = {
    # Gen 9 Box Legends
    "koraidon": [
        {"name": "swordsdance", "type": "normal"},
        {"name": "lowkick", "type": "fighting"},
        {"name": "scaleshot", "type": "dragon"},
        {"name": "closecombat", "type": "fighting"},
        {"name": "dragonclaw", "type": "dragon"},
        {"name": "flamecharge", "type": "fire"},
        {"name": "wildcharge", "type": "electric"},
        {"name": "uturn", "type": "bug"}
    ],

    "miridon": [
        {"name": "electrodrift", "type": "electric"},
        {"name": "dracometeor", "type": "dragon"},
        {"name": "voltswitch", "type": "electric"},
        {"name": "overheat", "type": "fire"},
        {"name": "calmmind", "type": "psychic"},
        {"name": "paraboliccharge", "type": "electric"},
        {"name": "terablast", "type": "normal"},
        {"name": "dazzlinggleam", "type": "fairy"}
    ],

    # Zacian (still Uber)
    "zaciancrowned": [
        {"name": "behemothblade", "type": "steel"},
        {"name": "closecombat", "type": "fighting"},
        {"name": "playrough", "type": "fairy"},
        {"name": "wildcharge", "type": "electric"},
        {"name": "crunch", "type": "dark"},
        {"name": "swordsdance", "type": "normal"}
    ],

    # Major Paradox Pokemon
    "flutter_mane": [
        {"name": "shadowball", "type": "ghost"},
        {"name": "moonblast", "type": "fairy"},
        {"name": "calmmind", "type": "psychic"},
        {"name": "substitute", "type": "normal"},
        {"name": "taunt", "type": "dark"},
        {"name": "mysticalfire", "type": "fire"},
        {"name": "psyshock", "type": "psychic"}
    ],

    "chiyu": [
        {"name": "overheat", "type": "fire"},
        {"name": "darkpulse", "type": "dark"},
        {"name": "taunt", "type": "dark"},
        {"name": "nastyplot", "type": "dark"},
        {"name": "terablast", "type": "normal"},
        {"name": "flamethrower", "type": "fire"},
        {"name": "psychic", "type": "psychic"}
    ],

    "chienpao": [
        {"name": "icespinner", "type": "ice"},
        {"name": "suckerpunch", "type": "dark"},
        {"name": "swordsdance", "type": "normal"},
        {"name": "sacredsword", "type": "fighting"},
        {"name": "crunch", "type": "dark"},
        {"name": "iciclecrash", "type": "ice"}
    ],

    "ironbundle": [
        {"name": "hydropump", "type": "water"},
        {"name": "freezedry", "type": "ice"},
        {"name": "flipturn", "type": "water"},
        {"name": "icespinner", "type": "ice"},
        {"name": "taunt", "type": "dark"},
        {"name": "icebeam", "type": "ice"}
    ],

    "palafinhero": [
        {"name": "wavecrash", "type": "water"},
        {"name": "jetpunch", "type": "water"},
        {"name": "flipturn", "type": "water"},
        {"name": "taunt", "type": "dark"},
        {"name": "icepunch", "type": "ice"},
        {"name": "closecombat", "type": "fighting"}
    ],

    # New Gen 9 Threats
    "ogerponhearthflame": [
        {"name": "ivycudgel", "type": "fire"},
        {"name": "playrough", "type": "fairy"},
        {"name": "trailblaze", "type": "grass"},
        {"name": "swordsdance", "type": "normal"},
        {"name": "uturn", "type": "bug"},
        {"name": "hornleech", "type": "grass"}
    ],

    "kingambit": [
        {"name": "suckerpunch", "type": "dark"},
        {"name": "kowtowcleave", "type": "dark"},
        {"name": "ironhead", "type": "steel"},
        {"name": "lowkick", "type": "fighting"},
        {"name": "swordsdance", "type": "normal"},
        {"name": "zenheadbutt", "type": "psychic"}
    ],

    # Important Support/Defensive Pokemon
    "grimmsnarl": [
        {"name": "reflect", "type": "psychic"},
        {"name": "lightscreen", "type": "psychic"},
        {"name": "spiritbreak", "type": "fairy"},
        {"name": "taunt", "type": "dark"},
        {"name": "thunderwave", "type": "electric"},
        {"name": "partingshot", "type": "dark"}
    ],

    "toxapex": [
        {"name": "recover", "type": "normal"},
        {"name": "scald", "type": "water"},
        {"name": "toxic", "type": "poison"},
        {"name": "haze", "type": "ice"},
        {"name": "toxicspikes", "type": "poison"},
        {"name": "knockoff", "type": "dark"}
    ],

    "dondozo": [
        {"name": "liquidation", "type": "water"},
        {"name": "earthquake", "type": "ground"},
        {"name": "rest", "type": "psychic"},
        {"name": "sleeptalk", "type": "normal"},
        {"name": "curse", "type": "ghost"},
        {"name": "bodyslam", "type": "normal"}
    ],

    # Gen 9 OU Mons Viable in Ubers
    "greattusk": [
        {"name": "headlongrush", "type": "ground"},
        {"name": "closecombat", "type": "fighting"},
        {"name": "rapidspin", "type": "normal"},
        {"name": "knockoff", "type": "dark"},
        {"name": "icespinner", "type": "ice"},
        {"name": "earthquake", "type": "ground"}
    ],

    "tinglu": [
        {"name": "ruination", "type": "dark"},
        {"name": "earthquake", "type": "ground"},
        {"name": "stealthrock", "type": "rock"},
        {"name": "whirlwind", "type": "normal"},
        {"name": "spikes", "type": "ground"},
        {"name": "rest", "type": "psychic"}
    ],

    "hatterene": [
        {"name": "drainingkiss", "type": "fairy"},
        {"name": "psyshock", "type": "psychic"},
        {"name": "mysticalfire", "type": "fire"},
        {"name": "calmmind", "type": "psychic"},
        {"name": "psychic", "type": "psychic"},
        {"name": "trickroom", "type": "psychic"}
    ],

    "skeledirge": [
        {"name": "torchsong", "type": "fire"},
        {"name": "slackoff", "type": "normal"},
        {"name": "shadowball", "type": "ghost"},
        {"name": "willowisp", "type": "fire"},
        {"name": "earthpower", "type": "ground"},
        {"name": "terablast", "type": "normal"}
    ],

    "garganacl": [
        {"name": "saltcure", "type": "rock"},
        {"name": "recover", "type": "normal"},
        {"name": "irondefense", "type": "steel"},
        {"name": "bodypress", "type": "fighting"},
        {"name": "stealthrock", "type": "rock"},
        {"name": "earthquake", "type": "ground"}
    ],

    "glimmora": [
        {"name": "mortalspin", "type": "poison"},
        {"name": "stealthrock", "type": "rock"},
        {"name": "earthpower", "type": "ground"},
        {"name": "sludgewave", "type": "poison"},
        {"name": "spikes", "type": "ground"},
        {"name": "powergemm", "type": "rock"}
    ],

    "roaringmoon": [
        {"name": "dragonclaw", "type": "dragon"},
        {"name": "acrobatics", "type": "flying"},
        {"name": "uturn", "type": "bug"},
        {"name": "earthquake", "type": "ground"},
        {"name": "dragondance", "type": "dragon"},
        {"name": "crunch", "type": "dark"}
    ],

    # Arceus Forms (Major Ubers Staples)
    "arceusnormal": [
        {"name": "judgment", "type": "normal"},
        {"name": "swordsdance", "type": "normal"},
        {"name": "earthquake", "type": "ground"},
        {"name": "recover", "type": "normal"},
        {"name": "extremespeed", "type": "normal"},
        {"name": "shadowclaw", "type": "ghost"}
    ],

    "arceusghost": [
        {"name": "judgment", "type": "ghost"},
        {"name": "calmmind", "type": "psychic"},
        {"name": "recover", "type": "normal"},
        {"name": "focusblast", "type": "fighting"},
        {"name": "earthpower", "type": "ground"},
        {"name": "willowisp", "type": "fire"}
    ],

    "arceusdark": [
        {"name": "judgment", "type": "dark"},
        {"name": "calmmind", "type": "psychic"},
        {"name": "recover", "type": "normal"},
        {"name": "earthpower", "type": "ground"},
        {"name": "focusblast", "type": "fighting"},
        {"name": "taunt", "type": "dark"}
    ],

    "arceusgrass": [
        {"name": "judgment", "type": "grass"},
        {"name": "toxic", "type": "poison"},
        {"name": "recover", "type": "normal"},
        {"name": "earthpower", "type": "ground"},
        {"name": "calmmind", "type": "psychic"},
        {"name": "icebeam", "type": "ice"}
    ],

    "arceusground": [
        {"name": "judgment", "type": "ground"},
        {"name": "calmmind", "type": "psychic"},
        {"name": "recover", "type": "normal"},
        {"name": "earthpower", "type": "ground"},
        {"name": "icebeam", "type": "ice"},
        {"name": "stoneedge", "type": "rock"}
    ],

    "arceuswater": [
        {"name": "judgment", "type": "water"},
        {"name": "toxic", "type": "poison"},
        {"name": "recover", "type": "normal"},
        {"name": "calmmind", "type": "psychic"},
        {"name": "icebeam", "type": "ice"},
        {"name": "earthpower", "type": "ground"}
    ],

    "arceusfairy": [
        {"name": "judgment", "type": "fairy"},
        {"name": "calmmind", "type": "psychic"},
        {"name": "recover", "type": "normal"},
        {"name": "earthpower", "type": "ground"},
        {"name": "focusblast", "type": "fighting"},
        {"name": "toxic", "type": "poison"}
    ],

    # Legacy Ubers Still Meta
    "necrozmaduskmane": [
        {"name": "sunsteelstrike", "type": "steel"},
        {"name": "earthquake", "type": "ground"},
        {"name": "morningsun", "type": "normal"},
        {"name": "stealthrock", "type": "rock"},
        {"name": "dragonclaw", "type": "dragon"},
        {"name": "stoneedge", "type": "rock"}
    ],

    "eternatus": [
        {"name": "sludgebomb", "type": "poison"},
        {"name": "flamethrower", "type": "fire"},
        {"name": "recover", "type": "normal"},
        {"name": "toxicspikes", "type": "poison"},
        {"name": "dynamaxcannon", "type": "dragon"},
        {"name": "toxic", "type": "poison"}
    ],

    "calyrexshadow": [
        {"name": "astralbarrage", "type": "ghost"},
        {"name": "psyshock", "type": "psychic"},
        {"name": "nastyplot", "type": "dark"},
        {"name": "substitute", "type": "normal"},
        {"name": "drainingkiss", "type": "fairy"},
        {"name": "psychic", "type": "psychic"}
    ],

    "calyrexice": [
        {"name": "glaciallance", "type": "ice"},
        {"name": "highhorsepower", "type": "ground"},
        {"name": "trickroom", "type": "psychic"},
        {"name": "swordsdance", "type": "normal"},
        {"name": "closecombat", "type": "fighting"},
        {"name": "zenheadbutt", "type": "psychic"}
    ],

    "hooh": [
        {"name": "sacredfire", "type": "fire"},
        {"name": "bravebird", "type": "flying"},
        {"name": "recover", "type": "normal"},
        {"name": "defog", "type": "flying"},
        {"name": "earthquake", "type": "ground"},
        {"name": "toxic", "type": "poison"}
    ],

    "lugia": [
        {"name": "toxic", "type": "poison"},
        {"name": "whirlwind", "type": "normal"},
        {"name": "recover", "type": "normal"},
        {"name": "icebeam", "type": "ice"},
        {"name": "aeroblast", "type": "flying"},
        {"name": "psychic", "type": "psychic"}
    ],

    "giratina": [
        {"name": "dragontail", "type": "dragon"},
        {"name": "toxic", "type": "poison"},
        {"name": "defog", "type": "flying"},
        {"name": "rest", "type": "psychic"},
        {"name": "willowisp", "type": "fire"},
        {"name": "shadowball", "type": "ghost"}
    ],

    "giratinaorigin": [
        {"name": "dracometeor", "type": "dragon"},
        {"name": "shadowball", "type": "ghost"},
        {"name": "aurasphere", "type": "fighting"},
        {"name": "defog", "type": "flying"},
        {"name": "hex", "type": "ghost"},
        {"name": "willowisp", "type": "fire"}
    ],

    "dialgaorigin": [
        {"name": "dracometeor", "type": "dragon"},
        {"name": "flashcannon", "type": "steel"},
        {"name": "stealthrock", "type": "rock"},
        {"name": "fireblast", "type": "fire"},
        {"name": "earthpower", "type": "ground"},
        {"name": "toxic", "type": "poison"}
    ],

    "rayquaza": [
        {"name": "dragondance", "type": "dragon"},
        {"name": "earthquake", "type": "ground"},
        {"name": "outrage", "type": "dragon"},
        {"name": "extremespeed", "type": "normal"},
        {"name": "vcreate", "type": "fire"},
        {"name": "dragonclaw", "type": "dragon"}
    ],

    "darkrai": [
        {"name": "darkpulse", "type": "dark"},
        {"name": "nastyplot", "type": "dark"},
        {"name": "sludgebomb", "type": "poison"},
        {"name": "focusblast", "type": "fighting"},
        {"name": "hypnosis", "type": "psychic"},
        {"name": "substitute", "type": "normal"}
    ],

    "groudon": [
        {"name": "precipiceblades", "type": "ground"},
        {"name": "stealthrock", "type": "rock"},
        {"name": "stoneedge", "type": "rock"},
        {"name": "dragontail", "type": "dragon"},
        {"name": "heatcrash", "type": "fire"},
        {"name": "toxic", "type": "poison"}
    ],

    "kyogre": [
        {"name": "waterspout", "type": "water"},
        {"name": "thunder", "type": "electric"},
        {"name": "icebeam", "type": "ice"},
        {"name": "originpulse", "type": "water"},
        {"name": "calmmind", "type": "psychic"},
        {"name": "surf", "type": "water"}
    ]
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
    # Ensure atk_type and def_types are lowercase for lookup
    atk_type = atk_type.lower() if atk_type else atk_type
    def_types = [dt.lower() for dt in def_types]
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


def has_stab(move_type: str, attacker: Pokemon) -> bool:
    if not move_type:
        return False
    return move_type in attacker.types


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
    return estimate_speed(p1) > estimate_speed(p2)


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
        self.plausible:Dict[str, List[Dict[str, str]]] = {}

    def update_with_battle(self, battle: AbstractBattle):

        opp = battle.opponent_active_pokemon
        if not opp:
            return
        # Add the opponent to the model if not already present
        if opp.species not in self.revealed:
            self.revealed[opp.species] = set()
            # Fill plausible with a list of moves (dicts with name/type) from COMMON_SETS if available
            if opp.species not in self.plausible:
                common_moves = COMMON_SETS.get(opp.species, [])
                self.plausible[opp.species] = [dict(m) for m in common_moves]

        # Add revealed moves if present
        for m in opp.moves.values():
            if m and m.id:
                self.revealed[opp.species].add(m.id)
                # Keep plausible set in sync
                if any(m.id == move_dict['name'] for move_dict in self.plausible[opp.species]):
                    self.plausible[opp.species] = [move_dict for move_dict in self.plausible[opp.species] if move_dict['name'] != m.id]


    def likely_strong_moves(self, attacker: Pokemon, defender: Pokemon) -> List[str]:
        moves = self.plausible.get(attacker.species, [])
        # Each plausible move is a dict with "name" and "type"
        # For each, predict effectiveness vs defender
        move_effects = []
        for move in moves:
            move_name = move.get("name", "")
            move_type = move.get("type", "")
            eff = predict_effectiveness(move_type, pokemon_types(defender)) if move_type else 1.
            if has_stab(move, attacker):
                eff *= 1.5  # Apply STAB boost
            move_effects.append({"name": move_name, "type": move_type, "effectiveness": eff})
        # Optionally, sort by effectiveness descending
        move_effects.sort(key=lambda x: x["effectiveness"], reverse=True)
        # Return as list of (effectiveness, move_name)
        ranked = [(m["effectiveness"], m["name"]) for m in move_effects]
        print(len(moves), "plausible moves for", attacker.species, "vs", defender.species, "->", ranked)
        return ranked


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
        # Count number of non-fainted Pokémon in our team
        alive_count = sum(1 for p in battle.team.values() if not p.fainted)
        opponent_alive_count = sum(1 for p in battle.opponent_team.values() if not p.fainted)
        self.log(battle, f"Non-fainted Pokémon in team: {alive_count} and opponent team: {opponent_alive_count}")

        self.log(battle, f"Active: {battle.active_pokemon.species if battle.active_pokemon else 'None'} \
             ({battle.active_pokemon.current_hp_fraction:.2%} HP) vs \
                {battle.opponent_active_pokemon.species if battle.opponent_active_pokemon else 'None'} \
                ({battle.opponent_active_pokemon.current_hp_fraction:.2%} HP) with available moves \
                    {', '.join([m.id for m in battle.available_moves]) if battle.available_moves else 'None'}")
        self.opp_model.update_with_battle(battle)
        me = battle.active_pokemon
        opp = battle.opponent_active_pokemon

        # If we must force a random choice (e.g., struggle), fallback
        if battle.force_switch or (me.current_hp < 20 or me.current_hp_fraction < 0.2 ): #switch out at low hp
            self.log(battle, f"Forced switch required or LOW HP. Current pokemon: {battle.active_pokemon.species if battle.active_pokemon \
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
        print(f"Opponent dangerous: {opp_dangerous}, faster: {opp_faster}, KO: {opp_is_ko}, attack exists: {opp_attack_move_exists}")
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
                    self.log(battle, f"Only neutral or status moves. Switching to {best_switch.species}. Switch score: {switch_score}, Opponent HP: {opp.current_hp}")
                    return self.create_order(best_switch)
                else:
                    self.log(battle, f"Choosing to move over switch: {best_switch.species} | Move chosen: {best_move.id}")
                    return self.create_order(best_move)
            else:
                self.log(battle, f"No valid switch available, choosing move: {best_move.id}")
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
        move_type = move.type.name if hasattr(move.type, "name") else str(move.type) 
        stab = 1.5 if has_stab(move_type, attacker) else 1.0

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
        komove = None
        bestmove = None
        # If any move can KO, pick the highest scoring KO move
        if exists := [m for m in move_ranks if m["can_KO"]]:
            self.log(battle, f"Found {len(exists)} moves that can KO the opponent.")
            exists.sort(key=lambda x: x["damage"], reverse=True)
            komove = exists[0]["move"]
            return komove, True, True
        # Sort moves by damage descending
        move_ranks.sort(key=lambda x: x["damage"], reverse=True)
        attack_move_exists = True
        if not move_ranks[0]["is_super_effective"]:  # No super effective move
            attack_move_exists = False
            #self.log(battle, "No effective attacking move found, choosing next best")
        #TODO: choose healing move or neutral move?
        bestmove = move_ranks[0]["move"]
        return bestmove, False, attack_move_exists

    def choose_best_switch(self, battle: AbstractBattle) -> Tuple[Optional[Pokemon], float, str]:
        me = battle.active_pokemon
        opp = battle.opponent_active_pokemon
        if not opp or not battle.available_switches:
            return None, -1.0, "No switches"
        
        if opp.moves is None or len(opp.moves) < 4:
            self.log(battle, f"All moves for {opp.species} not yet known; guess likely moves and STABs")
            
        # Evaluate switches by how well they resist likely moves and threaten back
        candidates = []
        likely = self.opp_model.likely_strong_moves(opp, me)  # may be empty 
        for sw in battle.available_switches:
            resist_score = 0.0
            if opp.moves is None or len(opp.moves) < 4:
                if likely:
                    for ef, _ in likely:
                        resist_score += {0.5: 8.0, 0.0: 12.0, 2.0: -10.0, 1.0: 0.0}.get(ef, 0.0)
            if opp.moves:
                #print(f"Opponent {opp.species} moves: {opp.moves}")
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
            hp_factor = sw.current_hp_fraction * 100.0
            self.log(battle, f"Switch candidate {sw.species}: resist_score {resist_score:.1f}, threat {threat:.1f}, hp_factor {hp_factor:.1f}")
            score = resist_score + threat + hp_factor #TOO simplisitic?
            candidates.append((sw, threat, threatmult, hp_factor, resist_score))

        if not candidates:
            return None, -1.0, "No candidates"
        # Sort by: highest resist_score, then highest threat, then highest current_hp_fraction
        candidates_sorted = sorted(
            candidates,
            key=lambda x: (x[3], x[4], x[1]),  # x[4]=resist_score, x[1]=threat, x[3]=current_hp_fraction
            reverse=True
        )
        #candidates.sort(reverse=True, key=lambda x: x[0])
        best_sw = candidates_sorted[0][0]
        #best_score = candidates_sorted[0][2] + candidates_sorted[0][3] + candidates_sorted[0][4]
        high_threat = candidates_sorted[0][1] 

        reason = f"Resists predicted STABs and can threaten back (score {high_threat:.1f})."
        return best_sw, high_threat, reason



    def _choose_best_switch(self, battle: AbstractBattle) -> Optional[Pokemon]:
        sw, _, _ = self.choose_best_switch(battle)
        return sw

    #unused functions here

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
        already_stab = has_stab(atk_type, me)
        if already_stab:
            return False
        # Assume tera type equals move type if possible (Showdown requires choosing team tera; poke_env tracks available)
        # Without exact tera info here, return False to avoid misuse.
        return False
    

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
        if me.species == "Ting-Lu" and me.current_hp_fraction > 0.6:
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
        likely = self.opp_model.likely_strong_moves(opp, target)
        # If any likely move is super-effective, consider threatened
        for mv in likely[:2]:
            # quick type guess already done in model via effectiveness
            # If we have no likely list yet, be conservative iff target < 60%
            pass
        # Conservative fallback: if we're below 60% vs a known breaker, consider threatened
        if opp.species in {"Koraidon", "Miraidon", "Zacian-Crowned", "Flutter Mane"} and target.current_hp_fraction < 0.6:
            return True
        return False

    