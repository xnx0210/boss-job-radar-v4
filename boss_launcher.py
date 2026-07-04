#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lakejobai-job-radar -- 一键启动器 (Python + PyInstaller)
自动检测 Python、安装依赖、启动 Web 控制台并打开浏览器
"""

import os
import sys
import subprocess
import webbrowser
import time
import re
from pathlib import Path

# ---- 获取自身所在目录（PyInstaller 打包后就是 EXE 所在目录） ----
if getattr(sys, 'frozen', False):
    APP_DIR = Path(sys.executable).parent.resolve()
else:
    APP_DIR = Path(__file__).parent.resolve()

os.chdir(APP_DIR)

BOSS_PORT = 8010

# ---- 纯 ASCII 颜色（兼容 GBK 控制台） ----


def colorize(text, code):
    return f'\033[{code}m{text}\033[0m'


def log_step(step, msg):
    print(f'  [{step}] {msg}')


def log_ok(*args):
    print(f'  {colorize("[OK]", 32)} {" ".join(args)}')


def log_err(*args):
    print(f'  {colorize("[FAIL]", 31)} {" ".join(args)}')


def log_warn(*args):
    print(f'  {colorize("[WARN]", 33)} {" ".join(args)}')


def banner(text, color=35):
    return colorize(text, color)


# ---- 核心函数 ----


def find_python():
    candidates = ['py', 'python3', 'python']
    for cmd in candidates:
        try:
            result = subprocess.run(
                [cmd, '--version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                ver = (result.stdout.strip() or result.stderr.strip())
                m = re.match(r'Python (\d+)\.(\d+)', ver)
                if m:
                    major, minor = int(m.group(1)), int(m.group(2))
                    if major > 3 or (major == 3 and minor >= 10):
                        return cmd, ver
        except (subprocess.TimeoutExpired, FileNotFoundError):
            continue
    return None, None


def check_deps(python_cmd):
    result = subprocess.run(
        [python_cmd, '-c',
         'import fastapi, uvicorn, yaml, bs4, lxml, websockets, playwright'],
        capture_output=True, text=True, timeout=30
    )
    return result.returncode == 0


def install_deps(python_cmd):
    return subprocess.run(
        [python_cmd, '-m', 'pip', 'install', '-r', 'requirements.txt'],
        cwd=APP_DIR
    ).returncode == 0


def check_playwright(python_cmd):
    code = subprocess.run(
        [python_cmd, '-c',
         'from playwright.sync_api import sync_playwright; '
         'p=sync_playwright().start(); '
         'f=p.firefox.launch(headless=True); f.close(); p.stop()'],
        capture_output=True, text=True, timeout=30
    ).returncode
    return code == 0


def install_playwright(python_cmd):
    return subprocess.run(
        [python_cmd, '-m', 'playwright', 'install', 'firefox']
    ).returncode == 0


# ---- 主流程 ----


def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(banner('''
+=========================================+
|   lakejobai-job-radar                   |
|   BOSS ZhiPin Smart Assistant - Web     |
+=========================================+
''', 35))

    # 1. 检查项目文件
    log_step('1/5', 'Checking project files...')
    required = ['boss_app.py', 'requirements.txt']
    missing = [f for f in required if not (APP_DIR / f).exists()]
    if missing:
        log_err('Missing required files:', ', '.join(missing))
        print(colorize(
            'Please place this program in the lakejobai-job-radar project root directory', 33))
        time.sleep(3)
        sys.exit(1)
    log_ok('Project files complete')

    # 2. 查找 Python
    log_step('2/5', 'Detecting Python...')
    python_cmd, version = find_python()
    if not python_cmd:
        log_err('Python 3.10+ not found')
        print(colorize('Please install Python: https://www.python.org/downloads/', 33))
        time.sleep(3)
        sys.exit(1)
    log_ok(f'Found Python: {version}')

    # 3. 安装依赖
    log_step('3/5', 'Checking Python dependencies...')
    if check_deps(python_cmd):
        log_ok('Python dependencies already installed')
    else:
        log_warn('Installing dependencies (pip install)...')
        if install_deps(python_cmd):
            log_ok('Python dependencies installed')
        else:
            log_err('Dependency installation failed')
            time.sleep(3)
            sys.exit(1)

    # 4. 检查 Playwright
    log_step('4/5', 'Checking Playwright browser...')
    if check_playwright(python_cmd):
        log_ok('Playwright browser ready')
    else:
        log_warn('Installing Playwright Firefox (first download may be slow)...')
        if install_playwright(python_cmd):
            log_ok('Playwright Firefox installed')
        else:
            log_warn('Playwright install failed, you can manually run: '
                     f'{python_cmd} -m playwright install firefox')

    # 5. 启动服务
    log_step('5/5', 'Starting Web console...')

    print(banner(f'''
+=========================================+
|  Ready!                                 |
|                                         |
|  Browser opened -> http://127.0.0.1:{BOSS_PORT}  |
|                                         |
|  First use: Settings -> Start Browser   |
|           -> Scan QR to login BOSS      |
|                                         |
|  Press Ctrl+C to stop the server        |
+=========================================+
''', 32))

    # 打开浏览器
    webbrowser.open(f'http://127.0.0.1:{BOSS_PORT}/')

    # 启动 Python 服务
    proc = subprocess.run(
        [python_cmd, 'boss_app.py', '--port', str(BOSS_PORT), '--auto-start'],
        cwd=APP_DIR
    )

    print(colorize(f'\nServer stopped (exit code: {proc.returncode}).', 90))
    time.sleep(2)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(colorize('\n\nInterrupted by user.', 33))
        time.sleep(1)
    except Exception as e:
        print(colorize(f'\nStartup failed: {e}', 31))
        time.sleep(3)
