

/**
 * 家庭单机版智能照片整理系统 - 主应用脚本
 */

// 全局配置
const CONFIG = {
    API_BASE_URL: '/api/v1',
    PAGE_SIZE: 50,
    DEBOUNCE_DELAY: 300,
    IMAGE_PLACEHOLDER: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgdmlld0JveD0iMCAwIDIwMCAyMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIyMDAiIGhlaWdodD0iMjAwIiBmaWxsPSIjRjNGNEY2Ii8+CjxwYXRoIGQ9Ik0xMDAgMTAwSDE0MEwxMjAgMTIwSDEwMFYxNDBIMTZWMTAwWiIgZmlsbD0iIzk3OTdhNyIvPgo8L3N2Zz4K'
};

// 全局状态管理
const AppState = {
    currentPage: 1,
    totalPages: 1,
    currentView: 'grid', // 'grid' or 'list'
    selectedPhotos: new Set(),
    isLoading: false,
    searchFilters: {
        keyword: '',
        dateFilter: '',
        qualityFilter: '',
        sortBy: 'taken_at',
        sortOrder: 'desc'
    },
    photos: [],
    stats: {}
};

// DOM 元素缓存
let elements = {};

// 初始化应用
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    console.log('🚀 初始化家庭单机版智能照片整理系统');

    // 缓存DOM元素
    cacheElements();

    // 绑定事件监听器
    bindEvents();

    // 初始化UI组件
    initializeUI();

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
        navAlbums: document.getElementById('navAlbums'),
        navSearch: document.getElementById('navSearch'),
        navSettings: document.getElementById('navSettings'),

        // 操作按钮
        importBtn: document.getElementById('importBtn'),
        batchBtn: document.getElementById('batchBtn'),

        // 搜索和筛选
        searchInput: document.getElementById('searchInput'),
        searchBtn: document.getElementById('searchBtn'),
        dateFilter: document.getElementById('dateFilter'),
        qualityFilter: document.getElementById('qualityFilter'),
        sortBy: document.getElementById('sortBy'),

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

    elements.navAlbums.addEventListener('click', (e) => {
        e.preventDefault();
        switchSection('albums');
    });

    elements.navSearch.addEventListener('click', (e) => {
        e.preventDefault();
        switchSection('search');
    });

    elements.navSettings.addEventListener('click', (e) => {
        e.preventDefault();
        switchSection('settings');
    });

    // 搜索事件
    elements.searchInput.addEventListener('input', debounce(handleSearch, CONFIG.DEBOUNCE_DELAY));
    elements.searchBtn.addEventListener('click', handleSearch);
    elements.dateFilter.addEventListener('change', handleFilterChange);
    elements.qualityFilter.addEventListener('change', handleFilterChange);
    elements.sortBy.addEventListener('change', handleSortChange);

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

