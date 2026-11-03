# Santorini AI Bots

Bots that play the board game Santorini. To win, you move a worker onto a level-3 building.

| Bot | How it plays |
|---|---|
| `random_bot.py` | Picks a random legal move |
| `alphabeta_bot.py` | Looks a few turns ahead with alpha-beta search |
| `heuristic_bot.py` | Same search, plus our own way of scoring boards. See [HEURISTIC.md](HEURISTIC.md). |

`run_eval.py` plays 50 games of the search bot vs. the random bot and saves the results.

The game engine and match runner were given as starter code. I wrote the bots, the experiment and the tests for the bots.

## Run it

```bash
pip install -r requirements.txt
```

Play one game:

```bash
python src/run_santorini.py --bot1 src/heuristic_bot.py --bot2 src/random_bot.py --num-games 1
```

Run the 50-game experiment:

```bash
python src/run_eval.py
```

Replay a saved game (example: game 36):

```bash
python src/show_game.py 36
```

Run the tests:

```bash
python -m pytest tests -q
```
