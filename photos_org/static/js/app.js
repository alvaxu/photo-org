

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

    // 确保 elements 对象在全局作用域中可用
    window.elements = elements;

    // 绑定基础事件（导航、导入、选择操作等）
    bindBasicEvents();

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

// 注意：handleFileSelection 函数已移至 app-events.js

// 注意：handleKeyboard 函数已移至 app-events.js

// 注意：数据加载函数 loadStats, loadPhotos 已移至 app-data.js

// 注意：渲染函数已移至 app-data.js

// 注意：renderPhotos, renderGridView, renderListView 已移至 app-data.js

// 注意：createPhotoCard 函数已移至 app-photos.js

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

// 注意：所有导入相关函数已移至 app-import.js

// ============ 批量处理功能 ============

// 注意：startBatchProcess 函数已移至 app-import.js

// 注意：startFolderImport 函数已移至 app-import.js

// 注意：monitorScanProgress 函数已移至 app-import.js

// 注意：startBatchProcess 函数已移至 app-import.js

// 注意：selectAllPhotos, clearSelection, deleteSelectedPhotos 函数已移至 app-photos.js
// 注意：switchSection, updateNavigation, showPhotosSection 函数已移至 app-photos.js


// 注意：toggleTags 函数已移至 app-ui.js

// ============ 全局导出 ============

window.PhotoApp = {
    loadPhotos,
    loadStats,
    showError
};

window.toggleTags = toggleTags;
window.selectSuggestion = selectSuggestion;
