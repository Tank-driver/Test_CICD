#!/bin/bash
# 部署脚本：由 Jenkins 通过 SSH 调用
# 用法: ./deploy.sh <镜像名> <tag>
set -e

IMAGE_NAME=$1
IMAGE_TAG=$2

DEPLOY_DIR=/data/cicd-demo
cd "$DEPLOY_DIR"

if [ ! -f .env ]; then
  echo "错误：缺少 $DEPLOY_DIR/.env，请先参照 .env.example 创建" >&2
  exit 1
fi

# 只更新镜像名与版本，保留 SECRET_KEY
sed -i "s|^IMAGE=.*|IMAGE=${IMAGE_NAME}|" .env
sed -i "s|^TAG=.*|TAG=${IMAGE_TAG}|" .env

echo "==> 拉取镜像 ${IMAGE_NAME}:${IMAGE_TAG}"
docker compose pull web

echo "==> 启动服务"
docker compose up -d

echo "==> 等待容器健康"
for i in $(seq 1 30); do
  STATUS=$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' poker-web 2>/dev/null || echo unknown)
  if [ "$STATUS" = "healthy" ]; then
    echo "poker-web 已就绪（第 ${i} 次检查）"
    break
  fi
  if [ "$STATUS" = "unhealthy" ]; then
    echo "容器状态异常，最近日志：" >&2
    docker logs --tail 60 poker-web >&2
    exit 1
  fi
  sleep 2
done

docker image prune -f
echo "部署完成: ${IMAGE_NAME}:${IMAGE_TAG}"
