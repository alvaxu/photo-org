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
                        console.log('调用monitorImportProgress之前，进度条状态:');
                        console.log('进度条区域可见:', !elements.importProgress.classList.contains('d-none'));
                        console.log('进度条宽度:', elements.importProgressBar.style.width);
                        console.log('状态文本:', elements.importStatus.textContent);
                        console.log('开始监控进度，总文件数:', files.length);
                        elements.importStatus.textContent = `后台正在处理 ${files.length} 个文件...`;
                        elements.importDetails.textContent = '正在初始化处理任务...';
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
                        console.log('获取到任务ID:', taskId);
                        console.log('调用monitorImportProgress之前，进度条状态:');
                        console.log('进度条区域可见:', !elements.importProgress.classList.contains('d-none'));
                        console.log('进度条宽度:', elements.importProgressBar.style.width);
                        console.log('状态文本:', elements.importStatus.textContent);
                        console.log('开始监控进度，总文件数:', imageFiles.length);
                        elements.importStatus.textContent = `后台正在处理 ${imageFiles.length} 个文件...`;
                        elements.importDetails.textContent = '正在初始化处理任务...';
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
        // 获取所有待处理的照片ID（直接从数据库查询，无分页限制）
        const pendingResponse = await fetch(`${window.CONFIG.API_BASE_URL}/analysis/pending-photos`);
        const pendingData = await pendingResponse.json();

        if (!pendingResponse.ok) {
            showError('获取待处理照片列表失败');
            return;
        }

        const photoIds = pendingData.photo_ids || [];
        
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
            const initialTotal = photoIds.length;  // 使用实际获取到的待处理照片数量
            
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

                        // 清除照片选择状态
                        if (window.clearSelection) {
                            window.clearSelection();
                        }
                         
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
                
                // 移除超时保护，让处理持续运行直到完成
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
    const maxChecks = 120; // 最多检查120次，每次0.5秒，总共1分钟

    console.log('开始监控进度，任务ID:', taskId, '总文件数:', totalFiles);

    // 立即设置初始状态，确保进度条显示
    console.log('设置进度条初始状态...');
    elements.importProgressBar.style.width = '0%';
    elements.importProgressBar.setAttribute('aria-valuenow', '0');
    elements.importStatus.textContent = `正在处理: 0/${totalFiles} (0%)`;
    elements.importDetails.textContent = '正在初始化处理任务...';

    // 确保进度条区域可见
    console.log('移除进度条隐藏类...');
    elements.importProgress.classList.remove('d-none');
    console.log('进度条显示状态:', !elements.importProgress.classList.contains('d-none'));
    console.log('进度条元素:', elements.importProgress);
    console.log('进度条宽度:', elements.importProgressBar.style.width);

    const progressInterval = setInterval(async () => {
        checkCount++;
        
        console.log(`进度检查第${checkCount}次，任务ID: ${taskId}`);
        
        // 超时保护
        if (checkCount > maxChecks) {
            clearInterval(progressInterval);
            console.error('进度监控超时');
            elements.importStatus.textContent = '处理超时';
            elements.importDetails.textContent = '服务器处理时间过长，请检查服务器状态';
            elements.importProgressBar.classList.remove('progress-bar-striped', 'progress-bar-animated');
            elements.importProgressBar.classList.add('bg-warning');
            showError('导入超时，请检查服务器状态');
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
            elements.importProgressBar.setAttribute('aria-valuenow', progress);

            // 更新状态文本
            elements.importStatus.textContent = `正在处理: ${statusData.processed_files || 0}/${totalFiles} (${progress}%)`;

            // 显示统计信息
            if (statusData.processed_files > 0) {
                elements.importStats.style.display = 'flex';
                elements.processedCount.textContent = statusData.processed_files || 0;
                elements.importedCount.textContent = statusData.imported_count || 0;
                elements.skippedCount.textContent = statusData.skipped_count || 0;
                elements.failedCount.textContent = statusData.failed_count || 0;

                // 更新详情文本
                const imported = statusData.imported_count || 0;
                const skipped = statusData.skipped_count || 0;
                const failed = statusData.failed_count || 0;
                const totalProcessed = imported + skipped + failed;

                if (totalProcessed > 0) {
                    const successRate = ((imported / totalProcessed) * 100).toFixed(1);
                    elements.importDetails.textContent = `成功率: ${successRate}% | 导入: ${imported}, 跳过: ${skipped}, 失败: ${failed}`;
                }
            }
            
            // 检查是否完成
            if (statusData.status === 'completed') {
                clearInterval(progressInterval);

                // 更新最终状态显示
                elements.importProgressBar.style.width = '100%';
                elements.importProgressBar.setAttribute('aria-valuenow', '100');
                elements.importStatus.textContent = `处理完成！共处理 ${statusData.total_files} 个文件`;

                const imported = statusData.imported_count || 0;
                const skipped = statusData.skipped_count || 0;
                const failed = statusData.failed_count || 0;
                const totalProcessed = imported + skipped + failed;
                const successRate = totalProcessed > 0 ? ((imported / totalProcessed) * 100).toFixed(1) : '0.0';

                elements.importDetails.textContent = `最终结果: 成功率 ${successRate}% | 导入: ${imported}, 跳过: ${skipped}, 失败: ${failed}`;

                // 更新统计信息
                elements.processedCount.textContent = statusData.processed_files || 0;
                elements.importedCount.textContent = imported;
                elements.skippedCount.textContent = skipped;
                elements.failedCount.textContent = failed;

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
                    elements.importModal.addEventListener('hidden.bs.modal', function onModalHidden() {
                        console.log('导入模态框已完全关闭，准备显示结果详情...');

                        // 移除事件监听器，避免重复执行
                        elements.importModal.removeEventListener('hidden.bs.modal', onModalHidden);

                        try {
                            // 显示导入结果详情
                            showImportDetails(detailsData);

                            // 重新加载照片列表
                            loadPhotos();
                        } catch (error) {
                            console.error('显示导入结果详情失败:', error);
                            showError('显示结果失败: ' + error.message);
                        }
                    });
                } else {
                    // 如果找不到模态框实例，直接显示结果（降级处理）
                    console.warn('找不到导入模态框实例，直接显示结果');
                    showImportDetails(detailsData);
                    loadPhotos();
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
    }, 500); // 每0.5秒检查一次
}

/**
 * 批量处理器 - 处理选中的照片智能分析
 */
class BatchProcessor {
    constructor() {
        // 使用PhotoManager进行照片选择管理
    }

    // 处理选中的照片
    async processSelectedPhotos(forceReprocess = false) {
        // 使用PhotoManager获取选中的照片ID
        const selectedIds = window.PhotoManager ?
            Array.from(window.PhotoManager.selectedPhotos) :
            [];

        if (selectedIds.length === 0) {
            showWarning('请先选择要处理的照片');
            return;
        }

        // 显示确认模态框
        await this.showProcessConfirmation(selectedIds, forceReprocess);
    }

    // 显示处理确认模态框
    async showProcessConfirmation(photoIds, forceReprocess) {
        const stats = await this.getProcessingStats(photoIds);

        const modalHtml = `
            <div class="modal fade" id="processConfirmationModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                ${forceReprocess ? '重新处理' : '智能分析'}确认
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="alert alert-info">
                                <i class="bi bi-info-circle me-2"></i>
                                将对选中的所有照片进行智能分析，包括已分析的照片也会重新处理。
                            </div>

                            <div class="processing-preview">
                                <h6>处理统计：</h6>
                                <div class="row text-center mb-2">
                                    <div class="col-6">
                                        <div class="stat-item">
                                            <div class="stat-value">${stats.total}</div>
                                            <div class="stat-label">总照片</div>
                                        </div>
                                    </div>
                                    <div class="col-6">
                                        <div class="stat-item">
                                            <div class="stat-value text-success">${stats.fully_analyzed}</div>
                                            <div class="stat-label">已完整分析</div>
                                        </div>
                                    </div>
                                </div>
                                <div class="row text-center">
                                    <div class="col-4">
                                        <div class="stat-item">
                                            <div class="stat-value text-muted">${stats.unanalyzed}</div>
                                            <div class="stat-label">未分析</div>
                                        </div>
                                    </div>
                                    <div class="col-4">
                                        <div class="stat-item">
                                            <div class="stat-value text-warning">${stats.missing_quality}</div>
                                            <div class="stat-label">缺质量评估</div>
                                        </div>
                                    </div>
                                    <div class="col-4">
                                        <div class="stat-item">
                                            <div class="stat-value text-info">${stats.missing_ai}</div>
                                            <div class="stat-label">缺AI分析</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                                取消
                            </button>
                            <button type="button" class="btn btn-primary" onclick="startBatchProcessing(${JSON.stringify(photoIds)}, ${forceReprocess})">
                                <i class="bi bi-play-fill me-1"></i> 开始处理
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // 显示模态框
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        const modal = new bootstrap.Modal(document.getElementById('processConfirmationModal'));
        modal.show();

        // 模态框关闭时清理DOM
        document.getElementById('processConfirmationModal').addEventListener('hidden.bs.modal', function() {
            this.remove();
        });
    }

    // 获取处理统计信息
    async getProcessingStats(photoIds) {
        const stats = {
            total: photoIds.length,
            unanalyzed: 0,      // 未分析（都没做）
            fully_analyzed: 0,  // 已分析（完整分析）
            missing_quality: 0, // 未质量评估（有AI分析，无质量评估）
            missing_ai: 0       // 未AI分析（有质量评估，无AI分析）
        };

        try {
            // 查询每张照片的状态
            for (const photoId of photoIds) {
                const photo = await this.getPhotoDetails(photoId);

                if (photo) {
                    // 简化判断逻辑：使用现有的API响应结构
                    const hasAnalysis = !!photo.analysis;  // 是否有PhotoAnalysis记录
                    const hasQuality = !!photo.quality;    // 是否有PhotoQuality记录

                    console.log(`照片 ${photoId} 状态:`, {
                        hasAnalysis,
                        hasQuality,
                        status: photo.status,
                        analysis_type: photo.analysis ? photo.analysis.type : 'none'
                    });

                    if (!hasAnalysis && !hasQuality) {
                        // 未分析（都没做）
                        stats.unanalyzed++;
                    } else if (hasAnalysis && hasQuality) {
                        // 已分析（完整分析）
                        stats.fully_analyzed++;
                    } else if (hasAnalysis && !hasQuality) {
                        // 未质量评估（有AI分析，无质量评估）
                        stats.missing_quality++;
                    } else if (!hasAnalysis && hasQuality) {
                        // 未AI分析（有质量评估，无AI分析）
                        stats.missing_ai++;
                    }
                } else {
                    // 如果无法获取照片详情，假设为未分析
                    stats.unanalyzed++;
                }
            }
        } catch (error) {
            console.error('获取照片状态失败:', error);
            // 如果查询失败，假设所有照片都未分析
            stats.unanalyzed = photoIds.length;
            stats.fully_analyzed = 0;
            stats.missing_quality = 0;
            stats.missing_ai = 0;
        }

        return stats;
    }

    // 获取照片详情
    async getPhotoDetails(photoId) {
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/photos/${photoId}`);
            if (response.ok) {
                const data = await response.json();
                return data.data || data; // 处理不同的响应格式
            }
        } catch (error) {
            console.error('获取照片详情失败:', error);
        }
        return null;
    }

    // 开始批量处理
    async startBatchProcessing(photoIds, forceReprocess) {
        // 关闭确认模态框
        const confirmModal = bootstrap.Modal.getInstance(document.getElementById('processConfirmationModal'));
        if (confirmModal) {
            confirmModal.hide();
        }

        // 显示处理进度模态框
        this.showProcessingModal();

        // 短暂延迟，让用户看到进度模态框
        await new Promise(resolve => setTimeout(resolve, 500));

        try {
            // 调用批量分析API
            const response = await fetch(`${CONFIG.API_BASE_URL}/analysis/batch-analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    photo_ids: photoIds,
                    analysis_types: ['content', 'quality', 'duplicate'],
                    force_reprocess: forceReprocess
                })
            });

            if (!response.ok) {
                throw new Error('批量分析请求失败');
            }

            const result = await response.json();

            // FastAPI BackgroundTasks异步处理，需要监控处理进度
            await this.monitorBatchProcessingProgress(photoIds, result);

        } catch (error) {
            console.error('批量处理启动失败:', error);

            // 即使前端出错，后端可能仍在处理，显示友好的提示
            if (error.message.includes('monitorBatchProcessingProgress') ||
                error.message.includes('getPhotoDetails')) {
                // 如果是监控过程中的错误，说明API调用成功但监控失败
                showWarning('智能分析任务已启动，后台正在处理中。如需查看进度请刷新页面。');
            } else {
                // 如果是API调用失败，显示错误
                showError('批量处理启动失败: ' + error.message);
            }

            this.hideProcessingModal();
        }
    }

    // 监控批量处理进度
    async monitorBatchProcessingProgress(photoIds, initialResult) {
        console.log('开始监控批量处理进度:', photoIds);

        const progressBar = document.querySelector('#batchProcessingModal .progress-bar');
        const statusText = document.querySelector('#batchProcessingModal .processing-status span');
        const totalPhotos = photoIds.length;

        let completedPhotos = 0;
        let checkCount = 0;
        const maxChecks = 300; // 最多检查5分钟 (300 * 1秒)

        // 更新进度条
        const updateProgress = (completed, total) => {
            const percentage = Math.round((completed / total) * 100);
            progressBar.style.width = `${percentage}%`;
            statusText.textContent = `正在处理照片... (${completed}/${total})`;
        };

        // 检查照片状态
        const checkProgress = async () => {
            checkCount++;

            try {
                // 获取所有选中照片的当前状态
                const currentStates = [];
                for (const photoId of photoIds) {
                    const photo = await this.getPhotoDetails(photoId);
                    if (photo) {
                        currentStates.push({
                            id: photoId,
                            hasAnalysis: !!photo.analysis,
                            hasQuality: !!photo.quality,
                            status: photo.status
                        });
                    }
                }

                // 计算完成数量（有分析记录或质量记录的照片）
                const newlyCompleted = currentStates.filter(state =>
                    state.hasAnalysis || state.hasQuality || state.status === 'completed'
                ).length;

                // 更新进度
                if (newlyCompleted > completedPhotos) {
                    completedPhotos = newlyCompleted;
                    updateProgress(completedPhotos, totalPhotos);
                }

                // 检查是否全部完成
                if (completedPhotos >= totalPhotos || checkCount >= maxChecks) {
                    console.log('批量处理完成或超时，显示结果');
                    await this.showBatchProcessingResults(photoIds);
                    return;
                }

                // 继续监控
                setTimeout(checkProgress, 1000); // 每秒检查一次

            } catch (error) {
                console.error('检查处理进度失败:', error);

                // 如果是网络错误，继续监控（后端可能仍在处理）
                if (checkCount < maxChecks) {
                    console.log('网络错误，继续监控处理进度...');
                    setTimeout(checkProgress, 2000); // 2秒后重试
                } else {
                    console.log('监控超时，显示当前状态');
                    // 即使监控失败，也尝试显示结果
                    await this.showBatchProcessingResults(photoIds);
                }
            }
        };

        // 开始监控
        updateProgress(0, totalPhotos);
        setTimeout(checkProgress, 1000); // 1秒后开始第一次检查
    }

    // 显示批量处理结果
    async showBatchProcessingResults(selectedIds) {
        console.log('显示批量处理结果，重新计算统计信息');

        // 隐藏处理进度模态框
        this.hideProcessingModal();

        // 重新获取所有选中照片的最终状态
        let finalStats;
        try {
            finalStats = await this.getProcessingStats(selectedIds);
        } catch (error) {
            console.error('获取最终统计信息失败:', error);
            // 如果获取统计失败，使用默认值
            finalStats = {
                total: selectedIds.length,
                fully_analyzed: 0,
                unanalyzed: selectedIds.length,
                missing_quality: 0,
                missing_ai: 0
            };
        }

        // 显示最终统计结果
        if (window.showBatchProcessDetails) {
            // 适配现有的showBatchProcessDetails函数格式
            const stats = {
                batch_total_photos: finalStats.total,
                batch_completed_photos: finalStats.fully_analyzed,
                batch_failed_photos: finalStats.unanalyzed + finalStats.missing_quality + finalStats.missing_ai,
                total: finalStats.total,
                fully_analyzed: finalStats.fully_analyzed,
                unanalyzed: finalStats.unanalyzed,
                missing_quality: finalStats.missing_quality,
                missing_ai: finalStats.missing_ai,
                successful_analyses: finalStats.fully_analyzed,
                failed_analyses: finalStats.unanalyzed + finalStats.missing_quality + finalStats.missing_ai,
                results: [], // 可以后续扩展
                errors: []   // 可以后续扩展
            };

            console.log('显示批量处理统计结果:', stats);
            window.showBatchProcessDetails(stats);
        } else {
            // 降级处理：显示简单的成功消息
            showSuccess(`智能分析完成！共处理 ${finalStats.total} 张照片，已完成 ${finalStats.fully_analyzed} 张`);
        }

        // 刷新照片列表
        if (window.loadPhotos) {
            window.loadPhotos();
        }

        // 清理选择状态
        if (window.PhotoManager) {
            window.PhotoManager.clearSelection();
        }
    }

    // 显示处理进度模态框
    showProcessingModal() {
        const modalHtml = `
            <div class="modal fade" id="batchProcessingModal" tabindex="-1" data-bs-backdrop="static">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">智能处理进度</h5>
                        </div>
                        <div class="modal-body">
                            <div class="progress mb-3">
                                <div class="progress-bar progress-bar-striped progress-bar-animated"
                                     style="width: 0%"></div>
                            </div>
                            <div class="processing-status">
                                <div class="alert alert-info">
                                    <i class="bi bi-info-circle me-2"></i>
                                    <span>正在进行智能分析，请稍候...</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);
        const modal = new bootstrap.Modal(document.getElementById('batchProcessingModal'));
        modal.show();
    }

    // 隐藏处理进度模态框
    hideProcessingModal() {
        const modal = bootstrap.Modal.getInstance(document.getElementById('batchProcessingModal'));
        if (modal) {
            modal.hide();
            document.getElementById('batchProcessingModal').remove();
        }
    }

    // 监控处理进度
    async monitorProcessingProgress(taskId, totalPhotos) {
        const progressBar = document.querySelector('#batchProcessingModal .progress-bar');
        const statusText = document.querySelector('#batchProcessingModal .processing-status span');

        const checkProgress = async () => {
            try {
                const response = await fetch(`${CONFIG.API_BASE_URL}/analysis/queue/status?initial_total=${totalPhotos}`);
                const status = await response.json();

                if (status.is_complete) {
                    // 处理完成
                    progressBar.style.width = '100%';
                    statusText.textContent = '智能处理完成！';

                    // 显示详细的处理结果
                    setTimeout(() => {
                        this.showProcessingResults(status, totalPhotos);
                    }, 1000);
                } else {
                    // 更新进度
                    const progress = Math.min(status.progress_percentage || 0, 95);
                    progressBar.style.width = `${progress}%`;
                    statusText.textContent = `正在处理... ${Math.round(progress)}% (${status.batch_completed_photos}/${status.batch_total_photos})`;

                    // 继续监控
                    setTimeout(checkProgress, 1000);
                }
            } catch (error) {
                console.error('进度检查失败:', error);
                statusText.textContent = '进度检查失败，正在重试...';
                setTimeout(checkProgress, 2000);
            }
        };

        // 开始监控
        checkProgress();
    }

    // 显示处理结果详情
    showProcessingResults(status, totalPhotos) {
        // 关闭处理进度模态框
        this.hideProcessingModal();

        // 构建结果数据
        const completedPhotos = status.batch_completed_photos || 0;
        const failedPhotos = totalPhotos - completedPhotos;

        // 准备结果详情数据
        const resultData = {
            batch_total_photos: totalPhotos,
            batch_completed_photos: completedPhotos,
            batch_failed_photos: failedPhotos,
            status: status,
            errors: status.errors || []
        };

        // 调用现有的结果显示函数
        if (window.showBatchProcessDetails) {
            window.showBatchProcessDetails(resultData);
        } else {
            console.error('showBatchProcessDetails 函数不存在');
            // 降级处理：直接刷新页面
            if (window.loadPhotos) {
                window.loadPhotos();
            }
            if (window.PhotoManager) {
                window.PhotoManager.clearSelection();
            }
        }
    }

}

