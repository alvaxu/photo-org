/**
 * 家庭版智能照片系统 - 导入功能模块
 * 
 * 功能：
 * 1. 导入方式切换
 * 2. 文件导入处理
 * 3. 文件夹导入处理
 * 4. 导入进度监控
 * 5. 智能通知系统（统一格式、详细结果、模态框展示）
 * 
 * 更新日志：
 * - 2025-01-19: 完善导入和智能通知系统
 *   - 统一通知格式：显示总数、成功、跳过、失败数量
 *   - 添加图标区分：✅全部成功、⚠️有跳过、❌有失败
 *   - 添加"查看详情"按钮，显示详细结果模态框
 *   - 通知不再自动消失，需用户手动关闭
 */

/**
 * 模态框保护器 - 防止意外关闭
 * 支持多个模态框的保护，确保长时间运行任务不被意外中断
 */
class ModalProtector {
    constructor(modalId) {
        this.modalId = modalId;
        this.isProtected = false;
        this.modalElement = null;
        this.closeHandler = null;
    }

    /**
     * 初始化保护器
     * 延迟初始化，确保DOM已加载且不影响页面启动
     */
    initialize() {
        if (this.modalElement) return; // 已初始化

        // 延迟到DOM完全加载后再初始化，避免影响页面启动
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.doInitialize();
            });
        } else {
            this.doInitialize();
        }
    }

    /**
     * 执行初始化
     */
    doInitialize() {
        this.modalElement = document.getElementById(this.modalId);
        if (!this.modalElement) {
            console.warn(`ModalProtector[${this.modalId}]: 找不到模态框元素`);
            return;
        }

        console.log(`ModalProtector[${this.modalId}]: 初始化完成`);
    }

    /**
     * 启用保护模式
     */
    protect() {
        this.initialize(); // 确保已初始化

        if (this.isProtected || !this.modalElement) return;

        this.isProtected = true;
        console.log(`ModalProtector[${this.modalId}]: 启用保护模式`);

        // 显示保护提示
        this.showProtectionMessage();

        // 设置事件监听器（双重保护）
        this.setupClosePrevention();

        // 基础分析模态框不再需要取消按钮保护（已移除取消按钮）
    }

    /**
     * 解除保护模式
     */
    unprotect() {
        if (!this.isProtected || !this.modalElement) return;

        this.isProtected = false;
        console.log(`ModalProtector[${this.modalId}]: 解除保护模式`);

        // 隐藏保护提示
        this.hideProtectionMessage();

        // 移除事件监听器
        this.removeClosePrevention();

        // 基础分析模态框不再需要取消按钮恢复（已移除取消按钮）
    }

    /**
     * 显示保护提示
     */
    showProtectionMessage() {
        if (!this.modalElement) return;

        const header = this.modalElement.querySelector('.modal-header');
        if (header && !header.querySelector('.protection-message')) {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'protection-message alert alert-warning py-2 mb-2';
            messageDiv.innerHTML = `
                <i class="bi bi-shield-lock-fill me-2"></i>
                <small class="fw-bold">
                    ${this.modalId === 'basicModal' ? '基础分析' : '导入'}进行中，此窗口无法关闭<br>
                    请等待任务完成，不要关闭此页面
                </small>
            `;
            header.insertBefore(messageDiv, header.firstChild);
        }
    }

    /**
     * 隐藏保护提示
     */
    hideProtectionMessage() {
        if (!this.modalElement) return;

        const message = this.modalElement.querySelector('.protection-message');
        if (message) {
            message.remove();
        }
    }

    /**
     * 设置关闭阻止监听器
     */
    setupClosePrevention() {
        if (!this.modalElement || this.closeHandler) return;

        this.closeHandler = this.preventClose.bind(this);
        this.modalElement.addEventListener('hide.bs.modal', this.closeHandler);
    }

    /**
     * 移除关闭阻止监听器
     */
    removeClosePrevention() {
        if (!this.modalElement || !this.closeHandler) return;

        this.modalElement.removeEventListener('hide.bs.modal', this.closeHandler);
        this.closeHandler = null;
    }

    /**
     * 阻止关闭的处理函数
     */
    preventClose(event) {
        if (this.isProtected) {
            console.log(`ModalProtector[${this.modalId}]: 阻止模态框关闭 - 保护模式激活`);
            event.preventDefault();
            event.stopPropagation();
            return false;
        }
    }

}

// 创建全局实例 - 延迟初始化，不影响页面启动
window.importModalProtector = new ModalProtector('importModal');
window.basicModalProtector = new ModalProtector('basicModal');
window.aiModalProtector = new ModalProtector('aiModal');

/**
 * 在导入模态框内显示错误信息
 * 
 * @param {string} message - 错误信息
 */
function showImportError(message) {
    const errorDiv = document.getElementById('importError');
    const errorMessage = document.getElementById('importErrorMessage');
    
    if (errorDiv && errorMessage) {
        errorMessage.textContent = message;
        errorDiv.classList.remove('d-none');
        
        // 滚动到错误信息位置
        errorDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } else {
        // 如果找不到模态框内的错误元素，回退到页面顶部显示
        showError(message);
    }
}

/**
 * 隐藏导入模态框内的错误信息
 */
function hideImportError() {
    const errorDiv = document.getElementById('importError');
    if (errorDiv) {
        errorDiv.classList.add('d-none');
    }
}

/**
 * 切换导入方式
 * 
 * @param {string} method - 导入方式 ('file' 或 'folder')
 */
function switchImportMethod(method) {
    // 移除调试日志
    
    // 切换时隐藏错误信息
    hideImportError();
    
    const fileSection = document.getElementById('fileImportSection');
    const folderSection = document.getElementById('folderImportSection');
    
    if (method === 'file') {
        fileSection.classList.remove('d-none');
        fileSection.style.display = 'block';
        folderSection.classList.add('d-none');
        folderSection.style.display = 'none';
    } else if (method === 'folder') {
        fileSection.classList.add('d-none');
        fileSection.style.display = 'none';
        folderSection.classList.remove('d-none');
        folderSection.style.display = 'block';
    }
}

/**
 * 处理文件夹路径变化
 */
function handleFolderPathChange() {
    // 文件夹路径变化处理 - 现在只用于文件夹导入模式
    // 文件导入模式已改为自动开始，无需按钮控制
}

/**
 * 浏览文件夹
 */
function browseFolder() {
    // 触发隐藏的文件夹选择输入框
    const folderFilesInput = document.getElementById('folderFiles');
    if (folderFilesInput) {
        // 先清空之前的选择，避免浏览器缓存
        folderFilesInput.value = '';
        folderFilesInput.click();
    } else {
        console.error('找不到文件夹输入框');
    }
}

/**
 * 处理文件夹选择事件
 * 
 * @param {Event} event - 文件选择事件
 */
function handleFolderSelection(event) {
    /**
     * 处理文件夹选择事件
     * 
     * @param {Event} event - 文件选择事件
     */
    const files = event.target.files;
    
    // 隐藏之前的错误信息
    hideImportError();
    
    // 清空文件导入的预览数据
    hideFilePreview();
    
    if (files && files.length > 0) {
        // 获取第一个文件的路径，去掉文件名得到文件夹路径
        const firstFile = files[0];
        const filePath = firstFile.webkitRelativePath || firstFile.name;
        const folderPath = filePath.substring(0, filePath.lastIndexOf('/'));
        
        // 处理文件夹路径
        
        // 显示文件夹路径
        elements.folderPath.value = folderPath;
        
        // 显示选择的文件数量
        const imageFiles = Array.from(files).filter(file => {
            // 检查MIME类型
            const isImageByType = file.type.startsWith('image/');
            // 检查文件扩展名（Windows对HEIC文件MIME类型支持有问题）
            const ext = file.name.split('.').pop().toLowerCase();
            const isImageByExt = ['jpg', 'jpeg', 'png', 'tiff', 'tif', 'webp', 'bmp', 'gif', 'heic', 'heif'].includes(ext);
            
            return isImageByType || isImageByExt;
        });
        // 显示选择的文件数量
        
        // 更新导入按钮状态
        handleFolderPathChange();
        
        // 延迟显示文件预览信息，确保浏览器确认对话框关闭后再显示
        setTimeout(() => {
            previewFolderContents(files);
            // 文件预览已显示
        }, 100);
    } else {
        console.log('❌ 没有选择任何文件');
    }
}

/**
 * 预览文件夹内容
 * 
 * @param {FileList} files - 选择的文件列表
 */
function previewFolderContents(files) {
    const stats = analyzeFiles(files);
    
    // 显示预览区域
    const previewDiv = document.getElementById('folderPreview');
    if (previewDiv) {
        previewDiv.style.display = 'block';
    }
    
    displayFileStats(stats);
    checkFileLimit(stats.count);
    
    // 显示确认按钮
    showImportConfirmation(stats);
}

/**
 * 分析文件统计信息
 * 
 * @param {FileList} files - 文件列表
 * @returns {Object} 统计信息
 */
function analyzeFiles(files) {
    // 先过滤出图片文件
    const imageFiles = Array.from(files).filter(file => {
        // 检查MIME类型
        const isImageByType = file.type.startsWith('image/');
        // 检查文件扩展名（Windows对HEIC文件MIME类型支持有问题）
        const ext = file.name.split('.').pop().toLowerCase();
        const isImageByExt = ['jpg', 'jpeg', 'png', 'tiff', 'tif', 'webp', 'bmp', 'gif', 'heic', 'heif'].includes(ext);
        
        return isImageByType || isImageByExt;
    });
    
    const stats = {
        count: imageFiles.length,
        formats: {},
        totalSize: 0,
        supportedFiles: imageFiles.length  // 所有过滤后的文件都是支持的
    };
    
    // 分析每个图片文件
    for (let file of imageFiles) {
        stats.totalSize += file.size;
        
        const ext = file.name.split('.').pop().toLowerCase();
        stats.formats[ext] = (stats.formats[ext] || 0) + 1;
    }
    
    return stats;
}

/**
 * 检查文件格式是否支持
 * 
 * @param {string} ext - 文件扩展名
 * @returns {boolean} 是否支持
 */
function isSupportedFormat(ext) {
    const supported = ['jpg', 'jpeg', 'png', 'tiff', 'tif', 'webp', 'bmp', 'gif', 'heic', 'heif'];
    return supported.includes(ext.toLowerCase());
}

/**
 * 格式化文件大小
 * 
 * @param {number} bytes - 字节数
 * @returns {string} 格式化后的大小
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * 显示文件统计信息
 * 
 * @param {Object} stats - 统计信息
 */
function displayFileStats(stats) {
    const statsDiv = document.getElementById('fileStats');
    if (!statsDiv) {
        console.error('找不到文件统计显示区域');
        return;
    }
    
    statsDiv.innerHTML = `
        <div class="row">
            <div class="col-md-6">
                <div class="d-flex justify-content-between mb-2">
                    <span class="text-muted">文件总数：</span>
                    <strong>${stats.count}</strong>
                </div>
                <div class="d-flex justify-content-between mb-2">
                    <span class="text-muted">支持格式：</span>
                    <strong>${stats.supportedFiles}</strong>
                </div>
            </div>
            <div class="col-md-6">
                <div class="d-flex justify-content-between mb-2">
                    <span class="text-muted">文件大小：</span>
                    <strong>${formatFileSize(stats.totalSize)}</strong>
                </div>
                <div class="d-flex justify-content-between mb-2">
                    <span class="text-muted">格式分布：</span>
                    <strong>${Object.entries(stats.formats).map(([ext, count]) => `${ext}: ${count}`).join(', ')}</strong>
                </div>
            </div>
        </div>
    `;
}

/**
 * 检查文件数量限制
 * 
 * @param {number} fileCount - 文件数量
 */
function checkFileLimit(fileCount) {
    const maxFiles = window.CONFIG?.importConfig?.max_upload_files || 50;
    const limitDiv = document.getElementById('limitCheck');
    
    if (!limitDiv) {
        console.error('找不到限制检查显示区域');
        return;
    }
    
    if (fileCount > maxFiles) {
        limitDiv.innerHTML = `
            <div class="alert alert-warning d-flex align-items-center">
                <i class="bi bi-exclamation-triangle-fill me-2"></i>
                <div>
                    <strong>文件数量超限</strong><br>
                    <small>当前选择 ${fileCount} 个文件，超过限制 ${maxFiles} 个文件。建议分批导入或减少文件数量。</small>
                </div>
            </div>
        `;
    } else {
        limitDiv.innerHTML = `
            <div class="alert alert-success d-flex align-items-center">
                <i class="bi bi-check-circle-fill me-2"></i>
                <div>
                    <strong>文件数量正常</strong><br>
                    <small>当前选择 ${fileCount} 个文件，符合导入要求。</small>
                </div>
            </div>
        `;
    }
}

/**
 * 显示文件预览信息
 * 
 * @param {Array} files - 文件列表
 */
function showFilePreview(files) {
    console.log('📋 显示文件预览，文件数量:', files.length);

    // 分析文件信息
    const stats = analyzeFiles(files);
    console.log('📊 文件统计信息:', stats);

    // 显示文件统计信息
    displayFileStats(stats);

    // 检查文件数量限制
    checkFileLimit(files.length);

    // 显示确认按钮
    showFileImportConfirmation(stats);
    console.log('✅ 文件预览显示完成');
}

/**
 * 显示文件导入确认按钮
 * 
 * @param {Object} stats - 统计信息
 */
