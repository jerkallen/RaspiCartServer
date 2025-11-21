// 任务管理器
class TaskManager {
    constructor() {
        this.tasks = [];
        this.latestData = {
            1: null,
            2: null,
            3: null,
            4: null
        };
    }

    // 初始化
    init() {
        this.loadTasks();
        this.loadLatestData();
        this.setupEventListeners();
        this.startAutoRefresh();
    }

    // 设置事件监听
    setupEventListeners() {
        // 添加任务按钮
        const addTaskBtn = document.getElementById('add-task-btn');
        if (addTaskBtn) {
            addTaskBtn.addEventListener('click', () => this.addTask());
        }

        // 清空队列按钮
        const clearQueueBtn = document.getElementById('clear-queue-btn');
        if (clearQueueBtn) {
            clearQueueBtn.addEventListener('click', () => this.clearQueue());
        }

        // WebSocket事件监听
        wsManager.on('task_result', (data) => this.handleTaskResult(data));
        wsManager.on('task_queue_update', () => this.loadTasks());
    }

    // 加载任务列表
    async loadTasks() {
        try {
            const response = await fetch('/api/tasks');
            const result = await response.json();

            if (result.status === 'success') {
                this.tasks = result.data.tasks;
                this.renderTaskQueue();
                this.updateTaskCount();
            }
        } catch (error) {
            console.error('[任务管理] 加载任务失败:', error);
        }
    }

    // 渲染任务队列
    renderTaskQueue() {
        const container = document.getElementById('task-queue-list');
        if (!container) return;

        if (this.tasks.length === 0) {
            container.innerHTML = '<div class="empty-message">暂无待处理任务</div>';
            return;
        }

        const taskNames = {
            1: '指针仪表',
            2: '温度检测',
            3: '烟雾监测A',
            4: '烟雾监测B'
        };

        container.innerHTML = this.tasks.map(task => `
            <div class="task-item">
                <div class="task-info">
                    <div class="task-type">${taskNames[task.task_type] || '未知任务'}</div>
                    <div class="task-station">站点 ${task.station_id}</div>
                </div>
                <button class="task-delete" onclick="taskManager.deleteTask('${task.task_id}')">删除</button>
            </div>
        `).join('');
    }

    // 更新任务数量
    updateTaskCount() {
        const countEl = document.getElementById('task-count');
        if (countEl) {
            countEl.textContent = this.tasks.length;
        }
    }

