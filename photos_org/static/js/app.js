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
const elements = {};

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
    elements.dateFilter.addEventListener('change', handleFilterChange);
    elements.qualityFilter.addEventListener('change', handleFilterChange);
    elements.sortBy.addEventListener('change', handleSortChange);

    // 视图切换事件
    elements.gridView.addEventListener('change', () => switchView('grid'));
    elements.listView.addEventListener('change', () => switchView('list'));

    // 导入事件
    elements.importBtn.addEventListener('click', showImportModal);
    elements.importFirstBtn.addEventListener('click', showImportModal);
    elements.photoFiles.addEventListener('change', handleFileSelection);
    elements.startImportBtn.addEventListener('click', startImport);

    // 批量处理事件
    elements.batchBtn.addEventListener('click', showBatchModal);
    elements.startBatchBtn.addEventListener('click', startBatchProcess);

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
    window.modals.importModal.show();
}

function showBatchModal() {
    window.modals.batchModal.show();
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
            AppState.photos = data.data || [];
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
        <div class="col-md-3">
            <div class="stats-card">
                <div class="stats-icon">
                    <i class="bi bi-images"></i>
                </div>
                <div class="stats-value">${stats.total_photos || 0}</div>
                <div class="stats-label">总照片数</div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="stats-card">
                <div class="stats-icon">
                    <i class="bi bi-tags"></i>
                </div>
                <div class="stats-value">${stats.total_tags || 0}</div>
                <div class="stats-label">标签数量</div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="stats-card">
                <div class="stats-icon">
                    <i class="bi bi-collection"></i>
                </div>
                <div class="stats-value">${stats.total_categories || 0}</div>
                <div class="stats-label">分类数量</div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="stats-card">
                <div class="stats-icon">
                    <i class="bi bi-star"></i>
                </div>
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
    const qualityLevel = photo.quality?.quality_rating || photo.analysis?.quality_rating || '';
    const qualityClass = getQualityClass(qualityLevel);
    const qualityText = getQualityText(qualityLevel);

    return `
        <div class="col photo-card" data-photo-id="${photo.id}">
            <img src="${photo.thumbnail_path || CONFIG.IMAGE_PLACEHOLDER}"
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
            <img src="${photo.thumbnail_path || CONFIG.IMAGE_PLACEHOLDER}"
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
    const texts = {
        'excellent': '优秀',
        'good': '良好',
        'average': '一般',
        'poor': '较差',
        'bad': '很差'
    };
    return texts[level] || '一般';
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

function startImport() {
    console.log('开始导入照片');
    // TODO: 实现照片导入功能
}

function startBatchProcess() {
    console.log('开始批量处理');
    // TODO: 实现批量处理功能
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
    console.log('切换到:', section);
    // TODO: 实现页面切换功能
}

// ============ 全局导出 ============

window.PhotoApp = {
    loadPhotos,
    loadStats,
    showError
};