function showFileImportConfirmation(stats) {
    console.log('🔘 显示文件导入确认按钮，统计信息:', stats);

    // 创建确认按钮区域
    const confirmDiv = document.getElementById('fileImportConfirmation');
    console.log('确认按钮区域元素:', confirmDiv);
    if (!confirmDiv) {
        // 如果不存在，创建一个
        const fileImportSection = document.getElementById('fileImportSection');
        const confirmArea = document.createElement('div');
        confirmArea.id = 'fileImportConfirmation';
        confirmArea.className = 'mt-3';
        fileImportSection.appendChild(confirmArea);
    }
    
    const confirmDivElement = document.getElementById('fileImportConfirmation');
    confirmDivElement.style.display = 'block'; // 确保显示
    confirmDivElement.innerHTML = `
        <div class="card">
            <div class="card-header">
                <h6 class="mb-0">
                    <i class="bi bi-file-earmark-image me-2"></i>
                    文件预览与确认
                </h6>
            </div>
            <div class="card-body">
                <!-- 文件统计信息 -->
                <div id="fileStats" class="mb-3"></div>
                
                <!-- 限制检查 -->
                <div id="limitCheck" class="mb-3"></div>
                
                <!-- 确认按钮 -->
                <div class="border-top pt-3">
                    <div class="text-center mb-3">
                        <h6 class="text-muted">准备导入 ${stats.count} 个文件</h6>
                        <p class="small text-muted mb-0">其中 ${stats.supportedFiles} 个为支持的图片格式，总大小 ${formatFileSize(stats.totalSize)}</p>
                    </div>
                    <div class="d-flex justify-content-center gap-3">
                        <button class="btn btn-primary px-4" onclick="confirmFileImport()">
                            <i class="bi bi-check-circle me-2"></i>开始导入
                        </button>
                        <button class="btn btn-outline-secondary px-4" onclick="cancelFileImport()">
                            <i class="bi bi-x-circle me-2"></i>取消
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 重新显示统计信息
    displayFileStats(stats);
    checkFileLimit(stats.count);
}

/**
 * 确认文件导入
 */
function confirmFileImport() {
    // 隐藏预览信息
    hideFilePreview();
    
    // 开始文件导入
    startFileImport();
}

/**
 * 取消文件导入
 */
function cancelFileImport() {
    // 清空文件选择
    const fileInput = document.getElementById('photoFiles');
    if (fileInput) {
        fileInput.value = '';
    }
    
    // 隐藏预览信息
    hideFilePreview();
}

/**
 * 隐藏文件预览
 */
function hideFilePreview() {
    const confirmDiv = document.getElementById('fileImportConfirmation');
    if (confirmDiv) {
        confirmDiv.innerHTML = '';
    }
}

/**
 * 显示导入确认按钮
 * 
 * @param {Object} stats - 统计信息
 */
function showImportConfirmation(stats) {
    const confirmDiv = document.getElementById('importConfirmation');
    if (!confirmDiv) {
        console.error('找不到导入确认显示区域');
        return;
    }
    
    confirmDiv.innerHTML = `
        <div class="border-top pt-3">
            <div class="text-center mb-3">
                <h6 class="text-muted">准备导入 ${stats.count} 个文件</h6>
                <p class="small text-muted mb-0">其中 ${stats.supportedFiles} 个为支持的图片格式，总大小 ${formatFileSize(stats.totalSize)}</p>
            </div>
            <div class="d-flex justify-content-center gap-3">
                <button class="btn btn-primary px-4" onclick="confirmFolderImport()">
                    <i class="bi bi-check-circle me-2"></i>确认导入
                </button>
                <button class="btn btn-outline-secondary px-4" onclick="cancelFolderImport()">
                    <i class="bi bi-x-circle me-2"></i>取消
                </button>
            </div>
        </div>
    `;
}

/**
 * 确认文件夹导入
 */
function confirmFolderImport() {
    console.log('✅ 用户确认文件夹导入');
    startFolderImport();
}

/**
 * 取消文件夹导入
 */
function cancelFolderImport() {
    console.log('❌ 用户取消文件夹导入');
    // 清空文件选择
    const folderFilesInput = document.getElementById('folderFiles');
    if (folderFilesInput) {
        folderFilesInput.value = '';
    }
    
    // 清空路径显示
    elements.folderPath.value = '';
    
    // 隐藏预览信息
    hideFolderPreview();
    
    // 更新按钮状态
    handleFolderPathChange();
}

/**
 * 隐藏文件夹预览信息
 */
function hideFolderPreview() {
    const statsDiv = document.getElementById('fileStats');
    const limitDiv = document.getElementById('limitCheck');
    const confirmDiv = document.getElementById('importConfirmation');
    const previewDiv = document.getElementById('folderPreview');
    
    if (statsDiv) statsDiv.innerHTML = '';
    if (limitDiv) limitDiv.innerHTML = '';
    if (confirmDiv) confirmDiv.innerHTML = '';
    if (previewDiv) previewDiv.style.display = 'none';
}

/**
 * 验证文件夹路径格式
 * 
 * @param {string} path - 路径字符串
 * @returns {boolean} 是否有效
 */
function validateFolderPath(path) {
    /**
     * 验证文件夹路径格式
     * 
     * @param {string} path - 路径字符串
     * @returns {boolean} 是否有效
     */
    if (!path || path.trim().length === 0) {
        return false;
    }
    
    // 检查是否包含非法字符
    const invalidChars = /[<>:"|?*]/;
    if (invalidChars.test(path)) {
        return false;
    }
    
    // 检查路径长度
    if (path.length > 260) {
        return false;
    }
    
    return true;
}

/**
 * 开始导入
 */
async function startImport() {
    // 检查配置和状态
    
    const importMethod = document.querySelector('input[name="importMethod"]:checked').value;
    // 获取选择的导入方式
    
    if (importMethod === 'file') {
        // 执行文件导入
        await startFileImport();
    } else if (importMethod === 'folder') {
        // 执行文件夹导入
        await startFolderImport();
    } else {
        console.error('未知的导入方式:', importMethod);
        showError('未知的导入方式，请重新选择');
    }
}

/**
 * 开始文件导入
 */
// 分批上传文件的函数
async function uploadFilesInBatches(allFiles, batchSize = 100) {
    const results = [];
    const totalBatches = Math.ceil(allFiles.length / batchSize);
    const totalFiles = allFiles.length;

    // 显示分批上传状态
    elements.importStatus.textContent = `正在分批上传 ${totalFiles} 个文件，共${totalBatches}批...`;
    elements.importDetails.textContent = `准备开始分批处理...`;

    // 初始化进度条为0
    elements.importProgressBar.style.width = '0%';
    elements.importProgressBar.setAttribute('aria-valuenow', '0');

    for (let i = 0; i < totalBatches; i++) {
        const start = i * batchSize;
        const end = Math.min(start + batchSize, allFiles.length);
        const batchFiles = Array.from(allFiles).slice(start, end);

        // 更新当前批次状态
        const currentProgress = Math.round((i / totalBatches) * 100);
        elements.importProgressBar.style.width = `${currentProgress}%`;
        elements.importProgressBar.setAttribute('aria-valuenow', currentProgress);
        elements.importDetails.textContent = `正在上传第${i + 1}/${totalBatches}批: ${batchFiles.length}个文件...`;

        try {
            const formData = new FormData();
            batchFiles.forEach(file => {
                formData.append('files', file);
            });

            const response = await fetch('/api/v1/import/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                results.push({
                    batchIndex: i + 1,
                    taskId: data.data.task_id,
                    files: batchFiles.length,
                    success: true
                });

                // 批次上传成功，显示成功状态
                elements.importDetails.textContent = `第${i + 1}批上传成功 (${batchFiles.length}个文件)`;
            } else {
                results.push({
                    batchIndex: i + 1,
                    files: batchFiles.length,
                    success: false,
                    error: data.message || '上传失败'
                });

                // 批次上传失败
                elements.importDetails.textContent = `第${i + 1}批上传失败: ${data.message || '未知错误'}`;
            }
        } catch (error) {
            results.push({
                batchIndex: i + 1,
                files: batchFiles.length,
                success: false,
                error: error.message
            });

            // 批次上传出错
            elements.importDetails.textContent = `第${i + 1}批上传出错: ${error.message}`;
        }
    }

    // 所有批次上传完成
    elements.importProgressBar.style.width = '100%';
    elements.importProgressBar.setAttribute('aria-valuenow', '100');
    elements.importStatus.textContent = `所有批次上传完成，正在后台处理...`;
    elements.importDetails.textContent = `共上传${results.filter(r => r.success).length}/${totalBatches}批成功`;

    return results;
}

async function startFileImport() {
    // 开始文件导入

    // 确保用户配置已加载
    if (!window.userConfig) {
        // 加载用户配置
        await loadUserConfig();
    }

    const files = elements.photoFiles.files;

    if (files.length === 0) {
        showImportError('请先选择要导入的照片文件');
        return;
    }

    // 🔒 启用模态框保护，防止意外关闭
    window.importModalProtector.protect();

    // 如果文件数量超过阈值，使用分批上传（获得并行处理优势）
    const BATCH_THRESHOLD = CONFIG.importConfig?.batch_threshold || 200;
    if (files.length > BATCH_THRESHOLD) {
        // 文件数量超过阈值，使用分批上传

        // 隐藏之前的错误信息
        hideImportError();

        // 显示进度条
        elements.importProgress.classList.remove('d-none');
        elements.importProgressBar.style.width = '0%';
        elements.importProgressBar.setAttribute('aria-valuenow', '0');
        elements.importStatus.textContent = `准备分批上传 ${files.length} 个文件...`;
        elements.importDetails.textContent = '正在初始化分批处理...';

        // 隐藏统计信息
        elements.importStats.style.display = 'none';

        try {
            const batchSize = CONFIG.importConfig?.scan_batch_size || 100;
            // 使用配置的导入批次大小
            const batchResults = await uploadFilesInBatches(files, batchSize);

            // 统计结果
            const successfulBatches = batchResults.filter(r => r.success);
            const failedBatches = batchResults.filter(r => !r.success);

            if (failedBatches.length > 0) {
                showImportError(`分批上传完成，但${failedBatches.length}批失败: ${failedBatches.map(f => `第${f.batchIndex}批(${f.error})`).join(', ')}`);
                return;
            }

            // 所有批次上传成功，开始监控批次完成状态
            // 所有批次上传成功

            // 收集所有批次的任务ID
            const batchTaskIds = successfulBatches.map(batch => batch.taskId);
            // 收集批次任务ID

            // 开始监控批次聚合状态
            monitorBatchProgress(batchTaskIds, files.length);

        } catch (error) {
            console.error('分批上传失败:', error);
            // ❌ 出错时解除保护
            window.importModalProtector.unprotect();
            showImportError(`分批上传失败: ${error.message}`);
        }

        return;
    }
    
    // 隐藏之前的错误信息
    hideImportError();
    
    // 显示进度条
    elements.importProgress.classList.remove('d-none');
    elements.importProgressBar.style.width = '0%';
    elements.importProgressBar.setAttribute('aria-valuenow', '0');
    elements.importStatus.textContent = `正在准备处理 ${files.length} 个文件...`;
    elements.importDetails.textContent = '请稍候...';

    // 隐藏统计信息
    elements.importStats.style.display = 'none';
    
    try {
        // 创建FormData对象
        const formData = new FormData();
        Array.from(files).forEach(file => {
            formData.append('files', file);
        });
        
        // 使用XMLHttpRequest替代fetch以获取上传进度
        const xhr = new XMLHttpRequest();

        // 上传进度事件监听器
        let lastReportedProgress = 0;
        let uploadStartTime = Date.now();
        let lastLoaded = 0;
        let lastTime = uploadStartTime;

        xhr.upload.addEventListener('progress', (event) => {
            if (event.lengthComputable) {
                const percentComplete = Math.round((event.loaded / event.total) * 100);
                const currentTime = Date.now();

                // 计算上传速度
                const timeDiff = (currentTime - lastTime) / 1000; // 秒
                const loadedDiff = event.loaded - lastLoaded; // 字节
                const speedBps = loadedDiff / timeDiff; // 字节/秒
                const speedMBps = speedBps / (1024 * 1024); // MB/s

                // 估算剩余时间
                const remainingBytes = event.total - event.loaded;
                const etaSeconds = speedBps > 0 ? remainingBytes / speedBps : 0;
                const etaText = etaSeconds > 0 ?
                    (etaSeconds < 60 ? `${Math.round(etaSeconds)}秒` : `${Math.round(etaSeconds/60)}分钟`) : '';

                // 更新变量
                lastLoaded = event.loaded;
                lastTime = currentTime;

                // 避免过于频繁的更新（至少1%的变化才更新）
                if (percentComplete - lastReportedProgress >= 1 || percentComplete === 100) {
                    elements.importProgressBar.style.width = `${percentComplete}%`;
                    elements.importProgressBar.setAttribute('aria-valuenow', percentComplete);
                    elements.importStatus.textContent = `正在上传 ${files.length} 个文件... ${percentComplete}%`;
                    elements.importDetails.textContent = speedMBps > 0 ?
                        `速度: ${speedMBps.toFixed(2)} MB/s${etaText ? ` | 剩余: ${etaText}` : ''}` : '正在计算速度...';
                    lastReportedProgress = percentComplete;
                }
            }
        });

        // 上传开始
        xhr.upload.addEventListener('loadstart', () => {
            elements.importStatus.textContent = `开始上传 ${files.length} 个文件...`;
        });

        // 上传完成
        xhr.upload.addEventListener('load', () => {
            elements.importProgressBar.style.width = '100%';
            elements.importProgressBar.setAttribute('aria-valuenow', '100');
            elements.importStatus.textContent = `上传完成，正在准备后台处理...`;
            elements.importDetails.textContent = `已上传 ${files.length} 个文件，正在初始化处理任务...`;
            console.log('文件上传完成，立即显示后台处理进度条...');

            // 文件上传完成后显示等待状态
            setTimeout(() => {
                elements.importProgressBar.style.width = '50%';
                elements.importProgressBar.setAttribute('aria-valuenow', '50');
                elements.importStatus.textContent = `后台正在处理 ${files.length} 个文件...`;
                elements.importDetails.textContent = '正在等待服务器响应...';
                console.log('进度条显示等待服务器响应状态...');
            }, 300); // 短暂延迟，让用户看到上传完成状态
        });

        // 请求完成
        xhr.addEventListener('load', () => {
            // 检查HTTP状态码
            if (xhr.status === 200 || xhr.status === 202) {
                try {
                    const data = JSON.parse(xhr.responseText);

                    // 获取任务ID并开始进度监控
                    if (data.success && data.data.task_id) {
                        const taskId = data.data.task_id;
                        console.log('开始监控文件处理进度，总文件数:', files.length);

                        // 获取到task_id，立即开始监控实际进度
                        elements.importDetails.textContent = '正在初始化处理任务...';

                        monitorImportProgress(taskId, files.length);
                    } else {
                        console.error('服务器响应中未找到任务ID:', data);
                        showImportError(data.message || '导入失败');
                        elements.importProgress.classList.add('d-none');
                    }
                } catch (parseError) {
                    console.error('解析响应失败:', parseError);
                    showImportError('服务器响应格式错误');
                    elements.importProgress.classList.add('d-none');
                }
            } else {
                try {
                    const errorData = JSON.parse(xhr.responseText);
                    const errorMessage = errorData.detail || errorData.message || '请求失败';
                    showImportError(`上传失败：${errorMessage}`);
                } catch (parseError) {
                    showImportError('上传失败：服务器响应错误');
                }
                elements.importProgress.classList.add('d-none');
            }
        });

        // 错误处理
        xhr.addEventListener('error', () => {
            console.error('网络请求失败');
            elements.importStatus.textContent = '网络连接失败';
            elements.importDetails.textContent = '请检查网络连接和服务器状态';
            elements.importProgressBar.classList.remove('progress-bar-striped', 'progress-bar-animated');
            elements.importProgressBar.classList.add('bg-danger');
            showImportError('网络连接失败，请检查服务器是否正常运行');
        });

        // 发送请求
        xhr.open('POST', `${CONFIG.API_BASE_URL}/import/upload`);
        xhr.send(formData);
        
    } catch (error) {
        console.error('文件导入失败:', error);

        // ❌ 出错时解除保护
        window.importModalProtector.unprotect();

        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            showImportError('网络连接失败，请检查服务器是否正常运行');
        } else {
            showImportError(`文件导入失败：${error.message}\n\n请稍后重试或检查网络连接`);
        }
        elements.importProgress.classList.add('d-none');
    }
}

/**
 * 开始文件夹导入
 */
async function startFolderImport() {
    // 开始目录扫描导入

    // 确保用户配置已加载
    if (!window.userConfig) {
        // 加载用户配置
        await loadUserConfig();
    }
    
    // 获取选择的文件
    const folderFilesInput = document.getElementById('folderFiles');
    console.log('文件夹输入框:', folderFilesInput);
    const files = folderFilesInput.files;
    console.log('选择的文件数量:', files?.length || 0);
    
    if (!files || files.length === 0) {
        console.error('没有选择任何文件');
        showImportError('请先选择照片目录');
        return;
    }

    // 🔒 启用模态框保护，防止意外关闭
    window.importModalProtector.protect();

    // 过滤出图片文件
    const imageFiles = Array.from(files).filter(file => {
        // 检查MIME类型
        const isImageByType = file.type.startsWith('image/');
        // 检查文件扩展名（Windows对HEIC文件MIME类型支持有问题）
        const ext = file.name.split('.').pop().toLowerCase();
        const isImageByExt = ['jpg', 'jpeg', 'png', 'tiff', 'tif', 'webp', 'bmp', 'gif', 'heic', 'heif'].includes(ext);
        
        return isImageByType || isImageByExt;
    });
    console.log('图片文件数量:', imageFiles.length);

    if (imageFiles.length === 0) {
        showImportError('选择的目录中没有找到图片文件');
        return;
    }

    // 如果文件数量超过阈值，使用分批上传（获得并行处理优势）
    const BATCH_THRESHOLD = CONFIG.importConfig?.batch_threshold || 200;
    if (imageFiles.length > BATCH_THRESHOLD) {
        // 目录文件数量超过阈值，使用分批上传

        // 隐藏之前的错误信息
        hideImportError();

        // 隐藏预览信息
        hideFolderPreview();

        // 显示进度条
        elements.importProgress.classList.remove('d-none');
        elements.importProgressBar.style.width = '0%';
        elements.importProgressBar.setAttribute('aria-valuenow', '0');
        elements.importStatus.textContent = `准备分批上传目录中的 ${imageFiles.length} 个文件...`;
        elements.importDetails.textContent = '正在初始化分批处理...';

        // 隐藏统计信息
        elements.importStats.style.display = 'none';

        try {
            const batchSize = CONFIG.importConfig?.scan_batch_size || 100;
            // 使用配置的导入批次大小
            const batchResults = await uploadFilesInBatches(imageFiles, batchSize);

            // 统计上传结果
            const successfulBatches = batchResults.filter(r => r.success);
            const failedBatches = batchResults.filter(r => !r.success);
            const totalSuccessfulFiles = successfulBatches.reduce((sum, b) => sum + b.files, 0);
            const totalFailedFiles = failedBatches.reduce((sum, b) => sum + b.files, 0);

            if (successfulBatches.length > 0) {
                // 有成功的批次，继续处理
                console.log(`目录批次上传：${successfulBatches.length}批成功(${totalSuccessfulFiles}文件)，${failedBatches.length}批失败(${totalFailedFiles}文件)`);

                // 收集成功批次的任务ID
                const successfulTaskIds = successfulBatches.map(batch => batch.taskId);
                // 监控成功批次任务ID

                // 开始监控成功的批次处理进度
                monitorBatchProgress(successfulTaskIds, totalSuccessfulFiles, failedBatches);

                // 根据失败情况给出不同提示
                if (failedBatches.length > 0) {
                    // 部分失败：显示警告信息
                    elements.importStatus.textContent = `⚠️ ${failedBatches.length}批上传失败，但将继续处理 ${totalSuccessfulFiles} 个成功上传的文件...`;
                    elements.importDetails.textContent = `上传结果：${successfulBatches.length}/${successfulBatches.length + failedBatches.length} 批成功，共 ${imageFiles.length} 个文件`;

                    // 在控制台显示失败详情
                    console.warn('上传失败的批次:', failedBatches.map(f => `第${f.batchIndex}批(${f.files}文件): ${f.error}`).join('; '));
                } else {
                    // 全部成功：正常显示
                    elements.importStatus.textContent = `所有批次上传成功，正在后台处理 ${totalSuccessfulFiles} 个文件...`;
                    elements.importDetails.textContent = `已提交 ${successfulBatches.length} 个后台处理任务`;
                }
            } else {
                // 全部失败：显示错误
                const errorMsg = failedBatches.map(f => `第${f.batchIndex}批: ${f.error}`).join('; ');
                showImportError(`目录分批上传失败：所有 ${failedBatches.length} 批均失败。错误详情：${errorMsg}`);
                return;
            }

        } catch (error) {
            console.error('目录分批上传失败:', error);
            showImportError(`目录分批上传失败: ${error.message}`);
        }

        return;
    }

    // 隐藏之前的错误信息
    hideImportError();

    // 隐藏预览信息
    hideFolderPreview();

    // 显示进度条
    elements.importProgress.classList.remove('d-none');
    elements.importProgressBar.style.width = '0%';
    elements.importStatus.textContent = `正在准备处理 ${imageFiles.length} 个文件...`;
    
    try {
        // 直接使用文件上传API处理选择的文件
        const formData = new FormData();
        imageFiles.forEach(file => {
            formData.append('files', file);
        });
        
        const apiUrl = `${window.CONFIG.API_BASE_URL}/import/upload`;
        // API调用
        console.log('发送的文件数量:', imageFiles.length);
        
        // 使用XMLHttpRequest替代fetch以获取上传进度
        const xhr = new XMLHttpRequest();

        // 上传进度事件监听器
        let lastReportedProgress = 0;
        xhr.upload.addEventListener('progress', (event) => {
            if (event.lengthComputable) {
                const percentComplete = Math.round((event.loaded / event.total) * 100);

                // 避免过于频繁的更新（至少1%的变化才更新）
                if (percentComplete - lastReportedProgress >= 1 || percentComplete === 100) {
                    elements.importProgressBar.style.width = `${percentComplete}%`;
                    elements.importStatus.textContent = `正在上传文件夹文件... ${percentComplete}% (${event.loaded}/${event.total} 字节)`;
                    lastReportedProgress = percentComplete;
                }
            }
        });

        // 上传开始
        xhr.upload.addEventListener('loadstart', () => {
            elements.importStatus.textContent = `开始上传 ${imageFiles.length} 个文件夹文件...`;
        });

        // 上传完成
        xhr.upload.addEventListener('load', () => {
            elements.importProgressBar.style.width = '100%';
            elements.importProgressBar.setAttribute('aria-valuenow', '100');
            elements.importStatus.textContent = `上传完成，正在准备后台处理...`;
            elements.importDetails.textContent = `已上传 ${imageFiles.length} 个文件，正在初始化处理任务...`;
            console.log('文件夹上传完成，立即显示后台处理进度条...');

            // 文件上传完成后立即重置进度条为后台处理状态
            setTimeout(() => {
                elements.importProgressBar.style.width = '0%';
                elements.importProgressBar.setAttribute('aria-valuenow', '0');
                elements.importStatus.textContent = `后台正在处理 ${imageFiles.length} 个文件...`;
                elements.importDetails.textContent = '正在等待服务器响应...';
                console.log('进度条已重置为后台处理状态，等待task_id...');
            }, 300); // 短暂延迟，让用户看到上传完成状态
        });

        // 请求完成
        xhr.addEventListener('load', () => {
            console.log('API响应状态:', xhr.status);

            // 检查HTTP状态码
            if (xhr.status === 200 || xhr.status === 202) {
                try {
                    const data = JSON.parse(xhr.responseText);

                    // 获取任务ID并开始进度监控
                    if (data.success && data.data.task_id) {
                        const taskId = data.data.task_id;
                        console.log('开始监控目录文件处理进度，总文件数:', imageFiles.length);

                        // 更新状态文本，进度条已经在上传完成后重置了
                        elements.importDetails.textContent = '正在初始化处理任务...';

                        monitorImportProgress(taskId, imageFiles.length);
                    } else {
                        console.error('服务器响应中未找到任务ID:', data);
                        showImportError(data.message || '导入失败');
                        elements.importProgress.classList.add('d-none');
                    }
                } catch (parseError) {
                    console.error('解析响应失败:', parseError);
                    showImportError('服务器响应格式错误');
                    elements.importProgress.classList.add('d-none');
                }
            } else {
                try {
                    const errorData = JSON.parse(xhr.responseText);
                    const errorMessage = errorData.detail || errorData.message || '请求失败';
                    showImportError(`上传失败：${errorMessage}`);
                } catch (parseError) {
                    showImportError('上传失败：服务器响应错误');
                }
                elements.importProgress.classList.add('d-none');
            }
        });

        // 错误处理
        xhr.addEventListener('error', () => {
            console.error('网络请求失败');
            elements.importStatus.textContent = '网络连接失败';
            elements.importDetails.textContent = '请检查网络连接和服务器状态';
            elements.importProgressBar.classList.remove('progress-bar-striped', 'progress-bar-animated');
            elements.importProgressBar.classList.add('bg-danger');
            showImportError('网络连接失败，请检查服务器是否正常运行');
        });

        // 发送请求
        xhr.open('POST', apiUrl);
        xhr.send(formData);
        
    } catch (error) {
        console.error('文件夹导入失败:', error);

        // ❌ 出错时解除保护
        window.importModalProtector.unprotect();

        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            showImportError('网络连接失败，请检查服务器是否正常运行');
        } else {
            showImportError(`文件夹导入失败：${error.message}\n\n请稍后重试或检查网络连接`);
        }
        elements.importProgress.classList.add('d-none');
    }
}

/**
 * 监控扫描任务进度
 * 
 * @param {string} taskId - 任务ID
 * @param {number} totalFiles - 总文件数
 */
async function monitorScanProgress(taskId, totalFiles) {
    /**
     * 监控扫描任务进度
     * 
     * @param {string} taskId - 任务ID
     * @param {number} totalFiles - 总文件数
     */
    let checkCount = 0;
    const maxChecks = 300; // 最多检查300次，每次2秒，总共10分钟
    
    const progressInterval = setInterval(async () => {
        checkCount++;
        
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/import/scan-status/${taskId}`);
            const statusData = await response.json();
            
            if (response.ok) {
                const progress = statusData.progress_percentage || 0;
                const processed = statusData.processed_files || 0;
                const imported = statusData.imported_count || 0;
                const skipped = statusData.skipped_count || 0;
                const failed = statusData.failed_count || 0;
                
                // 更新进度条
                elements.importProgressBar.style.width = `${progress}%`;
                elements.importStatus.textContent = `正在处理: ${processed}/${totalFiles} (${progress}%) - 已导入: ${imported}, 跳过: ${skipped}, 失败: ${failed}`;
                
                // 检查是否完成
                if (statusData.status === 'completed') {
                    clearInterval(progressInterval);
                    
                    // 直接显示导入结果详情模态框
                    showImportDetails(statusData);

                    // 重新加载照片列表
                    await loadPhotos();
                    await loadStats();
                    
                    // 关闭导入模态框
                    const modal = bootstrap.Modal.getInstance(elements.importModal);
                    if (modal) {
                        modal.hide();
                    }
                } else if (statusData.status === 'failed') {
                    clearInterval(progressInterval);
                    showError(`扫描失败：${statusData.error || '未知错误'}`);
                }
            } else {
                console.error('获取扫描状态失败:', statusData);
                if (checkCount >= maxChecks) {
                    clearInterval(progressInterval);
                    showError('扫描超时，请检查服务器状态');
                }
            }
        } catch (error) {
            console.error('监控扫描进度失败:', error);
            if (checkCount >= maxChecks) {
                clearInterval(progressInterval);
                showError('监控扫描进度失败，请检查网络连接');
            }
        }
    }, 2000); // 每2秒检查一次
    
    // 设置超时
    setTimeout(() => {
        clearInterval(progressInterval);
        showError('扫描超时，请检查服务器状态');
    }, 600000); // 10分钟超时
}



