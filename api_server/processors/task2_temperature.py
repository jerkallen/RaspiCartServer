"""
任务2: 高温物体检测处理器
功能: 处理温度数据（不调用大模型）
"""
import sys
from pathlib import Path
import time

# 添加服务器根目录到路径
server_root = Path(__file__).parent.parent
sys.path.insert(0, str(server_root))

from base_project import BaseProject
from utils import save_image, determine_status
from typing import Dict, Any


class TemperatureProcessor(BaseProject):
    """高温物体检测处理器"""
    
    # 温度阈值
    THRESHOLDS = {
        "warning": 60.0,
        "danger": 80.0
    }
    
    def get_project_name(self) -> str:
        """返回项目名称"""
        return "task2_temperature"
    
    def get_project_description(self) -> str:
        """返回项目描述"""
        return "任务2: 高温物体检测"
    
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
        
        # 必须有参数
        params = data.get("params", {})
        if "station_id" not in params:
            return False
        
        # 必须有温度数据
        if "max_temperature" not in params:
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
                    - max_temperature: float - 最高温度
                    - avg_temperature: float - 平均温度（可选）
                    - ambient_temperature: float - 环境温度（可选）
        
        Returns:
            dict: 处理结果
        """
        start_time = time.time()
        
        images = data.get("images", [])
        params = data.get("params", {})
        station_id = params.get("station_id")
        task_type = params.get("task_type", 2)
        
        max_temp = params.get("max_temperature")
        avg_temp = params.get("avg_temperature", None)
        ambient_temp = params.get("ambient_temperature", None)
        
        # 使用第一张图片
        image_array = images[0]
        
        try:
            # 保存图片
            save_result = save_image(image_array, task_type, station_id)
            
            # 判断状态
            status = determine_status(max_temp, self.THRESHOLDS)
            
            # 构造结果
            result = {
                "max_temperature": max_temp,
                "status": status,
                "threshold_warning": self.THRESHOLDS["warning"],
                "threshold_danger": self.THRESHOLDS["danger"]
            }
            
            if avg_temp is not None:
                result["avg_temperature"] = avg_temp
            
            if ambient_temp is not None:
                result["ambient_temperature"] = ambient_temp
            
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
    processor = TemperatureProcessor()
    print(f"项目名称: {processor.get_project_name()}")
    print(f"项目描述: {processor.get_project_description()}")

