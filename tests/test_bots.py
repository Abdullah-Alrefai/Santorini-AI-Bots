"""Checks that both bots follow the required interface and play legal, timely moves."""
import importlib.util
import sys
from pathlib import Path
from time import perf_counter

SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC))

from santorini_engine import apply_action, legal_actions_from, public_state_for, setup  # noqa: E402

TIME_LIMIT = 2.0


def load(name):
    spec = importlib.util.spec_from_file_location(name, str(SRC / f"{name}.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_bots_have_choose_action():
    for name in ("random_bot", "heuristic_bot"):
        assert callable(load(name).choose_action)


def test_bots_return_legal_actions_within_time():
    random_bot = load("random_bot").choose_action
    search_bot = load("heuristic_bot").choose_action
    for seed in (1, 2, 3):
        board = setup(seed)
        for turn in range(12):
            legal = legal_actions_from(board)
            if not legal or board.winner is not None:
                break
            bot = search_bot if board.current_player == 0 else random_bot
            state = public_state_for(board, board.current_player)
            started = perf_counter()
            action = bot(state, legal, TIME_LIMIT)
            assert perf_counter() - started <= TIME_LIMIT
            assert action in legal
            board = apply_action(board, action)


def test_search_bot_takes_an_immediate_win():
    """If a worker can step onto level 3, the search bot must do it."""
    search_bot = load("heuristic_bot").choose_action
    board = setup(0)
    for _ in range(60):
        legal = legal_actions_from(board)
        if not legal or board.winner is not None:
            break
        state = public_state_for(board, board.current_player)
        winning = [a for a in legal if state.heights[a.move_to.row][a.move_to.column] == 3]
        if winning and board.current_player == 0:
            assert search_bot(state, legal, TIME_LIMIT) in winning
            return
        board = apply_action(board, legal[0])
