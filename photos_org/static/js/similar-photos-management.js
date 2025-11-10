/**
 * 相似照识别管理模块 - 独立页面版本
 * 
 * 功能特点：
 * 1. 相似照片聚类展示和管理
 * 2. 聚类照片浏览
 * 3. 聚类生成任务管理
 * 4. 参考人物管理页面的实现
 */

// 全局配置
const SIMILAR_PHOTOS_CONFIG = {
    IMAGE_PLACEHOLDER: '/static/images/placeholder.jpg'
};

// 初始化elements对象（如果不存在）
function initializeElements() {
    if (typeof window.elements === 'undefined') {
        window.elements = {
            photoModal: document.getElementById('photoModal')
        };
    }
}

// 在DOM加载完成后初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeElements);
} else {
    initializeElements();
}

class SimilarPhotosManagement {
    constructor() {
        this.clustersData = [];
        this.statistics = {};
        this.clusterPhotosModal = null; // 保存模态框实例引用
        
        // 分页状态
        this.currentPage = 1;
        this.totalPages = 1;
        this.totalClusters = 0;
        this.pageSize = 30; // 默认值，将从配置中加载
        
        // 不在这里调用init，改为在DOMContentLoaded中调用
    }

    async init() {
        await this.loadPageSize();
        this.bindEvents();
        this.loadClustersData();
    }

    async loadPageSize() {
        /**
         * 从用户配置加载每页显示数量
         */
        try {
            const response = await fetch('/api/v1/config/user');
            const data = await response.json();
            if (data.success && data.data && data.data.ui && data.data.ui.photos_per_page) {
                this.pageSize = data.data.ui.photos_per_page;
                console.log('加载分页配置成功:', this.pageSize);
            } else {
                console.warn('配置中未找到photos_per_page，使用默认值:', this.pageSize);
            }
        } catch (error) {
            console.warn('加载分页配置失败，使用默认值:', error);
            // 使用默认值
        }
    }

    bindEvents() {
        // 刷新按钮
        document.getElementById('refreshClustersBtn')?.addEventListener('click', () => {
            this.loadClustersData(this.currentPage);
        });

        // 开始聚类按钮
        document.getElementById('startClusterBtn')?.addEventListener('click', () => {
            this.startClustering();
        });

        document.getElementById('startClusterFirstBtn')?.addEventListener('click', () => {
            this.startClustering();
        });

        // 图像特征提取按钮事件
        const imageFeatureExtractionBtn = document.getElementById('imageFeatureExtractionBtn');
        if (imageFeatureExtractionBtn) {
            imageFeatureExtractionBtn.addEventListener('click', () => {
                if (typeof window.showImageFeatureExtractionModal === 'function') {
                    window.showImageFeatureExtractionModal();
                } else {
                    console.warn('图像特征提取功能尚未加载');
                    alert('图像特征提取功能尚未加载，请刷新页面重试');
                }
            });
        }
        
        // 图像特征提取开始按钮事件
        const startFeatureExtractionBtn = document.getElementById('startFeatureExtractionBtn');
        if (startFeatureExtractionBtn) {
            startFeatureExtractionBtn.addEventListener('click', () => {
                if (typeof window.startImageFeatureExtraction === 'function') {
                    window.startImageFeatureExtraction();
                } else {
                    console.warn('图像特征提取功能尚未加载');
                    alert('图像特征提取功能尚未加载，请刷新页面重试');
                }
            });
        }
    }

