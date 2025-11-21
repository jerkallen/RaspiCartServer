#!/bin/bash
# 智能巡检系统 - BentoML API服务启动脚本 (Linux/Mac)

echo "================================================"
echo "智能巡检系统 - BentoML API服务"
echo "================================================"
echo

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 激活虚拟环境
if [ -f "$SCRIPT_DIR/../venv/bin/activate" ]; then
    echo "激活虚拟环境..."
    source "$SCRIPT_DIR/../venv/bin/activate"
else
    echo "警告: 未找到虚拟环境，使用系统Python"
fi

# 切换到api_server目录
cd "$SCRIPT_DIR"

# 运行启动脚本
python start_server.py serve

