/**
 * 家庭版智能照片系统 - 数据管理模块
 * 包含数据加载、状态管理、API调用等核心功能
 */

// 全局配置
const CONFIG = {
    API_BASE_URL: '/api/v1',
    PAGE_SIZE: 12,  // 默认值，将从配置中动态加载
    DEBOUNCE_DELAY: 300,
    IMAGE_PLACEHOLDER: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgdmlld0JveD0iMCAwIDIwMCAyMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIyMDAiIGhlaWdodD0iMjAwIiBmaWxsPSIjRjNGNEY2Ii8+CjxwYXRoIGQ9Ik0xMDAgMTAwSDE0MEwxMjAgMTIwSDEwMFYxNDBIMTZWMTAwWiIgZmlsbD0iIzk3OTdhNyIvPgo8L3N2Zz4K',
    importConfig: {
        max_upload_files: 50  // 默认值，将从配置中动态加载
    }
};

// 用户配置缓存
let userConfig = null;

// 全局状态管理
const AppState = {
    currentPage: 1,
    totalPages: 1,
    totalPhotos: 0,  // 添加总照片数
    currentView: 'grid', // 'grid' or 'list'
    selectedPhotos: new Set(),
    isLoading: false,
    searchFilters: {
        keyword: '',
        searchType: 'all',
        dateFilter: '',
        qualityFilter: '',
        sortBy: 'taken_at',
        sortOrder: 'desc',
        selectedTags: [],
        selectedCategories: []
    },
    photos: [],
    stats: {}
};

// 搜索类型提示文字映射
const searchTypePlaceholders = {
    'all': '支持搜索照片全部文本内容',
    'filename': '搜索照片文件名...',
    'description': '搜索用户照片描述...',
    'ai_analysis': '搜索AI分析结果...'
};

// 搜索范围提示文字映射
const searchScopeHints = {
    'all': '',
    'filename': '',
    'description': '',
    'ai_analysis': ''
};

// ============ 配置管理 ============

/**
 * 加载用户配置
 */
async function loadUserConfig() {
    try {
        const response = await fetch('/api/v1/config/user');
        if (response.ok) {
            const result = await response.json();
            if (result.success) {
                userConfig = result.data;
                // 更新全局配置
                CONFIG.PAGE_SIZE = userConfig.ui?.photos_per_page || 12;
                CONFIG.importConfig = userConfig.import || {};
                CONFIG.analysisConfig = userConfig.analysis || {};
                // 用户配置加载成功
            }
        }
    } catch (error) {
        console.error('加载用户配置失败:', error);
        // 使用默认配置
        CONFIG.PAGE_SIZE = 12;
        CONFIG.importConfig = { max_upload_files: 50 };
        CONFIG.analysisConfig = { batch_size: 100 };
    }
}

// ============ 多选下拉组件 ============

let tagMultiSelect = null;
let categoryMultiSelect = null;

// 全局标签和分类数据存储
let globalTagsData = [];
let globalCategoriesData = [];

// 标签名称查找辅助函数
function findTagName(tagId) {
    // 查找标签名称

    // 首先尝试从当前显示的选项中查找（最可靠的方法）
    const tagOptions = document.querySelectorAll('#tagOptions input[type="checkbox"]');
    for (const checkbox of tagOptions) {
        if (parseInt(checkbox.value) === tagId) {
            // 找到对应的标签文本
            const label = checkbox.parentElement.querySelector('label');
            if (label) {
                const tagName = label.textContent.trim();
                // 从DOM选项中找到标签
                return tagName;
            }
        }
    }

    // 如果DOM查找失败，尝试从多选组件数据中查找
    let tag = null;
    if (window.tagMultiSelect && window.tagMultiSelect.filteredData) {
        tag = window.tagMultiSelect.filteredData.find(item => item.id === tagId);
        // 从多选组件过滤数据查找
    }

    if (!tag && window.tagMultiSelect && window.tagMultiSelect.data) {
        tag = window.tagMultiSelect.data.find(item => item.id === tagId);
        // 从多选组件原始数据查找
    }

    // 如果还是找不到，尝试从全局标签数据中查找
    if (!tag) {
        tag = globalTagsData ? globalTagsData.find(tag => tag.id === tagId) : null;
        // 从全局标签数据查找
    }

    const result = tag ? tag.name : `标签${tagId}`;
    // 返回结果
    return result;
}

