"""Run the 50-game experiment (search bot vs. random bot) and save the results.

Run from the project folder:   python src/run_eval.py
Writes to results/:  games.json, depths.txt, config.json, summary.txt
"""
import importlib.util
import json
import os
import platform
import statistics as st
import sys
from dataclasses import asdict
from pathlib import Path

HERE = Path(__file__).resolve().parent  # the src/ folder
RESULTS = HERE.parent / "results"
RESULTS.mkdir(exist_ok=True)
sys.path.insert(0, str(HERE))
os.chdir(RESULTS)  # the logged bot writes depths.txt into the current folder

from santorini_harness import MatchConfig, run_santorini_tournament  # noqa: E402

SEARCH_BOT = HERE / "heuristic_bot_logged.py"
RANDOM_BOT = HERE / "random_bot.py"
GAMES_PER_SIDE = int(sys.argv[1]) if len(sys.argv) > 1 else 25
SEED = 2026
TIME_LIMIT = 2.0
MAX_TURNS = 200
DEPTH_FILE = RESULTS / "depths.txt"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.choose_action


def read_depths():
    if not DEPTH_FILE.exists():
        return []
    return [int(x) for x in DEPTH_FILE.read_text().split()]


if DEPTH_FILE.exists():
    DEPTH_FILE.unlink()

config_info = {
    "search_bot": SEARCH_BOT.name,
    "random_bot": RANDOM_BOT.name,
    "games_per_side": GAMES_PER_SIDE,
    "total_games": 2 * GAMES_PER_SIDE,
    "base_seed": SEED,
    "seeds_used_in_each_order": [SEED + i for i in range(GAMES_PER_SIDE)],
    "time_limit_seconds": TIME_LIMIT,
    "max_turns": MAX_TURNS,
    "python_version": platform.python_version(),
    "note": "random_bot.py is not seeded, so exact games differ between runs.",
}
with open(RESULTS / "config.json", "w") as f:
    json.dump(config_info, f, indent=2)

search = load(SEARCH_BOT, "search_bot")
rand = load(RANDOM_BOT, "random_bot")

games = []
for order in ("search_first", "random_first"):
    bot_a, bot_b = (search, rand) if order == "search_first" else (rand, search)
    search_id = 0 if order == "search_first" else 1
    for i in range(GAMES_PER_SIDE):
        seed = SEED + i
        seen = len(read_depths())
        config = MatchConfig(move_time_limit_seconds=TIME_LIMIT, max_turns=MAX_TURNS, seed=seed)
        result = run_santorini_tournament(bot_a, bot_b, config=config, num_games=1)[0]
        if result.winner is None:
            winner = "draw"
        else:
            winner = "search" if result.winner == search_id else "random"
        games.append(
            {
                "game": len(games) + 1,
                "order": order,
                "seed": seed,
                "winner": winner,
                "reason": result.reason.value,
                "turns": result.turns_played,
                "detail": result.detail,
                "depths": read_depths()[seen:],
                "moves": [asdict(m) for m in result.moves],
            }
        )
        print(f"game {len(games)} done: {winner} wins in {result.turns_played} turns", flush=True)

with open(RESULTS / "games.json", "w") as f:
    json.dump(games, f)

lines = []


def out(text=""):
    print(text)
    lines.append(text)


turns = [g["turns"] for g in games]
depths = [d for g in games for d in g["depths"]]
reasons = {}
for g in games:
    reasons[g["reason"]] = reasons.get(g["reason"], 0) + 1

out("\n===== SUMMARY =====")
out(f"Games: {len(games)}")
out(f"search wins: {sum(g['winner'] == 'search' for g in games)}")
out(f"random wins: {sum(g['winner'] == 'random' for g in games)}")
out(f"Draws: {sum(g['winner'] == 'draw' for g in games)}")
for order in ("search_first", "random_first"):
    sub = [g for g in games if g["order"] == order]
    out(f"  {order}: search won {sum(g['winner'] == 'search' for g in sub)} of {len(sub)}")
out(f"How games ended: {reasons}")
out(f"Turns: avg {round(st.mean(turns), 1)} min {min(turns)} max {max(turns)}")
if depths:
    out(f"Search depth: avg {round(st.mean(depths), 2)} min {min(depths)} max {max(depths)}")
    for label, sl in (("first 3 moves", slice(0, 3)), ("later moves", slice(3, None))):
        vals = [d for g in games for d in g["depths"][sl]]
        if vals:
            out(f"  depth, {label}: avg {round(st.mean(vals), 2)}")
longest = max(games, key=lambda g: g["turns"])
shortest = min(games, key=lambda g: g["turns"])
out(f"Longest game: #{longest['game']} ({longest['turns']} turns)")
out(f"Shortest game: #{shortest['game']} ({shortest['turns']} turns)")
out("Saved to the results/ folder. Replay a game with:  python src/show_game.py <game number>")

with open(RESULTS / "summary.txt", "w") as f:
    f.write("\n".join(lines).strip() + "\n")