function initializeUI() {
    console.log('🎨 初始化UI组件');

    // 初始化Bootstrap模态框
    const photoModal = new bootstrap.Modal(elements.photoModal);
    const importModal = new bootstrap.Modal(elements.importModal);
    const batchModal = new bootstrap.Modal(elements.batchModal);

    // 存储在全局对象中
    window.modals = {
        photoModal,
        importModal,
        batchModal
    };

    // 添加全局关闭函数
    window.closeModal = function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            console.log('🔒 全局关闭模态框:', modalId);
            
            // 使用Bootstrap API关闭模态框
            const modalInstance = bootstrap.Modal.getInstance(modal);
            if (modalInstance) {
                modalInstance.hide();
            } else {
                // 如果Bootstrap实例不存在，创建一个新的
                const newModalInstance = new bootstrap.Modal(modal);
                newModalInstance.hide();
            }
        }
    };

    // 添加调试信息
    console.log('📱 模态框初始化完成:', {
        photoModal: !!photoModal,
        importModal: !!importModal,
        batchModal: !!batchModal
    });

    // 添加测试函数
    window.testModalClose = function() {
        console.log('🧪 测试模态框关闭功能');
        const modals = ['importModal', 'batchModal', 'photoModal'];
        modals.forEach(modalId => {
            const modal = document.getElementById(modalId);
            if (modal) {
                console.log(`模态框 ${modalId} 存在:`, modal);
                const closeButtons = modal.querySelectorAll('[data-bs-dismiss="modal"]');
                console.log(`关闭按钮数量:`, closeButtons.length);
            }
        });
    };

    // 添加紧急清理函数
    window.forceCleanup = function() {
        console.log('🚨 强制清理页面状态');
        
        // 关闭所有模态框
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            modal.classList.remove('show');
            modal.style.display = 'none';
            modal.setAttribute('aria-hidden', 'true');
            modal.removeAttribute('aria-modal');
        });
        
        // 移除所有遮罩层
        const backdrops = document.querySelectorAll('.modal-backdrop');
        backdrops.forEach(backdrop => backdrop.remove());
        
        // 恢复body状态
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
        
        console.log('✅ 强制清理完成');
    };

    // 监听模态框事件并确保正确清理
    document.addEventListener('show.bs.modal', function(e) {
        console.log('📱 模态框显示:', e.target.id);
    });
    
    document.addEventListener('hide.bs.modal', function(e) {
        console.log('📱 模态框隐藏:', e.target.id);
        
        // 确保清理所有可能的遮罩层
        setTimeout(() => {
            const backdrops = document.querySelectorAll('.modal-backdrop');
            backdrops.forEach(backdrop => backdrop.remove());
            
            // 确保body恢复正常状态
            document.body.classList.remove('modal-open');
            document.body.style.overflow = '';
            document.body.style.paddingRight = '';
            
            console.log('🧹 清理完成，页面应该可以正常点击了');
        }, 100);
    });
    
    // 页面加载时检查并清理遮罩层
    function checkAndCleanupOverlay() {
        const backdrops = document.querySelectorAll('.modal-backdrop');
        if (backdrops.length > 0) {
            console.log('发现残留遮罩层，正在清理...');
            window.forceCleanup();
        }
    }

    // 页面加载完成后检查
    document.addEventListener('DOMContentLoaded', checkAndCleanupOverlay);
    
    // 页面完全加载后再次检查
    window.addEventListener('load', checkAndCleanupOverlay);

    // 监听模态框完全隐藏后的事件
    document.addEventListener('hidden.bs.modal', function(e) {
        console.log('📱 模态框完全隐藏:', e.target.id);
        
        // 再次确保清理
        const backdrops = document.querySelectorAll('.modal-backdrop');
        backdrops.forEach(backdrop => backdrop.remove());
        
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
    });

    // 初始化工具提示
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

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

// ============ 事件处理函数 ============

function handleSearch() {
    const keyword = elements.searchInput.value.trim();
    AppState.searchFilters.keyword = keyword;
    AppState.currentPage = 1;
    loadPhotos(1);
}

function handleFilterChange() {
    AppState.searchFilters.dateFilter = elements.dateFilter.value;
    AppState.searchFilters.qualityFilter = elements.qualityFilter.value;
    AppState.currentPage = 1;
    loadPhotos(1);
}

function handleSortChange() {
    AppState.searchFilters.sortBy = elements.sortBy.value;
    AppState.currentPage = 1;
    loadPhotos(1);
}

function switchView(viewType) {
    AppState.currentView = viewType;
    renderPhotos();
}

function showImportModal() {
    // 使用Bootstrap API显示模态窗口
    const modal = new bootstrap.Modal(elements.importModal);
    modal.show();
}

function showBatchModal() {
    // 使用Bootstrap API显示模态窗口
    const modal = new bootstrap.Modal(elements.batchModal);
    modal.show();
}

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

// ============ 数据加载函数 ============

