/**
 * 按肖像筛选功能模块
 * 
 * 功能特点：
 * 1. 显示人物统计信息
 * 2. 肖像选择筛选
 * 3. 与照片库集成
 */

class PortraitFilterPanel {
    constructor() {
        this.clusters = [];
        this.selectedClusterId = 'all';
        this.isExpanded = false;
        // 分页显示状态
        this.displayedCount = 10; // 初始显示10个
        this.totalClusters = 0;
        this.maxClusters = 40; // 默认值，将在loadClusters中从配置读取
        this.minClusterSize = 1; // 默认值，将在loadClusters中从配置读取
        this.init();
    }
    
    async init() {
        await this.loadClusters();
        await this.updatePeopleStats();
        this.renderPortraits();
        this.bindEvents();
    }
    
    async loadClusters() {
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
            
            // 从配置获取参数
            if (window.userConfig?.face_recognition?.max_clusters) {
                this.maxClusters = window.userConfig.face_recognition.max_clusters;
                console.log('max_clusters:', this.maxClusters);
            }
            
            if (window.userConfig?.face_recognition?.min_cluster_size) {
                this.minClusterSize = window.userConfig.face_recognition.min_cluster_size;
                console.log('min_cluster_size:', this.minClusterSize);
            }
            
            const response = await fetch('/api/v1/face-clusters/clusters');
            const data = await response.json();
            this.clusters = data.clusters || [];
            
            // 获取总聚类数
            const statsResponse = await fetch('/api/v1/face-clusters/statistics');
            if (statsResponse.ok) {
                const statsData = await statsResponse.json();
                this.totalClusters = statsData.statistics?.total_clusters || this.clusters.length;
            } else {
                this.totalClusters = this.clusters.length;
            }
            
            console.log(`聚类加载完成: 获取到 ${this.clusters.length} 个聚类 (总数据: ${this.totalClusters} 个)`);
            
            // 🔥 修复：加载聚类数据后，同时刷新统计信息和UI
            await this.updatePeopleStats();
            this.renderPortraits();
            
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
        const container = grid?.parentElement;
        
        // 按人脸数量降序排序
        const sortedClusters = [...this.clusters].sort((a, b) => b.face_count - a.face_count);
        
        // 只显示前 displayCount 个
        const displayedClusters = sortedClusters.slice(0, this.displayedCount);
        
        let html = displayedClusters.map(cluster => `
            <div class="col-auto">
                <div class="portrait-card" data-cluster-id="${cluster.cluster_id}">
                    <div class="portrait-img-container">
                        <img src="${cluster.face_crop_url || '/static/images/placeholder.jpg'}" 
                             class="portrait-img" alt="${cluster.person_name || '未命名人物'}">
                    </div>
                    <span class="portrait-name">${cluster.person_name || '未命名人物'}</span>
                    <small class="portrait-count">(${cluster.face_count})</small>
                </div>
            </div>
        `).join('');
        
        // 添加操作按钮
        const remainingCount = this.totalClusters - this.displayedCount;
        const maxDisplayCount = Math.min(this.maxClusters, this.totalClusters);
        
        // 折回按钮：当显示数量超过10个时显示
        if (this.displayedCount > 10) {
            html += `
                <div class="col-auto">
                    <div class="portrait-card portrait-collapse" id="collapsePortraits" style="cursor: pointer; border: 2px dashed #ffc107; background-color: #fff8e1;" title="折回显示初始10个">
                        <div class="portrait-img-container" style="align-items: center; justify-content: center;">
                            <i class="bi bi-arrow-up" style="font-size: 2rem; color: #ffc107;"></i>
                        </div>
                        <span class="portrait-name" style="text-align: center; white-space: nowrap;">
                            折回<br><small class="text-warning">初始10个</small>
                        </span>
                    </div>
                </div>
            `;
        }
        
        // 加载更多按钮：当还有更多可加载时显示
        if (remainingCount > 0 && this.displayedCount < maxDisplayCount) {
            const nextBatch = Math.min(10, maxDisplayCount - this.displayedCount);
            html += `
                <div class="col-auto">
                    <div class="portrait-card portrait-load-more" id="loadMorePortraits" style="cursor: pointer; border: 2px dashed #dee2e6; background-color: #f8f9fa;" title="每次加载10个">
                        <div class="portrait-img-container" style="align-items: center; justify-content: center;">
                            <i class="bi bi-chevron-down" style="font-size: 2rem; color: #6c757d;"></i>
                        </div>
                        <span class="portrait-name" style="text-align: center; white-space: nowrap;">
                            加载更多<br><small class="text-muted">+${nextBatch}个</small>
                        </span>
                    </div>
                </div>
            `;
            
            // 显示全部按钮
            html += `
                <div class="col-auto">
                    <div class="portrait-card portrait-show-all" id="showAllPortraits" style="cursor: pointer; border: 2px dashed #0d6efd; background-color: #e7f1ff;" title="一次性显示全部">
                        <div class="portrait-img-container" style="align-items: center; justify-content: center;">
                            <i class="bi bi-grid-3x3-gap" style="font-size: 2rem; color: #0d6efd;"></i>
                        </div>
                        <span class="portrait-name" style="text-align: center; white-space: nowrap;">
                            显示全部<br><small class="text-primary">共${maxDisplayCount}个</small>
                        </span>
                    </div>
                </div>
            `;
        }
        
        grid.innerHTML = html;
        
        // 绑定按钮事件
        this.bindLoadMoreEvents();
    }
    
