"""
BentoML服务测试脚本
用于测试API服务是否正常工作
"""
import os
import sys
import requests
from pathlib import Path
from PIL import Image, ImageDraw
import io
import json
import yaml
import time
import base64

# 添加当前目录到路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))


def get_base_url(config_path: str = "config.yaml"):
    """
    根据配置文件获取服务基础URL
    
    Args:
        config_path: 配置文件路径
    
    Returns:
        str: 基础URL（如 "http://127.0.0.1:3000"）
    """
    try:
        config_file = current_dir / config_path
        if not config_file.exists():
            print(f"警告: 配置文件不存在 {config_path}，使用默认地址")
            return "http://127.0.0.1:3000"
        
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        # 获取服务器配置
        server_config = config.get("server", {})
        host = server_config.get("host", "0.0.0.0")
        port = server_config.get("port", 3000)
        
        # 如果 host 是 0.0.0.0，使用 127.0.0.1 进行连接
        if host == "0.0.0.0":
            host = "127.0.0.1"
        
        return f"http://{host}:{port}"
    except Exception as e:
        print(f"警告: 读取配置失败 {e}，使用默认地址")
        return "http://127.0.0.1:3000"


def test_health(base_url="http://127.0.0.1:3000", session=None):
    """测试健康检查端点"""
    print("\n=== 测试健康检查端点 ===")
    
    try:
        # 记录开始时间
        start_time = time.time()
        # 使用session复用连接可以大幅提升响应速度
        client = session if session else requests
        response = client.post(f"{base_url}/health")
        elapsed = time.time() - start_time
        
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {result}")
        print(f"响应时间: {elapsed*1000:.1f} ms")
        return response.status_code == 200
    except Exception as e:
        print(f"错误: {e}")
        return False


def create_test_image():
    """创建测试图片，返回字节数据"""
    # 创建一个简单的测试图片（白色背景，黑色圆圈）
    img = Image.new('RGB', (400, 300), color='white')
    draw = ImageDraw.Draw(img)
    draw.ellipse([150, 100, 250, 200], outline='black', width=3)
    draw.line([200, 150, 220, 130], fill='black', width=2)  # 指针
    
    # 转换为字节
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes.read()


def test_process_task1(base_url="http://127.0.0.1:3000", session=None):
    """测试任务1: 指针仪表读数"""
    print("\n=== 测试任务1: 指针仪表读数 ===")
    
    try:
        # 使用根目录的测试图片
        test_image_path = current_dir.parent / "meter_test.jpg"
        if not test_image_path.exists():
            print(f"警告: 测试图片不存在 {test_image_path}，使用生成的测试图片")
            img_data = create_test_image()
            filename = 'test.png'
        else:
            print(f"使用测试图片: {test_image_path}")
            with open(test_image_path, 'rb') as f:
                img_data = f.read()
            filename = test_image_path.name
        
        # 准备请求 - 使用base64编码和JSON格式
        img_base64 = base64.b64encode(img_data).decode('utf-8')
        
        json_data = {
            'image_base64': img_base64,
            'task_type': 1,
            'station_id': 1
        }
        
        # 使用session复用连接，发送JSON请求
        client = session if session else requests
        response = client.post(
            f"{base_url}/api/process",
            json=json_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {result}")
        
        if result.get('status') == 'success':
            result_data = result.get('result', {})
            print(f"任务类型: {result_data.get('task_type')}")
            print(f"工位ID: {result_data.get('station_id')}")
            if 'reading' in result_data:
                print(f"读数: {result_data['reading']}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"错误: {e}")
        return False


def test_process_task2(base_url="http://127.0.0.1:3000", session=None):
    """测试任务2: 高温物体检测"""
    print("\n=== 测试任务2: 高温物体检测 ===")
    
    try:
        # 使用根目录的测试图片
        test_image_path = current_dir.parent / "somke_test.jpg"
        if not test_image_path.exists():
            print(f"警告: 测试图片不存在 {test_image_path}，使用生成的测试图片")
            img_data = create_test_image()
            filename = 'test.png'
        else:
            print(f"使用测试图片: {test_image_path}")
            with open(test_image_path, 'rb') as f:
                img_data = f.read()
            filename = test_image_path.name
        
        # 准备请求 - 使用base64编码和JSON格式
        img_base64 = base64.b64encode(img_data).decode('utf-8')
        
        params_dict = {
            'max_temperature': 75.5,
            'avg_temperature': 45.2,
            'ambient_temperature': 25.0
        }
        params_str = json.dumps(params_dict)
        
        json_data = {
            'image_base64': img_base64,
            'task_type': 2,
            'station_id': 5,
            'params': params_str
        }
        
        # 使用session复用连接，发送JSON请求
        client = session if session else requests
        response = client.post(
            f"{base_url}/api/process",
            json=json_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {result}")
        
        if result.get('status') == 'success':
            result_data = result.get('result', {})
            print(f"任务类型: {result_data.get('task_type')}")
            print(f"工位ID: {result_data.get('station_id')}")
            if 'is_abnormal' in result_data:
                print(f"是否异常: {result_data['is_abnormal']}")
                print(f"最高温度: {result_data.get('max_temperature')}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"错误: {e}")
        return False


def main():
    """主函数"""
    print("="*60)
    print("BentoML服务测试")
    print("="*60)
    
    # 根据配置文件获取基础URL
    base_url = get_base_url()
    print(f"\n服务地址: {base_url}")
    print("确保服务已启动")
    print("="*60)
    
    # 使用 Session 复用连接可以大幅提升性能
    session = requests.Session()
    
    with session:
        results = []
        
        # 测试健康检查
        results.append(("健康检查", test_health(base_url, session)))
        
        # 测试任务1
        results.append(("任务1", test_process_task1(base_url, session)))
        
        # 测试任务2
        results.append(("任务2", test_process_task2(base_url, session)))
        
        # 显示测试结果
        print("\n" + "="*60)
        print("测试结果汇总")
        print("="*60)
        for name, result in results:
            status = "✓ 通过" if result else "✗ 失败"
            print(f"{name}: {status}")
        
        passed = sum(1 for _, r in results if r)
        total = len(results)
        print(f"\n总计: {passed}/{total} 通过")
        
        if passed == total:
            print("\n所有测试通过！")
        else:
            print("\n部分测试失败，请检查服务是否正常运行。")


if __name__ == "__main__":
    main()

