"""
视觉项目基类
定义所有任务处理器必须实现的标准接口
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseProject(ABC):
    """任务处理器基类"""
    
    @abstractmethod
    def get_project_name(self) -> str:
        """
        返回项目名称
        
        Returns:
            str: 项目标识符
        """
        pass
    
    @abstractmethod
    def get_project_description(self) -> str:
        """
        返回项目描述
        
        Returns:
            str: 项目功能描述
        """
        pass
    
    @abstractmethod
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        核心处理方法
        
        Args:
            data: 输入数据字典
                - images: list[np.ndarray] - 图片数组列表（如果上传了图片）
                - params: dict - JSON参数（如果提供了参数）
                - task_type: int - 任务类型（1-4）
                - station_id: int - 站点ID
        
        Returns:
            dict: 处理结果（必须可JSON序列化）
        """
        pass
    
    @abstractmethod
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """
        验证输入数据格式
        
        Args:
            data: 待验证的输入数据
        
        Returns:
            bool: 数据是否有效
        """
        pass

