// 历史记录管理

// 任务类型名称映射
const TASK_TYPE_NAMES = {
    1: '指针仪表',
    2: '温度检测',
    3: '烟雾监测A',
    4: '烟雾监测B',
    5: '物品描述'
};

// 任务类型图标映射
const TASK_TYPE_ICONS = {
    1: '📊',
    2: '🌡️',
    3: '💨',
    4: '💨',
    5: '📦'
};

// 显示历史记录弹窗
async function showHistory(taskType) {
    const modal = document.getElementById('history-modal');
    const title = document.getElementById('history-modal-title');
    const loading = document.getElementById('history-loading');
    const grid = document.getElementById('history-grid');
    const empty = document.getElementById('history-empty');
    
    // 设置标题
    const icon = TASK_TYPE_ICONS[taskType] || '📋';
    const name = TASK_TYPE_NAMES[taskType] || `任务${taskType}`;
    title.textContent = `${icon} ${name} - 历史记录`;
    
    // 显示弹窗
    modal.classList.add('show');
    
    // 显示加载状态
    loading.style.display = 'flex';
    grid.style.display = 'none';
    empty.style.display = 'none';
    grid.innerHTML = '';
    
    try {
        // 获取历史记录
        const response = await fetch(`/api/history?task_type=${taskType}&limit=100`);
        const result = await response.json();
        
        if (result.status === 'success' && result.data.records.length > 0) {
            // 隐藏加载状态，显示网格
            loading.style.display = 'none';
            grid.style.display = 'grid';
            
            // 渲染历史记录
            renderHistoryGrid(result.data.records, taskType);
        } else {
            // 显示空状态
            loading.style.display = 'none';
            empty.style.display = 'block';
        }
    } catch (error) {
        console.error('[历史记录] 加载失败:', error);
        loading.style.display = 'none';
        empty.style.display = 'block';
        empty.textContent = '加载失败，请重试';
    }
}

// 渲染历史记录网格
function renderHistoryGrid(records, taskType) {
    const grid = document.getElementById('history-grid');
    grid.innerHTML = '';
    
    records.forEach(record => {
        const item = createHistoryItem(record, taskType);
        grid.appendChild(item);
    });
}

// 创建单个历史记录项
function createHistoryItem(record, taskType) {
    const item = document.createElement('div');
    item.className = 'history-item';
    
    // 图片部分
    const imageDiv = document.createElement('div');
    imageDiv.className = 'history-item-image';
    
    if (record.image_url) {
        const img = document.createElement('img');
        img.src = record.image_url;
        img.alt = '检测图片';
        img.onerror = () => {
            imageDiv.innerHTML = '<div class="history-item-no-image">图片加载失败</div>';
        };
        imageDiv.appendChild(img);
    } else {
        imageDiv.innerHTML = '<div class="history-item-no-image">暂无图片</div>';
    }
    
    // 状态标签
    const statusSpan = document.createElement('span');
    statusSpan.className = `history-item-status ${record.status || 'normal'}`;
    statusSpan.textContent = getStatusText(record.status);
    imageDiv.appendChild(statusSpan);
    
    // 信息部分
    const infoDiv = document.createElement('div');
    infoDiv.className = 'history-item-info';
    
    // 时间
    const timeDiv = document.createElement('div');
    timeDiv.className = 'history-item-time';
    timeDiv.textContent = formatHistoryTime(record.timestamp);
    infoDiv.appendChild(timeDiv);
    
    // 数据
    const dataDiv = document.createElement('div');
    dataDiv.className = 'history-item-data';
    dataDiv.innerHTML = formatHistoryData(record, taskType);
    infoDiv.appendChild(dataDiv);
    
    item.appendChild(imageDiv);
    item.appendChild(infoDiv);
    
    // 点击查看大图
    item.addEventListener('click', () => {
        if (record.image_url) {
            showImageViewer(record);
        }
    });
    
    return item;
}