    bindLoadMoreEvents() {
        const loadMoreBtn = document.getElementById('loadMorePortraits');
        const showAllBtn = document.getElementById('showAllPortraits');
        const collapseBtn = document.getElementById('collapsePortraits');
        
        if (loadMoreBtn) {
            loadMoreBtn.addEventListener('click', () => {
                this.showMore(10);
            });
        }
        
        if (showAllBtn) {
            showAllBtn.addEventListener('click', () => {
                this.showAll();
            });
        }
        
        if (collapseBtn) {
            collapseBtn.addEventListener('click', () => {
                this.collapse();
            });
        }
    }
    
    showMore(increment = 10) {
        const maxDisplayCount = Math.min(this.maxClusters, this.totalClusters);
        this.displayedCount = Math.min(this.displayedCount + increment, maxDisplayCount);
        this.renderPortraits();
    }
    
    showAll() {
        this.displayedCount = Math.min(this.maxClusters, this.totalClusters);
        this.renderPortraits();
    }
    
    collapse() {
        // 折回到初始10个
        this.displayedCount = 10;
        this.renderPortraits();
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
                // 排除操作按钮
                if (portraitCard && 
                    !portraitCard.classList.contains('portrait-load-more') && 
                    !portraitCard.classList.contains('portrait-show-all') &&
                    !portraitCard.classList.contains('portrait-collapse')) {
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
        // 更新选中状态
        document.querySelectorAll('.portrait-card').forEach(card => {
            card.classList.remove('active');
        });
        document.querySelector(`[data-cluster-id="${clusterId}"]`).classList.add('active');
        
        // 执行筛选
        await this.filterPhotosByCluster(clusterId);
    }
    
    async filterPhotosByCluster(clusterId) {
        // 更新筛选条件
        if (window.AppState && window.AppState.searchFilters) {
            window.AppState.searchFilters.person_filter = clusterId;
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
        this.selectedClusterId = 'all';
        document.querySelectorAll('.portrait-card').forEach(card => {
            card.classList.remove('active');
        });
        
        if (window.AppState && window.AppState.searchFilters) {
            window.AppState.searchFilters.person_filter = 'all';
        }
        
        // 注意：不在这里重新加载照片，由调用方处理
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
