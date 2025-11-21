"""
智能巡检小车模拟测试程序

模拟小车根据任务队列动态执行任务的完整工作流程：
1. 从服务端获取任务列表
2. 取出第一个任务
3. 模拟行驶到对应站点（5秒）
4. 执行任务并上传图片/数据到服务端
5. 任务完成后自动从队列删除
6. 重新获取任务列表
7. 重复步骤2-6，根据运行模式决定是否继续

特点：
- 任务列表由服务端管理，动态读取
- 支持任意数量的任务
- 支持任意站点和任务类型组合
- 每完成一个任务，自动从队列中移除
- 支持两种运行模式：
  * 单圈模式：完成所有任务后自动停止（适用于一次性巡检）
  * 循环模式：持续运行，任务完成后等待新任务（适用于长期监控）
"""

import requests
import time
import json
import os
import base64
from pathlib import Path
from datetime import datetime

# ==================== 配置区域 ====================

# 运行模式配置
# RUN_MODE = "单圈模式"  # 可选: "单圈模式" 或 "循环模式"
RUN_MODE = "循环模式"  # 可选: "单圈模式" 或 "循环模式"
# - 单圈模式: 完成所有任务后自动停止（适用于一次性巡检）
# - 循环模式: 持续循环运行，任务完成后等待新任务（适用于长期监控）

# 服务端IP配置（根据实际情况修改）
# 选项1: 局域网内的本地电脑（例如：'192.168.1.100'）
# 选项2: 云服务器（'47.110.156.72'）
# SERVER_IP = '47.110.156.72'  # 默认使用云服务器IP
SERVER_IP = '127.0.0.1'  # 本地测试

# 端口配置
WEB_PORT = 5000  # Web服务端口（获取任务）
API_PORT = 3000  # API服务端口（上传结果）

# 构造URL
TASK_URL = f'http://{SERVER_IP}:{WEB_PORT}/api/tasks'
PROCESS_URL = f'http://{SERVER_IP}:{API_PORT}/api/process'
STATUS_URL = f'http://{SERVER_IP}:{WEB_PORT}/api/cart/status'

# 测试图片路径（项目根目录下）
PROJECT_ROOT = Path(__file__).parent
IMAGE_FILES = {
    1: PROJECT_ROOT / 'meter_test.jpg',   # 站点1：压力表
    2: PROJECT_ROOT / 'heat_test.png',    # 站点2：热成像
    3: PROJECT_ROOT / 'smoke1_test.png',  # 站点3：烟雾探测1
    4: PROJECT_ROOT / 'smoke2_test.png',  # 站点4：烟雾探测2
}

# 模拟行驶时间（秒）
TRAVEL_TIME = 5

# 请求超时时间（秒）
REQUEST_TIMEOUT = 30

# 循环模式等待时间（秒）
LOOP_WAIT_TIME = 5  # 循环模式下无任务时的等待时间

# ==================== 辅助函数 ====================

def print_separator(char='=', length=60):
    """打印分隔线"""
    print(char * length)

def print_step(step_num, description):
    """打印步骤标题"""
    print_separator()
    print(f"步骤 {step_num}: {description}")
    print_separator()

def print_response(response_data, indent=2):
    """格式化打印响应数据"""
    print(json.dumps(response_data, indent=indent, ensure_ascii=False))

# ==================== 核心功能函数 ====================