// 分类名称查找辅助函数
function findCategoryName(categoryId) {
    // 首先尝试从全局分类数据中查找
    let category = globalCategoriesData ? globalCategoriesData.find(category => category.id === categoryId) : null;

    // 如果找不到，尝试从当前多选组件的过滤数据中查找
    if (!category && window.categoryMultiSelect && window.categoryMultiSelect.filteredData) {
        category = window.categoryMultiSelect.filteredData.find(item => item.id === categoryId);
    }

    // 如果还是找不到，尝试从当前多选组件的原始数据中查找
    if (!category && window.categoryMultiSelect && window.categoryMultiSelect.data) {
        category = window.categoryMultiSelect.data.find(item => item.id === categoryId);
    }

    return category ? category.name : `分类${categoryId}`;
}

/**
 * 初始化多选下拉组件
 */
function initMultiSelectDropdown(container, data, placeholder, onChange) {
    // 初始化多选下拉组件
    
    const button = container.querySelector('.dropdown-toggle');
    const buttonText = container.querySelector('[id$="FilterText"]');
    const searchInput = container.querySelector('input[type="text"]');
    const optionsContainer = container.querySelector('[id$="Options"]');
    
    // 找到必要的DOM元素
    
    let selectedItems = new Set();
    let filteredData = [...data];
    
    // 渲染选项
    function renderOptions() {
        console.log('渲染选项 - 容器:', optionsContainer);
        console.log('渲染选项 - 数据:', filteredData);
        optionsContainer.innerHTML = '';
        
        filteredData.forEach(item => {
            const optionDiv = document.createElement('div');
            optionDiv.className = 'form-check';
            
            const isSelected = selectedItems.has(item.id);
            
            optionDiv.innerHTML = `
                <input class="form-check-input" type="checkbox" 
                       id="option_${item.id}" 
                       value="${item.id}" 
                       ${isSelected ? 'checked' : ''}>
                <label class="form-check-label" for="option_${item.id}">
                    ${item.name}
                </label>
            `;
            
            // 绑定点击事件
            const checkbox = optionDiv.querySelector('input[type="checkbox"]');
            checkbox.addEventListener('change', (e) => {
                if (e.target.checked) {
                    selectedItems.add(item.id);
                } else {
                    selectedItems.delete(item.id);
                }
                updateButtonText();
                onChange(Array.from(selectedItems));
            });
            
            optionsContainer.appendChild(optionDiv);
        });
    }
    
    // 更新按钮文本
    function updateButtonText() {
        const count = selectedItems.size;
        if (count === 0) {
            buttonText.textContent = `选择${placeholder}`;
        } else if (count <= 3) {
            const selectedNames = Array.from(selectedItems).map(id => {
                if (placeholder === '标签') {
                    return findTagName(id);
                } else if (placeholder === '分类') {
                    return findCategoryName(id);
                } else {
                    return `ID:${id}`;
                }
            });
            buttonText.textContent = selectedNames.join(', ');
        } else {
            buttonText.textContent = `已选择 ${count} 个${placeholder}`;
        }
    }
    
    // 搜索功能 - 使用后端API
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            const searchTerm = e.target.value.trim();

            // 清除之前的定时器
            clearTimeout(searchTimeout);

            // 如果搜索词为空，显示所有数据
            if (searchTerm === '') {
                filteredData = [...data];
                renderOptions();
                return;
            }

            // 防抖处理，避免频繁API调用
            searchTimeout = setTimeout(async () => {
                try {
                    // 调用后端搜索API
                    const searchUrl = `/api/v1/tags/?search=${encodeURIComponent(searchTerm)}&limit=200`;
                    const response = await fetch(searchUrl);

                    if (response.ok) {
                        const searchResults = await response.json();
                        // 将搜索结果转换为前端需要的格式
                        filteredData = searchResults.map(tag => ({
                            id: tag.id,
                            name: tag.name
                        }));
                        console.log(`搜索 "${searchTerm}" 找到 ${filteredData.length} 个标签`);
                        renderOptions();
                    } else {
                        console.error('搜索标签失败:', response.status);
                        // 搜索失败时，回退到本地过滤
                        filteredData = data.filter(item =>
                            item.name.toLowerCase().includes(searchTerm.toLowerCase())
                        );
                        renderOptions();
                    }
                } catch (error) {
                    console.error('搜索标签出错:', error);
                    // 出错时，回退到本地过滤
                    filteredData = data.filter(item =>
                        item.name.toLowerCase().includes(searchTerm.toLowerCase())
                    );
                    renderOptions();
                }
            }, 300); // 300ms防抖
        });
    }
    
    // 阻止下拉菜单点击时关闭
    const dropdownMenu = container.querySelector('.dropdown-menu');
    if (dropdownMenu) {
        dropdownMenu.addEventListener('click', (e) => {
            e.stopPropagation();
        });
    }
    
    // 初始化
    renderOptions();
    updateButtonText();
    
    // 返回控制对象
    return {
        setSelectedItems: (itemIds) => {
            selectedItems = new Set(itemIds);
            renderOptions();
            updateButtonText();
        },
        clearSelection: () => {
            selectedItems.clear();
            renderOptions();
            updateButtonText();
            onChange([]);
        },
        // 暴露数据供查找函数使用
        data: data,
        filteredData: filteredData
    };
}

