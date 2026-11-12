# 基础镜像：走国内加速源（daocloud），避免直连 Docker Hub 卡住
# 如果哪天这个源不可用，可换回 python:3.11-slim 并在构建前先 docker pull
FROM docker.m.daocloud.io/library/python:3.11-slim

WORKDIR /app

# 不生成 .pyc、日志实时输出
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 先装依赖，利用层缓存
# --retries / --timeout：网络抖动时快速失败并重试，而不是无限挂起
COPY requirements.txt .
RUN pip install --no-cache-dir \
      --retries 3 --timeout 30 \
      -r requirements.txt \
      -i https://pypi.tuna.tsinghua.edu.cn/simple

# 再拷源码
COPY . .

RUN chmod +x docker-entrypoint.sh
ENTRYPOINT ["./docker-entrypoint.sh"]

EXPOSE 5000
