"""
阿里云服务封装模块
包含语音识别和意图解析功能
"""
import os
import json
import base64
from typing import Dict, Any, List, Optional
from pathlib import Path
from dotenv import load_dotenv
import logging

# 加载环境变量
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

logger = logging.getLogger(__name__)

# 导入OpenAI客户端（用于通义千问）
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("openai库未安装，通义千问功能不可用")

# 导入阿里云NLS SDK
try:
    import nls
    NLS_AVAILABLE = True
except ImportError:
    NLS_AVAILABLE = False
    logger.warning("阿里云NLS SDK未安装，语音识别功能不可用")


class SpeechRecognizer:
    """阿里云语音识别服务封装"""
    
    def __init__(self):
        """初始化语音识别服务"""
        if not NLS_AVAILABLE:
            raise RuntimeError("阿里云NLS SDK未安装，无法使用语音识别功能")
        
        # 获取配置
        self.access_key_id = os.getenv("ALIYUN_ACCESS_KEY_ID")
        self.access_key_secret = os.getenv("ALIYUN_ACCESS_KEY_SECRET")
        self.app_key = os.getenv("ALIYUN_APP_KEY")
        
        if not all([self.access_key_id, self.access_key_secret, self.app_key]):
            raise ValueError("缺少阿里云语音识别配置，请检查环境变量")
        
        logger.info("语音识别服务初始化成功")
    
    def recognize_audio(self, audio_data: bytes, format: str = "pcm") -> Dict[str, Any]:
        """
        识别音频文件
        
        Args:
            audio_data: 音频字节数据
            format: 音频格式（pcm/wav/opus等）
        
        Returns:
            识别结果字典，包含text和confidence
        """
        try:
            # 这里使用一次性识别接口
            # 注意：实际使用时需要根据阿里云NLS SDK的具体API进行调整
            
            # 创建识别请求
            url = "https://nls-gateway.cn-shanghai.aliyuncs.com/stream/v1/asr"
            token = self._get_token()
            
            # 简化实现：直接返回模拟结果
            # 实际生产环境需要完整实现SDK调用
            logger.info(f"收到音频识别请求，数据大小: {len(audio_data)} bytes")
            
            # TODO: 实际的SDK调用实现
            # 目前返回提示信息
            return {
                "success": False,
                "text": "",
                "error": "语音识别功能需要完整的阿里云NLS SDK配置",
                "confidence": 0.0
            }
            
        except Exception as e:
            logger.error(f"语音识别失败: {e}")
            return {
                "success": False,
                "text": "",
                "error": str(e),
                "confidence": 0.0
            }
    
    def _get_token(self) -> str:
        """获取访问令牌"""
        # 简化实现
        # 实际需要调用阿里云的Token服务
        return ""


