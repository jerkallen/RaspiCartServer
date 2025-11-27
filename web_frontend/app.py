"""
Flask Web服务 - 智能巡检系统
提供Web管理界面和任务管理API
"""
import os
import sys
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from datetime import datetime
import json
import logging
from logging.handlers import RotatingFileHandler
from typing import Dict, List, Any, Optional
import uuid

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.db_manager import DatabaseManager

# 创建Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'inspection-system-secret-key-2024'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB

# 启用CORS
CORS(app)

# 创建SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", ping_timeout=60, ping_interval=25)

# 配置日志
log_dir = project_root / "data" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

file_handler = RotatingFileHandler(
    filename=str(log_dir / 'flask.log'),
    maxBytes=5 * 1024 * 1024,
    backupCount=10,
    encoding='utf-8'
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)

# 初始化数据库管理器
try:
    db = DatabaseManager()
    logger.info("数据库管理器初始化成功")
except Exception as e:
    logger.error(f"数据库管理器初始化失败: {e}")
    db = None

# 配置路径
IMAGE_BASE_PATH = project_root / "data" / "images"
IMAGE_BASE_PATH.mkdir(parents=True, exist_ok=True)


# ==================== Web页面路由 ====================

@app.route('/')
def index():
    """主页面"""
    logger.info("访问主页面")
    return render_template('index.html')