/**
 * 初始化搜索式多选组件
 */
async function initSearchMultiSelect() {
    try {
        // 并行加载热门标签、全部标签和分类数据
        const [hotTagsResponse, tagsResponse, categoriesResponse] = await Promise.all([
            fetch('/api/v1/tags/popular?limit=50'),  // 热门标签优先
            fetch('/api/v1/tags/?limit=1000'),       // 获取最多标签确保包含所有标签
            fetch('/api/v1/categories/')
        ]);

        let tags = [];
        let categories = [];

        // 使用全部标签数据，确保包含所有标签
        if (tagsResponse.ok) {
            const allTags = await tagsResponse.json();
            tags = allTags.map(tag => ({
                id: tag.id,
                name: tag.name
            }));
            console.log('标签数据加载成功:', tags.length, '个标签');
        } else {
            console.error('标签数据加载失败:', tagsResponse.status, tagsResponse.statusText);
            // 如果全部标签加载失败，尝试使用热门标签
            if (hotTagsResponse.ok) {
                const hotTags = await hotTagsResponse.json();
                tags = hotTags.map(tag => ({
                    id: tag.id,
                    name: tag.name
                }));
                console.warn('使用热门标签作为备用:', tags.length, '个热门标签');
            }
        }

        // 存储完整标签数据到全局变量（用于搜索时的本地过滤备用）
        // 注意：现在tags变量已经包含了全部标签数据
        globalTagsData = [...tags]; // 直接使用已加载的标签数据

        if (categoriesResponse.ok) {
            categories = await categoriesResponse.json();
            globalCategoriesData = categories; // 存储到全局变量
            console.log('分类数据加载成功:', categories.length, '个分类');
        } else {
            console.error('分类数据加载失败:', categoriesResponse.status, categoriesResponse.statusText);
        }

        // 初始化标签多选组件
        const tagContainer = document.getElementById('tagFilter');
        console.log('标签容器:', tagContainer);
        if (tagContainer) {
            console.log('开始初始化标签多选组件');
            tagMultiSelect = initMultiSelectDropdown(tagContainer, tags, '标签', (selectedIds) => {
                AppState.searchFilters.selectedTags = selectedIds;
                AppState.currentPage = 1;
                loadPhotos(1);
                updateFilterStatus();
            });
            // 设置为全局变量供查找函数使用
            window.tagMultiSelect = tagMultiSelect;
        } else {
            console.error('未找到标签容器元素 #tagFilter');
        }

        // 初始化分类多选组件
        const categoryContainer = document.getElementById('categoryFilter');
        console.log('分类容器:', categoryContainer);
        if (categoryContainer) {
            console.log('开始初始化分类多选组件');
            categoryMultiSelect = initMultiSelectDropdown(categoryContainer, categories, '分类', (selectedIds) => {
                AppState.searchFilters.selectedCategories = selectedIds;
                AppState.currentPage = 1;
                loadPhotos(1);
                updateFilterStatus();
            });
            // 设置为全局变量供查找函数使用
            window.categoryMultiSelect = categoryMultiSelect;
        } else {
            console.error('未找到分类容器元素 #categoryFilter');
        }

        console.log('搜索式多选组件初始化完成');
    } catch (error) {
        console.error('初始化搜索式多选组件失败:', error);
    }
}

// ============ 数据加载函数 ============

