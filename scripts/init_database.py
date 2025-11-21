"""
数据库初始化脚本 - 智能巡检系统
用于初始化数据库和创建示例数据
"""
import sys
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.db_manager import DatabaseManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


def init_database(create_sample_data: bool = False):
    """
    初始化数据库
    
    Args:
        create_sample_data: 是否创建示例数据
    """
    logger.info("="*60)
    logger.info("开始初始化数据库")
    logger.info("="*60)
    
    try:
        # 创建数据库管理器（会自动创建表）
        db = DatabaseManager()
        logger.info("✅ 数据库表创建成功")
        
        # 检查表是否存在
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table'
                ORDER BY name
            """)
            tables = cursor.fetchall()
            
            logger.info(f"\n当前数据表 ({len(tables)} 个):")
            for table in tables:
                logger.info(f"  - {table[0]}")
                
                # 显示每个表的列信息
                cursor.execute(f"PRAGMA table_info({table[0]})")
                columns = cursor.fetchall()
                logger.info(f"    字段 ({len(columns)} 个): {', '.join([col[1] for col in columns])}")
        
        # 创建示例数据（如果需要）
        if create_sample_data:
            logger.info("\n创建示例数据...")
            create_sample_tasks(db)
        
        logger.info("\n" + "="*60)
        logger.info("✅ 数据库初始化完成!")
        logger.info("="*60)
        
        return db
        
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")
        raise


def create_sample_tasks(db: DatabaseManager):
    """
    创建示例任务数据
    
    Args:
        db: 数据库管理器
    """
    import uuid
    
    logger.info("\n添加示例任务到队列...")
    
    # 示例任务配置
    sample_tasks = [
        {
            "station_id": 1,
            "task_type": 1,
            "params": {
                "camera_angle": 30,
                "description": "1号站气压表读数"
            }
        },
        {
            "station_id": 3,
            "task_type": 1,
            "params": {
                "camera_angle": 30,
                "description": "3号站气压表读数"
            }
        },
        {
            "station_id": 5,
            "task_type": 2,
            "params": {
                "description": "5号站温度检测"
            }
        },
        {
            "station_id": 7,
            "task_type": 3,
            "params": {
                "description": "7号站烟雾监测A"
            }
        },
        {
            "station_id": 9,
            "task_type": 4,
            "params": {
                "description": "9号站烟雾监测B"
            }
        }
    ]
    
    # 添加任务到队列
    for task_config in sample_tasks:
        task_id = db.add_task_to_queue(**task_config)
        description = task_config.get('params', {}).get('description', '未命名任务')
        logger.info(f"  ✓ 添加任务: {description} (ID: {task_id[:8]}...)")
    
    logger.info(f"✅ 成功添加 {len(sample_tasks)} 个示例任务")
    
    # 显示当前队列
    pending_tasks = db.get_pending_tasks()
    logger.info(f"\n当前待执行任务: {len(pending_tasks)} 个")
    for task in pending_tasks:
        logger.info(f"  - 站点{task['station_id']} | 类型{task['task_type']}")


def reset_database():
    """
    重置数据库（删除所有数据）
    
    警告：此操作会删除所有数据！
    """
    logger.warning("="*60)
    logger.warning("⚠️  警告: 即将重置数据库，所有数据将被删除!")
    logger.warning("="*60)
    
    response = input("\n确认要重置数据库吗? (yes/no): ").strip().lower()
    
    if response != 'yes':
        logger.info("操作已取消")
        return
    
    try:
        db = DatabaseManager()
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 删除所有表
            tables = ['task_records', 'task_queue', 'alert_log', 'cart_status']
            for table in tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
                logger.info(f"  ✓ 删除表: {table}")
            
            conn.commit()
        
        logger.info("✅ 数据库已重置")
        logger.info("正在重新创建表...")
        
        # 重新初始化
        init_database()
        
    except Exception as e:
        logger.error(f"❌ 重置失败: {e}")
        raise


def show_statistics(db: DatabaseManager):
    """
    显示数据库统计信息
    
    Args:
        db: 数据库管理器
    """
    logger.info("\n" + "="*60)
    logger.info("数据库统计信息")
    logger.info("="*60)
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # 任务记录统计
        cursor.execute("SELECT COUNT(*) FROM task_records")
        record_count = cursor.fetchone()[0]
        logger.info(f"\n任务记录总数: {record_count}")
        
        if record_count > 0:
            cursor.execute("""
                SELECT task_type, COUNT(*) as count 
                FROM task_records 
                GROUP BY task_type
                ORDER BY task_type
            """)
            for row in cursor.fetchall():
                logger.info(f"  - 任务类型 {row[0]}: {row[1]} 条")
        
        # 任务队列统计
        cursor.execute("SELECT COUNT(*) FROM task_queue")
        queue_count = cursor.fetchone()[0]
        logger.info(f"\n任务队列总数: {queue_count}")
        
        if queue_count > 0:
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM task_queue 
                GROUP BY status
            """)
            for row in cursor.fetchall():
                logger.info(f"  - {row[0]}: {row[1]} 条")
        
        # 报警日志统计
        cursor.execute("SELECT COUNT(*) FROM alert_log")
        alert_count = cursor.fetchone()[0]
        logger.info(f"\n报警日志总数: {alert_count}")
        
        if alert_count > 0:
            cursor.execute("""
                SELECT alert_level, COUNT(*) as count 
                FROM alert_log 
                GROUP BY alert_level
            """)
            for row in cursor.fetchall():
                logger.info(f"  - {row[0]}: {row[1]} 条")
        
        # 小车状态记录
        cursor.execute("SELECT COUNT(*) FROM cart_status")
        status_count = cursor.fetchone()[0]
        logger.info(f"\n小车状态记录: {status_count} 条")
        
        # 最新状态
        latest_status = db.get_latest_cart_status()
        if latest_status:
            logger.info(f"  - 最新状态: {'在线' if latest_status['online'] else '离线'}")
            logger.info(f"  - 当前站点: {latest_status.get('current_station', 'N/A')}")
            logger.info(f"  - 运行模式: {latest_status.get('mode', 'N/A')}")
            logger.info(f"  - 电池电量: {latest_status.get('battery_level', 'N/A')}%")
    
    logger.info("\n" + "="*60)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='数据库初始化工具')
    parser.add_argument(
        '--sample',
        action='store_true',
        help='创建示例数据'
    )
    parser.add_argument(
        '--reset',
        action='store_true',
        help='重置数据库（删除所有数据）'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='显示数据库统计信息'
    )
    
    args = parser.parse_args()
    
    try:
        if args.reset:
            # 重置数据库
            reset_database()
        elif args.stats:
            # 显示统计信息
            db = DatabaseManager()
            show_statistics(db)
        else:
            # 初始化数据库
            init_database(create_sample_data=args.sample)
            
            if args.sample:
                # 显示统计
                db = DatabaseManager()
                show_statistics(db)
        
    except Exception as e:
        logger.error(f"执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

