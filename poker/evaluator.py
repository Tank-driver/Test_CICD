"""牌型判定。

核心思路：
1. 先算五张牌的得分（元组，可直接比较大小）；
2. 七张牌时枚举所有 C(7,5)=21 种组合，取最大的那个。

得分元组格式：(牌型等级, 比较用的点数...)，比较时从左到右依次比较。
等级越大牌越大：
    8 同花顺 / 7 四条 / 6 葫芦 / 5 同花 / 4 顺子
    3 三条 / 2 两对 / 1 一对 / 0 高牌
"""

from collections import Counter
from itertools import combinations

from .cards import Card

# 牌型名称（中文），用于界面展示
CATEGORY_NAMES = {
    8: "同花顺",
    7: "四条",
    6: "葫芦",
    5: "同花",
    4: "顺子",
    3: "三条",
    2: "两对",
    1: "一对",
    0: "高牌",
}

# 皇家同花顺作为同花顺的特例单独展示
ROYAL_NAME = "皇家同花顺"


def _straight_high(ranks: list[int]) -> int | None:
    """判断是否能组成顺子，返回顺子最大牌；不能则返回 None。

    A 可以当作 1 使用，因此 A-2-3-4-5 是合法顺子，最大牌算 5。
    """
    uniq = sorted(set(ranks), reverse=True)
    # 把 A 也当成 1 加进去，处理 A2345
    if 14 in uniq:
        uniq.append(1)

    # 排序后找连续 5 张：首尾差为 4 即连续
    for i in range(len(uniq) - 4):
        window = uniq[i : i + 5]
        if window[0] - window[4] == 4:
            return window[0]
    return None


def evaluate_five(cards: list[Card]) -> tuple:
    """评估恰好五张牌的牌型，返回可比较的元组。"""
    assert len(cards) == 5

    ranks = sorted((c.rank for c in cards), reverse=True)
    is_flush = len({c.suit for c in cards}) == 1
    straight_high = _straight_high(ranks)

    # 统计每个点数出现次数，按 (次数, 点数) 降序排列
    counts = Counter(ranks)
    groups = sorted(counts.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)

    # 同花顺
    if is_flush and straight_high:
        return (8, straight_high)

    # 四条：四张同点 + 一张踢脚
    if groups[0][1] == 4:
        quad = groups[0][0]
        kicker = max(r for r in ranks if r != quad)
        return (7, quad, kicker)

    # 葫芦：三条 + 一对
    if groups[0][1] == 3 and groups[1][1] == 2:
        return (6, groups[0][0], groups[1][0])

    # 同花
    if is_flush:
        return (5, *ranks)

    # 顺子
    if straight_high:
        return (4, straight_high)

    # 三条：三条 + 两张踢脚
    if groups[0][1] == 3:
        three = groups[0][0]
        kickers = sorted((r for r in ranks if r != three), reverse=True)[:2]
        return (3, three, *kickers)

    # 两对：大对 + 小对 + 踢脚
    if groups[0][1] == 2 and groups[1][1] == 2:
        high_pair, low_pair = sorted((groups[0][0], groups[1][0]), reverse=True)
        kicker = max(r for r in ranks if r not in (high_pair, low_pair))
        return (2, high_pair, low_pair, kicker)

    # 一对：一对 + 三张踢脚
    if groups[0][1] == 2:
        pair = groups[0][0]
        kickers = sorted((r for r in ranks if r != pair), reverse=True)[:3]
        return (1, pair, *kickers)

    # 高牌
    return (0, *ranks)


def best_hand(cards: list[Card]) -> tuple[tuple, list[Card]]:
    """从 5-7 张牌中选出最大的五张。

    :return: (得分元组, 组成该牌型的五张牌)
    """
    if len(cards) < 5:
        raise ValueError("至少需要 5 张牌")

    best_score = None
    best_combo = None
    for combo in combinations(cards, 5):
        score = evaluate_five(list(combo))
        if best_score is None or score > best_score:
            best_score, best_combo = score, list(combo)
    return best_score, best_combo


def describe(score: tuple) -> str:
    """把得分元组转成中文描述，如「葫芦 (8 带 5)」。"""
    category = score[0]
    name = CATEGORY_NAMES[category]

    if category == 8 and score[1] == 14:
        return ROYAL_NAME

    return name


def compare(a: list[Card], b: list[Card]) -> int:
    """比较两组牌（各 5-7 张）。

    :return: 1 表示 a 大，-1 表示 b 大，0 表示平局
    """
    score_a, _ = best_hand(a)
    score_b, _ = best_hand(b)
    if score_a > score_b:
        return 1
    if score_a < score_b:
        return -1
    return 0
