#!/bin/bash
cd "$(dirname "$0")/src"

if [ ! -f ".venv/bin/python3" ]; then
    echo "正在创建虚拟环境..."
    python3 -m venv .venv || { echo "创建虚拟环境失败，请检查 Python3 是否已安装。"; read -r; exit 1; }
fi

source .venv/bin/activate
echo "正在检查依赖..."
pip install -q -r requirements.txt || { echo "安装依赖失败。"; read -r; exit 1; }

python window_app.py
