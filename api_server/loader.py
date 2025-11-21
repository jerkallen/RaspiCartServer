"""
项目加载器
职责：配置管理 + 项目加载 + 路由注册
"""
import sys
import yaml
import importlib.util
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import numpy as np
from PIL import Image
from io import BytesIO

from base_project import BaseProject


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    加载配置文件
    
    Args:
        config_path: 配置文件路径
    
    Returns:
        dict: 配置字典
    """
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config


def resolve_project_path(path: str, base_dir: str = None) -> str:
    """
    解析项目路径（相对路径转为绝对路径）
    
    Args:
        path: 项目路径（绝对或相对）
        base_dir: 基准目录（默认为当前目录）
    
    Returns:
        str: 绝对路径
    """
    project_path = Path(path)
    
    if project_path.is_absolute():
        return str(project_path.resolve())
    
    if base_dir is None:
        base_dir = Path.cwd()
    else:
        base_dir = Path(base_dir)
    
    return str((base_dir / project_path).resolve())


def load_project_from_path(project_path: str, project_name: str) -> BaseProject:
    """
    从指定路径动态加载项目
    
    Args:
        project_path: 项目目录路径
        project_name: 项目名称
    
    Returns:
        BaseProject: 项目实例
    """
    project_dir = Path(project_path)
    
    if not project_dir.exists():
        raise FileNotFoundError(f"项目路径不存在: {project_path}")
    
    # 将项目目录添加到sys.path
    project_dir_str = str(project_dir)
    if project_dir_str not in sys.path:
        sys.path.insert(0, project_dir_str)
    
    # 导入processor模块
    processor_path = project_dir / "processor.py"
    if not processor_path.exists():
        raise FileNotFoundError(f"找不到processor.py: {processor_path}")
    
    spec = importlib.util.spec_from_file_location(
        f"{project_name}_processor",
        processor_path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # 查找继承自BaseProject的类
    project_class = None
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if (isinstance(attr, type) and 
            issubclass(attr, BaseProject) and 
            attr != BaseProject):
            project_class = attr
            break
    
    if project_class is None:
        raise ValueError(f"在{processor_path}中找不到继承自BaseProject的类")
    
    return project_class()


def get_all_active_projects(config_path: str = "config.yaml") -> Dict[str, Dict[str, Any]]:
    """
    获取所有启用的项目实例
    
    Args:
        config_path: 配置文件路径
    
    Returns:
        dict: {项目名称: {instance: 项目实例, config: 项目配置, handler: 处理函数}}
    """
    config = load_config(config_path)
    projects = {}
    
    for project_config in config.get("projects", []):
        if not project_config.get("enabled", False):
            continue
        
        name = project_config["name"]
        project_path = project_config.get("project_path")
        
        if not project_path:
            raise ValueError(f"项目 {name} 缺少 project_path 配置")
        
        # 解析项目路径
        resolved_path = resolve_project_path(project_path)
        
        # 加载项目
        project_instance = load_project_from_path(resolved_path, name)
        
        # 创建项目信息字典
        project_info = {
            "instance": project_instance,
            "config": project_config
        }
        
        # 创建handler
        project_info["handler"] = create_route_handler(project_info)
        
        projects[name] = project_info
    
    return projects


def parse_request_data(files: Optional[list] = None, 
                       params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    解析请求数据
    
    Args:
        files: 上传的文件列表
        params: JSON参数
    
    Returns:
        dict: 统一格式的数据字典
    """
    data = {
        "images": [],
        "params": params or {}
    }
    
    if files:
        for file_data in files:
            # 将文件转换为numpy数组
            img = Image.open(BytesIO(file_data))
            img_array = np.array(img)
            data["images"].append(img_array)
    
    return data


def format_response(status: str, data: Any = None, error: str = None, error_code: str = None) -> Dict[str, Any]:
    """
    格式化统一响应
    
    Args:
        status: 状态 ("success" 或 "error")
        data: 响应数据
        error: 错误信息
        error_code: 错误代码
    
    Returns:
        dict: 格式化的响应
    """
    response = {
        "status": status,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    if status == "success":
        response["data"] = data
    else:
        response["error"] = {
            "code": error_code or "UNKNOWN_ERROR",
            "message": error or "处理失败"
        }
    
    return response


def create_route_handler(project_info: Dict[str, Any]):
    """
    为项目创建路由处理函数
    
    Args:
        project_info: 项目信息字典，包含instance和config
    
    Returns:
        function: 路由处理函数
    """
    project_instance = project_info["instance"]
    
    def handler(files: Optional[list] = None, 
                params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        路由处理函数
        """
        try:
            # 解析请求数据
            data = parse_request_data(files, params)
            
            # 验证输入
            if not project_instance.validate_input(data):
                return format_response("error", error="输入数据验证失败", error_code="INVALID_INPUT")
            
            # 调用项目处理方法
            result = project_instance.process(data)
            
            return format_response("success", data=result)
            
        except Exception as e:
            return format_response("error", error=str(e), error_code="PROCESSING_FAILED")
    
    return handler

