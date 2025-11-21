"""
清除数据库所有数据
删除所有表中的数据，但保留表结构
"""
import sys
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from scripts.db_manager import DatabaseManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


def clear_all_data(db_path=None):
    """
    清除数据库中的所有数据
    
    Args:
        db_path: 数据库文件路径，默认为 None（使用默认路径）
    
    Returns:
        dict: 包含各表删除记录数的字典
    """
    db = DatabaseManager(db_path)
    
    result = {}
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # 需要清除数据的表（按外键依赖顺序）
        tables = [
            'alert_log',      # 有外键依赖，先删除
            'task_records',   # 被 alert_log 引用
            'task_queue',     # 独立表
            'cart_status'     # 独立表
        ]
        
        for table in tables:
            cursor.execute(f"DELETE FROM {table}")
            count = cursor.rowcount
            result[table] = count
            logger.info(f"清除表 {table}: {count} 条记录")
        
        conn.commit()
    
    logger.info("="*60)
    logger.info("✅ 数据库数据清除完成!")
    logger.info("="*60)
    
    return result


if __name__ == "__main__":
    try:
        logger.info("="*60)
        logger.info("开始清除数据库所有数据")
        logger.info("="*60)
        
        result = clear_all_data()
        
        logger.info("\n清除结果:")
        total = 0
        for table, count in result.items():
            logger.info(f"  {table}: {count} 条")
            total += count
        
        logger.info(f"\n总计清除: {total} 条记录")
        
    except Exception as e:
        logger.error(f"❌ 清除失败: {e}")
        sys.exit(1)

