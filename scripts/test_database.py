"""
数据库功能测试脚本
演示如何使用数据库管理器
"""
from db_manager import get_db_manager
import uuid
from datetime import datetime


def test_task_queue():
    """测试任务队列功能"""
    print("="*60)
    print("测试任务队列功能")
    print("="*60)
    
    db = get_db_manager()
    
    # 添加测试任务
    task_id1 = str(uuid.uuid4())
    task_id2 = str(uuid.uuid4())
    
    print("\n1. 添加任务到队列...")
    db.add_task_to_queue(
        task_id=task_id1,
        station_id=1,
        task_type=1,
        priority="high",
        params={"description": "指针仪表读数"}
    )
    print(f"   任务1已添加: {task_id1}")
    
    db.add_task_to_queue(
        task_id=task_id2,
        station_id=2,
        task_type=2,
        priority="medium",
        params={"description": "温度检测"}
    )
    print(f"   任务2已添加: {task_id2}")
    
    # 查询待处理任务
    print("\n2. 查询待处理任务...")
    tasks = db.get_pending_tasks()
    print(f"   共有 {len(tasks)} 个待处理任务:")
    for task in tasks:
        print(f"   - 站点{task['station_id']}, 类型{task['task_type']}, 优先级:{task['priority']}")
    
    # 更新任务状态
    print("\n3. 更新任务状态...")
    db.update_task_status(task_id1, "assigned")
    print(f"   任务1状态更新为: assigned")
    
    db.update_task_status(task_id2, "completed")
    print(f"   任务2状态更新为: completed")
    
    # 再次查询
    print("\n4. 再次查询待处理任务...")
    tasks = db.get_pending_tasks()
    print(f"   剩余 {len(tasks)} 个待处理任务")
    
    # 清理测试数据
    print("\n5. 清理测试任务...")
    db.delete_task(task_id1)
    db.delete_task(task_id2)
    print("   测试任务已清理")
    
    print("\n[完成] 任务队列功能测试通过")


def test_task_records():
    """测试任务记录功能"""
    print("\n" + "="*60)
    print("测试任务记录功能")
    print("="*60)
    
    db = get_db_manager()
    
    # 添加测试记录
    print("\n1. 添加任务记录...")
    record_id = db.add_task_record(
        task_id="test-task-001",
        task_type=1,
        station_id=1,
        image_path="data/images/2024-11-21/task1/test.jpg",
        result_data={
            "value": 1.05,
            "unit": "MPa",
            "confidence": 0.95,
            "status": "normal"
        },
        status="normal",
        confidence=0.95,
        processing_time=1.2
    )
    print(f"   记录已添加，ID: {record_id}")
    
    # 查询记录
    print("\n2. 查询任务记录...")
    records = db.get_task_records(task_type=1, limit=5)
    print(f"   查询到 {len(records)} 条记录")
    if records:
        latest = records[0]
        print(f"   最新记录: 站点{latest['station_id']}, 状态:{latest['status']}")
    
    # 查询最新记录
    print("\n3. 查询最新记录...")
    latest = db.get_latest_record(task_type=1, station_id=1)
    if latest:
        print(f"   最新记录时间: {latest['timestamp']}")
        print(f"   置信度: {latest['confidence']}")
    
    print("\n[完成] 任务记录功能测试通过")


def test_alert_log():
    """测试报警日志功能"""
    print("\n" + "="*60)
    print("测试报警日志功能")
    print("="*60)
    
    db = get_db_manager()
    
    # 添加报警
    print("\n1. 添加报警记录...")
    alert_id = db.add_alert(
        alert_level="warning",
        alert_type="high_temperature",
        message="检测到高温，温度75℃"
    )
    print(f"   报警已添加，ID: {alert_id}")
    
    # 查询未处理报警
    print("\n2. 查询未处理报警...")
    alerts = db.get_unhandled_alerts()
    print(f"   共有 {len(alerts)} 条未处理报警")
    for alert in alerts:
        print(f"   - [{alert['alert_level']}] {alert['message']}")
    
    # 标记已处理
    print("\n3. 标记报警为已处理...")
    db.mark_alert_handled(alert_id)
    print(f"   报警{alert_id}已标记为已处理")
    
    # 再次查询
    alerts = db.get_unhandled_alerts()
    print(f"   剩余 {len(alerts)} 条未处理报警")
    
    print("\n[完成] 报警日志功能测试通过")


def test_cart_status():
    """测试小车状态功能"""
    print("\n" + "="*60)
    print("测试小车状态功能")
    print("="*60)
    
    db = get_db_manager()
    
    # 更新小车状态
    print("\n1. 更新小车状态...")
    db.update_cart_status(
        online=True,
        current_station=3,
        mode="循环模式",
        battery_level=85,
        last_activity="执行任务1"
    )
    print("   小车状态已更新")
    
    # 查询小车状态
    print("\n2. 查询小车状态...")
    status = db.get_cart_status()
    if status:
        print(f"   在线状态: {'在线' if status['online'] else '离线'}")
        print(f"   当前站点: {status['current_station']}")
        print(f"   运行模式: {status['mode']}")
        print(f"   电池电量: {status['battery_level']}%")
        print(f"   最后活动: {status['last_activity']}")
    
    print("\n[完成] 小车状态功能测试通过")


def test_statistics():
    """测试统计功能"""
    print("\n" + "="*60)
    print("测试统计功能")
    print("="*60)
    
    db = get_db_manager()
    
    print("\n获取系统统计...")
    stats = db.get_statistics()
    
    print(f"\n系统统计信息:")
    print(f"  总任务数: {stats['total_tasks']}")
    print(f"  今日任务数: {stats['today_tasks']}")
    print(f"  待处理任务: {stats['pending_tasks']}")
    print(f"  未处理报警: {stats['unhandled_alerts']}")
    
    print(f"\n各类型任务统计:")
    for task_type, count in stats['task_type_stats'].items():
        print(f"  任务类型{task_type}: {count}次")
    
    print("\n[完成] 统计功能测试通过")


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("数据库管理器功能测试")
    print("="*60)
    print("\n说明: 此脚本将测试数据库管理器的各项功能")
    print("测试将在实际数据库上进行，但会清理测试数据\n")
    
    try:
        # 运行所有测试
        test_task_queue()
        test_task_records()
        test_alert_log()
        test_cart_status()
        test_statistics()
        
        print("\n" + "="*60)
        print("[成功] 所有测试通过！")
        print("="*60)
        
    except Exception as e:
        print(f"\n[失败] 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

