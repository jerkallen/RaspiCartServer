"""
视觉项目基类
定义所有任务处理器必须实现的标准接口
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path
import yaml


class BaseProject(ABC):
    """任务处理器基类"""
    
    _config_cache: Optional[Dict[str, Any]] = None
    
    @classmethod
    def _load_config(cls, config_path: str = None) -> Dict[str, Any]:
        """
        加载配置文件（带缓存）
        
        Args:
            config_path: 配置文件路径，默认为 api_server/config.yaml
        
        Returns:
            dict: 配置字典
        """
        if cls._config_cache is not None:
            return cls._config_cache
        
        if config_path is None:
            # 默认从 api_server 目录查找 config.yaml
            current_file = Path(__file__)
            config_path = current_file.parent / "config.yaml"
        
        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(config_path, "r", encoding="utf-8") as f:
            cls._config_cache = yaml.safe_load(f)
        
        return cls._config_cache
    
    def get_prompt_from_config(self, prompt_key: str = None) -> str:
        """
        从配置文件获取提示词
        
        Args:
            prompt_key: 提示词键名，如果为None则使用项目名称
        
        Returns:
            str: 提示词内容
        """
        if prompt_key is None:
            prompt_key = self.get_project_name()
        
        config = self._load_config()
        prompts = config.get("prompts", {})
        
        if prompt_key not in prompts:
            raise ValueError(f"配置文件中未找到提示词: {prompt_key}")
        
        prompt = prompts[prompt_key]
        # 如果是字符串，去除首尾空白
        if isinstance(prompt, str):
            return prompt.strip()
        
        return str(prompt).strip()
    
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

