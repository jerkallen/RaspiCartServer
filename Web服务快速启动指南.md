# Flask Web服务 - 快速启动指南

## 📋 前提条件

在启动Web服务前,请确保:

1. ✅ Python 3.10/3.11 已安装
2. ✅ 虚拟环境已创建并激活
3. ✅ 依赖包已安装 (`requirements.txt`)
4. ✅ 数据库已初始化 (`scripts/init_database.py`)
5. ✅ BentoML API服务正在运行(端口3000)

## 🚀 启动Web服务

### 方式1: 使用启动脚本(推荐)

#### Windows系统

双击运行或命令行执行:

```bash
cd web_frontend
start_web.bat
```

#### Linux/Mac系统

```bash
cd web_frontend
chmod +x start_web.sh
./start_web.sh
```

### 方式2: 手动启动

```bash
# 1. 激活虚拟环境
venv\Scripts\activate    # Windows
source venv/bin/activate # Linux/Mac

# 2. 进入web_frontend目录
cd web_frontend

# 3. 启动服务
python start_web.py
```

## 🌐 访问地址

启动成功后,在浏览器访问:

### 本地访问
```
http://localhost:5000
```

### 局域网访问
```
http://服务器IP:5000
```

例如: `http://192.168.1.100:5000`

## 📊 界面说明

### 顶部栏
- 系统标题
- 小车在线状态
- 当前时间

### 左侧边栏

#### 1. 任务管理
- 输入站点ID
- 选择任务类型(1-4)
- 设置优先级
- 点击"添加任务"

#### 2. 任务队列
- 查看待处理任务
- 删除单个任务
- 清空已完成任务

#### 3. 小车状态
- 在线状态
- 当前站点
- 运行模式
- 电池电量
- 最近活动

#### 4. 系统日志
- 实时系统日志
- 任务完成记录
- 报警信息

#### 5. 系统统计
- 总任务数
- 今日任务数

### 主显示区(田字格布局)

#### 任务1面板 - 指针仪表
- 📈 历史数据折线图
- 🔢 最新读数值和置信度
- 🖼️ 最新采集图片
- ⚙️ 操作按钮

#### 任务2面板 - 温度检测
- 📈 温度变化趋势图
- 🔢 最高温度和平均温度
- 🖼️ 最新热成像图片
- ⚙️ 操作按钮

#### 任务3面板 - 烟雾监测A
- 📈 检测记录图表
- 🔢 检测结果和置信度
- 🖼️ 最新监测图片
- ⚙️ 操作按钮

#### 任务4面板 - 烟雾监测B
- 📈 检测记录图表
- 🔢 检测结果和置信度
- 🖼️ 最新监测图片
- ⚙️ 操作按钮

## 🔧 功能测试

### 1. 测试添加任务

1. 在左侧边栏输入站点ID: `1`
2. 选择任务类型: `任务1 - 指针仪表`
3. 选择优先级: `中`
4. 点击"添加任务"按钮
5. 查看任务队列是否显示新任务

### 2. 测试WebSocket连接

打开浏览器开发者工具(F12):
- 查看Console标签
- 应该看到 `[WebSocket] 连接成功` 消息
- 右上角应显示"小车在线"(如果小车已连接)

### 3. 测试实时数据更新

当BentoML API服务处理任务完成后:
- 对应任务面板应自动更新
- 图表会添加新数据点
- 最新图片会刷新
- 系统日志会显示完成记录
- 收到WebSocket推送通知

## 🔌 API接口测试

### 测试获取任务列表

```bash
curl http://localhost:5000/api/tasks
```

### 测试添加任务

```bash
curl -X POST http://localhost:5000/api/tasks/add \
  -H "Content-Type: application/json" \
  -d '{
    "station_id": 1,
    "task_type": 1,
    "priority": "medium"
  }'
```

### 测试查询历史记录

```bash
curl "http://localhost:5000/api/history?task_type=1&limit=10"
```

### 测试获取统计信息

```bash
curl http://localhost:5000/api/statistics
```

### 测试获取小车状态

```bash
curl http://localhost:5000/api/cart/status
```

## 📝 日志查看

### 查看实时日志

**Windows:**
```bash
type ..\data\logs\flask.log
```