    async loadClustersData(page = 1) {
        try {
            this.showLoadingState();
            
            // 确保配置已加载
            if (this.pageSize === 30) {
                // 如果还是默认值，尝试重新加载配置
                await this.loadPageSize();
            }
            
            // 计算offset
            const offset = (page - 1) * this.pageSize;
            
            console.log('加载聚类数据:', { page, pageSize: this.pageSize, offset });
            
            // 并行加载统计信息和聚类数据
            const [statisticsResponse, clustersResponse] = await Promise.all([
                fetch('/api/v1/similar-photos-clusters/statistics'),
                fetch(`/api/v1/similar-photos-clusters/clusters?limit=${this.pageSize}&offset=${offset}`)
            ]);

            if (!statisticsResponse.ok || !clustersResponse.ok) {
                throw new Error('API请求失败');
            }

            const statisticsData = await statisticsResponse.json();
            const clustersData = await clustersResponse.json();

            this.statistics = statisticsData.statistics || {};
            this.clustersData = clustersData.clusters || [];
            this.totalClusters = clustersData.total || 0;
            this.currentPage = page;
            this.totalPages = Math.ceil(this.totalClusters / this.pageSize);

            this.updateStatistics();
            this.renderClusterCards();
            this.renderPagination();
            this.renderPaginationInfo();
            
            // 只有在有数据时才调用hideLoadingState（空状态时renderClusterCards已经调用了showEmptyState）
            if (this.clustersData.length > 0) {
                this.hideLoadingState();
            }
            // 如果数据为空，renderClusterCards已经调用了showEmptyState，不需要再调用hideLoadingState
            
            // 恢复按钮状态（如果之前被禁用）
            this.enableClusterButtons();

        } catch (error) {
            console.error('加载聚类数据失败:', error);
            this.showErrorState('加载聚类数据失败: ' + error.message);
            // 恢复按钮状态
            this.enableClusterButtons();
        }
    }
    
    enableClusterButtons() {
        /**恢复聚类按钮状态*/
        const startBtn = document.getElementById('startClusterBtn');
        const startFirstBtn = document.getElementById('startClusterFirstBtn');
        
        if (startBtn) {
            startBtn.disabled = false;
            startBtn.innerHTML = '<i class="bi bi-diagram-3"></i> 开始聚类';
        }
        if (startFirstBtn) {
            startFirstBtn.disabled = false;
            startFirstBtn.innerHTML = '<i class="bi bi-diagram-3 me-2"></i>开始聚类';
        }
    }

    updateStatistics() {
        // 更新统计数字
        document.getElementById('totalClustersCount').textContent = this.statistics.total_clusters || 0;
        document.getElementById('totalPhotosInClusters').textContent = this.statistics.total_photos || 0;
        document.getElementById('highQualityClustersCount').textContent = this.statistics.high_quality_clusters || 0;
        document.getElementById('avgSimilarity').textContent = this.statistics.avg_similarity 
            ? (this.statistics.avg_similarity * 100).toFixed(1) 
            : '-';
        document.getElementById('clustersCount').textContent = this.statistics.total_clusters || 0;
    }

    renderClusterCards() {
        const clustersList = document.getElementById('clustersList');
        if (!clustersList) return;

        if (this.clustersData.length === 0) {
            this.showEmptyState();
            return;
        }

        // 按照片数量排序
        const sortedClusters = [...this.clustersData].sort((a, b) => b.photo_count - a.photo_count);

        clustersList.innerHTML = sortedClusters.map(cluster => this.createClusterCard(cluster)).join('');
    }