// ============ 全局导出 ============

// 将函数导出到全局作用域
window.showImportError = showImportError;
window.hideImportError = hideImportError;
window.switchImportMethod = switchImportMethod;
window.handleFolderPathChange = handleFolderPathChange;
window.browseFolder = browseFolder;
window.handleFolderSelection = handleFolderSelection;
window.validateFolderPath = validateFolderPath;




document.addEventListener('DOMContentLoaded', function() {
    // 基础分析按钮事件监听
    const basicAnalysisBtn = document.getElementById('basicAnalysisBtn');
    if (basicAnalysisBtn) {
        basicAnalysisBtn.addEventListener('click', startBasicAnalysis);
    }

    // AI分析按钮事件监听
    const aiAnalysisBtn = document.getElementById('aiAnalysisBtn');
    if (aiAnalysisBtn) {
        aiAnalysisBtn.addEventListener('click', startAIAnalysis);
    }

    // GPS转地址按钮事件监听
    const gpsToAddressBtn = document.getElementById('gpsToAddressBtn');
    if (gpsToAddressBtn) {
        gpsToAddressBtn.addEventListener('click', startBatchGpsToAddress);
    }

    // 基础分析模态框中的开始按钮事件监听
    const startBasicBtn = document.getElementById('startBasicBtn');
    if (startBasicBtn) {
        startBasicBtn.addEventListener('click', startBasicProcess);
    }

    // AI分析模态框中的开始按钮事件监听
    const startAIBtn = document.getElementById('startAIBtn');
    if (startAIBtn) {
        startAIBtn.addEventListener('click', startAIProcess);
    }
});