**Linux/Mac:**
```bash
tail -f ../data/logs/flask.log
```

### 日志位置

```
RaspiCartServer/
└── data/
    └── logs/
        └── flask.log
```

## ❗ 常见问题

### 1. 端口5000被占用

**症状:** 启动失败,提示端口占用

**解决方法:**

方法A - 关闭占用程序:
```bash
# Windows查找占用进程
netstat -ano | findstr :5000

# 杀死进程(替换PID)
taskkill /PID <PID> /F
```

方法B - 修改端口:

编辑 `web_frontend/start_web.py`:
```python
socketio.run(app, host='0.0.0.0', port=5001)  # 改为5001
```

### 2. WebSocket连接失败

**症状:** 页面显示"WebSocket连接断开"

**检查项:**
- 确认Flask服务正在运行
- 检查防火墙是否阻止5000端口
- 检查浏览器控制台错误信息

**解决方法:**
```bash
# Windows防火墙规则
netsh advfirewall firewall add rule name="Flask5000" dir=in action=allow protocol=TCP localport=5000
```

### 3. 数据库连接失败

**症状:** 页面显示"数据库未初始化"

**解决方法:**
```bash
# 初始化数据库
python scripts/init_database.py

# 测试数据库
python scripts/test_database.py
```

### 4. 图片无法显示

**症状:** 任务面板显示"暂无图片"

**检查项:**
- 确认图片目录存在: `data/images/`
- 确认BentoML服务已保存图片
- 检查图片路径是否正确

**解决方法:**
```bash
# 创建图片目录
mkdir -p data/images
```

### 5. 依赖包缺失

**症状:** 启动时报 `ModuleNotFoundError`

**解决方法:**
```bash
# 激活虚拟环境
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 6. 无法访问管理界面

**症状:** 浏览器无法打开页面

**检查项:**
- Flask服务是否正常运行
- 端口号是否正确
- 防火墙是否放行

**解决方法:**
```bash
# 测试本地访问
curl http://localhost:5000

# 测试API是否正常
curl http://localhost:5000/api/statistics
```

## 🔄 完整启动流程

### Step 1: 启动BentoML API服务

```bash
# 终端1
cd api_server
bentoml serve service.py --port 3000
```

等待显示: `Uvicorn running on http://0.0.0.0:3000`

### Step 2: 启动Flask Web服务

```bash
# 终端2(新窗口)
cd web_frontend
python start_web.py
```

等待显示: `智能巡检Web服务启动`

### Step 3: 打开浏览器

访问: `http://localhost:5000`

### Step 4: 验证功能

1. ✅ 页面正常加载
2. ✅ WebSocket连接成功(右上角显示状态)
3. ✅ 系统日志显示"WebSocket连接成功"
4. ✅ 可以添加任务到队列
5. ✅ 图表正常显示

## 📚 相关文档

- [需求文档](智能巡检服务端需求文档-服务端.md)
- [Web服务README](web_frontend/README.md)
- [API服务文档](api_server/架构说明.md)
- [数据库管理](scripts/db_manager.py)

## 💡 开发建议

### 修改界面样式

编辑文件: `web_frontend/static/css/style.css`

### 添加新功能

1. 后端API: 编辑 `web_frontend/app.py`
2. 前端逻辑: 编辑 `web_frontend/static/js/*.js`
3. 页面布局: 编辑 `web_frontend/templates/index.html`

### 调试技巧

1. 打开浏览器开发者工具(F12)
2. 查看Console标签了解JavaScript错误
3. 查看Network标签监控API请求
4. 查看WebSocket标签监控实时通信

## 🎯 下一步

Web服务启动成功后:

1. 小车端连接到Web服务获取任务
2. 小车执行任务并上传图片到API服务
3. API服务处理图片并通知Web服务
4. Web服务通过WebSocket推送结果到浏览器
5. 浏览器实时更新显示

## 📞 技术支持

如遇到问题:

1. 查看日志文件: `data/logs/flask.log`
2. 检查数据库: `python scripts/test_database.py`
3. 验证API服务: `curl http://localhost:3000/health`
4. 参考需求文档

---

**版本**: v1.0  
**更新日期**: 2024-11-21

