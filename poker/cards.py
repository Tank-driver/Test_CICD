"""扑克牌基础：牌与牌堆。"""

import random

# 点数映射：内部用 2-14，14 表示 A
RANK_LABELS = {
    2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8",
    9: "9", 10: "10", 11: "J", 12: "Q", 13: "K", 14: "A",
}

# 花色：s 黑桃 / h 红桃 / d 方块 / c 梅花
SUIT_LABELS = {"s": "♠", "h": "♥", "d": "♦", "c": "♣"}


class Card:
    """一张牌。

    rank: 2-14（14 = A）
    suit: s / h / d / c
    """

    __slots__ = ("rank", "suit")

    def __init__(self, rank: int, suit: str):
        self.rank = rank
        self.suit = suit

    @property
    def label(self) -> str:
        """点数显示字符，如 A、10、7。"""
        return RANK_LABELS[self.rank]

    @property
    def suit_label(self) -> str:
        """花色符号。"""
        return SUIT_LABELS[self.suit]

    @property
    def is_red(self) -> bool:
        """红桃和方块显示为红色。"""
        return self.suit in ("h", "d")

    def to_dict(self) -> dict:
        """给模板/接口用的字典。"""
        return {
            "rank": self.rank,
            "suit": self.suit,
            "label": self.label,
            "suit_label": self.suit_label,
            "red": self.is_red,
        }

    def __repr__(self) -> str:
        return f"{self.label}{self.suit_label}"

    def __eq__(self, other) -> bool:
        return isinstance(other, Card) and (self.rank, self.suit) == (other.rank, other.suit)

    def __hash__(self) -> int:
        return hash((self.rank, self.suit))


def new_deck() -> list[Card]:
    """生成一副 52 张的新牌。"""
    return [Card(rank, suit) for suit in "shdc" for rank in range(2, 15)]


def shuffled_deck(rng: random.Random | None = None) -> list[Card]:
    """洗好的一副牌。"""
    deck = new_deck()
    (rng or random).shuffle(deck)
    return deck