    // 添加任务
    async addTask() {
        const taskType = document.getElementById('task-type').value;

        if (!taskType) {
            showNotification('请选择任务类型', 'warning');
            return;
        }

        // 站点ID与任务类型一一对应
        const stationId = parseInt(taskType);

        try {
            const response = await fetch('/api/tasks/add', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    station_id: stationId,
                    task_type: parseInt(taskType),
                    params: {}
                })
            });

            const result = await response.json();

            if (result.status === 'success') {
                showNotification('任务添加成功', 'success');
                this.loadTasks();
            } else {
                showNotification('任务添加失败: ' + result.error.message, 'danger');
            }
        } catch (error) {
            console.error('[任务管理] 添加任务失败:', error);
            showNotification('任务添加失败', 'danger');
        }
    }

    // 删除任务
    async deleteTask(taskId) {
        try {
            const response = await fetch(`/api/tasks/${taskId}`, {
                method: 'DELETE'
            });

            const result = await response.json();

            if (result.status === 'success') {
                showNotification('任务删除成功', 'success');
                this.loadTasks();
            } else {
                showNotification('任务删除失败', 'danger');
            }
        } catch (error) {
            console.error('[任务管理] 删除任务失败:', error);
            showNotification('任务删除失败', 'danger');
        }
    }

    // 清空队列
    async clearQueue() {
        if (!confirm('确定要清空已完成的任务吗?')) {
            return;
        }

        try {
            const response = await fetch('/api/tasks/clear', {
                method: 'POST'
            });

            const result = await response.json();

            if (result.status === 'success') {
                showNotification(`已清除 ${result.data.cleared_count} 个任务`, 'success');
                this.loadTasks();
            }
        } catch (error) {
            console.error('[任务管理] 清空队列失败:', error);
            showNotification('清空队列失败', 'danger');
        }
    }

    // 加载最新数据
    async loadLatestData() {
        for (let taskType = 1; taskType <= 4; taskType++) {
            try {
                const response = await fetch(`/api/history?task_type=${taskType}&limit=1`);
                const result = await response.json();

                if (result.status === 'success' && result.data.records.length > 0) {
                    const record = result.data.records[0];
                    this.latestData[taskType] = record;
                    this.updatePanelDisplay(taskType, record);
                }
            } catch (error) {
                console.error(`[任务管理] 加载最新数据失败: 任务${taskType}`, error);
            }
        }
    }

    // 更新面板显示
    updatePanelDisplay(taskType, record) {
        // 更新状态
        const statusEl = document.getElementById(`status-${taskType}`);
        if (statusEl) {
            const status = record.status || 'normal';
            statusEl.className = `panel-status ${status}`;
            statusEl.textContent = status === 'normal' ? '正常' : 
                                  status === 'warning' ? '警告' : '危险';
        }

        // 更新最新数据
        const resultData = typeof record.result_data === 'string' 
            ? JSON.parse(record.result_data) 
            : record.result_data;

        if (taskType === 1) {
            // 指针仪表
            this.updateDataDisplay(taskType, 'value', resultData.value || 0, resultData.unit || '');
            this.updateDataDisplay(taskType, 'confidence', 
                ((resultData.confidence || 0) * 100).toFixed(0), '%');
        } else if (taskType === 2) {
            // 温度检测
            this.updateDataDisplay(taskType, 'max-temp', resultData.max_temperature || 0, '℃');
            this.updateDataDisplay(taskType, 'avg-temp', resultData.avg_temperature || 0, '℃');
        } else if (taskType === 3 || taskType === 4) {
            // 烟雾监测
            this.updateDataDisplay(taskType, 'smoke', resultData.has_smoke ? '检测到' : '无', '');
            this.updateDataDisplay(taskType, 'confidence', 
                ((resultData.confidence || 0) * 100).toFixed(0), '%');
        }

        // 更新图片
        if (record.image_path) {
            const imgEl = document.getElementById(`image-${taskType}`);
            if (imgEl) {
                imgEl.src = '/images/' + record.image_path.replace(/\\/g, '/').split('images/')[1];
                imgEl.style.display = 'block';
            }

            const noImageEl = document.getElementById(`no-image-${taskType}`);
            if (noImageEl) {
                noImageEl.style.display = 'none';
            }

            // 更新时间戳
            const overlayEl = document.getElementById(`image-overlay-${taskType}`);
            if (overlayEl) {
                overlayEl.textContent = new Date(record.timestamp).toLocaleString('zh-CN');
            }
        }
    }

    // 更新数据显示
    updateDataDisplay(taskType, dataType, value, unit) {
        const el = document.getElementById(`${dataType}-${taskType}`);
        if (el) {
            el.textContent = value;
        }

        const unitEl = document.getElementById(`${dataType}-unit-${taskType}`);
        if (unitEl && unit) {
            unitEl.textContent = unit;
        }
    }

    // 处理任务结果
    handleTaskResult(data) {
        const taskData = data.data || data;
        const taskType = taskData.task_type;

        if (taskType) {
            console.log('[任务管理] 收到任务结果:', taskData);
            
            // 更新最新数据
            this.latestData[taskType] = {
                result_data: taskData.result,
                status: taskData.result.status,
                image_path: taskData.image_path,
                timestamp: taskData.timestamp
            };

            this.updatePanelDisplay(taskType, this.latestData[taskType]);

            // 显示通知
            const taskNames = {
                1: '指针仪表',
                2: '温度检测',
                3: '烟雾监测A',
                4: '烟雾监测B'
            };
            showNotification(`${taskNames[taskType]}任务完成`, 'success');

            // 播放音效
            playAlertSound(taskData.result.status || 'normal');
        }
    }

    // 开始自动刷新
    startAutoRefresh() {
        // 每30秒刷新一次任务列表
        setInterval(() => {
            this.loadTasks();
        }, 30000);

        // 每60秒刷新一次最新数据
        setInterval(() => {
            this.loadLatestData();
        }, 60000);
    }
}

// 创建全局任务管理器
const taskManager = new TaskManager();

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    taskManager.init();
});