async function loadStats() {
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/search/stats`);
        const data = await response.json();

        if (data.success) {
            AppState.stats = data.data;
            renderStats();
        }
    } catch (error) {
        console.error('加载统计信息失败:', error);
        showError('加载统计信息失败，请稍后重试');
    }
}

async function loadPhotos(page = 1) {
    try {
        setLoading(true);

        const params = new URLSearchParams({
            offset: (page - 1) * CONFIG.PAGE_SIZE,
            limit: CONFIG.PAGE_SIZE,
            sort_by: AppState.searchFilters.sortBy,
            sort_order: AppState.searchFilters.sortOrder,
            keyword: AppState.searchFilters.keyword,
            date_filter: AppState.searchFilters.dateFilter,
            quality_filter: AppState.searchFilters.qualityFilter
        });

        const response = await fetch(`${CONFIG.API_BASE_URL}/search/photos?${params}`);
        const data = await response.json();

        if (data.success) {
            // 兼容两种数据格式：data.data 和 data.photos
            AppState.photos = data.data || data.photos || [];
            AppState.currentPage = page;
            AppState.totalPages = Math.ceil((data.total || 0) / CONFIG.PAGE_SIZE);

            renderPhotos();
            renderPagination();
            updatePhotoCount(data.total || 0);
        } else {
            showError(data.error || '加载照片失败');
        }
    } catch (error) {
        console.error('加载照片失败:', error);
        showError('加载照片失败，请检查网络连接');
    } finally {
        setLoading(false);
    }
}

// ============ 渲染函数 ============

function renderStats() {
    const stats = AppState.stats;
    const statsHtml = `
        <div class="d-flex align-items-center mb-2">
            <div class="stats-icon me-2">
                <i class="bi bi-images text-primary"></i>
            </div>
            <div class="flex-grow-1">
                <div class="stats-value">${stats.total_photos || 0}</div>
                <div class="stats-label">总照片数</div>
            </div>
        </div>
        <div class="d-flex align-items-center mb-2">
            <div class="stats-icon me-2">
                <i class="bi bi-tags text-success"></i>
            </div>
            <div class="flex-grow-1">
                <div class="stats-value">${stats.total_tags || 0}</div>
                <div class="stats-label">标签数量</div>
            </div>
        </div>
        <div class="d-flex align-items-center mb-2">
            <div class="stats-icon me-2">
                <i class="bi bi-collection text-info"></i>
            </div>
            <div class="flex-grow-1">
                <div class="stats-value">${stats.total_categories || 0}</div>
                <div class="stats-label">分类数量</div>
            </div>
        </div>
        <div class="d-flex align-items-center">
            <div class="stats-icon me-2">
                <i class="bi bi-star text-warning"></i>
            </div>
            <div class="flex-grow-1">
                <div class="stats-value">${Object.keys(stats.quality_distribution || {}).length}</div>
                <div class="stats-label">质量等级</div>
            </div>
        </div>
    `;

    elements.statsRow.innerHTML = statsHtml;
}

function renderPhotos() {
    const photos = AppState.photos;

    if (photos.length === 0) {
        showEmptyState();
        return;
    }

    hideEmptyState();

    if (AppState.currentView === 'grid') {
        renderGridView(photos);
    } else {
        renderListView(photos);
    }
}

function renderGridView(photos) {
    const html = photos.map(photo => createPhotoCard(photo)).join('');
    elements.photosGrid.innerHTML = html;

    // 为每个照片卡片绑定事件
    photos.forEach((photo, index) => {
        const card = elements.photosGrid.children[index];
        card.addEventListener('click', () => showPhotoDetail(photo));
    });
}

function renderListView(photos) {
    const html = photos.map(photo => createPhotoListItem(photo)).join('');
    elements.photosGrid.innerHTML = html;
}

function createPhotoCard(photo) {
    const tagsHtml = (photo.tags || []).map(tag =>
        `<span class="photo-tag">${tag}</span>`
    ).join('');

    // 获取质量信息
    const qualityLevel = photo.quality?.level || photo.analysis?.quality_rating || '';
    const qualityClass = getQualityClass(qualityLevel);
    const qualityText = getQualityText(qualityLevel);

    return `
        <div class="col photo-card" data-photo-id="${photo.id}">
            <img src="/${(photo.thumbnail_path || CONFIG.IMAGE_PLACEHOLDER).replace(/\\/g, '/')}"
                 alt="${photo.filename}"
                 class="photo-image"
                 loading="lazy">
            <div class="photo-overlay">
                <i class="bi bi-eye text-white" style="font-size: 2rem;"></i>
            </div>
            <div class="photo-info">
                <div class="photo-title">${photo.filename}</div>
                <div class="photo-meta">
                    <i class="bi bi-calendar me-1"></i>${formatDate(photo.created_at)}
                </div>
                <div class="photo-tags">
                    ${tagsHtml}
                </div>
                <div class="photo-quality ${qualityClass}">
                    ${qualityText}
                </div>
            </div>
        </div>
    `;
}

function createPhotoListItem(photo) {
    const tagsHtml = (photo.tags || []).slice(0, 3).map(tag =>
        `<span class="badge bg-secondary me-1">${tag}</span>`
    ).join('');

    const qualityClass = getQualityClass(photo.quality?.level || '');
    const qualityText = getQualityText(photo.quality?.level || '');

    return `
        <div class="photo-list-item" data-photo-id="${photo.id}">
            <img src="/${(photo.thumbnail_path || CONFIG.IMAGE_PLACEHOLDER).replace(/\\/g, '/')}"
                 alt="${photo.filename}"
                 class="photo-thumbnail">
            <div class="photo-details">
                <div class="photo-title">${photo.filename}</div>
                <div class="photo-meta">
                    <i class="bi bi-calendar me-1"></i>${formatDate(photo.taken_at)}
                    <i class="bi bi-geo-alt me-1 ms-3"></i>${photo.location_name || '未知位置'}
                </div>
                <div class="photo-description">
                    ${photo.analysis?.description || '暂无描述'}
                </div>
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        ${tagsHtml}
                    </div>
                    <span class="badge ${qualityClass}">${qualityText}</span>
                </div>
            </div>
        </div>
    `;
}

function renderPagination() {
    if (AppState.totalPages <= 1) {
        elements.paginationContainer.classList.add('d-none');
        return;
    }

    elements.paginationContainer.classList.remove('d-none');

    let html = '';

    // 上一页
    if (AppState.currentPage > 1) {
        html += `<li class="page-item">
            <a class="page-link" href="#" data-page="${AppState.currentPage - 1}">上一页</a>
        </li>`;
    }

    // 页码
    const startPage = Math.max(1, AppState.currentPage - 2);
    const endPage = Math.min(AppState.totalPages, AppState.currentPage + 2);

    for (let i = startPage; i <= endPage; i++) {
        const activeClass = i === AppState.currentPage ? 'active' : '';
        html += `<li class="page-item ${activeClass}">
            <a class="page-link" href="#" data-page="${i}">${i}</a>
        </li>`;
    }

    // 下一页
    if (AppState.currentPage < AppState.totalPages) {
        html += `<li class="page-item">
            <a class="page-link" href="#" data-page="${AppState.currentPage + 1}">下一页</a>
        </li>`;
    }

    elements.pagination.innerHTML = html;

    // 绑定分页事件
    elements.pagination.querySelectorAll('.page-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = parseInt(e.target.dataset.page);
            loadPhotos(page);
        });
    });
}

// ============ 工具函数 ============

function setLoading(loading) {
    AppState.isLoading = loading;

    if (loading) {
        elements.loadingIndicator.classList.remove('d-none');
        elements.photosGrid.classList.add('d-none');
    } else {
        elements.loadingIndicator.classList.add('d-none');
        elements.photosGrid.classList.remove('d-none');
    }
}

function showEmptyState() {
    elements.emptyState.classList.remove('d-none');
    elements.photosGrid.innerHTML = '';
}

function hideEmptyState() {
    elements.emptyState.classList.add('d-none');
}

function updatePhotoCount(count) {
    elements.photoCount.textContent = count;
}

function formatDate(dateString) {
    if (!dateString) return '未知日期';

    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('zh-CN');
    } catch (e) {
        return dateString;
    }
}

function getQualityClass(level) {
    const classes = {
        'excellent': 'excellent',
        'good': 'good',
        'average': 'average',
        'poor': 'poor',
        'bad': 'bad'
    };
    return classes[level] || 'average';
}

function getQualityText(level) {
    // 修复编码问题：将乱码转换为正确的中文
    const fixEncoding = (str) => {
        if (!str) return '一般';
        
        // 检查是否是乱码
        if (str.includes('浼樼') || str.includes('')) {
            return '优秀';
        }
        if (str.includes('良好') || str.includes('')) {
            return '良好';
        }
        if (str.includes('一般') || str.includes('')) {
            return '一般';
        }
        if (str.includes('较差') || str.includes('')) {
            return '较差';
        }
        if (str.includes('很差') || str.includes('')) {
            return '很差';
        }
        
        return str;
    };
    
    // 修复编码
    const fixedLevel = fixEncoding(level);
    
    // 如果已经是正确的中文，直接返回
    if (['优秀', '良好', '一般', '较差', '很差'].includes(fixedLevel)) {
        return fixedLevel;
    }
    
    // 如果是英文，转换为中文
    const texts = {
        'excellent': '优秀',
        'good': '良好',
        'average': '一般',
        'fair': '一般',
        'poor': '较差',
        'bad': '很差'
    };
    return texts[fixedLevel] || '一般';
}

function debounce(func, delay) {
    let timeoutId;
    return function(...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
}

function showError(message) {
    // 使用Bootstrap的toast组件显示错误信息
    const toastHtml = `
        <div class="toast align-items-center text-white bg-danger border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;

    const toastContainer = document.querySelector('.toast-container') || createToastContainer();
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);

    const toast = new bootstrap.Toast(toastContainer.lastElementChild);
    toast.show();
}

