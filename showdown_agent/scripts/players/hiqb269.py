
from typing import Dict, List, Optional, Tuple

from poke_env.battle import AbstractBattle,Weather, MoveCategory
from poke_env.battle.pokemon import Pokemon
from poke_env.battle.move import Move
from poke_env.battle.pokemon_type import PokemonType
from poke_env.player import Player
import datetime
import os

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
    "fluttermane": [
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
        {"name": "powergem", "type": "rock"}
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


def has_stab(move_type: str, attacker: Pokemon) -> bool:
    if not move_type:
        return False
    return any(t and t.name.lower() == move_type.lower() for t in attacker.types)


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
            pass
    return int(estimated_speed)


def is_first_one_faster(p1: Pokemon, p2: Pokemon) -> bool:
    return estimate_speed(p1) > estimate_speed(p2)

def pokemon_types(p: Pokemon) -> List[str]:
    return [t.name for t in p.types if t is not None]

def is_status_move(m: Move) -> bool:
    return m.category == MoveCategory.STATUS

def is_hazard_move(m: Move) -> bool:
    name = m.id
    return name in {"stealthrock", "spikes", "toxicspikes", "stickyweb"}

def is_healing_move(m: Move) -> bool:
    name = m.id
    return name in {"recover", "roost", "slackoff", "softboiled", "moonlight", "morningsun", "synthesis", "rest"}

def can_heal(p: Pokemon) -> Optional[Move]:
    if not p or p.fainted:
        return None
    for m in p.moves.values():
        if m and is_healing_move(m):
            return m
    return None


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
                self.revealed[opp.species].add(m)
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
            if has_stab(move_type, attacker):
                eff *= 1.5  # Apply STAB boost
            move_effects.append({"name": move_name, "type": move_type, "effectiveness": eff})
        move_effects.sort(key=lambda x: x["effectiveness"], reverse=True)
        # Return as list of (effectiveness, move_name)
        ranked = [(m["effectiveness"], m["name"]) for m in move_effects]
        #print(len(moves), "plausible moves for", attacker.species, "vs", defender.species, "->", ranked)
        return ranked


class CustomAgent(Player):
    def __init__(self, *args, **kwargs):
        super().__init__(team=team, *args, **kwargs)
        self.opp_model = OpponentModel()
        self.debug = False  # Enable detailed logging
        self.alive_count = 6  # Track non-fainted pokemon count

    # ---- Logging utility ----
    def log(self, battle: AbstractBattle, msg: str):
        if self.debug:
            #print(f"[Turn {battle.turn}] {msg}")
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            log_dir = "hiqb269v4logs"
            os.makedirs(log_dir, exist_ok=True)
            if not hasattr(self, "_log_filename"):
                self._log_filename = f"{log_dir}/battle_loghiqb269_v4_{timestamp}.txt"
            filename = self._log_filename
            with open(filename, "a") as f:
                f.write(f"[Turn {battle.turn}] {msg}\n")


    def choose_move(self, battle: AbstractBattle):
        self.alive_count = sum(1 for p in battle.team.values() if not p.fainted)
        self.log(battle, f"Non-fainted Pokémon in team: {self.alive_count}")

        self.log(battle, f"Active: {battle.active_pokemon.species if battle.active_pokemon else 'None'} \
             ({battle.active_pokemon.current_hp_fraction:.2%} HP) vs \
                {battle.opponent_active_pokemon.species if battle.opponent_active_pokemon else 'None'} \
                ({battle.opponent_active_pokemon.current_hp_fraction:.2%} HP) with available moves \
                    {', '.join([m.id for m in battle.available_moves]) if battle.available_moves else 'None'}")
        
        self.opp_model.update_with_battle(battle)
        me = battle.active_pokemon
        opp = battle.opponent_active_pokemon

        if me is None or opp is None:
            self.log(battle, "No active Pokémon on either side, choosing random move.")
            return self.choose_random_move(battle)

        ranked_switches = []
        best_switch = None
        switch_damage = 0.0


        # Path 1: If battle in a force switch
        if battle.force_switch:
            self.log(battle, f"Forced switch required")
            ranked_switches = self.bring_ranked_switches(battle)
            best_switch = ranked_switches[0][0] if ranked_switches else None
            if best_switch:
                self.log(battle, f"Forced switch -> {best_switch.species}")
                return self.create_order(best_switch)
            else:
                self.log(battle, "No valid switch available for forced switch, choosing healthiest pokemon or Random move.")
                healthiest_switch = self.choose_healthiest_switch(battle)
                return self.create_order(healthiest_switch) if healthiest_switch else self.choose_random_move(battle)

        # Check if opponent is an immediate threat
        opp_faster, opp_dangerous, opp_is_ko, opp_may_ko = self.is_opp_immediate_threat(battle)

        opp_threat = opp_faster and (opp_may_ko or opp_dangerous)
        major_threat = self._is_major_threat(battle) #has boosts
        self.log(battle, f"Opponent dangerous: {opp_dangerous}, has boosts: {major_threat}, faster: {opp_faster}, KO: {opp_is_ko}, opponent may have a ko move: {opp_may_ko}")

        ranked_moves = self.bring_ranked_moves(battle, True)
        best_move_info = ranked_moves[0] if ranked_moves else None
        best_move = best_move_info["move"] if best_move_info else None

        can_ko = best_move_info["can_KO"] if best_move_info else False
        attack_move_exists = best_move_info["is_super_effective"] if best_move_info else False

        # PRIORITY 1: SECURE A KO ON A MAJOR THREAT
        if best_move and can_ko and (major_threat or opp_is_ko or opp.current_hp_fraction <= 0.5):
            self.log(battle, f"Priority 1: Securing KO on boosted threat {battle.opponent_active_pokemon.species} with {best_move.id}.")
            return self.create_order(best_move)
        
        # PRIORITY 2: SET UP HAZARDS
        if not opp_is_ko and not opp_threat and self._should_set_rocks(battle):
            hazard_move = next((m for m in battle.available_moves if is_hazard_move(m)), None)
            if hazard_move:
                self.log(battle, f"Priority 2: Setting up Stealth Rock for move 'stealthrock'")
                return self.create_order(hazard_move)

        # PRIORITY 3: HEAL IF IT'S THE BEST LONG-TERM PLAY
        if not (opp_faster and (opp_is_ko or opp_may_ko or opp_dangerous) ):  
            heal_move = can_heal(me)
            if heal_move and self._should_heal(opp_is_ko, battle): #TODO check with speed for ko and attack move
                self.log(battle, f"Priority 3: Healing {me.species} with {heal_move.id}.")
                return self.create_order(heal_move)

        # PRIORITY 4: TAKE ANY OTHER GUARANTEED KO
        if best_move and (can_ko or attack_move_exists):
            recoildamage = best_move_info.get("recoilDamage", 0) if best_move_info else 0
            if recoildamage and self.could_faint(recoildamage, me.current_hp, False):
                 self.log(battle, f"Skipping KO with {best_move.id} due to self-KO recoil risk.")
            else:
                self.log(battle, f"Priority 4: Securing standard KO on {battle.opponent_active_pokemon.species} with {best_move.id}.")
                return self.create_order(best_move)
            
        # PRIORITY 5: SET UP TO SWEEP
        if not opp_is_ko:
            setup_move = next((m for m in battle.available_moves if m.id == 'calmmind'), None)
            if setup_move and self._should_setup(battle):
                self.log(battle, "Priority 5: Setting up with Calm Mind.")
                return self.create_order(setup_move)
         
        
        ranked_switches = self.bring_ranked_switches(battle)
        best_switch = ranked_switches[0][0] if ranked_switches else None
        switch_damage = ranked_switches[0][1] if ranked_switches else 0.0

        # PRIORITY 6: PIVOT FOR MOMENTUM
        pivot_move = next((m for m in battle.available_moves if m.id == 'uturn'), None)
        if pivot_move and self._should_pivot(battle, best_switch, switch_damage):
            self.log(battle, "Priority 6: Pivoting with U-turn for momentum.")
            return self.create_order(pivot_move)

        # PRIORITY 7: MAKE A DEFENSIVE SWITCH
        if (opp_is_ko or (opp_faster and opp_dangerous)) and best_switch:
            self.log(battle, f"Priority 7: Opponent threatens a KO; seeking a defensive switch.")
            return self.create_order(best_switch)

        # PRIORITY 8: DEFAULT TO BEST AVAILABLE MOVE
        if best_move:
            self.log(battle, f"Priority 8: No other conditions met; using best available move {best_move.id}.")
            return self.create_order(best_move)

        # FALLBACK
        self.log(battle, "Fallback: No optimal move found, choosing random move.")
        return self.choose_random_move(battle)
    

    def choose_healthiest_switch(self, battle: AbstractBattle) -> Optional[Pokemon]:
        healthiest = None
        max_hp_frac = -1.0
        for p in battle.available_switches:
            if p and not p.fainted:
                hp_frac = p.current_hp_fraction if hasattr(p, 'current_hp_fraction') else (p.current_hp / p.max_hp if p.max_hp > 0 else 0)
                if hp_frac > max_hp_frac:
                    healthiest = p
                    max_hp_frac = hp_frac
        return healthiest

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
        off_key = "atk" if move.category == MoveCategory.PHYSICAL else "spa"
        def_key = "def" if move.category == MoveCategory.PHYSICAL else "spd"

        off_boost = (attacker.boosts.get(off_key, 0) if attacker.boosts else 0)
        def_boost = (defender.boosts.get(def_key, 0) if defender.boosts else 0)

        # Translate stat stages to multipliers (2+n)/2 for positive, 2/(2-n) for negative
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

        recoildamage = 0.0
        if getattr(move, "recoil", 0):
            recoil = move.recoil
            recoildamage = float(score * recoil)

        return multiplier, score, recoildamage
    
    def bring_ranked_moves(self, battle: AbstractBattle, for_me: bool) -> Optional[List[Dict]]:
        move_ranks = self._assign_move_ranks(battle, for_me)
        return self.sort_ranked_moves(move_ranks)


    def sort_ranked_moves(self, move_ranks: List[Dict]) -> Optional[List[Dict]]:
        if not move_ranks or len(move_ranks) == 0:
            return None
        move_ranks.sort(key=lambda x: x["damage"], reverse=True)
        move_ranks_sorted = sorted(
            move_ranks,
            key=lambda x: (
            not x["can_KO"],   # KO moves (can_KO=True) first
            -x["damage"],      # Higher damage first
            x["recoildamage"]  # Lower recoil damage first
            )
        )
        return move_ranks_sorted

    def _assign_move_ranks(self, battle: AbstractBattle, for_me: bool) -> Optional[List[Dict]]:
        attacker, defender, moves, likely = None, None, None, None
        
        if for_me == True:
            attacker = battle.active_pokemon
            defender = battle.opponent_active_pokemon
            moves = battle.available_moves
        elif for_me == False:
            attacker = battle.opponent_active_pokemon
            defender = battle.active_pokemon
            moves = battle.opponent_active_pokemon.moves.values()
            if not moves or len(moves) < 4:
                likely = self.opp_model.likely_strong_moves(attacker, defender)

        if not attacker or not defender or not moves:
            return None
        
        self.log(battle, f"Assigning move ranks for {'us' if for_me else 'opponent'}")
        damage = 0.0
        recoildamage = 0.0
        move_ids = []
            # Collect move IDs from actual moves and likely moves
        if self.debug:
            if moves:
                move_ids = [m.id for m in moves if hasattr(m, "id")]
            if likely: 
                move_ids += [mv for ef, mv in likely if mv not in move_ids]
        #TEST
        self.log(battle, f"Evaluating moves {', '.join(move_ids)} for {attacker.species} vs {defender.species}")
         # Rank moves by estimated damage and other factors
        move_ranks = []
        for move in moves:
            if move.base_power > 0:
                eff = defender.damage_multiplier(move)
                _, damage, recoildamage= self.estimate_damage(move, attacker, defender, battle.weather)
                move_info = {
                    "move": move,
                    "effectiveness": eff,
                    "damage": damage, 
                    "recoildamage": recoildamage,
                    "can_KO": self.is_possible_KO(eff,damage, defender, for_me),
                    "can_recoil_KO": self.is_possible_KO(1.5, recoildamage, attacker, not for_me),
                    "is_super_effective": eff > 1.0,
                    "is_resisted": eff < 1.0,
                    "is_neutral": eff == 1.0,
                    "is_status": is_status_move(move),
                    "may_KO": False, 
                }
                move_ranks.append(move_info)

        if likely:
                    for ef, mv in likely:
                        if mv not in move_ids:
                            move_info = {
                                "move": Move(move_id=mv, gen=9,),
                                "effectiveness": ef,
                                "damage": -1.00,  # unknown
                                "recoildamage": -1.00,
                                "can_KO": False,
                                "can_recoil_KO": False,
                                "is_super_effective": ef > 1.0,
                                "is_resisted": ef < 1.0,
                                "is_neutral": ef == 1.0,
                                "may_KO": self.is_possible_KO(ef, -1.00, defender, for_me),
                            }
                            move_ranks.append(move_info)
        
        if(for_me):
            self.log(battle, f"Move ranks for {attacker.species} vs {defender.species}: {move_ranks}")
        return move_ranks
    
    
    def bring_ranked_switches(self, battle: AbstractBattle) -> Optional[List[Dict]]:
        me = battle.active_pokemon
        opp = battle.opponent_active_pokemon
        if not opp or not battle.available_switches:
            return None
              
        # Evaluate switches by how well they resist likely moves and threaten back
        candidates = []
        for sw in battle.available_switches:
            opp_can_KO = False
            opp_may_KO = False
            resist_score = 0.0
            
            if opp.moves is None or len(opp.moves) < 4:
                self.log(battle, f"All moves for {opp.species} not yet known; guess likely moves")   
                likely = self.opp_model.likely_strong_moves(opp, sw)
                if likely:
                    for ef, _ in likely: #TODO: check for survival (ef > 2)
                        resist_score += {0.5: 8.0, 0.0: 12.0, 2.0: -10.0, 1.0: 0.0}.get(ef, 0.0)
                    super_effective_count = sum(1 for ef_val, _ in likely if ef_val >= 2)
                    opp_may_KO = super_effective_count > 0 
            if opp.moves:
                self.log(battle, f"Evaluating known {len(opp.moves)} moves for {opp.species}")
                for mv in opp.moves.values():
                    if not mv:
                        continue
                    eff, predicted_damage, _ = self.estimate_damage(mv, opp, sw,battle.weather)
                    if self.could_faint(predicted_damage, sw.current_hp, False) and eff > 1.0:
                        opp_can_KO = True
                        break
                    if eff <= 0.0:
                        bucket = 0.0  # immune
                    elif eff < 0.75:
                        bucket = 0.5  # resist
                    elif eff < 1.5:
                        bucket = 1.0  # neutral
                    else:
                        bucket = 2.0  # super-effective

                    resist_score += {0.5: 8.0, 0.0: 12.0, 2.0: -10.0, 1.0: 0.0}.get(bucket, 0.0)
            # Offensive threat after switch: check our best immediate move
            threat = 0.0
            if sw.moves:
                # Synthesize a rough "best move" vs opp
                for m in sw.moves.values():
                    if not m:
                        continue
                    if not is_status_move(m):
                        #threat = max(threat, effectiveness(m, opp) * (1.5 if has_stab(m, sw) else 1.0))
                        threat = max(threat, self.estimate_damage(m,sw, opp, battle.weather)[1])
            # Health consideration
            hp_factor = sw.current_hp_fraction * 100.0
            is_healthy = sw.current_hp > 0.5 * sw.max_hp
            self.log(battle, f"Switch candidate {sw.species}: resist_score {resist_score:.1f}, threat {threat:.1f}, hp_factor {hp_factor:.1f}")
            #score = resist_score + threat + hp_factor #TOO simplisitic?
            candidates.append((sw, threat, hp_factor, resist_score, opp_may_KO, opp_can_KO))

        if not candidates:
            return None
        # Sort candidates by threat level from opponent:
        # 1. Candidates where opp_may_KO and opp_can_KO are both True (worst) -- bottom
        # 2. Candidates where only opp_can_KO is True -- just above
        # 3. Candidates where only opp_may_KO is True -- above that
        # 4. Candidates where neither is True -- best, at the top
        def candidate_sort_key(x):
            sw, threat, hp_factor, resist_score, opp_may_KO, opp_can_KO = x
            # Lower is better for opp_can_KO/opp_may_KO, so True = 1, False = 0
            # Both True = 2, only can_KO = 1, only may_KO = 1, neither = 0
            # But we want both True (worst) at bottom, so use tuple:
            # (both_true, can_KO, may_KO, -hp, -threat)
            both_true = int(opp_may_KO and opp_can_KO)
            return (
                both_true,
                int(opp_can_KO),
                int(opp_may_KO),
                -hp_factor,
                -threat,
                -resist_score
            )

        candidates_sorted = sorted(
            candidates,
            key=candidate_sort_key
        )
        
        self.log(battle, "Sorted switch candidates:")
        for sw, threat, hp_factor, resist_score, opp_may_KO, opp_can_KO in candidates_sorted:
            self.log(battle, f"  {sw.species}: threat {threat:.1f}, hp_factor {hp_factor:.1f}, resist_score {resist_score:.1f}, opp_may_KO {opp_may_KO}, opp_can_KO {opp_can_KO}")
        return candidates_sorted


    def is_possible_KO(self, eff: float, damage: float, target: Pokemon, for_me: bool = True) -> bool:
        if not target or target.current_hp is None:
            return False
        return self.could_faint(damage, target.current_hp, for_me)


    def could_faint(self, damage: float, hp: float, for_me: bool) -> bool:
        if hp is None or damage is None:
            return False
        if for_me:   # our move vs opponent
            return damage >= hp * 1.15   # conservative (avoid overestimating KO chance)
        if not for_me:  # opponent’s move vs us
            return damage >= hp * 0.85   # cautious (assume near-KO can still kill)
        return False
        
    
    def _is_major_threat(self, battle: AbstractBattle) -> bool:
        """Checks if the opponent is a high-priority threat that must be dealt with."""
        opp = battle.opponent_active_pokemon
        if not opp:
            return False
        # A major threat is one that has boosted its stats and is poised to sweep.
        has_boosts = (
            opp.boosts.get('atk', 0) >= 1 or
            opp.boosts.get('spa', 0) >= 1 or
            opp.boosts.get('spe', 0) >= 1
        )
        return has_boosts
    

    def get_opponent_best_move(self, battle: AbstractBattle) -> Tuple[Optional[Move], bool, bool]:
        opponentMoves = self.bring_ranked_moves(battle, False)
        damage = opponentMoves[0]["damage"] if opponentMoves else None
        can_ko = opponentMoves[0]["can_KO"] if opponentMoves else False
        attack_move_exists = opponentMoves[0]["may_KO"] if opponentMoves else False
        return damage, can_ko, attack_move_exists

    def is_opp_immediate_threat(self, battle: AbstractBattle) -> Tuple[bool, bool, bool,bool]:
        opp = battle.opponent_active_pokemon
        me = battle.active_pokemon
        if not opp or not me:
            return False, False, False, False
        # If opponent is faster and has a likely strong move, consider it a threat
        opp_faster = is_first_one_faster(opp, me)
        opp_expected_damage, opp_is_ko, opp_may_ko = self.get_opponent_best_move(battle)
        opp_dangerous = opp_expected_damage is not None and self.could_faint(opp_expected_damage, me.current_hp, False)
        return  opp_faster, opp_dangerous, opp_is_ko, opp_may_ko

    def _should_heal(self, opp_can_ko: bool, battle: AbstractBattle) -> bool:
        me = battle.active_pokemon

        # Don't heal if at high health.
        if me.current_hp_fraction > 0.8:
            return False

        # Heal if you are a key defensive Pokémon and can safely take a hit.
        is_key_pokemon = me.species in ["hooh", "necrozmaduskmane", "arceusground"]
        if is_key_pokemon and me.current_hp_fraction < 0.65 and not opp_can_ko:
            self.log(battle, f"Analysis: {me.species} is a key mon; preserving it with healing.")
            return True

        #Heal if you are low on health but not in immediate KO danger.
        if me.current_hp_fraction < 0.5 and not opp_can_ko:
            self.log(battle, "Analysis: Can safely take a hit; healing is optimal.")
            return True    
        return False

    def _should_setup(self, battle: AbstractBattle) -> bool:
        me = battle.active_pokemon
        # Only our designated setup sweeper should use this.
        if me.species != "arceusground":
            return False
        
        if self.alive_count < 3:
            return False    
        #  Don't set up if already significantly boosted.
        if me.boosts.get('spa', 0) >= 2:
            return False
        #  Don't set up if health is too low to be safe.
        if me.current_hp_fraction < 0.6: #Initially set to 0.6 - might have to adjust
            return False

        self.log(battle, "Opponent is not an immediate threat; good time to set up.")
        return True

    def _should_pivot(self, battle: AbstractBattle, best_switch: Pokemon, switch_damage: float) -> bool:
        me = battle.active_pokemon
        opp = battle.opponent_active_pokemon
        if not me or not opp or not best_switch:
            return False
        # For a specific pokemon only.
        if me.species != "koraidon":
            return False
        # If a very safe and threatening switch exists (high score), pivoting is a great play.
        # The 'switch_score' here is the estimated damage the switch-in can do.
        if self.could_faint(switch_damage, opp.current_hp, True)  and switch_damage > ( opp.current_hp / 2): #why= half? just a guess 
             self.log(battle, f"Good pivot opportunity to {best_switch.species}.")
             return True
        
        return False
    
    def _should_set_rocks(self, battle: AbstractBattle) -> bool:
        me = battle.active_pokemon
    
        if me.species != "necrozmaduskmane":
            return False
        
        # Don't set hazards if they're already up.
        if "stealthrock" in battle.opponent_side_conditions:
            return False    

        if battle.turn > 15:
            return False
        
        if me.current_hp_fraction < 0.6: #Initially set to 0.6 - might have to adjust
            return False

        self.log(battle, "Conditions are favorable for setting Stealth Rock.")
        return True

    


    