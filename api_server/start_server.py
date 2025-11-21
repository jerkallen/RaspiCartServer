"""
BentoML服务启动脚本
"""
import os
import sys
from pathlib import Path

# 添加当前目录到路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 确保必要的目录存在
def ensure_directories():
    """确保必要的目录存在"""
    dirs = [
        "../data/images",
        "../data/logs",
        "../data/database",
        "../data/config"
    ]
    
    for dir_path in dirs:
        path = current_dir / dir_path
        path.mkdir(parents=True, exist_ok=True)
        print(f"✓ 目录已创建/存在: {path}")


def check_environment():
    """检查环境变量"""
    from dotenv import load_dotenv
    
    # 尝试从项目根目录加载.env
    env_path = current_dir.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✓ 已加载环境变量: {env_path}")
    else:
        print(f"⚠ 未找到.env文件: {env_path}")
        print("  请复制 env.example 为 .env 并配置API密钥")
    
    # 检查关键环境变量
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("❌ 错误: 未设置 DASHSCOPE_API_KEY 环境变量")
        print("  请在 .env 文件中设置 DASHSCOPE_API_KEY")
        sys.exit(1)
    else:
        # 只显示前8位和后4位
        masked_key = f"{api_key[:8]}...{api_key[-4:]}"
        print(f"✓ DASHSCOPE_API_KEY: {masked_key}")


def main():
    """主函数"""
    print("="*60)
    print("智能巡检系统 - BentoML API服务")
    print("="*60)
    print()
    
    # 确保目录存在
    print("1. 检查目录结构...")
    ensure_directories()
    print()
    
    # 检查环境
    print("2. 检查环境配置...")
    check_environment()
    print()
    
    print("3. 启动BentoML服务...")
    print()
    print("提示: 使用以下命令启动服务:")
    print(f"  cd {current_dir}")
    print("  bentoml serve service.py:InspectionAPIService --port 3000")
    print()
    print("或者直接运行:")
    print("  python start_server.py serve")
    print()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        # 如果传入serve参数，执行检查后启动服务
        main()
        
        # 使用bentoml命令启动
        import subprocess
        os.chdir(current_dir)
        subprocess.run([
            "bentoml", "serve", 
            "service.py:InspectionAPIService",
            "--port", "3000",
            "--host", "0.0.0.0"
        ])
    else:
        # 否则只显示信息
        main()

