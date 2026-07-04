@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================
echo  lakejobai-job-radar ^| Web 控制台一键启动
echo ============================================
echo.

REM 获取当前目录
set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

REM 自动检测 Python
set "PYTHON_EXE="
for %%c in (py python3 python) do (
    for /f "tokens=*" %%v in ('%%c --version 2^>nul') do (
        echo %%v | findstr /R "Python 3\.\(1[0-9]\|[0-9][0-9]\)" >nul
        if !errorlevel! equ 0 (
            set "PYTHON_EXE=%%c"
            goto :found_python
        )
    )
)
:found_python

if "%PYTHON_EXE%"=="" (
    echo [ERROR] 未检测到 Python 3.10+
    echo 请安装 Python: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python: %PYTHON_EXE%
%PYTHON_EXE% --version
echo.

REM 检查依赖
echo [1/3] 检查依赖...
%PYTHON_EXE% -c "import fastapi, uvicorn, yaml, bs4, lxml, websockets, playwright" 2>nul
if errorlevel 1 (
    echo [..] 安装依赖中...
    %PYTHON_EXE% -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] 依赖安装失败
        pause
        exit /b 1
    )
    echo [OK] 依赖安装完成
) else (
    echo [OK] 依赖已就绪
)
echo.

REM 检查 Playwright 浏览器
echo [2/3] 检查 Playwright...
%PYTHON_EXE% -c "from playwright.sync_api import sync_playwright; p=sync_playwright().start(); p.firefox.launch(headless=True).close(); p.stop()" 2>nul
if errorlevel 1 (
    echo [..] 安装 Playwright Firefox 浏览器中...
    %PYTHON_EXE% -m playwright install firefox
    if errorlevel 1 (
        echo [WARN] Playwright 安装失败，可稍后手动安装
    ) else (
        echo [OK] Playwright 安装完成
    )
) else (
    echo [OK] Playwright 已就绪
)
echo.

REM 启动 Web 控制台
set "BOSS_PORT=8010"
echo [3/3] 启动 Web 控制台 (http://127.0.0.1:!BOSS_PORT!)...
start "" http://127.0.0.1:!BOSS_PORT!/

%PYTHON_EXE% boss_app.py --port !BOSS_PORT! --auto-start

echo.
echo 服务已停止。
pause