window.startImport = startImport;
window.startFileImport = startFileImport;
window.startFolderImport = startFolderImport;
window.monitorScanProgress = monitorScanProgress;
window.previewFolderContents = previewFolderContents;
window.analyzeFiles = analyzeFiles;
window.isSupportedFormat = isSupportedFormat;
window.formatFileSize = formatFileSize;
window.displayFileStats = displayFileStats;
window.checkFileLimit = checkFileLimit;
window.showFilePreview = showFilePreview;
window.showFileImportConfirmation = showFileImportConfirmation;
window.confirmFileImport = confirmFileImport;
window.cancelFileImport = cancelFileImport;
window.hideFilePreview = hideFilePreview;
window.showImportConfirmation = showImportConfirmation;
window.confirmFolderImport = confirmFolderImport;
window.cancelFolderImport = cancelFolderImport;
window.hideFolderPreview = hideFolderPreview;
window.startBasicAnalysis = startBasicAnalysis;
window.startAIAnalysis = startAIAnalysis;
window.startBasicProcess = startBasicProcess;
window.startAIProcess = startAIProcess;

/**
 * 监控导入任务进度
 * 
 * @param {string} taskId - 任务ID
 * @param {number} totalFiles - 总文件数量
 */
function monitorImportProgress(taskId, totalFiles) {
    let checkCount = 0;
    const maxChecks = 600; // 最多检查600次，每次1秒，总共10分钟

    console.log('开始监控文件处理进度，总文件数:', totalFiles);

    const progressInterval = setInterval(async () => {
        checkCount++;
        
        // 超时保护
        if (checkCount > maxChecks) {
            clearInterval(progressInterval);
            console.error('进度监控超时');

            // ❌ 超时/出错时解除保护
            window.importModalProtector.unprotect();

            elements.importStatus.textContent = '处理超时';
            elements.importDetails.textContent = '服务器处理时间过长，请检查服务器状态';
            elements.importProgressBar.classList.remove('progress-bar-striped', 'progress-bar-animated');
            elements.importProgressBar.classList.add('bg-warning');
            showError('导入超时，请检查服务器状态');
            return;
        }
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/import/scan-status/${taskId}`);

            if (!response.ok) {
                console.error('进度查询失败:', response.status, response.statusText);
                return;
            }

            const statusData = await response.json();

            // 更新进度条
            const progress = statusData.progress_percentage || 0;
            elements.importProgressBar.style.width = `${progress}%`;
            elements.importProgressBar.setAttribute('aria-valuenow', progress);

            // 更新状态文本
            elements.importStatus.textContent = `正在处理: ${statusData.processed_files || 0}/${totalFiles} (${progress}%)`;

            // 处理过程中始终隐藏统计面板，避免显示混乱
            elements.importStats.style.display = 'none';
            
            // 检查是否完成
            if (statusData.status === 'completed') {
                clearInterval(progressInterval);

                // ✅ 完成时解除保护，允许正常关闭
                window.importModalProtector.unprotect();

                // 更新最终状态显示
                elements.importProgressBar.style.width = '100%';
                elements.importProgressBar.setAttribute('aria-valuenow', '100');
                elements.importStatus.textContent = `处理完成！共处理 ${statusData.total_files} 个文件`;

                const imported = statusData.imported_count || 0;
                const skipped = statusData.skipped_count || 0;
                const failed = statusData.failed_count || 0;
                const totalProcessed = imported + skipped + failed;
                const successRate = totalProcessed > 0 ? ((imported / totalProcessed) * 100).toFixed(1) : '0.0';

                elements.importDetails.textContent = `处理完成，准备显示结果详情...`;

                // 转换数据格式以匹配showImportDetails的期望
                const detailsData = {
                    total_files: statusData.total_files,
                    imported_photos: statusData.imported_count,
                    skipped_photos: statusData.skipped_count,
                    failed_photos: statusData.failed_count,
                    failed_files: statusData.failed_files
                };

                // 【修改】先关闭导入模态框，然后监听关闭事件再显示结果
                const modal = bootstrap.Modal.getInstance(elements.importModal);
                if (modal) {
                    modal.hide();

                    // 监听模态框关闭事件，确保模态框完全消失后才显示结果
                    // 使用全局变量确保事件监听器能被正确移除
                    if (window.importModalCloseHandler) {
                        elements.importModal.removeEventListener('hidden.bs.modal', window.importModalCloseHandler);
                    }
                    
                    window.importModalCloseHandler = function() {
                        console.log('导入模态框已完全关闭，准备显示结果详情...');

                        // 移除事件监听器，避免重复执行
                        elements.importModal.removeEventListener('hidden.bs.modal', window.importModalCloseHandler);
                        window.importModalCloseHandler = null;

                        try {
                            // 显示导入结果详情
                            showImportDetails(detailsData);

                            // 重新加载照片列表
                            loadPhotos();
                            loadStats();
                        } catch (error) {
                            console.error('显示导入结果详情失败:', error);
                            showError('显示结果失败: ' + error.message);
                        }
                    };
                    
                    elements.importModal.addEventListener('hidden.bs.modal', window.importModalCloseHandler);
                } else {
                    // 如果找不到模态框实例，直接显示结果（降级处理）
                    console.warn('找不到导入模态框实例，直接显示结果');
                    showImportDetails(detailsData);
                    loadPhotos();
                    loadStats();
                }
                // 直接返回，避免继续执行后续的状态检查逻辑
                return;
            } else if (statusData.status === 'failed') {
                clearInterval(progressInterval);

                // 【修改】失败时也先关闭模态框再显示错误
                const modal = bootstrap.Modal.getInstance(elements.importModal);
                if (modal) {
                    modal.hide();

                    // 监听模态框关闭事件
                    elements.importModal.addEventListener('hidden.bs.modal', function onModalHidden() {
                        elements.importModal.removeEventListener('hidden.bs.modal', onModalHidden);
                        showError(`导入失败：${statusData.error || '未知错误'}`);
                        elements.importProgress.classList.add('d-none');
                    });
                } else {
                    // 降级处理
                    showError(`导入失败：${statusData.error || '未知错误'}`);
                    elements.importProgress.classList.add('d-none');
                }
                // 直接返回，避免继续执行后续的状态检查逻辑
                return;
            }
        } catch (error) {
            console.error('进度监控失败:', error);
        }
    }, 1000); // 每1秒检查一次
}

/**
 * 监控批次聚合进度
 *
 * @param {Array<string>} taskIds - 批次任务ID数组
 * @param {number} totalFiles - 总文件数量
 * @param {Array} failedBatches - 上传失败的批次信息（可选）
 */
function monitorBatchProgress(taskIds, totalFiles, failedBatches = [], startTime = null) {
    let checkCount = 0;
    const maxElapsedTime = 60 * 60 * 1000; // 1小时超时（毫秒）
    const actualStartTime = startTime || Date.now();

    console.log('开始监控批次聚合进度，总任务数:', taskIds.length, '总文件数:', totalFiles);

    // 🔄 渐进式查询频率：开始快，后来慢
    let currentInterval = 2000; // 起始2秒（导入比基础分析频率稍低）
    let progressInterval;

    const checkProgress = async () => {
        checkCount++;

        // 超时保护 - 基于实际时间
        const elapsedTime = Date.now() - actualStartTime;
        if (elapsedTime >= maxElapsedTime) {
            if (progressInterval) {
                clearInterval(progressInterval);
                clearTimeout(progressInterval);
            }
            console.error('批次进度监控超时，经过时间:', Math.round(elapsedTime/1000), '秒');
            elements.importStatus.textContent = '处理超时';
            elements.importDetails.textContent = '服务器处理时间过长，请检查服务器状态';
            elements.importProgressBar.classList.remove('progress-bar-striped', 'progress-bar-animated');
            elements.importProgressBar.classList.add('bg-warning');
            showError('导入超时，请检查服务器状态');
            return;
        }

        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/import/batch-status`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(taskIds)
            });

            if (!response.ok) {
                console.error('批次状态查询失败:', response.status, response.statusText);
                return;
            }

            const batchData = await response.json();
            console.log('批次聚合状态:', batchData);

            // 更新进度条 - 显示批次完成进度
            const batchProgress = batchData.overall_progress_percentage || 0;
            elements.importProgressBar.style.width = `${batchProgress}%`;
            elements.importProgressBar.setAttribute('aria-valuenow', batchProgress);

            // 更新状态文本
            elements.importStatus.textContent = `批次处理中: ${batchData.completed_tasks}/${batchData.total_tasks} 批完成 (${batchProgress}%)`;

            // 显示详细统计
            const processedFiles = batchData.total_processed_files || 0;
            const importedCount = batchData.total_imported_count || 0;
            const skippedCount = batchData.total_skipped_count || 0;
            const failedCount = batchData.total_failed_count || 0;

            elements.importDetails.textContent = `已处理: ${processedFiles}/${totalFiles} 个文件 | 导入: ${importedCount}, 跳过: ${skippedCount}, 失败: ${failedCount}`;

            // 检查是否完成
            if (batchData.overall_status === 'completed') {
                clearInterval(progressInterval);
                console.log('所有批次处理完成，开始显示结果');

                // ✅ 完成时解除保护，允许正常关闭
                window.importModalProtector.unprotect();

                // 更新最终状态显示
                elements.importProgressBar.style.width = '100%';
                elements.importProgressBar.setAttribute('aria-valuenow', '100');
                elements.importStatus.textContent = `批次处理完成！共处理 ${totalFiles} 个文件`;

                // 计算成功率
                const totalProcessed = importedCount + skippedCount + failedCount;
                const successRate = totalProcessed > 0 ? ((importedCount / totalProcessed) * 100).toFixed(1) : '0.0';
                elements.importDetails.textContent = `最终结果: 成功率 ${successRate}% | 导入: ${importedCount}, 跳过: ${skippedCount}, 失败: ${failedCount}`;

                // 更新统计信息
                elements.processedCount.textContent = processedFiles;
                elements.importedCount.textContent = importedCount;
                elements.skippedCount.textContent = skippedCount;
                elements.failedCount.textContent = failedCount;

                // 转换数据格式以匹配showImportDetails的期望
                const detailsData = {
                    total_files: totalFiles,
                    imported_photos: importedCount,
                    skipped_photos: skippedCount,
                    failed_photos: failedCount,
                    failed_files: batchData.failed_files || [],
                    // 上传失败批次信息
                    upload_failed_batches: failedBatches.length,
                    upload_failed_details: failedBatches.map(f => ({
                        batch_index: f.batchIndex,
                        files_count: f.files,
                        error: f.error
                    }))
                };

                // 【关键】执行和非分批处理完全相同的UI流程
                const modal = bootstrap.Modal.getInstance(elements.importModal);
                if (modal) {
                    modal.hide();

                    // 监听模态框关闭事件，确保模态框完全消失后才显示结果
                    elements.importModal.addEventListener('hidden.bs.modal', function onModalHidden() {
                        console.log('导入模态框已完全关闭，准备显示批次处理结果...');

                        // 移除事件监听器，避免重复执行
                        elements.importModal.removeEventListener('hidden.bs.modal', onModalHidden);

                        try {
                            // 显示导入结果详情
                            showImportDetails(detailsData);

                            // 重新加载照片列表
                            loadPhotos();
                            loadStats();
                        } catch (error) {
                            console.error('显示批次处理结果详情失败:', error);
                            showError('显示结果失败: ' + error.message);
                        }
                    });
                } else {
                    // 如果找不到模态框实例，直接显示结果（降级处理）
                    console.warn('找不到导入模态框实例，直接显示批次处理结果');
                    showImportDetails(detailsData);
                    loadPhotos();
                    loadStats();
                }
                // 直接返回，避免继续执行后续的状态检查逻辑
                return;
            }
        } catch (error) {
            console.error('批次进度监控失败:', error);
        }

        // 🔄 动态调整查询频率
        // 0-30秒：2秒间隔，30-120秒：5秒间隔，120-300秒：10秒间隔，300秒以后：20秒间隔
        const elapsedSeconds = (Date.now() - startTime) / 1000;
        let nextInterval;

        if (elapsedSeconds < 30) {
            nextInterval = 2000; // 2秒
        } else if (elapsedSeconds < 120) {
            nextInterval = 5000; // 5秒
        } else if (elapsedSeconds < 300) {
            nextInterval = 10000; // 10秒
        } else {
            nextInterval = 20000; // 20秒
        }

        // 如果频率改变，重新设置定时器
        if (nextInterval !== currentInterval) {
            currentInterval = nextInterval;
            if (progressInterval) {
                clearInterval(progressInterval);
                clearTimeout(progressInterval);
            }
            progressInterval = setTimeout(checkProgress, currentInterval);
        } else {
            progressInterval = setTimeout(checkProgress, currentInterval);
        }
    };

    // 启动首次检查
    progressInterval = setTimeout(checkProgress, currentInterval);
}













/**
 * 开始基础分析
 */
