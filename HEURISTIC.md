# Board-evaluation heuristic (`heuristic_bot.py`)

The bot looks ahead with alpha-beta search. When it stops looking ahead, `evaluate` gives the
board a score: higher is better for us. It is written from player 0's (our) point of view, and
it is only called when the player to move cannot win right away (the search checks that first).

## Features and why we chose them

| Feature | What it measures | Why |
| --- | --- | --- |
| **Immediate win / loss** | Someone just stepped onto level 3, or the player to move can step onto level 3 right now | This is the game's actual result, so it outweighs everything else |
| **Worker height** | Level each worker stands on, valued 0 / 40 / 120 for levels 0 / 1 / 2 | You can only win from level 2. The value rises steeply because each level up matters more than the one before |
| **Access to level 3 (threats)** | Open level-3 squares next to a worker on level 2 | A threat means "I win next turn unless you stop me" |
| **Double threats** | Two or more such squares at once | The opponent gets one build per turn, so they can dome only one. The position is lost for them |
| **Blocking opportunity** | Whether the player to move can move a worker next to the threat square and build a dome on it | A threat that can be blocked costs the opponent a turn. One that can't be blocked is a win |
| **Climb options** | Neighboring squares exactly one level higher | These are the steps toward height and future threats |
| **Mobility** | Number of squares each worker can legally move to | Few moves means you're close to being trapped. A player with no moves loses, and that is scored as a loss |
| **Center** | How close each worker is to the middle square | Center squares have 8 neighbors and corners have 3, so the center gives more options |

**Left out: the full number of legal actions.** Counting every move+build pair at every scored
board is slow and cost the bot a search depth. Mobility measures almost the same thing (how much
freedom you have) for roughly 1/8 of the work.

## How the features are combined

1. **Exact checks first.** If the player to move has no legal move, or faces a threat it can't
   block (two threats, or one that no worker can reach), the board is scored as a near-certain
   win for the other side (±100,000). These aren't guesses: the result is forced in one more turn.
2. **Otherwise, a weighted sum** of (our value − opponent's value) for each feature:

   ```
   score = height + 15·climb options + 3·mobility + 2·center ∓ 60 for a blockable threat
   ```

The weights follow how directly each feature leads to a win:
**win/loss ≫ forced threats ≫ height > blockable threat > climb options > mobility > center.**
They are named constants at the top of `heuristic_bot.py`, so they are easy to tune.

Because it's a sum of (ours − theirs), the score is symmetric: a good feature for the opponent
counts against us by the same amount. That's what minimax needs.

**Speed.** Everything is computed in one pass over each worker's 8 neighbors, so the bot still
looks about 3 turns ahead within the 2-second limit.

## Results

Same search, only the scoring function differs. 10 seeds, each bot playing first once per seed
(20 games, 2-second limit):

| Match | Result |
| --- | --- |
| `heuristic_bot` vs `alphabeta_bot` (old, simple scoring) | **14 – 6** |
| `heuristic_bot` vs `random_bot` | 10 – 0 |
| `heuristic_bot` vs `starter_bot` | 10 – 0 |

No game was lost to a timeout, crash, or invalid move.

## Tuning

We tried two other weight settings against `alphabeta_bot` (same 20-game setup) and kept the
original weights because they won the most:

| Weights | vs `alphabeta_bot` |
| --- | --- |
| **Chosen:** height 0/40/120, threat 60, climb 15, mobility 3 | **14 – 6** |
| More aggressive: height 0/30/160, threat 100 | 11 – 9 |
| More positional: climb 25, mobility 5 | 10 – 10 |

Pushing harder for height and threats, or for freedom of movement, both did worse than the
balanced mix. Twenty games is a small sample, so these numbers show a trend, not an exact ranking.