// loadHotData 函数已移除，因为热门标签和分类配置已从用户界面移除

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

        // 确保配置已加载
        if (!userConfig) {
            await loadUserConfig();
        }

        const params = new URLSearchParams({
            offset: (page - 1) * CONFIG.PAGE_SIZE,
            limit: CONFIG.PAGE_SIZE,
            sort_by: AppState.searchFilters.sortBy,
            sort_order: AppState.searchFilters.sortOrder,
            keyword: AppState.searchFilters.keyword,
            search_type: AppState.searchFilters.searchType,
            date_filter: AppState.searchFilters.dateFilter,
            quality_filter: AppState.searchFilters.qualityFilter
        });

        // 添加标签筛选参数
        if (AppState.searchFilters.selectedTags.length > 0) {
            params.append('tag_ids', AppState.searchFilters.selectedTags.join(','));
        }

        // 添加分类筛选参数
        if (AppState.searchFilters.selectedCategories.length > 0) {
            params.append('category_ids', AppState.searchFilters.selectedCategories.join(','));
        }
        
        // 添加自定义日期范围参数
        if (AppState.searchFilters.dateFilter === 'custom') {
            if (elements.startDate.value) {
                params.append('start_date', elements.startDate.value);
            }
            if (elements.endDate.value) {
                params.append('end_date', elements.endDate.value);
            }
        }

        console.log('发送搜索请求:', `${CONFIG.API_BASE_URL}/search/photos?${params}`);
        
        const response = await fetch(`${CONFIG.API_BASE_URL}/search/photos?${params}`);
        const data = await response.json();

        console.log('API响应数据:', data);

        if (data.success) {
            // 兼容两种数据格式：data.data 和 data.photos
            AppState.photos = data.data || data.photos || [];
            AppState.currentPage = page;
            AppState.totalPhotos = data.total || 0;
            AppState.totalPages = Math.ceil(AppState.totalPhotos / CONFIG.PAGE_SIZE);

            // 调试信息
            console.log('照片库分页信息:', {
                currentPage: AppState.currentPage,
                totalPages: AppState.totalPages,
                totalPhotos: AppState.totalPhotos,
                photosInCurrentPage: AppState.photos.length,
                pageSize: CONFIG.PAGE_SIZE
            });

            renderPhotos();
            renderPagination();
            renderPaginationInfo();
            updatePhotoCount(AppState.totalPhotos);
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
        <div class="stats-item">
            <i class="bi bi-images text-primary me-1"></i>
            <span class="stats-value">${stats.total_photos || 0}</span>
            <span class="stats-label">照片</span>
        </div>
        <div class="stats-divider"></div>
        <div class="stats-item">
            <i class="bi bi-tags text-success me-1"></i>
            <span class="stats-value">${stats.total_tags || 0}</span>
            <span class="stats-label">标签</span>
        </div>
        <div class="stats-divider"></div>
        <div class="stats-item">
            <i class="bi bi-collection text-info me-1"></i>
            <span class="stats-value">${stats.total_categories || 0}</span>
            <span class="stats-label">分类</span>
        </div>
        <div class="stats-divider"></div>
        <div class="stats-item">
            <i class="bi bi-star text-warning me-1"></i>
            <span class="stats-value">${Object.keys(stats.quality_distribution || {}).length}</span>
            <span class="stats-label">质量等级</span>
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
    const html = photos.map(photo => `
        <div class="col-md-2 col-6">
            ${createPhotoCard(photo)}
        </div>
    `).join('');
    elements.photosGrid.innerHTML = html;

    // 为每个照片卡片绑定事件
    photos.forEach((photo, index) => {
        const colDiv = elements.photosGrid.children[index];
        const card = colDiv.querySelector('.photo-card');
        
        // 绑定点击事件 - 支持选择和查看详情
        card.addEventListener('click', (event) => {
            // 检查是否是触摸设备，如果是触摸设备且不是按钮区域，则忽略
            if (window.HybridInputManager && window.HybridInputManager.getCurrentInputType() === 'touch') {
                const photoImage = event.target.closest('.photo-image, .photo-thumbnail');
                const photoOverlay = event.target.closest('.photo-overlay');

                // 如果是触摸图片区域，不处理点击事件（由混合交互管理器处理）
                if (photoImage && !photoOverlay) {
                    return;
                }
            }

            // 检查点击的是否是照片图片区域（只有图片区域才触发查看详情）
            const isPhotoImage = event.target.closest('.photo-image, .photo-thumbnail');
            const isPhotoOverlay = event.target.closest('.photo-overlay');
            const isGpsIcon = event.target.closest('.gps-icon');
            const isPhotoInfo = event.target.closest('.photo-info');

            // 如果按住了Ctrl键，则切换选择状态（无论点击哪里）
            if (event.ctrlKey || event.metaKey) {
                event.preventDefault();
                event.stopPropagation();

                if (window.PhotoManager) {
                    window.PhotoManager.togglePhotoSelection(photo.id);
                }
                return;
            }

            // 如果点击的是照片图片区域，查看详情
            if (isPhotoImage && !isPhotoOverlay) {
                showPhotoDetail(photo);
                return;
            }

            // 如果点击的是GPS图标或照片信息区域，不做任何处理（由各自的事件处理器处理）
            // 这样可以避免误触发查看详情
        });
    });

    // 初始化选择框状态
    if (window.initializeSelectionCheckboxes) {
        window.initializeSelectionCheckboxes();
    }
}

