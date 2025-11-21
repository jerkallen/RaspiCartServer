// WebSocket连接管理
class WebSocketManager {
    constructor() {
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 2000;
        this.listeners = {};
    }

    // 连接WebSocket
    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/socket.io/`;
        
        console.log('[WebSocket] 正在连接...', wsUrl);
        
        try {
            this.socket = io({
                transports: ['websocket', 'polling'],
                reconnection: true,
                reconnectionDelay: this.reconnectDelay,
                reconnectionAttempts: this.maxReconnectAttempts
            });

            this.setupEventHandlers();
        } catch (error) {
            console.error('[WebSocket] 连接失败:', error);
            this.scheduleReconnect();
        }
    }

    // 设置事件处理器
    setupEventHandlers() {
        // 连接成功
        this.socket.on('connect', () => {
            console.log('[WebSocket] 连接成功');
            this.reconnectAttempts = 0;
            this.notifyListeners('connected', { connected: true });
            showNotification('WebSocket连接成功', 'success');
        });

        // 连接断开
        this.socket.on('disconnect', (reason) => {
            console.log('[WebSocket] 连接断开:', reason);
            this.notifyListeners('disconnected', { reason });
            showNotification('WebSocket连接断开', 'warning');
        });

        // 重连尝试
        this.socket.on('reconnect_attempt', (attemptNumber) => {
            console.log(`[WebSocket] 重连尝试 ${attemptNumber}/${this.maxReconnectAttempts}`);
        });

        // 重连失败
        this.socket.on('reconnect_failed', () => {
            console.error('[WebSocket] 重连失败');
            showNotification('WebSocket重连失败，请刷新页面', 'danger');
        });

        // 任务结果推送
        this.socket.on('task_result', (data) => {
            console.log('[WebSocket] 收到任务结果:', data);
            this.notifyListeners('task_result', data);
        });

        // 任务队列更新
        this.socket.on('task_queue_update', (data) => {
            console.log('[WebSocket] 任务队列更新:', data);
            this.notifyListeners('task_queue_update', data);
        });

        // 小车状态更新
        this.socket.on('cart_status', (data) => {
            console.log('[WebSocket] 小车状态更新:', data);
            this.notifyListeners('cart_status', data);
        });

        // 报警推送
        this.socket.on('alert', (data) => {
            console.log('[WebSocket] 收到报警:', data);
            this.notifyListeners('alert', data);
            
            // 显示报警通知
            const alertData = data.data || data;
            const level = alertData.level || 'warning';
            showNotification(alertData.message, level);
            
            // 播放报警音效
            playAlertSound(level);
        });

        // 心跳响应
        this.socket.on('pong', (data) => {
            // console.log('[WebSocket] 心跳响应:', data);
        });
    }

    // 发送心跳
    sendPing() {
        if (this.socket && this.socket.connected) {
            this.socket.emit('ping');
        }
    }

    // 注册事件监听器
    on(event, callback) {
        if (!this.listeners[event]) {
            this.listeners[event] = [];
        }
        this.listeners[event].push(callback);
    }

    // 移除事件监听器
    off(event, callback) {
        if (this.listeners[event]) {
            this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
        }
    }

    // 通知监听器
    notifyListeners(event, data) {
        if (this.listeners[event]) {
            this.listeners[event].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`[WebSocket] 监听器回调错误 (${event}):`, error);
                }
            });
        }
    }

    // 安排重连
    scheduleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('[WebSocket] 达到最大重连次数');
            showNotification('WebSocket连接失败，请刷新页面', 'danger');
            return;
        }

        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
        
        console.log(`[WebSocket] ${delay}ms 后尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        
        setTimeout(() => {
            this.connect();
        }, delay);
    }

    // 断开连接
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
        }
    }
}

// 创建全局WebSocket管理器实例
const wsManager = new WebSocketManager();

// 页面加载完成后连接
document.addEventListener('DOMContentLoaded', () => {
    wsManager.connect();
    
    // 定期发送心跳
    setInterval(() => {
        wsManager.sendPing();
    }, 25000);
});

// 页面卸载时断开连接
window.addEventListener('beforeunload', () => {
    wsManager.disconnect();
});

