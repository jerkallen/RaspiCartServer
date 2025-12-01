// 主脚本文件

// 全局配置
const APP_CONFIG = {
    API_BASE_URL: '',
    REFRESH_INTERVAL: 30000,
    CHART_MAX_POINTS: 20
};

// 音效管理
const AUDIO_FILES = {
    normal: '/static/audio/normal.mp3',
    warning: '/static/audio/warning.wav',
    danger: '/static/audio/danger.mp3',
    complete: '/static/audio/complete.mp3'
};

// 播放报警音效
function playAlertSound(level) {
    return new Promise((resolve) => {
        const audioFile = AUDIO_FILES[level] || AUDIO_FILES.normal;
        const audio = new Audio(audioFile);
        audio.volume = 0.5;
        
        // 监听播放结束事件
        audio.addEventListener('ended', () => {
            resolve();
        });
        
        // 监听错误事件
        audio.addEventListener('error', () => {
            console.warn('[音效] 播放失败:', audioFile);
            resolve(); // 即使失败也resolve，避免阻塞
        });
        
        audio.play().catch(err => {
            console.warn('[音效] 播放失败:', err);
            resolve(); // 即使失败也resolve，避免阻塞
        });
    });
}

// 显示通知
function showNotification(message, type = 'info', duration = 3000) {
    // 危险通知显示时间延长到8秒
    if (type === 'danger') {
        duration = 8000;
    }
    
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, duration);
}

