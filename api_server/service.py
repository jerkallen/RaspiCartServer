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
import base64
from io import BytesIO
import sys
import time
import requests
from concurrent.futures import ThreadPoolExecutor

from loader import get_all_active_projects, format_response

# 添加项目根目录到路径，以便导入数据库管理器
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.db_manager import DatabaseManager

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
        
        # 初始化数据库管理器
        try:
            self.db = DatabaseManager()
            logger.info("数据库管理器初始化成功")
        except Exception as e:
            logger.error(f"数据库管理器初始化失败: {e}")
            self.db = None
        
        # 初始化后台任务处理线程池
        self.executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="task_processor")
        logger.info("后台任务处理线程池初始化成功（最大工作线程数: 10）")
        
        logger.info(f"\n{'='*60}")
        logger.info("智能巡检API服务启动")
        logger.info(f"已加载 {len(self.projects)} 个任务处理器:")
        for name, info in self.projects.items():
            config = info["config"]
            logger.info(f"  - {name}: {config.get('description')}")
        logger.info(f"{'='*60}\n")
    
    def _process_task_in_background(
        self,
        image_bytes: bytes,
        task_type: int,
        station_id: int,
        project_name: str,
        extra_params: dict,
        record_id: int
    ):
        """
        后台处理任务的函数（仅负责图片识别和更新结果）
        
        Args:
            image_bytes: 图片字节数据
            task_type: 任务类型
            station_id: 站点ID
            project_name: 项目名称
            extra_params: 额外参数
            record_id: 数据库记录ID（用于后续更新结果）
        """
        try:
            # 重新打开图片（在新线程中）
            image = Image.open(BytesIO(image_bytes))
            
            # 转换为字节供处理器使用
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
            
            logger.info(f"[后台处理] 开始处理 -> 任务类型: {task_type}, 站点ID: {station_id}, 记录ID: {record_id}")
            
            # 调用处理器
            project_info = self.projects[project_name]
            handler = project_info["handler"]
            result = handler(files=files, params=process_params)
            
            # 记录处理结果
            status = result.get("status", "unknown")
            logger.info(f"[后台处理] 处理完成 -> 任务类型: {task_type}, 站点ID: {station_id}, 状态: {status}")
            
            # 更新数据库记录
            if self.db and status == "success":
                try:
                    # 提取结果数据
                    result_data = result.get("data", {})
                    result_info = result_data.get("result", {})
                    image_path = result_data.get("image_path", "")
                    processing_time = result_data.get("processing_time", 0)
                    
                    # 获取状态和置信度
                    item_status = result_info.get("status", "normal")
                    confidence = result_info.get("confidence", None)
                    
                    # 更新任务记录
                    self.db.update_task_record(
                        record_id,
                        result_data=result_info,
                        image_path=image_path,
                        status=item_status,
                        confidence=confidence,
                        processing_time=processing_time
                    )
                    logger.info(f"[后台处理] 任务记录已更新 -> record_id: {record_id}")
                    
                    # 通知Web服务推送WebSocket消息
                    self._notify_web_service({
                        'task_type': task_type,
                        'station_id': station_id,
                        'result': result_info,
                        'image_path': image_path,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    
                except Exception as db_error:
                    logger.error(f"[后台处理] 更新数据库失败 -> record_id: {record_id}, 错误: {db_error}")
                    # 更新失败时，标记为处理失败
                    try:
                        self.db.update_task_record(record_id, status="failed")
                    except:
                        pass
            elif status != "success":
                # 处理失败，更新状态
                try:
                    error_info = result.get("error", "未知错误")
                    self.db.update_task_record(
                        record_id,
                        status="failed",
                        result_data={'error': error_info}
                    )
                    logger.warning(f"[后台处理] 任务处理失败，已更新状态 -> record_id: {record_id}")
                except Exception as e:
                    logger.error(f"[后台处理] 更新失败状态时出错: {e}")
            
        except Exception as e:
            logger.error(f"[后台处理] 处理异常 -> 任务类型: {task_type}, 错误: {str(e)}")
            # 发生异常时，标记为失败
            if self.db:
                try:
                    self.db.update_task_record(
                        record_id,
                        status="failed",
                        result_data={'error': str(e)}
                    )
                except:
                    pass
    
    def _notify_web_service(self, task_data: Dict[str, Any]):
        """
        通知Web服务推送WebSocket消息
        
        Args:
            task_data: 任务数据
        """
        try:
            # Web服务的通知接口URL（默认在5000端口）
            web_notify_url = "http://127.0.0.1:5000/api/notify/task_result"
            
            response = requests.post(
                web_notify_url,
                json=task_data,
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info(f"[WebSocket通知] ✅ 已通知Web服务推送消息 -> 任务类型: {task_data.get('task_type')}, 状态: {task_data.get('result', {}).get('status', 'unknown')}")
            else:
                logger.warning(f"[WebSocket通知] ⚠️ Web服务响应异常 -> 状态码: {response.status_code}, 响应: {response.text}")
                
        except requests.exceptions.Timeout:
            logger.warning(f"[WebSocket通知] 通知Web服务超时")
        except requests.exceptions.ConnectionError:
            logger.warning(f"[WebSocket通知] 无法连接到Web服务")
        except Exception as e:
            logger.error(f"[WebSocket通知] 通知失败: {e}")
    
    def _notify_task_queue_update(self, action: str, task_id: str):
        """
        通知Web服务任务队列已更新
        
        Args:
            action: 操作类型（add/delete/complete）
            task_id: 任务ID
        """
        try:
            # Web服务的任务队列更新通知接口URL
            web_notify_url = "http://127.0.0.1:5000/api/notify/task_queue_update"
            
            response = requests.post(
                web_notify_url,
                json={
                    "action": action,
                    "task_id": task_id
                },
                timeout=3
            )
            
            if response.status_code == 200:
                logger.info(f"[任务队列通知] ✅ 已通知Web服务 -> 操作: {action}, task_id: {task_id}")
            else:
                logger.warning(f"[任务队列通知] ⚠️ Web服务响应异常 -> 状态码: {response.status_code}")
                
        except requests.exceptions.Timeout:
            logger.warning(f"[任务队列通知] 通知Web服务超时")
        except requests.exceptions.ConnectionError:
            logger.warning(f"[任务队列通知] 无法连接到Web服务")
        except Exception as e:
            logger.warning(f"[任务队列通知] 通知失败: {e}")
    
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
        image_base64: str,
        task_type: int,
        station_id: int,
        params: Optional[str] = None,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        统一处理路由（稳妥的异步模式）
        
        流程：
        1. 验证图片和参数
        2. 从任务队列中删除任务（如果提供了task_id）
        3. 创建数据库记录（标记为processing）
        4. 返回成功响应
        5. 后台线程处理图片识别并更新结果
        
        Args:
            image_base64: base64编码的图片
            task_type: 任务类型（1-4）
            station_id: 站点ID
            params: 额外参数（JSON字符串）
            task_id: 任务ID（可选，从队列中获取的任务ID）
        
        Returns:
            立即返回接收成功的响应
        """
        # ========== 第1步：验证图片 ==========
        try:
            img_data = base64.b64decode(image_base64)
            # 验证图片是否可以打开
            image = Image.open(BytesIO(img_data))
            image_info = f"图片尺寸: {image.size}, 模式: {image.mode}"
        except Exception as e:
            logger.error(f"图片解码失败: {e}")
            return format_response(
                "error",
                error=f"图片解码失败: {str(e)}",
                error_code="IMAGE_DECODE_ERROR"
            )
        
        # 记录请求信息
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
        
        # ========== 第2步：从任务队列中删除任务（如果提供了task_id）==========
        if task_id and self.db:
            try:
                deleted = self.db.delete_task_from_queue(task_id)
                if deleted:
                    logger.info(f"✅ 任务已从队列删除 -> task_id: {task_id}")
                    # 通知Web服务任务队列已更新
                    self._notify_task_queue_update("delete", task_id)
                else:
                    logger.warning(f"⚠️ 任务不在队列中（可能已被删除）-> task_id: {task_id}")
            except Exception as e:
                logger.error(f"❌ 从队列删除任务时出错 -> task_id: {task_id}, 错误: {e}")
                # 即使删除失败，也继续处理（可能是任务不存在）
        
        # ========== 第3步：创建数据库记录（标记为processing）==========
        record_id = None
        if self.db:
            try:
                # 生成任务记录ID（如果没有提供task_id，则生成一个）
                task_record_id = task_id if task_id else f"task_{task_type}_{station_id}_{int(time.time())}"
                
                # 创建初始记录（状态为processing）
                record_id = self.db.add_task_record(
                    task_id=task_record_id,
                    task_type=task_type,
                    station_id=station_id,
                    result_data={'message': '正在处理中'},
                    image_path="",  # 稍后由后台处理器更新
                    status="processing",
                    confidence=None,
                    processing_time=0
                )
                
                logger.info(f"✅ 任务记录已创建 -> record_id: {record_id}, task_id: {task_record_id}")
                
            except Exception as db_error:
                logger.error(f"❌ 创建任务记录失败: {db_error}")
                # 如果数据库失败，返回错误（因为无法追踪任务）
                return format_response(
                    "error",
                    error=f"创建任务记录失败: {str(db_error)}",
                    error_code="DATABASE_ERROR"
                )
        
        # ========== 第4步：提交后台处理任务 ==========
        if record_id:
            self.executor.submit(
                self._process_task_in_background,
                img_data,  # 传递原始字节数据
                task_type,
                station_id,
                project_name,
                extra_params,
                record_id  # 传递记录ID用于后续更新
            )
            logger.info(f"📤 任务已提交到后台处理 -> record_id: {record_id}")
        
        # ========== 第5步：返回成功响应 ==========
        return format_response(
            "success",
            data={
                "message": "任务已接收并从队列移除，正在后台处理",
                "task_type": task_type,
                "station_id": station_id,
                "task_id": task_id,
                "record_id": record_id,
                "status": "processing",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        )

