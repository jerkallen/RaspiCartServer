// 图表管理器
class ChartManager {
    constructor() {
        this.charts = {};
        this.taskTypes = {
            1: { name: '指针仪表', unit: 'MPa', color: '#3498db' },
            2: { name: '温度检测', unit: '℃', color: '#e74c3c' },
            3: { name: '烟雾监测A', unit: '', color: '#f39c12' },
            4: { name: '烟雾监测B', unit: '', color: '#9b59b6' }
        };
    }

    // 初始化所有图表
    initCharts() {
        for (let taskType = 1; taskType <= 4; taskType++) {
            this.createChart(taskType);
        }
    }

    // 创建图表
    createChart(taskType) {
        const chartDom = document.getElementById(`chart-${taskType}`);
        if (!chartDom) {
            console.error(`[图表] 未找到容器: chart-${taskType}`);
            return;
        }

        const chart = echarts.init(chartDom);
        const taskInfo = this.taskTypes[taskType];

        const option = {
            backgroundColor: 'transparent',
            title: {
                text: taskInfo.name,
                left: 'center',
                top: 10,
                textStyle: {
                    color: '#eee',
                    fontSize: 14
                }
            },
            tooltip: {
                trigger: 'axis',
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                borderColor: '#333',
                textStyle: {
                    color: '#eee'
                },
                formatter: (params) => {
                    if (params && params.length > 0) {
                        const data = params[0];
                        return `${data.name}<br/>${data.seriesName}: ${data.value}${taskInfo.unit}`;
                    }
                    return '';
                }
            },
            grid: {
                left: '10%',
                right: '10%',
                top: '25%',
                bottom: '15%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: [],
                axisLine: {
                    lineStyle: {
                        color: '#555'
                    }
                },
                axisLabel: {
                    color: '#bbb',
                    fontSize: 10,
                    rotate: 30
                }
            },
            yAxis: {
                type: 'value',
                name: taskInfo.unit,
                nameTextStyle: {
                    color: '#bbb'
                },
                axisLine: {
                    lineStyle: {
                        color: '#555'
                    }
                },
                axisLabel: {
                    color: '#bbb',
                    fontSize: 10
                },
                splitLine: {
                    lineStyle: {
                        color: '#333'
                    }
                }
            },
            series: [
                {
                    name: taskInfo.name,
                    type: 'line',
                    smooth: true,
                    symbol: 'circle',
                    symbolSize: 6,
                    data: [],
                    lineStyle: {
                        color: taskInfo.color,
                        width: 2
                    },
                    itemStyle: {
                        color: taskInfo.color
                    },
                    areaStyle: {
                        color: {
                            type: 'linear',
                            x: 0,
                            y: 0,
                            x2: 0,
                            y2: 1,
                            colorStops: [
                                { offset: 0, color: taskInfo.color + '80' },
                                { offset: 1, color: taskInfo.color + '10' }
                            ]
                        }
                    }
                }
            ]
        };

        chart.setOption(option);
        this.charts[taskType] = chart;

        // 响应窗口大小变化
        window.addEventListener('resize', () => {
            chart.resize();
        });

        console.log(`[图表] 初始化完成: 任务${taskType}`);
    }

    // 更新图表数据
    updateChart(taskType, newData) {
        const chart = this.charts[taskType];
        if (!chart) {
            console.error(`[图表] 未找到图表: 任务${taskType}`);
            return;
        }

        const option = chart.getOption();
        const xAxisData = option.xAxis[0].data;
        const seriesData = option.series[0].data;

        // 添加新数据
        const timestamp = new Date(newData.timestamp).toLocaleTimeString('zh-CN', {
            hour: '2-digit',
            minute: '2-digit'
        });
        
        xAxisData.push(timestamp);
        seriesData.push(newData.value);

        // 保持最多20个数据点
        if (xAxisData.length > 20) {
            xAxisData.shift();
            seriesData.shift();
        }

        // 更新图表
        chart.setOption({
            xAxis: {
                data: xAxisData
            },
            series: [{
                data: seriesData
            }]
        });

        console.log(`[图表] 更新数据: 任务${taskType}, 值=${newData.value}`);
    }

