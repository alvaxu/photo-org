/**
 * 高级搜索功能
 */

// 高级搜索状态
const AdvancedSearchState = {
    // 保存的搜索条件
    savedSearches: [],
    
    // 当前搜索条件名称
    currentSearchName: '',
    
    // 高级搜索面板状态
    isAdvancedPanelOpen: false
};

/**
 * 初始化高级搜索功能
 */
document.addEventListener('DOMContentLoaded', function() {
    initializeAdvancedSearch();
    loadSavedSearches();
});

/**
 * 初始化高级搜索
 */
function initializeAdvancedSearch() {
    console.log('初始化高级搜索功能');
    
    // 添加高级搜索面板切换按钮
    addAdvancedSearchToggle();
    
    // 添加保存搜索条件功能
    addSaveSearchFunctionality();
    
    // 添加搜索建议功能
    addSearchSuggestions();
}

/**
 * 添加高级搜索面板切换按钮
 */
function addAdvancedSearchToggle() {
    const searchForm = document.getElementById('advancedSearchForm');
    const toggleButton = document.createElement('button');
    toggleButton.type = 'button';
    toggleButton.className = 'btn btn-outline-info btn-sm mt-2';
    toggleButton.innerHTML = '<i class="bi bi-gear"></i> 高级选项';
    toggleButton.onclick = toggleAdvancedPanel;
    
    searchForm.appendChild(toggleButton);
    
    // 创建高级搜索面板
    createAdvancedPanel();
}

/**
 * 创建高级搜索面板
 */
