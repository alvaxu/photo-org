/**
 * 人物管理模块 - 独立页面版本
 * 
 * 功能特点：
 * 1. 人物聚类展示和管理
 * 2. 人物命名和标签管理
 * 3. 人物照片浏览
 * 4. 人脸识别任务管理
 * 5. 类似iPhone相册的人物分类界面
 */

// 全局配置
const PEOPLE_CONFIG = {
    IMAGE_PLACEHOLDER: '/static/images/placeholder.jpg'
};

class PeopleManagementStandalone {
    constructor() {
        this.peopleData = [];
        this.clustersData = [];
        this.statistics = {};
        
        // 人物照片分页状态
        this.personPhotosState = {
            clusterId: null,
            currentPage: 1,
            pageSize: 12, // 默认值，将在init()中从配置更新
            totalPhotos: 0,
            totalPages: 0
        };
        
        this.init();
    }

    init() {
        // 🔥 修复：从配置更新分页大小
        this.personPhotosState.pageSize = this.getPersonPhotosPageSize();
        
        this.bindEvents();
        this.loadPeopleData();
    }
    
    // 从配置中读取人物照片分页参数
    getPersonPhotosPageSize() {
        return window.userConfig?.face_recognition?.person_photos_pagination?.page_size || 
               window.userConfig?.ui?.person_photos_per_page || 
               window.userConfig?.ui?.photos_per_page || 12;
    }
    
    getMaxPagesShown() {
        return window.userConfig?.face_recognition?.person_photos_pagination?.max_pages_shown || 5;
    }
    
    getLoadingDelay() {
        return window.userConfig?.face_recognition?.person_photos_pagination?.loading_delay || 300;
    }
    
