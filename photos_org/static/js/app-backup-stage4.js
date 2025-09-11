

/**
 * 家庭单机版智能照片整理系统 - 主应用脚本
 */

// 注意：CONFIG, AppState, searchTypePlaceholders, searchScopeHints 已移至 app-data.js

// DOM 元素缓存
let elements = {};

// 初始化应用
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// 注意：loadHotData 函数已移至 app-data.js

function initializeApp() {
    console.log('🚀 初始化家庭单机版智能照片整理系统');

    // 缓存DOM元素
    cacheElements();

    // 绑定事件监听器
    bindEvents();

    // 初始化UI组件
    initializeUI();
    
    // 加载热门数据
    loadHotData();

    // 加载初始数据
    loadInitialData();

    // 设置定期刷新
    setupAutoRefresh();
}

function cacheElements() {
    console.log('📋 缓存DOM元素');

    elements = {
        // 导航
        navPhotos: document.getElementById('navPhotos'),

        // 操作按钮
        importBtn: document.getElementById('importBtn'),
        batchBtn: document.getElementById('batchBtn'),

        // 搜索和筛选
        searchInput: document.getElementById('searchInput'),
        searchBtn: document.getElementById('searchBtn'),
    searchType: document.getElementById('searchType'),
    searchScopeHint: document.getElementById('searchScopeHint'),
    searchSuggestions: document.getElementById('searchSuggestions'),
        dateFilter: document.getElementById('dateFilter'),
        customDateRange: document.getElementById('customDateRange'),
        startDate: document.getElementById('startDate'),
        endDate: document.getElementById('endDate'),
        qualityFilter: document.getElementById('qualityFilter'),
        sortBy: document.getElementById('sortBy'),
        sortOrder: document.getElementById('sortOrder'),
        clearFilters: document.getElementById('clearFilters'),
        clearFiltersSmall: document.getElementById('clearFiltersSmall'),
        filterStatus: document.getElementById('filterStatus'),
        filterStatusText: document.getElementById('filterStatusText'),

        // 视图切换
        gridView: document.getElementById('gridView'),
        listView: document.getElementById('listView'),

        // 统计信息
        statsRow: document.getElementById('statsRow'),

        // 照片区域
        photoCount: document.getElementById('photoCount'),
        loadingIndicator: document.getElementById('loadingIndicator'),
        emptyState: document.getElementById('emptyState'),
        photosGrid: document.getElementById('photosGrid'),
        paginationContainer: document.getElementById('paginationContainer'),
        pagination: document.getElementById('pagination'),

        // 选择操作
        selectAllBtn: document.getElementById('selectAllBtn'),
        clearSelectionBtn: document.getElementById('clearSelectionBtn'),
        deleteSelectedBtn: document.getElementById('deleteSelectedBtn'),

        // 模态框
        photoModal: document.getElementById('photoModal'),
        importModal: document.getElementById('importModal'),
        batchModal: document.getElementById('batchModal'),

        // 导入相关
        photoFiles: document.getElementById('photoFiles'),
        startImportBtn: document.getElementById('startImportBtn'),
        importFirstBtn: document.getElementById('importFirstBtn'),
        importProgress: document.getElementById('importProgress'),
        importProgressBar: document.getElementById('importProgressBar'),
        importStatus: document.getElementById('importStatus'),
        
        // 导入方式切换
        fileImport: document.getElementById('fileImport'),
        folderImport: document.getElementById('folderImport'),
        fileImportSection: document.getElementById('fileImportSection'),
        folderImportSection: document.getElementById('folderImportSection'),
        folderPath: document.getElementById('folderPath'),
        browseFolderBtn: document.getElementById('browseFolderBtn'),
        recursiveScan: document.getElementById('recursiveScan'),

        // 批量处理相关
        startBatchBtn: document.getElementById('startBatchBtn'),
        batchProgress: document.getElementById('batchProgress'),
        batchProgressBar: document.getElementById('batchProgressBar'),
        batchStatus: document.getElementById('batchStatus')
    };
}