function renderListView(photos) {
    const html = photos.map(photo => createPhotoListItem(photo)).join('');
    elements.photosGrid.innerHTML = html;

    // 为每个照片列表项绑定事件
    photos.forEach((photo, index) => {
        const item = elements.photosGrid.children[index];
        
        // 绑定点击事件 - 支持选择和查看详情
        item.addEventListener('click', (event) => {
            // 检查是否是触摸设备，如果是触摸设备且不是按钮区域，则忽略
            if (window.HybridInputManager && window.HybridInputManager.getCurrentInputType() === 'touch') {
                const photoImage = event.target.closest('.photo-image, .photo-thumbnail');
                const photoOverlay = event.target.closest('.photo-overlay');

                // 如果是触摸图片区域，不处理点击事件（由混合交互管理器处理）
                if (photoImage && !photoOverlay) {
                    return;
                }
            }

            // 检查点击的是否是照片缩略图区域（只有缩略图区域才触发查看详情）
            const isPhotoThumbnail = event.target.closest('.photo-thumbnail');
            const isPhotoOverlay = event.target.closest('.photo-overlay');
            const isGpsIcon = event.target.closest('.gps-icon');
            const isPhotoDetails = event.target.closest('.photo-details');

            // 如果按住了Ctrl键，则切换选择状态（无论点击哪里）
            if (event.ctrlKey || event.metaKey) {
                event.preventDefault();
                event.stopPropagation();

                if (window.PhotoManager) {
                    window.PhotoManager.togglePhotoSelection(photo.id);
                }
                return;
            }

            // 如果点击的是照片缩略图区域，查看详情
            if (isPhotoThumbnail && !isPhotoOverlay) {
                showPhotoDetail(photo);
                return;
            }

            // 如果点击的是GPS图标或照片详情区域，不做任何处理（由各自的事件处理器处理）
            // 这样可以避免误触发查看详情
        });
    });

    // 初始化选择框状态
    if (window.initializeSelectionCheckboxes) {
        window.initializeSelectionCheckboxes();
    }
}

function renderPagination() {
    console.log('渲染分页:', {
        currentPage: AppState.currentPage,
        totalPages: AppState.totalPages,
        totalPhotos: AppState.totalPhotos,
        shouldShow: AppState.totalPages > 1,
        paginationContainer: elements.paginationContainer,
        pagination: elements.pagination
    });

    if (!elements.paginationContainer) {
        console.error('分页容器元素未找到!');
        return;
    }

    if (AppState.totalPages <= 1) {
        console.log('总页数 <= 1，隐藏分页控件');
        elements.paginationContainer.classList.add('d-none');
        return;
    }

    console.log('显示分页控件，移除d-none类');
    elements.paginationContainer.classList.remove('d-none');

    let html = '';

    // 上一页
    if (AppState.currentPage > 1) {
        html += `<li class="page-item">
            <a class="page-link" href="#" data-page="${AppState.currentPage - 1}">
                <i class="bi bi-chevron-left"></i> 上一页
            </a>
        </li>`;
    } else {
        html += `<li class="page-item disabled">
            <span class="page-link">
                <i class="bi bi-chevron-left"></i> 上一页
            </span>
        </li>`;
    }

    // 第一页
    if (AppState.currentPage > 3) {
        html += `<li class="page-item">
            <a class="page-link" href="#" data-page="1">1</a>
        </li>`;
        if (AppState.currentPage > 4) {
            html += `<li class="page-item disabled">
                <span class="page-link">...</span>
            </li>`;
        }
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

    // 最后一页
    if (AppState.currentPage < AppState.totalPages - 2) {
        if (AppState.currentPage < AppState.totalPages - 3) {
            html += `<li class="page-item disabled">
                <span class="page-link">...</span>
            </li>`;
        }
        html += `<li class="page-item">
            <a class="page-link" href="#" data-page="${AppState.totalPages}">${AppState.totalPages}</a>
        </li>`;
    }

    // 下一页
    if (AppState.currentPage < AppState.totalPages) {
        html += `<li class="page-item">
            <a class="page-link" href="#" data-page="${AppState.currentPage + 1}">
                下一页 <i class="bi bi-chevron-right"></i>
            </a>
        </li>`;
    } else {
        html += `<li class="page-item disabled">
            <span class="page-link">
                下一页 <i class="bi bi-chevron-right"></i>
            </span>
        </li>`;
    }

    elements.pagination.innerHTML = html;

    // 绑定分页事件
    elements.pagination.querySelectorAll('.page-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = parseInt(e.target.dataset.page);
            if (page && page !== AppState.currentPage) {
                console.log('切换到页面:', page);
                loadPhotos(page);
            }
        });
    });
    
    // 确认分页容器状态
    console.log('分页渲染完成，容器类名:', elements.paginationContainer.className);
    console.log('分页HTML内容:', elements.pagination.innerHTML);
}