# ==================== 任务管理API ====================

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """获取任务列表"""
    try:
        if db is None:
            return jsonify({
                "status": "error",
                "error": {
                    "code": "DB_NOT_INITIALIZED",
                    "message": "数据库未初始化"
                },
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }), 500
        
        # 获取待处理任务
        tasks = db.get_pending_tasks()
        
        # 格式化任务数据
        formatted_tasks = []
        for task in tasks:
            formatted_tasks.append({
                "task_id": task['task_id'],
                "station_id": task['station_id'],
                "task_type": task['task_type'],
                "params": task.get('params', {})
            })
        
        logger.info(f"返回 {len(formatted_tasks)} 个待处理任务")
        
        return jsonify({
            "status": "success",
            "data": {
                "tasks": formatted_tasks,
                "count": len(formatted_tasks)
            },
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        return jsonify({
            "status": "error",
            "error": {
                "code": "GET_TASKS_FAILED",
                "message": str(e)
            },
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }), 500


@app.route('/api/tasks/add', methods=['POST'])
def add_task():
    """添加新任务"""
    try:
        if db is None:
            return jsonify({
                "status": "error",
                "error": {
                    "code": "DB_NOT_INITIALIZED",
                    "message": "数据库未初始化"
                }
            }), 500
        
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['station_id', 'task_type']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "status": "error",
                    "error": {
                        "code": "MISSING_FIELD",
                        "message": f"缺少必填字段: {field}"
                    }
                }), 400
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 添加任务到数据库
        db.add_task_to_queue(
            task_id=task_id,
            station_id=data['station_id'],
            task_type=data['task_type'],
            params=data.get('params')
        )
        
        logger.info(f"添加新任务: ID={task_id}, 站点={data['station_id']}, 类型={data['task_type']}")
        
        # 通过WebSocket通知前端
        socketio.emit('task_queue_update', {
            "type": "task_queue_update",
            "data": {
                "action": "add",
                "task_id": task_id
            }
        })
        
        return jsonify({
            "status": "success",
            "data": {
                "task_id": task_id,
                "message": "任务添加成功"
            },
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    
    except Exception as e:
        logger.error(f"添加任务失败: {e}")
        return jsonify({
            "status": "error",
            "error": {
                "code": "ADD_TASK_FAILED",
                "message": str(e)
            }
        }), 500


@app.route('/api/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id: str):
    """删除任务"""
    try:
        if db is None:
            return jsonify({
                "status": "error",
                "error": {
                    "code": "DB_NOT_INITIALIZED",
                    "message": "数据库未初始化"
                }
            }), 500
        
        # 删除任务
        success = db.delete_task(task_id)
        
        if success:
            logger.info(f"删除任务: ID={task_id}")
            
            # 通过WebSocket通知前端
            socketio.emit('task_queue_update', {
                "type": "task_queue_update",
                "data": {
                    "action": "delete",
                    "task_id": task_id
                }
            })
            
            return jsonify({
                "status": "success",
                "data": {
                    "message": "任务删除成功"
                }
            })
        else:
            return jsonify({
                "status": "error",
                "error": {
                    "code": "TASK_NOT_FOUND",
                    "message": "任务不存在"
                }
            }), 404
    
    except Exception as e:
        logger.error(f"删除任务失败: {e}")
        return jsonify({
            "status": "error",
            "error": {
                "code": "DELETE_TASK_FAILED",
                "message": str(e)
            }
        }), 500


@app.route('/api/tasks/clear', methods=['POST'])
def clear_tasks():
    """清空已完成的任务"""
    try:
        if db is None:
            return jsonify({
                "status": "error",
                "error": {
                    "code": "DB_NOT_INITIALIZED",
                    "message": "数据库未初始化"
                }
            }), 500
        
        count = db.clear_completed_tasks()
        
        logger.info(f"清空已完成任务: {count} 个")
        
        return jsonify({
            "status": "success",
            "data": {
                "cleared_count": count,
                "message": f"已清除 {count} 个已完成任务"
            }
        })
    
    except Exception as e:
        logger.error(f"清空任务失败: {e}")
        return jsonify({
            "status": "error",
            "error": {
                "code": "CLEAR_TASKS_FAILED",
                "message": str(e)
            }
        }), 500


# ==================== 历史数据API ====================

@app.route('/api/history', methods=['GET'])
def get_history():
    """获取历史数据"""
    try:
        if db is None:
            return jsonify({
                "status": "error",
                "error": {
                    "code": "DB_NOT_INITIALIZED",
                    "message": "数据库未初始化"
                }
            }), 500
        
        # 获取查询参数
        task_type = request.args.get('task_type', type=int)
        station_id = request.args.get('station_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = request.args.get('limit', default=50, type=int)
        offset = request.args.get('offset', default=0, type=int)
        
        # 查询历史记录
        records = db.get_task_records(
            task_type=task_type,
            station_id=station_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
        
        # 转换image_path为相对URL
        for record in records:
            if record.get('image_path'):
                # 将绝对路径转换为相对URL
                image_path = record['image_path']
                if isinstance(image_path, str):
                    # 提取日期/task/文件名部分
                    parts = Path(image_path).parts
                    if len(parts) >= 3:
                        # 例如: 2025-11-21/task1/station01_231016.jpg
                        record['image_url'] = f"/images/{parts[-3]}/{parts[-2]}/{parts[-1]}"
                    else:
                        record['image_url'] = None
                else:
                    record['image_url'] = None
        
        logger.info(f"查询历史记录: 返回 {len(records)} 条")
        
        return jsonify({
            "status": "success",
            "data": {
                "records": records,
                "count": len(records),
                "limit": limit,
                "offset": offset
            },
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    
    except Exception as e:
        logger.error(f"查询历史记录失败: {e}")
        return jsonify({
            "status": "error",
            "error": {
                "code": "GET_HISTORY_FAILED",
                "message": str(e)
            }
        }), 500


# ==================== 系统状态API ====================

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """获取系统统计信息"""
    try:
        if db is None:
            return jsonify({
                "status": "error",
                "error": {
                    "code": "DB_NOT_INITIALIZED",
                    "message": "数据库未初始化"
                }
            }), 500
        
        stats = db.get_statistics()
        
        return jsonify({
            "status": "success",
            "data": stats,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        return jsonify({
            "status": "error",
            "error": {
                "code": "GET_STATS_FAILED",
                "message": str(e)
            }
        }), 500


@app.route('/api/cart/status', methods=['GET', 'POST'])
def cart_status_api():
    """获取或更新小车状态"""
    if request.method == 'GET':
        return get_cart_status()
    else:
        return update_cart_status_api()


def get_cart_status():
    """获取小车状态"""
    try:
        if db is None:
            return jsonify({
                "status": "error",
                "error": {
                    "code": "DB_NOT_INITIALIZED",
                    "message": "数据库未初始化"
                }
            }), 500
        
        cart_status = db.get_cart_status()
        
        if cart_status is None:
            # 如果没有状态记录,返回默认状态
            cart_status = {
                "online": False,
                "current_station": None,
                "mode": "idle",
                "battery_level": 0,
                "last_activity": None
            }
        
        return jsonify({
            "status": "success",
            "data": cart_status,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    
    except Exception as e:
        logger.error(f"获取小车状态失败: {e}")
        return jsonify({
            "status": "error",
            "error": {
                "code": "GET_CART_STATUS_FAILED",
                "message": str(e)
            }
        }), 500


def update_cart_status_api():
    """更新小车状态（供小车端调用）"""
    try:
        if db is None:
            return jsonify({
                "status": "error",
                "error": {
                    "code": "DB_NOT_INITIALIZED",
                    "message": "数据库未初始化"
                }
            }), 500
        
        data = request.get_json()
        
        # 更新数据库
        db.update_cart_status(
            online=data.get('online', True),
            current_station=data.get('current_station'),
            mode=data.get('mode', 'idle'),
            battery_level=data.get('battery_level'),
            last_activity=data.get('last_activity', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        
        # 获取最新状态
        cart_status = db.get_cart_status()
        
        logger.info(f"更新小车状态: 在线={data.get('online')}, 站点={data.get('current_station')}, 模式={data.get('mode')}")
        
        # 通过WebSocket推送状态更新
        socketio.emit('cart_status', {
            "type": "cart_status",
            "data": cart_status
        })
        
        return jsonify({
            "status": "success",
            "data": {
                "message": "状态更新成功",
                "cart_status": cart_status
            },
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    
    except Exception as e:
        logger.error(f"更新小车状态失败: {e}")
        return jsonify({
            "status": "error",
            "error": {
                "code": "UPDATE_CART_STATUS_FAILED",
                "message": str(e)
            }
        }), 500


@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """获取未处理的报警"""
    try:
        if db is None:
            return jsonify({
                "status": "error",
                "error": {
                    "code": "DB_NOT_INITIALIZED",
                    "message": "数据库未初始化"
                }
            }), 500
        
        alerts = db.get_unhandled_alerts()
        
        return jsonify({
            "status": "success",
            "data": {
                "alerts": alerts,
                "count": len(alerts)
            },
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    
    except Exception as e:
        logger.error(f"获取报警信息失败: {e}")
        return jsonify({
            "status": "error",
            "error": {
                "code": "GET_ALERTS_FAILED",
                "message": str(e)
            }
        }), 500


# ==================== 图片访问路由 ====================

@app.route('/images/<path:filename>')
def serve_image(filename):
    """提供图片访问"""
    try:
        return send_from_directory(IMAGE_BASE_PATH, filename)
    except Exception as e:
        logger.error(f"图片访问失败: {filename}, 错误: {e}")
        return "Image not found", 404


# ==================== WebSocket事件处理 ====================

@socketio.on('connect')
def handle_connect():
    """客户端连接"""
    logger.info(f"WebSocket客户端连接: {request.sid}")
    emit('connected', {'message': '连接成功'})


@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开连接"""
    logger.info(f"WebSocket客户端断开: {request.sid}")


@socketio.on('ping')
def handle_ping():
    """心跳检测"""
    emit('pong', {'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")})


# ==================== 通知函数（供API服务调用）====================

def notify_task_result(task_data: Dict[str, Any]):
    """通知任务结果（通过WebSocket推送到前端）"""
    socketio.emit('task_result', {
        "type": "task_result",
        "data": task_data
    })
    logger.info(f"推送任务结果: 类型={task_data.get('task_type')}, 站点={task_data.get('station_id')}")


def notify_alert(alert_data: Dict[str, Any]):
    """通知报警（通过WebSocket推送到前端）"""
    socketio.emit('alert', {
        "type": "alert",
        "data": alert_data
    })
    logger.info(f"推送报警: 级别={alert_data.get('level')}, 消息={alert_data.get('message')}")


@app.route('/api/notify/task_result', methods=['POST'])
def api_notify_task_result():
    """接收任务结果通知（供BentoML服务调用）"""
    try:
        task_data = request.get_json()
        if not task_data:
            logger.warning("收到空的任务结果通知")
            return jsonify({
                "status": "error",
                "error": {"code": "INVALID_DATA", "message": "缺少任务数据"}
            }), 400
        
        logger.info(f"收到任务结果通知: 任务类型={task_data.get('task_type')}, 状态={task_data.get('result', {}).get('status')}")
        
        # 推送WebSocket通知
        notify_task_result(task_data)
        
        return jsonify({
            "status": "success",
            "message": "通知已推送"
        })
    except Exception as e:
        logger.error(f"推送任务结果通知失败: {e}")
        return jsonify({
            "status": "error",
            "error": {"code": "NOTIFY_ERROR", "message": str(e)}
        }), 500


@app.route('/api/notify/task_queue_update', methods=['POST'])
def api_notify_task_queue_update():
    """接收任务队列更新通知（供BentoML服务调用）"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "error": {"code": "INVALID_DATA", "message": "缺少数据"}
            }), 400
        
        action = data.get('action', 'update')
        task_id = data.get('task_id', '')
        
        logger.info(f"收到任务队列更新通知: 操作={action}, task_id={task_id}")
        
        # 推送WebSocket通知任务队列更新
        socketio.emit('task_queue_update', {
            "type": "task_queue_update",
            "data": {
                "action": action,
                "task_id": task_id
            }
        })
        
        return jsonify({
            "status": "success",
            "message": "任务队列更新通知已推送"
        })
    except Exception as e:
        logger.error(f"推送任务队列更新通知失败: {e}")
        return jsonify({
            "status": "error",
            "error": {"code": "NOTIFY_ERROR", "message": str(e)}
        }), 500


# ==================== 智能语音助手API ====================

@app.route('/api/voice/recognize', methods=['POST'])
def voice_recognize():
    """语音识别接口"""
    try:
        # 检查是否有上传的文件
        if 'audio' not in request.files:
            return jsonify({
                "status": "error",
                "error": {
                    "code": "NO_AUDIO_FILE",
                    "message": "未找到音频文件"
                }
            }), 400
        
        audio_file = request.files['audio']
        
        # 读取音频数据
        audio_data = audio_file.read()
        logger.info(f"收到语音识别请求，音频大小: {len(audio_data)} bytes")
        
        # 由于阿里云NLS SDK需要完整配置，这里提供降级方案
        # 实际生产环境需要完整实现语音识别
        
        # 暂时返回提示信息，让用户使用文字输入
        return jsonify({
            "status": "error",
            "error": {
                "code": "NOT_IMPLEMENTED",
                "message": "语音识别功能需要完整的阿里云NLS SDK配置，请使用文字输入"
            }
        }), 501
        
    except Exception as e:
        logger.error(f"语音识别失败: {e}")
        return jsonify({
            "status": "error",
            "error": {
                "code": "RECOGNITION_ERROR",
                "message": str(e)
            }
        }), 500


@app.route('/api/intent/parse', methods=['POST'])
def intent_parse():
    """意图解析接口"""
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({
                "status": "error",
                "error": {
                    "code": "MISSING_TEXT",
                    "message": "缺少文本参数"
                }
            }), 400
        
        user_text = data['text'].strip()
        
        if not user_text:
            return jsonify({
                "status": "error",
                "error": {
                    "code": "EMPTY_TEXT",
                    "message": "文本不能为空"
                }
            }), 400
        
        logger.info(f"收到意图解析请求: {user_text}")
        
        # 导入意图解析器
        try:
            from aliyun_services import IntentParser
            parser = IntentParser()
            result = parser.parse_intent(user_text)
            
            if result['success']:
                logger.info(f"意图解析成功: 提取到 {len(result['tasks'])} 个任务")
                return jsonify({
                    "status": "success",
                    "data": {
                        "tasks": result['tasks'],
                        "original_input": result['original_input'],
                        "method": result.get('method', 'llm')
                    },
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
            else:
                return jsonify({
                    "status": "error",
                    "error": {
                        "code": "PARSE_FAILED",
                        "message": "意图解析失败"
                    }
                }), 500
                
        except Exception as e:
            logger.error(f"意图解析器初始化或执行失败: {e}")
            return jsonify({
                "status": "error",
                "error": {
                    "code": "PARSER_ERROR",
                    "message": f"意图解析器错误: {str(e)}"
                }
            }), 500
        
    except Exception as e:
        logger.error(f"意图解析接口错误: {e}")
        return jsonify({
            "status": "error",
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e)
            }
        }), 500


# ==================== 错误处理 ====================

@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return jsonify({
        "status": "error",
        "error": {
            "code": "NOT_FOUND",
            "message": "请求的资源不存在"
        }
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    logger.error(f"服务器内部错误: {error}")
    return jsonify({
        "status": "error",
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "服务器内部错误"
        }
    }), 500


# ==================== 启动服务 ====================

if __name__ == '__main__':
    logger.info("="*60)
    logger.info("智能巡检Web服务启动")
    logger.info(f"访问地址: http://0.0.0.0:5000")
    logger.info("="*60)
    
    # 使用SocketIO运行
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=False,
        allow_unsafe_werkzeug=True
    )

