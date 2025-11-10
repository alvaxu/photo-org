/**
 * 图像特征提取批处理模块
 * 
 * 参考基础分析和AI分析的批处理实现
 */

/**
 * 显示图像特征提取模态框
 */
async function showImageFeatureExtractionModal() {
    console.log('显示图像特征提取模态框');
    
    // 重置模态框状态
    resetFeatureExtractionModal();
    
    // 显示模态框
    const modal = new bootstrap.Modal(document.getElementById('imageFeatureExtractionModal'));
    modal.show();
    
    // 获取待提取特征的照片数量
    try {
        const countResponse = await fetch('/api/v1/image-features/pending-photos');
        const countData = await countResponse.json();
        
        const countInfo = document.getElementById('featurePhotoCountInfo');
        const countText = document.getElementById('featurePhotoCountText');
        const batchInfo = document.getElementById('featureBatchInfo');
        const startBtn = document.getElementById('startFeatureExtractionBtn');
        
        if (countResponse.ok && countData.total > 0) {
            // 有照片需要提取特征
            countInfo.style.display = 'block';
            countText.textContent = `发现 ${countData.total} 张照片需要提取特征`;
            
            // 显示批次信息
            batchInfo.style.display = 'block';
            
            // 获取配置信息
            if (!window.userConfig) {
                await loadUserConfig();
            }
            
            const batchSize = window.userConfig?.image_features?.batch_size || 200;
            const batchThreshold = window.userConfig?.image_features?.batch_threshold || 100;
            
            // 计算批次数
            const totalPhotos = countData.total;
            const estimatedBatches = totalPhotos > batchThreshold 
                ? Math.ceil(totalPhotos / batchSize) 
                : 1;
            
            // 更新批次信息显示
            document.getElementById('featureTotalPhotos').textContent = totalPhotos;
            document.getElementById('featureBatchCount').textContent = estimatedBatches;
            document.getElementById('featureBatchSize').textContent = batchSize;
            document.getElementById('featureBatchThreshold').textContent = batchThreshold;
            
            startBtn.disabled = false;
            startBtn.textContent = '开始特征提取';
        } else if (countResponse.ok && countData.total === 0) {
            // 所有照片都已完成特征提取
            countInfo.style.display = 'block';
            countInfo.className = 'alert alert-success';
            countText.textContent = '所有照片都已完成特征提取';
            batchInfo.style.display = 'none';
            startBtn.disabled = true;
            startBtn.textContent = '无需提取';
        } else {
            // 获取失败
            countInfo.style.display = 'block';
            countInfo.className = 'alert alert-danger';
            countText.textContent = '获取照片数量失败';
            batchInfo.style.display = 'none';
            startBtn.disabled = true;
        }
    } catch (error) {
        console.error('获取待提取特征照片数量失败:', error);
        const countInfo = document.getElementById('featurePhotoCountInfo');
        const countText = document.getElementById('featurePhotoCountText');
        countInfo.style.display = 'block';
        countInfo.className = 'alert alert-danger';
        countText.textContent = '获取照片数量失败: ' + error.message;
    }
}

/**
 * 重置特征提取模态框状态
 */
function resetFeatureExtractionModal() {
    // 重置所有显示元素
    document.getElementById('featurePhotoCountInfo').style.display = 'none';
    document.getElementById('featurePhotoCountInfo').className = 'alert alert-warning';
    document.getElementById('featureBatchInfo').style.display = 'none';
    document.getElementById('featureProgress').classList.add('d-none');
    document.getElementById('featureStats').style.display = 'none';
    
    // 重置进度条
    document.getElementById('featureProgressBar').style.width = '0%';
    document.getElementById('featureStatus').textContent = '正在准备特征提取...';
    document.getElementById('featureDetails').textContent = '请稍候...';
    
    // 重置统计数字
    document.getElementById('featureProcessedCount').textContent = '0';
    document.getElementById('featureExtractedCount').textContent = '0';
    document.getElementById('featureSkippedCount').textContent = '0';
    document.getElementById('featureFailedCount').textContent = '0';
    
    // 重置按钮
    const startBtn = document.getElementById('startFeatureExtractionBtn');
    startBtn.disabled = false;
    startBtn.textContent = '开始特征提取';
    
    // 显示底部按钮
    const modalFooter = document.querySelector('#imageFeatureExtractionModal .modal-footer');
    if (modalFooter) modalFooter.style.display = 'flex';
}