// 创建全局实例
console.log('=== 创建BatchProcessor实例 ===');
window.batchProcessor = new BatchProcessor();
console.log('BatchProcessor实例创建完成:', !!window.batchProcessor);

// 更新全局函数
// 所有选中的照片都要处理，包括已分析的
window.processSelectedPhotos = () => window.batchProcessor.processSelectedPhotos(true);
window.reprocessSelectedPhotos = () => window.batchProcessor.processSelectedPhotos(true);

/**
 * 开始基础分析
 */
async function startBasicAnalysis() {
    console.log('开始基础分析');

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
 * 开始AI分析
 */
async function startAIAnalysis() {
    console.log('开始AI分析');

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

    // 显示进度
    document.getElementById('basicProgress').classList.remove('d-none');
    document.getElementById('startBasicBtn').disabled = true;
    document.getElementById('basicProgressBar').style.width = '0%';
    document.getElementById('basicStatus').textContent = '正在准备基础分析...';

    try {
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

        // 获取任务开始时的待处理照片总数（imported + error）
        let pendingTotal = photoIds.length; // 默认使用本次任务的照片数
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
        await monitorBasicAnalysisProgress(data.task_id, photoIds.length, pendingTotal);

    } catch (error) {
        console.error('基础分析处理失败:', error);
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
    console.log(`开始AI分析分批处理: ${photoIds.length}张照片分${batchCount}批`);

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

    for (let i = 0; i < batches.length; i++) {
        const batch = batches[i];
        console.log(`处理第${i + 1}批: ${batch.photoIds.length}张照片`);

        // 更新批次进度显示
        updateAIBatchProgress(i + 1, batches.length, batch, totalPhotosInAllBatches);

        try {
            // 提交当前批次
            await submitAIBatch(batch.photoIds);

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
    try {
        // 计算总照片数
        const totalPhotosInBatches = batches.reduce((sum, batch) => sum + batch.photoIds.length, 0);
        const completedPhotos = userStopped ? (i * batch.photoIds.length) : totalPhotosInBatches;

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

    } catch (error) {
        console.error('显示最终结果失败:', error);
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
}

/**
 * 处理单批次AI分析（少量照片时的直接处理）
 */
async function processAISingleBatch(photoIds) {
    console.log(`直接处理AI分析: ${photoIds.length}张照片`);

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
 * 提交单个AI分析批次
 */
async function submitAIBatch(photoIds) {
    console.log(`提交AI分析批次: ${photoIds.length}张照片`);

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

    return data;
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
    const maxChecks = 120; // 最多检查120次，每次1秒，总共2分钟

    const statusCheckInterval = setInterval(async () => {
        checkCount++;

        try {
            const statusResponse = await fetch(`${window.CONFIG.API_BASE_URL}/analysis/task-status/${taskId}?initial_total=${initialTotal}`);
            const statusData = await statusResponse.json();

            console.log('基础分析状态:', statusData);

            // 更新进度条
            const progress = Math.min(statusData.progress_percentage || 0, 95);
            document.getElementById('basicProgressBar').style.width = `${progress}%`;
            document.getElementById('basicStatus').textContent = `正在分析... ${Math.round(progress)}% (${statusData.completed_photos}/${statusData.total_photos})`;

            // 检查是否完成
            if (statusData.status === 'completed' || statusData.processing_photos === 0) {
                clearInterval(statusCheckInterval);

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
    const maxChecks = 120; // 最多检查120次，每次1秒，总共2分钟

    const statusCheckInterval = setInterval(async () => {
        checkCount++;

        try {
            const statusResponse = await fetch(`${window.CONFIG.API_BASE_URL}/analysis/task-status/${taskId}?initial_total=${initialTotal}`);
            const statusData = await statusResponse.json();

            console.log('AI分析状态:', statusData);

            // 更新进度条
            const progress = Math.min(statusData.progress_percentage || 0, 95);
            document.getElementById('aiProgressBar').style.width = `${progress}%`;
            document.getElementById('aiStatus').textContent = `正在分析... ${Math.round(progress)}% (${statusData.completed_photos}/${statusData.total_photos})`;

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
        console.log('基础分析任务已启动:', result);

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
        console.log('AI分析任务已启动:', result);

        // 监控处理进度
        await monitorAIAnalysisProgress(result.task_id, photoIds.length, photoIds.length);

    } catch (error) {
        console.error('AI分析启动失败:', error);
        showError('AI分析启动失败: ' + error.message);
        document.getElementById('startAIBtn').disabled = false;
    }
}

window.startBatchProcessing = (photoIds, forceReprocess) => window.batchProcessor.startBatchProcessing(photoIds, forceReprocess);

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
    // 隐藏进度条
    const aiProgress = document.getElementById('aiProgress');
    if (aiProgress) aiProgress.classList.add('d-none');

    // 重置进度条
    const aiProgressBar = document.getElementById('aiProgressBar');
    if (aiProgressBar) aiProgressBar.style.width = '0%';

    // 重置状态文本
    const aiStatus = document.getElementById('aiStatus');
    if (aiStatus) aiStatus.textContent = '正在处理...';

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
window.resetBasicModal = resetBasicModal;
window.resetAIModal = resetAIModal;

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