function bindEvents() {
    console.log('🔗 绑定事件监听器');

    // 导航事件
    elements.navPhotos.addEventListener('click', (e) => {
        e.preventDefault();
        switchSection('photos');
    });

    // 搜索事件
    elements.searchInput.addEventListener('input', debounce(handleSearch, CONFIG.DEBOUNCE_DELAY));
    elements.searchBtn.addEventListener('click', handleSearch);
    elements.searchType.addEventListener('change', handleSearchTypeChange);
    elements.dateFilter.addEventListener('change', handleDateFilterChange);
    elements.qualityFilter.addEventListener('change', handleFilterChange);
    elements.sortBy.addEventListener('change', handleSortChange);
    elements.sortOrder.addEventListener('change', handleSortChange);
    elements.startDate.addEventListener('change', handleCustomDateChange);
    elements.endDate.addEventListener('change', handleCustomDateChange);
    elements.clearFilters.addEventListener('click', clearAllFilters);
    elements.clearFiltersSmall.addEventListener('click', clearAllFilters);

    // 视图切换事件
    elements.gridView.addEventListener('change', () => switchView('grid'));
    elements.listView.addEventListener('change', () => switchView('list'));

    // 导入事件
    // 注意：importBtn 和 batchBtn 使用 data-bs-toggle="modal" 自动处理，不需要手动监听
    elements.importFirstBtn.addEventListener('click', showImportModal);
    elements.photoFiles.addEventListener('change', handleFileSelection);
    elements.startImportBtn.addEventListener('click', startImport);
    
    // 导入方式切换事件
    elements.fileImport.addEventListener('change', () => switchImportMethod('file'));
    elements.folderImport.addEventListener('change', () => switchImportMethod('folder'));
    elements.folderPath.addEventListener('input', handleFolderPathChange);
    elements.browseFolderBtn.addEventListener('click', browseFolder);
    
    // 绑定文件夹选择事件
    const folderFilesInput = document.getElementById('folderFiles');
    if (folderFilesInput) {
        folderFilesInput.addEventListener('change', handleFolderSelection);
    }

    // 批量处理事件
    // 注意：batchBtn 使用 data-bs-toggle="modal" 自动处理，不需要手动监听
    elements.startBatchBtn.addEventListener('click', startBatchProcess);
    
    // 添加调试信息
    console.log('批量处理按钮绑定状态:', {
        batchBtn: !!elements.batchBtn,
        startBatchBtn: !!elements.startBatchBtn
    });

    // 选择操作事件
    elements.selectAllBtn.addEventListener('click', selectAllPhotos);
    elements.clearSelectionBtn.addEventListener('click', clearSelection);
    elements.deleteSelectedBtn.addEventListener('click', deleteSelectedPhotos);

    // 键盘快捷键
    document.addEventListener('keydown', handleKeyboard);
}

// 注意：initializeUI 函数已移至 app-ui.js

function loadInitialData() {
    console.log('📊 加载初始数据');

    // 加载统计信息
    loadStats();

    // 加载第一页照片
    loadPhotos(1);
}

function setupAutoRefresh() {
    // 每5分钟自动刷新统计信息
    setInterval(() => {
        loadStats();
    }, 5 * 60 * 1000);
}

// 注意：搜索和筛选函数已移至 app-data.js

// 注意：switchView, showImportModal, showBatchModal 函数已移至 app-ui.js

function handleFileSelection(event) {
    const files = event.target.files;
    const hasFiles = files && files.length > 0;

    elements.startImportBtn.disabled = !hasFiles;

    if (hasFiles) {
        elements.startImportBtn.textContent = `开始导入 (${files.length} 个文件)`;
    } else {
        elements.startImportBtn.textContent = '开始导入';
    }
}

