

/**
 * 家庭版智能照片系统 - 主应用脚本
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
    console.log('🚀 初始化家庭版智能照片系统');

    // 缓存DOM元素
    cacheElements();

    // 绑定事件监听器
    bindEvents();

    // 初始化UI组件
    initializeUI();
    
    // 热门数据加载已移除，因为相关配置已从用户界面移除

    // 初始化搜索式多选组件
    initSearchMultiSelect();

    // 加载初始数据
    loadInitialData();

    // 设置定期刷新
    setupAutoRefresh();
    
    // 确保搜索框placeholder正确设置
    setTimeout(() => {
        if (elements.searchInput && searchTypePlaceholders) {
            elements.searchInput.placeholder = searchTypePlaceholders['all'] || '搜索照片、文件名、描述...';
        }
        
        // 初始化搜索语法提示
        const searchSyntax = document.getElementById('searchSyntax');
        if (searchSyntax && elements.searchType) {
            if (elements.searchType.value === 'all') {
                searchSyntax.style.display = 'block';
            } else {
                searchSyntax.style.display = 'none';
            }
        }
        
        // 初始化搜索范围提示（隐藏）
        if (elements.searchScopeHint) {
            elements.searchScopeHint.style.display = 'none';
        }
        
        // 初始化搜索框tooltip（只在全部内容时显示）
        if (elements.searchInput && elements.searchType) {
            if (elements.searchType.value === 'all') {
                elements.searchInput.title = '支持关键词搜索、精确搜索、前缀搜索等';
            } else {
                elements.searchInput.title = '';
            }
        }
    }, 100);
}

function cacheElements() {
    console.log('📋 缓存DOM元素');

    elements = {
        // 导航
        navPhotos: document.getElementById('navPhotos'),

        // 操作按钮
        importBtn: document.getElementById('importBtn'),

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
        formatFilter: document.getElementById('formatFilter'),
        cameraFilter: document.getElementById('cameraFilter'),
        advancedFilterMode: document.getElementById('advancedFilterMode'),
        advancedFilterOptions: document.getElementById('advancedFilterOptions'),
        sortBy: document.getElementById('sortBy'),
        sortOrder: document.getElementById('sortOrder'),
        clearFiltersSmall: document.getElementById('clearFiltersSmall'),
        filterStatus: document.getElementById('filterStatus'),
        filterStatusText: document.getElementById('filterStatusText'),

        // 视图切换
        gridView: document.getElementById('gridView'),
        listView: document.getElementById('listView'),

        // 统计信息
        statsRow: document.getElementById('statsRow'),
        photoCount: document.getElementById('photoCount'),

        // 照片区域
        loadingIndicator: document.getElementById('loadingIndicator'),
        emptyState: document.getElementById('emptyState'),
        photosGrid: document.getElementById('photosGrid'),
        paginationContainer: document.getElementById('paginationContainer'),
        pagination: document.getElementById('pagination'),

        // 选择操作
        selectAllBtn: document.getElementById('selectAllBtn'),
        clearSelectionBtn: document.getElementById('clearSelectionBtn'),
        aiProcessSelectedBtn: document.getElementById('aiProcessSelectedBtn'),
        deleteSelectedBtn: document.getElementById('deleteSelectedBtn'),

        // 模态框
        photoModal: document.getElementById('photoModal'),
        importModal: document.getElementById('importModal'),

        // 导入相关
        photoFiles: document.getElementById('photoFiles'),
        // startImportBtn: document.getElementById('startImportBtn'), // 已删除按钮
        importFirstBtn: document.getElementById('importFirstBtn'),
        importProgress: document.getElementById('importProgress'),
        importProgressBar: document.getElementById('importProgressBar'),
        importStatus: document.getElementById('importStatus'),
        importDetails: document.getElementById('importDetails'),
        importStats: document.getElementById('importStats'),
        processedCount: document.getElementById('processedCount'),
        importedCount: document.getElementById('importedCount'),
        skippedCount: document.getElementById('skippedCount'),
        failedCount: document.getElementById('failedCount'),
        
        // 导入方式切换
        fileImport: document.getElementById('fileImport'),
        folderImport: document.getElementById('folderImport'),
        fileImportSection: document.getElementById('fileImportSection'),
        folderImportSection: document.getElementById('folderImportSection'),
        folderPath: document.getElementById('folderPath'),
        browseFolderBtn: document.getElementById('browseFolderBtn'),
        recursiveScan: document.getElementById('recursiveScan'),

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
    // 基础筛选模式切换
    elements.advancedFilterMode.addEventListener('change', () => {
        switchAdvancedFilterMode(elements.advancedFilterMode.value);
    });

    // 初始化基础筛选模式（默认日期筛选）
    switchAdvancedFilterMode('date');
    elements.sortBy.addEventListener('change', handleSortChange);
    elements.sortOrder.addEventListener('change', handleSortChange);
    elements.startDate.addEventListener('change', handleCustomDateChange);
    elements.endDate.addEventListener('change', handleCustomDateChange);
    elements.clearFiltersSmall.addEventListener('click', clearAllFilters);

    // 收藏筛选按钮事件
    if (typeof bindFavoriteFilterEvent === 'function') {
        bindFavoriteFilterEvent();
    }

    // 视图切换事件
    elements.gridView.addEventListener('change', () => switchView('grid'));
    elements.listView.addEventListener('change', () => switchView('list'));

    // 照片编辑模态框事件
    const savePhotoEditBtn = document.getElementById('savePhotoEdit');
    if (savePhotoEditBtn) {
        savePhotoEditBtn.addEventListener('click', savePhotoEdit);
    }
    
    // 添加标签按钮事件
    const addTagBtn = document.getElementById('addTagBtn');
    if (addTagBtn) {
        addTagBtn.addEventListener('click', () => {
            const tagInput = document.getElementById('editPhotoTags');
            const tagName = tagInput.value.trim();
            if (tagName) {
                addTag(tagName);
                tagInput.value = '';
            }
        });
    }
    
    // 标签输入框回车事件
    const tagInput = document.getElementById('editPhotoTags');
    if (tagInput) {
        tagInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                const tagName = tagInput.value.trim();
                if (tagName) {
                    addTag(tagName);
                    tagInput.value = '';
                }
            }
        });
    }
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

// 注意：createPhotoListItem 函数已移至 app-photos.js

// 注意：renderPagination 已移至 app-data.js

// 注意：showPhotoDetail, createPhotoDetailModal 函数已移至 app-ui.js

// ============ 导入功能 ============

// 注意：所有导入相关函数已移至 app-import.js


// 注意：startFolderImport 函数已移至 app-import.js



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
