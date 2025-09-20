/**
 * 家庭版智能照片系统 - 导入功能模块
 * 
 * 功能：
 * 1. 导入方式切换
 * 2. 文件导入处理
 * 3. 文件夹导入处理
 * 4. 导入进度监控
 * 5. 智能处理功能
 * 6. 智能通知系统（统一格式、详细结果、模态框展示）
 * 
 * 更新日志：
 * - 2025-01-19: 完善导入和智能处理通知系统
 *   - 统一通知格式：显示总数、成功、跳过、失败数量
 *   - 添加图标区分：✅全部成功、⚠️有跳过、❌有失败
 *   - 添加"查看详情"按钮，显示详细结果模态框
 *   - 通知不再自动消失，需用户手动关闭
 *   - 智能处理模态框在显示结果后自动关闭
 */

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
    console.log('切换导入方式:', method);
    
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
    console.log('🔍 点击浏览文件夹按钮');
    // 触发隐藏的文件夹选择输入框
    const folderFilesInput = document.getElementById('folderFiles');
    console.log('文件夹输入框:', folderFilesInput);
    if (folderFilesInput) {
        console.log('✅ 触发文件夹选择对话框');
        // 先清空之前的选择，避免浏览器缓存
        folderFilesInput.value = '';
        folderFilesInput.click();
    } else {
        console.error('❌ 找不到文件夹输入框');
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
    console.log('📁 文件夹选择事件触发');
    const files = event.target.files;
    console.log('选择的文件数量:', files?.length || 0);
    
    // 隐藏之前的错误信息
    hideImportError();
    
    // 清空文件导入的预览数据
    hideFilePreview();
    
    if (files && files.length > 0) {
        // 获取第一个文件的路径，去掉文件名得到文件夹路径
        const firstFile = files[0];
        const filePath = firstFile.webkitRelativePath || firstFile.name;
        const folderPath = filePath.substring(0, filePath.lastIndexOf('/'));
        
        console.log('文件夹路径:', folderPath);
        
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
        console.log(`选择了文件夹，包含 ${imageFiles.length} 个图片文件`);
        
        // 更新导入按钮状态
        handleFolderPathChange();
        
        // 延迟显示文件预览信息，确保浏览器确认对话框关闭后再显示
        setTimeout(() => {
            previewFolderContents(files);
            console.log('📋 文件预览已显示，等待用户确认导入');
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
    // 分析文件信息
    const stats = analyzeFiles(files);
    
    // 显示文件统计信息
    displayFileStats(stats);
    
    // 检查文件数量限制
    checkFileLimit(files.length);
    
    // 显示确认按钮
    showFileImportConfirmation(stats);
}

/**
 * 显示文件导入确认按钮
 * 
 * @param {Object} stats - 统计信息
 */
function showFileImportConfirmation(stats) {
    // 创建确认按钮区域
    const confirmDiv = document.getElementById('fileImportConfirmation');
    if (!confirmDiv) {
        // 如果不存在，创建一个
        const fileImportSection = document.getElementById('fileImportSection');
        const confirmArea = document.createElement('div');
        confirmArea.id = 'fileImportConfirmation';
        confirmArea.className = 'mt-3';
        fileImportSection.appendChild(confirmArea);
    }
    
    const confirmDivElement = document.getElementById('fileImportConfirmation');
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
    console.log('🚀 开始导入，检查配置和状态...');
    console.log('CONFIG 对象:', window.CONFIG);
    console.log('AppState 对象:', window.AppState);
    
    const importMethod = document.querySelector('input[name="importMethod"]:checked').value;
    console.log('选择的导入方式:', importMethod);
    
    if (importMethod === 'file') {
        console.log('执行文件导入...');
        await startFileImport();
    } else if (importMethod === 'folder') {
        console.log('执行文件夹导入...');
        await startFolderImport();
    } else {
        console.error('未知的导入方式:', importMethod);
        showError('未知的导入方式，请重新选择');
    }
}

/**
 * 开始文件导入
 */
async function startFileImport() {
    console.log('开始文件导入');
    const files = elements.photoFiles.files;
    
    if (files.length === 0) {
        showImportError('请先选择要导入的照片文件');
        return;
    }
    
    // 隐藏之前的错误信息
    hideImportError();
    
    // 显示进度条
    elements.importProgress.classList.remove('d-none');
    elements.importProgressBar.style.width = '0%';
    elements.importStatus.textContent = `正在准备处理 ${files.length} 个文件...`;
    
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
        xhr.upload.addEventListener('progress', (event) => {
            if (event.lengthComputable) {
                const percentComplete = Math.round((event.loaded / event.total) * 100);

                // 避免过于频繁的更新（至少1%的变化才更新）
                if (percentComplete - lastReportedProgress >= 1 || percentComplete === 100) {
                    elements.importProgressBar.style.width = `${percentComplete}%`;
                    elements.importStatus.textContent = `正在上传 ${files.length} 个文件... ${percentComplete}%`;
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
            elements.importStatus.textContent = `上传完成，后台正在处理 ${files.length} 个文件...`;
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
                        console.log('获取到任务ID:', taskId);
                        console.log('开始监控进度，总文件数:', files.length);
                        monitorImportProgress(taskId, files.length);
                    } else {
                        console.error('获取任务ID失败:', data);
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
            showImportError('网络连接失败，请检查服务器是否正常运行');
            elements.importProgress.classList.add('d-none');
        });

        // 发送请求
        xhr.open('POST', `${CONFIG.API_BASE_URL}/import/upload`);
        xhr.send(formData);
        
    } catch (error) {
        console.error('文件导入失败:', error);
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
    console.log('开始目录扫描导入');
    console.log('CONFIG.API_BASE_URL:', window.CONFIG?.API_BASE_URL);
    
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
        console.log('API URL:', apiUrl);
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
            elements.importStatus.textContent = `上传完成，后台正在处理 ${imageFiles.length} 个文件...`;
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
                        monitorImportProgress(taskId, imageFiles.length);
                    } else {
                        console.error('获取任务ID失败:', data);
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
            showImportError('网络连接失败，请检查服务器是否正常运行');
            elements.importProgress.classList.add('d-none');
        });

        // 发送请求
        xhr.open('POST', apiUrl);
        xhr.send(formData);
        
    } catch (error) {
        console.error('文件夹导入失败:', error);
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

/**
 * 开始智能处理
 */
async function startBatchProcess() {
    console.log('开始智能处理');
    console.log('智能处理按钮点击事件触发');
    
    // 智能处理默认执行所有三种分析类型
    const enableAIAnalysis = true;
    const enableQualityAssessment = true;
    const enableClassification = true;
    
    // 显示进度
    window.elements.batchProgress.classList.remove('d-none');
    window.elements.startBatchBtn.disabled = true;
    window.elements.batchProgressBar.style.width = '0%';
    window.elements.batchStatus.textContent = '正在准备智能处理...';
    
    try {
        // 首先获取所有照片的ID
        const photosResponse = await fetch(`${window.CONFIG.API_BASE_URL}/photos?limit=1000`);
        const photosData = await photosResponse.json();
        
        if (!photosResponse.ok) {
            showError('获取照片列表失败');
            return;
        }
        
        const photoIds = photosData.photos.map(photo => photo.id);
        
        if (photoIds.length === 0) {
            showWarning('没有找到需要处理的照片');
            return;
        }
        
        // 构建分析类型列表
        const analysisTypes = [];
        if (enableAIAnalysis) analysisTypes.push('content');
        if (enableQualityAssessment) analysisTypes.push('quality');
        if (enableClassification) analysisTypes.push('duplicate');
        
        const response = await fetch(`${window.CONFIG.API_BASE_URL}/analysis/batch-analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                photo_ids: photoIds,
                analysis_types: analysisTypes
            })
        });
        
        const data = await response.json();
        
        // 检查响应是否成功（批量分析API返回BatchAnalysisResponse格式）
        if (response.ok) {
            if (data.total_photos === 0) {
                // 没有照片需要处理的情况
                showSuccess(`✅ ${data.message || '没有需要处理的照片，所有照片都已完成分析'}`);
                window.elements.startBatchBtn.disabled = false;
                
                // 等待2秒后自动关闭模态框
                setTimeout(() => {
                    const modal = bootstrap.Modal.getInstance(window.elements.batchModal);
                    if (modal) {
                        modal.hide();
                    }
                }, 2000);
                return;
            }
            
            // 有照片需要处理的情况
            // 已删除智能处理开始通知，避免冗余（模态框已有进度条显示）
            
            // 保存初始总数，用于进度条计算
            const initialTotal = data.total_photos;
            
            // 使用真实的状态检查API
            let checkCount = 0;
            const maxChecks = 120; // 最多检查120次，每次1秒，总共2分钟
            
            const statusCheckInterval = setInterval(async () => {
                checkCount++;
                
                try {
                    // 调用真实的状态检查API，传递初始总数
                    const statusResponse = await fetch(`${window.CONFIG.API_BASE_URL}/analysis/queue/status?initial_total=${initialTotal}`);
                    const statusData = await statusResponse.json();
                    
                    console.log('处理状态:', statusData);
                    
                    // 更新进度条
                    const progress = Math.min(statusData.progress_percentage || 0, 95);
                    window.elements.batchProgressBar.style.width = `${progress}%`;
                    window.elements.batchStatus.textContent = `正在处理... ${Math.round(progress)}% (${statusData.batch_completed_photos}/${statusData.batch_total_photos})`;
                    
                     // 检查是否完成
                     if (statusData.is_complete || statusData.processing_photos === 0) {
                         // 立即停止状态检查
                         clearInterval(statusCheckInterval);
                         
                         window.elements.batchProgressBar.style.width = '100%';
                         window.elements.batchStatus.textContent = '智能处理完成！';
                         
                         // 重置按钮状态
                         window.elements.startBatchBtn.disabled = false;
                         
                         // 立即关闭智能处理模态框
                         const modal = bootstrap.Modal.getInstance(window.elements.batchModal);
                         if (modal) {
                             modal.hide();
                             
                             // 监听模态框关闭事件
                             window.elements.batchModal.addEventListener('hidden.bs.modal', function onModalHidden() {
                                 console.log('智能处理模态框已完全关闭，准备显示结果详情...', statusData);
                                 
                                 // 移除事件监听器，避免重复执行
                                 window.elements.batchModal.removeEventListener('hidden.bs.modal', onModalHidden);
                                 
                                 try {
                                     showBatchProcessDetails(statusData);
                                     console.log('智能处理结果详情模态框已调用');
                                 } catch (error) {
                                     console.error('显示智能处理结果详情模态框失败:', error);
                                     showError('显示处理结果失败: ' + error.message);
                                 }
                             }, { once: true });
                         } else {
                             // 如果无法获取模态框实例，直接显示结果详情
                             console.log('无法获取智能处理模态框实例，直接显示结果详情...', statusData);
                             try {
                                 showBatchProcessDetails(statusData);
                                 console.log('智能处理结果详情模态框已调用');
                             } catch (error) {
                                 console.error('显示智能处理结果详情模态框失败:', error);
                                 showError('显示处理结果失败: ' + error.message);
                             }
                         }
                         
                         // 等待3秒确保数据库事务完成，然后刷新照片列表和统计信息
                         setTimeout(async () => {
                             console.log('重新加载照片列表和统计信息...');
                             try {
                                 await window.loadPhotos();
                                 await window.loadStats();
                                 console.log('照片列表和统计信息重新加载完成');
                             } catch (error) {
                                 console.error('刷新数据失败:', error);
                                 // 如果刷新失败，显示错误提示
                                 showError('数据刷新失败，请手动刷新页面');
                             }
                         }, 3000);
                         
                         // 直接返回，避免继续执行后续的状态检查逻辑
                         return;
                     }
                } catch (error) {
                    console.error('检查处理状态失败:', error);
                    clearInterval(statusCheckInterval);
                    showError('检查处理状态失败');
                    window.elements.startBatchBtn.disabled = false;
                }
                
                // 超时保护
                if (checkCount >= maxChecks) {
                    clearInterval(statusCheckInterval);
                    showWarning('智能处理超时，请手动检查结果');
                    window.elements.startBatchBtn.disabled = false;
                }
            }, 1000);
            
        } else {
            showError(data.detail || '智能处理启动失败');
            window.elements.startBatchBtn.disabled = false;
        }
    } catch (error) {
        console.error('智能处理失败:', error);
        showError('智能处理失败');
        window.elements.startBatchBtn.disabled = false;
    }
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
/**
 * 获取需要处理的照片数量
 * 包括imported和error状态的照片
 */
async function getPhotoCounts() {
    try {
        console.log('获取照片数量统计...');
        
        // 获取imported状态的照片数量
        const importedResponse = await fetch(`${window.CONFIG.API_BASE_URL}/photos?limit=1&filters=${encodeURIComponent(JSON.stringify({status: 'imported'}))}`);
        const importedData = await importedResponse.json();
        
        // 获取error状态的照片数量
        const errorResponse = await fetch(`${window.CONFIG.API_BASE_URL}/photos?limit=1&filters=${encodeURIComponent(JSON.stringify({status: 'error'}))}`);
        const errorData = await errorResponse.json();
        
        if (importedResponse.ok && errorResponse.ok) {
            const importedCount = importedData.total || 0;
            const errorCount = errorData.total || 0;
            const totalCount = importedCount + errorCount;
            
            console.log(`照片数量统计 - 未处理: ${importedCount}, 失败: ${errorCount}, 总计: ${totalCount}`);
            
            // 更新显示
            const photoCountInfo = document.getElementById('photoCountInfo');
            const photoCountText = document.getElementById('photoCountText');
            
            if (totalCount > 0) {
                photoCountText.innerHTML = `共有 <strong>${totalCount}</strong> 张照片需要处理（未处理: ${importedCount}张，失败重试: ${errorCount}张）`;
                photoCountInfo.style.display = 'block';
            } else {
                photoCountText.innerHTML = '所有照片都已完成智能处理';
                photoCountInfo.style.display = 'block';
            }
        } else {
            console.error('获取照片数量失败:', importedData, errorData);
            // 隐藏统计信息
            document.getElementById('photoCountInfo').style.display = 'none';
        }
    } catch (error) {
        console.error('获取照片数量异常:', error);
        // 隐藏统计信息
        document.getElementById('photoCountInfo').style.display = 'none';
    }
}

/**
 * 智能处理弹窗显示时的处理
 */
function onBatchModalShow() {
    console.log('智能处理弹窗显示，重置状态并获取照片数量...');
    
    // 重置智能处理模态框的状态
    resetBatchModalState();
    
    // 获取照片数量
    getPhotoCounts();
}

/**
 * 重置智能处理模态框的状态
 */
function resetBatchModalState() {
    // 重置进度条
    const progressBar = document.getElementById('batchProgressBar');
    if (progressBar) {
        progressBar.style.width = '0%';
    }
    
    // 重置状态文本
    const statusText = document.getElementById('batchStatus');
    if (statusText) {
        statusText.textContent = '准备开始处理...';
    }
    
    // 隐藏进度区域
    const progressArea = document.getElementById('batchProgress');
    if (progressArea) {
        progressArea.classList.add('d-none');
    }
    
    // 重置开始处理按钮状态
    const startBtn = document.getElementById('startBatchBtn');
    if (startBtn) {
        startBtn.disabled = false;
        startBtn.textContent = '开始处理';
    }
    
    console.log('智能处理模态框状态已重置');
}

// 添加弹窗显示事件监听器
document.addEventListener('DOMContentLoaded', function() {
    const batchModal = document.getElementById('batchModal');
    if (batchModal) {
        batchModal.addEventListener('shown.bs.modal', onBatchModalShow);
    }
});

window.startImport = startImport;
window.startFileImport = startFileImport;
window.startFolderImport = startFolderImport;
window.monitorScanProgress = monitorScanProgress;
window.startBatchProcess = startBatchProcess;
window.getPhotoCounts = getPhotoCounts;
window.resetBatchModalState = resetBatchModalState;
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

/**
 * 监控导入任务进度
 * 
 * @param {string} taskId - 任务ID
 * @param {number} totalFiles - 总文件数量
 */
function monitorImportProgress(taskId, totalFiles) {
    let checkCount = 0;
    const maxChecks = 120; // 最多检查120次，每次0.5秒，总共1分钟
    
    console.log('开始监控进度，任务ID:', taskId, '总文件数:', totalFiles);
    
    const progressInterval = setInterval(async () => {
        checkCount++;
        
        console.log(`进度检查第${checkCount}次，任务ID: ${taskId}`);
        
        // 超时保护
        if (checkCount > maxChecks) {
            clearInterval(progressInterval);
            console.error('进度监控超时');
            showError('导入超时，请检查服务器状态');
            elements.importProgress.classList.add('d-none');
            return;
        }
        try {
            const apiUrl = `${CONFIG.API_BASE_URL}/import/scan-status/${taskId}`;
            console.log('调用API:', apiUrl);
            
            const response = await fetch(apiUrl);
            
            if (!response.ok) {
                console.error('进度查询失败:', response.status, response.statusText);
                return;
            }
            
            const statusData = await response.json();
            
            console.log('进度监控数据:', statusData);
            
            // 更新进度条
            const progress = statusData.progress_percentage || 0;
            elements.importProgressBar.style.width = `${progress}%`;
            elements.importStatus.textContent = `正在处理: ${statusData.processed_files || 0}/${totalFiles} (${progress}%) - 已导入: ${statusData.imported_count || 0}, 跳过: ${statusData.skipped_count || 0}, 失败: ${statusData.failed_count || 0}`;
            
            // 检查是否完成
            if (statusData.status === 'completed') {
                clearInterval(progressInterval);
                
                // 转换数据格式以匹配showImportDetails的期望
                const detailsData = {
                    total_files: statusData.total_files,
                    imported_photos: statusData.imported_count,
                    skipped_photos: statusData.skipped_count,
                    failed_photos: statusData.failed_count,
                    failed_files: statusData.failed_files
                };
                
                // 显示导入结果详情
                showImportDetails(detailsData);
                
                // 重新加载照片列表
                await loadPhotos();
                
                // 关闭导入模态框
                const modal = bootstrap.Modal.getInstance(elements.importModal);
                if (modal) {
                    modal.hide();
                }
            } else if (statusData.status === 'failed') {
                clearInterval(progressInterval);
                showError(`导入失败：${statusData.error || '未知错误'}`);
                elements.importProgress.classList.add('d-none');
            }
        } catch (error) {
            console.error('进度监控失败:', error);
        }
    }, 500); // 每0.5秒检查一次
}

// 导出函数到全局作用域
window.monitorImportProgress = monitorImportProgress;
