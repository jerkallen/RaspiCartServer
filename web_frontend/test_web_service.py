"""
Web服务测试脚本
测试Flask Web服务的各项功能
"""
import requests
import json
from datetime import datetime


def print_result(test_name, success, message=""):
    """打印测试结果"""
    status = "✓" if success else "✗"
    color = "\033[92m" if success else "\033[91m"
    reset = "\033[0m"
    print(f"{color}[{status}]{reset} {test_name}")
    if message:
        print(f"    {message}")


def test_web_service(base_url="http://localhost:5000"):
    """测试Web服务"""
    print("="*60)
    print("智能巡检系统 - Web服务测试")
    print("="*60)
    print(f"测试地址: {base_url}")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    
    # 测试1: 主页面访问
    print("1. 测试主页面访问...")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        success = response.status_code == 200
        print_result("主页面访问", success, f"状态码: {response.status_code}")
    except Exception as e:
        print_result("主页面访问", False, f"错误: {str(e)}")
    
    # 测试2: 获取任务列表
    print("\n2. 测试获取任务列表...")
    try:
        response = requests.get(f"{base_url}/api/tasks", timeout=5)
        success = response.status_code == 200
        if success:
            data = response.json()
            count = data.get('data', {}).get('count', 0)
            print_result("获取任务列表", success, f"任务数量: {count}")
        else:
            print_result("获取任务列表", success, f"状态码: {response.status_code}")
    except Exception as e:
        print_result("获取任务列表", False, f"错误: {str(e)}")
    
    # 测试3: 添加任务
    print("\n3. 测试添加任务...")
    try:
        task_data = {
            "station_id": 99,
            "task_type": 1,
            "params": {}
        }
        response = requests.post(
            f"{base_url}/api/tasks/add",
            json=task_data,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        success = response.status_code == 200
        if success:
            data = response.json()
            task_id = data.get('data', {}).get('task_id', 'N/A')
            print_result("添加任务", success, f"任务ID: {task_id}")
            
            # 测试4: 删除刚添加的任务
            print("\n4. 测试删除任务...")
            try:
                response = requests.delete(f"{base_url}/api/tasks/{task_id}", timeout=5)
                success = response.status_code == 200
                print_result("删除任务", success, f"任务ID: {task_id}")
            except Exception as e:
                print_result("删除任务", False, f"错误: {str(e)}")
        else:
            print_result("添加任务", success, f"状态码: {response.status_code}")
    except Exception as e:
        print_result("添加任务", False, f"错误: {str(e)}")
    
    # 测试5: 获取历史记录
    print("\n5. 测试获取历史记录...")
    try:
        response = requests.get(f"{base_url}/api/history?limit=5", timeout=5)
        success = response.status_code == 200
        if success:
            data = response.json()
            count = data.get('data', {}).get('count', 0)
            print_result("获取历史记录", success, f"记录数量: {count}")
        else:
            print_result("获取历史记录", success, f"状态码: {response.status_code}")
    except Exception as e:
        print_result("获取历史记录", False, f"错误: {str(e)}")
    
    # 测试6: 获取统计信息
    print("\n6. 测试获取统计信息...")
    try:
        response = requests.get(f"{base_url}/api/statistics", timeout=5)
        success = response.status_code == 200
        if success:
            data = response.json()
            stats = data.get('data', {})
            print_result("获取统计信息", success, 
                        f"总任务: {stats.get('total_tasks', 0)}, "
                        f"今日: {stats.get('today_tasks', 0)}")
        else:
            print_result("获取统计信息", success, f"状态码: {response.status_code}")
    except Exception as e:
        print_result("获取统计信息", False, f"错误: {str(e)}")
    
    # 测试7: 获取小车状态
    print("\n7. 测试获取小车状态...")
    try:
        response = requests.get(f"{base_url}/api/cart/status", timeout=5)
        success = response.status_code == 200
        if success:
            data = response.json()
            cart = data.get('data', {})
            online = "在线" if cart.get('online') else "离线"
            print_result("获取小车状态", success, f"状态: {online}")
        else:
            print_result("获取小车状态", success, f"状态码: {response.status_code}")
    except Exception as e:
        print_result("获取小车状态", False, f"错误: {str(e)}")
    
    # 测试8: 获取报警信息
    print("\n8. 测试获取报警信息...")
    try:
        response = requests.get(f"{base_url}/api/alerts", timeout=5)
        success = response.status_code == 200
        if success:
            data = response.json()
            count = data.get('data', {}).get('count', 0)
            print_result("获取报警信息", success, f"未处理报警: {count}")
        else:
            print_result("获取报警信息", success, f"状态码: {response.status_code}")
    except Exception as e:
        print_result("获取报警信息", False, f"错误: {str(e)}")
    
    print("\n" + "="*60)
    print("测试完成!")
    print("="*60)


if __name__ == "__main__":
    import sys
    
    # 从命令行参数获取URL,默认为localhost:5000
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    
    test_web_service(base_url)