    createClusterCard(cluster) {
        const photoCount = cluster.photo_count || 0;
        const quality = cluster.cluster_quality || 'low';
        const avgSimilarity = cluster.avg_similarity || 0;
        const clusterId = cluster.cluster_id;

        // 质量标签颜色
        const qualityColor = quality === 'high' ? 'success' : quality === 'medium' ? 'warning' : 'secondary';
        const qualityText = quality === 'high' ? '高质量' : quality === 'medium' ? '中等质量' : '低质量';

        // 获取第一张照片作为预览（如果photoCount为0，使用占位图）
        const previewPhoto = (photoCount > 0 && cluster.preview_photo) ? cluster.preview_photo : null;
        let previewUrl = SIMILAR_PHOTOS_CONFIG.IMAGE_PLACEHOLDER;
        let previewPhotoId = null;
        if (previewPhoto) {
            previewPhotoId = previewPhoto.id;
            const path = previewPhoto.thumbnail_path || previewPhoto.original_path;
            if (path) {
                // 确保路径被正确转义：先转换为正斜杠
                previewUrl = `/photos_storage/${String(path).replace(/\\/g, '/')}`;
            }
        }

        return `
            <div class="col-lg-2 col-md-4 col-sm-6 mb-3">
                <div class="card h-100 cluster-card" data-cluster-id="${clusterId}">
                    <div class="card-body">
                        <div class="mb-3 photo-image-container" style="position: relative;">
                            <img src="${previewUrl}" 
                                 class="photo-image rounded" 
                                 style="width: 100%; height: 150px; object-fit: contain; object-position: center; cursor: pointer;"
                                 alt="聚类预览"
                                 ${previewPhotoId ? `onclick="if(typeof viewPhotoDetail === 'function') { viewPhotoDetail(${previewPhotoId}); }"` : ''}
                                 onerror="this.src='${SIMILAR_PHOTOS_CONFIG.IMAGE_PLACEHOLDER}'">
                        </div>
                        <div class="d-flex align-items-center gap-2 mb-2">
                            <span class="badge bg-${qualityColor}">${qualityText}</span>
                            <span class="badge bg-info">${photoCount} 张照片</span>
                        </div>
                        <small class="text-muted d-block mb-2">
                            平均相似度: ${(avgSimilarity * 100).toFixed(1)}%
                        </small>
                        
                        <div class="d-flex gap-1">
                            <button class="btn btn-sm btn-outline-primary flex-fill" onclick="similarPhotosManagement.viewClusterPhotos('${clusterId}')">
                                <i class="bi bi-images me-1"></i>查看照片
                            </button>
                            <button class="btn btn-sm btn-outline-danger flex-fill" onclick="similarPhotosManagement.deleteCluster('${clusterId}')">
                                <i class="bi bi-trash me-1"></i>删除聚类
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    async startClustering() {
        if (!confirm('确定要开始相似照片聚类分析吗？这将重新分析所有已提取特征的照片。')) {
            return;
        }

        // 禁用按钮，防止重复点击
        const startBtn = document.getElementById('startClusterBtn');
        const startFirstBtn = document.getElementById('startClusterFirstBtn');
        
        if (startBtn) {
            startBtn.disabled = true;
            startBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> 聚类中...';
        }
        if (startFirstBtn) {
            startFirstBtn.disabled = true;
            startFirstBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> 聚类中...';
        }

        // 立即显示进度条
        const progressContainer = document.getElementById('clusterProgress');
        const progressBar = document.getElementById('clusterProgressBar');
        const statusText = document.getElementById('clusterStatus');
        const detailsText = document.getElementById('clusterDetails');
        
        if (progressContainer) {
            progressContainer.classList.remove('d-none');
        }
        if (progressBar) {
            progressBar.style.width = '5%';
            progressBar.setAttribute('aria-valuenow', 5);
        }
        if (statusText) {
            statusText.textContent = '正在启动聚类分析...';
        }
        if (detailsText) {
            detailsText.textContent = '请稍候...';
        }

        try {
            const response = await fetch('/api/v1/search/similar-photos/cluster', {
                method: 'POST'
            });

            const data = await response.json();

            if (response.ok && data.success && data.task_id) {
                // 更新进度
                if (progressBar) {
                    progressBar.style.width = '10%';
                    progressBar.setAttribute('aria-valuenow', 10);
                }
                if (statusText) {
                    statusText.textContent = '聚类任务已启动，正在处理...';
                }
                
                // 开始轮询任务状态
                this.pollClusterTaskStatus(data.task_id);
            } else {
                // 隐藏进度条
                if (progressContainer) {
                    progressContainer.classList.add('d-none');
                }
                alert('启动聚类分析失败: ' + (data.message || '未知错误'));
                // 恢复按钮状态
                this.enableClusterButtons();
            }
        } catch (error) {
            console.error('启动聚类分析失败:', error);
            // 隐藏进度条
            if (progressContainer) {
                progressContainer.classList.add('d-none');
            }
            alert('启动聚类分析失败: ' + error.message);
            // 恢复按钮状态
            this.enableClusterButtons();
        }
    }

    async pollClusterTaskStatus(taskId) {
        /**
         * 轮询聚类任务状态，直到完成或失败
         */
        const maxAttempts = 900; // 最多轮询900次（30分钟，每次2秒）
        let attempts = 0;
        
        // 显示进度条
        const progressContainer = document.getElementById('clusterProgress');
        const progressBar = document.getElementById('clusterProgressBar');
        const statusText = document.getElementById('clusterStatus');
        const detailsText = document.getElementById('clusterDetails');
        
        if (progressContainer) {
            progressContainer.classList.remove('d-none');
        }
        
        const poll = async () => {
            try {
                const response = await fetch(`/api/v1/search/similar-photos/cluster/status/${taskId}`);
                const data = await response.json();
                
                if (!response.ok || !data.success) {
                    console.error('获取任务状态失败:', data.message);
                    if (attempts >= maxAttempts) {
                        alert('聚类任务状态查询超时，请手动刷新页面查看结果。');
                        this.enableClusterButtons();
                        if (progressContainer) {
                            progressContainer.classList.add('d-none');
                        }
                        return;
                    }
                    // 继续轮询
                    attempts++;
                    setTimeout(poll, 2000);
                    return;
                }
                
                const status = data.status;
                
                // 更新进度显示
                if (progressBar && data.progress_percentage !== undefined) {
                    const progress = Math.min(data.progress_percentage || 0, 100);
                    progressBar.style.width = `${progress}%`;
                    progressBar.setAttribute('aria-valuenow', progress);
                }
                
                if (statusText && data.message) {
                    statusText.textContent = data.message;
                }
                
                // 更新详细信息
                if (detailsText) {
                    let details = '';
                    if (data.current_stage === 'initial_clustering') {
                        details = `初始聚类阶段 - 总照片数: ${data.total_photos || 0}`;
                    } else if (data.current_stage === 'refining') {
                        const iteration = data.refining_iteration || 0;
                        const processed = data.refining_processed_clusters || 0;
                        const total = data.refining_total_clusters || 0;
                        details = `第 ${iteration} 次迭代 - 已处理 ${processed}/${total} 个大聚类`;
                    }
                    if (data.cluster_count !== undefined) {
                        details += details ? ` | 已创建 ${data.cluster_count} 个聚类` : `已创建 ${data.cluster_count} 个聚类`;
                    }
                    if (data.refined_count !== undefined && data.refined_count > 0) {
                        details += ` | 已细分 ${data.refined_count} 个大聚类`;
                    }
                    detailsText.textContent = details || '请稍候...';
                }
                
                if (status === 'completed') {
                    // 任务完成，刷新聚类列表
                    console.log('聚类任务完成:', data.message);
                    
                    // 更新最终进度
                    if (progressBar) {
                        progressBar.style.width = '100%';
                        progressBar.setAttribute('aria-valuenow', 100);
                    }
                    if (statusText) {
                        statusText.textContent = '聚类分析完成！';
                    }
                    if (detailsText) {
                        detailsText.textContent = `共创建 ${data.cluster_count || 0} 个聚类，细分 ${data.refined_count || 0} 个大聚类`;
                    }
                    
                    // 延迟隐藏进度条并刷新数据
                    setTimeout(async () => {
                        if (progressContainer) {
                            progressContainer.classList.add('d-none');
                        }
                        await this.loadClustersData(1); // 聚类完成后回到第一页
                        alert('聚类分析完成！' + (data.message || ''));
                        this.enableClusterButtons();
                    }, 1500);
                } else if (status === 'failed') {
                    // 任务失败
                    console.error('聚类任务失败:', data.message);
                    if (progressContainer) {
                        progressContainer.classList.add('d-none');
                    }
                    alert('聚类分析失败: ' + (data.message || '未知错误'));
                    this.enableClusterButtons();
                } else if (status === 'processing') {
                    // 任务进行中，继续轮询
                    if (attempts >= maxAttempts) {
                        alert('聚类任务超时，请手动刷新页面查看结果。');
                        if (progressContainer) {
                            progressContainer.classList.add('d-none');
                        }
                        this.enableClusterButtons();
                        return;
                    }
                    attempts++;
                    setTimeout(poll, 2000);
                } else if (status === 'not_found') {
                    // 任务不存在（可能已完成并清理）
                    console.warn('任务状态不存在，可能已完成，刷新页面查看结果');
                    if (progressContainer) {
                        progressContainer.classList.add('d-none');
                    }
                    await this.loadClustersData(1); // 回到第一页
                    this.enableClusterButtons();
                }
            } catch (error) {
                console.error('轮询任务状态失败:', error);
                if (attempts >= maxAttempts) {
                    alert('聚类任务状态查询超时，请手动刷新页面查看结果。');
                    if (progressContainer) {
                        progressContainer.classList.add('d-none');
                    }
                    this.enableClusterButtons();
                    return;
                }
                attempts++;
                setTimeout(poll, 2000);
            }
        };
        
        // 开始轮询
        poll();
    }

    async viewClusterPhotos(clusterId) {
        // 获取或创建模态框实例（复用现有实例，避免重复创建）
        const modalElement = document.getElementById('clusterPhotosModal');
        if (!modalElement) {
            console.error('聚类照片模态框未找到');
            return;
        }
        
        // 如果已有实例，复用；否则创建新实例
        if (!this.clusterPhotosModal) {
            this.clusterPhotosModal = new bootstrap.Modal(modalElement);
            
            // 🔥 监听模态框关闭事件，确保清理遮罩层
            modalElement.addEventListener('hidden.bs.modal', () => {
                // 延迟清理，确保Bootstrap已经完成清理
                setTimeout(() => {
                    this.cleanupModalBackdrop();
                }, 100);
            });
        }
        
        const container = document.getElementById('clusterPhotosContainer');
        const loading = document.getElementById('clusterPhotosLoading');
        
        // 显示模态框
        this.clusterPhotosModal.show();
        container.innerHTML = '';
        loading.style.display = 'block';

        try {
            const response = await fetch(`/api/v1/similar-photos-clusters/clusters/${clusterId}/photos`);
            const data = await response.json();

            if (response.ok && data.success) {
                loading.style.display = 'none';
                const photos = data.photos || [];
                
                if (photos.length === 0) {
                    container.innerHTML = '<div class="col-12 text-center py-5"><p class="text-muted">该聚类中没有照片</p></div>';
                } else {
                    // 为每张照片添加cluster_id，以便删除时使用
                    const photosWithClusterId = photos.map(photo => ({
                        ...photo,
                        cluster_id: clusterId
                    }));
                    container.innerHTML = photosWithClusterId.map(photo => this.createPhotoCard(photo)).join('');
                }
            } else {
                loading.style.display = 'none';
                container.innerHTML = '<div class="col-12 text-center py-5"><p class="text-danger">加载照片失败: ' + (data.message || '未知错误') + '</p></div>';
            }
        } catch (error) {
            console.error('加载聚类照片失败:', error);
            loading.style.display = 'none';
            container.innerHTML = '<div class="col-12 text-center py-5"><p class="text-danger">加载照片失败: ' + error.message + '</p></div>';
        }
    }

    createPhotoCard(photo) {
        // 安全地处理路径，避免转义序列问题
        let thumbnailUrl = SIMILAR_PHOTOS_CONFIG.IMAGE_PLACEHOLDER;
        if (photo.thumbnail_path) {
            thumbnailUrl = `/photos_storage/${String(photo.thumbnail_path).replace(/\\/g, '/')}`;
        } else if (photo.original_path) {
            thumbnailUrl = `/photos_storage/${String(photo.original_path).replace(/\\/g, '/')}`;
        }
        
        const similarity = photo.similarity_score ? (photo.similarity_score * 100).toFixed(1) : '-';
        const filename = String(photo.filename || '').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
        const photoId = photo.photo_id || photo.id;
        const clusterId = photo.cluster_id || '';

        return `
            <div class="col-md-3 col-sm-4 col-6">
                <div class="card">
                    <div class="photo-image-container" style="position: relative;">
                        <img src="${thumbnailUrl}" 
                             class="photo-image" 
                             style="width: 100%; height: 200px; object-fit: contain; object-position: center; cursor: pointer;"
                             alt="${filename}"
                             ${photoId ? `onclick="if(typeof viewPhotoDetail === 'function') { viewPhotoDetail(${photoId}); }"` : ''}
                             onerror="this.src='${SIMILAR_PHOTOS_CONFIG.IMAGE_PLACEHOLDER}'">
                    </div>
                    <div class="card-body p-2">
                        <div class="d-flex justify-content-between align-items-center">
                            <small class="text-muted text-truncate flex-grow-1 me-2" title="${filename}">${filename}</small>
                            ${photoId ? `
                            <button class="btn btn-link btn-sm p-0 text-danger" 
                                    onclick="event.stopPropagation(); similarPhotosManagement.deletePhotoFromCluster(${photoId}, '${clusterId}')" 
                                    title="删除照片"
                                    style="flex-shrink: 0; min-width: 24px; padding: 0;">
                                <i class="bi bi-trash"></i>
                            </button>
                            ` : ''}
                        </div>
                        <small class="text-muted d-block mt-1">相似度: ${similarity}%</small>
                    </div>
                </div>
            </div>
        `;
    }

    async deletePhotoFromCluster(photoId, clusterId) {
        if (!confirm('确定要删除这张照片吗？此操作不可恢复。')) {
            return;
        }

        try {
            // 删除照片（后端会自动清理聚类关系，如果只剩1张或0张则删除聚类）
            const response = await fetch(`/api/v1/photos/${photoId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '删除照片失败');
            }