async function startBasicAnalysis() {
    // 开始基础分析

    // 重置模态框状态到初始状态
    resetBasicModal();

    // 显示基础分析模态框
    const modal = new bootstrap.Modal(document.getElementById('basicModal'));
    modal.show();

    // 获取基础分析统计信息
    try {
        const countResponse = await fetch(`${window.CONFIG.API_BASE_URL}/analysis/basic-pending-count`);
        const countData = await countResponse.json();

        const countInfo = document.getElementById('basicPhotoCountInfo');
        const countText = document.getElementById('basicPhotoCountText');
        const startBtn = document.getElementById('startBasicBtn');

        if (countResponse.ok && countData.count > 0) {
            // 有照片需要分析
            countInfo.style.display = 'block';
            countText.textContent = `发现 ${countData.count} 张照片需要基础分析`;
            startBtn.disabled = false;
            startBtn.textContent = '开始基础分析';
        } else if (countResponse.ok && countData.count === 0) {
            // 所有照片都已完成基础分析
            countInfo.style.display = 'block';
            countText.textContent = '所有照片都已完成基础分析';
            startBtn.disabled = true;
            startBtn.textContent = '无需分析';
        } else {
            // API调用失败
            countInfo.style.display = 'none';
            startBtn.disabled = true;
            startBtn.textContent = '开始基础分析';
        }
    } catch (error) {
        console.error('获取基础分析统计失败:', error);
        // 出错时隐藏统计信息并禁用按钮
        document.getElementById('basicPhotoCountInfo').style.display = 'none';
        document.getElementById('startBasicBtn').disabled = true;
        document.getElementById('startBasicBtn').textContent = '开始基础分析';
    }
}

/**
 * 单批处理基础分析（传统逻辑）
 * @param {Array} photoIds - 需要分析的照片ID数组
 */
async function processBasicAnalysisSingleBatch(photoIds) {
    // 禁用开始按钮，防止重复点击
    document.getElementById('startBasicBtn').disabled = true;

    try {
        // 开始基础分析
        const response = await fetch(`${window.CONFIG.API_BASE_URL}/analysis/start-analysis`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                photo_ids: photoIds,
                analysis_types: ['quality']  // 基础分析只包含质量评估
            })
        });

        const data = await response.json();

        if (!response.ok) {
            showError('开始基础分析失败: ' + (data.detail || '未知错误'));
            document.getElementById('startBasicBtn').disabled = false;
            return;
        }

        // 监控分析进度 - 直接使用当前任务的照片数作为总数
        await monitorBasicAnalysisProgress(data.task_id, photoIds.length, photoIds.length);

    } catch (error) {
        console.error('基础分析单批处理失败:', error);
        showError('基础分析失败: ' + error.message);
        document.getElementById('startBasicBtn').disabled = false;
    }
}

/**
 * 分批处理基础分析 - 使用分阶段启动和并发控制
 * @param {Array} photoIds - 所有需要分析的照片ID
 * @param {number} batchSize - 每批大小
 */
async function processBasicAnalysisInBatches(photoIds, batchSize) {
    const totalPhotos = photoIds.length;
    const totalBatches = Math.ceil(totalPhotos / batchSize);
    
    // 🔥 新增：从配置读取最大并发批次数
    const maxConcurrentBatches = CONFIG.analysisConfig?.concurrent || 3;
    
    console.log(`分批处理基础分析：${totalPhotos}张照片，分为${totalBatches}批，最多${maxConcurrentBatches}批并发`);

    // 禁用开始按钮，防止重复点击
    document.getElementById('startBasicBtn').disabled = true;

    // 显示分批处理状态
    document.getElementById('basicStatus').textContent = `准备分批分析 ${totalPhotos} 张照片，共${totalBatches}批，最多${maxConcurrentBatches}批并发...`;

    try {
        // 🔥 新增：准备所有批次信息
        const allBatchTasks = [];  // 所有批次任务信息
        const activeTasks = new Map();  // 当前活跃任务 Map<taskId, batchInfo>
        let nextBatchIndex = 0;
        
        // 准备所有批次信息
        for (let i = 0; i < totalBatches; i++) {
            const start = i * batchSize;
            const end = Math.min(start + batchSize, totalPhotos);
            const batchPhotoIds = photoIds.slice(start, end);
            
            allBatchTasks.push({
                batchIndex: i + 1,
                photoIds: batchPhotoIds,
                taskId: null,
                status: 'pending'
            });
        }
        
        // 🔥 新增：分阶段启动批次
        await processBasicAnalysisWithConcurrency(allBatchTasks, activeTasks, maxConcurrentBatches, totalPhotos);

        // 🔥 新增：完成后处理逻辑（参考旧版实现）
        console.log('所有批次分析完成，开始显示结果');

        // 解除保护
        if (window.basicModalProtector) {
            window.basicModalProtector.unprotect();
        }

        // 重置按钮状态
        document.getElementById('startBasicBtn').disabled = false;

        // 关闭模态框
        const modal = bootstrap.Modal.getInstance(document.getElementById('basicModal'));
        if (modal) {
            modal.hide();
        }

        // 显示结果页
        setTimeout(async () => {
            try {
                // 🔥 修复：参考旧模式构建批次进度数据
                const batchProgress = {};
                
                // 初始化批次进度（参考旧模式第2109-2118行）
                allBatchTasks.forEach(batch => {
                    if (batch.taskId) {
                        batchProgress[batch.taskId] = {
                            completed: true, // 所有批次都已完成
                            completed_photos: batch.photoIds ? batch.photoIds.length : 0,
                            total_photos: batch.photoIds ? batch.photoIds.length : 0,
                            progress_percentage: 100,
                            status: 'completed',
                            batchIndex: batch.batchIndex,
                            error: null
                        };
                    }
                });
                
                await showBasicAnalysisBatchResults(allBatchTasks, batchProgress, totalPhotos);
                
                // 刷新数据
                if (window.loadPhotos) await window.loadPhotos();
                if (window.loadStats) await window.loadStats();
            } catch (error) {
                console.error('显示基础分析结果失败:', error);
            }
        }, 100);

    } catch (error) {
        console.error('基础分析分批处理失败:', error);
        showError('基础分析分批处理失败: ' + error.message);
        document.getElementById('startBasicBtn').disabled = false;
    }
}

/**
 * 🔥 新增：带并发控制的基础分析分批处理
 * @param {Array} allBatchTasks - 所有批次任务信息
 * @param {Map} activeTasks - 当前活跃任务
 * @param {number} maxConcurrentBatches - 最大并发批次数
 * @param {number} totalPhotos - 总照片数
 */
async function processBasicAnalysisWithConcurrency(allBatchTasks, activeTasks, maxConcurrentBatches, totalPhotos) {
    let nextBatchIndex = 0;
    
    // 第一阶段：启动初始并发批次
    const initialBatches = Math.min(maxConcurrentBatches, allBatchTasks.length);
    console.log(`启动初始${initialBatches}个批次`);
    
    for (let i = 0; i < initialBatches; i++) {
        await startNextBatch(allBatchTasks, activeTasks, nextBatchIndex++);
    }
    
    // 第二阶段：监控并动态扩容
    await monitorAndScaleConcurrentBatches(allBatchTasks, activeTasks, maxConcurrentBatches, totalPhotos);
}

/**
 * 🔥 新增：启动下一个批次
 * @param {Array} allBatchTasks - 所有批次任务信息
 * @param {Map} activeTasks - 当前活跃任务
 * @param {number} batchIndex - 批次索引
 */
async function startNextBatch(allBatchTasks, activeTasks, batchIndex) {
    if (batchIndex >= allBatchTasks.length) {
        return;
    }
    
    const batchTask = allBatchTasks[batchIndex];
    const currentBatch = batchIndex + 1;
    
    // 更新状态显示
    document.getElementById('basicStatus').textContent = 
        `正在启动第${currentBatch}批分析 (${batchTask.photoIds.length}张照片)...`;
    
    try {
        // 启动单批分析
        const response = await fetch(`${window.CONFIG.API_BASE_URL}/analysis/start-analysis`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                photo_ids: batchTask.photoIds,
                analysis_types: ['quality']
            })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(`第${currentBatch}批启动失败: ${errorData.detail || response.statusText}`);
        }

        const data = await response.json();
        
        // 更新批次信息
        batchTask.taskId = data.task_id;
        batchTask.status = 'active';
        
        // 添加到活跃任务列表
        activeTasks.set(data.task_id, {
            batchIndex: currentBatch,
            photoCount: batchTask.photoIds.length,
            startTime: Date.now()
        });
        
        console.log(`第${currentBatch}批分析任务已启动，任务ID: ${data.task_id}`);
        
    } catch (error) {
        console.error(`第${currentBatch}批启动失败:`, error);
        batchTask.status = 'failed';
        throw error;
    }
}

/**
 * 🔥 新增：监控活跃批次并动态扩容
 * @param {Array} allBatchTasks - 所有批次任务信息
 * @param {Map} activeTasks - 当前活跃任务
 * @param {number} maxConcurrentBatches - 最大并发批次数
 * @param {number} totalPhotos - 总照片数
 */
async function monitorAndScaleConcurrentBatches(allBatchTasks, activeTasks, maxConcurrentBatches, totalPhotos) {
    let nextBatchIndex = maxConcurrentBatches; // 从已启动的批次后开始
    let completedBatches = 0;
    
    return new Promise((resolve) => {
        const checkInterval = setInterval(async () => {
            try {
                // 1. 检查已完成的批次
                const completedTaskIds = await checkCompletedBatches(activeTasks);
                
                // 2. 从活跃列表中移除已完成的批次
                completedTaskIds.forEach(taskId => {
                    const batchInfo = activeTasks.get(taskId);
                    if (batchInfo) {
                        completedBatches++;
                        console.log(`第${batchInfo.batchIndex}批分析完成`);
                    }
                    activeTasks.delete(taskId);
                });
                
                // 3. 启动新的批次补充到最大并发数
                while (activeTasks.size < maxConcurrentBatches && nextBatchIndex < allBatchTasks.length) {
                    await startNextBatch(allBatchTasks, activeTasks, nextBatchIndex++);
                }
                
                // 4. 更新进度显示
                const totalCompleted = completedBatches;
                const progressPercentage = Math.round((totalCompleted / allBatchTasks.length) * 100);
                document.getElementById('basicStatus').textContent = 
                    `已完成${totalCompleted}/${allBatchTasks.length}批，活跃批次: ${activeTasks.size}/${maxConcurrentBatches}`;
                document.getElementById('basicProgressBar').style.width = `${progressPercentage}%`;
                document.getElementById('basicProgressBar').setAttribute('aria-valuenow', progressPercentage);
                
                // 5. 检查是否全部完成
                if (activeTasks.size === 0 && nextBatchIndex >= allBatchTasks.length) {
                    clearInterval(checkInterval);
                    console.log('所有批次分析完成');
                    document.getElementById('basicStatus').textContent = 
                        `所有${allBatchTasks.length}批分析任务已完成`;
                    document.getElementById('basicProgressBar').style.width = '100%';
                    document.getElementById('basicProgressBar').setAttribute('aria-valuenow', 100);
                    resolve();
                }
                
            } catch (error) {
                console.error('批次监控失败:', error);
                clearInterval(checkInterval);
                resolve();
            }
        }, 2000); // 每2秒检查一次
    });
}

/**
 * 🔥 新增：检查已完成的批次
 * @param {Map} activeTasks - 当前活跃任务
 * @returns {Array} 已完成的任务ID列表
 */
async function checkCompletedBatches(activeTasks) {
    const completedTaskIds = [];
    
    for (const [taskId, batchInfo] of activeTasks) {
        try {
            const response = await fetch(`${window.CONFIG.API_BASE_URL}/analysis/task-status/${taskId}`);
            if (response.ok) {
                const statusData = await response.json();
                if (statusData.status === 'completed' || statusData.status === 'failed') {
                    completedTaskIds.push(taskId);
                }
            }
        } catch (error) {
            console.error(`检查任务${taskId}状态失败:`, error);
        }
    }
    
    return completedTaskIds;
}


/**
 * 显示基础分析批次结果
 * @param {Array<Object>} batchInfo - 批次信息数组
 * @param {Object} batchProgress - 批次进度信息
 * @param {number} totalPhotos - 总照片数
 */
async function showBasicAnalysisBatchResults(batchInfo, batchProgress, totalPhotos) {
    try {
        // 收集所有批次的结果
        const aggregatedResults = {
            total_files: totalPhotos,
            imported_photos: 0,
            skipped_photos: 0,
            failed_photos: 0,
            failed_files: [],
            batch_count: batchInfo.length,
            completed_batches: 0,
            failed_batches: 0,
            batch_details: []
        };

        // 统计各批次结果
        for (let i = 0; i < batchInfo.length; i++) {
            const batch = batchInfo[i];
            const progress = batchProgress[batch.taskId];

            const batchDetail = {
                batch_index: batch.batchIndex,
                task_id: batch.taskId,
                completed_photos: progress.completed_photos || 0,
                total_photos: progress.total_photos || batch.photoCount || 0,
                status: progress.status,
                error: progress.error || null
            };

            aggregatedResults.batch_details.push(batchDetail);

            // 根据批次状态进行统计
            if (progress.status === 'completed') {
                aggregatedResults.completed_batches++;
                aggregatedResults.imported_photos += progress.completed_photos || 0;
            } else if (progress.status === 'error') {
                aggregatedResults.failed_batches++;
            }
            // 其他状态（processing, pending等）不计入已完成或失败
        }

        // 计算跳过和失败的数量（近似值）
        // 注意：这里没有精确的统计，因为批次间可能有重复
        // 理想情况下应该从服务端获取准确统计

        console.log('基础分析批次结果:', aggregatedResults);

        // 显示结果详情（复用现有的结果显示函数，但传入批次信息）
        showBasicProcessDetails(aggregatedResults);

    } catch (error) {
        console.error('获取基础分析批次结果失败:', error);
        showError('显示基础分析结果失败: ' + error.message);
    }
}

/**
 * 开始AI分析
 */
