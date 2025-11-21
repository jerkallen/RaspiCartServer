"""
任务1: 指针仪表读数处理器
功能: 识别指针式仪表的读数
"""
import sys
from pathlib import Path
import time

# 添加服务器根目录到路径
server_root = Path(__file__).parent.parent
sys.path.insert(0, str(server_root))

from base_project import BaseProject
from utils import DashScopeHelper, save_image
from typing import Dict, Any


class PointerReaderProcessor(BaseProject):
    """指针仪表读数处理器"""
    
    def __init__(self):
        """初始化处理器"""
        try:
            self.dashscope = DashScopeHelper()
        except Exception as e:
            print(f"警告: DashScope初始化失败: {e}")
            self.dashscope = None
    
    def get_project_name(self) -> str:
        """返回项目名称"""
        return "task1_pointer_reader"
    
    def get_project_description(self) -> str:
        """返回项目描述"""
        return "任务1: 指针式仪表读数识别"
    
    def get_prompt(self) -> str:
        """获取提示词模板"""
        return """请读取这个指针式仪表的数值。

分析步骤：
1. 识别表盘的量程范围（最小值到最大值）
2. 识别表盘的刻度间隔
3. 确定指针的精确位置
4. 计算读数（保留2位小数）

返回格式（纯JSON，无其他文字）：
{
    "value": 读数值,
    "unit": "单位（如MPa、℃等）",
    "min_range": 最小刻度,
    "max_range": 最大刻度,
    "confidence": 置信度(0-1),
    "status": "normal/warning/danger"
}

注意：如果指针不清晰或表盘损坏，confidence设为低值并在status中标注warning"""
    
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """
        验证输入数据格式
        
        Args:
            data: 待验证的输入数据
        
        Returns:
            bool: 数据是否有效
        """
        # 必须有图片
        images = data.get("images", [])
        if not images:
            return False
        
        # 必须有station_id
        params = data.get("params", {})
        if "station_id" not in params:
            return False
        
        return True
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        核心处理方法
        
        Args:
            data: 输入数据字典
                - images: list[np.ndarray] - 图片数组列表
                - params: dict - 参数
                    - station_id: int - 站点ID
                    - task_type: int - 任务类型
        
        Returns:
            dict: 处理结果
        """
        start_time = time.time()
        
        if self.dashscope is None:
            return {
                "task_type": 1,
                "error": "DashScope服务未初始化",
                "processing_time": 0
            }
        
        images = data.get("images", [])
        params = data.get("params", {})
        station_id = params.get("station_id")
        task_type = params.get("task_type", 1)
        
        # 使用第一张图片
        image_array = images[0]
        
        try:
            # 保存图片
            save_result = save_image(image_array, task_type, station_id)
            
            # 调用DashScope模型
            prompt = self.get_prompt()
            response_text = self.dashscope.call_vision_model(prompt, image_array)
            
            # 解析JSON响应
            result = self.dashscope.parse_json_response(response_text)
            
            # 计算处理时间
            processing_time = time.time() - start_time
            
            return {
                "task_type": task_type,
                "station_id": station_id,
                "result": result,
                "processing_time": round(processing_time, 2),
                "image_saved": save_result["saved"],
                "image_path": save_result["path"]
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            return {
                "task_type": task_type,
                "station_id": station_id,
                "error": str(e),
                "processing_time": round(processing_time, 2),
                "image_saved": save_result.get("saved", False) if 'save_result' in locals() else False
            }


if __name__ == "__main__":
    # 简单测试
    processor = PointerReaderProcessor()
    print(f"项目名称: {processor.get_project_name()}")
    print(f"项目描述: {processor.get_project_description()}")