function handleKeyboard(event) {
    // Ctrl+A 全选
    if (event.ctrlKey && event.key === 'a') {
        event.preventDefault();
        selectAllPhotos();
    }

    // Delete 键删除选中照片
    if (event.key === 'Delete' && AppState.selectedPhotos.size > 0) {
        deleteSelectedPhotos();
    }

    // Escape 键取消选择
    if (event.key === 'Escape') {
        clearSelection();
    }
}

// 注意：数据加载函数 loadStats, loadPhotos 已移至 app-data.js

// 注意：渲染函数已移至 app-data.js

// 注意：renderPhotos, renderGridView, renderListView 已移至 app-data.js

function createPhotoCard(photo) {
    const allTags = photo.tags || [];
    const visibleTags = allTags.slice(0, 5);
    const hiddenTagsCount = allTags.length - 5;
    
    const visibleTagsHtml = visibleTags.map(tag =>
        `<span class="photo-tag">${tag}</span>`
    ).join('');
    
    const hiddenTagsHtml = allTags.slice(5).map(tag =>
        `<span class="photo-tag">${tag}</span>`
    ).join('');

    // 获取质量信息
    const qualityLevel = photo.quality?.level || photo.analysis?.quality_rating || '';
    const qualityClass = getQualityClass(qualityLevel);
    const qualityText = getQualityText(qualityLevel);

    return `
        <div class="col-1 photo-card" data-photo-id="${photo.id}">
            <div class="photo-image-container">
                <img src="/${(photo.thumbnail_path || CONFIG.IMAGE_PLACEHOLDER).replace(/\\/g, '/')}"
                     alt="${photo.filename}"
                     class="photo-image"
                     loading="lazy">
                <div class="photo-overlay">
                    <i class="bi bi-eye text-white" style="font-size: 2rem;"></i>
                </div>
            </div>
            <div class="photo-info">
                <div class="photo-title">${photo.filename}</div>
                <div class="photo-meta">
                    <i class="bi bi-calendar me-1"></i>${formatDate(photo.taken_at)} (拍摄日期)
                </div>
                <div class="photo-tags">
                    <div class="visible-tags">
                        ${visibleTagsHtml}
                    </div>
                    ${hiddenTagsCount > 0 ? `
                        <div class="hidden-tags" style="display: none;">
                            ${hiddenTagsHtml}
                        </div>
                        <span class="tag-toggle" onclick="toggleTags(this, event)" data-photo-id="${photo.id}">
                            +${hiddenTagsCount} 更多
                        </span>
                    ` : ''}
                </div>
                <div class="photo-quality ${qualityClass}">
                    ${qualityText}
                </div>
            </div>
        </div>
    `;
}

