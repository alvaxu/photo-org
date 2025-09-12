/**
 * 高级搜索页面主逻辑
 */

// 搜索状态管理
const SearchState = {
    // 当前搜索条件
    currentFilters: {
        keyword: '',
        searchType: 'all',
        startDate: '',
        endDate: '',
        qualityMin: 0,
        cameraMake: '',
        tagFilter: '',
        categoryFilter: '',
        sortBy: 'taken_at',
        sortOrder: 'desc'
    },
    
    // 分页信息
    pagination: {
        currentPage: 1,
        pageSize: 12,  // 改为12张照片每页
        total: 0,
        totalPages: 0
    },
    
    // 选中的照片
    selectedPhotos: new Set(),
    
    // 搜索结果
    searchResults: [],
    
    // 加载状态
    isLoading: false
};

// DOM元素引用
const elements = {
    // 搜索表单
    advancedSearchForm: document.getElementById('advancedSearchForm'),
    keywordInput: document.getElementById('keywordInput'),
    searchType: document.getElementById('searchType'),
    startDate: document.getElementById('startDate'),
    endDate: document.getElementById('endDate'),
    qualityRange: document.getElementById('qualityRange'),
    qualityValue: document.getElementById('qualityValue'),
    cameraMake: document.getElementById('cameraMake'),
    tagFilter: document.getElementById('tagFilter'),
    categoryFilter: document.getElementById('categoryFilter'),
    
    // 搜索按钮
    resetSearch: document.getElementById('resetSearch'),
    
    // 排序
    sortBy: document.getElementById('sortBy'),
    sortOrder: document.getElementById('sortOrder'),
    
    // 结果展示
    searchResults: document.getElementById('searchResults'),
    searchResultsCount: document.getElementById('searchResultsCount'),
    loadingSpinner: document.getElementById('loadingSpinner'),
    emptyState: document.getElementById('emptyState'),
    paginationNav: document.getElementById('paginationNav'),
    pagination: document.getElementById('pagination'),
    
    // 批量操作
    batchToolbar: document.getElementById('batchToolbar'),
    selectedCount: document.getElementById('selectedCount'),
    selectAllBtn: document.getElementById('selectAllBtn'),
    clearSelectionBtn: document.getElementById('clearSelectionBtn'),
    batchDeleteBtn: document.getElementById('batchDeleteBtn'),
    batchEditBtn: document.getElementById('batchEditBtn'),
    batchTagBtn: document.getElementById('batchTagBtn'),
    batchCategoryBtn: document.getElementById('batchCategoryBtn'),
    
    // 搜索历史
    searchHistory: document.getElementById('searchHistory'),
    clearHistory: document.getElementById('clearHistory'),
    
    // 模态框
    photoModal: document.getElementById('photoModal'),
    photoModalTitle: document.getElementById('photoModalTitle'),
    photoModalImage: document.getElementById('photoModalImage'),
    photoModalInfo: document.getElementById('photoModalInfo')
};

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeSearchPage();
    bindEventListeners();
    loadSearchHistory();
});

/**
 * 初始化搜索页面
 */
function initializeSearchPage() {
    console.log('初始化高级搜索页面');
    
    // 设置默认值
    elements.qualityValue.textContent = elements.qualityRange.value;
    
    // 从URL参数加载搜索条件
    loadSearchConditionsFromURL();
    
    // 执行初始搜索
    performSearch();
}

/**
 * 绑定事件监听器
 */
function bindEventListeners() {
    // 搜索表单提交
    elements.advancedSearchForm.addEventListener('submit', function(e) {
        e.preventDefault();
        updateSearchFilters();
        performSearch();
    });
    
    // 重置搜索
    elements.resetSearch.addEventListener('click', function() {
        resetSearchFilters();
        performSearch();
    });
    
    // 质量滑块
    elements.qualityRange.addEventListener('input', function() {
        elements.qualityValue.textContent = this.value;
    });
    
    // 排序变化
    elements.sortBy.addEventListener('change', function() {
        SearchState.currentFilters.sortBy = this.value;
        performSearch();
    });
    
    elements.sortOrder.addEventListener('change', function() {
        SearchState.currentFilters.sortOrder = this.value;
        performSearch();
    });
    
    // 批量操作
    elements.selectAllBtn.addEventListener('click', function() {
        selectAllPhotos();
    });
    
    elements.clearSelectionBtn.addEventListener('click', function() {
        clearSelection();
    });
    
    elements.batchDeleteBtn.addEventListener('click', function() {
        batchDeletePhotos();
    });
    
    elements.batchEditBtn.addEventListener('click', function() {
        batchEditPhotos();
    });
    
    elements.batchTagBtn.addEventListener('click', function() {
        batchTagPhotos();
    });
    
    elements.batchCategoryBtn.addEventListener('click', function() {
        batchCategoryPhotos();
    });
    
    // 搜索历史
    elements.clearHistory.addEventListener('click', function() {
        clearSearchHistory();
    });
}

