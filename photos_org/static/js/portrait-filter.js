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
            const response = await fetch('/api/v1/face-clusters/clusters');
            const data = await response.json();
            this.clusters = data.clusters || [];
            
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
        const html = this.clusters.map(cluster => `
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
        
        grid.innerHTML = html;
    }
    
    bindEvents() {
        // 切换展开/收起
        document.getElementById('portraitFilterToggle').addEventListener('click', () => {
            this.toggleExpanded();
        });
        
        // 肖像选择
        document.addEventListener('click', (e) => {
            const portraitCard = e.target.closest('.portrait-card');
            if (portraitCard) {
                const clusterId = portraitCard.dataset.clusterId;
                this.selectCluster(clusterId);
            }
        });
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
