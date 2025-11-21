"""
数据库管理器 - 智能巡检系统
负责SQLite数据库的连接、操作和管理
"""
import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库管理器类"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径，默认为 data/database/inspection.db
        """
        if db_path is None:
            # 默认路径
            project_root = Path(__file__).parent.parent
            db_path = project_root / "data" / "database" / "inspection.db"
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"数据库路径: {self.db_path}")
        
        # 确保数据库表存在
        self._ensure_tables()
    
    @contextmanager
    def get_connection(self):
        """
        获取数据库连接的上下文管理器
        
        Yields:
            sqlite3.Connection: 数据库连接
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # 使用Row工厂，可以通过列名访问
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            conn.close()
    
    def _ensure_tables(self):
        """确保所有数据表存在"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 创建任务记录表
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
            
            # 创建任务队列表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS task_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT UNIQUE NOT NULL,
                    station_id INTEGER NOT NULL,
                    task_type INTEGER NOT NULL,
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
            
            # 创建报警日志表
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
            
            # 创建小车状态表
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
            
            conn.commit()
            logger.info("数据库表检查完成")
    
    # ==================== 任务记录相关 ====================
    
    def add_task_record(
        self,
        task_id: str,
        task_type: int,
        station_id: int,
        result_data: Dict[str, Any],
        image_path: Optional[str] = None,
        status: str = "normal",
        confidence: Optional[float] = None,
        processing_time: Optional[float] = None
    ) -> int:
        """
        添加任务记录
        
        Args:
            task_id: 任务ID
            task_type: 任务类型
            station_id: 站点ID
            result_data: 结果数据（字典）
            image_path: 图片路径
            status: 状态（normal/warning/danger）
            confidence: 置信度
            processing_time: 处理时间
        
        Returns:
            记录ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO task_records 
                (task_id, task_type, station_id, image_path, result_data, 
                 status, confidence, processing_time, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task_id,
                task_type,
                station_id,
                image_path,
                json.dumps(result_data, ensure_ascii=False),
                status,
                confidence,
                processing_time,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            
            record_id = cursor.lastrowid
            logger.info(f"添加任务记录: ID={record_id}, 任务类型={task_type}, 站点={station_id}")
            return record_id
    
    def get_task_records(
        self,
        task_type: Optional[int] = None,
        station_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        查询任务记录
        
        Args:
            task_type: 任务类型过滤
            station_id: 站点ID过滤
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回条数
            offset: 偏移量
        
        Returns:
            任务记录列表
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM task_records WHERE 1=1"
            params = []
            
            if task_type is not None:
                query += " AND task_type = ?"
                params.append(task_type)
            
            if station_id is not None:
                query += " AND station_id = ?"
                params.append(station_id)
            
            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date)
            
            query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            records = []
            for row in rows:
                record = dict(row)
                # 解析JSON字段
                if record.get('result_data'):
                    try:
                        record['result_data'] = json.loads(record['result_data'])
                    except json.JSONDecodeError:
                        pass
                records.append(record)
            
            return records
    
    def get_latest_record_by_station(
        self,
        station_id: int,
        task_type: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        获取指定站点的最新记录
        
        Args:
            station_id: 站点ID
            task_type: 任务类型（可选）
        
        Returns:
            最新记录或None
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM task_records WHERE station_id = ?"
            params = [station_id]
            
            if task_type is not None:
                query += " AND task_type = ?"
                params.append(task_type)
            
            query += " ORDER BY timestamp DESC LIMIT 1"
            
            cursor.execute(query, params)
            row = cursor.fetchone()
            
            if row:
                record = dict(row)
                if record.get('result_data'):
                    try:
                        record['result_data'] = json.loads(record['result_data'])
                    except json.JSONDecodeError:
                        pass
                return record
            
            return None
    
    def update_task_record(
        self,
        record_id: int,
        result_data: Optional[Dict[str, Any]] = None,
        image_path: Optional[str] = None,
        status: Optional[str] = None,
        confidence: Optional[float] = None,
        processing_time: Optional[float] = None
    ) -> bool:
        """
        更新任务记录
        
        Args:
            record_id: 记录ID
            result_data: 结果数据（字典）
            image_path: 图片路径
            status: 状态（normal/warning/danger/processing/failed）
            confidence: 置信度
            processing_time: 处理时间
        
        Returns:
            是否更新成功
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 构建更新语句
            updates = []
            params = []
            
            if result_data is not None:
                updates.append("result_data = ?")
                params.append(json.dumps(result_data, ensure_ascii=False))
            
            if image_path is not None:
                updates.append("image_path = ?")
                params.append(image_path)
            
            if status is not None:
                updates.append("status = ?")
                params.append(status)
            
            if confidence is not None:
                updates.append("confidence = ?")
                params.append(confidence)
            
            if processing_time is not None:
                updates.append("processing_time = ?")
                params.append(processing_time)
            
            if not updates:
                logger.warning(f"更新任务记录时没有提供任何字段: record_id={record_id}")
                return False
            
            # 添加记录ID到参数
            params.append(record_id)
            
            query = f"UPDATE task_records SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            
            updated = cursor.rowcount > 0
            if updated:
                logger.info(f"更新任务记录成功: record_id={record_id}")
            else:
                logger.warning(f"更新任务记录失败（记录不存在）: record_id={record_id}")
            
            return updated
    
    def get_statistics(
        self,
        task_type: Optional[int] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        获取统计信息
        
        Args:
            task_type: 任务类型
            days: 统计天数
        
        Returns:
            统计信息字典
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d 00:00:00")
            
            query = """
                SELECT 
                    COUNT(*) as total_count,
                    COUNT(CASE WHEN status = 'normal' THEN 1 END) as normal_count,
                    COUNT(CASE WHEN status = 'warning' THEN 1 END) as warning_count,
                    COUNT(CASE WHEN status = 'danger' THEN 1 END) as danger_count,
                    AVG(confidence) as avg_confidence,
                    AVG(processing_time) as avg_processing_time
                FROM task_records
                WHERE timestamp >= ?
            """
            params = [start_date]
            
            if task_type is not None:
                query += " AND task_type = ?"
                params.append(task_type)
            
            cursor.execute(query, params)
            row = cursor.fetchone()
            
            return dict(row) if row else {}
    
    # ==================== 任务队列相关 ====================
    
    def add_task_to_queue(
        self,
        station_id: int,
        task_type: int,
        params: Optional[Dict[str, Any]] = None,
        task_id: Optional[str] = None
    ) -> str:
        """
        添加任务到队列
        
        Args:
            station_id: 站点ID
            task_type: 任务类型
            params: 任务参数
            task_id: 任务ID（可选，不提供则自动生成）
        
        Returns:
            任务ID
        """
        if task_id is None:
            task_id = str(uuid.uuid4())
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO task_queue 
                (task_id, station_id, task_type, status, params)
                VALUES (?, ?, ?, 'pending', ?)
            """, (
                task_id,
                station_id,
                task_type,
                json.dumps(params, ensure_ascii=False) if params else None
            ))
            
            logger.info(f"添加任务到队列: {task_id}, 站点={station_id}, 类型={task_type}")
            return task_id
    
    def get_pending_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取待执行任务列表
        
        Args:
            limit: 返回条数
        
        Returns:
            任务列表
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM task_queue 
                WHERE status = 'pending'
                ORDER BY created_at ASC
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            
            tasks = []
            for row in rows:
                task = dict(row)
                if task.get('params'):
                    try:
                        task['params'] = json.loads(task['params'])
                    except json.JSONDecodeError:
                        pass
                tasks.append(task)
            
            return tasks
    
    def update_task_status(
        self,
        task_id: str,
        status: str,
        assigned_at: Optional[str] = None,
        completed_at: Optional[str] = None
    ) -> bool:
        """
        更新任务状态
        
        Args:
            task_id: 任务ID
            status: 新状态（pending/assigned/completed/failed）
            assigned_at: 分配时间
            completed_at: 完成时间
        
        Returns:
            是否更新成功
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE task_queue 
                SET status = ?, assigned_at = ?, completed_at = ?
                WHERE task_id = ?
            """, (status, assigned_at, completed_at, task_id))
            
            success = cursor.rowcount > 0
            if success:
                logger.info(f"更新任务状态: {task_id} -> {status}")
            return success
    
    def delete_task_from_queue(self, task_id: str) -> bool:
        """
        从队列中删除任务
        
        Args:
            task_id: 任务ID
        
        Returns:
            是否删除成功
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM task_queue WHERE task_id = ?", (task_id,))
            
            success = cursor.rowcount > 0
            if success:
                logger.info(f"删除任务: {task_id}")
            return success
    
    def delete_task(self, task_id: str) -> bool:
        """
        删除任务（别名方法）
        
        Args:
            task_id: 任务ID
        
        Returns:
            是否删除成功
        """
        return self.delete_task_from_queue(task_id)
    
    def clear_completed_tasks(self, days: int = 1) -> int:
        """
        清理已完成的任务
        
        Args:
            days: 清理N天前的任务
        
        Returns:
            删除的任务数量
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
            
            cursor.execute("""
                DELETE FROM task_queue 
                WHERE status IN ('completed', 'failed') 
                AND completed_at < ?
            """, (cutoff_date,))
            
            count = cursor.rowcount
            logger.info(f"清理已完成任务: {count} 条")
            return count
    
    # ==================== 报警日志相关 ====================
    
    def add_alert(
        self,
        alert_level: str,
        alert_type: str,
        message: str,
        record_id: Optional[int] = None
    ) -> int:
        """
        添加报警日志
        
        Args:
            alert_level: 报警级别（warning/danger）
            alert_type: 报警类型
            message: 报警消息
            record_id: 关联的任务记录ID
        
        Returns:
            报警日志ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO alert_log 
                (record_id, alert_level, alert_type, message)
                VALUES (?, ?, ?, ?)
            """, (record_id, alert_level, alert_type, message))
            
            alert_id = cursor.lastrowid
            logger.info(f"添加报警日志: ID={alert_id}, 级别={alert_level}")
            return alert_id
    
    def get_unhandled_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取未处理的报警
        
        Args:
            limit: 返回条数
        
        Returns:
            报警列表
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM alert_log 
                WHERE handled = 0
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def mark_alert_handled(self, alert_id: int) -> bool:
        """
        标记报警为已处理
        
        Args:
            alert_id: 报警ID
        
        Returns:
            是否更新成功
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE alert_log 
                SET handled = 1
                WHERE id = ?
            """, (alert_id,))
            
            return cursor.rowcount > 0
    
    # ==================== 小车状态相关 ====================
    
    def update_cart_status(
        self,
        online: bool = True,
        current_station: Optional[int] = None,
        mode: str = "idle",
        battery_level: Optional[int] = None,
        last_activity: Optional[str] = None
    ) -> int:
        """
        更新小车状态
        
        Args:
            online: 是否在线
            current_station: 当前站点
            mode: 运行模式
            battery_level: 电池电量
            last_activity: 最近活动
        
        Returns:
            状态记录ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO cart_status 
                (online, current_station, mode, battery_level, last_activity)
                VALUES (?, ?, ?, ?, ?)
            """, (online, current_station, mode, battery_level, last_activity))
            
            return cursor.lastrowid
    
    def get_latest_cart_status(self) -> Optional[Dict[str, Any]]:
        """
        获取最新的小车状态
        
        Returns:
            状态字典或None
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM cart_status 
                ORDER BY timestamp DESC 
                LIMIT 1
            """)
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_cart_status(self) -> Optional[Dict[str, Any]]:
        """
        获取最新的小车状态（别名方法）
        
        Returns:
            状态字典或None
        """
        return self.get_latest_cart_status()
    
    # ==================== 数据清理相关 ====================
    
    def cleanup_old_records(self, days: int = 90) -> int:
        """
        清理旧的任务记录
        
        Args:
            days: 保留天数
        
        Returns:
            删除的记录数量
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
            
            cursor.execute("""
                DELETE FROM task_records 
                WHERE created_at < ?
            """, (cutoff_date,))
            
            count = cursor.rowcount
            logger.info(f"清理旧记录: {count} 条")
            return count
    
    def vacuum_database(self):
        """优化数据库（执行VACUUM）"""
        with self.get_connection() as conn:
            conn.execute("VACUUM")
            logger.info("数据库优化完成")


# 为了兼容导入
import uuid

if __name__ == "__main__":
    # 简单测试
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    try:
        db = DatabaseManager()
        logger.info("数据库管理器初始化成功")
        
        # 测试添加任务记录
        task_id = "test-" + str(uuid.uuid4())
        record_id = db.add_task_record(
            task_id=task_id,
            task_type=1,
            station_id=1,
            result_data={"value": 1.5, "unit": "MPa"},
            status="normal",
            confidence=0.95
        )
        logger.info(f"添加任务记录成功: ID={record_id}")
        
        # 测试查询
        records = db.get_task_records(limit=5)
        logger.info(f"查询任务记录: {len(records)} 条")
        
        # 测试添加任务队列
        queue_task_id = db.add_task_to_queue(
            station_id=1,
            task_type=1
        )
        logger.info(f"添加任务到队列: {queue_task_id}")
        
        # 测试获取待执行任务
        pending = db.get_pending_tasks()
        logger.info(f"待执行任务: {len(pending)} 条")
        
        logger.info("数据库测试完成!")
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        raise