function showSuccess(message) {
    // 使用Bootstrap的toast组件显示成功信息
    const toastHtml = `
        <div class="toast align-items-center text-white bg-success border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="bi bi-check-circle me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;

    const toastContainer = document.querySelector('.toast-container') || createToastContainer();
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);

    const toast = new bootstrap.Toast(toastContainer.lastElementChild);
    toast.show();
}

function showWarning(message) {
    // 使用Bootstrap的toast组件显示警告信息
    const toastHtml = `
        <div class="toast align-items-center text-white bg-warning border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;

    const toastContainer = document.querySelector('.toast-container') || createToastContainer();
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);

    const toast = new bootstrap.Toast(toastContainer.lastElementChild);
    toast.show();
}

function createToastContainer() {
    const container = document.createElement('div');
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}

// ============ 待实现的功能 ============

function showPhotoDetail(photo) {
    console.log('显示照片详情:', photo);
    // TODO: 实现照片详情显示
}

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
    const files = event.target.files;
    
    if (files && files.length > 0) {
        // 获取第一个文件的路径，去掉文件名得到文件夹路径
        const firstFile = files[0];
        const filePath = firstFile.webkitRelativePath || firstFile.name;
        const folderPath = filePath.substring(0, filePath.lastIndexOf('/'));
        
        // 显示文件夹路径
        elements.folderPath.value = folderPath;
        
        // 显示选择的文件数量
        const imageFiles = Array.from(files).filter(file => file.type.startsWith('image/'));
        console.log(`选择了文件夹，包含 ${imageFiles.length} 个图片文件`);
        
        // 更新导入按钮状态
        handleFolderPathChange();
        
        // 显示选择结果
        showInfo(`已选择文件夹，发现 ${imageFiles.length} 个图片文件`);
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
    const importMethod = document.querySelector('input[name="importMethod"]:checked').value;
    
    if (importMethod === 'file') {
        await startFileImport();
    } else if (importMethod === 'folder') {
        await startFolderImport();
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
    
    // 获取选择的文件
    const folderFilesInput = document.getElementById('folderFiles');
    const files = folderFilesInput.files;
    
    if (!files || files.length === 0) {
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
        
        const response = await fetch(`${CONFIG.API_BASE_URL}/import/upload`, {
            method: 'POST',
            body: formData
        });
        
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
    // TODO: 实现全选功能
}

function clearSelection() {
    console.log('取消选择');
    // TODO: 实现取消选择功能
}

function deleteSelectedPhotos() {
    console.log('删除选中照片');
    // TODO: 实现删除功能
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
        case 'albums':
            showAlbumsSection();
            break;
        case 'search':
            showSearchSection();
            break;
        case 'settings':
            showSettingsSection();
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

function showAlbumsSection() {
    // 创建相册页面内容
    const mainContent = document.querySelector('.row:has(.col-md-9)');
    if (mainContent) {
        mainContent.innerHTML = `
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0">
                            <i class="bi bi-collection me-2"></i>
                            相册管理
                        </h5>
                    </div>
                    <div class="card-body text-center py-5">
                        <i class="bi bi-collection text-muted" style="font-size: 3rem;"></i>
                        <h4 class="mt-3 text-muted">相册功能开发中</h4>
                        <p class="text-muted">相册管理功能正在开发中，敬请期待...</p>
                    </div>
                </div>
            </div>
        `;
    }
}

function showSearchSection() {
    // 创建搜索页面内容
    const mainContent = document.querySelector('.row:has(.col-md-9)');
    if (mainContent) {
        mainContent.innerHTML = `
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0">
                            <i class="bi bi-search me-2"></i>
                            高级搜索
                        </h5>
                    </div>
                    <div class="card-body">
                        <div class="row g-3">
                            <div class="col-md-6">
                                <label class="form-label">关键词搜索</label>
                                <input type="text" class="form-control" placeholder="输入搜索关键词...">
                            </div>
                            <div class="col-md-3">
                                <label class="form-label">拍摄日期</label>
                                <input type="date" class="form-control">
                            </div>
                            <div class="col-md-3">
                                <label class="form-label">质量等级</label>
                                <select class="form-select">
                                    <option value="">全部质量</option>
                                    <option value="excellent">优秀</option>
                                    <option value="good">良好</option>
                                    <option value="fair">一般</option>
                                    <option value="poor">较差</option>
                                </select>
                            </div>
                        </div>
                        <div class="mt-3">
                            <button class="btn btn-primary">
                                <i class="bi bi-search me-1"></i>
                                开始搜索
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
}

function showSettingsSection() {
    // 创建设置页面内容
    const mainContent = document.querySelector('.row:has(.col-md-9)');
    if (mainContent) {
        mainContent.innerHTML = `
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0">
                            <i class="bi bi-gear me-2"></i>
                            系统设置
                        </h5>
                    </div>
                    <div class="card-body">
                        <div class="row g-3">
                            <div class="col-md-6">
                                <label class="form-label">存储路径</label>
                                <input type="text" class="form-control" value="photos_storage" readonly>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label">缩略图大小</label>
                                <select class="form-select">
                                    <option value="small">小 (150px)</option>
                                    <option value="medium" selected>中 (200px)</option>
                                    <option value="large">大 (300px)</option>
                                </select>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label">AI分析开关</label>
                                <div class="form-check form-switch">
                                    <input class="form-check-input" type="checkbox" checked>
                                    <label class="form-check-label">启用AI内容分析</label>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label">质量评估</label>
                                <div class="form-check form-switch">
                                    <input class="form-check-input" type="checkbox" checked>
                                    <label class="form-check-label">启用质量评估</label>
                                </div>
                            </div>
                        </div>
                        <div class="mt-4">
                            <button class="btn btn-primary me-2">
                                <i class="bi bi-save me-1"></i>
                                保存设置
                            </button>
                            <button class="btn btn-outline-secondary">
                                <i class="bi bi-arrow-clockwise me-1"></i>
                                重置设置
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
}

// ============ 全局导出 ============

window.PhotoApp = {
    loadPhotos,
    loadStats,
    showError
};