async function startAIAnalysis() {
    // 开始AI分析

    // 重置模态框状态到初始状态
    resetAIModal();

    // 显示AI分析模态框
    const modal = new bootstrap.Modal(document.getElementById('aiModal'));
    modal.show();

    // 获取AI分析统计信息
    try {
        const countResponse = await fetch(`${window.CONFIG.API_BASE_URL}/analysis/ai-pending-count`);
        const countData = await countResponse.json();

        const countInfo = document.getElementById('aiPhotoCountInfo');
        const countText = document.getElementById('aiPhotoCountText');
        const batchSetup = document.getElementById('aiBatchSetup');
        const startBtn = document.getElementById('startAIBtn');

        if (countResponse.ok && countData.count > 0) {
            // 有照片需要分析
            countInfo.style.display = 'block';
            countText.textContent = `发现 ${countData.count} 张照片需要AI分析`;

            // 总是显示批次设置
            batchSetup.style.display = 'block';

            // 动态设置批次数输入框的最大值和默认值
            const batchInput = document.getElementById('aiBatchCount');
            if (batchInput) {
                batchInput.max = countData.count; // 最大值不能超过照片数量
                batchInput.value = Math.min(5, countData.count); // 默认值为5或照片数量的较小值
            }

            updateAIBatchPreview(countData.count);

            startBtn.disabled = false;
            startBtn.textContent = '开始AI分析';
        } else if (countResponse.ok && countData.count === 0) {
            // 所有照片都已完成AI分析
            countInfo.style.display = 'block';
            countText.textContent = '所有照片都已完成AI分析';
            batchSetup.style.display = 'none';
            startBtn.disabled = true;
            startBtn.textContent = '无需分析';
        } else {
            // API调用失败
            countInfo.style.display = 'none';
            batchSetup.style.display = 'none';
            startBtn.disabled = true;
            startBtn.textContent = '开始AI分析';
        }
    } catch (error) {
        console.error('获取AI分析统计失败:', error);
        // 出错时隐藏统计信息并禁用按钮
        document.getElementById('aiPhotoCountInfo').style.display = 'none';
        document.getElementById('aiBatchSetup').style.display = 'none';
        document.getElementById('startAIBtn').disabled = true;
        document.getElementById('startAIBtn').textContent = '开始AI分析';
    }
}

/**
 * 执行基础分析处理
 */
async function startBasicProcess() {
    console.log('执行基础分析处理');

    // 确保用户配置已加载
    if (!window.userConfig) {
        // 加载用户配置
        await loadUserConfig();
    }

    // 显示进度
    document.getElementById('basicProgress').classList.remove('d-none');
    document.getElementById('startBasicBtn').disabled = true;
    document.getElementById('basicProgressBar').style.width = '0%';
    document.getElementById('basicStatus').textContent = '正在准备基础分析...';

    try {
        // 🔒 启用基础分析模态框保护
        window.basicModalProtector.protect();
        // 获取需要基础分析的照片ID
        const pendingResponse = await fetch(`${window.CONFIG.API_BASE_URL}/analysis/basic-pending-photos`);
        const pendingData = await pendingResponse.json();

        if (!pendingResponse.ok) {
            showError('获取待分析照片列表失败');
            return;
        }

        const photoIds = pendingData.photo_ids || [];

        if (photoIds.length === 0) {
            showWarning('没有找到需要基础分析的照片');
            document.getElementById('startBasicBtn').disabled = false;
            return;
        }

        // 分批处理配置
        const BATCH_THRESHOLD = CONFIG.analysisConfig?.batch_threshold || 200;  // 分批处理阈值
        const BATCH_SIZE = CONFIG.analysisConfig?.batch_size || 100;  // 从配置读取
        console.log(`使用配置的分批大小: ${BATCH_SIZE}`);  // 调试日志

        if (photoIds.length > BATCH_THRESHOLD) {
            // 分批处理
            console.log(`基础分析分批处理：${photoIds.length}张照片超过阈值${BATCH_THRESHOLD}，启用分批处理`);
            await processBasicAnalysisInBatches(photoIds, BATCH_SIZE);
        } else {
            // 单批处理（保持现有逻辑）
            console.log(`基础分析单批处理：${photoIds.length}张照片，使用传统单批处理`);
            await processBasicAnalysisSingleBatch(photoIds);
        }

    } catch (error) {
        console.error('基础分析处理失败:', error);

        // ❌ 出错时解除保护
        window.basicModalProtector.unprotect();

        showError('基础分析失败: ' + error.message);
        document.getElementById('startBasicBtn').disabled = false;
    }
}

/**
 * 执行AI分析处理
 */
async function startAIProcess() {
    console.log('执行AI分析处理');

    try {
        // 🔒 启用AI分析模态框保护
        window.aiModalProtector.protect();

        // 获取需要AI分析的照片ID
        const pendingResponse = await fetch(`${window.CONFIG.API_BASE_URL}/analysis/ai-pending-photos`);
        const pendingData = await pendingResponse.json();

        if (!pendingResponse.ok) {
            showError('获取待分析照片列表失败');
            return;
        }

        const photoIds = pendingData.photo_ids || [];

        if (photoIds.length === 0) {
            showWarning('没有找到需要AI分析的照片');
            document.getElementById('startAIBtn').disabled = false;
            return;
        }

        // 开始处理时隐藏底部按钮
        const modalFooter = document.querySelector('#aiModal .modal-footer');
        if (modalFooter) modalFooter.style.display = 'none';

        // 总是使用分批处理模式
        let batchCount = parseInt(document.getElementById('aiBatchCount').value) || 5;

        // 验证批次数不能超过照片数量
        if (batchCount > photoIds.length) {
            batchCount = Math.min(photoIds.length, 5); // 限制为照片数量或5的较小值
            console.log(`批次数超过照片数量，已调整为 ${batchCount}`);
        }

        // 确保批次数至少为1
        batchCount = Math.max(1, batchCount);

        await processAIAnalysisInBatches(photoIds, batchCount);

    } catch (error) {
        console.error('AI分析处理失败:', error);
        showError('AI分析失败: ' + error.message);

        // 发生错误时重新显示底部按钮
        const modalFooter = document.querySelector('#aiModal .modal-footer');
        if (modalFooter) modalFooter.style.display = 'flex';

        document.getElementById('startAIBtn').disabled = false;

        // ❌ 出错时解除AI分析模态框保护
        window.aiModalProtector.unprotect();
    }
}

/**
 * 计算批次分配（均匀分布策略）
 */
function calculateBatchDistribution(photoIds, batchCount) {
    const totalPhotos = photoIds.length;
    const baseSize = Math.floor(totalPhotos / batchCount);
    const remainder = totalPhotos % batchCount;

    const batches = [];
    let startIndex = 0;

    for(let i = 0; i < batchCount; i++) {
        // 前 remainder 批次多分配1张
        const batchSize = baseSize + (i < remainder ? 1 : 0);
        const endIndex = startIndex + batchSize;

        batches.push({
            index: i + 1,
            photoIds: photoIds.slice(startIndex, endIndex),
            size: batchSize
        });

        startIndex = endIndex;
    }

    return batches;
}

/**
 * AI分析分批处理
 */
async function processAIAnalysisInBatches(photoIds, batchCount) {
    // 开始AI分析分批处理

    // 计算批次分配
    const batches = calculateBatchDistribution(photoIds, batchCount);

    // 显示进度
    document.getElementById('aiProgress').classList.remove('d-none');
    document.getElementById('startAIBtn').disabled = true;

    // 开始批次处理时隐藏底部按钮
    const modalFooter = document.querySelector('#aiModal .modal-footer');
    if (modalFooter) modalFooter.style.display = 'none';

    // 标记是否用户主动停止
    let userStopped = false;

    // 计算所有批次的照片总数
    const totalPhotosInAllBatches = batches.reduce((sum, b) => sum + b.photoIds.length, 0);
    
    // 累积统计数据
    let totalSuccessfulPhotos = 0;
    let totalFailedPhotos = 0;
    const taskIds = []; // 保存所有任务ID

    for (let i = 0; i < batches.length; i++) {
        const batch = batches[i];
        // 处理第${i + 1}批

        // 更新批次进度显示
        updateAIBatchProgress(i + 1, batches.length, batch, totalPhotosInAllBatches);

        try {
            // 提交当前批次
            const batchResult = await submitAIBatch(batch.photoIds);
            taskIds.push(batchResult.task_id);

            // 等待批次完成
            await waitForAIBatchComplete(batch.photoIds.length);

            // 显示批次结果并等待用户确认
            const shouldContinue = await showBatchConfirmation(i + 1, batches.length, batch, totalPhotosInAllBatches);

            // 检查是否继续
            if (!shouldContinue && i < batches.length - 1) {
                console.log('用户选择停止处理');
                userStopped = true;
                break;
            }

        } catch (error) {
            console.error(`第${i + 1}批处理失败:`, error);
            showError(`第${i + 1}批AI分析失败: ${error.message}`);

            // 显示错误确认对话框
            const shouldContinue = await showErrorConfirmation(i + 1, batches.length, error);
            if (!shouldContinue) {
                userStopped = true;
                break;
            }
        }
    }

    // 处理完成或停止 - 显示最终结果
    // 将变量定义移到try-catch外面，确保在catch块中也能访问
    const totalPhotosInBatches = batches.reduce((sum, batch) => sum + batch.photoIds.length, 0);
    
    try {
        
        // 计算已完成批次的照片数
        let completedPhotos = 0;
        if (userStopped) {
            // 用户停止：计算已完成批次的照片数
            for (let j = 0; j < i; j++) {
                completedPhotos += batches[j].photoIds.length;
            }
        } else {
            // 全部完成：所有照片都已处理
            completedPhotos = totalPhotosInBatches;
        }

        // 隐藏进度条
        const aiProgress = document.getElementById('aiProgress');
        if (aiProgress) aiProgress.classList.add('d-none');

        // 隐藏批次设置区域
        const batchSetup = document.getElementById('aiBatchSetup');
        if (batchSetup) batchSetup.style.display = 'none';

        // 隐藏底部按钮区域
        const modalFooter = document.querySelector('#aiModal .modal-footer');
        if (modalFooter) modalFooter.style.display = 'none';

        // 显示最终结果
        const statusDiv = document.getElementById('aiBatchStatus');
        if (statusDiv) {
            statusDiv.innerHTML = `
                <div class="alert ${userStopped ? 'alert-warning' : 'alert-success'}">
                    <h5>${userStopped ? 'AI分析已停止' : '所有AI分析批次已完成！'}</h5>
                    <p>共处理了 ${completedPhotos} / ${totalPhotosInBatches} 张照片</p>
                    <div class="mt-3">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                    </div>
                </div>
            `;
        }

        // ❌ 分批处理完成，解除AI分析模态框保护
        window.aiModalProtector.unprotect();

        // 关闭AI分析模态框并显示详细结果（与单批次处理保持一致）
        const modal = bootstrap.Modal.getInstance(document.getElementById('aiModal'));
        if (modal) {
            modal.hide();

            // 监听模态框关闭事件
            document.getElementById('aiModal').addEventListener('hidden.bs.modal', async function onModalHidden() {
                document.getElementById('aiModal').removeEventListener('hidden.bs.modal', onModalHidden);

                try {
                    // 使用混合模式统计实际的成功和失败数量
                    const actualStats = await getActualAnalysisStats(totalPhotosInBatches, taskIds);
                    const resultData = {
                        total_photos: totalPhotosInBatches,
                        completed_photos: actualStats.successful_photos,
                        failed_photos: actualStats.failed_photos,
                        successful_photos: actualStats.successful_photos
                    };
                    showAIProcessDetails(resultData);
                } catch (error) {
                    console.error('显示AI分析结果详情失败:', error);
                    showError('显示处理结果失败: ' + error.message);
                }
            }, { once: true });
        } else {
            // 如果无法获取模态框实例，直接显示结果详情
            try {
                // 使用混合模式统计实际的成功和失败数量
                const actualStats = await getActualAnalysisStats(totalPhotosInBatches, taskIds);
                const resultData = {
                    total_photos: totalPhotosInBatches,
                    completed_photos: actualStats.successful_photos,
                    failed_photos: actualStats.failed_photos,
                    successful_photos: actualStats.successful_photos
                };
                showAIProcessDetails(resultData);
            } catch (error) {
                console.error('显示AI分析结果详情失败:', error);
                showError('显示处理结果失败: ' + error.message);
            }
        }

        // 刷新数据
        try {
            if (window.loadPhotos) await window.loadPhotos();
            if (window.loadStats) await window.loadStats();
        } catch (error) {
            console.error('刷新数据失败:', error);
        }

    } catch (error) {
        console.error('显示最终结果失败:', error);
        
        // 即使出现异常，也要显示结果页
        try {
            const actualStats = await getActualAnalysisStats(totalPhotosInBatches, taskIds);
            const resultData = {
                total_photos: totalPhotosInBatches,
                completed_photos: actualStats.successful_photos,
                failed_photos: actualStats.failed_photos,
                successful_photos: actualStats.successful_photos
            };
            showAIProcessDetails(resultData);
        } catch (statsError) {
            console.error('获取统计数据失败:', statsError);
            // 最后的降级处理：显示简单状态
            const statusDiv = document.getElementById('aiBatchStatus');
            if (statusDiv) {
                statusDiv.innerHTML = `
                    <div class="alert alert-info">
                        <h5>处理${userStopped ? '已停止' : '已完成'}</h5>
                        <p>处理已${userStopped ? '停止' : '完成'}</p>
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                    </div>
                `;
            }
        }

        // ❌ 出错时也要解除保护
        window.aiModalProtector.unprotect();

        // 即使出错也要尝试关闭模态框并显示结果
        const modal = bootstrap.Modal.getInstance(document.getElementById('aiModal'));
        if (modal) {
            modal.hide();
            
            // 监听模态框关闭事件，显示结果页
            document.getElementById('aiModal').addEventListener('hidden.bs.modal', async function onModalHidden() {
                document.getElementById('aiModal').removeEventListener('hidden.bs.modal', onModalHidden);
                
                try {
                    const actualStats = await getActualAnalysisStats(totalPhotosInBatches, taskIds);
                    const resultData = {
                        total_photos: totalPhotosInBatches,
                        completed_photos: actualStats.successful_photos,
                        failed_photos: actualStats.failed_photos,
                        successful_photos: actualStats.successful_photos
                    };
                    showAIProcessDetails(resultData);
                } catch (statsError) {
                    console.error('获取统计数据失败:', statsError);
                    showError('显示处理结果失败: ' + statsError.message);
                }
            }, { once: true });
        } else {
            // 如果无法获取模态框实例，直接显示结果详情
            try {
                const actualStats = await getActualAnalysisStats(totalPhotosInBatches, taskIds);
                const resultData = {
                    total_photos: totalPhotosInBatches,
                    completed_photos: actualStats.successful_photos,
                    failed_photos: actualStats.failed_photos,
                    successful_photos: actualStats.successful_photos
                };
                showAIProcessDetails(resultData);
            } catch (statsError) {
                console.error('获取统计数据失败:', statsError);
                showError('显示处理结果失败: ' + statsError.message);
            }
        }
    }
}

