"""Look-ahead Santorini bot: minimax search with alpha-beta pruning.

The bot looks several turns ahead using the engine's ``successors`` function.
It searches 1 turn deep, then 2, then 3, ... (iterative deepening) and keeps
the best move from the deepest search that finished before its time budget
ran out.  Inside the search our bot is always player 0 (the maximizer) and the
opponent is player 1 (the minimizer).
"""

import sys
from pathlib import Path
from time import perf_counter

if __name__ == "__main__":
    # Run-button support: let Python find the engine files in santorini/src.
    SRC = Path(__file__).parent / "santorini" / "src"
    sys.path.insert(0, str(SRC))

from santorini_engine import BOARD_SIZE, NEIGHBOR_OFFSETS, BoardState, successors
from santorini_types import Action, GameState

WIN_SCORE = 1_000_000
HEIGHT_WEIGHT = 100  # per level a worker stands on
CLIMB_WEIGHT = 10  # per neighboring square exactly one level higher
THREAT_WEIGHT = 50  # per worker on level 2 next to an open level-3 square
CENTER_WEIGHT = 2  # per step closer to the center

TIME_FRACTION = 0.75  # share of the time limit the search may use
MAX_DEPTH = 20


class TimeUp(Exception):
    """Raised inside the search when the time budget is spent."""


def choose_action(
    state: GameState,
    legal_actions: tuple[Action, ...],
    time_limit_seconds: float,
) -> Action:
    """Return the best member of legal_actions found by alpha-beta search.

    State and legal_actions are read-only.
    """
    deadline = perf_counter() + TIME_FRACTION * time_limit_seconds

    # Shortcut: stepping onto level 3 wins immediately.
    for action in legal_actions:
        if state.heights[action.move_to.row][action.move_to.column] == 3:
            return action

    board = BoardState(
        heights=state.heights,
        workers=(state.current_workers, state.opponent_workers),
        current_player=0,
        turn_number=state.turn_number,
    )
    children = _ordered_successors(board)
    best_action = children[0][0]

    for depth in range(1, MAX_DEPTH + 1):
        try:
            best_action, best_score = _search_root(children, depth, deadline)
        except TimeUp:
            break
        # Try this depth's best move first next time; it makes pruning work better.
        children.sort(key=lambda pair: pair[0] != best_action)
        if abs(best_score) >= WIN_SCORE - MAX_DEPTH:
            break  # a forced win or loss is already certain

    return best_action if best_action in legal_actions else legal_actions[0]


def _search_root(
    children: list[tuple[Action, BoardState]], depth: int, deadline: float
) -> tuple[Action, float]:
    """Search every root move to ``depth`` turns and return the best one."""
    best_action, best_score = children[0][0], -float("inf")
    alpha = -float("inf")
    for action, child in children:
        score = _alphabeta(child, depth - 1, alpha, float("inf"), 1, deadline)
        if score > best_score:
            best_action, best_score = action, score
        alpha = max(alpha, score)
    return best_action, best_score


def _alphabeta(board: BoardState, depth: int, alpha: float, beta: float, ply: int, deadline: float) -> float:
    """Minimax value of ``board`` for player 0, skipping branches that cannot matter.

    ``ply`` counts turns from the root so that quicker wins (and slower
    losses) score better.
    """
    if perf_counter() > deadline:
        raise TimeUp

    if board.winner is not None:
        return WIN_SCORE - ply if board.winner == 0 else -WIN_SCORE + ply
    if depth == 0:
        # Look one turn past the horizon for free: an immediate win can't be stopped.
        if _can_win_now(board):
            return WIN_SCORE - (ply + 1) if board.current_player == 0 else -WIN_SCORE + (ply + 1)
        return evaluate(board)

    children = _ordered_successors(board)
    if not children:  # the player to move is stuck and loses
        return -WIN_SCORE + ply if board.current_player == 0 else WIN_SCORE - ply

    if board.current_player == 0:
        value = -float("inf")
        for _, child in children:
            value = max(value, _alphabeta(child, depth - 1, alpha, beta, ply + 1, deadline))
            alpha = max(alpha, value)
            if alpha >= beta:
                break  # the opponent will never allow this line
        return value

    value = float("inf")
    for _, child in children:
        value = min(value, _alphabeta(child, depth - 1, alpha, beta, ply + 1, deadline))
        beta = min(beta, value)
        if alpha >= beta:
            break  # we will never allow this line
    return value


def _ordered_successors(board: BoardState) -> list[tuple[Action, BoardState]]:
    """Successors with winning moves first, then moves that climb highest."""
    heights = board.heights
    return sorted(
        successors(board),
        key=lambda pair: (
            pair[1].winner is not None,
            heights[pair[0].move_to.row][pair[0].move_to.column],
        ),
        reverse=True,
    )


def _can_win_now(board: BoardState) -> bool:
    """True if the player to move has a worker on level 2 next to an open level 3."""
    heights = board.heights
    occupied = {(worker.row, worker.column) for worker in board.workers[0] + board.workers[1]}
    for worker in board.workers[board.current_player]:
        if heights[worker.row][worker.column] < 2:
            continue
        for row_offset, column_offset in NEIGHBOR_OFFSETS:
            row, column = worker.row + row_offset, worker.column + column_offset
            on_board = 0 <= row < BOARD_SIZE and 0 <= column < BOARD_SIZE
            if on_board and (row, column) not in occupied and heights[row][column] == 3:
                return True
    return False


def evaluate(board: BoardState) -> float:
    """Score a non-terminal board from player 0's point of view (higher is better)."""
    heights = board.heights
    occupied = {(worker.row, worker.column) for worker in board.workers[0] + board.workers[1]}
    center = BOARD_SIZE // 2
    score = 0.0

    for player, sign in ((0, 1), (1, -1)):
        for worker in board.workers[player]:
            here = heights[worker.row][worker.column]
            score += sign * HEIGHT_WEIGHT * here
            score += sign * CENTER_WEIGHT * (center - max(abs(worker.row - center), abs(worker.column - center)))

            threatens_win = False
            for row_offset, column_offset in NEIGHBOR_OFFSETS:
                row, column = worker.row + row_offset, worker.column + column_offset
                if not (0 <= row < BOARD_SIZE and 0 <= column < BOARD_SIZE) or (row, column) in occupied:
                    continue
                if heights[row][column] == here + 1 and heights[row][column] <= 3:
                    score += sign * CLIMB_WEIGHT
                if here == 2 and heights[row][column] == 3:
                    threatens_win = True
            if threatens_win:
                score += sign * THREAT_WEIGHT

    return score


if __name__ == "__main__":
    # Run button: play 5 games, this bot (Bot A) vs the random bot (Bot B).
    import run_santorini

    opponent = Path(__file__).parent / "random_bot.py"
    sys.exit(run_santorini.main(["--bot1", __file__, "--bot2", str(opponent), "--num-games", "5"]))