    async loadUserConfig() {
        /**
         * 加载用户配置
         */
        try {
            const response = await fetch('/api/v1/config/user');
            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    window.userConfig = result.data;
                    console.log('用户配置加载成功:', window.userConfig);
                }
            }
        } catch (error) {
            console.error('加载用户配置失败:', error);
        }
    }

    bindEvents() {
        // 人物管理按钮
        document.getElementById('refreshPeopleBtn')?.addEventListener('click', () => {
            this.loadPeopleData();
        });

        document.getElementById('startFaceRecognitionBtn')?.addEventListener('click', () => {
            this.startFaceRecognition();
        });

        document.getElementById('startFaceRecognitionFirstBtn')?.addEventListener('click', () => {
            this.startFaceRecognition();
        });

        // 人脸识别模态框中的开始按钮事件监听
        document.getElementById('startFaceBtn')?.addEventListener('click', () => {
            this.startFaceRecognitionProcess();
        });

        // 🔥 新增：配置按钮事件
        document.getElementById('faceRecognitionConfigBtn')?.addEventListener('click', () => {
            this.openFaceRecognitionConfig();
        });

        // 🔥 新增：保存配置按钮事件
        document.getElementById('saveFaceRecognitionConfigBtn')?.addEventListener('click', () => {
            this.saveFaceRecognitionConfig();
        });
    }

    async loadPeopleData() {
        try {
            this.showLoadingState();
            
            // 🔥 先加载用户配置（如果没有加载）
            if (!window.userConfig) {
                await this.loadUserConfig();
            }

            // 并行加载统计信息和聚类数据
            const [statisticsResponse, clustersResponse] = await Promise.all([
                fetch('/api/v1/face-clusters/statistics'),
                fetch('/api/v1/face-clusters/clusters')
            ]);

            if (!statisticsResponse.ok || !clustersResponse.ok) {
                throw new Error('API请求失败');
            }

            const statisticsData = await statisticsResponse.json();
            const clustersData = await clustersResponse.json();

            this.statistics = statisticsData.statistics;
            this.clustersData = clustersData.clusters;

            this.updateStatistics();
            this.renderPeopleCards();
            this.hideLoadingState();

        } catch (error) {
            console.error('加载人物数据失败:', error);
            this.showErrorState('加载人物数据失败: ' + error.message);
        }
    }

    updateStatistics() {
        // 更新统计数字
        document.getElementById('totalPeopleCount').textContent = this.statistics.total_clusters || 0;
        document.getElementById('labeledPeopleCount').textContent = this.statistics.labeled_clusters || 0;
        document.getElementById('unlabeledPeopleCount').textContent = this.statistics.unlabeled_clusters || 0;
        document.getElementById('totalFacesCount').textContent = this.statistics.total_faces || 0;
        document.getElementById('peopleCount').textContent = this.statistics.total_clusters || 0;
        
        // 更新聚类显示提示
        this.updateClusterDisplayNotice();
    }
    
    updateClusterDisplayNotice() {
        const totalClusters = this.statistics.total_clusters || 0;
        const displayedClusters = this.clustersData.length || 0;
        
        // 从配置获取参数
        const maxClusters = window.userConfig?.face_recognition?.max_clusters || 40;
        const minClusterSize = window.userConfig?.face_recognition?.min_cluster_size || 1;
        
        // 只有当显示的聚类数小于总聚类数时才显示提示
        const noticeElement = document.getElementById('clusterDisplayNotice');
        const maxClustersNotice = document.getElementById('maxClustersNotice');
        const minClusterSizeNotice = document.getElementById('minClusterSizeNotice');
        
        if (noticeElement && maxClustersNotice && minClusterSizeNotice) {
            // 更新配置值
            maxClustersNotice.textContent = maxClusters;
            minClusterSizeNotice.textContent = minClusterSize;
            
            // 显示/隐藏提示
            if (displayedClusters < totalClusters && displayedClusters > 0) {
                noticeElement.style.display = 'flex';
            } else {
                noticeElement.style.display = 'none';
            }
        }
    }

    renderPeopleCards() {
        const peopleList = document.getElementById('peopleList');
        if (!peopleList) return;

        if (this.clustersData.length === 0) {
            this.showEmptyState();
            return;
        }

        // 按人脸数量排序
        const sortedClusters = [...this.clustersData].sort((a, b) => b.face_count - a.face_count);

        peopleList.innerHTML = sortedClusters.map(cluster => this.createPersonCard(cluster)).join('');
    }

    createPersonCard(cluster) {
        const isLabeled = cluster.is_labeled;
        const personName = cluster.person_name || '未命名';
        const faceCount = cluster.face_count;
        const quality = cluster.cluster_quality;
        const confidence = cluster.confidence;

        // 质量标签颜色
        const qualityColor = quality === 'high' ? 'success' : quality === 'medium' ? 'warning' : 'secondary';
        const qualityText = quality === 'high' ? '高质量' : quality === 'medium' ? '中等质量' : '低质量';

        return `
            <div class="col-lg-2 col-md-4 col-sm-6 mb-3">
                <div class="card h-100 person-card" data-cluster-id="${cluster.cluster_id}">
                    <div class="card-body">
                        <div class="d-flex align-items-start mb-3">
                            <div class="person-avatar me-2">
                                <div class="avatar-container position-relative" style="width: 50px; height: 50px;">
                                     <img src="${cluster.face_crop_url || '/photos_storage/' + (cluster.representative_photo_path || PEOPLE_CONFIG.IMAGE_PLACEHOLDER).replace(/\\/g, '/')}" 
                                          class="rounded-circle" 
                                          style="width: 50px; height: 50px; object-fit: cover;"
                                          alt="代表人脸"
                                          onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                                    <div class="avatar-placeholder bg-light rounded-circle d-flex align-items-center justify-content-center" 
                                         style="width: 50px; height: 50px; display: none !important;">
                                        <i class="bi bi-person-fill text-muted" style="font-size: 20px;"></i>
                                    </div>
                                </div>
                            </div>
                            <div class="flex-grow-1">
                                <h6 class="card-title mb-1 ${isLabeled ? 'text-primary' : 'text-muted'}">
                                    ${isLabeled ? personName : '未命名人物'}
                                </h6>
                                <div class="d-flex align-items-center gap-2 mb-2">
                                    <span class="badge bg-${qualityColor}">${qualityText}</span>
                                    <span class="badge bg-info">${faceCount} 张照片</span>
                                </div>
                                <small class="text-muted">
                                    置信度: ${(confidence * 100).toFixed(1)}%
                                </small>
                            </div>
                        </div>
                        
                        <div class="d-flex flex-column gap-1">
                            ${isLabeled ? 
                                `<button class="btn btn-sm btn-outline-primary" onclick="peopleManagement.viewPersonPhotos('${cluster.cluster_id}')">
                                    <i class="bi bi-images me-1"></i>查看照片
                                </button>
                                <div class="d-flex gap-1">
                                    <button class="btn btn-sm btn-outline-secondary flex-fill" onclick="peopleManagement.editPersonName('${cluster.cluster_id}', '${personName}')">
                                        <i class="bi bi-pencil"></i>
                                    </button>
                                    <button class="btn btn-sm btn-outline-danger flex-fill" onclick="peopleManagement.deletePerson('${cluster.cluster_id}')">
                                        <i class="bi bi-trash"></i>
                                    </button>
                                </div>
                                <button class="btn btn-sm btn-outline-warning" onclick="peopleManagement.reselectRepresentativeFace('${cluster.cluster_id}')" title="重新选择最佳代表人脸">
                                    <i class="bi bi-arrow-clockwise me-1"></i>优化肖像
                                </button>` :
                                `<button class="btn btn-sm btn-primary" onclick="peopleManagement.namePerson('${cluster.cluster_id}')">
                                    <i class="bi bi-tag me-1"></i>添加姓名
                                </button>
                                <button class="btn btn-sm btn-outline-primary" onclick="peopleManagement.viewPersonPhotos('${cluster.cluster_id}')">
                                    <i class="bi bi-images"></i> 查看照片
                                </button>
                                <button class="btn btn-sm btn-outline-warning" onclick="peopleManagement.reselectRepresentativeFace('${cluster.cluster_id}')" title="重新选择最佳代表人脸">
                                    <i class="bi bi-arrow-clockwise me-1"></i>优化肖像
                                </button>`
                            }
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    async startFaceRecognition() {
        // 重置模态框状态到初始状态
        this.resetFaceModal();

        // 显示人脸识别模态框
        const modal = new bootstrap.Modal(document.getElementById('faceRecognitionModal'));
        modal.show();

        // 获取人脸识别统计信息
        try {
            const countResponse = await fetch('/api/v1/face/pending-photos-count');
            const countData = await countResponse.json();

            const countInfo = document.getElementById('facePhotoCountInfo');
            const countText = document.getElementById('facePhotoCountText');
            const startBtn = document.getElementById('startFaceBtn');

            if (countResponse.ok && countData.count > 0) {
                // 有照片需要分析
                countInfo.style.display = 'block';
                countText.textContent = `发现 ${countData.count} 张照片需要人脸识别`;
                startBtn.disabled = false;
                startBtn.textContent = '开始人脸识别';
            } else if (countResponse.ok && countData.count === 0) {
                // 所有照片都已完成人脸识别
                countInfo.style.display = 'block';
                countText.textContent = '所有照片都已完成人脸识别';
                startBtn.disabled = true;
                startBtn.textContent = '无需识别';
            } else {
                // API调用失败
                countInfo.style.display = 'none';
                startBtn.disabled = true;
                startBtn.textContent = '开始人脸识别';
            }
        } catch (error) {
            console.error('获取人脸识别统计失败:', error);
            // 出错时隐藏统计信息并禁用按钮
            document.getElementById('facePhotoCountInfo').style.display = 'none';
            document.getElementById('startFaceBtn').disabled = true;
            document.getElementById('startFaceBtn').textContent = '开始人脸识别';
        }
    }

    resetFaceModal() {
        // 重置模态框状态
        document.getElementById('facePhotoCountInfo').style.display = 'none';
        document.getElementById('faceProgress').classList.add('d-none');
        document.getElementById('startFaceBtn').disabled = false;
        document.getElementById('startFaceBtn').textContent = '开始人脸识别';
    }

    async startFaceRecognitionProcess() {
        console.log('执行人脸识别处理');

        // 确保用户配置已加载
        if (!window.userConfig) {
            await loadUserConfig();
        }

        // 显示进度
        document.getElementById('faceProgress').classList.remove('d-none');
        document.getElementById('startFaceBtn').disabled = true;
        document.getElementById('faceProgressBar').style.width = '0%';
        document.getElementById('faceStatus').textContent = '正在准备人脸识别...';

        try {
            // 获取需要人脸识别的照片ID
            const pendingResponse = await fetch('/api/v1/face/pending-photos');
            const pendingData = await pendingResponse.json();

            if (!pendingResponse.ok) {
                this.showError('获取待识别照片列表失败');
                return;
            }

            const photoIds = pendingData.photo_ids || [];

            if (photoIds.length === 0) {
                this.showWarning('没有找到需要人脸识别的照片');
                document.getElementById('startFaceBtn').disabled = false;
                return;
            }

            // 分批处理配置（从用户配置读取）
            console.log('🔍 调试信息 - window.userConfig:', window.userConfig);
            console.log('🔍 调试信息 - face_recognition配置:', window.userConfig?.face_recognition);
            const BATCH_THRESHOLD = window.userConfig?.face_recognition?.batch_threshold || 10;  // 分批处理阈值
            const BATCH_SIZE = window.userConfig?.face_recognition?.batch_size || 20;  // 批次大小
            console.log(`🔍 调试信息 - 人脸识别分批阈值: ${BATCH_THRESHOLD}, 批次大小: ${BATCH_SIZE}`);
            console.log(`🔍 调试信息 - 照片数量: ${photoIds.length}, 阈值: ${BATCH_THRESHOLD}, 比较结果: ${photoIds.length > BATCH_THRESHOLD}`);

            // 🔥 修复：统一使用单批处理，让后端处理分批逻辑
            console.log(`人脸识别处理：${photoIds.length}张照片，后端自动分批处理`);
            await this.processFaceRecognitionSingleBatch(photoIds);

        } catch (error) {
            console.error('人脸识别处理失败:', error);
            this.showError('人脸识别处理失败: ' + error.message);
            document.getElementById('startFaceBtn').disabled = false;
        }
    }

    async processFaceRecognitionInBatches(photoIds, batchSize) {
        // 🔥 修复：确保用户配置已加载
        if (!window.userConfig) {
            await loadUserConfig();
        }
        
        const totalPhotos = photoIds.length;
        const totalBatches = Math.ceil(totalPhotos / batchSize);
        const maxConcurrentBatches = window.userConfig?.face_recognition?.max_concurrent_batches || 3;
        
        console.log(`分批处理人脸识别：${totalPhotos}张照片，分为${totalBatches}批，最多${maxConcurrentBatches}批并发`);

        // 显示分批处理状态
        document.getElementById('faceStatus').textContent = `准备分批识别 ${totalPhotos} 张照片，共${totalBatches}批，最多${maxConcurrentBatches}批并发...`;

        try {
            // 准备所有批次信息
            const allBatchTasks = [];
            const activeTasks = new Map();
            
            for (let i = 0; i < totalBatches; i++) {
                const start = i * batchSize;
                const end = Math.min(start + batchSize, totalPhotos);
                const batchPhotoIds = photoIds.slice(start, end);
                
                allBatchTasks.push({
                    batchIndex: i + 1,
                    photoIds: batchPhotoIds,
                    taskId: null,
                    status: 'pending'
                });
            }
            
            // 分阶段启动批次
            await this.processFaceRecognitionWithConcurrency(allBatchTasks, activeTasks, maxConcurrentBatches, totalPhotos);

            // 完成后处理逻辑
            console.log('所有批次识别完成，开始显示结果');

            // 重置按钮状态
            document.getElementById('startFaceBtn').disabled = false;

            // 关闭模态框
            const modal = bootstrap.Modal.getInstance(document.getElementById('faceRecognitionModal'));
            if (modal) {
                modal.hide();

                // 延迟显示结果详情
                setTimeout(async () => {
                    try {
                        await this.showFaceRecognitionBatchResults(allBatchTasks, totalPhotos);
                        // 刷新人物数据
                        this.loadPeopleData();
                    } catch (error) {
                        console.error('显示人脸识别结果失败:', error);
                    }
                }, 100);
            }

        } catch (error) {
            console.error('人脸识别分批处理失败:', error);
            this.showError('人脸识别分批处理失败: ' + error.message);
            document.getElementById('startFaceBtn').disabled = false;
        }
    }

    async processFaceRecognitionWithConcurrency(allBatchTasks, activeTasks, maxConcurrentBatches, totalPhotos) {
        let nextBatchIndex = 0;
        
        // 第一阶段：启动初始并发批次
        const initialBatches = Math.min(maxConcurrentBatches, allBatchTasks.length);
        console.log(`启动初始${initialBatches}个批次`);
        
        for (let i = 0; i < initialBatches; i++) {
            const batch = allBatchTasks[i];
            await this.startFaceRecognitionBatch(batch, activeTasks, totalPhotos);
            nextBatchIndex++;
        }
        
        // 第二阶段：监控并启动后续批次
        while (activeTasks.size > 0 || nextBatchIndex < allBatchTasks.length) {
            // 检查完成的任务
            const completedTasks = await this.checkCompletedFaceRecognitionTasks(activeTasks);
            
            // 启动新的批次
            while (activeTasks.size < maxConcurrentBatches && nextBatchIndex < allBatchTasks.length) {
                const batch = allBatchTasks[nextBatchIndex];
                await this.startFaceRecognitionBatch(batch, activeTasks, totalPhotos);
                nextBatchIndex++;
            }
            
            // 更新进度
            this.updateFaceRecognitionProgress(activeTasks, totalPhotos, allBatchTasks.length);
            
            // 等待一段时间再检查
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
    }

    async startFaceRecognitionBatch(batch, activeTasks, totalPhotos) {
        try {
            const response = await fetch('/api/v1/face/start-recognition', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    photo_ids: batch.photoIds
                })
            });

            if (!response.ok) {
                throw new Error('启动人脸识别批次失败');
            }

            const result = await response.json();
            
            if (result.success && result.task_id) {
                batch.taskId = result.task_id;
                batch.status = 'processing';
                activeTasks.set(result.task_id, batch);
                console.log(`批次 ${batch.batchIndex} 已启动，任务ID: ${result.task_id}`);
            } else {
                throw new Error(result.message || '启动人脸识别批次失败');
            }
        } catch (error) {
            console.error(`启动批次 ${batch.batchIndex} 失败:`, error);
            batch.status = 'failed';
            batch.error = error.message;
        }
    }

    async checkCompletedFaceRecognitionTasks(activeTasks) {
        const completedTasks = [];
        
        for (const [taskId, batch] of activeTasks) {
            try {
                const response = await fetch(`/api/v1/face/task-status/${taskId}`);
                const statusData = await response.json();
                
                if (statusData.success && statusData.status) {
                    const status = statusData.status;
                    
                    if (status.status === 'completed' || status.status === 'failed') {
                        batch.status = status.status;
                        batch.progress = status;
                        completedTasks.push(taskId);
                        activeTasks.delete(taskId);
                        console.log(`批次 ${batch.batchIndex} 完成，状态: ${status.status}`);
                    }
                }
            } catch (error) {
                console.error(`检查任务 ${taskId} 状态失败:`, error);
            }
        }
        
        return completedTasks;
    }

    updateFaceRecognitionProgress(activeTasks, totalPhotos, totalBatches = null) {
        let completedPhotos = 0;
        let totalProcessedPhotos = 0;
        let completedBatches = 0;
        
        for (const [taskId, batch] of activeTasks) {
            if (batch.progress) {
                completedPhotos += batch.progress.completed_photos || 0;
                totalProcessedPhotos += batch.progress.total_photos || batch.photoIds.length;
            }
            if (batch.status === 'completed') {
                completedBatches++;
            }
        }
        
        const progress = totalProcessedPhotos > 0 ? Math.min((completedPhotos / totalPhotos) * 100, 95) : 0;
        document.getElementById('faceProgressBar').style.width = `${progress}%`;
        
        // 构建状态文本（参考基础分析的格式）
        let statusText = '';
        if (totalBatches && totalBatches > 1) {
            // 分批处理：显示批次进度和照片进度
            statusText = `正在识别人脸... ${Math.round(progress)}% (已完成${completedBatches}/${totalBatches}批)`;
        } else {
            // 单批处理：显示照片进度
            statusText = `正在识别人脸... ${Math.round(progress)}% (${completedPhotos}/${totalPhotos})`;
        }
        
        document.getElementById('faceStatus').textContent = statusText;
    }

    async showFaceRecognitionBatchResults(batchInfo, totalPhotos) {
        try {
            // 收集所有批次的结果
            const aggregatedResults = {
                total_files: totalPhotos,
                processed_photos: 0,
                failed_photos: 0,
                skipped_photos: 0,  // 🔥 新增：跳过的照片统计
                batch_count: batchInfo.length,
                completed_batches: 0,
                failed_batches: 0,
                batch_details: []
            };

            // 统计各批次结果
            for (let i = 0; i < batchInfo.length; i++) {
                const batch = batchInfo[i];
                const progress = batch.progress;

                const batchDetail = {
                    batch_index: batch.batchIndex || (i + 1),  // 确保有批次索引
                    task_id: batch.taskId || `batch_${i + 1}`,  // 确保有任务ID
                    completed_photos: progress?.completed_photos || 0,
                    skipped_photos: progress?.skipped_photos || 0,  // 🔥 新增：批次跳过数量
                    failed_photos: progress?.failed_photos || 0,
                    total_photos: progress?.total_photos || batch.photoIds?.length || 0,
                    status: progress?.status || batch.status || 'unknown',
                    error: progress?.error || batch.error || null
                };

                aggregatedResults.batch_details.push(batchDetail);

                if (progress?.status === 'completed' || batch.status === 'completed') {
                    aggregatedResults.completed_batches++;
                    aggregatedResults.processed_photos += progress?.completed_photos || batch.photoIds?.length || 0;
                    aggregatedResults.skipped_photos += progress?.skipped_photos || 0;  // 🔥 新增：累计跳过数量
                } else if (progress?.status === 'failed' || batch.status === 'failed') {
                    aggregatedResults.failed_batches++;
                    aggregatedResults.failed_photos += progress?.failed_photos || batch.photoIds?.length || 0;
                }
            }

            // 显示结果详情页面
            this.showFaceRecognitionResultsModal(aggregatedResults);

        } catch (error) {
            console.error('显示人脸识别结果失败:', error);
            this.showError('显示人脸识别结果失败: ' + error.message);
        }
    }

    showFaceRecognitionResultsModal(results) {
        console.log('showFaceRecognitionResultsModal 被调用，数据:', results);

        // 解析人脸识别的统计数据
        const totalPhotos = results.total_files || results.total_photos || 0;
        const successfulPhotos = results.processed_photos || results.completed_photos || 0;
        const failedPhotos = results.failed_photos || 0;
        const skippedPhotos = results.skipped_photos || 0;  // 🔥 新增：跳过的照片（如GIF格式）

        let icon, alertClass, summaryText;
        if (failedPhotos > 0) {
            icon = '⚠️';
            alertClass = 'alert-warning';
            let skipText = skippedPhotos > 0 ? `，${skippedPhotos}张跳过` : '';
            summaryText = `人脸识别完成：${totalPhotos}张照片中，${successfulPhotos}张成功识别，${failedPhotos}张识别失败${skipText}`;
        } else if (skippedPhotos > 0) {
            icon = 'ℹ️';
            alertClass = 'alert-info';
            summaryText = `人脸识别完成：${totalPhotos}张照片中，${successfulPhotos}张成功识别，${skippedPhotos}张跳过（不支持格式）`;
        } else if (successfulPhotos > 0) {
            icon = '✅';
            alertClass = 'alert-success';
            summaryText = `人脸识别完成：${totalPhotos}张照片全部成功识别`;
        } else if (totalPhotos > 0) {
            icon = '✅';
            alertClass = 'alert-success';
            summaryText = `人脸识别完成：所有${totalPhotos}张照片都已完成人脸识别`;
        }

        const modalHtml = `
            <div class="modal fade" id="faceRecognitionResultsModal" tabindex="-1" aria-labelledby="faceRecognitionResultsModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="faceRecognitionResultsModalLabel">人脸识别结果详情</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="关闭"></button>
                        </div>
                        <div class="modal-body">
                            <!-- 处理结果摘要 -->
                            <div class="alert ${alertClass} mb-4">
                                <i class="bi bi-info-circle me-2"></i>
                                <strong>${icon} ${summaryText}</strong><br>
                                <small class="text-muted">所有照片已完成人脸检测和聚类分析</small>
                            </div>

                            <div class="row mb-3">
                                <div class="col-md-3">
                                    <div class="card text-center">
                                        <div class="card-body">
                                            <h5 class="card-title text-primary">${totalPhotos}</h5>
                                            <p class="card-text">总照片数</p>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="card text-center">
                                        <div class="card-body">
                                            <h5 class="card-title text-success">${successfulPhotos}</h5>
                                            <p class="card-text">已识别</p>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="card text-center">
                                        <div class="card-body">
                                            <h5 class="card-title text-warning">${skippedPhotos}</h5>
                                            <p class="card-text">跳过</p>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="card text-center">
                                        <div class="card-body">
                                            <h5 class="card-title text-danger">${failedPhotos}</h5>
                                            <p class="card-text">识别失败</p>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            ${failedPhotos > 0 || skippedPhotos > 0 ? `
                            <div class="mt-4">
                                <h6>处理详情：</h6>
                                ${failedPhotos > 0 ? `
                                <div class="alert alert-danger mb-2">
                                    <i class="bi bi-exclamation-triangle me-2"></i>
                                    有 ${failedPhotos} 张照片人脸识别失败；请检查这些照片是否包含清晰的人脸，或尝试重新处理。
                                </div>
                                ` : ''}
                                ${skippedPhotos > 0 ? `
                                <div class="alert alert-warning mb-2">
                                    <i class="bi bi-info-circle me-2"></i>
                                    有 ${skippedPhotos} 张照片被跳过（如GIF格式不支持人脸识别）；这些照片不会被计入识别统计。
                                </div>
                                ` : ''}
                            </div>
                            ` : `
                            <div class="mt-4">
                                <div class="alert alert-success">
                                    <i class="bi bi-check-circle me-2"></i>
                                    所有照片已成功完成人脸识别，现在您可以在人物管理页面查看识别结果了！
                                </div>
                            </div>
                            `}

                            ${results.batch_details ? `
                            <div class="mt-4">
                                <h6>批次处理详情：</h6>
                                <div class="alert alert-info">
                                    <i class="bi bi-grid me-2"></i>
                                    共分 ${results.batch_count} 批处理，
                                    ${results.completed_batches || 0} 批成功，
                                    ${results.failed_batches || 0} 批失败
                                </div>
                                <div class="table-responsive">
                                    <table class="table table-sm table-striped">
                                        <thead>
                                            <tr>
                                                <th>批次</th>
                                                <th>照片数量</th>
                                                <th>完成数量</th>
                                                <th>跳过数量</th>
                                                <th>失败数量</th>
                                                <th>状态</th>
                                                <th>详情</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            ${results.batch_details.map(batch => `
                                                <tr>
                                                    <td>${batch.batch_index}</td>
                                                    <td>${batch.total_photos}</td>
                                                    <td>${batch.completed_photos || 0}</td>
                                                    <td>${batch.skipped_photos || 0}</td>
                                                    <td>${batch.failed_photos || 0}</td>
                                                    <td>
                                                        <span class="badge ${batch.status === 'completed' ? 'bg-success' : 'bg-danger'}">
                                                            ${batch.status === 'completed' ? '完成' : '失败'}
                                                        </span>
                                                    </td>
                                                    <td>
                                                        ${batch.error ? `<small class="text-danger">${batch.error}</small>` : '正常'}
                                                    </td>
                                                </tr>
                                            `).join('')}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                            ` : ''}
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-primary" data-bs-dismiss="modal">
                                <i class="bi bi-check-lg me-1"></i>
                                完成
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // 移除已存在的模态框
        const existingModal = document.getElementById('faceRecognitionResultsModal');
        if (existingModal) {
            console.log('移除已存在的人脸识别结果模态框');
            existingModal.remove();
        }

        // 添加新的模态框
        console.log('添加新的人脸识别结果模态框到DOM');
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // 显示模态框
        const modalElement = document.getElementById('faceRecognitionResultsModal');
        if (modalElement) {
            console.log('人脸识别结果模态框元素已创建，准备显示');
            
            // 先销毁已存在的模态框实例
            const existingModalInstance = bootstrap.Modal.getInstance(modalElement);
            if (existingModalInstance) {
                console.log('销毁已存在的模态框实例');
                existingModalInstance.dispose();
            }
            
            const modal = new bootstrap.Modal(modalElement, {
                backdrop: 'static',
                keyboard: false
            });
            modal.show();
            console.log('人脸识别结果模态框已显示');
            
            // 添加关闭事件监听
            modalElement.addEventListener('hidden.bs.modal', function() {
                console.log('人脸识别结果模态框已关闭，清理DOM');
                modalElement.remove();
            });
        } else {
            console.error('人脸识别结果模态框元素创建失败');
        }
    }

    async processFaceRecognitionSingleBatch(photoIds) {
        // 单批处理逻辑（简化版）
        try {
            // 🔥 修复：确保用户配置已加载
            if (!window.userConfig) {
                await loadUserConfig();
            }
            
            const response = await fetch('/api/v1/face/start-recognition', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    photo_ids: photoIds
                })
            });

            if (!response.ok) {
                throw new Error('启动人脸识别失败');
            }

            const result = await response.json();
            
            if (result.success && result.task_id) {
                // 🔥 修复：计算实际批次数，让后端处理分批逻辑
                const BATCH_SIZE = window.userConfig?.face_recognition?.batch_size || 20;
                const totalBatches = Math.ceil(photoIds.length / BATCH_SIZE);
                
                console.log(`人脸识别任务启动：${photoIds.length}张照片，后端将分为${totalBatches}批处理`);
                
                // 监控进度（传递实际批次数）
                await this.monitorFaceRecognitionProgress(result.task_id, photoIds.length, totalBatches);
            } else {
                throw new Error(result.message || '启动人脸识别失败');
            }
        } catch (error) {
            console.error('单批人脸识别失败:', error);
            this.showError('人脸识别失败: ' + error.message);
            document.getElementById('startFaceBtn').disabled = false;
        }
    }

    async monitorFaceRecognitionProgress(taskId, totalPhotos = null, totalBatches = null) {
        // 🔥 修复：确保用户配置已加载
        if (!window.userConfig) {
            await loadUserConfig();
        }
        
        let checkCount = 0;
        const maxChecks = window.userConfig?.face_recognition?.max_progress_checks || 1800; // 最多检查次数
        let hasShownResults = false; // 添加标志防止重复显示结果

        const statusCheckInterval = setInterval(async () => {
            checkCount++;

            try {
                const statusResponse = await fetch(`/api/v1/face/task-status/${taskId}`);
                const statusData = await statusResponse.json();

                // 🔥 修复：直接使用statusData，不再访问.status属性
                const status = statusData;

                // 调试信息
                console.log('人脸识别任务状态:', statusData);

                // 更新进度条和状态文本
                const progress = Math.min(status.progress_percentage || 0, 95);
                document.getElementById('faceProgressBar').style.width = `${progress}%`;
                
                // 构建状态文本（参考基础分析的格式）
                let statusText = '';
                if (totalBatches && totalBatches > 1) {
                    // 分批处理：显示批次进度和照片进度
                    const completedBatches = status.current_batch || 0;
                    statusText = `正在识别人脸... ${Math.round(progress)}% (第${completedBatches}/${totalBatches}批)`;
                } else {
                    // 单批处理：显示照片进度
                    const completedPhotos = status.completed_photos || 0;
                    const totalPhotosCount = status.total_photos || totalPhotos || 0;
                    statusText = `正在识别人脸... ${Math.round(progress)}% (${completedPhotos}/${totalPhotosCount})`;
                }
                
                document.getElementById('faceStatus').textContent = statusText;

                // 检查是否完成
                if (status.status === 'completed' || status.processing_photos === 0) {
                    clearInterval(statusCheckInterval);

                    document.getElementById('faceProgressBar').style.width = '100%';
                    document.getElementById('faceStatus').textContent = '人脸识别完成！';

                    // 重置按钮状态
                    document.getElementById('startFaceBtn').disabled = false;

                    // 关闭人脸识别模态框
                    const modal = bootstrap.Modal.getInstance(document.getElementById('faceRecognitionModal'));
                    if (modal) {
                        modal.hide();

                        // 监听模态框关闭事件（只执行一次）
                        if (!hasShownResults) {
                            hasShownResults = true; // 设置标志防止重复
                            
                            document.getElementById('faceRecognitionModal').addEventListener('hidden.bs.modal', function onModalHidden() {
                                document.getElementById('faceRecognitionModal').removeEventListener('hidden.bs.modal', onModalHidden);

                                try {
                                    // 显示处理结果详情页面（不是小弹窗）
                                    const results = {
                                        total_files: status.total_photos,
                                        processed_photos: status.completed_photos,
                                        failed_photos: status.failed_photos,
                                        skipped_photos: status.skipped_photos || 0,  // 🔥 新增：跳过的照片
                                        // 🔥 修复：使用后端返回的实际批次信息
                                        batch_count: status.total_batches || 1,
                                        completed_batches: status.completed_batches || 1,
                                        failed_batches: status.failed_batches || 0,
                                        batch_details: status.batch_details || [{
                                            batch_index: 1,
                                            task_id: taskId,
                                            completed_photos: status.completed_photos,
                                            skipped_photos: status.skipped_photos || 0,  // 🔥 新增：批次跳过数量
                                            failed_photos: status.failed_photos || 0,
                                            total_photos: status.total_photos,
                                            status: 'completed',
                                            error: null
                                        }]
                                    };
                                    peopleManagement.showFaceRecognitionResultsModal(results);
                                    // 刷新人物数据
                                    peopleManagement.loadPeopleData();
                                } catch (error) {
                                    console.error('显示人脸识别结果失败:', error);
                                }
                            }, { once: true });
                        }
                    } else {
                        // 如果无法获取模态框实例，直接显示结果详情（只执行一次）
                        if (!hasShownResults) {
                            hasShownResults = true;
                            try {
                                const results = {
                                    total_files: status.total_photos,
                                    processed_photos: status.completed_photos,
                                    failed_photos: status.failed_photos,
                                    batch_count: 1,
                                    completed_batches: 1,
                                    failed_batches: 0,
                                    batch_details: [{
                                        batch_index: 1,
                                        task_id: taskId,
                                        completed_photos: status.completed_photos,
                                        total_photos: status.total_photos,
                                        status: 'completed',
                                        error: null
                                    }]
                                };
                                peopleManagement.showFaceRecognitionResultsModal(results);
                                // 刷新人物数据
                                peopleManagement.loadPeopleData();
                            } catch (error) {
                                console.error('显示人脸识别结果失败:', error);
                            }
                        }
                    }

                } else if (status.status === 'failed') {
                    clearInterval(statusCheckInterval);
                    document.getElementById('faceStatus').textContent = '人脸识别失败';
                    this.showError('人脸识别失败: ' + (status.error || '未知错误'));
                    document.getElementById('startFaceBtn').disabled = false;
                }

            } catch (error) {
                console.error('监控人脸识别进度失败:', error);
                clearInterval(statusCheckInterval);
                document.getElementById('startFaceBtn').disabled = false;
            }

            // 超时检查
            if (checkCount >= maxChecks) {
                clearInterval(statusCheckInterval);
                this.showError('人脸识别超时，请稍后重试');
                document.getElementById('startFaceBtn').disabled = false;
            }
        }, 1000); // 每1秒检查一次
    }

    namePerson(clusterId) {
        const personName = prompt('请输入人物姓名:');
        if (!personName || personName.trim() === '') return;

        this.updatePersonName(clusterId, personName.trim());
    }

    editPersonName(clusterId, currentName) {
        const personName = prompt('请输入新的人物姓名:', currentName);
        if (!personName || personName.trim() === '') return;

        this.updatePersonName(clusterId, personName.trim());
    }

    async updatePersonName(clusterId, personName) {
        try {
            const response = await fetch(`/api/v1/face-clusters/clusters/${clusterId}/name`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ person_name: personName })
            });

            if (!response.ok) {
                throw new Error('更新人物姓名失败');
            }

            const result = await response.json();
            if (result.success) {
                this.loadPeopleData(); // 刷新数据
            } else {
                throw new Error(result.message || '更新人物姓名失败');
            }

        } catch (error) {
            console.error('更新人物姓名失败:', error);
            alert('更新人物姓名失败: ' + error.message);
        }
    }

    async deletePerson(clusterId) {
        const confirmed = confirm('确定要删除这个人物吗？这将取消所有相关聚类的标记。');
        if (!confirmed) return;

        try {
            // 找到对应的人物ID
            const cluster = this.clustersData.find(c => c.cluster_id === clusterId);
            if (!cluster || !cluster.person_id) return;

            const response = await fetch(`/api/v1/face-clusters/persons/${cluster.person_id}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error('删除人物失败');
            }

            const result = await response.json();
            if (result.success) {
                this.loadPeopleData(); // 刷新数据
            } else {
                throw new Error(result.message || '删除人物失败');
            }

        } catch (error) {
            console.error('删除人物失败:', error);
            alert('删除人物失败: ' + error.message);
        }
    }

    async viewPersonPhotos(clusterId) {
        try {
            // 确保用户配置已加载
            if (!window.userConfig) {
                await loadUserConfig();
            }
            
            // 从配置中读取分页参数
            const pageSize = this.getPersonPhotosPageSize();
            
            // 获取第一页照片和总数
            const response = await fetch(`/api/v1/face-clusters/clusters/${clusterId}/photos?offset=0&limit=${pageSize}`);
            if (!response.ok) {
                throw new Error('获取照片列表失败');
            }

            const result = await response.json();
            if (result.success) {
                // 获取总照片数
                const totalResponse = await fetch(`/api/v1/face-clusters/clusters/${clusterId}/photos?offset=0&limit=1000`);
                const totalResult = await totalResponse.json();
                const totalPhotos = totalResult.success ? totalResult.photos.length : result.photos.length;
                
                this.showPersonPhotosModal(clusterId, result.photos, totalPhotos, pageSize);
            } else {
                throw new Error(result.message || '获取照片列表失败');
            }

        } catch (error) {
            console.error('获取照片列表失败:', error);
            alert('获取照片列表失败: ' + error.message);
        }
    }

    showPersonPhotosModal(clusterId, photos, totalPhotos, pageSize) {
        // 更新分页状态
        this.personPhotosState = {
            clusterId: clusterId,
            currentPage: 1,
            pageSize: pageSize,
            totalPhotos: totalPhotos,
            totalPages: Math.ceil(totalPhotos / pageSize)
        };
        
        // 创建模态框
        const modalHtml = `
            <div class="modal fade" id="personPhotosModal" tabindex="-1">
                <div class="modal-dialog modal-xl">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">人物照片 (${totalPhotos}张)</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row g-2" id="personPhotosGrid">
                                ${photos.map(photo => `
                                    <div class="col-lg-2 col-md-3 col-sm-4 col-6">
                                        <div class="card">
                                             <img src="/photos_storage/${(photo.display_path || photo.thumbnail_path || photo.original_path || PEOPLE_CONFIG.IMAGE_PLACEHOLDER).replace(/\\/g, '/')}" 
                                                  class="card-img-top" 
                                                  style="height: 150px; object-fit: contain; object-position: center;"
                                                  alt="照片">
                                            <div class="card-body p-2">
                                                <small class="text-muted">
                                                    置信度: ${(photo.confidence * 100).toFixed(1)}%
                                                </small>
                                            </div>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                            
                            <!-- 分页控件 -->
                            <div class="d-flex justify-content-between align-items-center mt-3" id="personPhotosPagination">
                                ${this.renderPersonPhotosPagination()}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // 移除现有模态框
        const existingModal = document.getElementById('personPhotosModal');
        if (existingModal) {
            existingModal.remove();
        }

        // 添加新模态框
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // 绑定分页事件
        this.bindPersonPhotosPaginationEvents();

        // 显示模态框
        const modal = new bootstrap.Modal(document.getElementById('personPhotosModal'));
        modal.show();

        // 模态框关闭时移除
        document.getElementById('personPhotosModal').addEventListener('hidden.bs.modal', function() {
            this.remove();
        });
    }
    
    // 渲染分页控件
    renderPersonPhotosPagination() {
        const { currentPage, totalPages, totalPhotos, pageSize } = this.personPhotosState;
        
        if (totalPages <= 1) {
            return '<div class="pagination-info"><small class="text-muted">共 ' + totalPhotos + ' 张照片</small></div>';
        }
        
        const maxPagesShown = this.getMaxPagesShown();
        const startPage = Math.max(1, currentPage - Math.floor(maxPagesShown / 2));
        const endPage = Math.min(totalPages, startPage + maxPagesShown - 1);
        
        let paginationHtml = `
            <div class="pagination-info">
                <small class="text-muted">第 ${currentPage} 页，共 ${totalPages} 页，共 ${totalPhotos} 张照片</small>
            </div>
            <nav>
                <ul class="pagination pagination-sm mb-0">
        `;
        
        // 上一页按钮
        paginationHtml += `
            <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
                <a class="page-link" href="#" data-page="prev">上一页</a>
            </li>
        `;
        
        // 页码按钮
        for (let i = startPage; i <= endPage; i++) {
            paginationHtml += `
                <li class="page-item ${i === currentPage ? 'active' : ''}">
                    <a class="page-link" href="#" data-page="${i}">${i}</a>
                </li>
            `;
        }
        
        // 下一页按钮
        paginationHtml += `
            <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
                <a class="page-link" href="#" data-page="next">下一页</a>
            </li>
        `;
        
        paginationHtml += `
                </ul>
            </nav>
        `;
        
        return paginationHtml;
    }
    
    // 绑定分页事件
    bindPersonPhotosPaginationEvents() {
        const paginationContainer = document.getElementById('personPhotosPagination');
        if (!paginationContainer) return;
        
        paginationContainer.addEventListener('click', (e) => {
            e.preventDefault();
            
            const target = e.target.closest('.page-link');
            if (!target) return;
            
            const page = target.dataset.page;
            let newPage = this.personPhotosState.currentPage;
            
            if (page === 'prev') {
                newPage = Math.max(1, this.personPhotosState.currentPage - 1);
            } else if (page === 'next') {
                newPage = Math.min(this.personPhotosState.totalPages, this.personPhotosState.currentPage + 1);
            } else {
                newPage = parseInt(page);
            }
            
            if (newPage !== this.personPhotosState.currentPage) {
                this.loadPersonPhotosPage(newPage);
            }
        });
    }
    
    // 加载指定页的照片
    async loadPersonPhotosPage(page) {
        try {
            const { clusterId, pageSize } = this.personPhotosState;
            const offset = (page - 1) * pageSize;
            
            // 显示加载状态
            const grid = document.getElementById('personPhotosGrid');
            if (grid) {
                grid.innerHTML = '<div class="col-12 text-center"><div class="spinner-border" role="status"></div></div>';
            }
            
            const response = await fetch(`/api/v1/face-clusters/clusters/${clusterId}/photos?offset=${offset}&limit=${pageSize}`);
            if (!response.ok) {
                throw new Error('获取照片列表失败');
            }
            
            const result = await response.json();
            if (result.success) {
                // 更新状态
                this.personPhotosState.currentPage = page;
                
                // 更新照片网格
                this.updatePersonPhotosGrid(result.photos);
                
                // 更新分页控件
                this.updatePersonPhotosPagination();
            } else {
                throw new Error(result.message || '获取照片列表失败');
            }
            
        } catch (error) {
            console.error('加载照片页面失败:', error);
            alert('加载照片页面失败: ' + error.message);
        }
    }
    
    // 更新照片网格
    updatePersonPhotosGrid(photos) {
        const grid = document.getElementById('personPhotosGrid');
        if (!grid) return;
        
        grid.innerHTML = photos.map(photo => `
            <div class="col-lg-2 col-md-3 col-sm-4 col-6">
                <div class="card">
                     <img src="/photos_storage/${(photo.display_path || photo.thumbnail_path || photo.original_path || PEOPLE_CONFIG.IMAGE_PLACEHOLDER).replace(/\\/g, '/')}" 
                          class="card-img-top" 
                          style="height: 150px; object-fit: contain; object-position: center;"
                          alt="照片">
                    <div class="card-body p-2">
                        <small class="text-muted">
                            置信度: ${(photo.confidence * 100).toFixed(1)}%
                        </small>
                    </div>
                </div>
            </div>
        `).join('');
    }
    
    // 更新分页控件
    updatePersonPhotosPagination() {
        const paginationContainer = document.getElementById('personPhotosPagination');
        if (!paginationContainer) return;
        
        paginationContainer.innerHTML = this.renderPersonPhotosPagination();
        this.bindPersonPhotosPaginationEvents();
    }

    showLoadingState() {
        document.getElementById('peopleLoadingState')?.classList.remove('d-none');
        document.getElementById('peopleEmptyState')?.classList.add('d-none');
        document.getElementById('peopleList')?.classList.add('d-none');
    }

    hideLoadingState() {
        document.getElementById('peopleLoadingState')?.classList.add('d-none');
        document.getElementById('peopleList')?.classList.remove('d-none');
    }

    showEmptyState() {
        document.getElementById('peopleEmptyState')?.classList.remove('d-none');
        document.getElementById('peopleLoadingState')?.classList.add('d-none');
        document.getElementById('peopleList')?.classList.add('d-none');
    }

    showErrorState(message) {
        document.getElementById('peopleLoadingState')?.classList.add('d-none');
        document.getElementById('peopleEmptyState')?.classList.add('d-none');
        document.getElementById('peopleList')?.classList.add('d-none');
        
        // 显示错误信息
        const errorHtml = `
            <div class="text-center py-5">
                <i class="bi bi-exclamation-triangle display-1 text-danger"></i>
                <h4 class="mt-3 text-danger">加载失败</h4>
                <p class="text-muted">${message}</p>
                <button class="btn btn-primary" onclick="peopleManagement.loadPeopleData()">
                    <i class="bi bi-arrow-clockwise me-2"></i>重试
                </button>
            </div>
        `;
        
        document.getElementById('peopleList').innerHTML = errorHtml;
        document.getElementById('peopleList')?.classList.remove('d-none');
    }

    /**
     * 重新选择代表人脸
     * @param {string} clusterId - 聚类ID
     */
    async reselectRepresentativeFace(clusterId) {
        try {
            const response = await fetch(`/api/v1/face-clusters/clusters/${clusterId}/reselect-representative`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            
            if (result.success) {
                // 显示成功消息
                this.showMessage('代表人脸重新选择成功！', 'success');
                
                // 重新加载数据
                await this.loadPeopleData();
                
                console.log(`代表人脸重新选择成功: ${clusterId} -> ${result.new_representative_face_id}`);
            } else {
                throw new Error(result.message || '重新选择失败');
            }
        } catch (error) {
            console.error('重新选择代表人脸失败:', error);
            this.showMessage('重新选择代表人脸失败: ' + error.message, 'error');
        }
    }

    /**
     * 显示消息提示
     * @param {string} message - 消息内容
     * @param {string} type - 消息类型 (success, error, info)
     */
    showMessage(message, type = 'info') {
        // 创建消息元素
        const messageDiv = document.createElement('div');
        messageDiv.className = `alert alert-${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'info'} alert-dismissible fade show`;
        messageDiv.style.position = 'fixed';
        messageDiv.style.top = '20px';
        messageDiv.style.right = '20px';
        messageDiv.style.zIndex = '9999';
        messageDiv.style.minWidth = '300px';
        
        messageDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        // 添加到页面
        document.body.appendChild(messageDiv);
        
        // 自动移除
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.parentNode.removeChild(messageDiv);
            }
        }, 5000);
    }

    /**
     * 打开人脸识别配置模态框
     */
    openFaceRecognitionConfig() {
        try {
            // 从当前配置读取值
            const minClusterSize = window.userConfig?.face_recognition?.min_cluster_size || 2;
            const maxClusters = window.userConfig?.face_recognition?.max_clusters || 40;
            
            // 填充输入框
            document.getElementById('configMinClusterSize').value = minClusterSize;
            document.getElementById('configMaxClusters').value = maxClusters;
            
            // 显示模态框
            const modal = new bootstrap.Modal(document.getElementById('faceRecognitionConfigModal'));
            modal.show();
        } catch (error) {
            console.error('打开配置模态框失败:', error);
            this.showMessage('打开配置失败: ' + error.message, 'error');
        }
    }

    /**
     * 保存人脸识别配置
     */
    async saveFaceRecognitionConfig() {
        try {
            const minClusterSize = parseInt(document.getElementById('configMinClusterSize').value);
            const maxClusters = parseInt(document.getElementById('configMaxClusters').value);
            
            // 验证输入
            if (!minClusterSize || minClusterSize < 1 || minClusterSize > 10) {
                this.showMessage('最小聚类照片数必须在1-10之间', 'error');
                return;
            }
            
            if (!maxClusters || maxClusters < 10 || maxClusters > 200) {
                this.showMessage('最大显示聚类数必须在10-200之间', 'error');
                return;
            }

            // 显示保存中状态
            const saveBtn = document.getElementById('saveFaceRecognitionConfigBtn');
            const originalText = saveBtn.innerHTML;
            saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>保存中...';
            saveBtn.disabled = true;

            try {
                // 调用保存配置API
                const response = await fetch('/api/v1/config/user', {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        face_recognition: {
                            min_cluster_size: minClusterSize,
                            max_clusters: maxClusters
                        }
                    })
                });

                const result = await response.json();

                if (result.success) {
                    // 更新本地配置
                    if (!window.userConfig) {
                        window.userConfig = {};
                    }
                    if (!window.userConfig.face_recognition) {
                        window.userConfig.face_recognition = {};
                    }
                    window.userConfig.face_recognition.min_cluster_size = minClusterSize;
                    window.userConfig.face_recognition.max_clusters = maxClusters;

                    // 显示成功消息
                    this.showMessage('配置保存成功！页面将刷新以应用新配置。', 'success');

                    // 关闭模态框
                    const modalInstance = bootstrap.Modal.getInstance(document.getElementById('faceRecognitionConfigModal'));
                    modalInstance.hide();

                    // 延迟刷新页面
                    setTimeout(() => {
                        this.loadPeopleData();
                    }, 500);
                } else {
                    throw new Error(result.message || '保存失败');
                }
            } catch (error) {
                console.error('保存配置失败:', error);
                this.showMessage('保存配置失败: ' + error.message, 'error');
            } finally {
                saveBtn.innerHTML = originalText;
                saveBtn.disabled = false;
            }
        } catch (error) {
            console.error('保存配置异常:', error);
            this.showMessage('保存配置异常: ' + error.message, 'error');
        }
    }
}

// 创建全局实例
const peopleManagement = new PeopleManagementStandalone();