/**
 * 更新搜索条件
 */
function updateSearchFilters() {
    SearchState.currentFilters = {
        keyword: elements.keywordInput.value.trim(),
        searchType: elements.searchType.value,
        startDate: elements.startDate.value,
        endDate: elements.endDate.value,
        qualityMin: parseInt(elements.qualityRange.value),
        cameraMake: elements.cameraMake.value,
        tagFilter: elements.tagFilter.value.trim(),
        categoryFilter: elements.categoryFilter.value.trim(),
        sortBy: elements.sortBy.value,
        sortOrder: elements.sortOrder.value
    };
    
    // 保存到搜索历史
    saveToSearchHistory();
}

/**
 * 重置搜索条件
 */
function resetSearchFilters() {
    elements.keywordInput.value = '';
    elements.searchType.value = 'all';
    elements.startDate.value = '';
    elements.endDate.value = '';
    elements.qualityRange.value = '0';
    elements.qualityValue.textContent = '0';
    elements.cameraMake.value = '';
    elements.tagFilter.value = '';
    elements.categoryFilter.value = '';
    elements.sortBy.value = 'taken_at';
    elements.sortOrder.value = 'desc';
    
    SearchState.currentFilters = {
        keyword: '',
        searchType: 'all',
        startDate: '',
        endDate: '',
        qualityMin: 0,
        cameraMake: '',
        tagFilter: '',
        categoryFilter: '',
        sortBy: 'taken_at',
        sortOrder: 'desc'
    };
}

/**
 * 执行搜索
 */
async function performSearch(page = 1) {
    if (SearchState.isLoading) return;
    
    SearchState.isLoading = true;
    SearchState.pagination.currentPage = page;
    
    showLoadingState();
    
    try {
        // 构建搜索参数
        const searchParams = buildSearchParams(page);
        
        // 调用搜索API
        const response = await fetch(`/api/v1/search/photos?${searchParams}`);
        
        if (!response.ok) {
            throw new Error(`搜索失败: ${response.status}`);
        }
        
        const data = await response.json();
        
        // 调试信息
        console.log('搜索API响应:', data);
        console.log('照片数据:', data.data);
        console.log('总数:', data.total);
        
        // 更新搜索结果
        SearchState.searchResults = data.data || [];
        SearchState.pagination.total = data.total || 0;
        SearchState.pagination.totalPages = Math.ceil(SearchState.pagination.total / SearchState.pagination.pageSize);
        
        // 渲染结果
        renderSearchResults();
        renderPagination();
        updateResultsCount();
        
    } catch (error) {
        console.error('搜索错误:', error);
        showErrorState('搜索失败，请重试');
    } finally {
        SearchState.isLoading = false;
        hideLoadingState();
    }
}

/**
 * 构建搜索参数
 */
function buildSearchParams(page) {
    const params = new URLSearchParams();
    
    // 分页参数
    params.append('offset', ((page - 1) * SearchState.pagination.pageSize).toString());
    params.append('limit', SearchState.pagination.pageSize.toString());
    
    // 搜索条件
    const filters = SearchState.currentFilters;
    
    if (filters.keyword) {
        params.append('keyword', filters.keyword);
        params.append('search_type', filters.searchType);
    }
    
    if (filters.startDate) {
        params.append('start_date', filters.startDate);
    }
    
    if (filters.endDate) {
        params.append('end_date', filters.endDate);
    }
    
    if (filters.qualityMin > 0) {
        params.append('quality_min', filters.qualityMin.toString());
    }
    
    if (filters.cameraMake) {
        params.append('camera_make', filters.cameraMake);
    }
    
    if (filters.tagFilter) {
        params.append('tags', filters.tagFilter);
    }
    
    if (filters.categoryFilter) {
        params.append('categories', filters.categoryFilter);
    }
    
    // 排序
    params.append('sort_by', filters.sortBy);
    params.append('sort_order', filters.sortOrder);
    
    return params.toString();
}

