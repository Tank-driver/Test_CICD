"""Flask 应用：网页版的单机德州扑克。

游戏状态保存在内存里（按会话 ID 区分），所以不需要数据库。
重启容器会清空进行中的牌局，这一点在设计上是可接受的。
"""

import os
import uuid

from flask import Flask, jsonify, redirect, render_template, request, session, url_for

from poker.game import Game

# 会话 ID → Game 实例
GAMES: dict[str, Game] = {}


def create_app(config: dict | None = None) -> Flask:
    """应用工厂。"""
    app = Flask(__name__)

    app.config.update(
        # 会话签名密钥；多实例部署时必须统一，否则会话不通用
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-secret-change-me"),
    )
    if config:
        app.config.update(config)

    def current_game() -> Game:
        """取出当前会话的牌局，没有就新建。"""
        sid = session.get("sid")
        if not sid:
            sid = uuid.uuid4().hex
            session["sid"] = sid
        game = GAMES.get(sid)
        if game is None:
            game = Game()
            GAMES[sid] = game
        return game

    # ---------- 页面 ----------

    @app.get("/")
    def index():
        """牌桌页面。"""
        return render_template("table.html", g=current_game().state())

    @app.post("/action")
    def action():
        """处理玩家的一个动作，然后重定向回牌桌（避免刷新重复提交）。"""
        game = current_game()
        kind = request.form.get("action", "")
        amount = request.form.get("amount", type=int)
        game.act(0, kind, amount)
        return redirect(url_for("index"))

    @app.post("/new")
    def new_game():
        """重开一局（筹码清零后使用）。"""
        sid = session.get("sid") or uuid.uuid4().hex
        session["sid"] = sid
        GAMES[sid] = Game()
        return redirect(url_for("index"))

    # ---------- 运维 ----------

    @app.get("/health")
    def health():
        """健康检查：容器探针用。"""
        return jsonify(status="ok", games=len(GAMES))

    @app.get("/api/state")
    def api_state():
        """当前牌局的 JSON 快照，方便调试或做前端。"""
        return jsonify(current_game().state())

    return app