// 显示危险确认弹窗
function showDangerConfirmDialog(taskName, stationId, taskData) {
    return new Promise((resolve) => {
        // 创建弹窗遮罩层
        const overlay = document.createElement('div');
        overlay.className = 'danger-dialog-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.85);
            backdrop-filter: blur(5px);
            z-index: 5000;
            display: flex;
            align-items: center;
            justify-content: center;
            animation: fadeIn 0.3s ease;
        `;

        // 创建弹窗内容
        const dialog = document.createElement('div');
        dialog.className = 'danger-dialog';
        dialog.style.cssText = `
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border-radius: 12px;
            padding: 30px;
            max-width: 500px;
            width: 90%;
            box-shadow: 0 8px 40px rgba(231, 76, 60, 0.6);
            border: 3px solid #e74c3c;
            animation: slideDown 0.3s ease;
            position: relative;
        `;

        // 危险图标和标题
        const title = document.createElement('div');
        title.style.cssText = `
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #e74c3c;
        `;
        
        const icon = document.createElement('div');
        icon.textContent = '🚨';
        icon.style.cssText = 'font-size: 48px;';
        
        const titleText = document.createElement('div');
        titleText.innerHTML = `
            <div style="font-size: 24px; font-weight: bold; color: #e74c3c; margin-bottom: 5px;">危险警报</div>
            <div style="font-size: 16px; color: #f5f5f5;">${taskName} - 站点${stationId}</div>
        `;
        
        title.appendChild(icon);
        title.appendChild(titleText);

        // 消息内容
        const message = document.createElement('div');
        message.style.cssText = `
            font-size: 16px;
            color: #f5f5f5;
            line-height: 1.6;
            margin-bottom: 25px;
            padding: 15px;
            background: rgba(231, 76, 60, 0.1);
            border-radius: 8px;
            border-left: 4px solid #e74c3c;
        `;
        message.textContent = `检测到危险状态！请立即检查并处理。`;

        // 确认按钮
        const buttonContainer = document.createElement('div');
        buttonContainer.style.cssText = `
            display: flex;
            justify-content: center;
            gap: 15px;
        `;
        
        const confirmBtn = document.createElement('button');
        confirmBtn.textContent = '我已了解';
        confirmBtn.style.cssText = `
            padding: 12px 40px;
            background: #e74c3c;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(231, 76, 60, 0.4);
        `;
        
        confirmBtn.onmouseover = () => {
            confirmBtn.style.background = '#c0392b';
            confirmBtn.style.transform = 'translateY(-2px)';
            confirmBtn.style.boxShadow = '0 6px 20px rgba(231, 76, 60, 0.6)';
        };
        
        confirmBtn.onmouseout = () => {
            confirmBtn.style.background = '#e74c3c';
            confirmBtn.style.transform = 'translateY(0)';
            confirmBtn.style.boxShadow = '0 4px 15px rgba(231, 76, 60, 0.4)';
        };
        
        confirmBtn.onclick = () => {
            overlay.style.animation = 'fadeOut 0.3s ease';
            setTimeout(() => {
                document.body.removeChild(overlay);
                resolve();
            }, 300);
        };

        buttonContainer.appendChild(confirmBtn);

        // 组装弹窗
        dialog.appendChild(title);
        dialog.appendChild(message);
        dialog.appendChild(buttonContainer);
        overlay.appendChild(dialog);

        // 添加到页面
        document.body.appendChild(overlay);

        // 添加动画样式（如果还没有）
        if (!document.getElementById('danger-dialog-styles')) {
            const style = document.createElement('style');
            style.id = 'danger-dialog-styles';
            style.textContent = `
                @keyframes fadeIn {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
                @keyframes fadeOut {
                    from { opacity: 1; }
                    to { opacity: 0; }
                }
                @keyframes slideDown {
                    from {
                        transform: translateY(-50px);
                        opacity: 0;
                    }
                    to {
                        transform: translateY(0);
                        opacity: 1;
                    }
                }
            `;
            document.head.appendChild(style);
        }
    });
}

// 格式化时间
function formatTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

// 格式化相对时间
function formatRelativeTime(timestamp) {
    const now = new Date();
    const date = new Date(timestamp);
    const diff = now - date;

    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days}天前`;
    if (hours > 0) return `${hours}小时前`;
    if (minutes > 0) return `${minutes}分钟前`;
    return `${seconds}秒前`;
}

// 系统日志管理
class SystemLogger {
    constructor() {
        this.logs = [];
        this.maxLogs = 100;
        this.container = null;
    }

    init() {
        this.container = document.getElementById('system-logs');
    }

    addLog(message, level = 'info') {
        const timestamp = new Date().toLocaleTimeString('zh-CN');
        const log = {
            timestamp,
            message,
            level
        };

        this.logs.unshift(log);

        if (this.logs.length > this.maxLogs) {
            this.logs = this.logs.slice(0, this.maxLogs);
        }

        this.render();
    }

    render() {
        if (!this.container) return;

        this.container.innerHTML = this.logs.map(log => `
            <div class="log-entry log-${log.level}">
                <span class="log-time">[${log.timestamp}]</span> ${log.message}
            </div>
        `).join('');
    }

    clear() {
        this.logs = [];
        this.render();
    }
}

// 创建全局日志管理器
const systemLogger = new SystemLogger();

// 小车状态管理
class CartStatusManager {
    constructor() {
        this.status = null;
        this.lastUpdate = null;
    }

    async loadStatus() {
        try {
            const response = await fetch('/api/cart/status');
            const result = await response.json();

            if (result.status === 'success') {
                this.status = result.data;
                this.lastUpdate = new Date();
                this.render();
            }
        } catch (error) {
            console.error('[小车状态] 加载失败:', error);
        }
    }

    render() {
        if (!this.status) return;

        // 更新在线状态
        const statusIndicator = document.querySelector('.status-indicator');
        const statusText = document.querySelector('.cart-status .status-text');
        
        if (statusIndicator && statusText) {
            if (this.status.online) {
                statusIndicator.className = 'status-indicator online';
                statusText.textContent = '小车在线';
            } else {
                statusIndicator.className = 'status-indicator offline';
                statusText.textContent = '小车离线';
            }
        }

        // 更新详细信息
        this.updateInfo('cart-online', this.status.online ? '在线' : '离线');
        this.updateInfo('cart-station', this.status.current_station || '--');
        
        // 格式化运行模式
        const modeMap = {
            'idle': '待机',
            'single': '单圈模式',
            'loop': '循环模式',
            'traveling': '行驶中',
            'working': '工作中'
        };
        const modeText = modeMap[this.status.mode] || this.status.mode || '--';
        this.updateInfo('cart-mode', modeText);
        
        this.updateInfo('cart-battery', this.status.battery_level ? `${this.status.battery_level}%` : '--');
        
        if (this.status.last_activity) {
            this.updateInfo('cart-activity', formatRelativeTime(this.status.last_activity));
        }
    }

    updateInfo(id, value) {
        const el = document.getElementById(id);
        if (el) {
            el.textContent = value;
        }
    }

    startAutoRefresh() {
        // 每10秒刷新一次小车状态
        setInterval(() => {
            this.loadStatus();
        }, 10000);
        
        // 每秒更新一次相对时间显示
        setInterval(() => {
            if (this.status && this.status.last_activity) {
                this.updateInfo('cart-activity', formatRelativeTime(this.status.last_activity));
            }
        }, 1000);
    }
}

// 创建全局小车状态管理器
const cartStatusManager = new CartStatusManager();

// 统计信息管理
class StatisticsManager {
    async loadStatistics() {
        try {
            const response = await fetch('/api/statistics');
            const result = await response.json();

            if (result.status === 'success') {
                this.render(result.data);
            }
        } catch (error) {
            console.error('[统计] 加载失败:', error);
        }
    }

    render(stats) {
        this.updateStat('total-tasks', stats.total_tasks || 0);
        this.updateStat('today-tasks', stats.today_tasks || 0);
        this.updateStat('pending-tasks', stats.pending_tasks || 0);
        this.updateStat('unhandled-alerts', stats.unhandled_alerts || 0);
    }

    updateStat(id, value) {
        const el = document.getElementById(id);
        if (el) {
            el.textContent = value;
        }
    }
}

// 创建全局统计管理器
const statisticsManager = new StatisticsManager();

// 初始化应用
function initApp() {
    console.log('[应用] 初始化开始...');

    // 初始化日志
    systemLogger.init();
    systemLogger.addLog('系统启动', 'info');

    // 加载小车状态
    cartStatusManager.loadStatus();
    cartStatusManager.startAutoRefresh();

    // 加载统计信息
    statisticsManager.loadStatistics();

    // 设置定期刷新统计
    setInterval(() => {
        statisticsManager.loadStatistics();
    }, 60000);

    // 监听WebSocket事件添加日志
    wsManager.on('connected', () => {
        systemLogger.addLog('WebSocket连接成功', 'info');
    });

    wsManager.on('disconnected', () => {
        systemLogger.addLog('WebSocket连接断开', 'warning');
    });

    wsManager.on('task_result', (data) => {
        const taskData = data.data || data;
        const taskNames = {
            1: '指针仪表',
            2: '温度检测',
            3: '烟雾监测A',
            4: '烟雾监测B',
            5: '物品描述'
        };
        const taskName = taskNames[taskData.task_type] || '未知任务';
        const status = taskData.result?.status || 'normal';
        
        // 根据状态使用不同的日志级别和图标
        if (status === 'danger') {
            systemLogger.addLog(`🚨 ${taskName}检测到危险状态 - 站点${taskData.station_id}`, 'error');
        } else if (status === 'warning') {
            systemLogger.addLog(`⚠️ ${taskName}检测到警告状态 - 站点${taskData.station_id}`, 'warning');
        } else {
            systemLogger.addLog(`✓ ${taskName}任务完成 - 站点${taskData.station_id}`, 'info');
        }
    });

    wsManager.on('alert', (data) => {
        const alertData = data.data || data;
        systemLogger.addLog(`⚠️ ${alertData.message}`, alertData.level === 'danger' ? 'error' : 'warning');
    });

    // 监听小车状态更新
    wsManager.on('cart_status', (data) => {
        const statusData = data.data || data;
        cartStatusManager.status = statusData;
        cartStatusManager.lastUpdate = new Date();
        cartStatusManager.render();
    });

    console.log('[应用] 初始化完成');
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

// 添加滑出动画
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

