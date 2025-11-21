@echo off
chcp 65001 >nul
echo ========================================
echo 重启智能巡检系统所有服务
echo ========================================
echo.

echo [1/2] 正在重启API服务...
taskkill /F /IM bentoml.exe 2>nul
timeout /t 2 /nobreak >nul
cd api_server
start "API服务" cmd /k "call ..\venv\Scripts\activate && python start_server.py"
cd ..
echo ✅ API服务已重启
echo.

echo [2/2] 正在重启Web服务...
timeout /t 3 /nobreak >nul
cd web_frontend
start "Web服务" cmd /k "call ..\venv\Scripts\activate && python start_web.py"
cd ..
echo ✅ Web服务已重启
echo.

echo ========================================
echo 所有服务重启完成！
echo ========================================
echo.
echo 请等待5-10秒让服务完全启动
echo 然后访问: http://localhost:5000
echo.
pause

