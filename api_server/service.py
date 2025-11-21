"""
BentoML服务入口 - 智能巡检系统API服务
统一处理路由: POST /api/process
"""
import bentoml
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from PIL import Image
from datetime import datetime
import json

from loader import get_all_active_projects, format_response

# 配置日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 创建日志格式
formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# 确保 log 文件夹存在
log_dir = Path('../data/logs')
log_dir.mkdir(parents=True, exist_ok=True)

# 轮转文件处理器
file_handler = RotatingFileHandler(
    filename=str(log_dir / 'bentoml.log'),
    maxBytes=5 * 1024 * 1024,  # 5MB
    backupCount=50,
    encoding='utf-8'
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

# 添加处理器
logger.addHandler(console_handler)
logger.addHandler(file_handler)


# 请求模型定义
class ProcessRequest(BaseModel):
    """处理请求模型"""
    task_type: int = Field(..., description="任务类型（1-4）", ge=1, le=4)
    station_id: int = Field(..., description="站点ID", ge=1)
    params: Optional[str] = Field(None, description="额外参数（JSON字符串）")


# 加载所有启用的项目
try:
    active_projects = get_all_active_projects()
    logger.info(f"成功加载 {len(active_projects)} 个任务处理器")
except Exception as e:
    logger.error(f"加载任务处理器失败: {e}")
    active_projects = {}


@bentoml.service(
    name="inspection_api_service",
    http={
        "timeout": 300,
        "keepalive_timeout": 60,
        "max_keepalive_connections": 100,
        "limit_concurrency": 200,
    }
)
class InspectionAPIService:
    """智能巡检API服务"""
    
    def __init__(self):
        """初始化服务"""
        self.projects = active_projects
        
        logger.info(f"\n{'='*60}")
        logger.info("智能巡检API服务启动")
        logger.info(f"已加载 {len(self.projects)} 个任务处理器:")
        for name, info in self.projects.items():
            config = info["config"]
            logger.info(f"  - {name}: {config.get('description')}")
        logger.info(f"{'='*60}\n")
    
    @bentoml.api(route="/health")
    def health(self) -> Dict[str, Any]:
        """健康检查端点"""
        logger.info("收到健康检查请求 /health")
        return {
            "status": "healthy",
            "service": "inspection_api_service",
            "processors": list(self.projects.keys()),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    @bentoml.api(route="/api/process")
    async def process(
        self,
        image: Image.Image,
        task_type: int,
        station_id: int,
        params: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        统一处理路由
        
        Args:
            image: 上传的图片
            task_type: 任务类型（1-4）
            station_id: 站点ID
            params: 额外参数（JSON字符串）
        
        Returns:
            处理结果
        """
        # 记录请求信息
        image_info = f"图片尺寸: {image.size}, 模式: {image.mode}" if image else "无图片"
        logger.info(f"收到处理请求 -> 任务类型: {task_type}, 站点ID: {station_id}, {image_info}")
        
        # 验证任务类型
        if task_type not in [1, 2, 3, 4]:
            logger.warning(f"无效的任务类型: {task_type}")
            return format_response(
                "error",
                error="无效的任务类型，必须是1-4之间的整数",
                error_code="INVALID_TASK_TYPE"
            )
        
        # 根据任务类型选择处理器
        task_map = {
            1: "task1_pointer_reader",
            2: "task2_temperature",
            3: "task3_smoke_a",
            4: "task4_smoke_b"
        }
        
        project_name = task_map[task_type]
        
        if project_name not in self.projects:
            logger.error(f"任务处理器 '{project_name}' 未加载")
            return format_response(
                "error",
                error=f"任务处理器未加载: {project_name}",
                error_code="PROCESSOR_NOT_FOUND"
            )
        
        # 解析额外参数
        extra_params = {}
        if params:
            try:
                extra_params = json.loads(params)
            except json.JSONDecodeError as e:
                logger.warning(f"参数JSON解析失败: {e}")
                return format_response(
                    "error",
                    error=f"参数JSON格式错误: {str(e)}",
                    error_code="INVALID_JSON"
                )
        
        # 将PIL Image转换为字节
        from io import BytesIO
        img_bytes = BytesIO()
        image.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        files = [img_bytes.read()]
        
        # 构造处理参数
        process_params = {
            "task_type": task_type,
            "station_id": station_id,
            **extra_params
        }
        
        # 调用处理器
        try:
            project_info = self.projects[project_name]
            handler = project_info["handler"]
            result = handler(files=files, params=process_params)
            
            # 记录处理结果
            status = result.get("status", "unknown")
            logger.info(f"处理完成 -> 任务类型: {task_type}, 站点ID: {station_id}, 状态: {status}")
            
            return result
            
        except Exception as e:
            logger.error(f"处理失败 -> 任务类型: {task_type}, 错误: {str(e)}")
            return format_response(
                "error",
                error=str(e),
                error_code="PROCESSING_FAILED"
            )