function createAdvancedPanel() {
    const searchForm = document.getElementById('advancedSearchForm');
    
    const advancedPanel = document.createElement('div');
    advancedPanel.id = 'advancedSearchPanel';
    advancedPanel.className = 'advanced-search-panel mt-3';
    advancedPanel.style.display = 'none';
    
    advancedPanel.innerHTML = `
        <div class="card">
            <div class="card-header">
                <h6 class="mb-0">
                    <i class="bi bi-gear me-1"></i>
                    高级搜索选项
                </h6>
            </div>
            <div class="card-body">
                <div class="row g-3">
                    <!-- 文件大小范围 -->
                    <div class="col-md-6">
                        <label class="form-label">文件大小 (MB)</label>
                        <div class="row g-2">
                            <div class="col-6">
                                <input type="number" class="form-control form-control-sm" id="minFileSize" placeholder="最小">
                            </div>
                            <div class="col-6">
                                <input type="number" class="form-control form-control-sm" id="maxFileSize" placeholder="最大">
                            </div>
                        </div>
                    </div>
                    
                    <!-- 图片尺寸 -->
                    <div class="col-md-6">
                        <label class="form-label">图片尺寸</label>
                        <select class="form-select form-select-sm" id="imageSize">
                            <option value="">任意尺寸</option>
                            <option value="4k">4K (3840x2160+)</option>
                            <option value="1080p">1080p (1920x1080+)</option>
                            <option value="720p">720p (1280x720+)</option>
                            <option value="small">小尺寸 (< 1280x720)</option>
                        </select>
                    </div>
                    
                    <!-- 拍摄模式 -->
                    <div class="col-md-6">
                        <label class="form-label">拍摄模式</label>
                        <select class="form-select form-select-sm" id="exposureMode">
                            <option value="">任意模式</option>
                            <option value="auto">自动</option>
                            <option value="manual">手动</option>
                            <option value="aperture">光圈优先</option>
                            <option value="shutter">快门优先</option>
                        </select>
                    </div>
                    
                    <!-- 闪光灯 -->
                    <div class="col-md-6">
                        <label class="form-label">闪光灯</label>
                        <select class="form-select form-select-sm" id="flashMode">
                            <option value="">任意</option>
                            <option value="on">开启</option>
                            <option value="off">关闭</option>
                            <option value="auto">自动</option>
                        </select>
                    </div>
                    
                    <!-- 白平衡 -->
                    <div class="col-md-6">
                        <label class="form-label">白平衡</label>
                        <select class="form-select form-select-sm" id="whiteBalance">
                            <option value="">任意</option>
                            <option value="auto">自动</option>
                            <option value="daylight">日光</option>
                            <option value="cloudy">阴天</option>
                            <option value="tungsten">钨丝灯</option>
                            <option value="fluorescent">荧光灯</option>
                        </select>
                    </div>
                    
                    <!-- ISO范围 -->
                    <div class="col-md-6">
                        <label class="form-label">ISO范围</label>
                        <div class="row g-2">
                            <div class="col-6">
                                <input type="number" class="form-control form-control-sm" id="minISO" placeholder="最小">
                            </div>
                            <div class="col-6">
                                <input type="number" class="form-control form-control-sm" id="maxISO" placeholder="最大">
                            </div>
                        </div>
                    </div>
                    
                    <!-- 光圈范围 -->
                    <div class="col-md-6">
                        <label class="form-label">光圈范围 (f/)</label>
                        <div class="row g-2">
                            <div class="col-6">
                                <input type="number" class="form-control form-control-sm" id="minAperture" placeholder="最小" step="0.1">
                            </div>
                            <div class="col-6">
                                <input type="number" class="form-control form-control-sm" id="maxAperture" placeholder="最大" step="0.1">
                            </div>
                        </div>
                    </div>
                    
                    <!-- 快门速度范围 -->
                    <div class="col-md-6">
                        <label class="form-label">快门速度 (秒)</label>
                        <div class="row g-2">
                            <div class="col-6">
                                <input type="number" class="form-control form-control-sm" id="minShutterSpeed" placeholder="最小" step="0.001">
                            </div>
                            <div class="col-6">
                                <input type="number" class="form-control form-control-sm" id="maxShutterSpeed" placeholder="最大" step="0.001">
                            </div>
                        </div>
                    </div>
                    
                    <!-- 焦距范围 -->
                    <div class="col-md-6">
                        <label class="form-label">焦距 (mm)</label>
                        <div class="row g-2">
                            <div class="col-6">
                                <input type="number" class="form-control form-control-sm" id="minFocalLength" placeholder="最小">
                            </div>
                            <div class="col-6">
                                <input type="number" class="form-control form-control-sm" id="maxFocalLength" placeholder="最大">
                            </div>
                        </div>
                    </div>
                    
                    <!-- 位置信息 -->
                    <div class="col-md-6">
                        <label class="form-label">位置信息</label>
                        <select class="form-select form-select-sm" id="hasLocation">
                            <option value="">任意</option>
                            <option value="true">有位置信息</option>
                            <option value="false">无位置信息</option>
                        </select>
                    </div>
                    
                    <!-- 人物数量 -->
                    <div class="col-md-6">
                        <label class="form-label">人物数量</label>
                        <select class="form-select form-select-sm" id="peopleCount">
                            <option value="">任意</option>
                            <option value="0">无人</option>
                            <option value="1">单人</option>
                            <option value="2">双人</option>
                            <option value="3+">多人 (3+)</option>
                        </select>
                    </div>
                    
                    <!-- 场景类型 -->
                    <div class="col-md-6">
                        <label class="form-label">场景类型</label>
                        <select class="form-select form-select-sm" id="sceneType">
                            <option value="">任意场景</option>
                            <option value="室内">室内</option>
                            <option value="室外">室外</option>
                            <option value="夜景">夜景</option>
                            <option value="风景">风景</option>
                            <option value="人像">人像</option>
                            <option value="建筑">建筑</option>
                            <option value="动物">动物</option>
                        </select>
                    </div>
                    
                    <!-- 情感分析 -->
                    <div class="col-md-6">
                        <label class="form-label">情感分析</label>
                        <select class="form-select form-select-sm" id="emotion">
                            <option value="">任意情感</option>
                            <option value="欢乐">欢乐</option>
                            <option value="平静">平静</option>
                            <option value="兴奋">兴奋</option>
                            <option value="忧郁">忧郁</option>
                            <option value="愤怒">愤怒</option>
                        </select>
                    </div>
                </div>
                
                <div class="mt-3 d-flex gap-2">
                    <button type="button" class="btn btn-primary btn-sm" onclick="applyAdvancedSearch()">
                        <i class="bi bi-search"></i> 应用高级搜索
                    </button>
                    <button type="button" class="btn btn-outline-secondary btn-sm" onclick="resetAdvancedSearch()">
                        <i class="bi bi-arrow-clockwise"></i> 重置
                    </button>
                </div>
            </div>
        </div>
    `;
    
    searchForm.appendChild(advancedPanel);
}

/**
 * 切换高级搜索面板
 */
function toggleAdvancedPanel() {
    const panel = document.getElementById('advancedSearchPanel');
    const button = event.target;
    
    if (panel.style.display === 'none') {
        panel.style.display = 'block';
        button.innerHTML = '<i class="bi bi-gear-fill"></i> 隐藏高级选项';
        AdvancedSearchState.isAdvancedPanelOpen = true;
    } else {
        panel.style.display = 'none';
        button.innerHTML = '<i class="bi bi-gear"></i> 高级选项';
        AdvancedSearchState.isAdvancedPanelOpen = false;
    }
}

