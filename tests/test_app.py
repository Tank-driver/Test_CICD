"""
接口与函数的单元测试。

运行方式：
    pytest -v
CI 中会使用 `pytest --junitxml=report.xml` 生成 JUnit 报告，供 Jenkins 收集展示。
"""

import pytest

# 从被测模块导入：纯函数 add 和 Flask 应用实例 app
from app import add, app


@pytest.fixture()
def client():
    """
    创建 Flask 测试客户端。

    fixture 会在每个测试用例执行前自动运行，结束后自动关闭，
    保证用例之间互不影响（不依赖真实端口，速度也快）。
    """
    # 开启测试模式（异常会直接抛出，便于定位问题）
    app.config.update(TESTING=True)
    # test_client() 返回的客户端可以直接发起 HTTP 请求，不会真正监听端口
    with app.test_client() as c:
        yield c


# ---------- 纯函数测试（不依赖 Web 框架） ----------

def test_add_positive():
    """正数相加。"""
    assert add(1, 2) == 3


def test_add_negative():
    """负数相加。"""
    assert add(-1, -2) == -3


def test_add_zero():
    """含 0 的情况，验证边界。"""
    assert add(0, 5) == 5


# ---------- 接口测试（通过测试客户端发请求） ----------

def test_index(client):
    """GET / 应返回 200，并带有服务名称。"""
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.get_json()["service"] == "cicd-demo"


def test_health(client):
    """健康检查接口应返回 {"status": "ok"}。"""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_add_api_ok(client):
    """正常计算：3 + 4 = 7。"""
    resp = client.post("/add", json={"a": 3, "b": 4})
    assert resp.status_code == 200
    assert resp.get_json()["result"] == 7


def test_add_api_missing_param(client):
    """缺少参数 b，应返回 400 并带错误信息。"""
    resp = client.post("/add", json={"a": 1})
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_add_api_wrong_type(client):
    """参数类型不是整数（字符串 "1"），应返回 400。"""
    resp = client.post("/add", json={"a": "1", "b": 2})
    assert resp.status_code == 400


def test_add_api_boolean_rejected(client):
    """布尔值属于 int 子类，应被显式拒绝，避免 True + 1 = 2 这类误判。"""
    resp = client.post("/add", json={"a": True, "b": 1})
    assert resp.status_code == 400


def test_add_api_not_json(client):
    """请求体不是 JSON 时，应返回 400 而不是 500。"""
    resp = client.post("/add", data="not-json", content_type="text/plain")
    assert resp.status_code == 400
