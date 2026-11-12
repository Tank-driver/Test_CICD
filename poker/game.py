"""单机德州扑克（单挑：玩家 vs 机器人）的游戏状态机。

一手牌的生命周期：
    发牌 → 翻牌前下注 → 翻牌 → 转牌 → 河牌 → 摊牌

下注轮结束条件：双方都已行动且本轮下注额相等。
单挑规则：按钮位（小盲）翻牌前先行动，翻牌后后行动。
"""

import random

from .ai import decide
from .cards import shuffled_deck
from .evaluator import best_hand, describe

# 初始筹码与盲注
START_STACK = 1000
SMALL_BLIND = 10
BIG_BLIND = 20

# 街（下注轮）名称
STREET_NAMES = {
    "preflop": "翻牌前",
    "flop": "翻牌",
    "turn": "转牌",
    "river": "河牌",
}

# 玩家的显示名
NAMES = {0: "你", 1: "机器人"}


class Game:
    """一局单挑德州扑克。"""

    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()

        # 双方筹码
        self.stacks = [START_STACK, START_STACK]
        # 按钮位：0 表示玩家是按钮（同时也是小盲）
        self.button = 0
        self.hand_no = 0
        # 游戏是否结束（某人输光）
        self.game_over = False
        # 操作日志，最近若干条展示在页面上
        self.log: list[str] = []

        self._start_hand()

    # ==================== 发牌与初始化 ====================

    def _start_hand(self) -> None:
        """开始新的一手：轮换按钮、洗牌、发底牌、下盲注。"""
        if self.game_over:
            return

        self.hand_no += 1
        # 第一手玩家是按钮，之后每手轮换
        if self.hand_no > 1:
            self.button ^= 1

        deck = shuffled_deck(self.rng)
        # 保存牌堆，后续发公共牌都从这里取
        self._deck = deck

        # 每人两张底牌（交替发牌，模拟真实发牌顺序）
        self.hands = [[], []]
        for _ in range(2):
            for p in (0, 1):
                self.hands[p].append(deck.pop())

        self.board = []
        self.pot = 0
        self.street_bets = [0, 0]       # 本轮各自已投入
        self.acted = [False, False]     # 本轮是否已行动
        self.all_in = [False, False]
        self.street = "preflop"
        self.last_raise = BIG_BLIND     # 最近一次加注的增量
        self.hand_over = False
        self.showdown = False
        self.result = None
        self.winner = None

        # 下盲注：按钮位下小盲，另一位下大盲
        sb = self.button
        bb = 1 - self.button
        self._commit(sb, SMALL_BLIND)
        self._commit(bb, BIG_BLIND)

        # 单挑时按钮位翻牌前先行动
        self.to_act = sb

        self._log(
            f"—— 第 {self.hand_no} 手 —— "
            f"{NAMES[sb]} 下小盲 {SMALL_BLIND}，{NAMES[bb]} 下大盲 {BIG_BLIND}"
        )

    # ==================== 筹码操作 ====================

    def _commit(self, player: int, amount: int) -> int:
        """从玩家筹码中拿出 amount 投入本轮，返回实际投入额。"""
        amount = max(0, min(amount, self.stacks[player]))
        self.stacks[player] -= amount
        self.street_bets[player] += amount
        if self.stacks[player] == 0:
            self.all_in[player] = True
        return amount

    def _collect_bets(self) -> None:
        """把本轮下注收进底池。"""
        self.pot += sum(self.street_bets)
        self.street_bets = [0, 0]

    # ==================== 合法动作 ====================

    def _to_call(self, player: int) -> int:
        """该玩家需要跟注的金额。"""
        return max(self.street_bets) - self.street_bets[player]

    def min_raise_total(self, player: int) -> int:
        """最小加注后的本轮总额。"""
        return max(self.street_bets) + self.last_raise

    def max_raise_total(self, player: int) -> int:
        """最大加注（全下）后的本轮总额。"""
        return self.street_bets[player] + self.stacks[player]

    def can_raise(self, player: int) -> bool:
        """是否还有加注空间。"""
        return (
            not self.hand_over
            and self.stacks[player] > 0
            and self.max_raise_total(player) >= self.min_raise_total(player)
        )

    def legal_actions(self, player: int = 0) -> dict:
        """给界面用的动作选项。"""
        to_call = self._to_call(player)
        return {
            "can_check": to_call == 0,
            "can_call": to_call > 0,
            "call_amount": min(to_call, self.stacks[player]),
            "can_raise": self.can_raise(player),
            "min_raise": self.min_raise_total(player),
            "max_raise": self.max_raise_total(player),
        }

    # ==================== 行动 ====================

    def act(self, player: int, action: str, amount: int | None = None) -> None:
        """玩家（默认 0 号）行动，随后自动推进机器人。"""
        if self.hand_over or self.game_over:
            return
        if player != self.to_act:
            return

        self._apply(player, action, amount)

        # 机器人可能需要连续行动（例如它加注后玩家再跟注）
        guard = 0
        while (
            not self.hand_over
            and not self.game_over
            and self.to_act == 1
            and guard < 20
        ):
            kind, amt = decide(self, 1, self.rng)
            self._apply(1, kind, amt)
            guard += 1

    def _apply(self, player: int, action: str, amount: int | None = None) -> None:
        """执行一个动作并检查是否需要推进到下一条街。"""
        name = NAMES[player]
        to_call = self._to_call(player)

        # ---------- 弃牌 ----------
        if action == "fold":
            self.acted[player] = True
            self._log(f"{name} 弃牌")
            self._collect_bets()
            self._award(1 - player, "对手弃牌")
            return

        # ---------- 过牌 / 跟注 ----------
        if action == "check":
            if to_call > 0:
                action = "call"      # 不能过牌时退化为跟注
            else:
                self.acted[player] = True
                self._log(f"{name} 过牌")
                self._maybe_advance()
                return

        if action == "call":
            pay = self._commit(player, to_call)
            self.acted[player] = True
            verb = "全下" if self.all_in[player] else "跟注"
            self._log(f"{name} {verb} {pay}")
            self._maybe_advance()
            return

        # ---------- 加注 ----------
        if action == "raise":
            if not self.can_raise(player):
                # 没有加注空间，退化为跟注
                pay = self._commit(player, to_call)
                self.acted[player] = True
                self._log(f"{name} 跟注 {pay}")
                self._maybe_advance()
                return

            min_total = self.min_raise_total(player)
            max_total = self.max_raise_total(player)
            target = amount if amount else min_total
            target = max(min_total, min(target, max_total))

            previous_max = max(self.street_bets)
            paid = self._commit(player, target - self.street_bets[player])

            # 加注增量：全下不足最小加注时，保持原增量
            increment = max(self.street_bets[player] - previous_max, 0)
            if increment > 0:
                self.last_raise = max(self.last_raise, increment)

            self.acted[player] = True
            # 对手需要重新行动
            self.acted[1 - player] = False

            verb = "全下" if self.all_in[player] else "加注到"
            if verb == "全下":
                self._log(f"{name} 全下 {self.street_bets[player]}")
            else:
                self._log(f"{name} 加注到 {self.street_bets[player]}（投入 {paid}）")

            self._maybe_advance()
            return

        # 未知动作：当作过牌/跟注处理
        self._apply(player, "check")

    # ==================== 推进 ====================

    def _refund_excess(self) -> None:
        """退还未被跟注的部分（单挑时只可能有一方多投）。"""
        diff = self.street_bets[0] - self.street_bets[1]
        if diff > 0:
            self.stacks[0] += diff
            self.street_bets[0] -= diff
        elif diff < 0:
            self.stacks[1] += -diff
            self.street_bets[1] += diff

    def _maybe_advance(self) -> None:
        """判断本轮是否结束：双方都行动后结算或进入下一条街。"""
        if self.hand_over:
            return

        if all(self.acted):
            # 下注不等：说明有人全下但筹码不足，退还差额再摊牌
            if self.street_bets[0] != self.street_bets[1]:
                self._refund_excess()

            self._collect_bets()

            # 河牌结束，或有人全下 → 直接摊牌
            if self.street == "river" or any(self.all_in):
                self._run_out_and_showdown()
                return

            self._next_street()
        else:
            # 轮到对手行动
            self.to_act = 1 - self.to_act

    def _next_street(self) -> None:
        """进入下一条街：发公共牌、重置状态。"""
        order = ["preflop", "flop", "turn", "river"]
        self.street = order[order.index(self.street) + 1]

        if self.street == "flop":
            self.board.extend([self.deck_pop(), self.deck_pop(), self.deck_pop()])
        else:
            self.board.append(self.deck_pop())

        self.street_bets = [0, 0]
        self.acted = [False, False]
        self.last_raise = BIG_BLIND

        # 翻牌后：非按钮位先行动（按钮位有位置优势）
        self.to_act = 1 - self.button

        self._log(
            f"【{STREET_NAMES[self.street]}】公共牌："
            + " ".join(str(c) for c in self.board)
        )

    def deck_pop(self):
        """从牌堆顶取一张（放在方法里方便测试替换）。"""
        return self._deck.pop()

    def _run_out_and_showdown(self) -> None:
        """全下或河牌结束：补齐公共牌后摊牌。"""
        while len(self.board) < 5:
            self.board.append(self.deck_pop())

        self.showdown = True
        mine, _ = best_hand(self.hands[0] + self.board)
        theirs, _ = best_hand(self.hands[1] + self.board)

        self._log(
            f"摊牌：{NAMES[0]} {describe(mine)}，{NAMES[1]} {describe(theirs)}"
        )

        if mine > theirs:
            self._award(0, f"{describe(mine)} 获胜")
        elif mine < theirs:
            self._award(1, f"{describe(theirs)} 获胜")
        else:
            self._split_pot()

    # ==================== 结算 ====================

    def _award(self, winner: int, reason: str) -> None:
        """把底池判给赢家。"""
        amount = self.pot
        self.stacks[winner] += amount
        self.pot = 0
        self.winner = winner
        self.hand_over = True
        self.result = f"{NAMES[winner]} 赢得 {amount}（{reason}）"
        self._log(self.result)

        # 有人输光则整局结束
        if min(self.stacks) <= 0:
            self.game_over = True
            self._log("游戏结束，可以点「重新开始」再来一局")

    def _split_pot(self) -> None:
        """平局：平分底池，零头给按钮位。"""
        half = self.pot // 2
        remainder = self.pot - half * 2
        self.stacks[0] += half
        self.stacks[1] += half
        self.stacks[self.button] += remainder
        amount = self.pot
        self.pot = 0
        self.hand_over = True
        self.winner = None
        self.result = f"平局，各分 {half}（共 {amount}）"
        self._log(self.result)

    # ==================== 日志 ====================

    def _log(self, message: str) -> None:
        self.log.append(message)

    # ==================== 对外状态 ====================

    def state(self, player: int = 0) -> dict:
        """给页面/接口用的完整状态。"""
        bot = 1 - player
        reveal = self.showdown or self.hand_over

        # 当前能组成的最好牌型（公共牌至少 3 张才有意义）
        my_best = None
        if len(self.board) >= 3:
            score, _ = best_hand(self.hands[player] + self.board)
            my_best = describe(score)

        return {
            "hand_no": self.hand_no,
            "street": STREET_NAMES.get(self.street, self.street),
            "pot": self.pot + sum(self.street_bets),
            "board": [c.to_dict() for c in self.board],
            "my_cards": [c.to_dict() for c in self.hands[player]],
            "bot_cards": (
                [c.to_dict() for c in self.hands[bot]]
                if reveal
                else [{"hidden": True} for _ in range(2)]
            ),
            "my_stack": self.stacks[player],
            "bot_stack": self.stacks[bot],
            "my_bet": self.street_bets[player],
            "bot_bet": self.street_bets[bot],
            "my_turn": (not self.hand_over) and (not self.game_over) and self.to_act == player,
            "hand_over": self.hand_over,
            "game_over": self.game_over,
            "result": self.result,
            "my_best": my_best,
            "actions": self.legal_actions(player),
            "log": self.log[-12:],
        }
