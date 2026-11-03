"""Print a saved game turn by turn.  Usage:  python src/show_game.py 36

Reads results/games.json (created by src/run_eval.py).
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent  # the src/ folder
sys.path.insert(0, str(HERE))

from santorini_engine import apply_action, setup  # noqa: E402
from santorini_types import Action, Coordinate  # noqa: E402

games_file = HERE.parent / "results" / "games.json"
if not games_file.exists():
    sys.exit("results/games.json not found. Run  python src/run_eval.py  first.")
if len(sys.argv) < 2:
    sys.exit("Usage: python src/show_game.py <game number>")

games = json.load(open(games_file))
game = games[int(sys.argv[1]) - 1]
board = setup(game["seed"])

search_player = 0 if game["order"] == "search_first" else 1
letters = (("A", "B"), ("C", "D"))
print(f"Game {game['game']}: search bot is workers {''.join(letters[search_player])} "
      f"(moves {'first' if search_player == 0 else 'second'}); winner: {game['winner']}, "
      f"{game['turns']} turns, ended by {game['reason']}")
print("Board key: height digit then worker letter ('.' = empty, D = dome)\n")


def show(b):
    spots = {}
    for player in (0, 1):
        for index, w in enumerate(b.workers[player]):
            spots[(w.row, w.column)] = letters[player][index]
    for r in range(5):
        cells = []
        for c in range(5):
            h = b.heights[r][c]
            cells.append(("D" if h == 4 else str(h)) + spots.get((r, c), "."))
        print("  " + "  ".join(cells))
    print()


print("Start:")
show(board)
for n, m in enumerate(game["moves"], 1):
    mover = board.current_player
    who = "SEARCH" if mover == search_player else "RANDOM"
    action = Action(
        worker=m["worker"],
        move_to=Coordinate(**m["move_to"]),
        build_at=Coordinate(**m["build_at"]),
    )
    board = apply_action(board, action)
    mv, bd = m["move_to"], m["build_at"]
    letter = letters[mover][m["worker"]]
    line = f"Turn {n} ({who}): worker {letter} moves to ({mv['row']},{mv['column']})"
    if board.winner is not None:
        line += " and WINS"
    else:
        line += f", builds at ({bd['row']},{bd['column']})"
    print(line)
    show(board)
