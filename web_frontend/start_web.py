"""
启动Web服务脚本
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import app, socketio, logger

if __name__ == '__main__':
    logger.info("="*60)
    logger.info("智能巡检Web服务启动")
    logger.info(f"访问地址: http://0.0.0.0:5000")
    logger.info("="*60)
    
    # 使用SocketIO运行
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=False,
        allow_unsafe_werkzeug=True
    )

