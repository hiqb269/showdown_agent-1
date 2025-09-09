# run_battle.py
"""
Runs a Pokemon battle between two agents provided as file arguments.

This script dynamically loads a 'CustomAgent' class from two Python files,
instantiates them, and runs a series of battles to determine the winner.

Usage:
    python run_battle.py <path_to_agent1.py> <path_to_agent2.py>
"""
import asyncio
import sys
import os
import importlib.util
from typing import Dict, List, Tuple

import poke_env as pke
from poke_env import AccountConfiguration
from poke_env.player.player import Player


def rank_players_by_victories(results_dict: Dict[str, Dict[str, float]]) -> List[Tuple[str, float]]:
    """
    Ranks players based on their victory rate from cross-evaluation results.
   
    """
    victory_scores = {}
    for player, opponents in results_dict.items():
        victories = [
            1 if (score is not None and score > 0.5) else 0
            for opp, score in opponents.items()
            if opp != player
        ]
        victory_scores[player] = sum(victories) / len(victories) if victories else 0.0

    return sorted(victory_scores.items(), key=lambda x: x[1], reverse=True)



async def run_battle_between(p1: Player, p2: Player) -> str:
    """
    Conducts a battle between two Player agents and returns the winner's username.
   
    """
    players = [p1, p2]
    # The cross_evaluate function runs multiple challenges between the players.
    cross_evaluation_results = await pke.cross_evaluate(players, n_challenges=3)

    # Rank players to find the one with the highest win rate.
    top_players = rank_players_by_victories(cross_evaluation_results)

    # The first player in the sorted list is the winner.
    winner_name = top_players[0][0]
    return winner_name



def load_agent_from_file(filepath: str) -> Player:
    """
    Dynamically loads a CustomAgent class from a Python file and instantiates it.
   
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Agent file not found at: {filepath}")

    module_name = os.path.basename(filepath).replace(".py", "")
    
    # Dynamically import the module from the specified file path.
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec for module {module_name} from {filepath}.")
    
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    if hasattr(module, "CustomAgent"):
        agent_class = getattr(module, "CustomAgent")
        
        # Create a unique account configuration for the agent.
        account_config = AccountConfiguration(module_name, None)
        return agent_class(
            account_configuration=account_config,
            battle_format="gen9ubers",
        )
    else:
        raise AttributeError(f"The file {filepath} must contain a 'CustomAgent' class.")


async def main():
    """
    Main function to parse arguments, load agents, and run the battle.
    """
    if len(sys.argv) != 3:
        print("Usage: python run_battle.py <path_to_agent1.py> <path_to_agent2.py>")
        sys.exit(1)

    agent1_path = sys.argv[1]
    agent2_path = sys.argv[2]

    try:
        print(f"Loading agent 1 from: {agent1_path}")
        agent1 = load_agent_from_file(agent1_path)
        
        print(f"Loading agent 2 from: {agent2_path}")
        agent2 = load_agent_from_file(agent2_path)
        
        print("\nStarting battle...")
        print(f"  - Player 1: {agent1.username}")
        print(f"  - Player 2: {agent2.username}")
        
        winner = await run_battle_between(agent1, agent2)
        
        print("\n--- Battle Complete ---")
        print(f"Winner: {winner}")

    except (FileNotFoundError, ImportError, AttributeError) as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())