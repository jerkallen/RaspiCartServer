"""
任务3: 烟雾判断A处理器
功能: 判断监测区域A是否存在烟雾
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


class SmokeDetectorAProcessor(BaseProject):
    """烟雾判断A处理器"""
    
    def __init__(self):
        """初始化处理器"""
        try:
            self.dashscope = DashScopeHelper()
        except Exception as e:
            print(f"警告: DashScope初始化失败: {e}")
            self.dashscope = None
    
    def get_project_name(self) -> str:
        """返回项目名称"""
        return "task3_smoke_a"
    
    def get_project_description(self) -> str:
        """返回项目描述"""
        return "任务3: 烟雾判断A"
    
    def get_prompt(self) -> str:
        """获取提示词模板（从配置文件读取）"""
        return self.get_prompt_from_config("task3_smoke_a")
    
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
                "task_type": 3,
                "error": "DashScope服务未初始化",
                "processing_time": 0
            }
        
        images = data.get("images", [])
        params = data.get("params", {})
        station_id = params.get("station_id")
        task_type = params.get("task_type", 3)
        
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
            
            # 根据烟雾情况设置状态
            if result.get("has_smoke", False):
                density = result.get("density", "none")
                if density == "heavy":
                    result["status"] = "danger"
                elif density == "medium":
                    result["status"] = "warning"
                else:
                    result["status"] = "warning"
            else:
                result["status"] = "normal"
            
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
    processor = SmokeDetectorAProcessor()
    print(f"项目名称: {processor.get_project_name()}")
    print(f"项目描述: {processor.get_project_description()}")

