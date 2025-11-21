"""
数据库管理模块
提供数据库操作的封装接口
"""
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
from contextlib import contextmanager


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径，默认使用标准路径
        """
        if db_path is None:
            base_dir = Path(__file__).parent.parent
            db_path = base_dir / "data" / "database" / "inspection.db"
        
        self.db_path = Path(db_path)
        
        if not self.db_path.exists():
            raise FileNotFoundError(
                f"数据库文件不存在: {self.db_path}\n"
                f"请先运行 python scripts/init_database.py 初始化数据库"
            )
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接（上下文管理器）"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # 支持字典式访问
        try:
            yield conn
        finally:
            conn.close()
    
    # ==================== 任务记录相关 ====================
    
    def add_task_record(
        self,
        task_id: str,
        task_type: int,
        station_id: int,
        image_path: str,
        result_data: Dict[str, Any],
        status: str = "normal",
        confidence: Optional[float] = None,
        processing_time: Optional[float] = None
    ) -> int:
        """
        添加任务记录
        
        Args:
            task_id: 任务ID
            task_type: 任务类型（1-4）
            station_id: 站点ID
            image_path: 图片路径
            result_data: 结果数据（字典）
            status: 状态（normal/warning/danger）
            confidence: 置信度
            processing_time: 处理时间
        
        Returns:
            int: 记录ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO task_records 
                (task_id, task_type, station_id, image_path, result_data, 
                 status, confidence, processing_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task_id,
                task_type,
                station_id,
                image_path,
                json.dumps(result_data, ensure_ascii=False),
                status,
                confidence,
                processing_time
            ))
            conn.commit()
            return cursor.lastrowid
    
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
            start_date: 开始日期（YYYY-MM-DD）
            end_date: 结束日期（YYYY-MM-DD）
            limit: 返回条数
            offset: 偏移量
        
        Returns:
            List[Dict]: 记录列表
        """
        conditions = []
        params = []
        
        if task_type is not None:
            conditions.append("task_type = ?")
            params.append(task_type)
        
        if station_id is not None:
            conditions.append("station_id = ?")
            params.append(station_id)
        
        if start_date:
            conditions.append("DATE(timestamp) >= ?")
            params.append(start_date)
        
        if end_date:
            conditions.append("DATE(timestamp) <= ?")
            params.append(end_date)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT * FROM task_records
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            records = []
            for row in rows:
                record = dict(row)
                # 解析JSON字段
                if record.get('result_data'):
                    record['result_data'] = json.loads(record['result_data'])
                records.append(record)
            
            return records
    
    def get_latest_record(
        self,
        task_type: int,
        station_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        获取最新的任务记录
        
        Args:
            task_type: 任务类型
            station_id: 站点ID（可选）
        
        Returns:
            Dict: 记录，不存在返回None
        """
        records = self.get_task_records(
            task_type=task_type,
            station_id=station_id,
            limit=1
        )
        return records[0] if records else None
    
    # ==================== 任务队列相关 ====================
    
    def add_task_to_queue(
        self,
        task_id: str,
        station_id: int,
        task_type: int,
        priority: str = "medium",
        params: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        添加任务到队列
        
        Args:
            task_id: 任务ID（唯一）
            station_id: 站点ID
            task_type: 任务类型
            priority: 优先级（high/medium/low）
            params: 额外参数
        
        Returns:
            int: 记录ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO task_queue 
                (task_id, station_id, task_type, priority, params)
                VALUES (?, ?, ?, ?, ?)
            """, (
                task_id,
                station_id,
                task_type,
                priority,
                json.dumps(params, ensure_ascii=False) if params else None
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        """
        获取所有待处理的任务
        
        Returns:
            List[Dict]: 任务列表
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM task_queue
                WHERE status = 'pending'
                ORDER BY 
                    CASE priority
                        WHEN 'high' THEN 1
                        WHEN 'medium' THEN 2
                        WHEN 'low' THEN 3
                    END,
                    created_at ASC
            """)
            rows = cursor.fetchall()
            
            tasks = []
            for row in rows:
                task = dict(row)
                # 解析JSON字段
                if task.get('params'):
                    task['params'] = json.loads(task['params'])
                tasks.append(task)
            
            return tasks
    
    def update_task_status(
        self,
        task_id: str,
        status: str,
        completed_at: Optional[str] = None
    ) -> bool:
        """
        更新任务状态
        
        Args:
            task_id: 任务ID
            status: 新状态（assigned/completed/failed）
            completed_at: 完成时间
        
        Returns:
            bool: 是否更新成功
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if status == "assigned":
                cursor.execute("""
                    UPDATE task_queue
                    SET status = ?, assigned_at = CURRENT_TIMESTAMP
                    WHERE task_id = ?
                """, (status, task_id))
            elif status in ["completed", "failed"]:
                cursor.execute("""
                    UPDATE task_queue
                    SET status = ?, completed_at = ?
                    WHERE task_id = ?
                """, (status, completed_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S"), task_id))
            else:
                cursor.execute("""
                    UPDATE task_queue
                    SET status = ?
                    WHERE task_id = ?
                """, (status, task_id))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_task(self, task_id: str) -> bool:
        """
        删除任务
        
        Args:
            task_id: 任务ID
        
        Returns:
            bool: 是否删除成功
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM task_queue WHERE task_id = ?", (task_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def clear_completed_tasks(self) -> int:
        """
        清除已完成的任务
        
        Returns:
            int: 清除的任务数量
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM task_queue WHERE status IN ('completed', 'failed')")
            conn.commit()
            return cursor.rowcount
    
    # ==================== 报警日志相关 ====================
    
    def add_alert(
        self,
        alert_level: str,
        alert_type: str,
        message: str,
        record_id: Optional[int] = None
    ) -> int:
        """
        添加报警记录
        
        Args:
            alert_level: 报警级别（warning/danger）
            alert_type: 报警类型
            message: 报警消息
            record_id: 关联的任务记录ID
        
        Returns:
            int: 记录ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO alert_log 
                (record_id, alert_level, alert_type, message)
                VALUES (?, ?, ?, ?)
            """, (record_id, alert_level, alert_type, message))
            conn.commit()
            return cursor.lastrowid
    
    def get_unhandled_alerts(self) -> List[Dict[str, Any]]:
        """
        获取未处理的报警
        
        Returns:
            List[Dict]: 报警列表
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM alert_log
                WHERE handled = 0
                ORDER BY timestamp DESC
            """)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def mark_alert_handled(self, alert_id: int) -> bool:
        """
        标记报警为已处理
        
        Args:
            alert_id: 报警ID
        
        Returns:
            bool: 是否标记成功
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE alert_log
                SET handled = 1
                WHERE id = ?
            """, (alert_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    # ==================== 小车状态相关 ====================
    
    def update_cart_status(
        self,
        online: bool,
        current_station: Optional[int] = None,
        mode: Optional[str] = None,
        battery_level: Optional[int] = None,
        last_activity: Optional[str] = None
    ) -> bool:
        """
        更新小车状态（更新最新一条记录）
        
        Args:
            online: 是否在线
            current_station: 当前站点
            mode: 运行模式
            battery_level: 电池电量
            last_activity: 最后活动
        
        Returns:
            bool: 是否更新成功
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 构建更新字段
            updates = ["online = ?"]
            params = [1 if online else 0]
            
            if current_station is not None:
                updates.append("current_station = ?")
                params.append(current_station)
            
            if mode is not None:
                updates.append("mode = ?")
                params.append(mode)
            
            if battery_level is not None:
                updates.append("battery_level = ?")
                params.append(battery_level)
            
            if last_activity is not None:
                updates.append("last_activity = ?")
                params.append(last_activity)
            
            updates.append("timestamp = CURRENT_TIMESTAMP")
            
            # 获取最新记录ID
            cursor.execute("SELECT id FROM cart_status ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            
            if row:
                # 更新现有记录
                record_id = row[0]
                params.append(record_id)
                cursor.execute(f"""
                    UPDATE cart_status
                    SET {', '.join(updates)}
                    WHERE id = ?
                """, params)
            else:
                # 插入新记录
                cursor.execute("""
                    INSERT INTO cart_status 
                    (online, current_station, mode, battery_level, last_activity)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    1 if online else 0,
                    current_station,
                    mode or 'idle',
                    battery_level,
                    last_activity
                ))
            
            conn.commit()
            return True
    
    def get_cart_status(self) -> Optional[Dict[str, Any]]:
        """
        获取当前小车状态
        
        Returns:
            Dict: 小车状态，不存在返回None
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM cart_status
                ORDER BY id DESC
                LIMIT 1
            """)
            row = cursor.fetchone()
            return dict(row) if row else None
    
    # ==================== 数据清理相关 ====================
    
    def cleanup_old_records(
        self,
        image_retention_days: int = 30,
        record_retention_days: int = 90
    ) -> Tuple[int, int]:
        """
        清理过期数据
        
        Args:
            image_retention_days: 图片保留天数
            record_retention_days: 记录保留天数
        
        Returns:
            Tuple[int, int]: (删除的记录数, 删除的报警数)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 计算截止日期
            cutoff_date = (
                datetime.now() - timedelta(days=record_retention_days)
            ).strftime("%Y-%m-%d")
            
            # 删除旧的任务记录
            cursor.execute("""
                DELETE FROM task_records
                WHERE DATE(timestamp) < ?
            """, (cutoff_date,))
            deleted_records = cursor.rowcount
            
            # 删除旧的报警日志
            cursor.execute("""
                DELETE FROM alert_log
                WHERE DATE(timestamp) < ?
            """, (cutoff_date,))
            deleted_alerts = cursor.rowcount
            
            conn.commit()
            
            return deleted_records, deleted_alerts
    
    # ==================== 统计相关 ====================
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取系统统计信息
        
        Returns:
            Dict: 统计信息
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # 总任务数
            cursor.execute("SELECT COUNT(*) FROM task_records")
            stats['total_tasks'] = cursor.fetchone()[0]
            
            # 今日任务数
            cursor.execute("""
                SELECT COUNT(*) FROM task_records
                WHERE DATE(timestamp) = DATE('now')
            """)
            stats['today_tasks'] = cursor.fetchone()[0]
            
            # 待处理任务数
            cursor.execute("""
                SELECT COUNT(*) FROM task_queue
                WHERE status = 'pending'
            """)
            stats['pending_tasks'] = cursor.fetchone()[0]
            
            # 未处理报警数
            cursor.execute("""
                SELECT COUNT(*) FROM alert_log
                WHERE handled = 0
            """)
            stats['unhandled_alerts'] = cursor.fetchone()[0]
            
            # 各类型任务统计
            cursor.execute("""
                SELECT task_type, COUNT(*) as count
                FROM task_records
                GROUP BY task_type
            """)
            stats['task_type_stats'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            return stats


# 便捷函数
def get_db_manager() -> DatabaseManager:
    """获取数据库管理器实例"""
    return DatabaseManager()


if __name__ == "__main__":
    # 测试数据库管理器
    try:
        db = get_db_manager()
        print("[OK] 数据库管理器初始化成功")
        
        # 测试统计功能
        stats = db.get_statistics()
        print("\n系统统计:")
        print(f"  总任务数: {stats['total_tasks']}")
        print(f"  今日任务数: {stats['today_tasks']}")
        print(f"  待处理任务: {stats['pending_tasks']}")
        print(f"  未处理报警: {stats['unhandled_alerts']}")
        
        # 测试小车状态
        cart_status = db.get_cart_status()
        if cart_status:
            print("\n小车状态:")
            print(f"  在线: {'是' if cart_status['online'] else '否'}")
            print(f"  当前站点: {cart_status['current_station']}")
            print(f"  运行模式: {cart_status['mode']}")
            print(f"  电池电量: {cart_status['battery_level']}%")
        
    except FileNotFoundError as e:
        print(f"[失败] {e}")
        print("请先运行: python scripts/init_database.py")