def get_tasks():
    """
    从服务端获取任务列表
    
    返回:
        dict: 任务列表数据，失败返回None
    """
    try:
        print(f"📡 发送请求: GET {TASK_URL}")
        response = requests.get(TASK_URL, timeout=REQUEST_TIMEOUT)
        
        print(f"✅ 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("📋 返回数据:")
            print_response(data)
            return data
        else:
            print(f"❌ 请求失败: HTTP {response.status_code}")
            print(f"响应内容: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print(f"❌ 请求超时（超过{REQUEST_TIMEOUT}秒）")
        return None
    except requests.exceptions.ConnectionError:
        print(f"❌ 连接失败，无法连接到 {TASK_URL}")
        print("请检查：")
        print(f"  1. 服务端IP地址是否正确（当前: {SERVER_IP}）")
        print(f"  2. 服务端是否正常运行")
        print(f"  3. 网络连接是否正常")
        return None
    except Exception as e:
        print(f"❌ 发生异常: {e}")
        return None

def upload_task_result(station_id, task_type, image_path, params=None, task_id=None):
    """
    上传任务执行结果到服务端
    
    参数:
        station_id: 站点ID
        task_type: 任务类型（1-4）
        image_path: 图片文件路径
        params: 额外参数（字典），默认为None
        task_id: 任务ID（可选，如果提供则服务端会在处理成功后自动删除任务）
    
    返回:
        dict: 识别结果数据，失败返回None
    """
    try:
        # 检查图片文件是否存在
        if not os.path.exists(image_path):
            print(f"❌ 图片文件不存在: {image_path}")
            return None
        
        print(f"📡 发送请求: POST {PROCESS_URL}")
        print(f"📸 图片文件: {image_path}")
        print(f"🎯 站点ID: {station_id}, 任务类型: {task_type}")
        
        # 读取图片并转换为base64
        with open(image_path, 'rb') as image_file:
            image_bytes = image_file.read()
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # 准备JSON数据
        data = {
            'image_base64': image_base64,
            'task_type': task_type,
            'station_id': station_id,
        }
        
        # 如果有task_id，添加到数据中
        if task_id:
            data['task_id'] = task_id
            print(f"🆔 任务ID: {task_id}")
        
        # 如果有额外参数，添加到数据中
        if params:
            data['params'] = json.dumps(params, ensure_ascii=False)
            print(f"📦 参数: {data['params']}")
        
        # 发送JSON请求
        response = requests.post(
            PROCESS_URL,
            json=data,
            timeout=REQUEST_TIMEOUT
        )
        
        print(f"✅ 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("🎉 识别结果:")
            print_response(result)
            return result
        else:
            print(f"❌ 请求失败: HTTP {response.status_code}")
            print(f"响应内容: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print(f"❌ 请求超时（超过{REQUEST_TIMEOUT}秒）")
        return None
    except requests.exceptions.ConnectionError:
        print(f"❌ 连接失败，无法连接到 {PROCESS_URL}")
        return None
    except Exception as e:
        print(f"❌ 发生异常: {e}")
        return None

def update_cart_status(online=True, current_station=None, mode='idle', battery_level=85):
    """
    更新小车状态到服务器
    
    参数:
        online: 是否在线
        current_station: 当前站点
        mode: 运行模式 (idle/single/loop/traveling/working)
        battery_level: 电池电量
    """
    try:
        data = {
            'online': online,
            'current_station': current_station,
            'mode': mode,
            'battery_level': battery_level,
            'last_activity': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        response = requests.post(
            STATUS_URL,
            json=data,
            timeout=5
        )
        
        if response.status_code == 200:
            return True
        else:
            print(f"   ⚠️  状态更新失败: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ⚠️  状态更新异常: {e}")
        return False

def simulate_travel(station_id, battery_level=85):
    """
    模拟小车行驶到指定站点
    
    参数:
        station_id: 目标站点ID
        battery_level: 当前电池电量
    """
    print(f"\n🚗 小车正在巡线前往站点 {station_id}...")
    
    # 更新状态：行驶中
    mode = 'single' if RUN_MODE == '单圈模式' else 'loop'
    update_cart_status(
        online=True, 
        current_station=None, 
        mode='traveling',
        battery_level=battery_level
    )
    
    for i in range(TRAVEL_TIME, 0, -1):
        print(f"   ⏱️  还需 {i} 秒到达...", end='\r')
        time.sleep(1)
    print(f"   🛑 已到达站点 {station_id}！      ")
    
    # 更新状态：到达站点，工作中
    update_cart_status(
        online=True,
        current_station=station_id,
        mode='working',
        battery_level=battery_level - 2  # 行驶消耗一点电量
    )

# ==================== 主测试流程 ====================

def execute_task(task):
    """
    执行单个任务
    
    参数:
        task: 任务信息字典，包含 task_id, station_id, task_type, params
    
    返回:
        bool: 任务是否成功执行
    """
    task_id = task['task_id']
    station_id = task['station_id']
    task_type = task['task_type']
    params = task.get('params', {})
    
    print(f"\n📍 执行任务: ID={task_id}")
    print(f"   站点: {station_id}, 类型: {task_type}")
    
    # 检查对应的测试图片是否存在
    if task_type not in IMAGE_FILES:
        print(f"   ❌ 不支持的任务类型: {task_type}")
        return False
    
    image_path = IMAGE_FILES[task_type]
    if not image_path.exists():
        print(f"   ❌ 测试图片不存在: {image_path}")
        return False
    
    # 根据任务类型执行相应操作
    task_names = {
        1: "压力表读取",
        2: "热成像测温",
        3: "烟雾探测A",
        4: "烟雾探测B"
    }
    
    print(f"   🎯 任务名称: {task_names.get(task_type, '未知任务')}")
    print(f"   📷 使用图片: {image_path.name}")
    
    # 对于温度任务，使用任务参数或模拟参数
    if task_type == 2:
        if not params:
            # 如果任务没有参数，使用模拟数据
            params = {
                'max_temperature': 85.6,
                'avg_temperature': 72.3,
                'ambient_temperature': 26.5
            }
            print(f"   📊 使用模拟温度数据")
        print(f"   📊 温度参数: {params}")
    
    # 上传任务结果（传递task_id，以便服务器在处理成功后自动删除任务）
    result = upload_task_result(
        station_id=station_id,
        task_type=task_type,
        image_path=image_path,
        params=params if task_type == 2 else None,
        task_id=task_id
    )
    
    return result is not None


def main():
    """主测试流程：根据任务列表动态执行任务"""
    
    print("\n" + "=" * 60)
    print("🤖 智能巡检小车模拟测试程序")
    print("=" * 60)
    print(f"🔧 运行模式: {RUN_MODE}")
    if RUN_MODE == "单圈模式":
        print("   - 完成所有任务后自动停止")
    else:
        print("   - 持续循环，等待新任务")
    print(f"📡 服务端配置:")
    print(f"   - IP地址: {SERVER_IP}")
    print(f"   - Web端口: {WEB_PORT} (获取任务)")
    print(f"   - API端口: {API_PORT} (上传结果)")
    print(f"⏱️  站点间隔: {TRAVEL_TIME}秒")
    print("=" * 60)
    
    # 检查测试图片是否存在
    print("\n🔍 检查测试图片文件...")
    missing_files = []
    for task_type, image_path in IMAGE_FILES.items():
        if image_path.exists():
            print(f"   ✅ 任务类型{task_type}: {image_path.name}")
        else:
            print(f"   ❌ 任务类型{task_type}: {image_path.name} (不存在)")
            missing_files.append(image_path)
    
    if missing_files:
        print(f"\n❌ 缺少 {len(missing_files)} 个测试图片，无法继续测试")
        return
    
    # ========== 开始执行任务循环 ==========
    step_num = 1
    completed_count = 0
    failed_count = 0
    battery_level = 100  # 初始电量100%
    
    print_step(step_num, "小车启动，获取任务列表")
    step_num += 1
    
    # 更新小车状态：启动，在线
    mode = 'single' if RUN_MODE == '单圈模式' else 'loop'
    update_cart_status(
        online=True,
        current_station=None,
        mode=mode,
        battery_level=battery_level
    )
    
    while True:
        # 获取当前任务列表
        tasks_data = get_tasks()
        
        if not tasks_data:
            print("\n❌ 无法获取任务列表，测试终止")
            break
        
        # 检查任务状态
        if tasks_data.get('status') != 'success':
            print("\n❌ 任务列表返回错误状态")
            break
        
        # 获取任务列表
        tasks = tasks_data.get('data', {}).get('tasks', [])
        task_count = len(tasks)
        
        print(f"\n📋 当前任务队列: {task_count} 个任务")
        
        if task_count == 0:
            if RUN_MODE == "单圈模式":
                print("\n🎉🎉🎉 所有任务已完成，巡检结束！")
                # 更新状态：完成，待机
                update_cart_status(
                    online=True,
                    current_station=None,
                    mode='idle',
                    battery_level=battery_level
                )
                break
            else:  # 循环模式
                print(f"\n🔄 循环模式: 当前无任务，等待 {LOOP_WAIT_TIME} 秒后重新检查...")
                # 更新状态：等待中
                update_cart_status(
                    online=True,
                    current_station=None,
                    mode='loop',
                    battery_level=battery_level
                )
                time.sleep(LOOP_WAIT_TIME)
                continue
        
        # 显示任务列表
        print("\n任务列表:")
        for i, task in enumerate(tasks, 1):
            print(f"   {i}. 站点{task['station_id']} - 类型{task['task_type']}")
        
        # 取出第一个任务
        current_task = tasks[0]
        
        print_step(step_num, f"前往站点 {current_task['station_id']} 执行任务")
        step_num += 1
        
        # 模拟行驶到站点（消耗电量）
        simulate_travel(current_task['station_id'], battery_level)
        battery_level = max(20, battery_level - 3)  # 每次任务消耗3%电量，最低保持20%
        
        # 执行任务
        success = execute_task(current_task)
        
        if success:
            print(f"\n✅ 任务完成: 站点{current_task['station_id']}")
            completed_count += 1
            # 更新状态：任务完成
            mode = 'single' if RUN_MODE == '单圈模式' else 'loop'
            update_cart_status(
                online=True,
                current_station=current_task['station_id'],
                mode=mode,
                battery_level=battery_level
            )
        else:
            print(f"\n❌ 任务失败: 站点{current_task['station_id']}")
            failed_count += 1
        
        # 短暂延迟后继续下一个任务
        remaining_tasks = task_count - 1  # 当前任务已完成，剩余任务数
        if remaining_tasks > 0:
            print(f"\n⏱️  准备执行下一个任务... (剩余 {remaining_tasks} 个任务)")
            time.sleep(2)
        elif RUN_MODE == "循环模式":
            print("\n🔄 循环模式: 准备重新获取任务列表...")
            time.sleep(2)
    
    # ========== 测试完成统计 ==========
    # 更新小车状态：离线
    update_cart_status(
        online=False,
        current_station=None,
        mode='idle',
        battery_level=battery_level
    )
    
    print_separator()
    print("📊 测试统计:")
    print(f"   🔧 运行模式: {RUN_MODE}")
    print(f"   ✅ 成功完成: {completed_count} 个任务")
    print(f"   ❌ 失败: {failed_count} 个任务")
    print(f"   📈 总计: {completed_count + failed_count} 个任务")
    print(f"   🔋 剩余电量: {battery_level}%")
    print_separator()
    if RUN_MODE == "单圈模式":
        print("✅ 单圈巡检完成")
    else:
        print("⏸️  循环模式已停止")
    print_separator()


if __name__ == "__main__":
    main()

