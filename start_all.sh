#!/bin/bash

echo "========================================"
echo "   智能巡检系统 - 统一启动"
echo "========================================"
echo

# 检查虚拟环境
if [ -f "venv/bin/python" ]; then
    echo "使用虚拟环境: venv"
    venv/bin/python start_all.py
else
    echo "使用系统Python"
    python3 start_all.py
fi

