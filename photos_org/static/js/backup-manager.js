/**
 * 备份管理模块
 * 提供数据备份、预览、进度跟踪等功能
 */
class BackupManager {
    constructor() {
        this.backupPath = '';
        this.backupMode = 'incremental';
        this.isBackingUp = false;
        this.showAllHistory = false;
        this.init();
    }
    
    init() {
        // 绑定导航栏按钮
        document.getElementById('backupBtn')?.addEventListener('click', () => {
            this.openBackupModal();
        });
        
        // 绑定模态框内按钮
        document.getElementById('selectBackupPathBtn')?.addEventListener('click', () => {
            this.selectBackupPath();
        });
        
        document.getElementById('startBackupBtn')?.addEventListener('click', () => {
            this.startBackup();
        });
        
        document.getElementById('showMoreBackupBtn')?.addEventListener('click', () => {
            this.showAllHistory = true;
            this.loadBackupHistory();
        });
        
        // 监听备份方式变化
        document.querySelectorAll('input[name="backupMode"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.backupMode = e.target.value;
            });
        });
        
        // 监听模态框关闭事件
        const backupModal = document.getElementById('backupModal');
        if (backupModal) {
            backupModal.addEventListener('shown.bs.modal', () => {
                // 打开时加载系统统计和备份历史
                this.loadSystemStats();
                this.loadBackupHistory();
            });
            
            backupModal.addEventListener('hidden.bs.modal', () => {
                this.resetBackupModal();
            });
        }
    }
    
    /**
     * 检查是否为远程访问
     * @returns {boolean} true表示远程访问，false表示服务器本机访问
     */
    isRemoteAccess() {
        const hostname = window.location.hostname;
        // 只有服务器本机访问才允许：localhost、127.0.0.1、::1
        // 内网IP（192.168.x.x、10.x.x.x）和公网IP都视为远程访问
        const isLocalhost = hostname === 'localhost' || 
                            hostname === '127.0.0.1' || 
                            hostname === '::1';
        return !isLocalhost;
    }
    
    /**
     * 打开备份模态框
     */
    openBackupModal() {
        // 检查是否为远程访问
        if (this.isRemoteAccess()) {
            alert('备份功能仅限本地访问。出于安全考虑，远程访问不允许发起备份任务。');
            return;
        }
        
        const modal = new bootstrap.Modal(document.getElementById('backupModal'));
        modal.show();
        
        // 尝试从备份历史中获取最近一次备份路径，并填充到输入框
        this.loadLastBackupPath();
    }
    
    /**
     * 加载最近一次备份路径（用于默认显示）
     */
    async loadLastBackupPath() {
        try {
            const response = await fetch('/api/v1/storage/backups/history');
            if (response.ok) {
                const data = await response.json();
                if (data.backups && data.backups.length > 0) {
                    const lastBackup = data.backups[0]; // 已按时间倒序排列
                    const lastPath = lastBackup.backup_path || '';
                    if (lastPath) {
                        // 填充到输入框
                        document.getElementById('backupPath').value = lastPath;
                        this.backupPath = lastPath;
                        
                        // 自动启用开始备份按钮（因为路径已存在且有效）
                        document.getElementById('startBackupBtn').disabled = false;
                    }
                }
            }
        } catch (error) {
            // 静默失败，不影响正常使用
            console.debug('加载上次备份路径失败:', error);
        }
    }
    
    /**
     * 加载系统统计信息（打开即显示）
     * 优化：先显示加载状态，然后异步加载数据
     */
    async loadSystemStats() {
        try {
            // 先显示加载状态
            document.getElementById('statsDbSize').textContent = '加载中...';
            document.getElementById('statsOriginalsCount').textContent = '加载中...';
            document.getElementById('statsOriginalsSize').textContent = '-';
            document.getElementById('statsThumbnailsCount').textContent = '加载中...';
            document.getElementById('statsThumbnailsSize').textContent = '-';
            
            const response = await fetch('/api/v1/storage/stats');
            if (!response.ok) {
                throw new Error('加载失败');
            }
            
            const data = await response.json();
            
            // 显示数据库信息（快速，立即显示）
            document.getElementById('statsDbSize').textContent = this.formatSize(data.database.size);
            
            // 显示原图信息（从数据库读取，快速）
            document.getElementById('statsOriginalsCount').textContent = `${data.originals.count} 个文件`;
            document.getElementById('statsOriginalsSize').textContent = this.formatSize(data.originals.total_size);
            
            // 显示缩略图信息（基于数据库估算，快速）
            document.getElementById('statsThumbnailsCount').textContent = `${data.thumbnails.count} 个文件`;
            document.getElementById('statsThumbnailsSize').textContent = `${this.formatSize(data.thumbnails.total_size)}（估）`;
            
        } catch (error) {
            console.error('加载系统统计失败:', error);
            document.getElementById('statsDbSize').textContent = '加载失败';
            document.getElementById('statsOriginalsCount').textContent = '加载失败';
            document.getElementById('statsOriginalsSize').textContent = '-';
            document.getElementById('statsThumbnailsCount').textContent = '加载失败';
            document.getElementById('statsThumbnailsSize').textContent = '-';
        }
    }
    
    /**
     * 选择备份路径
     */
    async selectBackupPath() {
        try {
            // 显示加载状态（使用更小的spinner，避免换行）
            const selectBtn = document.getElementById('selectBackupPathBtn');
            const originalText = selectBtn.innerHTML;
            selectBtn.disabled = true;
            // 使用更小的spinner，并设置固定宽度避免换行
            selectBtn.innerHTML = '<span class="spinner-border spinner-border-sm" style="width: 0.8rem; height: 0.8rem; border-width: 0.1em;"></span><span class="ms-1">选择中</span>';
            selectBtn.style.minWidth = selectBtn.offsetWidth + 'px'; // 保持按钮宽度
            
            // 获取当前路径作为初始目录（如果有）
            const currentPath = document.getElementById('backupPath').value || '';
            const requestBody = currentPath ? { initial_dir: currentPath } : {};
            
            // 调用API打开Windows文件夹选择对话框
            const response = await fetch('/api/v1/storage/backup/select-path', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestBody)
            });
            
            if (!response.ok) {
                throw new Error('选择路径失败');
            }
            
            const result = await response.json();
            
            if (result.success && result.path) {
                this.backupPath = result.path;
                document.getElementById('backupPath').value = this.backupPath;
                
                // 检查空间并提醒用户
                await this.checkBackupSpace();
                
                // 启用开始备份按钮
                document.getElementById('startBackupBtn').disabled = false;
            } else {
                if (result.message && !result.message.includes('取消')) {
                    alert('选择路径失败: ' + result.message);
                }
            }
            
        } catch (error) {
            console.error('选择备份路径失败:', error);
            alert('选择备份路径失败: ' + error.message);
        } finally {
            const selectBtn = document.getElementById('selectBackupPathBtn');
            selectBtn.disabled = false;
            selectBtn.innerHTML = '<i class="bi bi-folder2-open"></i> 选择';
            selectBtn.style.minWidth = ''; // 恢复默认宽度
        }
    }
    
    /**
     * 检查备份空间
     */
    async checkBackupSpace() {
        if (!this.backupPath) return;
        
        try {
            // 这里可以调用后端API检查空间，暂时使用前端提醒
            // 由于robocopy会自动处理，这里只做提醒
            alert('请确保备份目标路径有足够的可用空间！\n\n建议可用空间至少为系统数据总大小的1.5倍。');
        } catch (error) {
            console.error('检查备份空间失败:', error);
        }
    }
    
    /**
     * 开始备份
     */
    async startBackup() {
        if (!this.backupPath) {
            alert('请先选择备份路径');
            return;
        }
        
        // 获取备份方式
        const backupModeRadio = document.querySelector('input[name="backupMode"]:checked');
        this.backupMode = backupModeRadio ? backupModeRadio.value : 'incremental';
        
        if (!confirm(`确定要开始备份吗？\n\n备份路径: ${this.backupPath}\n备份方式: ${this.backupMode === 'incremental' ? '增量备份（跳过同名文件）' : '全量备份（覆盖同名文件）'}\n\n备份过程可能需要较长时间，请勿关闭此窗口。`)) {
            return;
        }
        
        try {
            this.isBackingUp = true;
            
            // 禁用按钮
            document.getElementById('startBackupBtn').disabled = true;
            document.getElementById('selectBackupPathBtn').disabled = true;
            document.getElementById('closeBackupModalBtn').disabled = true;
            
            // 显示进度条
            document.getElementById('backupProgressSection').style.display = 'block';
            this.updateProgress(0, '正在初始化备份...');
            
            // 调用备份API
            const response = await fetch('/api/v1/storage/backup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    backup_path: this.backupPath,
                    backup_mode: this.backupMode,
                    backup_type: 'manual'
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '备份失败');
            }
            
            const result = await response.json();
            
            // 检查是否成功启动
            if (!result.success || !result.task_id) {
                throw new Error('启动备份任务失败');
            }
            
            // 立即开始轮询状态
            this.pollBackupStatus(result.task_id);
            
        } catch (error) {
            console.error('备份失败:', error);
            alert('备份失败: ' + error.message);
            this.resetBackupProgress();
        }
    }
    
    /**
     * 轮询备份任务状态
     */
    pollBackupStatus(taskId) {
        const maxAttempts = 7200; // 最多轮询7200次（4小时，每次2秒）
        let attempts = 0;
        
        // 阶段名称映射
        const stageNames = {
            'initializing': '正在初始化...',
            'backing_up_db': '正在备份数据库...',
            'backing_up_originals': '正在备份原图文件...',
            'backing_up_thumbnails': '正在备份缩略图...',
            'calculating_stats': '正在计算统计信息...',
            'saving_metadata': '正在保存元信息...',
            'completed': '备份完成！'
        };
        
        const poll = async () => {
            try {
                const response = await fetch(`/api/v1/storage/backup/status/${taskId}`);
                const data = await response.json();
                
                if (!response.ok) {
                    console.error('获取任务状态失败:', data.message);
                    if (attempts >= maxAttempts) {
                        alert('备份任务状态查询超时，请手动刷新页面查看结果。');
                        this.resetBackupProgress();
                        return;
                    }
                    // 继续轮询
                    attempts++;
                    setTimeout(poll, 2000);
                    return;
                }
                
                const status = data.status;
                const progress = Math.min(data.progress_percentage || 0, 100);
                const message = data.message || stageNames[data.current_stage] || '请稍候...';
                
                // 更新进度条
                this.updateProgress(progress, message);
                
                if (status === 'completed') {
                    // 任务完成
                    console.log('备份任务完成:', data.message);
                    this.updateProgress(100, '备份完成！');
                    
                    // 延迟刷新备份历史并显示完成消息
                    setTimeout(() => {
                        this.onBackupComplete();
                    }, 1500);
                } else if (status === 'failed') {
                    // 任务失败
                    console.error('备份任务失败:', data.message);
                    alert('备份失败: ' + (data.message || '未知错误'));
                    this.resetBackupProgress();
                } else if (status === 'processing') {
                    // 任务进行中，继续轮询
                    if (attempts >= maxAttempts) {
                        alert('备份任务超时，请手动刷新页面查看结果。');
                        this.resetBackupProgress();
                        return;
                    }
                    attempts++;
                    setTimeout(poll, 2000);
                } else if (status === 'not_found') {
                    // 任务不存在（可能已完成并清理）
                    console.warn('任务状态不存在，可能已完成，刷新页面查看结果');
                    this.loadBackupHistory();
                    this.resetBackupProgress();
                }
                
            } catch (error) {
                console.error('轮询任务状态失败:', error);
                if (attempts >= maxAttempts) {
                    alert('备份任务状态查询超时，请手动刷新页面查看结果。');
                    this.resetBackupProgress();
                    return;
                }
                attempts++;
                setTimeout(poll, 2000);
            }
        };
        
        // 开始轮询
        poll();
    }
    
    /**
     * 更新进度条
     */
    updateProgress(percent, text) {
        const progressBar = document.getElementById('backupProgressBar');
        const progressText = document.getElementById('backupProgressText');
        const progressPercent = document.getElementById('backupProgressPercent');
        const statusText = document.getElementById('backupStatusText');
        
        progressBar.style.width = `${percent}%`;
        progressBar.setAttribute('aria-valuenow', percent);
        progressText.textContent = text;
        progressPercent.textContent = `${percent}%`;
        statusText.textContent = text;
    }
    
    /**
     * 备份完成
     */
    onBackupComplete() {
        this.isBackingUp = false;
        
        // 显示成功消息
        alert('备份完成！');
        
        // 重新加载备份历史
        this.loadBackupHistory();
        
        // 重置界面
        this.resetBackupProgress();
    }
    
    /**
     * 重置备份进度
     */
    resetBackupProgress() {
        document.getElementById('backupProgressSection').style.display = 'none';
        document.getElementById('startBackupBtn').disabled = false;
        document.getElementById('selectBackupPathBtn').disabled = false;
        document.getElementById('closeBackupModalBtn').disabled = false;
        this.updateProgress(0, '准备中...');
    }
    
    /**
     * 重置备份模态框
     */
    resetBackupModal() {
        this.isBackingUp = false;
        this.backupPath = '';
        this.showAllHistory = false;
        document.getElementById('backupPath').value = '';
        document.getElementById('startBackupBtn').disabled = true;
        document.getElementById('backupProgressSection').style.display = 'none';
    }
    
    /**
     * 加载备份历史
     */
    async loadBackupHistory() {
        try {
            const response = await fetch('/api/v1/storage/backups/history');
            if (!response.ok) {
                throw new Error('加载失败');
            }
            
            const data = await response.json();
            this.displayBackupHistory(data.backups || []);
            
        } catch (error) {
            console.error('加载备份历史失败:', error);
            document.getElementById('backupHistoryBody').innerHTML = `
                <tr>
                    <td colspan="4" class="text-center text-muted">
                        <i class="bi bi-exclamation-triangle me-1"></i>加载失败
                    </td>
                </tr>
            `;
        }
    }
    
    /**
     * 显示备份历史
     */
    displayBackupHistory(backups) {
        const tbody = document.getElementById('backupHistoryBody');
        const showMoreDiv = document.getElementById('showMoreBackupHistory');
        
        if (backups.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center text-muted">
                        <i class="bi bi-inbox me-1"></i>暂无备份记录
                    </td>
                </tr>
            `;
            showMoreDiv.style.display = 'none';
            return;
        }
        
        // 默认显示最近5次
        const displayCount = this.showAllHistory ? backups.length : Math.min(5, backups.length);
        const displayBackups = backups.slice(0, displayCount);
        
        tbody.innerHTML = displayBackups.map(backup => {
            const backupTime = new Date(backup.backup_time).toLocaleString('zh-CN');
            const backupMode = backup.backup_mode === 'full' ? '全量' : '增量';
            const backupSize = this.formatSize(backup.size || 0);
            const backupPath = backup.backup_path || '';
            
            // 原图显示：文件数（实际/总数）和大小（实际/总数）
            let originalsDisplay = '-';
            if (backup.originals) {
                const { total_files, copied_files, total_size, copied_size } = backup.originals;
                const filesText = `${(copied_files || 0).toLocaleString()}/${(total_files || 0).toLocaleString()} 个`;
                const sizeText = `${this.formatSize(copied_size || 0)}/${this.formatSize(total_size || 0)}`;
                originalsDisplay = `<small>${filesText}<br>${sizeText}</small>`;
            } else {
                // 向后兼容：如果没有 originals 字段，使用旧的 total_files 和 copied_files
                if (backup.total_files !== undefined && backup.copied_files !== undefined) {
                    const filesText = `${backup.copied_files.toLocaleString()}/${backup.total_files.toLocaleString()} 个`;
                    originalsDisplay = `<small>${filesText}</small>`;
                }
            }
            
            // 缩略图显示：文件数（实际/总数）和大小（实际/总数）
            let thumbnailsDisplay = '-';
            if (backup.thumbnails) {
                const { total_files, copied_files, total_size, copied_size } = backup.thumbnails;
                const filesText = `${(copied_files || 0).toLocaleString()}/${(total_files || 0).toLocaleString()} 个`;
                const sizeText = `${this.formatSize(copied_size || 0)}/${this.formatSize(total_size || 0)}`;
                thumbnailsDisplay = `<small>${filesText}<br>${sizeText}</small>`;
            }
            
            // 时长显示
            let elapsedDisplay = '-';
            if (backup.elapsed_time) {
                elapsedDisplay = backup.elapsed_time;
            } else if (backup.elapsed_seconds !== undefined && backup.elapsed_seconds !== null) {
                const hours = Math.floor(backup.elapsed_seconds / 3600);
                const minutes = Math.floor((backup.elapsed_seconds % 3600) / 60);
                const seconds = backup.elapsed_seconds % 60;
                elapsedDisplay = `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            }
            
            return `
                <tr>
                    <td><small>${backupTime}</small></td>
                    <td class="d-none d-md-table-cell"><small class="text-truncate d-inline-block" style="max-width: 200px;" title="${backupPath}">
                        ${backupPath}
                    </small></td>
                    <td><span class="badge ${backupMode === '全量' ? 'bg-warning' : 'bg-success'}">${backupMode}</span></td>
                    <td>${originalsDisplay}</td>
                    <td>${thumbnailsDisplay}</td>
                    <td class="d-none d-lg-table-cell"><small>${backupSize}</small></td>
                    <td><small>${elapsedDisplay}</small></td>
                </tr>
            `;
        }).join('');
        
        // 显示"显示更多"按钮
        if (backups.length > 5 && !this.showAllHistory) {
            showMoreDiv.style.display = 'block';
        } else {
            showMoreDiv.style.display = 'none';
        }
    }
    
    /**
     * 格式化文件大小
     */
    formatSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }
}

// 初始化备份管理器
let backupManager;
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('backupBtn')) {
        backupManager = new BackupManager();
    }
});

