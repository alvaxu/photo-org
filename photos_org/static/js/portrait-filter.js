/**
 * 按肖像筛选功能模块
 * 
 * 功能特点：
 * 1. 显示人物统计信息
 * 2. 肖像选择筛选
 * 3. 与照片库集成
 */

// JS文件版本号（与HTML中的?v=参数保持一致）
const PORTRAIT_FILTER_VERSION = '20250120_02';

class PortraitFilterPanel {
    constructor() {
        this.clusters = [];
        this.selectedClusterIds = []; // 改为数组，支持多选
        this.isExpanded = false;
        // 分页显示状态
        this.currentPage = 1; // 当前页码
        this.pageSize = 12; // 每页显示数量，默认12，将从配置读取
        this.totalClusters = 0; // 总聚类数
        this.totalPages = 0; // 总页数
        this.init();
    }
    
    async init() {
        await this.loadClusters();
        await this.updatePeopleStats();
        this.renderPortraits();
        this.bindEvents();
    }
    
    async loadClusters(page = 1) {
        try {
            // 🔥 先加载用户配置（如果没有加载）
            if (!window.userConfig) {
                try {
                    const configResponse = await fetch('/api/v1/config/user');
                    if (configResponse.ok) {
                        const configResult = await configResponse.json();
                        if (configResult.success) {
                            window.userConfig = configResult.data;
                            console.log('配置加载成功:', window.userConfig);
                        }
                    }
                } catch (e) {
                    console.warn('加载配置失败，使用默认值:', e);
                }
            }
            
            // 从配置获取每页显示数量（复用照片分页配置）
            if (window.userConfig?.ui?.photos_per_page) {
                this.pageSize = window.userConfig.ui.photos_per_page;
                console.log('portraits pageSize:', this.pageSize);
            }
            
            // 计算分页参数
            const offset = (page - 1) * this.pageSize;
            const limit = this.pageSize;
            
            // 调用API获取当前页数据
            const response = await fetch(`/api/v1/face-clusters/clusters?limit=${limit}&offset=${offset}`);
            const data = await response.json();
            this.clusters = data.clusters || [];
            
            // 获取总聚类数
            const statsResponse = await fetch('/api/v1/face-clusters/statistics');
            if (statsResponse.ok) {
                const statsData = await statsResponse.json();
                this.totalClusters = statsData.statistics?.total_clusters || data.total || 0;
            } else {
                this.totalClusters = data.total || this.clusters.length;
            }
            
            // 计算总页数
            this.totalPages = Math.ceil(this.totalClusters / this.pageSize);
            this.currentPage = page;
            
            console.log(`聚类加载完成: 第 ${page} 页，获取到 ${this.clusters.length} 个聚类 (总数据: ${this.totalClusters} 个，共 ${this.totalPages} 页)`);
            
            // 🔥 修复：加载聚类数据后，同时刷新统计信息和UI
            await this.updatePeopleStats();
            this.renderPortraits();
            this.renderPortraitPagination();
            this.renderPortraitPaginationInfo();
            
        } catch (error) {
            console.error('加载聚类数据失败:', error);
            this.clusters = [];
        }
    }
    
    async updatePeopleStats() {
        try {
            // 获取聚类统计信息
            const clustersResponse = await fetch('/api/v1/face-clusters/statistics');
            if (clustersResponse.ok) {
                const clustersData = await clustersResponse.json();
                const stats = clustersData.statistics;
                
                // 使用API返回的准确统计数据
                document.getElementById('totalPeopleCount').textContent = stats.total_clusters;
                document.getElementById('labeledPeopleCount').textContent = stats.labeled_clusters;
                document.getElementById('unlabeledPeopleCount').textContent = stats.unlabeled_clusters;
                document.getElementById('totalFacesCount').textContent = stats.total_faces;
            } else {
                // 如果API失败，回退到本地计算
                this.updatePeopleStatsLocal();
            }
        } catch (error) {
            console.error('获取统计信息失败:', error);
            // 如果API失败，回退到本地计算
            this.updatePeopleStatsLocal();
        }
    }
    
