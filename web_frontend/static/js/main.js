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
    warning: '/static/audio/warning.mp3',
    danger: '/static/audio/danger.mp3',
    complete: '/static/audio/complete.mp3'
};

// 播放报警音效
function playAlertSound(level) {
    // 音效功能可选，这里简化实现
    console.log(`[音效] 播放: ${level}`);
    
    // 如果需要实际播放音效，取消下面的注释
    /*
    const audioFile = AUDIO_FILES[level] || AUDIO_FILES.normal;
    const audio = new Audio(audioFile);
    audio.volume = 0.5;
    audio.play().catch(err => {
        console.warn('[音效] 播放失败:', err);
    });
    */
}

// 显示通知
function showNotification(message, type = 'info', duration = 3000) {
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
        this.updateInfo('cart-mode', this.status.mode || 'idle');
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
            4: '烟雾监测B'
        };
        const taskName = taskNames[taskData.task_type] || '未知任务';
        systemLogger.addLog(`${taskName}任务完成 - 站点${taskData.station_id}`, 'info');
    });

    wsManager.on('alert', (data) => {
        const alertData = data.data || data;
        systemLogger.addLog(`⚠️ ${alertData.message}`, alertData.level === 'danger' ? 'error' : 'warning');
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