/**
 * 处理单批次AI分析（少量照片时的直接处理）
 */
async function processAISingleBatch(photoIds) {
    // 直接处理AI分析

    // 显示进度
    document.getElementById('aiProgress').classList.remove('d-none');
    document.getElementById('startAIBtn').disabled = true;
    document.getElementById('aiProgressBar').style.width = '0%';
    document.getElementById('aiStatus').textContent = '正在准备AI分析...';

    // 开始AI分析
    const response = await fetch(`${window.CONFIG.API_BASE_URL}/analysis/start-analysis`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            photo_ids: photoIds,
            analysis_types: ['content']  // AI分析只包含内容分析
        })
    });

    const data = await response.json();

    if (!response.ok) {
        showError('开始AI分析失败: ' + (data.detail || '未知错误'));
        document.getElementById('startAIBtn').disabled = false;
        return;
    }

    // 获取任务开始时的待处理照片总数
    let pendingTotal = photoIds.length;
    try {
        const statusResponse = await fetch(`${window.CONFIG.API_BASE_URL}/analysis/queue/status`);
        const statusData = await statusResponse.json();
        if (statusResponse.ok) {
            pendingTotal = statusData.batch_pending_photos || photoIds.length;
        }
    } catch (error) {
        console.warn('获取待处理总数失败，使用默认值:', error);
    }

    // 监控分析进度
    await monitorAIAnalysisProgress(data.task_id, photoIds.length, pendingTotal);
}

/**
 * 更新AI分析批次预览
 */
function updateAIBatchPreview(totalCount) {
    let batchCount = parseInt(document.getElementById('aiBatchCount').value) || 5;

    // 确保批次数不超过照片数量，且至少为1
    batchCount = Math.min(Math.max(batchCount, 1), totalCount);

    // 更新输入框的值
    document.getElementById('aiBatchCount').value = batchCount;

    const previewDiv = document.getElementById('aiBatchPreview');

    // 计算批次分配
    const baseSize = Math.floor(totalCount / batchCount);
    const remainder = totalCount % batchCount;

    let previewText = '';
    for(let i = 0; i < batchCount; i++) {
        const batchSize = baseSize + (i < remainder ? 1 : 0);
        previewText += `批次${i + 1}: ${batchSize}张<br>`;
    }

    previewDiv.innerHTML = previewText;
}

/**
 * 更新AI分析批次进度显示
 */
function updateAIBatchProgress(currentBatch, totalBatches, batch, totalPhotosInAllBatches) {
    const progressContainer = document.getElementById('aiProgress');
    const completedPhotos = (currentBatch - 1) * batch.photoIds.length;
    const overallProgress = totalPhotosInAllBatches > 0 ? ((completedPhotos / totalPhotosInAllBatches) * 100).toFixed(1) : 0;

    progressContainer.innerHTML = `
        <div class="batch-progress mb-3">
            <h6>第 ${currentBatch} / ${totalBatches} 批次AI分析中</h6>
            <div class="progress mb-2">
                <div class="progress-bar" id="aiBatchProgressBar" style="width: ${overallProgress}%"></div>
            </div>
            <small class="text-muted">
                本批次：0/${batch.photoIds.length} 张 |
                总体：${completedPhotos}/${totalPhotosInAllBatches} 张
            </small>
        </div>
        <div id="aiBatchStatus">正在准备批次分析...</div>
    `;
}

/**
 * 显示错误确认对话框
 */
function showErrorConfirmation(batchIndex, totalBatches, error) {
    return new Promise((resolve) => {
        const statusDiv = document.getElementById('aiBatchStatus');
        if (statusDiv) {
            const errorHtml = `
                <div class="alert alert-danger">
                    <h6>第 ${batchIndex} / ${totalBatches} 批次处理失败</h6>
                    <p>错误信息: ${error.message}</p>
                    <p>是否继续处理剩余批次？</p>
                </div>
            `;

            statusDiv.innerHTML = errorHtml;

            // 显示继续和停止按钮
            const continueBtn = document.createElement('button');
            continueBtn.className = 'btn btn-warning me-2';
            continueBtn.textContent = '继续处理';
            continueBtn.onclick = () => resolve(true);

            const stopBtn = document.createElement('button');
            stopBtn.className = 'btn btn-secondary';
            stopBtn.textContent = '停止处理';
            stopBtn.onclick = () => resolve(false);

            statusDiv.appendChild(continueBtn);
            statusDiv.appendChild(stopBtn);
        } else {
            // 如果状态元素不存在，默认停止
            resolve(false);
        }
    });
}

/**
 * 显示批次确认对话框
 */
function showBatchConfirmation(batchIndex, totalBatches, batch, totalPhotosInAllBatches) {
    return new Promise((resolve) => {
        // 更新进度条到当前批次完成
        const completedPhotos = batchIndex * batch.photoIds.length;
        const overallProgress = totalPhotosInAllBatches > 0 ? ((completedPhotos / totalPhotosInAllBatches) * 100).toFixed(1) : 0;

        const progressBar = document.getElementById('aiBatchProgressBar');
        if (progressBar) {
            progressBar.style.width = `${overallProgress}%`;
        }

        // 更新进度文本
        const progressText = document.querySelector('#aiProgress .text-muted');
        if (progressText) {
            progressText.innerHTML = `
                本批次：${batch.photoIds.length}/${batch.photoIds.length} 张 |
                总体：${completedPhotos}/${totalPhotosInAllBatches} 张
            `;
        }

        // 显示确认界面
        const statusDiv = document.getElementById('aiBatchStatus');
        if (statusDiv) {
            const confirmationHtml = `
                <div class="alert alert-success">
                    <h6>第 ${batchIndex} / ${totalBatches} 批次完成</h6>
                    <p>已成功处理 ${batch.photoIds.length} 张照片</p>
                    ${batchIndex < totalBatches ?
                        '<p>是否继续处理下一批次？</p>' :
                        '<p>所有批次处理完成！</p>'}
                </div>
            `;

            statusDiv.innerHTML = confirmationHtml;

            // 如果是最后一批，直接返回true
            if (batchIndex >= totalBatches) {
                setTimeout(() => resolve(true), 2000);
            } else {
                // 显示继续和停止按钮
                const continueBtn = document.createElement('button');
                continueBtn.className = 'btn btn-primary me-2';
                continueBtn.textContent = '继续下一批';
                continueBtn.onclick = () => resolve(true);

                const stopBtn = document.createElement('button');
                stopBtn.className = 'btn btn-secondary';
                stopBtn.textContent = '停止处理';
                stopBtn.onclick = () => resolve(false);

                statusDiv.appendChild(continueBtn);
                statusDiv.appendChild(stopBtn);
            }
        } else {
            // 如果状态元素不存在，默认继续
            resolve(true);
        }
    });
}

/**
 * 获取实际的分析统计数据（混合模式）
 * 查询数据库中已处理照片的实际状态，统计成功和失败的数量
 */
async function getActualAnalysisStats(totalPhotos, taskIds = []) {
    try {
        if (taskIds.length === 0) {
            // 如果没有任务ID，使用默认值
            console.warn('没有任务ID，无法获取准确统计');
            return {
                successful_photos: 0,
                failed_photos: 0,
                total_processed: 0
            };
        }
        
        // 使用任务ID获取准确的统计数据
        const response = await fetch(`${window.CONFIG.API_BASE_URL}/analysis/batch-status`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                task_ids: taskIds,
                initial_totals: {}
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            
            // 使用任务状态跟踪的统计数据
            const successfulPhotos = data.total_completed_photos || 0;
            const failedPhotos = data.total_failed_photos || 0;
            
            return {
                successful_photos: successfulPhotos,
                failed_photos: failedPhotos,
                total_processed: successfulPhotos + failedPhotos
            };
        } else {
            console.warn('获取任务状态统计数据失败，使用默认值');
            return {
                successful_photos: 0,
                failed_photos: 0,
                total_processed: 0
            };
        }
    } catch (error) {
        console.error('获取分析统计数据失败:', error);
        return {
            successful_photos: 0,
            failed_photos: 0,
            total_processed: 0
        };
    }
}

/**
 * 提交单个AI分析批次
 */
async function submitAIBatch(photoIds) {
    // 提交AI分析批次

    const response = await fetch(`${window.CONFIG.API_BASE_URL}/analysis/start-analysis`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            photo_ids: photoIds,
            analysis_types: ['content']
        })
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error('开始AI分析失败: ' + (data.detail || '未知错误'));
    }

    // 等待批次完成
    await waitForAIBatchComplete(photoIds.length);

    return {
        task_id: data.task_id,
        total_photos: data.total_photos
    };
}

/**
 * 等待AI分析批次完成
 */
async function waitForAIBatchComplete(batchSize) {
    return new Promise((resolve, reject) => {
        let waitTime = 0;

        const checkInterval = setInterval(async () => {
            try {
                const response = await fetch(`${window.CONFIG.API_BASE_URL}/analysis/queue/status?initial_total=${batchSize}`);
                const data = await response.json();

                if (response.ok) {
                    // 检查是否有正在进行的任务
                    // 使用 analyzing_photos 字段来判断是否有正在分析的任务
                    if (data.analyzing_photos === 0) {
                        clearInterval(checkInterval);
                        resolve();
                    } else {
                        // 更新等待状态
                        waitTime += 2;
                        const statusDiv = document.getElementById('aiBatchStatus');
                        if (statusDiv) {
                            statusDiv.innerHTML = `正在分析批次... 已等待 ${waitTime} 秒`;
                        }
                    }
                }
            } catch (error) {
                console.warn('检查批次状态失败:', error);
            }
        }, 2000); // 每2秒检查一次

        // 超时保护：最多等待30分钟
        setTimeout(() => {
            clearInterval(checkInterval);
            reject(new Error('批次处理超时'));
        }, 30 * 60 * 1000);
    });
}

/**
 * 监控基础分析进度
 */
async function monitorBasicAnalysisProgress(taskId, totalPhotos, initialTotal) {
    let checkCount = 0;
    const maxChecks = 1800; // 最多检查1800次，每次1秒，总共30分钟

    const statusCheckInterval = setInterval(async () => {
        checkCount++;

        try {
            const statusResponse = await fetch(`${window.CONFIG.API_BASE_URL}/analysis/task-status/${taskId}?initial_total=${initialTotal}`);
            const statusData = await statusResponse.json();

            // 移除频繁的状态日志以提升性能

            // 更新进度条
            const progress = Math.min(statusData.progress_percentage || 0, 95);
            document.getElementById('basicProgressBar').style.width = `${progress}%`;
            document.getElementById('basicStatus').textContent = `正在分析... ${Math.round(progress)}% (${statusData.completed_photos}/${statusData.total_photos})`;

            // 检查是否完成
            if (statusData.status === 'completed' || statusData.processing_photos === 0) {
                clearInterval(statusCheckInterval);

                // ✅ 完成时解除保护
                window.basicModalProtector.unprotect();

                document.getElementById('basicProgressBar').style.width = '100%';
                document.getElementById('basicStatus').textContent = '基础分析完成！';

                // 重置按钮状态
                document.getElementById('startBasicBtn').disabled = false;

                // 清除照片选择状态
                if (window.clearSelection) {
                    window.clearSelection();
                }

                // 关闭基础分析模态框
                const modal = bootstrap.Modal.getInstance(document.getElementById('basicModal'));
                if (modal) {
                    modal.hide();

                    // 监听模态框关闭事件
                    document.getElementById('basicModal').addEventListener('hidden.bs.modal', function onModalHidden() {
                        document.getElementById('basicModal').removeEventListener('hidden.bs.modal', onModalHidden);

                        try {
                            showBasicProcessDetails(statusData);
                        } catch (error) {
                            console.error('显示基础分析结果详情失败:', error);
                            showError('显示处理结果失败: ' + error.message);
                        }
                    }, { once: true });
                } else {
                    // 如果无法获取模态框实例，直接显示结果详情
                    try {
                        showBasicProcessDetails(statusData);
                    } catch (error) {
                        console.error('显示基础分析结果详情失败:', error);
                        showError('显示处理结果失败: ' + error.message);
                    }
                }

                // 刷新数据
                try {
                    if (window.loadPhotos) await window.loadPhotos();
                    if (window.loadStats) await window.loadStats();
                } catch (error) {
                    console.error('刷新数据失败:', error);
                }
            }

        } catch (error) {
            console.error('检查基础分析状态失败:', error);
        }

        // 超时检查
        if (checkCount >= maxChecks) {
            clearInterval(statusCheckInterval);

            // ❌ 超时/出错时解除保护
            window.basicModalProtector.unprotect();

            showError('基础分析超时，请稍后重试');
            document.getElementById('startBasicBtn').disabled = false;
        }
    }, 1000);
}

/**
 * 监控AI分析进度
 */