    updatePeopleStatsLocal() {
        // 回退方法：使用本地聚类数据计算（可能不准确）
        const totalClusters = this.clusters.length;
        const labeledClusters = this.clusters.filter(c => c.is_labeled).length;
        const unlabeledClusters = totalClusters - labeledClusters;
        const totalFaces = this.clusters.reduce((sum, c) => sum + c.face_count, 0);
        
        // 更新统计显示
        document.getElementById('totalPeopleCount').textContent = totalClusters;
        document.getElementById('labeledPeopleCount').textContent = labeledClusters;
        document.getElementById('unlabeledPeopleCount').textContent = unlabeledClusters;
        document.getElementById('totalFacesCount').textContent = totalFaces;
    }
    
    renderPortraits() {
        const grid = document.getElementById('portraitFilterGrid');
        if (!grid) {
            console.error('肖像网格容器未找到');
            return;
        }
        
        // 后端已按face_count降序排序，直接渲染当前页数据
        let html = this.clusters.map(cluster => {
            const isSelected = this.selectedClusterIds.includes(cluster.cluster_id);
            const selectedClass = isSelected ? 'selected' : '';
            const checkmarkIcon = isSelected ? '<i class="bi bi-check-circle-fill checkmark-icon"></i>' : '';
            return `
            <div class="col-auto">
                <div class="portrait-card ${selectedClass}" data-cluster-id="${cluster.cluster_id}">
                    <div class="portrait-img-container">
                        ${checkmarkIcon}
                        <img src="${cluster.face_crop_url || '/static/images/placeholder.jpg'}" 
                             class="portrait-img" alt="${cluster.person_name || '未命名人物'}">
                    </div>
                    <span class="portrait-name">${cluster.person_name || '未命名人物'}</span>
                    <small class="portrait-count">(${cluster.face_count})</small>
                </div>
            </div>
        `;
        }).join('');
        
        // 如果没有数据，显示提示
        if (this.clusters.length === 0) {
            html = `
                <div class="col-12 text-center py-4">
                    <p class="text-muted mb-0">暂无人物数据</p>
                </div>
            `;
        }
        
        grid.innerHTML = html;
        
        // 更新选中状态UI（因为重新渲染了HTML）
        this.updateSelectionUI();
    }
    
