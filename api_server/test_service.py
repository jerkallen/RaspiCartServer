"""
BentoML服务测试脚本
用于测试API服务是否正常工作
"""
import os
import sys
import requests
from pathlib import Path
from PIL import Image
import io

# 添加当前目录到路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))


def test_health():
    """测试健康检查端点"""
    print("\n=== 测试健康检查端点 ===")
    url = "http://127.0.0.1:3000/health"
    
    try:
        response = requests.get(url)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"错误: {e}")
        return False


def create_test_image():
    """创建测试图片"""
    from PIL import Image, ImageDraw
    import io
    
    # 创建一个简单的测试图片（白色背景，黑色圆圈）
    img = Image.new('RGB', (400, 300), color='white')
    draw = ImageDraw.Draw(img)
    draw.ellipse([150, 100, 250, 200], outline='black', width=3)
    draw.line([200, 150, 220, 130], fill='black', width=2)  # 指针
    
    # 转换为字节
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes


def test_process_task1():
    """测试任务1: 指针仪表读数"""
    print("\n=== 测试任务1: 指针仪表读数 ===")
    url = "http://127.0.0.1:3000/api/process"
    
    # 创建测试图片
    img_bytes = create_test_image()
    
    # 准备请求
    files = {
        'image': ('test.png', img_bytes, 'image/png')
    }
    data = {
        'task_type': 1,
        'station_id': 1
    }
    
    try:
        response = requests.post(url, files=files, data=data)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"错误: {e}")
        return False


def test_process_task2():
    """测试任务2: 高温物体检测"""
    print("\n=== 测试任务2: 高温物体检测 ===")
    url = "http://127.0.0.1:3000/api/process"
    
    # 创建测试图片
    img_bytes = create_test_image()
    
    # 准备请求（包含温度数据）
    import json
    files = {
        'image': ('test.png', img_bytes, 'image/png')
    }
    data = {
        'task_type': 2,
        'station_id': 5,
        'params': json.dumps({
            'max_temperature': 75.5,
            'avg_temperature': 45.2,
            'ambient_temperature': 25.0
        })
    }
    
    try:
        response = requests.post(url, files=files, data=data)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"错误: {e}")
        return False


def main():
    """主函数"""
    print("="*60)
    print("BentoML服务测试")
    print("="*60)
    print("\n确保服务已启动在 http://127.0.0.1:3000")
    input("按Enter键开始测试...")
    
    results = []
    
    # 测试健康检查
    results.append(("健康检查", test_health()))
    
    # 测试任务1
    results.append(("任务1", test_process_task1()))
    
    # 测试任务2
    results.append(("任务2", test_process_task2()))
    
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


if __name__ == "__main__":
    main()