async function monitorAIAnalysisProgress(taskId, totalPhotos, initialTotal) {
    let checkCount = 0;
    const maxChecks = 600; // 最多检查600次，每次1秒，总共10分钟

    const statusCheckInterval = setInterval(async () => {
        checkCount++;

        try {
            const statusResponse = await fetch(`${window.CONFIG.API_BASE_URL}/analysis/task-status/${taskId}?initial_total=${initialTotal}`);
            const statusData = await statusResponse.json();

            // 移除频繁的状态日志以提升性能

            // 更新进度条
            const progress = Math.min(statusData.progress_percentage || 0, 95);
            document.getElementById('aiProgressBar').style.width = `${progress}%`;
            
            // 计算已处理数量（成功 + 失败）
            const processedPhotos = (statusData.completed_photos || 0) + (statusData.failed_photos || 0);
            document.getElementById('aiStatus').textContent = `正在分析... ${Math.round(progress)}% (${processedPhotos}/${statusData.total_photos})`;

            // 检查是否完成
            if (statusData.status === 'completed' || statusData.processing_photos === 0) {
                clearInterval(statusCheckInterval);

                document.getElementById('aiProgressBar').style.width = '100%';
                document.getElementById('aiStatus').textContent = 'AI分析完成！';

                // 重置按钮状态
                document.getElementById('startAIBtn').disabled = false;

                // 清除照片选择状态
                if (window.clearSelection) {
                    window.clearSelection();
                }

                // ❌ 完成前解除AI分析模态框保护
                window.aiModalProtector.unprotect();

                // 关闭AI分析模态框
                const modal = bootstrap.Modal.getInstance(document.getElementById('aiModal'));
                if (modal) {
                    modal.hide();

                    // 监听模态框关闭事件
                    document.getElementById('aiModal').addEventListener('hidden.bs.modal', function onModalHidden() {
                        document.getElementById('aiModal').removeEventListener('hidden.bs.modal', onModalHidden);

                        try {
                            showAIProcessDetails(statusData);
                        } catch (error) {
                            console.error('显示AI分析结果详情失败:', error);
                            showError('显示处理结果失败: ' + error.message);
                        }
                    }, { once: true });
                } else {
                    // 如果无法获取模态框实例，直接显示结果详情
                    try {
                        showAIProcessDetails(statusData);
                    } catch (error) {
                        console.error('显示AI分析结果详情失败:', error);
                        showError('显示处理结果失败: ' + error.message);
                    }
                }

                // 刷新数据
                try {
                    if (window.loadPhotos) await window.loadPhotos();
                    if (window.loadStats) await window.loadStats();
                } catch (error) {
                    console.error('刷新数据失败:', error);
                }
            }

        } catch (error) {
            console.error('检查AI分析状态失败:', error);
        }

        // 超时检查
        if (checkCount >= maxChecks) {
            clearInterval(statusCheckInterval);
            showError('AI分析超时，请稍后重试');
            document.getElementById('startAIBtn').disabled = false;

            // ❌ 超时也解除AI分析模态框保护
            window.aiModalProtector.unprotect();
        }
    }, 1000);
}
// 处理选中的照片 - 基础分析
window.processSelectedPhotosBasic = async (photoIds) => {
    console.log('开始处理选中照片的基础分析:', photoIds);

    const modalHtml = `
        <div class="modal fade" id="selectedBasicProcessModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">基础分析确认</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="alert alert-info">
                            <i class="bi bi-info-circle me-2"></i>
                            基础分析将对选中的 ${photoIds.length} 张照片进行质量评估，生成时间、EXIF等基础标签<br>
                            此功能无需AI，处理速度快，完全免费
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                            取消
                        </button>
                        <button type="button" class="btn btn-primary" onclick="startSelectedBasicProcessing(${JSON.stringify(photoIds).replace(/"/g, '&quot;')})">
                            <i class="bi bi-play-fill me-1"></i> 开始基础分析
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHtml);
    const modal = new bootstrap.Modal(document.getElementById('selectedBasicProcessModal'));
    modal.show();

    document.getElementById('selectedBasicProcessModal').addEventListener('hidden.bs.modal', function() {
        this.remove();
    });
};

// 处理选中的照片 - AI分析
window.processSelectedPhotosAI = async (photoIds) => {
    console.log('开始处理选中照片的AI分析:', photoIds);

    const modalHtml = `
        <div class="modal fade" id="selectedAIProcessModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">AI分析确认</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="alert alert-warning">
                            <i class="bi bi-exclamation-triangle me-2"></i>
                            AI分析将对选中的 ${photoIds.length} 张照片进行深度内容分析，生成场景、物体、情感等AI标签<br>
                            此功能需要大模型的API密钥，处理速度较慢
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                            取消
                        </button>
                        <button type="button" class="btn btn-primary" onclick="startSelectedAIProcessing(${JSON.stringify(photoIds).replace(/"/g, '&quot;')})">
                            <i class="bi bi-play-fill me-1"></i> 开始AI分析
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHtml);
    const modal = new bootstrap.Modal(document.getElementById('selectedAIProcessModal'));
    modal.show();

    document.getElementById('selectedAIProcessModal').addEventListener('hidden.bs.modal', function() {
        this.remove();
    });
};

// 开始处理选中的照片 - 基础分析
window.startSelectedBasicProcessing = async (photoIds) => {
    console.log('开始处理选中照片的基础分析:', photoIds);

    // 关闭确认模态框
    const confirmModal = bootstrap.Modal.getInstance(document.getElementById('selectedBasicProcessModal'));
    if (confirmModal) {
        confirmModal.hide();
    }

    // 显示基础分析模态框
    resetBasicModal();
    const modal = new bootstrap.Modal(document.getElementById('basicModal'));
    modal.show();

    // 直接开始处理选中的照片
    await startSelectedBasicAnalysis(photoIds);
};

// 开始处理选中的照片 - AI分析
window.startSelectedAIProcessing = async (photoIds) => {
    console.log('开始处理选中照片的AI分析:', photoIds);

    // 关闭确认模态框
    const confirmModal = bootstrap.Modal.getInstance(document.getElementById('selectedAIProcessModal'));
    if (confirmModal) {
        confirmModal.hide();
    }

    // 显示AI分析模态框
    resetAIModal();

    // 单次处理：隐藏取消按钮，强制用户等待完成
    const cancelBtn = document.querySelector('#aiModal .modal-footer .btn-secondary');
    if (cancelBtn) cancelBtn.style.display = 'none';

    const modal = new bootstrap.Modal(document.getElementById('aiModal'));
    modal.show();

    // 直接开始处理选中的照片
    await startSelectedAIAnalysis(photoIds);
};

// 处理选中的照片 - 基础分析（直接使用选中的照片ID）
async function startSelectedBasicAnalysis(selectedPhotoIds) {
    console.log('执行选中照片的基础分析处理:', selectedPhotoIds);

    // 显示进度
    document.getElementById('basicProgress').classList.remove('d-none');
    document.getElementById('startBasicBtn').disabled = true;
    document.getElementById('basicProgressBar').style.width = '0%';
    document.getElementById('basicStatus').textContent = '正在准备基础分析...';

    try {
        // 直接使用选中的照片ID
        const photoIds = selectedPhotoIds;

        if (photoIds.length === 0) {
            showWarning('没有选中需要基础分析的照片');
            document.getElementById('startBasicBtn').disabled = false;
            return;
        }

        // 开始基础分析
        const response = await fetch(`${window.CONFIG.API_BASE_URL}/analysis/start-analysis`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                photo_ids: photoIds,
                analysis_types: ['quality'],
                force_reprocess: true
            })
        });

        if (!response.ok) {
            throw new Error('基础分析请求失败');
        }

        const result = await response.json();
        // 基础分析任务已启动

        // 监控处理进度
        await monitorBasicAnalysisProgress(result.task_id, photoIds.length, photoIds.length);

    } catch (error) {
        console.error('基础分析启动失败:', error);
        showError('基础分析启动失败: ' + error.message);
        document.getElementById('startBasicBtn').disabled = false;
    }
}

// 处理选中的照片 - AI分析（直接使用选中的照片ID）
async function startSelectedAIAnalysis(selectedPhotoIds) {
    console.log('执行选中照片的AI分析处理:', selectedPhotoIds);

    // 显示进度
    document.getElementById('aiProgress').classList.remove('d-none');
    document.getElementById('startAIBtn').disabled = true;
    document.getElementById('aiProgressBar').style.width = '0%';
    document.getElementById('aiStatus').textContent = '正在准备AI分析...';

    try {
        // 🔒 启用AI分析模态框保护
        window.aiModalProtector.protect();

        // 直接使用选中的照片ID
        const photoIds = selectedPhotoIds;

        if (photoIds.length === 0) {
            showWarning('没有选中需要AI分析的照片');
            document.getElementById('startAIBtn').disabled = false;
            return;
        }

        // 开始AI分析
        const response = await fetch(`${window.CONFIG.API_BASE_URL}/analysis/start-analysis`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                photo_ids: photoIds,
                analysis_types: ['content'],
                force_reprocess: true
            })
        });

        if (!response.ok) {
            throw new Error('AI分析请求失败');
        }

        const result = await response.json();
        // AI分析任务已启动

        // 监控处理进度
        await monitorAIAnalysisProgress(result.task_id, photoIds.length, photoIds.length);

    } catch (error) {
        console.error('AI分析启动失败:', error);
        showError('AI分析启动失败: ' + error.message);
        document.getElementById('startAIBtn').disabled = false;

        // ❌ 出错时解除AI分析模态框保护
        window.aiModalProtector.unprotect();
    }
}


/**
 * 重置基础分析模态框到初始状态
 */
function resetBasicModal() {
    // 隐藏进度条
    document.getElementById('basicProgress').classList.add('d-none');

    // 重置进度条
    document.getElementById('basicProgressBar').style.width = '0%';

    // 重置状态文本
    document.getElementById('basicStatus').textContent = '正在处理...';

    // 启用开始按钮
    document.getElementById('startBasicBtn').disabled = false;

    // 隐藏照片数量统计（会根据API响应重新显示）
    document.getElementById('basicPhotoCountInfo').style.display = 'none';
}

/**
 * 重置AI分析模态框到初始状态
 */
function resetAIModal() {
    // 恢复aiProgress元素的原始内容（单次分析模式）
    const aiProgress = document.getElementById('aiProgress');
    if (aiProgress) {
        aiProgress.innerHTML = `
            <div class="progress mb-3">
                <div class="progress-bar" id="aiProgressBar" role="progressbar" style="width: 0%"></div>
            </div>
            <div id="aiStatus" class="text-center">正在处理...</div>
        `;
        aiProgress.classList.add('d-none');
    }

    // 启用开始按钮
    const startAIBtn = document.getElementById('startAIBtn');
    if (startAIBtn) startAIBtn.disabled = false;

    // 显示底部按钮区域
    const modalFooter = document.querySelector('#aiModal .modal-footer');
    if (modalFooter) modalFooter.style.display = 'flex';

    // 清理批次状态区域
    const aiBatchStatus = document.getElementById('aiBatchStatus');
    if (aiBatchStatus) aiBatchStatus.innerHTML = '';

    // 隐藏批次设置区域（会根据条件重新显示）
    const aiBatchSetup = document.getElementById('aiBatchSetup');
    if (aiBatchSetup) aiBatchSetup.style.display = 'none';

    // 隐藏照片数量统计（会根据API响应重新显示）
    const aiPhotoCountInfo = document.getElementById('aiPhotoCountInfo');
    if (aiPhotoCountInfo) aiPhotoCountInfo.style.display = 'none';
}

// 导出函数到全局作用域
window.monitorImportProgress = monitorImportProgress;
window.monitorBatchProgress = monitorBatchProgress;
window.resetBasicModal = resetBasicModal;
window.resetAIModal = resetAIModal;

/**
 * GPS转地址功能
 */
async function startBatchGpsToAddress() {
    const button = document.getElementById('gpsToAddressBtn');
    if (!button) return;

    const originalHtml = button.innerHTML;
    const originalDisabled = button.disabled;

    try {
        // 显示加载状态
        button.disabled = true;
        button.innerHTML = '<i class="bi bi-hourglass-split"></i> 处理中...';

        // 获取GPS统计信息
        const statsResponse = await fetch('/api/maps/photos/gps-stats');
        if (!statsResponse.ok) {
            throw new Error('获取GPS统计信息失败');
        }

        const stats = await statsResponse.json();

        if (stats.has_gps_without_address === 0) {
            showToast('没有需要转换的照片', 'info');
            return;
        }

        // 确认批量转换
        const confirmed = await showConfirmDialog(
            `批量GPS转地址`,
            `发现 ${stats.has_gps_without_address} 张照片有GPS信息但没有地址，是否开始批量转换？\n\n注意：此操作将在后台进行，不会阻塞界面。`
        );

        if (!confirmed) return;

        // 启动批量转换
        const batchSize = CONFIG.mapsConfig?.batch_size || 50; // 🔥 使用配置参数，默认50
        const convertResponse = await fetch('/api/maps/photos/batch-convert-gps-address', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({limit: batchSize}) // 🔥 使用配置的批次大小
        });

        const result = await convertResponse.json();

        if (convertResponse.ok) {
            showToast(result.message, 'success');

            // 检查是否还有更多照片需要转换
            const remaining = stats.has_gps_without_address - result.count;
            if (remaining > 0) {
                setTimeout(() => {
                    showToast(`还有 ${remaining} 张照片待转换，可再次点击按钮继续`, 'info');
                }, 2000);
            }

            // 刷新照片列表以显示最新状态
            setTimeout(() => {
                if (typeof loadPhotos === 'function') {
                    loadPhotos();
                    loadStats();
                }
            }, 1000);

        } else {
            showToast(result.detail || '批量转换启动失败', 'error');
        }

    } catch (error) {
        console.error('批量GPS转地址失败:', error);
        showToast('批量转换失败，请检查网络连接', 'error');
    } finally {
        // 恢复按钮状态
        button.disabled = originalDisabled;
        button.innerHTML = originalHtml;
    }
}

// 确认对话框函数（如果不存在）
function showConfirmDialog(title, message) {
    return new Promise((resolve) => {
        // 使用Bootstrap的模态框
        const modalHtml = `
            <div class="modal fade" id="confirmModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">${title}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <p style="white-space: pre-line;">${message}</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                            <button type="button" class="btn btn-primary" id="confirmBtn">确定</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // 移除现有模态框
        const existingModal = document.getElementById('confirmModal');
        if (existingModal) {
            existingModal.remove();
        }

        // 添加新模态框
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        const modal = new bootstrap.Modal(document.getElementById('confirmModal'));
        const confirmBtn = document.getElementById('confirmBtn');

        confirmBtn.addEventListener('click', () => {
            modal.hide();
            resolve(true);
        });

        document.getElementById('confirmModal').addEventListener('hidden.bs.modal', () => {
            resolve(false);
        });

        modal.show();
    });
}

// 绑定AI分析批次设置事件
document.addEventListener('DOMContentLoaded', function() {
    const aiBatchCountInput = document.getElementById('aiBatchCount');
    if (aiBatchCountInput) {
        aiBatchCountInput.addEventListener('input', function() {
            const totalCount = parseInt(document.getElementById('aiPhotoCountText')?.textContent?.match(/\d+/)?.[0]) || 0;
            if (totalCount > 0) {
                updateAIBatchPreview(totalCount);
            }
        });
    }
});



