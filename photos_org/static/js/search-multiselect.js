/**
 * 家庭版智能照片系统 - 搜索式多选组件
 * 
 * 功能：
 * 1. 搜索式多选下拉框
 * 2. 支持标签和分类的多选
 * 3. 实时搜索过滤
 * 4. 已选择项目显示和管理
 */

/**
 * 搜索式多选组件类
 */
class SearchMultiSelect {
    constructor(options) {
        this.container = options.container;
        this.placeholder = options.placeholder || '搜索...';
        this.dataSource = options.dataSource || [];
        this.onChange = options.onChange || (() => {});
        this.maxDisplayItems = options.maxDisplayItems || 5;
        this.selectedItems = new Set();
        this.filteredData = [...this.dataSource];
        this.isOpen = false;
        this.hoverTimeout = null;
        
        this.init();
    }
    
    init() {
        this.createHTML();
        this.bindEvents();
        this.render();
    }
    
    createHTML() {
        this.container.innerHTML = `
            <div class="search-multiselect">
                <div class="search-multiselect-trigger">
                    <span class="selected-count">选择${this.placeholder}</span>
                    <i class="bi bi-chevron-down"></i>
                </div>
                <div class="search-multiselect-selected">
                    <!-- 已选择的项目将在这里显示 -->
                </div>
            </div>
        `;
        
        // 创建下拉菜单并添加到body
        this.dropdown = document.createElement('div');
        this.dropdown.className = 'search-multiselect-dropdown';
        this.dropdown.innerHTML = `
            <div class="search-multiselect-search">
                <input type="text" class="form-control" placeholder="${this.placeholder}">
                <i class="bi bi-search"></i>
            </div>
            <div class="search-multiselect-options">
                <!-- 选项列表将在这里动态生成 -->
            </div>
            <div class="search-multiselect-actions">
                <button type="button" class="btn btn-sm btn-outline-primary" id="selectAll">全选</button>
                <button type="button" class="btn btn-sm btn-outline-secondary" id="clearAll">清空</button>
            </div>
        `;
        
        // 将下拉菜单添加到body
        document.body.appendChild(this.dropdown);
        
        // 获取DOM元素
        this.trigger = this.container.querySelector('.search-multiselect-trigger');
        this.searchInput = this.dropdown.querySelector('.search-multiselect-search input');
        this.optionsContainer = this.dropdown.querySelector('.search-multiselect-options');
        this.selectedContainer = this.container.querySelector('.search-multiselect-selected');
        this.selectAllBtn = this.dropdown.querySelector('#selectAll');
        this.clearAllBtn = this.dropdown.querySelector('#clearAll');
    }
    