function createPhotoListItem(photo) {
    const allTags = photo.tags || [];
    const visibleTags = allTags.slice(0, 5);
    const hiddenTagsCount = allTags.length - 5;
    
    const visibleTagsHtml = visibleTags.map(tag =>
        `<span class="badge bg-secondary me-1 mb-1">${tag}</span>`
    ).join('');
    
    const hiddenTagsHtml = allTags.slice(5).map(tag =>
        `<span class="badge bg-secondary me-1 mb-1">${tag}</span>`
    ).join('');

    const qualityClass = getQualityClass(photo.quality?.level || '');
    const qualityText = getQualityText(photo.quality?.level || '');

    // 格式化文件大小
    const formatFileSize = (bytes) => {
        if (!bytes) return '未知';
        const units = ['B', 'KB', 'MB', 'GB'];
        let size = bytes;
        let unitIndex = 0;
        while (size >= 1024 && unitIndex < units.length - 1) {
            size /= 1024;
            unitIndex++;
        }
        return `${size.toFixed(1)} ${units[unitIndex]}`;
    };

    // 格式化分辨率
    const resolution = photo.width && photo.height ? `${photo.width} × ${photo.height}` : '未知';

    return `
        <div class="photo-list-item" data-photo-id="${photo.id}">
            <div class="photo-thumbnail-container">
                <img src="/${(photo.thumbnail_path || CONFIG.IMAGE_PLACEHOLDER).replace(/\\/g, '/')}"
                     alt="${photo.filename}"
                     class="photo-thumbnail">
                <div class="photo-overlay">
                    <i class="bi bi-eye text-white"></i>
                </div>
            </div>
            <div class="photo-details">
                <div class="photo-header">
                    <div class="photo-title">${photo.filename}</div>
                    <div class="photo-actions">
                        <span class="badge ${qualityClass}">${qualityText}</span>
                    </div>
                </div>
                <div class="photo-meta">
                    <div class="meta-row">
                        <span class="meta-item">
                            <i class="bi bi-calendar me-1"></i>
                            ${formatDate(photo.taken_at)} (拍摄日期)
                        </span>
                        <span class="meta-item">
                            <i class="bi bi-geo-alt me-1"></i>
                            ${photo.location_name || '未知位置'}
                        </span>
                        <span class="meta-item">
                            <i class="bi bi-camera me-1"></i>
                            ${photo.camera_make || '未知'} ${photo.camera_model || ''}
                        </span>
                    </div>
                    <div class="meta-row">
                        <span class="meta-item">
                            <i class="bi bi-image me-1"></i>
                            ${resolution}
                        </span>
                        <span class="meta-item">
                            <i class="bi bi-file-earmark me-1"></i>
                            ${formatFileSize(photo.file_size)}
                        </span>
                        <span class="meta-item">
                            <i class="bi bi-clock me-1"></i>
                            ${formatDateTime(photo.created_at)}
                        </span>
                    </div>
                </div>
                <div class="photo-description">
                    ${photo.analysis?.description || '暂无描述'}
                </div>
                <div class="photo-tags">
                    <div class="visible-tags">
                        ${visibleTagsHtml}
                    </div>
                    ${hiddenTagsCount > 0 ? `
                        <div class="hidden-tags" style="display: none;">
                            ${hiddenTagsHtml}
                        </div>
                        <span class="tag-toggle" onclick="toggleTags(this, event)" data-photo-id="${photo.id}">
                            +${hiddenTagsCount} 更多
                        </span>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
}

// 注意：renderPagination 已移至 app-data.js

// 注意：showPhotoDetail, createPhotoDetailModal 函数已移至 app-ui.js

// ============ 导入功能 ============

function switchImportMethod(method) {
    console.log('切换导入方式:', method);
    
    if (method === 'file') {
        elements.fileImportSection.classList.remove('d-none');
        elements.folderImportSection.classList.add('d-none');
        elements.startImportBtn.disabled = elements.photoFiles.files.length === 0;
    } else if (method === 'folder') {
        elements.fileImportSection.classList.add('d-none');
        elements.folderImportSection.classList.remove('d-none');
        elements.startImportBtn.disabled = !elements.folderPath.value.trim();
    }
}

function handleFolderPathChange() {
    const hasPath = elements.folderPath.value.trim().length > 0;
    elements.startImportBtn.disabled = !hasPath;
    
    if (hasPath) {
        elements.startImportBtn.textContent = '开始扫描导入';
    } else {
        elements.startImportBtn.textContent = '开始导入';
    }
}

function browseFolder() {
    // 触发隐藏的文件夹选择输入框
    const folderFilesInput = document.getElementById('folderFiles');
    if (folderFilesInput) {
        folderFilesInput.click();
    }
}

