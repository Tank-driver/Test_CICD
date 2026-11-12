# 单机德州扑克（Flask + 规则引擎 + Jenkins CI/CD）

你 vs 机器人，网页操作，完整实现德州扑克规则。
包含**牌型判定引擎**、**蒙特卡洛机器人**、**游戏状态机**，以及一条完整的 CI/CD 流水线。

## 玩法

打开页面即可开始：你（按钮位）先下小盲 10，机器人下大盲 20。

- **弃牌**：放弃这手，对手赢得底池
- **过牌 / 跟注**：不投入或跟上当前注额
- **加注**：输入总额（含本轮已投入），最小加注为「当前注额 + 上次加注增量」
- 每手结束点「下一手」；筹码输光点「重新开始」

初始筹码 1000，盲注 10/20，单挑（Heads-up）规则：
按钮位翻牌前先行动，翻牌后后行动。

## 已实现的规则

- ✅ 52 张牌洗牌、每人两张底牌
- ✅ 翻牌前 / 翻牌 / 转牌 / 河牌 四轮下注
- ✅ 小盲、大盲、最小加注额限制
- ✅ 全下（All-in）、退还未被跟注的筹码
- ✅ 摊牌：七选五取最优牌型
- ✅ 十种牌型判定（含 A2345 轮子顺子）
- ✅ 平局分池（零头给按钮位）

## 目录结构

```
.
├── poker/
│   ├── cards.py        # 牌与牌堆
│   ├── evaluator.py    # 牌型判定（五张评分 + 七选五）
│   ├── ai.py           # 机器人：蒙特卡洛估胜率 + 底池赔率
│   └── game.py         # 状态机：发牌、下注、摊牌、结算
├── app/
│   ├── __init__.py     # Flask 路由（页面 + /api/state + /health）
│   ├── templates/      # 牌桌页面
│   └── static/         # 样式
├── tests/
│   ├── test_evaluator.py   # 17 个牌型用例
│   └── test_game.py        # 12 个流程用例
├── deploy/                 # 目标机部署文件
├── wsgi.py                 # gunicorn 入口
└── Jenkinsfile
```

## 本地运行

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

python wsgi.py
# 打开 http://127.0.0.1:5000
```

## 测试

```bash
pytest -v
```

25 个用例，覆盖牌型判定、七选五、盲注、弃牌、加注、全下、摊牌、状态输出。

## 接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/` | 牌桌页面 |
| POST | `/action` | 执行动作（`action=fold/check/call/raise`，`amount=总额`） |
| POST | `/new` | 重开一局 |
| GET | `/api/state` | 当前牌局 JSON 快照 |
| GET | `/health` | 健康检查（容器探针用） |

## 技术要点

**牌型判定**：先给五张牌打分（元组，可直接比较大小），七张牌时枚举 21 种组合取最大。
比较逻辑天然处理踢脚（kicker），例如两对先比大对、再比小对、最后比单张。

**机器人**：对当前手牌做 150 次蒙特卡洛模拟（随机对手底牌 + 补齐公共牌），
估算胜率后与底池赔率比较：胜率低于赔率就弃牌，明显领先就加注，其余跟注。

**状态管理**：牌局对象按会话 ID 存在内存字典里，无需数据库。
重启容器会丢失进行中的牌局（设计上可接受）。

## 部署

目标机 `/data/cicd-demo/` 下放 `docker-compose.yml`、`deploy.sh`、`.env`，
由 Jenkins 通过 SSH 调用 `deploy.sh` 完成滚动更新。

详见 `deploy/` 目录与 `CHANGELOG.md` 的升级说明。

## CI/CD

```
Checkout → Install → Test(25) → Build → Push → Deploy → Smoke Test
```

- push 代码后由 SCM 轮询自动触发
- 镜像推送到私有仓库 `192.168.17.129:5000/poker`
- 部署后请求 `/health` 验证
