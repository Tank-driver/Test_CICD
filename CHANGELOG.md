# 更新日志

## [3.0.0] - 2026-11-05

### 重构主题

项目从「博客系统」重构为「**单机德州扑克游戏**」。
因为游戏状态保存在内存中，**移除了 MySQL**，部署回到单容器，链路反而更简单。

### 新增 Added

**规则引擎（`poker/`）**
- `cards.py`：52 张牌、花色/点数、洗牌
- `evaluator.py`：五张牌评分 + 七选五最优组合，覆盖全部十种牌型，
  支持 A2345 轮子顺子、踢脚比较、平局判定
- `game.py`：单挑状态机——盲注、四轮下注、最小加注额、全下、
  退还未跟注筹码、摊牌结算、平局分池
- `ai.py`：蒙特卡洛胜率估算（150 次模拟）+ 底池赔率决策 + 随机扰动

**Web**
- 牌桌页面：公共牌、双方底牌、底池、筹码、牌局日志
- 操作：弃牌 / 过牌 / 跟注 / 加注（带合法区间）
- `/api/state` JSON 快照、`/new` 重开、`/health` 健康检查

**测试**
- 25 个用例：17 个牌型判定 + 12 个游戏流程（盲注、弃牌、加注、全下、摊牌、筹码守恒）

### 变更 Changed

| 项 | 变更前（2.0.0 博客） | 变更后（3.0.0 扑克） |
|---|---|---|
| 业务 | 文章 CRUD | 德州扑克对局 |
| 数据库 | MySQL 8（SQLAlchemy） | **无**（内存字典） |
| 部署拓扑 | compose 双服务（db + web） | **单容器** |
| 镜像名 | `cicd-demo` | **`poker`** |
| 容器名 | `blog-web` / `blog-db` | **`poker-web`** |
| 对外端口 | 8080 -> 5000 | 不变 |
| 部署目录 | `/data/cicd-demo` | 不变 |
| 健康检查 | 查数据库 | 只返回服务状态 |
| 测试数 | 13 | 25 |

### 移除 Removed

- `app/models.py`、`app/auth.py`、`app/blog.py` 及博客模板
- `deploy/docker-compose.yml` 中的 `db` 服务
- 依赖：`flask-sqlalchemy`、`pymysql`、`cryptography`
- `container_tokens` 相关的数据库初始化逻辑（`init-db` 命令）

### 破坏性变更 Breaking

1. **镜像名改为 `poker`**，旧的 `cicd-demo` 镜像不再使用。
2. **容器名改为 `poker-web`**，旧容器 `blog-web`、`blog-db` 必须清理，
   否则 8080 端口冲突：
   ```bash
   cd /data/cicd-demo
   docker compose down
   docker rm -f blog-web blog-db poker-web 2>/dev/null || true
   ```
3. **MySQL 数据卷不再使用**，确认无数据需要保留后可删除：
   ```bash
   docker volume rm cicd-demo_db_data   # 卷名可通过 docker volume ls 确认
   ```
4. `.env` 只需保留 `IMAGE`、`TAG`、`SECRET_KEY` 三项，数据库密码可删除。

### 升级步骤 Upgrade

```bash
# 1. 提交并推送
git add -A
git commit -m "refactor: 重构为单机德州扑克"
git push

# 2. 传部署文件到目标机
scp deploy/docker-compose.yml root@192.168.17.130:/data/cicd-demo/
scp deploy/deploy.sh          root@192.168.17.130:/data/cicd-demo/
scp deploy/.env.example       root@192.168.17.130:/data/cicd-demo/

# 3. 目标机清理旧服务
ssh root@192.168.17.130
cd /data/cicd-demo
cp docker-compose.yml docker-compose.yml.bak
docker compose down
docker rm -f blog-web blog-db poker-web 2>/dev/null || true

# 4. 重建 .env（只有三项）
cat > .env <<EOF
IMAGE=192.168.17.129:5000/poker
TAG=latest
SECRET_KEY=$(openssl rand -hex 32)
EOF
chmod 600 .env
chmod +x deploy.sh

# 5. 触发 Jenkins 构建
```

### 验证 Verify

```bash
curl http://192.168.17.130:8080/health    # {"games":1,"status":"ok"}
curl http://192.168.17.130:8080/api/state # 当前牌局快照
```

浏览器打开 `http://192.168.17.130:8080` 即可开玩。

### 回滚 Rollback

```bash
git revert HEAD --no-edit
# 部署回滚到上一构建
cd /data/cicd-demo && ./deploy.sh 192.168.17.129:5000/poker <上一个构建号>
```

> 注意：3.0.0 的 `deploy.sh` 与 2.0.0 不兼容（服务名、容器名都变了）。
> 回滚代码时需同时恢复旧 `docker-compose.yml`（`docker-compose.yml.bak`）。

### 已知问题 Known Issues

- 牌局状态在内存中，**重启容器会丢失进行中的对局**；多副本部署时会话不通用（需按会话粘滞或外置存储）。
- 机器人基于蒙特卡洛 + 固定策略，不具备诈唬/位置感知等高级能力。
- 无持久化战绩、无历史回放。

---

## [2.0.0] - 2026-11-05

### 新增
- Flask 博客系统：文章 CRUD、后台登录、草稿机制、JSON 接口
- MySQL 8 + 命名卷、gunicorn、13 个测试
- `deploy/` 目录：compose 编排、部署脚本、配置模板

### 说明
已在 3.0.0 中整体替换。

---

## [1.0.0] - 2026-11-02

### 新增
- 最小 Flask 演示应用（`/`、`/health`、`POST /add`），10 个测试
- Jenkins 流水线：拉代码 → 装依赖 → 测试 → 构建镜像
- 私有 registry + SSH 部署到 `192.168.17.130`，SCM 轮询自动触发

### 说明
用于跑通 CI/CD 全链路，已被 2.0.0 取代。
