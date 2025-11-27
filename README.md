# 智能巡检系统 - 服务端

基于树莓派5的智能巡检小车系统的服务端部分。

## 项目结构

```
RaspiCartServer/
├── api_server/              # BentoML API服务
│   ├── base_project.py      # 任务处理器基类
│   ├── loader.py            # 项目加载器
│   ├── service.py           # BentoML服务入口
│   ├── utils.py             # 工具函数
│   ├── config.yaml          # 服务配置
│   ├── start_server.py      # 启动脚本
│   ├── start_server.bat     # Windows启动脚本
│   ├── start_server.sh      # Linux/Mac启动脚本
│   └── processors/          # 任务处理器
│       ├── task1_pointer_reader/    # 任务1: 指针仪表读数
│       │   └── processor.py
│       ├── task2_temperature/       # 任务2: 高温物体检测
│       │   └── processor.py
│       ├── task3_smoke_a/           # 任务3: 烟雾判断A
│       │   └── processor.py
│       ├── task4_smoke_b/           # 任务4: 烟雾判断B
│       │   └── processor.py
│       └── task5_object_description/ # 任务5: 物品描述
│           └── processor.py
├── data/                    # 数据存储
│   ├── database/            # SQLite数据库
│   ├── images/              # 图片存储
│   ├── logs/                # 日志文件
│   └── config/              # 配置文件
├── requirements.txt         # Python依赖
└── env.example              # 环境变量示例
```

## 快速开始

### 1. 安装依赖

```bash
# 激活虚拟环境（如果有）
.\venv\Scripts\activate  # Windows
source venv/bin/activate # Linux/Mac

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `env.example` 为 `.env` 并配置：

```bash
cp env.example .env
```

编辑 `.env` 文件，填入你的阿里云API密钥：

```
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 3. 启动服务

#### Windows:
```bash
cd api_server
start_server.bat
```

或者手动启动：
```bash
cd api_server
python start_server.py serve
```

#### Linux/Mac:
```bash
cd api_server
chmod +x start_server.sh
./start_server.sh
```

或者手动启动：
```bash
cd api_server
python start_server.py serve
```

服务将在 `http://0.0.0.0:3000` 启动。

### 4. 测试服务

访问健康检查端点：

```bash
curl http://localhost:3000/health
```

## API接口

### 统一处理路由

**接口**: `POST /api/process`

**请求格式**: `multipart/form-data`

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| image | File | 是 | 任务图片（JPEG/PNG） |
| task_type | int | 是 | 任务类型（1-5） |
| station_id | int | 是 | 站点ID |
| params | JSON字符串 | 否 | 额外参数 |

**任务类型说明**:
- `1`: 指针仪表读数识别
- `2`: 高温物体检测
- `3`: 烟雾判断A
- `4`: 烟雾判断B
- `5`: 物品描述识别

**响应格式**（成功）:
```json
{
    "status": "success",
    "data": {
        "task_type": 1,
        "station_id": 3,
        "result": {
            "value": 1.05,
            "unit": "MPa",
            "confidence": 0.95,
            "status": "normal"
        },
        "processing_time": 1.2,
        "image_saved": true,
        "image_path": "data/images/2024-11-21/task1/station03_143005.jpg"
    },
    "timestamp": "2024-11-21 14:30:05"
}
```

**响应格式**（失败）:
```json
{
    "status": "error",
    "error": {
        "code": "PROCESSING_FAILED",
        "message": "图像识别失败"
    },
    "timestamp": "2024-11-21 14:30:05"
}
```

### 健康检查

**接口**: `GET /health`

**响应**:
```json
{
    "status": "healthy",
    "service": "inspection_api_service",
    "processors": ["task1_pointer_reader", "task2_temperature", "task3_smoke_a", "task4_smoke_b", "task5_object_description"],
    "timestamp": "2024-11-21 14:30:00"
}
```

## 任务处理器说明

### 任务1: 指针仪表读数

- 调用DashScope视觉模型识别指针位置
- 返回读数值、单位、置信度等信息

### 任务2: 高温物体检测

- 处理温度数据（不调用大模型）
- 根据温度阈值判断状态（normal/warning/danger）
- 阈值：60℃（warning）、80℃（danger）

### 任务3/4: 烟雾判断

- 调用DashScope视觉模型判断是否存在烟雾
- 返回烟雾类型、密度、置信度等信息

### 任务5: 物品描述

- 调用DashScope视觉模型识别A4纸上的物品
- 返回物品描述、物品列表、数量、置信度等信息

## 开发说明

### 添加新任务处理器

1. 在 `api_server/processors/` 目录下创建新的任务目录
2. 创建 `processor.py` 文件，继承 `BaseProject` 类
3. 实现必要的方法：
   - `get_project_name()`: 返回项目名称
   - `get_project_description()`: 返回项目描述
   - `validate_input()`: 验证输入数据
   - `process()`: 核心处理逻辑
4. 在 `config.yaml` 中注册新任务

### 日志查看

日志文件位于 `data/logs/bentoml.log`

## 依赖项

- Python 3.10+
- BentoML 1.4.28
- OpenAI SDK 2.7.1 (用于调用DashScope)
- Pillow, NumPy (图像处理)
- PyYAML (配置管理)

## 技术栈

- **服务框架**: BentoML
- **大模型**: 阿里云百炼 DashScope (qwen-vl-plus)
- **图像处理**: Pillow, NumPy
- **配置管理**: YAML

## 许可证

MIT License

## 作者

智能巡检系统开发组

