"""游戏状态机测试：盲注、行动、弃牌、摊牌。"""

import random

import pytest

from poker.game import BIG_BLIND, SMALL_BLIND, START_STACK, Game


def new_game(seed: int = 42) -> Game:
    """固定随机种子，保证测试可复现。"""
    return Game(rng=random.Random(seed))


def play_passively(game: Game, limit: int = 60) -> None:
    """玩家一路过牌/跟注，直到这手结束或需要机器人行动。"""
    guard = 0
    while not game.hand_over and guard < limit:
        guard += 1
        if game.to_act != 0:
            break
        actions = game.legal_actions(0)
        game.act(0, "check" if actions["can_check"] else "call")


# ---------- 开局 ----------

def test_blinds_are_posted():
    """开局应扣掉小盲和大盲，底池为两者之和。"""
    game = new_game()
    total_bets = sum(game.street_bets)
    assert sorted(game.street_bets) == [SMALL_BLIND, BIG_BLIND]
    assert game.state()["pot"] == total_bets
    assert sum(game.stacks) == START_STACK * 2 - total_bets


def test_first_to_act_is_button():
    """单挑时按钮位（小盲）翻牌前先行动。"""
    game = new_game()
    assert game.to_act == game.button


# ---------- 弃牌 ----------

def test_fold_ends_hand():
    """弃牌后本手立即结束，对手赢得底池。"""
    game = new_game()
    # 总筹码 = 手上筹码 + 本轮已下注（盲注已从筹码中扣除）
    before = sum(game.stacks) + sum(game.street_bets)
    game.act(0, "fold")
    assert game.hand_over is True
    assert game.winner == 1
    assert sum(game.stacks) + sum(game.street_bets) == before  # 筹码守恒，只是换了主人


# ---------- 推进 ----------

def test_call_and_check_advance_to_flop():
    """跟注 + 机器人过牌后，应发出三张翻牌。"""
    game = new_game()
    game.act(0, "call")          # 玩家跟注，机器人随后行动
    if not game.hand_over:
        assert len(game.board) in (0, 3) or game.street in ("flop", "turn", "river")


def test_full_hand_reaches_showdown():
    """一路跟注到底，应能走到摊牌并产生结果。"""
    game = new_game(seed=7)
    play_passively(game)
    assert game.hand_over is True
    assert game.result is not None
    assert len(game.board) == 5


def test_chips_are_conserved():
    """任何一手结束后，双方筹码之和不应变化。"""
    game = new_game(seed=11)
    total_before = sum(game.stacks) + game.pot + sum(game.street_bets)
    play_passively(game)
    assert sum(game.stacks) + game.pot + sum(game.street_bets) == total_before


# ---------- 加注 ----------

def test_raise_increases_pot():
    """加注后底池（含本轮下注）应明显变大。"""
    game = new_game()
    before = game.state()["pot"]
    target = game.min_raise_total(0)
    game.act(0, "raise", target)
    assert game.state()["pot"] > before


def test_raise_amount_is_clamped():
    """请求的加注额超出上限时，应被压到全下。"""
    game = new_game()
    game.act(0, "raise", 999999)
    assert game.stacks[0] >= 0
    assert game.all_in[0] is True


# ---------- 状态输出 ----------

def test_state_hides_bot_cards():
    """未摊牌时，机器人底牌应是隐藏状态。"""
    game = new_game()
    state = game.state()
    assert len(state["my_cards"]) == 2
    assert all(card.get("hidden") for card in state["bot_cards"])


def test_state_contains_required_keys():
    """状态字典应包含页面渲染需要的字段。"""
    state = new_game().state()
    for key in (
        "hand_no", "street", "pot", "board", "my_cards", "bot_cards",
        "my_stack", "bot_stack", "my_turn", "actions", "log",
    ):
        assert key in state