function renderPaginationInfo() {
    const paginationInfo = document.getElementById('paginationInfo');
    const paginationText = document.getElementById('paginationText');
    const pageSize = document.getElementById('pageSize');
    
    console.log('渲染分页信息:', {
        paginationInfo: paginationInfo,
        paginationText: paginationText,
        pageSize: pageSize,
        totalPages: AppState.totalPages,
        totalPhotos: AppState.totalPhotos
    });
    
    if (!paginationInfo) {
        console.error('分页信息元素未找到!');
        return;
    }
    
    if (AppState.totalPages <= 1) {
        console.log('总页数 <= 1，隐藏分页信息');
        paginationInfo.classList.add('d-none');
        return;
    }
    
    console.log('显示分页信息，移除d-none类');
    paginationInfo.classList.remove('d-none');
    
    const startPhoto = (AppState.currentPage - 1) * CONFIG.PAGE_SIZE + 1;
    const endPhoto = Math.min(AppState.currentPage * CONFIG.PAGE_SIZE, AppState.totalPhotos);
    
    paginationText.textContent = `第 ${AppState.currentPage} 页，共 ${AppState.totalPages} 页 (显示 ${startPhoto}-${endPhoto} 张，共 ${AppState.totalPhotos} 张照片)`;
    pageSize.textContent = CONFIG.PAGE_SIZE;
}

// ============ 搜索和筛选函数 ============

function handleSearch() {
    const keyword = elements.searchInput.value.trim();
    AppState.searchFilters.keyword = keyword;
    AppState.currentPage = 1;
    loadPhotos(1);
    updateFilterStatus();
}

function handleSearchTypeChange() {
    const searchType = elements.searchType.value;
    AppState.searchFilters.searchType = searchType;
    
    // 更新搜索框提示文字
    elements.searchInput.placeholder = searchTypePlaceholders[searchType] || searchTypePlaceholders['all'];
    
    // 更新搜索框tooltip（只在全部内容时显示高级语法）
    if (searchType === 'all') {
        elements.searchInput.title = '支持关键词搜索、精确搜索、前缀搜索等';
    } else {
        elements.searchInput.title = '';
    }
    
    // 隐藏搜索范围提示
    elements.searchScopeHint.style.display = 'none';
    
    // 显示或隐藏搜索语法提示
    const searchSyntax = document.getElementById('searchSyntax');
    if (searchSyntax) {
        if (searchType === 'all') {
            searchSyntax.style.display = 'block';
        } else {
            searchSyntax.style.display = 'none';
        }
    }
    
    // 如果搜索帮助面板打开，也关闭它
    const searchHelpPanel = document.getElementById('searchHelpPanel');
    if (searchHelpPanel && searchHelpPanel.style.display !== 'none') {
        searchHelpPanel.style.display = 'none';
    }
    
    // 显示或隐藏搜索建议
    updateSearchSuggestions(searchType);
    
    // 如果有关键词，重新搜索
    if (AppState.searchFilters.keyword) {
        AppState.currentPage = 1;
        loadPhotos(1);
    }
    
    updateFilterStatus();
}

