"""机器人决策：用蒙特卡洛模拟估算胜率，再结合底池赔率行动。"""

import random

from .cards import Card, new_deck
from .evaluator import best_hand


def estimate_equity(
    hole: list[Card],
    board: list[Card],
    n: int = 200,
    rng: random.Random | None = None,
) -> float:
    """估算当前手牌的胜率（含平局折半）。

    做法：随机给对手发两张、把公共牌补满，比较双方牌力，重复 n 次。

    :param hole: 自己的两张底牌
    :param board: 已发出的公共牌（0/3/4/5 张）
    :param n: 模拟次数，越大越准也越慢
    :return: 0.0 - 1.0 的胜率
    """
    rng = rng or random.Random()

    known = set(hole) | set(board)
    rest = [c for c in new_deck() if c not in known]

    need_board = 5 - len(board)
    wins = 0.0

    for _ in range(n):
        # 一次性抽取：对手两张 + 剩余公共牌
        sample = rng.sample(rest, 2 + need_board)
        opp_hole = sample[:2]
        full_board = board + sample[2:]

        mine, _ = best_hand(hole + full_board)
        theirs, _ = best_hand(opp_hole + full_board)

        if mine > theirs:
            wins += 1.0
        elif mine == theirs:
            wins += 0.5  # 平局按半分池计算

    return wins / n


def decide(game, player: int = 1, rng: random.Random | None = None):
    """机器人行动决策。

    :return: (动作, 加注总额) —— 动作为 fold / check / call / raise
    """
    rng = rng or random.Random()
    hole = game.hands[player]
    board = game.board

    to_call = max(game.street_bets) - game.street_bets[player]
    pot = game.pot + sum(game.street_bets)

    # 估算胜率，并加入少量随机扰动，避免行为完全可预测
    equity = estimate_equity(hole, board, n=150, rng=rng)
    equity = max(0.0, min(1.0, equity + rng.uniform(-0.04, 0.04)))

    # 底池赔率：跟注额 / (底池 + 跟注额)
    pot_odds = to_call / (pot + to_call) if to_call > 0 else 0.0

    can_raise = game.can_raise(player)

    # 无需跟注：要么过牌，要么主动下注
    if to_call == 0:
        if can_raise and equity > 0.72:
            return "raise", game.min_raise_total(player)
        if can_raise and equity > 0.55 and rng.random() < 0.45:
            return "raise", game.min_raise_total(player)
        return "check", None

    # 胜率明显低于赔率要求 → 弃牌
    if equity < pot_odds + 0.02:
        return "fold", None

    # 胜率很高 → 加注施压
    if can_raise and equity > 0.80 and rng.random() < 0.7:
        return "raise", game.min_raise_total(player)

    return "call", None
