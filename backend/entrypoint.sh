#!/usr/bin/env bash
# SightEcho backend entrypoint
set -e

echo "[entrypoint] 等待依赖就绪..."
# 简易 wait：mysql/redis
for i in $(seq 1 30); do
  if python -c "import socket,sys; s=socket.socket(); s.settimeout(2); s.connect(('${MYSQL_HOST:-mysql}', ${MYSQL_PORT:-3306})); s.close()" 2>/dev/null; then
    echo "[entrypoint] mysql ok"
    break
  fi
  sleep 1
done

# 数据库迁移（如已建表则跳过）
echo "[entrypoint] 运行 alembic 迁移..."
alembic upgrade head || echo "[entrypoint] alembic 迁移失败（首次启动可忽略）"

# 启动 uvicorn
echo "[entrypoint] 启动 uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
