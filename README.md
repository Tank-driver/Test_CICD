# CICD 演示项目（Python + Flask）

一个用于练习 Jenkins CI/CD 流水线的最小可运行项目。

## 功能

| 接口 | 方法 | 说明 |
|---|---|---|
| `/` | GET | 返回服务名与版本 |
| `/health` | GET | 健康检查，返回 `{"status": "ok"}` |
| `/add` | POST | 计算两整数之和，请求体 `{"a": 1, "b": 2}` |

## 本地运行

```bash
# 1. 创建虚拟环境（可选，但推荐）
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows

# 2. 安装依赖（国内可加 -i 清华源）
pip install -r requirements.txt

# 3. 启动服务
python app.py
# 访问 http://127.0.0.1:5000/health

# 4. 运行测试
pytest -v
```

## 在 Docker 中运行

```bash
# 构建镜像
docker build -t cicd-demo:latest .

# 启动容器（映射到宿主机 5000 端口）
docker run -d --name cicd-demo -p 5000:5000 cicd-demo:latest

# 验证
curl http://127.0.0.1:5000/health
curl -X POST http://127.0.0.1:5000/add \
     -H 'Content-Type: application/json' \
     -d '{"a": 1, "b": 2}'
```

## 目录结构

```
.
├── app.py                 # Flask 应用（业务逻辑 + 接口）
├── requirements.txt       # 依赖清单
├── tests/
│   ├── __init__.py
│   └── test_app.py        # 单元测试 + 接口测试
├── Dockerfile             # 镜像构建文件
├── .dockerignore          # 镜像构建排除项
├── .gitignore             # Git 忽略项
└── README.md
```

## 在 Jenkins 中使用的下一步

1. 提交到 Git 仓库（GitLab / Gitee / GitHub）
2. 在 Jenkins 新建 Pipeline 任务，选择 `Pipeline script from SCM`
3. `Jenkinsfile` 中依次执行：拉代码 → 装依赖 → `pytest` → `docker build` → 推送镜像 → 部署