/**
 * 渲染搜索结果
 */
function renderSearchResults() {
    const resultsContainer = elements.searchResults;
    
    console.log('渲染搜索结果，照片数量:', SearchState.searchResults.length);
    console.log('搜索结果:', SearchState.searchResults);
    
    if (SearchState.searchResults.length === 0) {
        showEmptyState();
        return;
    }
    
    hideEmptyState();
    
    // 清空现有结果
    resultsContainer.innerHTML = '';
    
    // 渲染每个搜索结果
    SearchState.searchResults.forEach(photo => {
        const photoElement = createPhotoElement(photo);
        resultsContainer.appendChild(photoElement);
    });
}

/**
 * 创建照片元素
 */
function createPhotoElement(photo) {
    const col = document.createElement('div');
    col.className = 'col-md-2 col-6';  // 每行6张照片（12/2=6）
    
    const isSelected = SearchState.selectedPhotos.has(photo.id);
    
    col.innerHTML = `
        <div class="search-result-item ${isSelected ? 'selected' : ''}" data-photo-id="${photo.id}">
            <div class="result-checkbox">
                <input type="checkbox" class="photo-checkbox" data-photo-id="${photo.id}" ${isSelected ? 'checked' : ''}>
            </div>
            <div class="result-image-container">
                <img src="/${(photo.thumbnail_path || '/static/images/placeholder.jpg').replace(/\\/g, '/')}" 
                     alt="${photo.filename}" 
                     class="result-image"
                     loading="lazy">
                <div class="result-overlay">
                    <button class="btn btn-light btn-sm" onclick="viewPhoto(${photo.id})" title="查看详情">
                        <i class="bi bi-eye"></i>
                    </button>
                    <button class="btn btn-warning btn-sm" onclick="editPhoto(${photo.id})" title="编辑">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-danger btn-sm" onclick="deletePhoto(${photo.id})" title="删除">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </div>
            <div class="result-info">
                <div class="result-title" title="${photo.filename}">${photo.filename}</div>
                <div class="result-meta">
                    <span>${formatDate(photo.taken_at || photo.created_at)}</span>
                    ${photo.quality_score ? `<span class="quality-score quality-${getQualityClass(photo.quality_level)}">${photo.quality_score}分</span>` : ''}
                </div>
                <div class="result-tags">
                    ${(photo.tags || []).slice(0, 3).map(tag => `<span class="tag">${tag}</span>`).join('')}
                    ${(photo.tags || []).length > 3 ? `<span class="tag">+${(photo.tags || []).length - 3}</span>` : ''}
                </div>
            </div>
        </div>
    `;
    
    // 绑定选择事件
    const checkbox = col.querySelector('.photo-checkbox');
    checkbox.addEventListener('change', function() {
        togglePhotoSelection(photo.id, this.checked);
    });
    
    // 绑定点击选择事件
    col.addEventListener('click', function(e) {
        if (e.target.type !== 'checkbox' && !e.target.closest('.result-overlay')) {
            const checkbox = this.querySelector('.photo-checkbox');
            checkbox.checked = !checkbox.checked;
            togglePhotoSelection(photo.id, checkbox.checked);
        }
    });
    
    return col;
}

/**
 * 渲染分页控件
 */