// 搜索帮助功能
function toggleSearchHelp() {
    const helpPanel = document.getElementById('searchHelpPanel');
    if (helpPanel) {
        if (helpPanel.style.display === 'none' || helpPanel.style.display === '') {
            helpPanel.style.display = 'block';
        } else {
            helpPanel.style.display = 'none';
        }
    }
}

function hideSearchHelp() {
    const helpPanel = document.getElementById('searchHelpPanel');
    if (helpPanel) {
        helpPanel.style.display = 'none';
    }
}

// 照片展示区帮助功能
function togglePhotoDisplayHelp() {
    const helpPanel = document.getElementById('photoDisplayHelpPanel');
    if (helpPanel) {
        if (helpPanel.style.display === 'none' || helpPanel.style.display === '') {
            helpPanel.style.display = 'block';
        } else {
            helpPanel.style.display = 'none';
        }
    }
}

function hidePhotoDisplayHelp() {
    const helpPanel = document.getElementById('photoDisplayHelpPanel');
    if (helpPanel) {
        helpPanel.style.display = 'none';
    }
}

// 搜索建议功能
function searchSuggestion(text) {
    if (elements.searchInput) {
        elements.searchInput.value = text;
        AppState.searchFilters.keyword = text;
        AppState.currentPage = 1;
        loadPhotos(1);
        hideSearchHelp();
    }
}

function updateSearchSuggestions(searchType) {
    const suggestionsContainer = elements.searchSuggestions;
    const suggestionsDiv = suggestionsContainer.querySelector('div');
    
    // 由于标签和分类已移至筛选区域，搜索建议功能暂时隐藏
    // 未来可以根据需要添加其他类型的搜索建议
    suggestionsContainer.style.display = 'none';
}

function selectSuggestion(text) {
    // 设置搜索框内容
    elements.searchInput.value = text;
    
    // 触发搜索
    AppState.searchFilters.keyword = text;
    AppState.currentPage = 1;
    loadPhotos(1);
    updateFilterStatus();
}

function handleDateFilterChange() {
    const dateFilter = elements.dateFilter.value;
    AppState.searchFilters.dateFilter = dateFilter;
    
    // 显示或隐藏自定义日期范围
    if (dateFilter === 'custom') {
        elements.customDateRange.style.display = 'block';
    } else {
        elements.customDateRange.style.display = 'none';
        // 清除自定义日期
        elements.startDate.value = '';
        elements.endDate.value = '';
    }
    
    AppState.currentPage = 1;
    loadPhotos(1);
    updateFilterStatus();
}

function handleCustomDateChange() {
    const startDate = elements.startDate.value;
    const endDate = elements.endDate.value;
    
    // 验证日期范围
    if (startDate && endDate && startDate > endDate) {
        showWarning('开始日期不能晚于结束日期');
        return;
    }
    
    AppState.currentPage = 1;
    loadPhotos(1);
    updateFilterStatus();
}

function handleFilterChange() {
    AppState.searchFilters.qualityFilter = elements.qualityFilter.value;
    AppState.currentPage = 1;
    loadPhotos(1);
    updateFilterStatus();
}

function handleSortChange() {
    AppState.searchFilters.sortBy = elements.sortBy.value;
    AppState.searchFilters.sortOrder = elements.sortOrder.value;
    AppState.currentPage = 1;
    loadPhotos(1);
    updateFilterStatus();
}

function clearAllFilters() {
    // 先更新AppState
    AppState.searchFilters = {
        keyword: '',
        searchType: 'all',
        dateFilter: '',
        qualityFilter: '',
        sortBy: 'taken_at',
        sortOrder: 'desc',
        selectedTags: [],
        selectedCategories: []
    };
    
    // 重置所有筛选条件
    elements.searchInput.value = '';
    elements.searchType.value = 'all';
    elements.dateFilter.value = '';
    elements.qualityFilter.value = '';
    elements.sortBy.value = 'taken_at';
    elements.sortOrder.value = 'desc';
    elements.startDate.value = '';
    elements.endDate.value = '';
    
    // 重置搜索提示文字
    elements.searchInput.placeholder = searchTypePlaceholders['all'];
    elements.searchScopeHint.textContent = searchScopeHints['all'];
    
    // 隐藏搜索建议
    elements.searchSuggestions.style.display = 'none';
    
    // 隐藏自定义日期范围
    elements.customDateRange.style.display = 'none';
    
    // 清空多选组件
    if (tagMultiSelect) {
        tagMultiSelect.clearSelection();
    }
    if (categoryMultiSelect) {
        categoryMultiSelect.clearSelection();
    }
    
    AppState.currentPage = 1;
    loadPhotos(1);
    updateFilterStatus();
}

