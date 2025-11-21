"""
数据库初始化脚本
用于创建SQLite数据库和所有必需的表
"""
import sqlite3
from pathlib import Path
from datetime import datetime


def get_db_path():
    """获取数据库文件路径"""
    # 脚本在 scripts/ 目录，数据库在 data/database/
    base_dir = Path(__file__).parent.parent
    db_dir = base_dir / "data" / "database"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / "inspection.db"


def create_tables(conn):
    """创建所有数据表"""
    cursor = conn.cursor()
    
    # 1. 任务记录表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT NOT NULL,
            task_type INTEGER NOT NULL,
            station_id INTEGER NOT NULL,
            image_path TEXT,
            result_data TEXT,
            status TEXT DEFAULT 'normal',
            confidence REAL,
            processing_time REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 创建索引
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_task_type 
        ON task_records(task_type)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_station_id 
        ON task_records(station_id)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_timestamp 
        ON task_records(timestamp)
    """)
    
    print("[OK] 创建表: task_records (任务记录表)")
    
    # 2. 任务队列表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT UNIQUE NOT NULL,
            station_id INTEGER NOT NULL,
            task_type INTEGER NOT NULL,
            priority TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'pending',
            params TEXT,
            assigned_at DATETIME,
            completed_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 创建索引
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_status 
        ON task_queue(status)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_station_task 
        ON task_queue(station_id, task_type)
    """)
    
    print("[OK] 创建表: task_queue (任务队列表)")
    
    # 3. 报警日志表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alert_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id INTEGER,
            alert_level TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            message TEXT,
            handled BOOLEAN DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (record_id) REFERENCES task_records(id)
        )
    """)
    
    # 创建索引
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_alert_level 
        ON alert_log(alert_level)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_handled 
        ON alert_log(handled)
    """)
    
    print("[OK] 创建表: alert_log (报警日志表)")
    
    # 4. 小车状态表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cart_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            online BOOLEAN DEFAULT 1,
            current_station INTEGER,
            mode TEXT DEFAULT 'idle',
            battery_level INTEGER,
            last_activity TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    print("[OK] 创建表: cart_status (小车状态表)")
    
    conn.commit()


def insert_initial_data(conn):
    """插入初始数据"""
    cursor = conn.cursor()
    
    # 检查是否已有数据
    cursor.execute("SELECT COUNT(*) FROM cart_status")
    count = cursor.fetchone()[0]
    
    if count == 0:
        # 插入初始小车状态
        cursor.execute("""
            INSERT INTO cart_status (online, current_station, mode, battery_level, last_activity)
            VALUES (0, 0, 'idle', 100, '等待连接')
        """)
        print("[OK] 插入初始小车状态数据")
    else:
        print("[OK] 小车状态数据已存在，跳过初始化")
    
    conn.commit()


def verify_tables(conn):
    """验证表是否创建成功"""
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' 
        ORDER BY name
    """)
    
    tables = cursor.fetchall()
    print("\n数据库中的表:")
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"  - {table_name}: {count} 条记录")
    
    return len(tables) >= 4


def init_database(interactive=True):
    """
    初始化数据库
    
    Args:
        interactive: 是否为交互模式（需要用户确认）
    """
    print("="*60)
    print("智能巡检系统 - 数据库初始化")
    print("="*60)
    
    db_path = get_db_path()
    print(f"\n数据库路径: {db_path}")
    
    # 检查数据库是否已存在
    db_exists = db_path.exists()
    if db_exists:
        print("[警告] 数据库文件已存在")
        if interactive:
            try:
                user_input = input("是否要重新初始化？这将保留现有数据但确保表结构正确 (y/n): ")
                if user_input.lower() != 'y':
                    print("取消初始化")
                    return False
            except EOFError:
                # 非交互模式，自动继续
                print("非交互模式，自动继续初始化...")
        else:
            print("自动继续初始化...")
    
    try:
        # 连接数据库（如果不存在会自动创建）
        conn = sqlite3.connect(str(db_path))
        print("[OK] 数据库连接成功")
        
        # 创建表
        print("\n创建数据表...")
        create_tables(conn)
        
        # 插入初始数据
        print("\n插入初始数据...")
        insert_initial_data(conn)
        
        # 验证表
        print("\n验证数据库...")
        if verify_tables(conn):
            print("\n[成功] 数据库初始化成功！")
            success = True
        else:
            print("\n[失败] 数据库验证失败，表数量不足")
            success = False
        
        # 关闭连接
        conn.close()
        
        print("="*60)
        return success
        
    except sqlite3.Error as e:
        print(f"\n[失败] 数据库错误: {e}")
        print("="*60)
        return False
    except Exception as e:
        print(f"\n[失败] 未知错误: {e}")
        print("="*60)
        return False


if __name__ == "__main__":
    import sys
    # 检查是否为非交互模式（如果有命令行参数--non-interactive）
    interactive = "--non-interactive" not in sys.argv
    success = init_database(interactive=interactive)
    exit(0 if success else 1)