function handleFolderSelection(event) {
    /**
     * 处理文件夹选择事件
     * 
     * @param {Event} event - 文件选择事件
     */
    console.log('📁 文件夹选择事件触发');
    const files = event.target.files;
    console.log('选择的文件数量:', files?.length || 0);
    
    if (files && files.length > 0) {
        // 获取第一个文件的路径，去掉文件名得到文件夹路径
        const firstFile = files[0];
        const filePath = firstFile.webkitRelativePath || firstFile.name;
        const folderPath = filePath.substring(0, filePath.lastIndexOf('/'));
        
        console.log('文件夹路径:', folderPath);
        
        // 显示文件夹路径
        elements.folderPath.value = folderPath;
        
        // 显示选择的文件数量
        const imageFiles = Array.from(files).filter(file => file.type.startsWith('image/'));
        console.log(`选择了文件夹，包含 ${imageFiles.length} 个图片文件`);
        
        // 更新导入按钮状态
        handleFolderPathChange();
        
        // 显示选择结果
        showSuccess(`已选择文件夹，发现 ${imageFiles.length} 个图片文件`);
        
        // 自动开始导入
        console.log('🚀 准备自动开始文件夹导入...');
        console.log('CONFIG 对象:', window.CONFIG);
        console.log('AppState 对象:', window.AppState);
        
        // 确保导入方式设置为文件夹
        const folderRadio = document.querySelector('input[name="importMethod"][value="folder"]');
        if (folderRadio) {
            folderRadio.checked = true;
            console.log('✅ 已设置导入方式为文件夹');
        } else {
            console.error('❌ 找不到文件夹导入单选按钮');
        }
        
        setTimeout(() => {
            console.log('⏰ 延迟后开始执行文件夹导入...');
            startFolderImport();
        }, 1000); // 增加延迟时间到1秒
    } else {
        console.log('❌ 没有选择任何文件');
    }
}

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
    
    // 检查是否以驱动器字母开头（Windows）或根目录开头（Linux/Mac）
    const windowsPattern = /^[A-Za-z]:\\/;
    const unixPattern = /^\//;
    
    return windowsPattern.test(path) || unixPattern.test(path);
}

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

async function startFileImport() {
    console.log('开始文件导入');
    const files = elements.photoFiles.files;
    
    if (files.length === 0) {
        showError('请先选择要导入的照片文件');
        return;
    }
    
    // 显示进度
    elements.importProgress.classList.remove('d-none');
    elements.startImportBtn.disabled = true;
    
    try {
        const formData = new FormData();
        for (let i = 0; i < files.length; i++) {
            formData.append('files', files[i]);
        }
        
        const response = await fetch(`${CONFIG.API_BASE_URL}/import/upload`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            const importedCount = data.data.imported_photos || 0;
            const totalFiles = data.data.total_files || files.length;
            const failedFiles = data.data.failed_files || [];
            
            // 显示导入结果
            console.log('导入结果处理 - 新版本代码已加载'); // 调试信息
            if (failedFiles.length > 0) {
                // 分类显示失败文件
                const duplicateFiles = [];
                const errorFiles = [];
                
                failedFiles.forEach(f => {
                    if (f.includes('文件已存在') || f.includes('重复')) {
                        duplicateFiles.push(f);
                    } else {
                        errorFiles.push(f);
                    }
                });
                
                let message = `部分导入成功：${importedCount}/${totalFiles} 张照片`;
                
                if (duplicateFiles.length > 0) {
                    const duplicateList = duplicateFiles.map(f => `• ${f}`).join('\n');
                    message += `\n\n重复文件（已跳过）：\n${duplicateList}`;
                }
                
                if (errorFiles.length > 0) {
                    const errorList = errorFiles.map(f => `• ${f}`).join('\n');
                    message += `\n\n处理失败的文件：\n${errorList}`;
                }
                
                showWarning(message);
            } else {
                showSuccess(`成功导入 ${importedCount} 张照片！\n\n请手动点击"批量处理"按钮进行智能分析。`);
            }
            
            // 重新加载照片列表
            await loadPhotos();
            // 关闭导入模态框
            const modal = bootstrap.Modal.getInstance(elements.importModal);
            if (modal) {
                modal.hide();
            }
        } else {
            showError(data.message || '导入失败');
        }
    } catch (error) {
        console.error('文件导入失败:', error);
        showError('文件导入失败，请稍后重试');
    } finally {
        elements.importProgress.classList.add('d-none');
        elements.startImportBtn.disabled = false;
    }
}

