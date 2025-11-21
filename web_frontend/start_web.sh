#!/bin/bash

echo "========================================"
echo "   智能巡检系统 - Web服务启动"
echo "========================================"
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 激活虚拟环境
cd "$PROJECT_ROOT"
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "[错误] 虚拟环境不存在，请先创建: python -m venv venv"
    exit 1
fi

# 检查依赖是否安装
python -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[错误] Flask未安装，正在安装依赖..."
    pip install -r requirements.txt
fi

# 切换到web_frontend目录
cd web_frontend

# 启动服务
echo "[启动] 正在启动Web服务..."
echo "[访问] http://localhost:5000"
echo ""
python start_web.py

