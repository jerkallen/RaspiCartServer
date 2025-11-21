@echo off
REM 智能巡检系统 - BentoML API服务启动脚本 (Windows)

echo ================================================
echo 智能巡检系统 - BentoML API服务
echo ================================================
echo.

REM 激活虚拟环境
if exist "..\venv\Scripts\activate.bat" (
    echo 激活虚拟环境...
    call ..\venv\Scripts\activate.bat
) else (
    echo 警告: 未找到虚拟环境，使用系统Python
)

REM 切换到api_server目录
cd /d "%~dp0"

REM 运行启动脚本
python start_server.py serve

pause