/**
 * 开始图像特征提取处理
 */
async function startImageFeatureExtraction() {
    console.log('执行图像特征提取处理');
    
    // 确保用户配置已加载
    if (!window.userConfig) {
        await loadUserConfig();
    }
    
    // 显示进度
    document.getElementById('featureProgress').classList.remove('d-none');
    document.getElementById('featureStats').style.display = 'flex';
    document.getElementById('startFeatureExtractionBtn').disabled = true;
    document.getElementById('featureProgressBar').style.width = '0%';
    document.getElementById('featureStatus').textContent = '正在准备特征提取...';
    document.getElementById('featureDetails').textContent = '请稍候...';
    
    // 隐藏底部按钮
    const modalFooter = document.querySelector('#imageFeatureExtractionModal .modal-footer');
    if (modalFooter) modalFooter.style.display = 'none';
    
    try {
        // 获取需要提取特征的照片ID
        const pendingResponse = await fetch('/api/v1/image-features/pending-photos');
        const pendingData = await pendingResponse.json();
        
        if (!pendingResponse.ok) {
            showError('获取待提取特征照片列表失败');
            return;
        }
        
        // 处理不同的API返回格式
        let photoIds = [];
        if (pendingData.photos && Array.isArray(pendingData.photos)) {
            photoIds = pendingData.photos.map(p => typeof p === 'object' ? p.id : p);
        } else if (pendingData.photo_ids && Array.isArray(pendingData.photo_ids)) {
            photoIds = pendingData.photo_ids;
        } else if (Array.isArray(pendingData)) {
            photoIds = pendingData.map(p => typeof p === 'object' ? p.id : p);
        }
        
        if (photoIds.length === 0) {
            showWarning('没有找到需要提取特征的照片');
            document.getElementById('startFeatureExtractionBtn').disabled = false;
            if (modalFooter) modalFooter.style.display = 'flex';
            return;
        }
        
        // 启动特征提取任务
        const startResponse = await fetch('/api/v1/image-features/start-extraction', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                photo_ids: photoIds
            })
        });
        
        const startData = await startResponse.json();
        
        if (!startResponse.ok || !startData.success) {
            throw new Error(startData.message || '启动特征提取任务失败');
        }
        
        const taskId = startData.task_id;
        console.log('特征提取任务已启动，任务ID:', taskId);
        
        // 开始轮询任务状态
        await pollFeatureExtractionStatus(taskId);
        
    } catch (error) {
        console.error('图像特征提取处理失败:', error);
        showError('图像特征提取失败: ' + error.message);
        
        // 发生错误时重新显示底部按钮
        if (modalFooter) modalFooter.style.display = 'flex';
        document.getElementById('startFeatureExtractionBtn').disabled = false;
    }
}

/**
 * 轮询特征提取任务状态
 */
