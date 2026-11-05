"""
CICD 演示项目：一个极简的 Flask HTTP 服务。

提供三个接口：
    GET  /          —— 返回服务名和版本，用于确认服务存活
    GET  /health    —— 健康检查，供容器编排（Docker/K8s）探活使用
    POST /add       —— 计算两个整数之和，用于演示带参数的接口

运行方式：
    python app.py
    # 或
    flask --app app run --host 0.0.0.0 --port 5000
"""

from flask import Flask, jsonify, request

# 创建 Flask 应用实例。
# __name__ 用于让 Flask 知道当前模块的位置，以便定位模板/静态文件目录。
app = Flask(__name__)


def add(a: int, b: int) -> int:
    """
    纯函数：返回两个整数之和。

    单独抽出来是为了：
    1. 单元测试可以直接测这个函数，不需要启动 HTTP 服务；
    2. 业务逻辑与 Web 框架解耦，将来换框架不用改这里。

    :param a: 第一个加数
    :param b: 第二个加数
    :return: 两数之和
    """
    return a + b


@app.get("/")
def index():
    """根路径：返回服务标识，方便浏览器直接访问确认服务已启动。"""
    return jsonify(
        service="cicd-demo",  # 服务名称
        version="1.0.0",      # 版本号，发布时可与镜像 tag 对应
        docs="/health, POST /add",
    )


@app.get("/health")
def health():
    """
    健康检查接口。

    容器平台（docker healthcheck / K8s livenessProbe）会周期性调用它：
    返回 200 表示进程正常，返回非 200 则容器会被重启。
    """
    return jsonify(status="ok")


@app.post("/add")
def add_api():
    """
    计算接口：接收 JSON {"a": 1, "b": 2}，返回 {"result": 3}。

    设计要点：
    1. 用 silent=True，请求体不是合法 JSON 时不抛异常，而是得到 None；
    2. 用 isinstance(x, int) 校验类型，避免字符串拼接等隐式错误；
    3. 参数错误统一返回 400，方便调用方区分「业务失败」和「服务异常」。
    """
    # 解析请求体；解析失败时返回空字典，避免 None 参与后续取值
    payload = request.get_json(silent=True) or {}

    # 取出两个参数（不存在时得到 None）
    a = payload.get("a")
    b = payload.get("b")

    # 类型校验：bool 在 Python 里是 int 的子类，需要额外排除 True/False
    if (
        not isinstance(a, int)
        or isinstance(a, bool)
        or not isinstance(b, int)
        or isinstance(b, bool)
    ):
        return jsonify(error="参数 a、b 必须是整数"), 400

    # 调用纯函数完成计算并返回结果
    return jsonify(result=add(a, b))


@app.route("/who", methods=["GET", "POST"])
def whom():
    return jsonify(message="你是帅哥")

if __name__ == "__main__":
    # 直接执行本文件时启动开发服务器。
    # host="0.0.0.0" 让容器外部可以访问（只写 127.0.0.1 容器外访问不到）。
    # debug=False：流水线/容器环境必须关闭，否则会暴露调试器和源码。
    app.run(host="0.0.0.0", port=5000, debug=False)
