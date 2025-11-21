@echo off
chcp 65001 >nul
echo ========================================
echo    智能巡检系统 - Web服务启动
echo ========================================
echo.

REM 激活虚拟环境
cd /d "%~dp0.."
call venv\Scripts\activate.bat

REM 检查Python是否可用
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Python未找到，请先安装Python
    pause
    exit /b 1
)

REM 检查依赖是否安装
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo [错误] Flask未安装，正在安装依赖...
    pip install -r requirements.txt
)

REM 切换到web_frontend目录
cd web_frontend

REM 启动服务
echo [启动] 正在启动Web服务...
echo [访问] http://localhost:5000
echo.
python start_web.py

pause