async function pollFeatureExtractionStatus(taskId) {
    const pollInterval = 2000; // 每2秒轮询一次
    const maxPollTime = 3 * 60 * 60 * 1000; // 最多轮询3小时
    const startTime = Date.now();
    
    let lastProgress = 0;
    
    const poll = async () => {
        try {
            // 检查是否超时
            if (Date.now() - startTime > maxPollTime) {
                throw new Error('特征提取任务超时');
            }
            
            // 获取任务状态
            const statusResponse = await fetch(`/api/v1/image-features/task-status/${taskId}`);
            const statusData = await statusResponse.json();
            
            if (!statusResponse.ok) {
                throw new Error(statusData.detail || statusData.message || '获取任务状态失败');
            }
            
            // 处理不同的返回格式
            const status = statusData.success !== undefined ? statusData : statusData;
            
            // 更新进度显示
            const progress = status.progress_percentage || 0;
            const completed = status.completed_photos || 0;
            const failed = status.failed_photos || 0;
            const total = status.total_photos || 0;
            
            // 更新进度条
            document.getElementById('featureProgressBar').style.width = progress + '%';
            
            // 更新状态文本
            document.getElementById('featureStatus').textContent = 
                `正在处理: ${completed}/${total} (${progress.toFixed(1)}%)`;
            
            // 更新详细信息
            if (status.current_batch && status.total_batches) {
                document.getElementById('featureDetails').textContent = 
                    `批次 ${status.current_batch}/${status.total_batches}`;
            }
            
            // 更新统计数字
            document.getElementById('featureProcessedCount').textContent = completed + failed;
            document.getElementById('featureExtractedCount').textContent = completed;
            document.getElementById('featureFailedCount').textContent = failed;
            
            // 检查任务是否完成
            if (status.status === 'completed') {
                // 任务完成
                document.getElementById('featureProgressBar').style.width = '100%';
                document.getElementById('featureStatus').textContent = 
                    `特征提取完成: ${completed}/${total}`;
                document.getElementById('featureDetails').textContent = 
                    `成功: ${completed}, 失败: ${failed}`;
                
                // 关闭进度模态框
                const modal = bootstrap.Modal.getInstance(document.getElementById('imageFeatureExtractionModal'));
                if (modal) {
                    modal.hide();
                }
                
                // 等待模态框关闭后显示结果页面
                setTimeout(async () => {
                    // 显示结果页面
                    showImageFeatureExtractionResults(status);
                    
                    // 刷新照片列表（只有在首页才刷新，相似照识别页面不需要）
                    // 检查是否在首页：通过检查是否存在 photosGrid 元素来判断
                    if (typeof loadPhotos === 'function') {
                        // 检查是否在首页（相似照识别页面没有 photosGrid 元素）
                        const isHomePage = document.getElementById('photosGrid') !== null;
                        
                        if (isHomePage) {
                            // 延迟1秒，给服务器时间完成数据库操作
                            await new Promise(resolve => setTimeout(resolve, 1000));
                            try {
                                await loadPhotos();
                            } catch (error) {
                                console.warn('刷新照片列表失败（可忽略）:', error);
                                // 不显示错误，因为特征提取已完成，用户可以手动刷新
                            }
                        } else {
                            console.log('相似照识别页面，跳过照片列表刷新');
                        }
                    }
                }, 300);
                
                return; // 停止轮询
            } else if (status.status === 'failed') {
                // 任务失败
                throw new Error(status.error || '特征提取任务失败');
            } else {
                // 继续轮询
                setTimeout(poll, pollInterval);
            }
            
        } catch (error) {
            console.error('轮询特征提取任务状态失败:', error);
            showError('特征提取任务状态查询失败: ' + error.message);
            
            // 重新显示底部按钮
            const modalFooter = document.querySelector('#imageFeatureExtractionModal .modal-footer');
            if (modalFooter) modalFooter.style.display = 'flex';
            document.getElementById('startFeatureExtractionBtn').disabled = false;
        }
    };
    
    // 开始轮询
    poll();
}

/**
 * 显示图像特征提取结果页面
 */