// 格式化历史记录数据
function formatHistoryData(record, taskType) {
    const resultData = record.result_data || {};
    
    switch (taskType) {
        case 1: // 指针仪表
            return `
                <div class="history-item-data-item">
                    <div class="history-item-data-label">读数值</div>
                    <div class="history-item-data-value">
                        ${formatValue(resultData.value)} ${resultData.unit || 'MPa'}
                    </div>
                </div>
            `;
        
        case 2: // 温度检测
            return `
                <div class="history-item-data-item">
                    <div class="history-item-data-label">最高温度</div>
                    <div class="history-item-data-value">
                        ${formatValue(resultData.max_temperature)} ℃
                    </div>
                </div>
                <div class="history-item-data-item">
                    <div class="history-item-data-label">平均温度</div>
                    <div class="history-item-data-value">
                        ${formatValue(resultData.avg_temperature)} ℃
                    </div>
                </div>
            `;
        
        case 3: // 烟雾监测A
        case 4: // 烟雾监测B
            return `
                <div class="history-item-data-item">
                    <div class="history-item-data-label">检测结果</div>
                    <div class="history-item-data-value">
                        ${resultData.has_smoke ? '⚠️ 有烟雾' : '✓ 无烟雾'}
                    </div>
                </div>
            `;
        
        case 5: // 物品描述
            return `
                <div class="history-item-data-item">
                    <div class="history-item-data-label">物品描述</div>
                    <div class="history-item-data-value" style="text-align: left; white-space: normal; word-break: break-word;">
                        ${resultData.description || '--'}
                    </div>
                </div>
            `;
        
        default:
            return '<div class="history-item-data-item">--</div>';
    }
}

// 格式化数值
function formatValue(value) {
    if (value === null || value === undefined) {
        return '--';
    }
    if (typeof value === 'number') {
        return value.toFixed(2);
    }
    return value;
}

// 获取状态文本
function getStatusText(status) {
    const statusMap = {
        'normal': '正常',
        'warning': '警告',
        'danger': '危险'
    };
    return statusMap[status] || '正常';
}

// 格式化历史记录时间
function formatHistoryTime(timestamp) {
    if (!timestamp) return '--';
    
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

// 关闭历史记录弹窗
function closeHistory() {
    const modal = document.getElementById('history-modal');
    modal.classList.remove('show');
}

// 显示图片大图查看器
function showImageViewer(record) {
    const viewer = document.getElementById('image-viewer');
    const img = document.getElementById('viewer-image');
    const info = document.getElementById('viewer-info');
    
    img.src = record.image_url;
    
    // 设置图片信息
    const statusText = getStatusText(record.status);
    const timeText = formatHistoryTime(record.timestamp);
    info.innerHTML = `
        <span style="color: ${getStatusColor(record.status)}; font-weight: bold;">
            ${statusText}
        </span>
        &nbsp;|&nbsp;
        ${timeText}
    `;
    
    viewer.classList.add('show');
}

// 获取状态颜色
function getStatusColor(status) {
    const colorMap = {
        'normal': '#27ae60',
        'warning': '#f39c12',
        'danger': '#e74c3c'
    };
    return colorMap[status] || '#27ae60';
}

// 关闭图片查看器
function closeImageViewer() {
    const viewer = document.getElementById('image-viewer');
    viewer.classList.remove('show');
}

// 点击弹窗背景关闭
document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('history-modal');
    const viewer = document.getElementById('image-viewer');
    
    // 点击弹窗背景关闭历史记录弹窗
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeHistory();
        }
    });
    
    // 点击查看器背景关闭图片查看器
    viewer.addEventListener('click', (e) => {
        if (e.target === viewer) {
            closeImageViewer();
        }
    });
    
    // ESC键关闭弹窗
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            if (viewer.classList.contains('show')) {
                closeImageViewer();
            } else if (modal.classList.contains('show')) {
                closeHistory();
            }
        }
    });
});

