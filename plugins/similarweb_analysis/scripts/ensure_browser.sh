#!/bin/bash
# 确保 dev-browser server 已启动
# 用法: bash ensure_browser.sh <DEV_BROWSER_DIR>

DEV_BROWSER_DIR="${1:?Usage: ensure_browser.sh <DEV_BROWSER_DIR>}"

# 检查 dev-browser server 是否在运行
if curl -s http://localhost:9222 > /dev/null 2>&1; then
  echo "dev-browser server is already running."
  exit 0
fi

echo "dev-browser server not detected. Starting..."
cd "$DEV_BROWSER_DIR" && bash server.sh &
SERVER_PID=$!

# 等待 server ready（最多 30 秒）
for i in $(seq 1 30); do
  if curl -s http://localhost:9222 > /dev/null 2>&1; then
    echo "dev-browser server is ready."
    exit 0
  fi
  sleep 1
done

echo "ERROR: dev-browser server failed to start within 30 seconds."
exit 1