function showImageFeatureExtractionResults(status) {
    try {
        const total = status.total_photos || 0;
        const completed = status.completed_photos || 0;
        const failed = status.failed_photos || 0;
        const batchDetails = status.batch_details || [];
        
        // 收集批次详情
        const batchDetailsHtml = batchDetails.length > 0 ? `
            <div class="mt-3">
                <h6 class="mb-3">批次详情</h6>
                <div class="table-responsive">
                    <table class="table table-sm table-striped">
                        <thead>
                            <tr>
                                <th>批次</th>
                                <th>照片数量</th>
                                <th>成功</th>
                                <th>失败</th>
                                <th>状态</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${batchDetails.map(batch => `
                                <tr>
                                    <td>第${batch.batch_index || '-'}批</td>
                                    <td>${batch.total_photos || 0}</td>
                                    <td>${batch.completed_photos || 0}</td>
                                    <td>${batch.failed_photos || 0}</td>
                                    <td>
                                        ${batch.status === 'completed' ? '<span class="badge bg-success">成功</span>' :
                                          batch.status === 'failed' ? '<span class="badge bg-danger">失败</span>' :
                                          '<span class="badge bg-warning">处理中</span>'}
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        ` : '';
        
        // 错误详情
        const errorDetails = status.error_details || [];
        const errorDetailsHtml = errorDetails.length > 0 ? `
            <div class="mt-3">
                <h6 class="mb-3 text-danger">错误详情</h6>
                <div class="alert alert-danger">
                    <ul class="mb-0">
                        ${errorDetails.slice(0, 10).map(error => `
                            <li>照片ID ${error.photo_id}: ${error.error}</li>
                        `).join('')}
                        ${errorDetails.length > 10 ? `<li><small>还有 ${errorDetails.length - 10} 个错误...</small></li>` : ''}
                    </ul>
                </div>
            </div>
        ` : '';
        
        const modalHtml = `
            <div class="modal fade" id="imageFeatureExtractionResultModal" tabindex="-1" aria-labelledby="imageFeatureExtractionResultModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header bg-success text-white">
                            <h5 class="modal-title" id="imageFeatureExtractionResultModalLabel">
                                <i class="bi bi-check-circle me-2"></i>特征提取完成
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="关闭"></button>
                        </div>
                        <div class="modal-body">
                            <!-- 处理结果摘要 -->
                            <div class="alert alert-success">
                                <h6 class="alert-heading">
                                    <i class="bi bi-check-circle me-2"></i>处理完成
                                </h6>
                                <div class="row mt-3">
                                    <div class="col-md-4 text-center">
                                        <div class="h4 text-primary mb-1">${total}</div>
                                        <small class="text-muted">总照片数</small>
                                    </div>
                                    <div class="col-md-4 text-center">
                                        <div class="h4 text-success mb-1">${completed}</div>
                                        <small class="text-muted">成功提取</small>
                                    </div>
                                    <div class="col-md-4 text-center">
                                        <div class="h4 text-danger mb-1">${failed}</div>
                                        <small class="text-muted">提取失败</small>
                                    </div>
                                </div>
                            </div>
                            
                            ${batchDetailsHtml}
                            ${errorDetailsHtml}
                            
                            <div class="mt-3">
                                <div class="alert alert-info">
                                    <i class="bi bi-info-circle me-2"></i>
                                    <strong>提示：</strong>特征向量已保存到数据库，现在可以使用基于特征向量的相似照片搜索功能。
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-primary" data-bs-dismiss="modal">
                                <i class="bi bi-check-lg me-1"></i>完成
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // 移除已存在的模态框
        const existingModal = document.getElementById('imageFeatureExtractionResultModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // 添加新模态框到页面
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // 显示模态框
        const modal = new bootstrap.Modal(document.getElementById('imageFeatureExtractionResultModal'));
        modal.show();
        
        // 模态框关闭后清理
        document.getElementById('imageFeatureExtractionResultModal').addEventListener('hidden.bs.modal', function() {
            this.remove();
        });
        
    } catch (error) {
        console.error('显示特征提取结果失败:', error);
        showError('显示特征提取结果失败: ' + error.message);
    }
}

// 导出函数到全局作用域
window.showImageFeatureExtractionModal = showImageFeatureExtractionModal;
window.startImageFeatureExtraction = startImageFeatureExtraction;
window.showImageFeatureExtractionResults = showImageFeatureExtractionResults;