    // 加载历史数据
    async loadHistoryData(taskType, limit = 20) {
        try {
            const response = await fetch(`/api/history?task_type=${taskType}&limit=${limit}`);
            const result = await response.json();

            if (result.status === 'success' && result.data.records.length > 0) {
                const chart = this.charts[taskType];
                if (!chart) return;

                const records = result.data.records.reverse(); // 时间正序
                const xAxisData = [];
                const seriesData = [];

                records.forEach(record => {
                    const timestamp = new Date(record.timestamp).toLocaleTimeString('zh-CN', {
                        hour: '2-digit',
                        minute: '2-digit'
                    });
                    xAxisData.push(timestamp);

                    // 提取数值
                    let value = 0;
                    if (record.result_data) {
                        const resultData = typeof record.result_data === 'string' 
                            ? JSON.parse(record.result_data) 
                            : record.result_data;
                        
                        if (taskType === 1) {
                            value = resultData.value || 0;
                        } else if (taskType === 2) {
                            value = resultData.max_temperature || 0;
                        } else if (taskType === 3 || taskType === 4) {
                            value = resultData.has_smoke ? 1 : 0;
                        }
                    }
                    seriesData.push(value);
                });

                // 更新图表
                chart.setOption({
                    xAxis: {
                        data: xAxisData
                    },
                    series: [{
                        data: seriesData
                    }]
                });

                console.log(`[图表] 加载历史数据完成: 任务${taskType}, 共${records.length}条`);
            }
        } catch (error) {
            console.error(`[图表] 加载历史数据失败: 任务${taskType}`, error);
        }
    }

    // 加载所有历史数据
    async loadAllHistoryData() {
        for (let taskType = 1; taskType <= 4; taskType++) {
            await this.loadHistoryData(taskType);
        }
    }

    // 清空图表数据
    clearChart(taskType) {
        const chart = this.charts[taskType];
        if (!chart) return;

        chart.setOption({
            xAxis: {
                data: []
            },
            series: [{
                data: []
            }]
        });

        console.log(`[图表] 清空数据: 任务${taskType}`);
    }

    // 销毁所有图表
    dispose() {
        Object.values(this.charts).forEach(chart => {
            chart.dispose();
        });
        this.charts = {};
    }
}

// 创建全局图表管理器
const chartManager = new ChartManager();

// 页面加载完成后初始化图表
document.addEventListener('DOMContentLoaded', () => {
    // 等待DOM完全加载
    setTimeout(() => {
        chartManager.initCharts();
        chartManager.loadAllHistoryData();
    }, 500);
});

// 监听任务结果更新图表
wsManager.on('task_result', (data) => {
    const taskData = data.data || data;
    const taskType = taskData.task_type;
    
    if (taskType && taskData.result) {
        let value = 0;
        
        if (taskType === 1) {
            value = taskData.result.value || 0;
        } else if (taskType === 2) {
            value = taskData.result.max_temperature || 0;
        } else if (taskType === 3 || taskType === 4) {
            value = taskData.result.has_smoke ? 1 : 0;
        } else if (taskType === 5) {
            // 任务5：物品描述 - 更新UI元素
            updateTask5Panel(taskData);
            return; // 任务5不需要更新图表
        }
        
        chartManager.updateChart(taskType, {
            timestamp: taskData.timestamp || new Date().toISOString(),
            value: value
        });
    }
});

// 更新任务5面板
function updateTask5Panel(taskData) {
    const result = taskData.result;
    const status = result.status || 'normal';
    
    // 更新描述文本
    const descriptionEl = document.getElementById('description-5');
    if (descriptionEl && result.description) {
        descriptionEl.textContent = result.description;
    }
    
    // 更新状态
    const statusEl = document.getElementById('status-5');
    if (statusEl) {
        statusEl.className = `panel-status ${status}`;
        const statusText = {
            'normal': '正常',
            'warning': '警告',
            'danger': '危险'
        };
        statusEl.textContent = statusText[status] || '正常';
    }
    
    // 更新图片
    if (taskData.image_path) {
        const imageEl = document.getElementById('image-5');
        const noImageEl = document.getElementById('no-image-5');
        const overlayEl = document.getElementById('image-overlay-5');
        
        if (imageEl && noImageEl) {
            imageEl.src = '/' + taskData.image_path;
            imageEl.style.display = 'block';
            noImageEl.style.display = 'none';
            
            // 添加点击查看大图
            imageEl.onclick = () => {
                showImageViewer(imageEl.src, taskData);
            };
        }
        
        if (overlayEl) {
            const timestamp = new Date(taskData.timestamp).toLocaleString('zh-CN');
            overlayEl.textContent = timestamp;
        }
    }
    
    console.log('[任务5] UI更新完成');
}