            // 检查聚类是否还存在（通过尝试获取聚类照片来检查）
            let clusterDeleted = false;
            if (clusterId) {
                try {
                    const clusterCheckResponse = await fetch(`/api/v1/similar-photos-clusters/clusters/${clusterId}/photos`);
                    if (clusterCheckResponse.status === 404) {
                        clusterDeleted = true;
                    }
                } catch (e) {
                    // 如果检查失败，假设聚类可能已被删除
                    clusterDeleted = true;
                }
            }

            // 如果聚类被删除，关闭模态框并提示用户
            if (clusterDeleted) {
                if (this.clusterPhotosModal) {
                    this.clusterPhotosModal.hide();
                }
                // 等待模态框关闭完成
                await new Promise(resolve => setTimeout(resolve, 300));
                // 清理残留的backdrop
                this.cleanupModalBackdrop();
                // 刷新聚类列表
                await this.loadClustersData(this.currentPage);
                alert('照片删除成功。由于聚类中只剩一张照片，聚类已自动删除。');
                return;
            }

            // 如果聚类还存在，先关闭模态框，等待关闭完成后再刷新
            if (clusterId && this.clusterPhotosModal) {
                // 先关闭当前模态框
                this.clusterPhotosModal.hide();
                // 等待模态框完全关闭
                await new Promise(resolve => {
                    const modalElement = document.getElementById('clusterPhotosModal');
                    if (modalElement) {
                        const onHidden = () => {
                            modalElement.removeEventListener('hidden.bs.modal', onHidden);
                            // 清理残留的backdrop
                            this.cleanupModalBackdrop();
                            resolve();
                        };
                        modalElement.addEventListener('hidden.bs.modal', onHidden, { once: true });
                    } else {
                        resolve();
                    }
                });
                // 刷新照片列表（会重新显示模态框）
                await this.viewClusterPhotos(clusterId);
            }
            