function renderPagination() {
    const pagination = elements.pagination;
    const { currentPage, totalPages } = SearchState.pagination;
    
    if (totalPages <= 1) {
        elements.paginationNav.style.display = 'none';
        return;
    }
    
    elements.paginationNav.style.display = 'block';
    pagination.innerHTML = '';
    
    // 上一页按钮
    const prevLi = document.createElement('li');
    prevLi.className = `page-item ${currentPage === 1 ? 'disabled' : ''}`;
    prevLi.innerHTML = `<a class="page-link" href="#" data-page="${currentPage - 1}">上一页</a>`;
    pagination.appendChild(prevLi);
    
    // 页码按钮
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);
    
    for (let i = startPage; i <= endPage; i++) {
        const li = document.createElement('li');
        li.className = `page-item ${i === currentPage ? 'active' : ''}`;
        li.innerHTML = `<a class="page-link" href="#" data-page="${i}">${i}</a>`;
        pagination.appendChild(li);
    }
    
    // 下一页按钮
    const nextLi = document.createElement('li');
    nextLi.className = `page-item ${currentPage === totalPages ? 'disabled' : ''}`;
    nextLi.innerHTML = `<a class="page-link" href="#" data-page="${currentPage + 1}">下一页</a>`;
    pagination.appendChild(nextLi);
    
    // 绑定分页事件
    pagination.addEventListener('click', function(e) {
        e.preventDefault();
        if (e.target.classList.contains('page-link')) {
            const page = parseInt(e.target.dataset.page);
            if (page && page !== currentPage && page >= 1 && page <= totalPages) {
                performSearch(page);
            }
        }
    });
}

/**
 * 显示加载状态
 */
function showLoadingState() {
    elements.loadingSpinner.style.display = 'block';
    elements.searchResults.style.display = 'none';
    elements.emptyState.style.display = 'none';
    elements.paginationNav.style.display = 'none';
}

/**
 * 隐藏加载状态
 */
function hideLoadingState() {
    elements.loadingSpinner.style.display = 'none';
    elements.searchResults.style.display = 'block';
}

/**
 * 显示空状态
 */
function showEmptyState() {
    elements.emptyState.style.display = 'block';
    elements.searchResults.style.display = 'none';
    elements.paginationNav.style.display = 'none';
}

/**
 * 隐藏空状态
 */
function hideEmptyState() {
    elements.emptyState.style.display = 'none';
}

/**
 * 显示错误状态
 */
function showErrorState(message) {
    elements.emptyState.querySelector('h5').textContent = '搜索出错';
    elements.emptyState.querySelector('p').textContent = message;
    showEmptyState();
}

/**
 * 更新结果计数
 */
function updateResultsCount() {
    const { total, currentPage, pageSize } = SearchState.pagination;
    const start = (currentPage - 1) * pageSize + 1;
    const end = Math.min(currentPage * pageSize, total);
    
    elements.searchResultsCount.textContent = `找到 ${total} 张照片 (显示 ${start}-${end})`;
}

/**
 * 切换照片选择状态
 */
function togglePhotoSelection(photoId, selected) {
    if (selected) {
        SearchState.selectedPhotos.add(photoId);
    } else {
        SearchState.selectedPhotos.delete(photoId);
    }
    
    updateBatchToolbar();
    updatePhotoSelectionUI(photoId, selected);
}

/**
 * 更新照片选择UI
 */
function updatePhotoSelectionUI(photoId, selected) {
    const photoElement = document.querySelector(`[data-photo-id="${photoId}"]`);
    if (photoElement) {
        if (selected) {
            photoElement.classList.add('selected');
        } else {
            photoElement.classList.remove('selected');
        }
    }
}

/**
 * 全选照片
 */
function selectAllPhotos() {
    SearchState.searchResults.forEach(photo => {
        SearchState.selectedPhotos.add(photo.id);
    });
    
    // 更新UI
    document.querySelectorAll('.photo-checkbox').forEach(checkbox => {
        checkbox.checked = true;
    });
    
    document.querySelectorAll('.search-result-item').forEach(item => {
        item.classList.add('selected');
    });
    
    updateBatchToolbar();
}

/**
 * 取消选择
 */
function clearSelection() {
    SearchState.selectedPhotos.clear();
    
    // 更新UI
    document.querySelectorAll('.photo-checkbox').forEach(checkbox => {
        checkbox.checked = false;
    });
    
    document.querySelectorAll('.search-result-item').forEach(item => {
        item.classList.remove('selected');
    });
    
    updateBatchToolbar();
}

/**
 * 更新批量操作工具栏
 */
