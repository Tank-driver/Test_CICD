#!/bin/sh
# 容器启动入口：直接跑 gunicorn（游戏状态在内存中，无需初始化数据库）
set -e

echo "==> 启动单机德州扑克"
exec gunicorn \
    -b 0.0.0.0:5000 \
    -w 2 \
    --access-logfile - \
    --error-logfile - \
    wsgi:app