/**
 * 应用高级搜索
 */
function applyAdvancedSearch() {
    // 获取高级搜索条件
    const advancedFilters = getAdvancedSearchFilters();
    
    // 合并到当前搜索条件
    Object.assign(SearchState.currentFilters, advancedFilters);
    
    // 执行搜索
    performSearch();
}

/**
 * 获取高级搜索条件
 */
function getAdvancedSearchFilters() {
    const filters = {};
    
    // 文件大小
    const minFileSize = document.getElementById('minFileSize').value;
    const maxFileSize = document.getElementById('maxFileSize').value;
    if (minFileSize) filters.minFileSize = parseInt(minFileSize) * 1024 * 1024; // 转换为字节
    if (maxFileSize) filters.maxFileSize = parseInt(maxFileSize) * 1024 * 1024;
    
    // 图片尺寸
    const imageSize = document.getElementById('imageSize').value;
    if (imageSize) {
        const sizeMap = {
            '4k': { minWidth: 3840, minHeight: 2160 },
            '1080p': { minWidth: 1920, minHeight: 1080 },
            '720p': { minWidth: 1280, minHeight: 720 },
            'small': { maxWidth: 1280, maxHeight: 720 }
        };
        Object.assign(filters, sizeMap[imageSize]);
    }
    
    // 拍摄模式
    const exposureMode = document.getElementById('exposureMode').value;
    if (exposureMode) filters.exposureMode = exposureMode;
    
    // 闪光灯
    const flashMode = document.getElementById('flashMode').value;
    if (flashMode) filters.flash = flashMode;
    
    // 白平衡
    const whiteBalance = document.getElementById('whiteBalance').value;
    if (whiteBalance) filters.whiteBalance = whiteBalance;
    
    // ISO范围
    const minISO = document.getElementById('minISO').value;
    const maxISO = document.getElementById('maxISO').value;
    if (minISO) filters.minISO = parseInt(minISO);
    if (maxISO) filters.maxISO = parseInt(maxISO);
    
    // 光圈范围
    const minAperture = document.getElementById('minAperture').value;
    const maxAperture = document.getElementById('maxAperture').value;
    if (minAperture) filters.minAperture = parseFloat(minAperture);
    if (maxAperture) filters.maxAperture = parseFloat(maxAperture);
    
    // 快门速度范围
    const minShutterSpeed = document.getElementById('minShutterSpeed').value;
    const maxShutterSpeed = document.getElementById('maxShutterSpeed').value;
    if (minShutterSpeed) filters.minShutterSpeed = parseFloat(minShutterSpeed);
    if (maxShutterSpeed) filters.maxShutterSpeed = parseFloat(maxShutterSpeed);
    
    // 焦距范围
    const minFocalLength = document.getElementById('minFocalLength').value;
    const maxFocalLength = document.getElementById('maxFocalLength').value;
    if (minFocalLength) filters.minFocalLength = parseInt(minFocalLength);
    if (maxFocalLength) filters.maxFocalLength = parseInt(maxFocalLength);
    
    // 位置信息
    const hasLocation = document.getElementById('hasLocation').value;
    if (hasLocation) filters.hasLocation = hasLocation === 'true';
    
    // 人物数量
    const peopleCount = document.getElementById('peopleCount').value;
    if (peopleCount) {
        if (peopleCount === '3+') {
            filters.minPeopleCount = 3;
        } else {
            const count = parseInt(peopleCount);
            filters.minPeopleCount = count;
            filters.maxPeopleCount = count;
        }
    }
    
    // 场景类型
    const sceneType = document.getElementById('sceneType').value;
    if (sceneType) filters.sceneType = sceneType;
    
    // 情感分析
    const emotion = document.getElementById('emotion').value;
    if (emotion) filters.emotion = emotion;
    
    return filters;
}

/**
 * 重置高级搜索
 */
function resetAdvancedSearch() {
    const advancedPanel = document.getElementById('advancedSearchPanel');
    const inputs = advancedPanel.querySelectorAll('input, select');
    
    inputs.forEach(input => {
        if (input.type === 'number' || input.type === 'text') {
            input.value = '';
        } else if (input.tagName === 'SELECT') {
            input.selectedIndex = 0;
        }
    });
}

/**
 * 添加保存搜索条件功能
 */