    bindEvents() {
        // 搜索输入事件
        if (this.searchInput) {
            this.searchInput.addEventListener('input', (e) => {
                this.filterOptions(e.target.value);
            });
        }
        
        // 全选按钮
        if (this.selectAllBtn) {
            this.selectAllBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.selectAll();
            });
        }
        
        // 清空按钮
        if (this.clearAllBtn) {
            this.clearAllBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.clearAll();
            });
        }
        
        // 点击外部关闭下拉框
        document.addEventListener('click', (e) => {
            if (!this.container.contains(e.target)) {
                this.closeDropdown();
            }
        });
        
        // 触发器点击事件
        if (this.trigger) {
            this.trigger.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.toggleDropdown();
            });
            
            // 鼠标悬停事件
            this.trigger.addEventListener('mouseenter', () => {
                if (this.hoverTimeout) {
                    clearTimeout(this.hoverTimeout);
                }
            });
            
            this.trigger.addEventListener('mouseleave', () => {
                this.hoverTimeout = setTimeout(() => {
                    if (this.isOpen) {
                        this.closeDropdown();
                    }
                }, 150);
            });
        }
        
        // 下拉框鼠标事件
        if (this.dropdown) {
            this.dropdown.addEventListener('click', (e) => {
                e.stopPropagation();
            });
            
            this.dropdown.addEventListener('mouseenter', () => {
                if (this.hoverTimeout) {
                    clearTimeout(this.hoverTimeout);
                }
            });
            
            this.dropdown.addEventListener('mouseleave', () => {
                this.hoverTimeout = setTimeout(() => {
                    this.closeDropdown();
                }, 150);
            });
        }
    }
    
    filterOptions(searchTerm) {
        const term = searchTerm.toLowerCase().trim();
        
        if (term === '') {
            this.filteredData = [...this.dataSource];
        } else {
            this.filteredData = this.dataSource.filter(item => 
                item.name.toLowerCase().includes(term)
            );
        }
        
        this.renderOptions();
    }
    
    renderOptions() {
        this.optionsContainer.innerHTML = '';
        
        if (this.filteredData.length === 0) {
            this.optionsContainer.innerHTML = '<div class="text-center text-muted py-2">没有找到匹配的选项</div>';
            return;
        }
        
        this.filteredData.forEach(item => {
            const option = document.createElement('div');
            option.className = `search-multiselect-option ${this.selectedItems.has(item.id) ? 'selected' : ''}`;
            option.innerHTML = `
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" 
                           id="option-${item.id}" 
                           ${this.selectedItems.has(item.id) ? 'checked' : ''}>
                    <label class="form-check-label" for="option-${item.id}">
                        ${item.name}
                    </label>
                </div>
            `;
            
            option.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggleOption(item.id);
            });
            
            this.optionsContainer.appendChild(option);
        });
    }
    
    toggleOption(itemId) {
        if (this.selectedItems.has(itemId)) {
            this.selectedItems.delete(itemId);
        } else {
            this.selectedItems.add(itemId);
        }
        
        this.renderOptions();
        this.renderSelected();
        this.updateTrigger();
        this.onChange(Array.from(this.selectedItems));
    }
    
    selectAll() {
        this.filteredData.forEach(item => {
            this.selectedItems.add(item.id);
        });
        
        this.renderOptions();
        this.renderSelected();
        this.updateTrigger();
        this.onChange(Array.from(this.selectedItems));
    }
    
    clearAll() {
        this.selectedItems.clear();
        this.renderOptions();
        this.renderSelected();
        this.updateTrigger();
        this.onChange(Array.from(this.selectedItems));
    }
    
    renderSelected() {
        this.selectedContainer.innerHTML = '';
        
        if (this.selectedItems.size === 0) {
            return;
        }
        
        const selectedItems = Array.from(this.selectedItems).map(id => 
            this.dataSource.find(item => item.id === id)
        ).filter(Boolean);
        
        // 显示前maxDisplayItems个，超出显示"等X个"
        const displayItems = selectedItems.slice(0, this.maxDisplayItems);
        const hiddenCount = selectedItems.length - this.maxDisplayItems;
        
        displayItems.forEach(item => {
            const tag = document.createElement('span');
            tag.className = 'badge bg-primary me-1 mb-1';
            tag.innerHTML = `${item.name} <i class="bi bi-x" style="cursor: pointer; margin-left: 4px;"></i>`;
            tag.addEventListener('click', (e) => {
                e.stopPropagation();
                this.removeItem(item.id);
            });
            this.selectedContainer.appendChild(tag);
        });
        
        if (hiddenCount > 0) {
            const moreTag = document.createElement('span');
            moreTag.className = 'badge bg-secondary me-1 mb-1';
            moreTag.textContent = `等${hiddenCount}个`;
            this.selectedContainer.appendChild(moreTag);
        }
    }
    
    removeItem(itemId) {
        this.selectedItems.delete(itemId);
        this.renderOptions();
        this.renderSelected();
        this.updateTrigger();
        this.onChange(Array.from(this.selectedItems));
    }
    
    updateTrigger() {
        const count = this.selectedItems.size;
        const countText = count > 0 ? `(${count})` : '';
        this.trigger.querySelector('.selected-count').textContent = `选择${this.placeholder} ${countText}`;
    }
    
    closeDropdown() {
        this.dropdown.classList.remove('show');
        this.isOpen = false;
        if (this.hoverTimeout) {
            clearTimeout(this.hoverTimeout);
        }
    }
    
    openDropdown() {
        this.dropdown.classList.add('show');
        this.isOpen = true;
        if (this.hoverTimeout) {
            clearTimeout(this.hoverTimeout);
        }
        
        // 计算下拉菜单位置
        this.positionDropdown();
    }
    
    positionDropdown() {
        const triggerRect = this.trigger.getBoundingClientRect();
        const dropdown = this.dropdown;
        
        // 设置下拉菜单位置
        dropdown.style.top = (triggerRect.bottom + window.scrollY + 4) + 'px';
        dropdown.style.left = (triggerRect.left + window.scrollX) + 'px';
        dropdown.style.width = triggerRect.width + 'px';
    }
    
    toggleDropdown() {
        if (this.isOpen) {
            this.closeDropdown();
        } else {
            this.openDropdown();
        }
    }
    
    getSelectedItems() {
        return Array.from(this.selectedItems);
    }
    
    setSelectedItems(itemIds) {
        this.selectedItems = new Set(itemIds);
        this.renderOptions();
        this.renderSelected();
        this.updateTrigger();
    }
    
    render() {
        this.renderOptions();
        this.renderSelected();
        this.updateTrigger();
    }
}

// 全局导出
window.SearchMultiSelect = SearchMultiSelect;
