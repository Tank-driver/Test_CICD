"""牌型判定测试：覆盖所有等级和几个经典边界。"""

import pytest

from poker.cards import Card
from poker.evaluator import best_hand, describe, evaluate_five

RANK_MAP = {"A": 14, "K": 13, "Q": 12, "J": 11, "T": 10}


def C(spec: str) -> Card:
    """把 'As'、'Th' 这样的字符串转成 Card。"""
    rank_char, suit = spec[0], spec[1].lower()
    rank = RANK_MAP.get(rank_char) or int(rank_char)
    return Card(rank, suit)


def hand(*specs: str) -> list[Card]:
    return [C(s) for s in specs]


# ---------- 各牌型 ----------

def test_royal_flush():
    score = evaluate_five(hand("As", "Ks", "Qs", "Js", "Ts"))
    assert score[0] == 8
    assert score[1] == 14
    assert describe(score) == "皇家同花顺"


def test_straight_flush():
    score = evaluate_five(hand("9h", "8h", "7h", "6h", "5h"))
    assert score == (8, 9)


def test_four_of_a_kind():
    score = evaluate_five(hand("7s", "7h", "7d", "7c", "Ks"))
    assert score == (7, 7, 13)


def test_full_house():
    score = evaluate_five(hand("8s", "8h", "8d", "5c", "5d"))
    assert score == (6, 8, 5)


def test_flush():
    score = evaluate_five(hand("Ac", "Jc", "8c", "5c", "2c"))
    assert score[0] == 5


def test_straight():
    score = evaluate_five(hand("9s", "8h", "7d", "6c", "5s"))
    assert score == (4, 9)


def test_wheel_straight_is_lowest():
    """A-2-3-4-5 是顺子，但属于最小的顺子。"""
    wheel = evaluate_five(hand("As", "2h", "3d", "4c", "5s"))
    six_high = evaluate_five(hand("2s", "3h", "4d", "5c", "6s"))
    assert wheel == (4, 5)
    assert wheel < six_high


def test_three_of_a_kind():
    score = evaluate_five(hand("Qs", "Qh", "Qd", "9c", "4s"))
    assert score == (3, 12, 9, 4)


def test_two_pair_kicker_matters():
    """两对相同，比踢脚。"""
    better = evaluate_five(hand("Js", "Jh", "4d", "4c", "As"))
    worse = evaluate_five(hand("Jd", "Jc", "4h", "4s", "Ks"))
    assert better > worse


def test_one_pair():
    score = evaluate_five(hand("Ts", "Th", "Kd", "7c", "3s"))
    assert score == (1, 10, 13, 7, 3)


def test_high_card():
    score = evaluate_five(hand("As", "Jh", "9d", "6c", "3s"))
    assert score == (0, 14, 11, 9, 6, 3)


# ---------- 七选五 ----------

def test_best_hand_picks_flush_from_seven():
    """七张牌里有五张同花，应识别为同花而不是两对之类。"""
    cards = hand("Ah", "Kh", "9h", "5h", "2h", "Kd", "Ks")
    score, best = best_hand(cards)
    assert score[0] == 5
    assert len(best) == 5
    assert all(c.suit == "h" for c in best)


def test_best_hand_prefers_full_house_over_flush():
    cards = hand("8s", "8h", "8d", "5c", "5d", "2c", "9h")
    score, _ = best_hand(cards)
    assert score[0] == 6


# ---------- 比较 ----------

def test_compare_same_category_by_kicker():
    a = hand("As", "Kd", "Qc", "Jh", "9s")
    b = hand("Ah", "Kc", "Qd", "Js", "8h")
    assert best_hand(a)[0] > best_hand(b)[0]


def test_identical_hands_tie():
    a = hand("As", "Kd", "Qc", "Jh", "Ts")
    b = hand("Ah", "Kc", "Qd", "Js", "Th")
    assert best_hand(a)[0] == best_hand(b)[0]