function updateFilterStatus() {
    const filters = AppState.searchFilters;
    const statusParts = [];
    
    // 检查是否有筛选条件
    if (filters.keyword) {
        const searchTypeLabels = {
            'all': '全部内容',
            'filename': '文件名',
            'description': '描述',
            'address': '拍摄地址',
            'ai_analysis': 'AI分析结果'
        };
        const searchTypeLabel = searchTypeLabels[filters.searchType] || '全部内容';
        statusParts.push(`搜索(${searchTypeLabel}): "${filters.keyword}"`);
    }
    
    if (filters.dateFilter && filters.dateFilter !== '') {
        const dateLabels = {
            'today': '今天',
            'yesterday': '昨天',
            'last_7_days': '最近7天',
            'last_30_days': '最近30天',
            'last_month': '上个月',
            'this_year': '今年',
            'last_year': '去年',
            'no_date': '无拍摄时间',
            'custom': '自定义'
        };
        if (filters.dateFilter === 'custom' && elements.startDate.value && elements.endDate.value) {
            statusParts.push(`日期: ${elements.startDate.value} 至 ${elements.endDate.value}`);
        } else if (dateLabels[filters.dateFilter]) {
            statusParts.push(`日期: ${dateLabels[filters.dateFilter]}`);
        } else if (filters.dateFilter === 'no_date') {
            statusParts.push('日期: 无拍摄时间');
        }
    }
    
    if (filters.qualityFilter) {
        const qualityLabels = {
            'excellent': '优秀',
            'good': '良好',
            'average': '一般',
            'poor': '较差',
            'bad': '很差'
        };
        statusParts.push(`质量: ${qualityLabels[filters.qualityFilter] || filters.qualityFilter}`);
    }
    
    // 显示选中的标签
    if (filters.selectedTags.length > 0) {
        const selectedTagNames = filters.selectedTags.map(id => findTagName(id));
        statusParts.push(`标签: ${selectedTagNames.join(', ')}`);
    }
    
    // 显示选中的分类
    if (filters.selectedCategories.length > 0) {
        const selectedCategoryNames = filters.selectedCategories.map(id => findCategoryName(id));
        statusParts.push(`分类: ${selectedCategoryNames.join(', ')}`);
    }
    
    if (filters.sortBy !== 'taken_at' || filters.sortOrder !== 'desc') {
        const sortLabels = {
            'taken_at': '拍摄时间',
            'created_at': '导入时间',
            'filename': '文件名',
            'quality_score': '质量分数'
        };
        const orderLabels = {
            'asc': '升序',
            'desc': '降序'
        };
        statusParts.push(`排序: ${sortLabels[filters.sortBy] || filters.sortBy} ${orderLabels[filters.sortOrder] || filters.sortOrder}`);
    }
    
    // 显示或隐藏筛选状态
    if (statusParts.length > 0) {
        elements.filterStatusText.textContent = `当前筛选条件：${statusParts.join(' | ')}`;
        elements.filterStatus.style.display = 'block';
    } else {
        elements.filterStatus.style.display = 'none';
    }
}

// ============ 全局导出 ============

// 导出配置和状态
window.CONFIG = CONFIG;
window.AppState = AppState;
window.searchTypePlaceholders = searchTypePlaceholders;
window.searchScopeHints = searchScopeHints;

// 导出数据加载函数
window.loadUserConfig = loadUserConfig;
// window.loadHotData 已移除
window.loadStats = loadStats;
window.loadPhotos = loadPhotos;
window.initSearchMultiSelect = initSearchMultiSelect;

// 导出渲染函数
window.renderStats = renderStats;
window.renderPhotos = renderPhotos;
window.renderGridView = renderGridView;
window.renderListView = renderListView;
window.renderPagination = renderPagination;

// 导出搜索和筛选函数
window.handleSearch = handleSearch;
window.handleSearchTypeChange = handleSearchTypeChange;
window.updateSearchSuggestions = updateSearchSuggestions;
window.selectSuggestion = selectSuggestion;
window.handleDateFilterChange = handleDateFilterChange;
window.handleCustomDateChange = handleCustomDateChange;
window.handleFilterChange = handleFilterChange;
window.handleSortChange = handleSortChange;
window.clearAllFilters = clearAllFilters;
window.updateFilterStatus = updateFilterStatus;