    renderPortraitPagination() {
        const paginationContainer = document.getElementById('portraitPaginationContainer');
        const pagination = document.getElementById('portraitPagination');
        
        if (!paginationContainer || !pagination) {
            console.warn('分页容器未找到');
            return;
        }
        
        // 如果只有一页或没有数据，隐藏分页控件
        if (this.totalPages <= 1) {
            paginationContainer.classList.add('d-none');
            return;
        }
        
        paginationContainer.classList.remove('d-none');
        
        let html = '';
        
        // 上一页
        if (this.currentPage > 1) {
            html += `<li class="page-item">
                <a class="page-link" href="#" data-page="${this.currentPage - 1}">
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
        if (this.currentPage > 3) {
            html += `<li class="page-item">
                <a class="page-link" href="#" data-page="1">1</a>
            </li>`;
            if (this.currentPage > 4) {
                html += `<li class="page-item disabled">
                    <span class="page-link">...</span>
                </li>`;
            }
        }
        
        // 页码
        const startPage = Math.max(1, this.currentPage - 2);
        const endPage = Math.min(this.totalPages, this.currentPage + 2);
        
        for (let i = startPage; i <= endPage; i++) {
            const activeClass = i === this.currentPage ? 'active' : '';
            html += `<li class="page-item ${activeClass}">
                <a class="page-link" href="#" data-page="${i}">${i}</a>
            </li>`;
        }
        
        // 最后一页
        if (this.currentPage < this.totalPages - 2) {
            if (this.currentPage < this.totalPages - 3) {
                html += `<li class="page-item disabled">
                    <span class="page-link">...</span>
                </li>`;
            }
            html += `<li class="page-item">
                <a class="page-link" href="#" data-page="${this.totalPages}">${this.totalPages}</a>
            </li>`;
        }
        
        // 下一页
        if (this.currentPage < this.totalPages) {
            html += `<li class="page-item">
                <a class="page-link" href="#" data-page="${this.currentPage + 1}">
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
        
        pagination.innerHTML = html;
        
        // 绑定分页事件
        this.bindPortraitPaginationEvents();
    }
    
    renderPortraitPaginationInfo() {
        const paginationInfo = document.getElementById('portraitPaginationInfo');
        const paginationText = document.getElementById('portraitPaginationText');
        
        if (!paginationInfo) {
            return;
        }
        
        // 如果只有一页或没有数据，隐藏分页信息
        if (this.totalPages <= 1) {
            paginationInfo.classList.add('d-none');
            return;
        }
        
        paginationInfo.classList.remove('d-none');
        
        const startCluster = (this.currentPage - 1) * this.pageSize + 1;
        const endCluster = Math.min(this.currentPage * this.pageSize, this.totalClusters);
        
        if (paginationText) {
            paginationText.textContent = `第 ${this.currentPage} 页，共 ${this.totalPages} 页 (显示 ${startCluster}-${endCluster} 个，共 ${this.totalClusters} 个人物)`;
        }
    }
    
    bindPortraitPaginationEvents() {
        const pagination = document.getElementById('portraitPagination');
        if (!pagination) {
            return;
        }
        
        pagination.querySelectorAll('.page-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = parseInt(e.target.dataset.page || e.target.closest('.page-link').dataset.page);
                if (page && page !== this.currentPage && page >= 1 && page <= this.totalPages) {
                    this.goToPage(page);
                }
            });
        });
    }
    
    goToPage(page) {
        if (page < 1 || page > this.totalPages) {
            return;
        }
        this.loadClusters(page);
    }
    
    bindEvents() {
        // 切换展开/收起
        document.getElementById('portraitFilterToggle').addEventListener('click', () => {
            this.toggleExpanded();
        });
        
        // 使用事件委托处理肖像选择（避免重复绑定）
        const grid = document.getElementById('portraitFilterGrid');
        if (grid) {
            grid.addEventListener('click', (e) => {
                const portraitCard = e.target.closest('.portrait-card');
                if (portraitCard) {
                    const clusterId = portraitCard.dataset.clusterId;
                    if (clusterId) {
                        this.selectCluster(clusterId);
                    }
                }
            });
        }
    }
    
    toggleExpanded() {
        const content = document.getElementById('portraitFilterContent');
        const icon = document.querySelector('#portraitFilterToggle i');
        const button = document.getElementById('portraitFilterToggle');
        
        if (this.isExpanded) {
            content.classList.remove('show');
            icon.className = 'bi bi-chevron-down';
            button.innerHTML = '<i class="bi bi-chevron-down"></i> 点击展开';
        } else {
            content.classList.add('show');
            icon.className = 'bi bi-chevron-up';
            button.innerHTML = '<i class="bi bi-chevron-up"></i> 点击收起';
        }
        
        this.isExpanded = !this.isExpanded;
    }
    
    async selectCluster(clusterId) {
        // 切换选中状态（支持多选）
        const index = this.selectedClusterIds.indexOf(clusterId);
        if (index > -1) {
            // 已选中，取消选中
            this.selectedClusterIds.splice(index, 1);
        } else {
            // 未选中，添加到选中列表
            this.selectedClusterIds.push(clusterId);
        }
        
        // 更新UI显示
        this.updateSelectionUI();
        
        // 执行筛选
        await this.filterPhotosByCluster();
    }
    
    updateSelectionUI() {
        // 更新所有肖像卡的选中状态
        document.querySelectorAll('.portrait-card').forEach(card => {
            const clusterId = card.dataset.clusterId;
            const isSelected = this.selectedClusterIds.includes(clusterId);
            if (isSelected) {
                card.classList.add('selected');
                // 添加选中标记图标（如果还没有）
                const imgContainer = card.querySelector('.portrait-img-container');
                if (imgContainer && !imgContainer.querySelector('.checkmark-icon')) {
                    const checkmark = document.createElement('i');
                    checkmark.className = 'bi bi-check-circle-fill checkmark-icon';
                    imgContainer.insertBefore(checkmark, imgContainer.firstChild);
                }
            } else {
                card.classList.remove('selected');
                // 移除选中标记图标
                const checkmark = card.querySelector('.checkmark-icon');
                if (checkmark) {
                    checkmark.remove();
                }
            }
        });
        
        // 更新已选数量提示
        this.updateSelectedCountHint();
    }
    
    updateSelectedCountHint() {
        const count = this.selectedClusterIds.length;
        let hintElement = document.getElementById('selectedPortraitsHint');
        
        if (count > 0) {
            if (!hintElement) {
                // 创建提示元素
                const container = document.getElementById('portraitFilterContent');
                if (container) {
                    hintElement = document.createElement('div');
                    hintElement.id = 'selectedPortraitsHint';
                    hintElement.className = 'alert alert-info mb-2';
                    hintElement.style.marginBottom = '0.5rem';
                    container.insertBefore(hintElement, container.firstChild);
                }
            }
            
            if (hintElement) {
                // 需要从所有页面查找选中的人物名称（因为当前页可能不包含所有选中的人物）
                // 这里只显示当前页中选中的人物，其他页的用"..."表示
                const currentPageSelected = this.selectedClusterIds.filter(id => 
                    this.clusters.some(c => c.cluster_id === id)
                );
                const otherPagesCount = count - currentPageSelected.length;
                
                let clustersInfo = currentPageSelected.map(id => {
                    const cluster = this.clusters.find(c => c.cluster_id === id);
                    return cluster ? (cluster.person_name || '未命名人物') : id;
                }).join('、');
                
                if (otherPagesCount > 0) {
                    clustersInfo += ` 等${count}个`;
                }
                
                hintElement.innerHTML = `
                    <i class="bi bi-people-fill me-2"></i>
                    <strong>已选 ${count} 个人物：</strong>${clustersInfo}
                    <button class="btn btn-sm btn-outline-danger ms-2" onclick="window.portraitFilterPanel.clearFilter()">
                        <i class="bi bi-x-circle"></i> 清除
                    </button>
                `;
                hintElement.style.display = 'block';
            }
        } else {
            // 没有选中，隐藏提示
            if (hintElement) {
                hintElement.style.display = 'none';
            }
        }
    }
    
    async filterPhotosByCluster() {
        // 更新筛选条件（支持多选：使用逗号分隔）
        if (window.AppState && window.AppState.searchFilters) {
            if (this.selectedClusterIds.length === 0) {
                // 没有选中，显示所有照片
                window.AppState.searchFilters.person_filter = 'all';
            } else if (this.selectedClusterIds.length === 1) {
                // 单个选中，向后兼容
                window.AppState.searchFilters.person_filter = this.selectedClusterIds[0];
            } else {
                // 多个选中，使用逗号分隔（AND关系：显示同时包含所有选中人物的照片）
                window.AppState.searchFilters.person_filter = this.selectedClusterIds.join(',');
            }
        }
        
        // 重新加载照片和统计
        if (typeof window.loadPhotos === 'function') {
            await window.loadPhotos(1);
        }
        if (typeof window.loadStats === 'function') {
            await window.loadStats();
        }
        if (typeof window.updateFilterStatus === 'function') {
            window.updateFilterStatus();
        }
    }
    
    // 清除筛选
    clearFilter() {
        this.selectedClusterIds = [];
        this.updateSelectionUI();
        
        if (window.AppState && window.AppState.searchFilters) {
            window.AppState.searchFilters.person_filter = 'all';
        }
        
        // 重新加载照片和统计
        if (typeof window.loadPhotos === 'function') {
            window.loadPhotos(1);
        }
        if (typeof window.loadStats === 'function') {
            window.loadStats();
        }
        if (typeof window.updateFilterStatus === 'function') {
            window.updateFilterStatus();
        }
    }
}

// 全局实例
let portraitFilterPanel = null;

// 初始化函数
function initPortraitFilter() {
    portraitFilterPanel = new PortraitFilterPanel();
    // 更新全局引用
    window.portraitFilterPanel = portraitFilterPanel;
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    initPortraitFilter();
});

// 导出到全局
window.initPortraitFilter = initPortraitFilter;

// 注册版本号（用于版本检测）
if (typeof window.registerJSVersion === 'function') {
    window.registerJSVersion('portrait-filter.js', PORTRAIT_FILTER_VERSION);
}
