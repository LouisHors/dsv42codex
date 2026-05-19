@echo off
chcp 65001 >nul 2>&1
setlocal
cd /d "%~dp0src"

if not exist ".venv\Scripts\python.exe" (
    echo 正在创建虚拟环境...
    python -m venv .venv
    if errorlevel 1 (
        echo 创建虚拟环境失败，请检查 Python 是否已安装。
        pause
        exit /b 1
    )
)

echo 正在检查依赖...
.venv\Scripts\python.exe -m pip install -q -r requirements.txt
if errorlevel 1 (
    echo 安装依赖失败。
    pause
    exit /b 1
)

start "" ".venv\Scripts\pythonw.exe" "%~dp0src\window_app.py"
