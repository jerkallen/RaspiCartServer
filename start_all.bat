@echo off
chcp 65001 >nul
echo ========================================
echo    智能巡检系统 - 统一启动
echo ========================================
echo.

REM 检查虚拟环境
if exist "venv\Scripts\python.exe" (
    echo 使用虚拟环境: venv
    venv\Scripts\python.exe start_all.py
) else (
    echo 使用系统Python
    python start_all.py
)

pause

