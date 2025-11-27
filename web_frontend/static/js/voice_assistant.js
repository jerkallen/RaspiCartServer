// 智能语音助手模块

class VoiceAssistant {
    constructor() {
        this.modal = null;
        this.inputText = null;
        this.recordBtn = null;
        this.sendBtn = null;
        this.statusDiv = null;
        this.resultDiv = null;
        
        this.recorder = null;
        this.isRecording = false;
        this.mediaStream = null;
        this.audioChunks = [];
    }

    init() {
        // 获取DOM元素
        this.modal = document.getElementById('voice-assistant-modal');
        this.inputText = document.getElementById('voice-input-text');
        this.recordBtn = document.getElementById('voice-record-btn');
        this.sendBtn = document.getElementById('voice-send-btn');
        this.statusDiv = document.getElementById('voice-status');
        this.resultDiv = document.getElementById('voice-result');
        
        // 绑定事件
        this.setupEventListeners();
        
        console.log('[语音助手] 初始化成功');
    }

    setupEventListeners() {
        // 打开按钮
        const openBtn = document.getElementById('voice-assistant-btn');
        if (openBtn) {
            openBtn.addEventListener('click', () => this.open());
        }

        // 录音按钮（暂时禁用，需要阿里云NLS SDK配置）
        if (this.recordBtn) {
            this.recordBtn.addEventListener('click', () => this.toggleRecording());
        }

        // 发送按钮
        if (this.sendBtn) {
            this.sendBtn.addEventListener('click', () => this.sendText());
        }

        // 回车发送
        if (this.inputText) {
            this.inputText.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && e.ctrlKey) {
                    this.sendText();
                }
            });
        }

        // 点击模态框外部关闭
        if (this.modal) {
            this.modal.addEventListener('click', (e) => {
                if (e.target === this.modal) {
                    this.close();
                }
            });
        }
    }

    open() {
        if (this.modal) {
            this.modal.style.display = 'flex';
            if (this.inputText) {
                this.inputText.focus();
            }
            this.clearStatus();
            this.clearResult();
            console.log('[语音助手] 打开');
        }
    }

    close() {
        if (this.modal) {
            this.modal.style.display = 'none';
            // 如果正在录音，停止录音
            if (this.isRecording) {
                this.stopRecording();
            }
            console.log('[语音助手] 关闭');
        }
    }

    async toggleRecording() {
        if (this.isRecording) {
            this.stopRecording();
        } else {
            await this.startRecording();
        }
    }

    async startRecording() {
        try {
            // 请求麦克风权限
            this.mediaStream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    sampleRate: 16000
                } 
            });

            // 创建录音器
            const options = { mimeType: 'audio/webm' };
            this.recorder = new MediaRecorder(this.mediaStream, options);
            this.audioChunks = [];

            this.recorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };

            this.recorder.onstop = () => {
                this.processRecording();
            };

            // 开始录音
            this.recorder.start();
            this.isRecording = true;

            // 更新UI
            this.recordBtn.classList.add('recording');
            this.recordBtn.innerHTML = '<span class="btn-icon recording-icon">⏹️</span><span class="btn-text">停止录音</span>';
            this.showStatus('正在录音...', 'info');

            console.log('[语音助手] 开始录音');

        } catch (error) {
            console.error('[语音助手] 录音启动失败:', error);
            this.showStatus('无法访问麦克风，请检查权限设置', 'error');
        }
    }

    stopRecording() {
        if (this.recorder && this.isRecording) {
            this.recorder.stop();
            this.isRecording = false;

            // 停止媒体流
            if (this.mediaStream) {
                this.mediaStream.getTracks().forEach(track => track.stop());
                this.mediaStream = null;
            }

            // 更新UI
            this.recordBtn.classList.remove('recording');
            this.recordBtn.innerHTML = '<span class="btn-icon">🎙️</span><span class="btn-text">语音输入</span>';
            this.showStatus('录音结束，正在识别...', 'info');

            console.log('[语音助手] 停止录音');
        }
    }

    async processRecording() {
        try {
            // 创建音频Blob
            const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
            console.log('[语音助手] 音频大小:', audioBlob.size, 'bytes');

            // 上传到服务器进行识别
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.webm');

            const response = await fetch('/api/voice/recognize', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.status === 'success' && result.data.text) {
                // 将识别的文字填入输入框
                this.inputText.value = result.data.text;
                this.showStatus('识别成功', 'success');
                console.log('[语音助手] 识别成功:', result.data.text);
            } else {
                // 语音识别未实现，提示用户使用文字输入
                this.showStatus('语音识别功能暂未配置，请直接输入文字', 'warning');
                console.log('[语音助手] 语音识别未实现');
            }

        } catch (error) {
            console.error('[语音助手] 语音识别失败:', error);
            this.showStatus('语音识别失败，请使用文字输入', 'error');
        }
    }

    async sendText() {
        const text = this.inputText.value.trim();

        if (!text) {
            this.showStatus('请输入任务需求', 'warning');
            return;
        }

        try {
            this.showStatus('正在解析意图...', 'info');
            this.sendBtn.disabled = true;

            // 调用意图解析API
            const response = await fetch('/api/intent/parse', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text: text })
            });

            const result = await response.json();

            if (result.status === 'success' && result.data.tasks) {
                const tasks = result.data.tasks;
                
                if (tasks.length === 0) {
                    this.showStatus('未识别到有效任务，请重新输入', 'warning');
                    return;
                }

                this.showStatus(`识别到 ${tasks.length} 个任务，正在添加...`, 'success');

                // 批量添加任务
                let successCount = 0;
                let failCount = 0;

                for (const task of tasks) {
                    try {
                        const addResponse = await fetch('/api/tasks/add', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                station_id: task.station_id,
                                task_type: task.task_type,
                                params: {}
                            })
                        });

                        const addResult = await addResponse.json();

                        if (addResult.status === 'success') {
                            successCount++;
                        } else {
                            failCount++;
                        }

                        // 短暂延迟，避免请求过快
                        await new Promise(resolve => setTimeout(resolve, 100));

                    } catch (error) {
                        console.error('[语音助手] 添加任务失败:', error);
                        failCount++;
                    }
                }

                // 显示结果
                const taskNames = {
                    1: '指针仪表',
                    2: '温度检测',
                    3: '烟雾监测A',
                    4: '烟雾监测B',
                    5: '物品描述'
                };

                const taskList = tasks.map(t => taskNames[t.task_type] || `任务${t.task_type}`).join('、');
                
                this.showResult(
                    `<div class="result-success">
                        <div class="result-title">✅ 任务添加完成</div>
                        <div class="result-detail">
                            <p>成功添加: ${successCount} 个</p>
                            ${failCount > 0 ? `<p>失败: ${failCount} 个</p>` : ''}
                            <p>任务列表: ${taskList}</p>
                        </div>
                    </div>`
                );

                // 通知任务管理器刷新
                if (window.taskManager) {
                    taskManager.loadTasks();
                }

                // 显示系统通知
                showNotification(`✅ 成功添加 ${successCount} 个任务`, 'success');

                // 清空输入框
                this.inputText.value = '';

                console.log('[语音助手] 任务添加完成:', { successCount, failCount });

                // 2秒后自动关闭窗口
                setTimeout(() => {
                    this.close();
                }, 2000);

            } else {
                this.showStatus('意图解析失败: ' + (result.error?.message || '未知错误'), 'error');
            }

        } catch (error) {
            console.error('[语音助手] 发送失败:', error);
            this.showStatus('请求失败: ' + error.message, 'error');
        } finally {
            this.sendBtn.disabled = false;
        }
    }

    showStatus(message, type = 'info') {
        if (this.statusDiv) {
            this.statusDiv.className = `voice-status ${type}`;
            this.statusDiv.textContent = message;
            this.statusDiv.style.display = 'block';
        }
    }

    clearStatus() {
        if (this.statusDiv) {
            this.statusDiv.style.display = 'none';
            this.statusDiv.textContent = '';
        }
    }

    showResult(html) {
        if (this.resultDiv) {
            this.resultDiv.innerHTML = html;
            this.resultDiv.style.display = 'block';
        }
    }

    clearResult() {
        if (this.resultDiv) {
            this.resultDiv.style.display = 'none';
            this.resultDiv.innerHTML = '';
        }
    }
}

// 创建全局实例
const voiceAssistant = new VoiceAssistant();

// 挂载到window对象，使其在HTML中可访问
window.voiceAssistant = voiceAssistant;

// 关闭语音助手（全局函数）
function closeVoiceAssistant() {
    if (window.voiceAssistant) {
        window.voiceAssistant.close();
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    voiceAssistant.init();
    console.log('[语音助手] 模块加载完成');
});