function addSaveSearchFunctionality() {
    const searchForm = document.getElementById('advancedSearchForm');
    
    // 添加保存搜索条件按钮
    const saveButton = document.createElement('button');
    saveButton.type = 'button';
    saveButton.className = 'btn btn-outline-success btn-sm mt-2 me-2';
    saveButton.innerHTML = '<i class="bi bi-bookmark"></i> 保存搜索条件';
    saveButton.onclick = showSaveSearchDialog;
    
    searchForm.appendChild(saveButton);
    
    // 添加加载搜索条件按钮
    const loadButton = document.createElement('button');
    loadButton.type = 'button';
    loadButton.className = 'btn btn-outline-info btn-sm mt-2';
    loadButton.innerHTML = '<i class="bi bi-folder-open"></i> 加载搜索条件';
    loadButton.onclick = showLoadSearchDialog;
    
    searchForm.appendChild(loadButton);
}

/**
 * 显示保存搜索条件对话框
 */
function showSaveSearchDialog() {
    const searchName = prompt('请输入搜索条件名称:');
    if (searchName && searchName.trim()) {
        saveSearchCondition(searchName.trim());
    }
}

/**
 * 保存搜索条件
 */
function saveSearchCondition(name) {
    const searchCondition = {
        id: Date.now(),
        name: name,
        filters: { ...SearchState.currentFilters },
        advancedFilters: getAdvancedSearchFilters(),
        timestamp: new Date().toISOString()
    };
    
    AdvancedSearchState.savedSearches.push(searchCondition);
    localStorage.setItem('savedSearches', JSON.stringify(AdvancedSearchState.savedSearches));
    
    alert('搜索条件已保存');
}

/**
 * 显示加载搜索条件对话框
 */
function showLoadSearchDialog() {
    if (AdvancedSearchState.savedSearches.length === 0) {
        alert('没有保存的搜索条件');
        return;
    }
    
    const searchList = AdvancedSearchState.savedSearches.map((search, index) => 
        `${index + 1}. ${search.name} (${formatDateTime(search.timestamp)})`
    ).join('\n');
    
    const choice = prompt(`请选择要加载的搜索条件:\n\n${searchList}\n\n请输入序号:`);
    const index = parseInt(choice) - 1;
    
    if (index >= 0 && index < AdvancedSearchState.savedSearches.length) {
        loadSearchCondition(AdvancedSearchState.savedSearches[index]);
    }
}

/**
 * 加载搜索条件
 */
function loadSearchCondition(searchCondition) {
    // 应用基础搜索条件
    const filters = searchCondition.filters;
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
    
    // 应用高级搜索条件
    if (searchCondition.advancedFilters) {
        applyAdvancedFilters(searchCondition.advancedFilters);
    }
    
    // 更新搜索状态并执行搜索
    updateSearchFilters();
    performSearch();
    
    alert(`已加载搜索条件: ${searchCondition.name}`);
}

/**
 * 应用高级搜索条件
 */