function updateBatchToolbar() {
    const selectedCount = SearchState.selectedPhotos.size;
    
    if (selectedCount > 0) {
        elements.batchToolbar.style.display = 'block';
        elements.selectedCount.textContent = `已选择 ${selectedCount} 张照片`;
        elements.batchDeleteBtn.disabled = false;
        elements.batchEditBtn.disabled = false;
        elements.batchTagBtn.disabled = false;
        elements.batchCategoryBtn.disabled = false;
    } else {
        elements.batchToolbar.style.display = 'none';
        elements.batchDeleteBtn.disabled = true;
        elements.batchEditBtn.disabled = true;
        elements.batchTagBtn.disabled = true;
        elements.batchCategoryBtn.disabled = true;
    }
}

/**
 * 批量删除照片
 */
async function batchDeletePhotos() {
    const selectedIds = Array.from(SearchState.selectedPhotos);
    
    if (selectedIds.length === 0) {
        alert('请先选择要删除的照片');
        return;
    }
    
    if (!confirm(`确定要删除选中的 ${selectedIds.length} 张照片吗？此操作不可撤销。`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/v1/photos/batch-delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                photo_ids: selectedIds,
                delete_files: true
            })
        });
        
        if (!response.ok) {
            throw new Error('批量删除失败');
        }
        
        const result = await response.json();
        console.log('批量删除结果:', result);
        
        // 清空选择
        clearSelection();
        
        // 重新搜索
        performSearch(SearchState.pagination.currentPage);
        
        alert(`成功删除 ${result.successful_deletions} 张照片`);
        
    } catch (error) {
        console.error('批量删除错误:', error);
        alert('批量删除失败，请重试');
    }
}

/**
 * 批量编辑照片
 */
function batchEditPhotos() {
    const selectedIds = Array.from(SearchState.selectedPhotos);
    
    if (selectedIds.length === 0) {
        alert('请先选择要编辑的照片');
        return;
    }
    
    // TODO: 实现批量编辑功能
    alert('批量编辑功能开发中...');
}

/**
 * 批量标签照片
 */
function batchTagPhotos() {
    const selectedIds = Array.from(SearchState.selectedPhotos);
    
    if (selectedIds.length === 0) {
        alert('请先选择要添加标签的照片');
        return;
    }
    
    // TODO: 实现批量标签功能
    alert('批量标签功能开发中...');
}

/**
 * 批量分类照片
 */
function batchCategoryPhotos() {
    const selectedIds = Array.from(SearchState.selectedPhotos);
    
    if (selectedIds.length === 0) {
        alert('请先选择要分类的照片');
        return;
    }
    
    // TODO: 实现批量分类功能
    alert('批量分类功能开发中...');
}

/**
 * 查看照片详情
 */
function viewPhoto(photoId) {
    // TODO: 实现照片详情查看
    console.log('查看照片详情:', photoId);
}

/**
 * 编辑照片
 */
function editPhoto(photoId) {
    // TODO: 实现照片编辑
    console.log('编辑照片:', photoId);
}

/**
 * 删除照片
 */