async function startFolderImport() {
    console.log('开始目录扫描导入');
    console.log('CONFIG.API_BASE_URL:', window.CONFIG?.API_BASE_URL);
    
    // 获取选择的文件
    const folderFilesInput = document.getElementById('folderFiles');
    console.log('文件夹输入框:', folderFilesInput);
    const files = folderFilesInput.files;
    console.log('选择的文件数量:', files?.length || 0);
    
    if (!files || files.length === 0) {
        console.error('没有选择文件');
        showError('请先选择照片目录');
        return;
    }
    
    // 过滤出图片文件
    const imageFiles = Array.from(files).filter(file => file.type.startsWith('image/'));
    
    if (imageFiles.length === 0) {
        showError('选择的目录中没有找到图片文件');
        return;
    }
    
    // 显示进度
    elements.importProgress.classList.remove('d-none');
    elements.startImportBtn.disabled = true;
    elements.importStatus.textContent = `正在处理 ${imageFiles.length} 个图片文件...`;
    
    try {
        // 直接使用文件上传API处理选择的文件
        const formData = new FormData();
        imageFiles.forEach(file => {
            formData.append('files', file);
        });
        
        const apiUrl = `${window.CONFIG.API_BASE_URL}/import/upload`;
        console.log('API URL:', apiUrl);
        console.log('发送的文件数量:', imageFiles.length);
        
        const response = await fetch(apiUrl, {
            method: 'POST',
            body: formData
        });
        
        console.log('API响应状态:', response.status);
        
        const data = await response.json();
        
        if (data.success) {
            const importedCount = data.data.imported_photos || 0;
            const totalFiles = data.data.total_files || imageFiles.length;
            const failedFiles = data.data.failed_files || [];
            
            // 直接处理完成
            if (failedFiles.length > 0) {
                const failedList = failedFiles.slice(0, 10).map(f => `• ${f}`).join('\n');
                const moreText = failedFiles.length > 10 ? `\n... 还有 ${failedFiles.length - 10} 个失败文件` : '';
                showWarning(`部分导入成功：${importedCount}/${totalFiles} 张照片\n\n失败的文件：\n${failedList}${moreText}`);
            } else {
                showSuccess(`成功导入 ${importedCount} 张照片！\n\n请手动点击"批量处理"按钮进行智能分析。`);
            }
            
            // 重新加载照片列表
            await loadPhotos();
            // 关闭导入模态框
            const modal = bootstrap.Modal.getInstance(elements.importModal);
            if (modal) {
                modal.hide();
            }
        } else {
            // 根据错误类型显示不同的错误信息
            const errorMessage = data.message || '文件夹导入失败';
            showError(`文件夹导入失败：${errorMessage}`);
        }
    } catch (error) {
        console.error('文件夹导入失败:', error);
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            showError('网络连接失败，请检查服务器是否正常运行');
        } else {
            showError(`文件夹导入失败：${error.message}\n\n请稍后重试或检查网络连接`);
        }
    } finally {
        elements.importProgress.classList.add('d-none');
        elements.startImportBtn.disabled = false;
        elements.importStatus.textContent = '正在导入...';
    }
}

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
                const failed = statusData.failed_files || [];
                
                // 更新进度显示
                elements.importStatus.textContent = `正在处理... ${processed}/${totalFiles} (${progress.toFixed(1)}%)`;
                
                if (statusData.status === 'completed') {
                    clearInterval(progressInterval);
                    
                    // 处理完成
                    if (failed.length > 0) {
                        const failedList = failed.slice(0, 10).map(f => `• ${f}`).join('\n');
                        const moreText = failed.length > 10 ? `\n... 还有 ${failed.length - 10} 个失败文件` : '';
                        showWarning(`后台导入完成：成功 ${imported}/${totalFiles} 张照片\n\n失败的文件：\n${failedList}${moreText}`);
                    } else {
                        showSuccess(`后台导入完成：成功导入 ${imported} 张照片！\n\n请手动点击"批量处理"按钮进行智能分析。`);
                    }
                    
                    // 重新加载照片列表
                    await loadPhotos();
                    // 关闭导入模态框
                    const modal = bootstrap.Modal.getInstance(elements.importModal);
                    if (modal) {
                        modal.hide();
                    }
                    
                    // 隐藏进度条
                    elements.importProgress.classList.add('d-none');
                    elements.startImportBtn.disabled = false;
                    elements.importStatus.textContent = '正在导入...';
                    
                } else if (statusData.status === 'failed') {
                    clearInterval(progressInterval);
                    showError(`后台导入失败：${statusData.error || '未知错误'}`);
                    
                    // 隐藏进度条
                    elements.importProgress.classList.add('d-none');
                    elements.startImportBtn.disabled = false;
                    elements.importStatus.textContent = '正在导入...';
                }
            } else {
                console.error('获取扫描状态失败:', statusData);
            }
            
        } catch (error) {
            console.error('监控扫描进度失败:', error);
        }
        
        // 超时检查
        if (checkCount >= maxChecks) {
            clearInterval(progressInterval);
            showWarning('扫描任务超时，请检查任务状态或重新尝试');
            elements.importProgress.classList.add('d-none');
            elements.startImportBtn.disabled = false;
            elements.importStatus.textContent = '正在导入...';
        }
        
    }, 2000); // 每2秒检查一次
}

