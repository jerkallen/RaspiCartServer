"""
统一启动脚本 - 同时启动前端和后端服务
"""
import os
import sys
import subprocess
import signal
import time
import logging
from pathlib import Path

# 项目根目录
project_root = Path(__file__).parent

# 添加项目根目录到路径（用于导入 scripts 模块）
sys.path.insert(0, str(project_root))

# 子进程列表
processes = []

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def signal_handler(sig, frame):
    """处理Ctrl+C信号，优雅地关闭所有服务"""
    print("\n\n正在关闭所有服务...")
    for proc in processes:
        if proc.poll() is None:  # 进程还在运行
            proc.terminate()
    
    # 等待进程结束
    time.sleep(2)
    for proc in processes:
        if proc.poll() is None:
            proc.kill()
    
    print("所有服务已关闭")
    sys.exit(0)


def init_database():
    """初始化数据库（仅当数据库不存在时）"""
    db_path = project_root / "data" / "database" / "inspection.db"
    
    # 检查数据库文件是否存在
    if db_path.exists():
        logger.info(f"数据库已存在: {db_path}")
        return
    
    print("="*60)
    print("数据库不存在，正在初始化...")
    print("="*60)
    
    try:
        from scripts.db_manager import DatabaseManager
        
        # 创建数据库管理器（会自动创建表）
        db = DatabaseManager()
        logger.info("数据库初始化成功")
        
        # 检查表是否存在
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table'
                ORDER BY name
            """)
            tables = cursor.fetchall()
            
            logger.info(f"已创建数据表: {len(tables)} 个")
            for table in tables:
                logger.info(f"  - {table[0]}")
        
        print("="*60)
        print()
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        print("警告: 数据库初始化失败，但服务将继续启动")
        print("="*60)
        print()


def start_backend():
    """启动后端API服务"""
    print("="*60)
    print("正在启动后端API服务 (端口: 3000)...")
    print("="*60)
    
    backend_dir = project_root / "api_server"
    
    # Windows系统
    if sys.platform == "win32":
        proc = subprocess.Popen(
            [sys.executable, "start_server.py", "serve"],
            cwd=backend_dir,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        # Linux/Mac系统
        proc = subprocess.Popen(
            [sys.executable, "start_server.py", "serve"],
            cwd=backend_dir,
            preexec_fn=os.setsid
        )
    
    processes.append(proc)
    return proc


def start_frontend():
    """启动前端Web服务"""
    print("="*60)
    print("正在启动前端Web服务 (端口: 5000)...")
    print("="*60)
    
    frontend_dir = project_root / "web_frontend"
    
    # Windows系统
    if sys.platform == "win32":
        proc = subprocess.Popen(
            [sys.executable, "start_web.py"],
            cwd=frontend_dir,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        # Linux/Mac系统
        proc = subprocess.Popen(
            [sys.executable, "start_web.py"],
            cwd=frontend_dir,
            preexec_fn=os.setsid
        )
    
    processes.append(proc)
    return proc


def check_services():
    """检查服务是否正常运行"""
    for proc in processes:
        if proc.poll() is not None:
            print(f"❌ 服务进程 {proc.pid} 已退出")
            return False
    return True


def main():
    """主函数"""
    print("\n")
    print("*"*60)
    print("      智能巡检系统 - 统一启动脚本")
    print("*"*60)
    print("\n")
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    if sys.platform != "win32":
        signal.signal(signal.SIGTERM, signal_handler)
    
    # 初始化数据库
    init_database()
    
    # 启动后端服务
    backend_proc = start_backend()
    time.sleep(3)  # 等待后端启动
    
    # 启动前端服务
    frontend_proc = start_frontend()
    time.sleep(2)  # 等待前端启动
    
    print("\n")
    print("="*60)
    print("✓ 所有服务启动完成!")
    print("="*60)
    print()
    print("服务访问地址:")
    print(f"  - 前端Web界面: http://localhost:5000")
    print(f"  - 后端API服务: http://localhost:3000")
    print()
    print("按 Ctrl+C 停止所有服务")
    print("="*60)
    print()
    
    # 监控服务运行状态
    try:
        while True:
            if not check_services():
                print("❌ 检测到服务异常退出")
                break
            time.sleep(5)
    except KeyboardInterrupt:
        signal_handler(None, None)


if __name__ == "__main__":
    main()

