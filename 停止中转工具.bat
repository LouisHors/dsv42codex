@echo off
chcp 65001 >nul 2>&1
setlocal

set HOST=127.0.0.1
set PORT=9468

:: 检测服务是否在运行
curl -sf --max-time 1 http://%HOST%:%PORT%/health >nul 2>&1
if errorlevel 1 (
    echo 中转服务未运行（%HOST%:%PORT%）。
    exit /b 0
)

echo 检测到中转服务正在运行（%HOST%:%PORT%），正在停止...

:: 查找占用该端口的进程 PID
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PORT%" ^| findstr "LISTENING"') do set PID=%%a

if "%PID%"=="" (
    echo 未找到监听 %PORT% 的进程。
    exit /b 1
)

echo 进程 PID: %PID%
taskkill /PID %PID% >nul 2>&1

:: 等待进程退出
set /a COUNT=0
:waitloop
if %COUNT% GEQ 10 goto forcekill
tasklist /FI "PID eq %PID%" 2>nul | findstr "%PID%" >nul
if errorlevel 1 (
    echo 中转服务已停止。
    exit /b 0
)
set /a COUNT+=1
ping -n 2 127.0.0.1 >nul
goto waitloop

:forcekill
echo 正常停止超时，强制终止...
taskkill /F /PID %PID% >nul 2>&1
ping -n 2 127.0.0.1 >nul

tasklist /FI "PID eq %PID%" 2>nul | findstr "%PID%" >nul
if errorlevel 1 (
    echo 中转服务已强制停止。
) else (
    echo 无法停止进程 %PID%，请手动终止。
    exit /b 1
)