function applyAdvancedFilters(advancedFilters) {
    // 文件大小
    if (advancedFilters.minFileSize) {
        document.getElementById('minFileSize').value = Math.round(advancedFilters.minFileSize / (1024 * 1024));
    }
    if (advancedFilters.maxFileSize) {
        document.getElementById('maxFileSize').value = Math.round(advancedFilters.maxFileSize / (1024 * 1024));
    }
    
    // 图片尺寸
    if (advancedFilters.minWidth && advancedFilters.minHeight) {
        if (advancedFilters.minWidth >= 3840) {
            document.getElementById('imageSize').value = '4k';
        } else if (advancedFilters.minWidth >= 1920) {
            document.getElementById('imageSize').value = '1080p';
        } else if (advancedFilters.minWidth >= 1280) {
            document.getElementById('imageSize').value = '720p';
        }
    } else if (advancedFilters.maxWidth && advancedFilters.maxWidth < 1280) {
        document.getElementById('imageSize').value = 'small';
    }
    
    // 其他条件
    if (advancedFilters.exposureMode) {
        document.getElementById('exposureMode').value = advancedFilters.exposureMode;
    }
    if (advancedFilters.flash) {
        document.getElementById('flashMode').value = advancedFilters.flash;
    }
    if (advancedFilters.whiteBalance) {
        document.getElementById('whiteBalance').value = advancedFilters.whiteBalance;
    }
    if (advancedFilters.minISO) {
        document.getElementById('minISO').value = advancedFilters.minISO;
    }
    if (advancedFilters.maxISO) {
        document.getElementById('maxISO').value = advancedFilters.maxISO;
    }
    if (advancedFilters.minAperture) {
        document.getElementById('minAperture').value = advancedFilters.minAperture;
    }
    if (advancedFilters.maxAperture) {
        document.getElementById('maxAperture').value = advancedFilters.maxAperture;
    }
    if (advancedFilters.minShutterSpeed) {
        document.getElementById('minShutterSpeed').value = advancedFilters.minShutterSpeed;
    }
    if (advancedFilters.maxShutterSpeed) {
        document.getElementById('maxShutterSpeed').value = advancedFilters.maxShutterSpeed;
    }
    if (advancedFilters.minFocalLength) {
        document.getElementById('minFocalLength').value = advancedFilters.minFocalLength;
    }
    if (advancedFilters.maxFocalLength) {
        document.getElementById('maxFocalLength').value = advancedFilters.maxFocalLength;
    }
    if (advancedFilters.hasLocation !== undefined) {
        document.getElementById('hasLocation').value = advancedFilters.hasLocation ? 'true' : 'false';
    }
    if (advancedFilters.minPeopleCount !== undefined) {
        if (advancedFilters.minPeopleCount >= 3) {
            document.getElementById('peopleCount').value = '3+';
        } else {
            document.getElementById('peopleCount').value = advancedFilters.minPeopleCount.toString();
        }
    }
    if (advancedFilters.sceneType) {
        document.getElementById('sceneType').value = advancedFilters.sceneType;
    }
    if (advancedFilters.emotion) {
        document.getElementById('emotion').value = advancedFilters.emotion;
    }
}

/**
 * 加载保存的搜索条件
 */
function loadSavedSearches() {
    const saved = localStorage.getItem('savedSearches');
    if (saved) {
        AdvancedSearchState.savedSearches = JSON.parse(saved);
    }
}

/**
 * 添加搜索建议功能
 */
function addSearchSuggestions() {
    // 为关键词输入框添加搜索建议
    const keywordInput = document.getElementById('keywordInput');
    let suggestionTimeout;
    
    keywordInput.addEventListener('input', function() {
        clearTimeout(suggestionTimeout);
        const query = this.value.trim();
        
        if (query.length >= 2) {
            suggestionTimeout = setTimeout(() => {
                loadSearchSuggestions(query);
            }, 300);
        } else {
            hideSearchSuggestions();
        }
    });
    
    // 为标签和分类输入框添加搜索建议
    const tagFilter = document.getElementById('tagFilter');
    const categoryFilter = document.getElementById('categoryFilter');
    
    [tagFilter, categoryFilter].forEach(input => {
        input.addEventListener('input', function() {
            clearTimeout(suggestionTimeout);
            const query = this.value.trim();
            
            if (query.length >= 1) {
                suggestionTimeout = setTimeout(() => {
                    loadFilterSuggestions(this.id, query);
                }, 300);
            }
        });
    });
}

/**
 * 加载搜索建议
 */
async function loadSearchSuggestions(query) {
    try {
        const response = await fetch(`/api/v1/search/suggestions?prefix=${encodeURIComponent(query)}&limit=10`);
        
        if (response.ok) {
            const data = await response.json();
            showSearchSuggestions(data);
        }
    } catch (error) {
        console.error('加载搜索建议失败:', error);
    }
}

/**
 * 显示搜索建议
 */
function showSearchSuggestions(suggestions) {
    // TODO: 实现搜索建议显示
    console.log('搜索建议:', suggestions);
}

/**
 * 隐藏搜索建议
 */
function hideSearchSuggestions() {
    // TODO: 实现隐藏搜索建议
}

/**
 * 加载筛选建议
 */
async function loadFilterSuggestions(filterType, query) {
    try {
        let endpoint = '';
        if (filterType === 'tagFilter') {
            endpoint = '/api/v1/tags';
        } else if (filterType === 'categoryFilter') {
            endpoint = '/api/v1/categories';
        }
        
        if (endpoint) {
            const response = await fetch(`${endpoint}?search=${encodeURIComponent(query)}&limit=10`);
            
            if (response.ok) {
                const data = await response.json();
                showFilterSuggestions(filterType, data);
            }
        }
    } catch (error) {
        console.error('加载筛选建议失败:', error);
    }
}

/**
 * 显示筛选建议
 */
function showFilterSuggestions(filterType, suggestions) {
    // TODO: 实现筛选建议显示
    console.log(`${filterType} 建议:`, suggestions);
}