async function startBatchProcess() {
    console.log('开始批量处理');
    console.log('批量处理按钮点击事件触发');
    
    // 获取选中的处理选项
    const enableAIAnalysis = document.getElementById('enableAIAnalysis').checked;
    const enableQualityAssessment = document.getElementById('enableQualityAssessment').checked;
    const enableClassification = document.getElementById('enableClassification').checked;
    
    // 检查是否至少选择了一个选项
    if (!enableAIAnalysis && !enableQualityAssessment && !enableClassification) {
        showWarning('请至少选择一个处理选项');
        return;
    }
    
    // 显示进度
    elements.batchProgress.classList.remove('d-none');
    elements.startBatchBtn.disabled = true;
    elements.batchProgressBar.style.width = '0%';
    elements.batchStatus.textContent = '正在准备批量处理...';
    
    try {
        // 首先获取所有照片的ID
        const photosResponse = await fetch(`${CONFIG.API_BASE_URL}/photos?limit=1000`);
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
        
        const response = await fetch(`${CONFIG.API_BASE_URL}/analysis/batch-analyze`, {
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
        if (response.ok && data.total_photos > 0) {
            showSuccess(`批量处理已开始，正在处理 ${data.total_photos} 张照片`);
            
            // 保存初始总数，用于进度条计算
            const initialTotal = data.total_photos;
            
            // 使用真实的状态检查API
            let checkCount = 0;
            const maxChecks = 120; // 最多检查120次，每次1秒，总共2分钟
            
            const statusCheckInterval = setInterval(async () => {
                checkCount++;
                
                try {
                    // 调用真实的状态检查API，传递初始总数
                    const statusResponse = await fetch(`${CONFIG.API_BASE_URL}/analysis/queue/status?initial_total=${initialTotal}`);
                    const statusData = await statusResponse.json();
                    
                    console.log('处理状态:', statusData);
                    
                    // 更新进度条
                    const progress = Math.min(statusData.progress_percentage || 0, 95);
                    elements.batchProgressBar.style.width = `${progress}%`;
                    elements.batchStatus.textContent = `正在处理... ${Math.round(progress)}% (${statusData.batch_completed_photos}/${statusData.batch_total_photos})`;
                    
                    // 检查是否完成
                    if (statusData.is_complete || statusData.processing_photos === 0) {
                        clearInterval(statusCheckInterval);
                        elements.batchProgressBar.style.width = '100%';
                        elements.batchStatus.textContent = '批量处理完成！';
                        showSuccess('批量处理完成！');
                        
                        // 重置按钮状态
                        elements.startBatchBtn.disabled = false;
                        
                        // 等待2秒确保数据库事务完成，然后刷新照片列表
                        setTimeout(async () => {
                            console.log('重新加载照片列表...');
                            await loadPhotos();
                            console.log('照片列表重新加载完成');
                            // 关闭模态框
                            const modal = bootstrap.Modal.getInstance(elements.batchModal);
                            modal.hide();
                        }, 2000);
                        return;
                    }
                    
                    // 超时保护
                    if (checkCount >= maxChecks) {
                        clearInterval(statusCheckInterval);
                        elements.batchProgressBar.style.width = '100%';
                        elements.batchStatus.textContent = '批量处理完成！';
                        showSuccess('批量处理完成！');
                        
                        // 重置按钮状态
                        elements.startBatchBtn.disabled = false;
                        
                        // 等待3秒确保数据库事务完成，然后刷新照片列表
                        setTimeout(async () => {
                            console.log('重新加载照片列表...');
                            await loadPhotos();
                            console.log('照片列表重新加载完成');
                            // 关闭模态框
                            const modal = bootstrap.Modal.getInstance(elements.batchModal);
                            modal.hide();
                        }, 3000);
                    }
                    
                } catch (error) {
                    console.error('检查处理状态失败:', error);
                    // 如果API调用失败，继续等待
                }
            }, 1000); // 每1秒检查一次
            
        } else {
            // 检查是否是因为没有需要处理的照片
            if (data.total_photos === 0) {
                showSuccess('所有照片都已完成智能处理，无需重复处理！');
            } else {
                showError(data.detail || data.message || '批量处理启动失败');
            }
            // 重置按钮状态
            elements.startBatchBtn.disabled = false;
            elements.batchProgress.classList.add('d-none');
        }
    } catch (error) {
        console.error('批量处理失败:', error);
        showError('批量处理失败，请稍后重试');
        // 重置按钮状态
        elements.startBatchBtn.disabled = false;
        elements.batchProgress.classList.add('d-none');
    } finally {
        // 注意：成功时按钮状态在进度完成后重置
    }
}

function selectAllPhotos() {
    console.log('全选照片');
    if (window.PhotoManager) {
        window.PhotoManager.selectAllPhotos();
    } else {
        console.error('PhotoManager 未初始化');
        showError('照片管理器未初始化，请刷新页面重试');
    }
}

function clearSelection() {
    console.log('取消选择');
    if (window.PhotoManager) {
        window.PhotoManager.clearSelection();
    } else {
        console.error('PhotoManager 未初始化');
        showError('照片管理器未初始化，请刷新页面重试');
    }
}

function deleteSelectedPhotos() {
    console.log('删除选中照片');
    if (window.PhotoManager) {
        const selectedIds = window.PhotoManager.getSelectedPhotoIds();
        if (selectedIds.length > 0) {
            window.PhotoManager.deletePhotos(selectedIds);
        } else {
            showWarning('请先选择要删除的照片');
        }
    } else {
        console.error('PhotoManager 未初始化');
        showError('照片管理器未初始化，请刷新页面重试');
    }
}


function switchSection(section) {
    console.log('📄 切换到页面:', section);
    
    // 更新导航状态
    updateNavigation(section);
    
    // 根据页面显示不同内容
    switch(section) {
        case 'photos':
            showPhotosSection();
            break;
        default:
            showPhotosSection();
    }
}

function updateNavigation(activeSection) {
    // 移除所有导航项的激活状态
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    
    // 激活当前导航项
    const activeLink = document.querySelector(`[data-section="${activeSection}"]`);
    if (activeLink) {
        activeLink.classList.add('active');
    }
}

function showPhotosSection() {
    // 显示照片网格区域
    const mainContent = document.querySelector('.row:has(.col-md-9)');
    if (mainContent) {
        mainContent.style.display = 'block';
    }
    
    // 加载照片数据
    loadPhotos();
}


// 注意：toggleTags 函数已移至 app-ui.js

// ============ 全局导出 ============

window.PhotoApp = {
    loadPhotos,
    loadStats,
    showError
};

window.toggleTags = toggleTags;
window.selectSuggestion = selectSuggestion;
