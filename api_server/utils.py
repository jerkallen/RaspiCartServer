"""
工具函数模块
包含图片保存、DashScope调用等辅助功能
"""
import os
import base64
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from io import BytesIO
import numpy as np
from PIL import Image
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# DashScope客户端
try:
    from openai import OpenAI
    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False
    print("警告: openai库未安装，DashScope功能不可用")


class DashScopeHelper:
    """DashScope辅助类"""
    
    def __init__(self):
        """初始化DashScope客户端"""
        if not DASHSCOPE_AVAILABLE:
            raise RuntimeError("openai库未安装，无法使用DashScope")
        
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("未找到DASHSCOPE_API_KEY环境变量")
        
        base_url = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        self.client = OpenAI(api_key=self.api_key, base_url=base_url)
        self.default_model = "qwen-vl-plus"
    
    def numpy_to_base64_data_uri(self, image_array: np.ndarray) -> str:
        """
        将numpy数组转换为base64编码的data URI
        
        Args:
            image_array: numpy图片数组
            
        Returns:
            base64编码的data URI字符串
        """
        # 转换为PIL Image
        if len(image_array.shape) == 2:
            pil_image = Image.fromarray(image_array, mode='L')
        elif len(image_array.shape) == 3:
            if image_array.shape[2] == 3:
                pil_image = Image.fromarray(image_array, mode='RGB')
            elif image_array.shape[2] == 4:
                pil_image = Image.fromarray(image_array, mode='RGBA')
            else:
                raise ValueError(f"不支持的图片通道数: {image_array.shape[2]}")
        else:
            raise ValueError(f"不支持的图片形状: {image_array.shape}")
        
        # 转换为字节
        buffer = BytesIO()
        pil_image.save(buffer, format='PNG')
        image_bytes = buffer.getvalue()
        
        # 编码为base64
        base64_data = base64.b64encode(image_bytes).decode('utf-8')
        return f"data:image/png;base64,{base64_data}"
    
    def call_vision_model(self, text: str, image_array: np.ndarray, model: str = None) -> str:
        """
        调用视觉语言模型
        
        Args:
            text: 提示词
            image_array: 图片数组
            model: 模型名称（可选）
        
        Returns:
            模型返回的文本
        """
        if model is None:
            model = self.default_model
        
        # 转换图片为base64
        image_url = self.numpy_to_base64_data_uri(image_array)
        
        # 构造消息
        messages = [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": image_url}},
                {"type": "text", "text": text}
            ]
        }]
        
        # 调用模型
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            stream=False
        )
        
        return response.choices[0].message.content or ""
    
    def parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        解析JSON响应（处理可能的markdown代码块）
        
        Args:
            response: 模型返回的响应文本
        
        Returns:
            解析后的JSON对象
        """
        # 去除可能的markdown代码块
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        
        response = response.strip()
        
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON解析失败: {e}\n原始响应: {response}")


def save_image(image_array: np.ndarray, task_type: int, station_id: int) -> Dict[str, Any]:
    """
    保存图片到磁盘
    
    Args:
        image_array: 图片数组
        task_type: 任务类型
        station_id: 站点ID
    
    Returns:
        包含保存信息的字典
    """
    # 创建日期目录
    today = datetime.now().strftime("%Y-%m-%d")
    save_dir = Path(f"../data/images/{today}/task{task_type}")
    save_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成文件名
    timestamp = datetime.now().strftime("%H%M%S")
    filename = f"station{station_id:02d}_{timestamp}.jpg"
    filepath = save_dir / filename
    
    # 保存图片
    pil_image = Image.fromarray(image_array)
    pil_image.save(str(filepath), quality=95)
    
    # 返回相对路径
    relative_path = f"data/images/{today}/task{task_type}/{filename}"
    
    return {
        "saved": True,
        "path": relative_path,
        "absolute_path": str(filepath.absolute())
    }


def determine_status(value: float, thresholds: Dict[str, float]) -> str:
    """
    根据阈值判断状态
    
    Args:
        value: 数值
        thresholds: 阈值字典，包含warning和danger
    
    Returns:
        状态字符串: normal/warning/danger
    """
    if value >= thresholds.get("danger", float('inf')):
        return "danger"
    elif value >= thresholds.get("warning", float('inf')):
        return "warning"
    else:
        return "normal"

