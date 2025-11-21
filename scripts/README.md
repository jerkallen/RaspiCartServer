# 数据库管理模块说明

## 模块列表

### 1. db_manager.py - 数据库管理器

提供完整的数据库操作功能，包括任务记录、任务队列、报警日志和小车状态管理。

**主要功能**:
- 任务记录的增删改查
- 任务队列管理
- 报警日志管理
- 小车状态管理
- 数据统计和清理

### 2. init_database.py - 数据库初始化脚本

用于初始化数据库、创建示例数据和管理数据库。

## 快速开始

### 初始化数据库

```bash
# 基础初始化（仅创建表结构）
python scripts/init_database.py

# 初始化并创建示例数据
python scripts/init_database.py --sample

# 查看数据库统计信息
python scripts/init_database.py --stats

# 重置数据库（删除所有数据）
python scripts/init_database.py --reset
```

### 使用数据库管理器

```python
from scripts.db_manager import DatabaseManager

# 初始化
db = DatabaseManager()

# 添加任务记录
record_id = db.add_task_record(
    task_id="task-123",
    task_type=1,
    station_id=3,
    result_data={"value": 1.05, "unit": "MPa"},
    status="normal",
    confidence=0.95
)

# 查询任务记录
records = db.get_task_records(
    task_type=1,
    limit=10
)

# 添加任务到队列
task_id = db.add_task_to_queue(
    station_id=3,
    task_type=1,
    params={"camera_angle": 30}
)

# 获取待执行任务
pending_tasks = db.get_pending_tasks(limit=10)

# 更新任务状态
db.update_task_status(
    task_id=task_id,
    status="completed"
)

# 添加报警
alert_id = db.add_alert(
    alert_level="warning",
    alert_type="high_temperature",
    message="检测到高温物体，温度85℃",
    record_id=record_id
)

# 更新小车状态
db.update_cart_status(
    online=True,
    current_station=3,
    mode="循环模式",
    battery_level=85
)
```

## 数据库表结构

### task_records - 任务记录表

存储所有任务的执行记录和结果。

| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | INTEGER | 主键 |
| task_id | TEXT | 任务ID |
| task_type | INTEGER | 任务类型（1-4） |
| station_id | INTEGER | 站点ID |
| image_path | TEXT | 图片路径 |
| result_data | TEXT | 结果数据（JSON） |
| status | TEXT | 状态（normal/warning/danger） |
| confidence | REAL | 置信度 |
| processing_time | REAL | 处理时间（秒） |
| timestamp | DATETIME | 时间戳 |
| created_at | DATETIME | 创建时间 |

### task_queue - 任务队列表

管理待执行的任务队列。

| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | INTEGER | 主键 |
| task_id | TEXT | 任务ID（唯一） |
| station_id | INTEGER | 站点ID |
| task_type | INTEGER | 任务类型（1-4） |
| status | TEXT | 状态（pending/assigned/completed/failed） |
| params | TEXT | 参数（JSON） |
| assigned_at | DATETIME | 分配时间 |
| completed_at | DATETIME | 完成时间 |
| created_at | DATETIME | 创建时间 |

### alert_log - 报警日志表

记录所有报警信息。

| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | INTEGER | 主键 |
| record_id | INTEGER | 关联任务记录ID |
| alert_level | TEXT | 报警级别（warning/danger） |
| alert_type | TEXT | 报警类型 |
| message | TEXT | 报警消息 |
| handled | BOOLEAN | 是否已处理 |
| timestamp | DATETIME | 时间戳 |

### cart_status - 小车状态表

记录小车的状态信息。

| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | INTEGER | 主键 |
| online | BOOLEAN | 是否在线 |
| current_station | INTEGER | 当前站点 |
| mode | TEXT | 运行模式 |
| battery_level | INTEGER | 电池电量（%） |
| last_activity | TEXT | 最近活动 |
| timestamp | DATETIME | 时间戳 |

## 常用操作

### 查询统计信息

```python
# 获取最近7天的统计信息
stats = db.get_statistics(days=7)

# 获取指定任务类型的统计
stats = db.get_statistics(task_type=1, days=30)
```

### 数据清理

```python
# 清理90天前的旧记录
count = db.cleanup_old_records(days=90)

# 清理已完成的任务（1天前）
count = db.clear_completed_tasks(days=1)

# 优化数据库
db.vacuum_database()
```

### 获取最新数据

```python
# 获取指定站点的最新记录
latest = db.get_latest_record_by_station(station_id=3)

# 获取最新小车状态
cart_status = db.get_latest_cart_status()
```

## 注意事项

1. **数据库路径**: 默认路径为 `data/database/inspection.db`
2. **连接管理**: 使用上下文管理器自动处理连接和提交
3. **错误处理**: 所有数据库操作都有完整的错误处理和日志记录
4. **索引优化**: 已为常用查询字段创建索引
5. **数据备份**: 建议定期备份数据库文件

## 测试

### 测试数据库管理器

```bash
python scripts/db_manager.py
```

### 测试初始化脚本

```bash
# 创建示例数据并查看统计
python scripts/init_database.py --sample
```

## 维护建议

1. **定期清理**: 建议每周运行一次数据清理
2. **数据库优化**: 每月运行一次 VACUUM
3. **备份策略**: 每天自动备份数据库文件
4. **监控空间**: 监控磁盘空间使用情况

## 故障排除

### 问题：数据库文件被锁定

**解决方法**: 确保没有其他进程在使用数据库，关闭所有相关服务后重试。

### 问题：查询速度慢

**解决方法**: 
1. 检查是否需要添加索引
2. 运行 `db.vacuum_database()` 优化数据库
3. 清理旧数据

### 问题：磁盘空间不足

**解决方法**:
1. 运行 `db.cleanup_old_records()` 清理旧记录
2. 清理过期的图片文件
3. 删除旧的日志文件