            // 刷新聚类列表（更新照片数量）
            await this.loadClustersData(this.currentPage);
            
            alert('照片删除成功');
        } catch (error) {
            console.error('删除照片失败:', error);
            alert('删除失败: ' + error.message);
        }
    }
    
    cleanupModalBackdrop() {
        /**
         * 清理模态框遮罩层，防止残留
         * 这个方法会清理所有残留的遮罩层和相关的body样式
         */
        // 清理所有残留的遮罩层
        const backdrops = document.querySelectorAll('.modal-backdrop');
        backdrops.forEach(backdrop => backdrop.remove());
        
        // 清理body上的模态框相关样式
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
        
        // 确保没有模态框处于显示状态
        const openModals = document.querySelectorAll('.modal.show');
        if (openModals.length === 0) {
            // 如果没有打开的模态框，确保清理所有样式
            document.body.style.overflow = '';
            document.body.style.paddingRight = '';
        }
    }

    async deleteCluster(clusterId) {
        if (!confirm('确定要删除这个聚类吗？此操作不可恢复。')) {
            return;
        }

        try {
            const response = await fetch(`/api/v1/similar-photos-clusters/clusters/${clusterId}`, {
                method: 'DELETE'
            });

            const data = await response.json();

            if (response.ok && data.success) {
                alert('聚类已删除');
                this.loadClustersData(this.currentPage);
            } else {
                alert('删除聚类失败: ' + (data.message || '未知错误'));
            }
        } catch (error) {
            console.error('删除聚类失败:', error);
            alert('删除聚类失败: ' + error.message);
        }
    }

    showLoadingState() {
        document.getElementById('clustersLoadingState')?.classList.remove('d-none');
        document.getElementById('clustersList')?.classList.add('d-none');
        document.getElementById('clustersEmptyState')?.classList.add('d-none');
    }

    hideLoadingState() {
        document.getElementById('clustersLoadingState')?.classList.add('d-none');
        document.getElementById('clustersList')?.classList.remove('d-none');
    }

    showEmptyState() {
        document.getElementById('clustersEmptyState')?.classList.remove('d-none');
        document.getElementById('clustersList')?.classList.add('d-none');
        document.getElementById('clustersLoadingState')?.classList.add('d-none');
    }

    showErrorState(message) {
        this.hideLoadingState();
        alert(message);
    }

    renderPagination() {
        /**
         * 渲染分页控件
         */
        const paginationContainer = document.getElementById('clustersPaginationContainer');
        const pagination = document.getElementById('clustersPagination');
        
        if (!paginationContainer || !pagination) {
            return;
        }
        
        // 如果没有数据或只有一页，隐藏分页控件
        if (this.totalPages <= 1) {
            paginationContainer.classList.add('d-none');
            return;
        }
        
        paginationContainer.classList.remove('d-none');
        
        let paginationHTML = '';
        
        // 上一页按钮
        const prevDisabled = this.currentPage === 1 ? 'disabled' : '';
        paginationHTML += `
            <li class="page-item ${prevDisabled}">
                <a class="page-link" href="#" onclick="event.preventDefault(); similarPhotosManagement.loadClustersData(${this.currentPage - 1}); return false;" ${prevDisabled ? 'tabindex="-1" aria-disabled="true"' : ''}>
                    <i class="bi bi-chevron-left"></i>
                </a>
            </li>
        `;
        
        // 页码按钮
        const maxPagesToShow = 5; // 最多显示5个页码
        let startPage = Math.max(1, this.currentPage - Math.floor(maxPagesToShow / 2));
        let endPage = Math.min(this.totalPages, startPage + maxPagesToShow - 1);
        
        // 调整起始页码
        if (endPage - startPage < maxPagesToShow - 1) {
            startPage = Math.max(1, endPage - maxPagesToShow + 1);
        }
        
        // 第一页
        if (startPage > 1) {
            paginationHTML += `
                <li class="page-item">
                    <a class="page-link" href="#" onclick="event.preventDefault(); similarPhotosManagement.loadClustersData(1); return false;">1</a>
                </li>
            `;
            if (startPage > 2) {
                paginationHTML += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
            }
        }
        
        // 页码
        for (let i = startPage; i <= endPage; i++) {
            const active = i === this.currentPage ? 'active' : '';
            paginationHTML += `
                <li class="page-item ${active}">
                    <a class="page-link" href="#" onclick="event.preventDefault(); similarPhotosManagement.loadClustersData(${i}); return false;">${i}</a>
                </li>
            `;
        }
        
        // 最后一页
        if (endPage < this.totalPages) {
            if (endPage < this.totalPages - 1) {
                paginationHTML += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
            }
            paginationHTML += `
                <li class="page-item">
                    <a class="page-link" href="#" onclick="event.preventDefault(); similarPhotosManagement.loadClustersData(${this.totalPages}); return false;">${this.totalPages}</a>
                </li>
            `;
        }
        
        // 下一页按钮
        const nextDisabled = this.currentPage === this.totalPages ? 'disabled' : '';
        paginationHTML += `
            <li class="page-item ${nextDisabled}">
                <a class="page-link" href="#" onclick="event.preventDefault(); similarPhotosManagement.loadClustersData(${this.currentPage + 1}); return false;" ${nextDisabled ? 'tabindex="-1" aria-disabled="true"' : ''}>
                    <i class="bi bi-chevron-right"></i>
                </a>
            </li>
        `;
        
        pagination.innerHTML = paginationHTML;
    }

    renderPaginationInfo() {
        /**
         * 渲染分页信息
         */
        const paginationInfo = document.getElementById('clustersPaginationInfo');
        const paginationText = document.getElementById('clustersPaginationText');
        const pageSizeText = document.getElementById('clustersPageSize');
        
        if (!paginationInfo) {
            return;
        }
        
        // 如果没有数据，隐藏分页信息
        if (this.totalClusters === 0) {
            paginationInfo.classList.add('d-none');
            return;
        }
        
        paginationInfo.classList.remove('d-none');
        
        if (paginationText) {
            const startCluster = (this.currentPage - 1) * this.pageSize + 1;
            const endCluster = Math.min(this.currentPage * this.pageSize, this.totalClusters);
            paginationText.textContent = `第 ${this.currentPage} 页，共 ${this.totalPages} 页 (显示 ${startCluster}-${endCluster} 个，共 ${this.totalClusters} 个聚类)`;
        }
        
        if (pageSizeText) {
            pageSizeText.textContent = this.pageSize;
        }
    }
}

// 初始化
let similarPhotosManagement;
document.addEventListener('DOMContentLoaded', async () => {
    similarPhotosManagement = new SimilarPhotosManagement();
    await similarPhotosManagement.init();
});