class IntentParser:
    """意图解析服务（基于通义千问文本模型）"""
    
    # 任务映射表
    TASK_MAP = {
        "指针仪表": {"task_type": 1, "station_id": 1, "keywords": ["指针", "仪表", "压力表", "读数"]},
        "温度检测": {"task_type": 2, "station_id": 2, "keywords": ["温度", "高温", "测温", "热"]},
        "烟雾监测A": {"task_type": 3, "station_id": 3, "keywords": ["烟雾A", "烟A", "站点3"]},
        "烟雾监测B": {"task_type": 4, "station_id": 4, "keywords": ["烟雾B", "烟B", "站点4"]},
        "物品描述": {"task_type": 5, "station_id": 5, "keywords": ["物品", "物体", "识别", "描述"]}
    }
    
    def __init__(self):
        """初始化意图解析服务"""
        if not OPENAI_AVAILABLE:
            raise RuntimeError("openai库未安装，无法使用通义千问")
        
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("未找到DASHSCOPE_API_KEY环境变量")
        
        base_url = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        self.client = OpenAI(api_key=self.api_key, base_url=base_url)
        self.model = "qwen-plus"
        
        logger.info("意图解析服务初始化成功")
    
    def parse_intent(self, user_input: str) -> Dict[str, Any]:
        """
        解析用户意图，提取任务列表
        
        Args:
            user_input: 用户输入的文本
        
        Returns:
            解析结果，包含tasks列表
        """
        try:
            # 构造提示词
            prompt = self._build_prompt(user_input)
            
            # 调用通义千问
            messages = [
                {
                    "role": "system",
                    "content": "你是一个智能巡检系统的任务解析助手。你的职责是理解用户的检查需求，并将其转换为具体的任务列表。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,
                stream=False
            )
            
            response_text = response.choices[0].message.content or ""
            logger.info(f"意图解析响应: {response_text}")
            
            # 解析JSON响应
            tasks = self._parse_response(response_text)
            
            return {
                "success": True,
                "tasks": tasks,
                "original_input": user_input
            }
            
        except Exception as e:
            logger.error(f"意图解析失败: {e}")
            # 降级方案：使用关键词匹配
            return self._fallback_parse(user_input)
    
    def _build_prompt(self, user_input: str) -> str:
        """构造提示词"""
        prompt = f"""
请分析用户的检查需求，并返回需要执行的任务列表。

系统支持的任务类型：
1. 任务1 - 指针仪表读数（站点1）：检查指针式压力表的读数
2. 任务2 - 温度检测（站点2）：检测高温物体
3. 任务3 - 烟雾监测A（站点3）：监测烟雾情况
4. 任务4 - 烟雾监测B（站点4）：监测烟雾情况
5. 任务5 - 物品描述（站点5）：识别和描述物品

用户输入："{user_input}"

请理解用户意图，提取需要执行的任务。例如：
- "检查压力表和温度" -> 任务1和任务2
- "检查站点1和站点5" -> 任务1和任务5
- "全部检查一遍" -> 全部5个任务
- "烟雾检测" -> 任务3和任务4

请严格按照以下JSON格式返回，不要添加任何其他内容：
{{
  "tasks": [
    {{"task_type": 1, "station_id": 1}},
    {{"task_type": 2, "station_id": 2}}
  ]
}}
"""
        return prompt
    
    def _parse_response(self, response_text: str) -> List[Dict[str, int]]:
        """解析模型响应"""
        # 去除可能的markdown代码块
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        
        try:
            data = json.loads(response_text)
            tasks = data.get("tasks", [])
            
            # 验证任务格式
            valid_tasks = []
            for task in tasks:
                if isinstance(task, dict) and "task_type" in task and "station_id" in task:
                    task_type = int(task["task_type"])
                    station_id = int(task["station_id"])
                    if 1 <= task_type <= 5 and 1 <= station_id <= 5:
                        valid_tasks.append({
                            "task_type": task_type,
                            "station_id": station_id
                        })
            
            return valid_tasks
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"JSON解析失败: {e}, 原始响应: {response_text}")
            raise ValueError(f"无法解析模型响应: {e}")
    
    def _fallback_parse(self, user_input: str) -> Dict[str, Any]:
        """降级方案：使用关键词匹配"""
        logger.info("使用关键词匹配进行意图解析")
        
        user_input_lower = user_input.lower()
        tasks = []
        
        # 检查是否要求全部检查
        if any(keyword in user_input_lower for keyword in ["全部", "所有", "全面", "完整"]):
            tasks = [
                {"task_type": 1, "station_id": 1},
                {"task_type": 2, "station_id": 2},
                {"task_type": 3, "station_id": 3},
                {"task_type": 4, "station_id": 4},
                {"task_type": 5, "station_id": 5}
            ]
        else:
            # 关键词匹配
            for task_name, task_info in self.TASK_MAP.items():
                keywords = task_info["keywords"]
                if any(keyword in user_input for keyword in keywords):
                    tasks.append({
                        "task_type": task_info["task_type"],
                        "station_id": task_info["station_id"]
                    })
            
            # 检查站点号
            for i in range(1, 6):
                if f"站点{i}" in user_input or f"站点 {i}" in user_input:
                    # 确保该站点的任务被添加
                    task_exists = any(t["station_id"] == i for t in tasks)
                    if not task_exists:
                        tasks.append({
                            "task_type": i,
                            "station_id": i
                        })
        
        # 去重
        unique_tasks = []
        seen = set()
        for task in tasks:
            key = (task["task_type"], task["station_id"])
            if key not in seen:
                seen.add(key)
                unique_tasks.append(task)
        
        return {
            "success": True,
            "tasks": unique_tasks,
            "original_input": user_input,
            "method": "fallback"
        }


# 测试代码
if __name__ == "__main__":
    # 测试意图解析
    parser = IntentParser()
    
    test_inputs = [
        "检查压力表和物品识别",
        "检查站点1和站点5",
        "全部检查一遍",
        "温度和烟雾"
    ]
    
    for user_input in test_inputs:
        print(f"\n输入: {user_input}")
        result = parser.parse_intent(user_input)
        print(f"结果: {json.dumps(result, ensure_ascii=False, indent=2)}")

