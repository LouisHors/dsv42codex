#!/bin/bash
# 检测本地中转服务是否在运行，如果正在运行则停止

HOST="127.0.0.1"
PORT=9468
HEALTH_URL="http://${HOST}:${PORT}/health"

# 检测服务是否在运行
if ! curl -sf --max-time 1 "${HEALTH_URL}" > /dev/null 2>&1; then
    echo "中转服务未运行（${HOST}:${PORT}）。"
    exit 0
fi

echo "检测到中转服务正在运行（${HOST}:${PORT}），正在停止..."

# 查找占用该端口的进程 PID
PID=$(lsof -ti :${PORT} -sTCP:LISTEN 2>/dev/null)

if [ -z "${PID}" ]; then
    echo "未找到监听 ${PORT} 的进程。"
    exit 1
fi

echo "进程 PID: ${PID}"
kill ${PID} 2>/dev/null

# 等待进程退出
for i in $(seq 1 10); do
    if ! kill -0 ${PID} 2>/dev/null; then
        echo "中转服务已停止。"
        exit 0
    fi
    sleep 0.5
done

# 超时后强制终止
echo "正常停止超时，强制终止..."
kill -9 ${PID} 2>/dev/null
sleep 0.5

if ! kill -0 ${PID} 2>/dev/null; then
    echo "中转服务已强制停止。"
else
    echo "无法停止进程 ${PID}，请手动终止。"
    exit 1
fi