async function deletePhoto(photoId) {
    if (!confirm('确定要删除这张照片吗？此操作不可撤销。')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/v1/photos/${photoId}?delete_file=true`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('删除失败');
        }
        
        // 从选择中移除
        SearchState.selectedPhotos.delete(photoId);
        
        // 重新搜索
        performSearch(SearchState.pagination.currentPage);
        
        alert('照片删除成功');
        
    } catch (error) {
        console.error('删除错误:', error);
        alert('删除失败，请重试');
    }
}

/**
 * 从URL加载搜索条件
 */
function loadSearchConditionsFromURL() {
    const urlParams = new URLSearchParams(window.location.search);
    
    if (urlParams.has('keyword')) {
        elements.keywordInput.value = urlParams.get('keyword');
    }
    
    if (urlParams.has('search_type')) {
        elements.searchType.value = urlParams.get('search_type');
    }
    
    if (urlParams.has('start_date')) {
        elements.startDate.value = urlParams.get('start_date');
    }
    
    if (urlParams.has('end_date')) {
        elements.endDate.value = urlParams.get('end_date');
    }
    
    if (urlParams.has('quality_min')) {
        const qualityMin = parseInt(urlParams.get('quality_min'));
        elements.qualityRange.value = qualityMin;
        elements.qualityValue.textContent = qualityMin;
    }
    
    if (urlParams.has('camera_make')) {
        elements.cameraMake.value = urlParams.get('camera_make');
    }
    
    if (urlParams.has('tags')) {
        elements.tagFilter.value = urlParams.get('tags');
    }
    
    if (urlParams.has('categories')) {
        elements.categoryFilter.value = urlParams.get('categories');
    }
    
    if (urlParams.has('sort_by')) {
        elements.sortBy.value = urlParams.get('sort_by');
    }
    
    if (urlParams.has('sort_order')) {
        elements.sortOrder.value = urlParams.get('sort_order');
    }
    
    // 更新搜索状态
    updateSearchFilters();
}

/**
 * 保存到搜索历史
 */
function saveToSearchHistory() {
    const history = getSearchHistory();
    const searchCondition = {
        id: Date.now(),
        filters: { ...SearchState.currentFilters },
        timestamp: new Date().toISOString()
    };
    
    // 添加到历史记录开头
    history.unshift(searchCondition);
    
    // 限制历史记录数量
    if (history.length > 20) {
        history.splice(20);
    }
    
    localStorage.setItem('searchHistory', JSON.stringify(history));
    renderSearchHistory();
}

/**
 * 获取搜索历史
 */
function getSearchHistory() {
    const history = localStorage.getItem('searchHistory');
    return history ? JSON.parse(history) : [];
}

/**
 * 加载搜索历史
 */
function loadSearchHistory() {
    renderSearchHistory();
}

/**
 * 渲染搜索历史
 */
function renderSearchHistory() {
    const history = getSearchHistory();
    const historyContainer = elements.searchHistory;
    
    if (history.length === 0) {
        historyContainer.innerHTML = '<p class="text-muted text-center">暂无搜索历史</p>';
        return;
    }
    
    historyContainer.innerHTML = history.map(item => `
        <div class="history-item" data-history-id="${item.id}">
            <div class="history-query">${item.filters.keyword || '无关键词'}</div>
            <div class="history-time">${formatDateTime(item.timestamp)}</div>
            <div class="history-actions">
                <button class="btn btn-sm btn-outline-primary" onclick="applySearchHistory(${item.id})">搜索</button>
                <button class="btn btn-sm btn-outline-secondary" onclick="removeSearchHistory(${item.id})">删除</button>
            </div>
        </div>
    `).join('');
}

/**
 * 应用搜索历史
 */
function applySearchHistory(historyId) {
    const history = getSearchHistory();
    const historyItem = history.find(item => item.id === historyId);
    
    if (historyItem) {
        // 应用搜索条件
        const filters = historyItem.filters;
        elements.keywordInput.value = filters.keyword || '';
        elements.searchType.value = filters.searchType || 'all';
        elements.startDate.value = filters.startDate || '';
        elements.endDate.value = filters.endDate || '';
        elements.qualityRange.value = filters.qualityMin || 0;
        elements.qualityValue.textContent = filters.qualityMin || 0;
        elements.cameraMake.value = filters.cameraMake || '';
        elements.tagFilter.value = filters.tagFilter || '';
        elements.categoryFilter.value = filters.categoryFilter || '';
        elements.sortBy.value = filters.sortBy || 'taken_at';
        elements.sortOrder.value = filters.sortOrder || 'desc';
        
        // 更新搜索状态并执行搜索
        updateSearchFilters();
        performSearch();
    }
}

/**
 * 删除搜索历史
 */
function removeSearchHistory(historyId) {
    const history = getSearchHistory();
    const filteredHistory = history.filter(item => item.id !== historyId);
    localStorage.setItem('searchHistory', JSON.stringify(filteredHistory));
    renderSearchHistory();
}

/**
 * 清空搜索历史
 */
function clearSearchHistory() {
    if (confirm('确定要清空所有搜索历史吗？')) {
        localStorage.removeItem('searchHistory');
        renderSearchHistory();
    }
}

/**
 * 工具函数
 */

function formatDate(dateString) {
    if (!dateString) return '未知';
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN');
}

function formatDateTime(dateString) {
    if (!dateString) return '未知';
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
}

function getQualityClass(qualityLevel) {
    const qualityMap = {
        '优秀': 'excellent',
        '良好': 'good',
        '一般': 'fair',
        '较差': 'poor'
    };
    return qualityMap[qualityLevel] || 'fair';
}
