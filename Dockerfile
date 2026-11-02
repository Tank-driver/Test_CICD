# 基础镜像：官方 Python 3.11 精简版，体积小、自带 pip
FROM python:3.11-slim

# 设置容器内的工作目录，后续 COPY/RUN/CMD 都在此目录下执行
WORKDIR /app

# 环境变量说明：
#   PYTHONDONTWRITEBYTECODE=1 —— 不生成 .pyc 缓存文件，保持镜像干净
#   PYTHONUNBUFFERED=1        —— 标准输出不缓冲，docker logs 能实时看到日志
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 先单独拷贝依赖清单，利用 Docker 分层缓存：
# 只要 requirements.txt 没变，重新构建时这层缓存可直接复用，不必重装依赖
COPY requirements.txt .

# 安装依赖：
#   --no-cache-dir 不保留 pip 缓存，减小镜像体积
#   -i 指定国内镜像源，加速下载（海外环境可删掉这一行）
RUN pip install --no-cache-dir -r requirements.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

# 拷贝项目源码（.dockerignore 中列出的文件不会被拷贝进来）
COPY . .

# 声明容器监听的端口（仅作文档用途，实际映射由 docker run -p 决定）
EXPOSE 5000

# 容器启动命令：以前台方式运行 Flask 应用
CMD ["python", "app.py"]
