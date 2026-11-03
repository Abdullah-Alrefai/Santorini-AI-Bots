"""Random Santorini bot: picks one legal action uniformly at random."""

import random
import sys
from pathlib import Path

if __name__ == "__main__":
    # Run-button support: let Python find the engine files in santorini/src.
    SRC = Path(__file__).parent / "santorini" / "src"
    sys.path.insert(0, str(SRC))

from santorini_types import Action, GameState


def choose_action(
    state: GameState,
    legal_actions: tuple[Action, ...],
    time_limit_seconds: float,
) -> Action:
    """Return a uniformly random member of legal_actions.

    Each Action is a complete turn: a worker, a legal adjacent move, and a
    legal adjacent build. State and legal_actions are treated as read-only.
    """
    return random.choice(legal_actions)


if __name__ == "__main__":
    # Run button: play 5 games, this bot (Bot A) vs the starter bot (Bot B).
    import run_santorini

    sys.exit(run_santorini.main(["--bot1", __file__, "--bot2", str(SRC / "starter_bot.py"), "--num-games", "5"]))
