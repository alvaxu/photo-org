/**
 * 家庭版智能照片系统 - 工具函数模块
 * 包含格式化、通知、工具等通用函数
 */

// ============ 格式化函数 ============

function formatDate(dateString) {
    if (!dateString) return '未知日期';

    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('zh-CN');
    } catch (e) {
        return dateString;
    }
}

function formatDateTime(dateString) {
    if (!dateString) return '未知时间';

    try {
        const date = new Date(dateString);
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch (e) {
        return dateString;
    }
}

function getQualityClass(level) {
    const classes = {
        'excellent': 'excellent',
        'good': 'good',
        'average': 'average',
        'poor': 'poor',
        'bad': 'bad'
    };
    return classes[level] || 'average';
}

function getQualityText(level) {
    // 如果已经是正确的中文，直接返回
    if (['优秀', '良好', '一般', '较差', '很差'].includes(level)) {
        return level;
    }

    // 如果是英文，转换为中文
    const texts = {
        'excellent': '优秀',
        'good': '良好',
        'average': '一般',
        'fair': '一般',
        'poor': '较差',
        'bad': '很差'
    };
    return texts[level] || '一般';
}

// 新增质量状态判断函数（支持"未评估"状态，用⭐️显示等级）
function getQualityStatus(photo) {
    // 检查是否有质量分析结果（API返回的字段名是 score）
    const qualityScore = photo.quality?.score || 0;

    if (qualityScore > 0) {
        // 有质量评估结果，根据分数确定等级和图标
        const levelInfo = getQualityLevelInfo(qualityScore);
        return {
            score: qualityScore,
            level: levelInfo.level,
            icon: levelInfo.icon,
            color: levelInfo.color,
            text: levelInfo.text,
            class: getQualityClass(levelInfo.level),
            isAssessed: true,
            title: `质量评分：${qualityScore}分 - ${levelInfo.text}`
        };
    } else {
        // 未进行质量评估（分数为0或无质量数据）
        return {
            score: 0,
            level: 'unassessed',
            icon: 'bi-circle',
            color: '#6c757d',
            text: '未评估',
            class: 'unassessed',
            isAssessed: false,
            title: '尚未进行质量评估'
        };
    }
}

// 新增根据分数确定等级和⭐️的函数
function getQualityLevelInfo(score) {
    if (score >= 85) {
        return {
            level: 'excellent',
            text: '优秀',
            icon: 'bi-star-fill',
            color: '#dc3545' // 红色
        };
    } else if (score >= 70) {
        return {
            level: 'good',
            text: '良好',
            icon: 'bi-star-half',
            color: '#28a745' // 绿色
        };
    } else if (score >= 50) {
        return {
            level: 'average',
            text: '一般',
            icon: 'bi-dash-circle-fill',
            color: '#ffc107' // 橙色
        };
    } else if (score >= 30) {
        return {
            level: 'poor',
            text: '较差',
            icon: 'bi-exclamation-triangle-fill',
            color: '#fd7e14' // 橙红
        };
    } else {
        return {
            level: 'bad',
            text: '很差',
            icon: 'bi-x-circle-fill',
            color: '#dc3545' // 红色
        };
    }
}

// 新增AI分析状态判断函数
function getAIAnalysisStatus(photo) {
    // 只检查AI内容分析结果，不检查基础分析
    // 通过confidence>0来判断是否有AI分析（API返回的字段名是confidence）
    if (photo.analysis && photo.analysis.confidence > 0) {
        return {
            hasAIAnalysis: true,
            iconClass: 'bi-robot',
            title: 'AI已分析'
        };
    } else {
        return {
            hasAIAnalysis: false,
            iconClass: 'bi-circle',
            title: 'AI未分析'
        };
    }
}

// ============ 通知函数 ============

function showError(message) {
    console.error('错误:', message);
    // 使用Bootstrap的alert组件显示错误
    const alertHtml = `
        <div class="alert alert-danger alert-dismissible fade show" role="alert">
            <i class="bi bi-exclamation-triangle me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    // 在页面顶部显示错误
    const container = document.querySelector('.container-fluid') || document.body;
    const alertDiv = document.createElement('div');
    alertDiv.innerHTML = alertHtml;
    container.insertBefore(alertDiv.firstElementChild, container.firstChild);
    
    // 不自动消失，只有用户点击关闭按钮才会消失
}

function showSuccess(message, showDetails = false, detailsData = null) {
    console.log('成功:', message);
    
    // 处理多行消息
    const formattedMessage = message.replace(/\n/g, '<br>');
    
    // 构建查看详情按钮
    let detailsButton = '';
    if (showDetails && detailsData) {
        detailsButton = `<button type="button" class="btn btn-outline-success btn-sm ms-2" onclick="showImportDetails(${JSON.stringify(detailsData).replace(/"/g, '&quot;')})">查看详情</button>`;
    }
    
    // 使用Bootstrap的alert组件显示成功消息
    const alertHtml = `
        <div class="alert alert-success alert-dismissible fade show" role="alert">
            <i class="bi bi-check-circle me-2"></i>
            ${formattedMessage}
            ${detailsButton}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    // 在页面顶部显示成功消息
    const container = document.querySelector('.container-fluid') || document.body;
    const alertDiv = document.createElement('div');
    alertDiv.innerHTML = alertHtml;
    container.insertBefore(alertDiv.firstElementChild, container.firstChild);
    
    // 不自动消失，只有用户点击关闭按钮才会消失
}

function showInfo(message, showDetails = false, detailsData = null) {
    console.log('信息:', message);

    // 处理多行消息
    const formattedMessage = message.replace(/\n/g, '<br>');

    // 构建查看详情按钮
    let detailsButton = '';
    if (showDetails && detailsData) {
        detailsButton = `<button type="button" class="btn btn-outline-info btn-sm ms-2" onclick="showImportDetails(${JSON.stringify(detailsData).replace(/"/g, '&quot;')})">查看详情</button>`;
    }

    // 使用Bootstrap的alert组件显示信息消息
    const alertHtml = `
        <div class="alert alert-info alert-dismissible fade show" role="alert">
            <i class="bi bi-info-circle me-2"></i>
            ${formattedMessage}
            ${detailsButton}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;

    // 在页面顶部显示信息
    const container = document.querySelector('.container-fluid') || document.body;
    const alertDiv = document.createElement('div');
    alertDiv.innerHTML = alertHtml;
    container.insertBefore(alertDiv.firstElementChild, container.firstChild);

    // 不自动消失，只有用户点击关闭按钮才会消失
}

function showWarning(message, showDetails = false, detailsData = null) {
    console.warn('警告:', message);
    
    // 处理多行消息
    const formattedMessage = message.replace(/\n/g, '<br>');
    
    // 构建查看详情按钮
    let detailsButton = '';
    if (showDetails && detailsData) {
        detailsButton = `<button type="button" class="btn btn-outline-warning btn-sm ms-2" onclick="showImportDetails(${JSON.stringify(detailsData).replace(/"/g, '&quot;')})">查看详情</button>`;
    }
    
    // 使用Bootstrap的alert组件显示警告
    const alertHtml = `
        <div class="alert alert-warning alert-dismissible fade show" role="alert">
            <i class="bi bi-exclamation-triangle me-2"></i>
            ${formattedMessage}
            ${detailsButton}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    // 在页面顶部显示警告
    const container = document.querySelector('.container-fluid') || document.body;
    const alertDiv = document.createElement('div');
    alertDiv.innerHTML = alertHtml;
    container.insertBefore(alertDiv.firstElementChild, container.firstChild);
    
    // 不自动消失，只有用户点击关闭按钮才会消失
}

// ============ 加载状态管理 ============

/**
 * 显示加载状态
 * @param {string} message - 加载提示消息
 */
function showLoading(message = '正在加载...') {
    // 移除现有的加载提示
    hideLoading();

    const loadingHtml = `
        <div id="globalLoading" class="position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center" style="z-index: 9999; background: rgba(0,0,0,0.5);">
            <div class="bg-white rounded p-4 shadow">
                <div class="d-flex align-items-center">
                    <div class="spinner-border spinner-border-sm me-3" role="status">
                        <span class="visually-hidden">加载中...</span>
                    </div>
                    <div class="fw-semibold">${message}</div>
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', loadingHtml);
}

/**
 * 隐藏加载状态
 */
function hideLoading() {
    const loadingElement = document.getElementById('globalLoading');
    if (loadingElement) {
        loadingElement.remove();
    }
}

function createToastContainer() {
    const container = document.createElement('div');
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}

// ============ 导入详情显示函数 ============

function showImportDetails(detailsData) {
    // 移除已存在的导入结果模态框
    const existingModal = document.getElementById('importDetailsModal');
    if (existingModal) {
        console.log('移除已存在的导入结果模态框');
        existingModal.remove();
    }

    // 根据导入结果确定图标和颜色
    const importedCount = detailsData.imported_photos || 0;
    const skippedCount = detailsData.skipped_photos || 0;
    const failedCount = detailsData.failed_photos || 0;
    const totalFiles = detailsData.total_files || 0;
    
    let icon, alertClass, summaryText;
    if (failedCount > 0) {
        icon = '❌';
        alertClass = 'alert-danger';
        summaryText = `总共${totalFiles}张照片，${importedCount}张导入成功，${skippedCount}张无需导入，${failedCount}张导入失败`;
    } else if (skippedCount > 0) {
        icon = '⚠️';
        alertClass = 'alert-warning';
        summaryText = `总共${totalFiles}张照片，${importedCount}张导入成功，${skippedCount}张无需导入，${failedCount}张导入失败`;
    } else {
        icon = '✅';
        alertClass = 'alert-success';
        summaryText = `总共${totalFiles}张照片，${importedCount}张导入成功，${skippedCount}张无需导入，${failedCount}张导入失败`;
    }
    
    const modalHtml = `
        <div class="modal fade" id="importDetailsModal" tabindex="-1" aria-labelledby="importDetailsModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="importDetailsModalLabel">导入结果详情</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="关闭"></button>
                    </div>
                    <div class="modal-body">
                        <!-- 导入结果摘要 -->
                        <div class="alert ${alertClass} mb-4">
                            <i class="bi bi-info-circle me-2"></i>
                            <strong>${icon} ${summaryText}</strong><br>
                            <small class="text-muted">🎯 下一步：请先点击上方导航栏的"基础分析"按钮，进行质量评估和基础标签生成；如需更深入的AI分析，再点击"AI分析"按钮</small>
                        </div>
                        <div class="row mb-3">
                            <div class="col-md-3">
                                <div class="card text-center">
                                    <div class="card-body">
                                        <h5 class="card-title text-primary">${detailsData.total_files}</h5>
                                        <p class="card-text">总文件数</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card text-center">
                                    <div class="card-body">
                                        <h5 class="card-title text-success">${detailsData.imported_photos}</h5>
                                        <p class="card-text">成功导入</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card text-center">
                                    <div class="card-body">
                                        <h5 class="card-title text-warning">${detailsData.skipped_photos || 0}</h5>
                                        <p class="card-text">无需导入</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card text-center">
                                    <div class="card-body">
                                        <h5 class="card-title text-danger">${detailsData.failed_photos || 0}</h5>
                                        <p class="card-text">导入失败</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        ${detailsData.failed_files && detailsData.failed_files.length > 0 ? `
                        <div class="mt-4">
                            <h6>处理失败的文件：</h6>
                            <div class="table-responsive">
                                <table class="table table-sm">
                                    <thead>
                                        <tr>
                                            <th>文件名</th>
                                            <th>状态</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${detailsData.failed_files.map(file => `
                                            <tr>
                                                <td>${file.split(':')[0]}</td>
                                                <td>${file.split(':')[1] || ''}</td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                        ` : ''}

                        ${detailsData.upload_failed_details && detailsData.upload_failed_details.length > 0 ? `
                        <div class="mt-4">
                            <h6>⚠️ 上传失败的批次：</h6>
                            <div class="alert alert-warning">
                                <p>有 ${detailsData.upload_failed_batches} 批文件由于网络或其他原因上传失败，未进行处理。您可以重新选择这些文件进行上传。</p>
                            </div>
                            <div class="table-responsive">
                                <table class="table table-sm">
                                    <thead>
                                        <tr>
                                            <th>批次</th>
                                            <th>文件数量</th>
                                            <th>失败原因</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${detailsData.upload_failed_details.map(batch => `
                                            <tr>
                                                <td>第${batch.batch_index}批</td>
                                                <td>${batch.files_count}个文件</td>
                                                <td>${batch.error}</td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                        ` : ''}
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // 移除已存在的模态框
    const existingModalToRemove = document.getElementById('importDetailsModal');
    if (existingModalToRemove) {
        existingModalToRemove.remove();
    }

    // 添加新的模态框
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // 显示模态框
    const modal = new bootstrap.Modal(document.getElementById('importDetailsModal'));
    modal.show();
}

// ============ 智能处理结果详情显示函数 ============

function showBatchProcessDetails(detailsData) {
    console.log('showBatchProcessDetails 被调用，数据:', detailsData);

    // 解析新的统计数据
    const totalPhotos = detailsData.total || detailsData.batch_total_photos || 0;
    const fullyAnalyzed = detailsData.fully_analyzed || 0;
    const unanalyzed = detailsData.unanalyzed || 0;
    const missingQuality = detailsData.missing_quality || 0;
    const missingAI = detailsData.missing_ai || 0;

    // 计算成功和失败的数量
    const successfulPhotos = fullyAnalyzed;
    const failedPhotos = unanalyzed + missingQuality + missingAI;

    console.log('处理结果统计:', {
        totalPhotos,
        fullyAnalyzed,
        unanalyzed,
        missingQuality,
        missingAI,
        successfulPhotos,
        failedPhotos
    });

    let icon, alertClass, summaryText;
    if (failedPhotos > 0) {
        icon = '⚠️';
        alertClass = 'alert-warning';
        summaryText = `智能处理完成：${totalPhotos}张照片中，${successfulPhotos}张完整分析，${failedPhotos}张需要补全`;
    } else if (successfulPhotos > 0) {
        icon = '✅';
        alertClass = 'alert-success';
        summaryText = `智能处理完成：${totalPhotos}张照片全部完整分析`;
    } else if (totalPhotos > 0) {
        // 有照片但没有成功和失败的，说明所有照片都已完成处理
        icon = '✅';
        alertClass = 'alert-success';
        summaryText = `智能处理完成：所有${totalPhotos}张照片都已完成智能分析`;
    }
    
    const modalHtml = `
        <div class="modal fade" id="batchProcessDetailsModal" tabindex="-1" aria-labelledby="batchProcessDetailsModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="batchProcessDetailsModalLabel">智能处理结果详情</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="关闭"></button>
                    </div>
                    <div class="modal-body">
                        <!-- 处理结果摘要 -->
                        <div class="alert ${alertClass} mb-4">
                            <i class="bi bi-info-circle me-2"></i>
                            <strong>${icon} ${summaryText}</strong><br>
                            <small class="text-muted">所有照片已完成AI分析、质量评估和智能分类</small>
                        </div>
                        
                        <div class="row mb-3">
                            <div class="col-md-6">
                                <div class="card text-center">
                                    <div class="card-body">
                                        <h5 class="card-title text-primary">${totalPhotos}</h5>
                                        <p class="card-text">总照片数</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="card text-center">
                                    <div class="card-body">
                                        <h5 class="card-title text-success">${fullyAnalyzed}</h5>
                                        <p class="card-text">已完整分析</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="row mb-3">
                            <div class="col-md-4">
                                <div class="card text-center">
                                    <div class="card-body">
                                        <h5 class="card-title text-muted">${unanalyzed}</h5>
                                        <p class="card-text">未分析</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="card text-center">
                                    <div class="card-body">
                                        <h5 class="card-title text-warning">${missingQuality}</h5>
                                        <p class="card-text">缺质量评估</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="card text-center">
                                    <div class="card-body">
                                        <h5 class="card-title text-info">${missingAI}</h5>
                                        <p class="card-text">缺AI分析</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        ${failedPhotos > 0 ? `
                        <div class="mt-4">
                            <h6>处理详情：</h6>
                            <div class="alert alert-info">
                                <i class="bi bi-info-circle me-2"></i>
                                ${unanalyzed > 0 ? `有 ${unanalyzed} 张照片未分析；` : ''}
                                ${missingQuality > 0 ? `${missingQuality} 张照片缺少质量评估；` : ''}
                                ${missingAI > 0 ? `${missingAI} 张照片缺少AI分析；` : ''}
                                请在照片展示区选择这些照片，然后点击该区域的“智能处理”按钮，尝试再次处理。
                            </div>
                        </div>
                        ` : `
                        <div class="mt-4">
                            <div class="alert alert-success">
                                <i class="bi bi-check-circle me-2"></i>
                                所有照片已成功完成智能分析和质量评估，现在您可以搜索、查看和整理您的照片了！
                            </div>
                        </div>
                        `}
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
    const existingModal = document.getElementById('batchProcessDetailsModal');
    if (existingModal) {
        console.log('移除已存在的模态框');
        existingModal.remove();
    }
    
    // 添加新的模态框
    console.log('添加新的模态框到DOM');
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // 显示模态框
    const modalElement = document.getElementById('batchProcessDetailsModal');
    if (modalElement) {
        console.log('模态框元素已创建，准备显示');
        const modal = new bootstrap.Modal(modalElement);
        modal.show();
        console.log('模态框显示命令已执行');
    } else {
        console.error('无法找到模态框元素');
    }
}

// ============ 工具函数 ============

function debounce(func, delay) {
    let timeoutId;
    return function(...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
}

function setLoading(loading) {
    AppState.isLoading = loading;

    if (loading) {
        elements.loadingIndicator.classList.remove('d-none');
        elements.photosGrid.classList.add('d-none');
    } else {
        elements.loadingIndicator.classList.add('d-none');
        elements.photosGrid.classList.remove('d-none');
    }
}

function showEmptyState() {
    elements.emptyState.classList.remove('d-none');
    elements.photosGrid.innerHTML = '';
}

function hideEmptyState() {
    elements.emptyState.classList.add('d-none');
}

function updatePhotoCount(count) {
    if (elements.photoCount) {
        elements.photoCount.textContent = count;
    }
}

// ============ 全局导出 ============

// 将函数添加到全局作用域，确保向后兼容
window.formatDate = formatDate;
window.formatDateTime = formatDateTime;
window.getQualityClass = getQualityClass;
window.getQualityText = getQualityText;
window.getQualityStatus = getQualityStatus;
window.getQualityLevelInfo = getQualityLevelInfo;
window.getAIAnalysisStatus = getAIAnalysisStatus;
window.showError = showError;
window.showSuccess = showSuccess;
window.showWarning = showWarning;
window.createToastContainer = createToastContainer;
window.showImportDetails = showImportDetails;
// ============ 基础分析结果详情显示函数 ============

function showBasicProcessDetails(detailsData) {
    console.log('showBasicProcessDetails 被调用，数据:', detailsData);

    // 解析基础分析的统计数据
    const totalPhotos = detailsData.total_files || detailsData.total_photos || detailsData.total || detailsData.batch_total_photos || 0;
    const successfulPhotos = detailsData.imported_photos || detailsData.completed_photos || detailsData.successful_photos || 0;
    const failedPhotos = detailsData.failed_photos || 0;

    let icon, alertClass, summaryText;
    if (failedPhotos > 0) {
        icon = '⚠️';
        alertClass = 'alert-warning';
        summaryText = `基础分析完成：${totalPhotos}张照片中，${successfulPhotos}张成功分析，${failedPhotos}张需要补全`;
    } else if (successfulPhotos > 0) {
        icon = '✅';
        alertClass = 'alert-success';
        summaryText = `基础分析完成：${totalPhotos}张照片全部成功分析`;
    } else if (totalPhotos > 0) {
        // 有照片但没有成功和失败的，说明所有照片都已完成处理
        icon = '✅';
        alertClass = 'alert-success';
        summaryText = `基础分析完成：所有${totalPhotos}张照片都已完成基础分析`;
    }

    const modalHtml = `
        <div class="modal fade" id="basicProcessDetailsModal" tabindex="-1" aria-labelledby="basicProcessDetailsModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="basicProcessDetailsModalLabel">基础分析结果详情</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="关闭"></button>
                    </div>
                    <div class="modal-body">
                        <!-- 处理结果摘要 -->
                        <div class="alert ${alertClass} mb-4">
                            <i class="bi bi-info-circle me-2"></i>
                            <strong>${icon} ${summaryText}</strong><br>
                            <small class="text-muted">所有照片已完成质量评估和基础标签生成</small>
                        </div>

                        <div class="row mb-3">
                            <div class="col-md-6">
                                <div class="card text-center">
                                    <div class="card-body">
                                        <h5 class="card-title text-primary">${totalPhotos}</h5>
                                        <p class="card-text">总照片数</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="card text-center">
                                    <div class="card-body">
                                        <h5 class="card-title text-success">${successfulPhotos}</h5>
                                        <p class="card-text">已分析</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        ${failedPhotos > 0 ? `
                        <div class="mt-4">
                            <h6>处理详情：</h6>
                            <div class="alert alert-info">
                                <i class="bi bi-info-circle me-2"></i>
                                有 ${failedPhotos} 张照片基础分析失败；
                                请在照片展示区选择这些照片，然后点击该区域的"基础分析"按钮，尝试再次处理。
                            </div>
                        </div>
                        ` : `
                        <div class="mt-4">
                            <div class="alert alert-success">
                                <i class="bi bi-check-circle me-2"></i>
                                所有照片已成功完成基础分析，现在您可以查看照片的质量评分和基础标签了！
                            </div>
                        </div>
                        `}

                        ${detailsData.batch_details ? `
                        <div class="mt-4">
                            <h6>批次处理详情：</h6>
                            <div class="alert alert-info">
                                <i class="bi bi-grid me-2"></i>
                                共分 ${detailsData.batch_count} 批处理，
                                ${detailsData.completed_batches || 0} 批成功，
                                ${detailsData.failed_batches || 0} 批失败
                            </div>
                            <div class="table-responsive">
                                <table class="table table-sm table-striped">
                                    <thead>
                                        <tr>
                                            <th>批次</th>
                                            <th>照片数量</th>
                                            <th>完成数量</th>
                                            <th>状态</th>
                                            <th>详情</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${detailsData.batch_details.map(batch => `
                                            <tr>
                                                <td>第${batch.batch_index}批</td>
                                                <td>${batch.total_photos}</td>
                                                <td>${batch.completed_photos}</td>
                                                <td>
                                                    ${batch.status === 'completed' ? '<span class="badge bg-success">成功</span>' :
                                                      batch.status === 'error' ? '<span class="badge bg-danger">失败</span>' :
                                                      '<span class="badge bg-warning">处理中</span>'}
                                                </td>
                                                <td>
                                                    ${batch.error ? `<small class="text-danger">${batch.error}</small>` :
                                                      batch.status === 'completed' ? '<small class="text-success">处理完成</small>' :
                                                      '<small class="text-muted">正在处理</small>'}
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
    const existingModal = document.getElementById('basicProcessDetailsModal');
    if (existingModal) {
        console.log('移除已存在的模态框');
        existingModal.remove();
    }

    // 添加新的模态框
    console.log('添加新的模态框到DOM');
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // 显示模态框
    const modalElement = document.getElementById('basicProcessDetailsModal');
    if (modalElement) {
        console.log('模态框元素已创建，准备显示');
        const modal = new bootstrap.Modal(modalElement);
        modal.show();
        console.log('模态框已显示');
    } else {
        console.error('模态框元素创建失败');
    }
}

// ============ AI分析结果详情显示函数 ============

function showAIProcessDetails(detailsData) {
    console.log('showAIProcessDetails 被调用，数据:', detailsData);

    // 解析AI分析的统计数据
    const totalPhotos = detailsData.total_photos || detailsData.total || detailsData.batch_total_photos || 0;
    const successfulPhotos = detailsData.completed_photos || detailsData.successful_photos || 0;
    const failedPhotos = detailsData.failed_photos || 0;
    
    // 计算实际处理数量
    const processedPhotos = successfulPhotos + failedPhotos;

    let icon, alertClass, summaryText;
    if (failedPhotos > 0) {
        icon = '⚠️';
        alertClass = 'alert-warning';
        summaryText = `AI分析完成：${totalPhotos}张照片中，${successfulPhotos}张成功分析，${failedPhotos}张分析失败`;
    } else if (successfulPhotos > 0 && processedPhotos === totalPhotos) {
        icon = '✅';
        alertClass = 'alert-success';
        summaryText = `AI分析完成：${totalPhotos}张照片全部成功分析`;
    } else if (processedPhotos > 0) {
        icon = 'ℹ️';
        alertClass = 'alert-info';
        summaryText = `AI分析完成：${processedPhotos}张照片已处理（${successfulPhotos}张成功，${failedPhotos}张失败）`;
    } else if (totalPhotos > 0) {
        // 有照片但没有成功和失败的，说明所有照片都已完成处理
        icon = '✅';
        alertClass = 'alert-success';
        summaryText = `AI分析完成：所有${totalPhotos}张照片都已完成AI分析`;
    }

    const modalHtml = `
        <div class="modal fade" id="aiProcessDetailsModal" tabindex="-1" aria-labelledby="aiProcessDetailsModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="aiProcessDetailsModalLabel">AI分析结果详情</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="关闭"></button>
                    </div>
                    <div class="modal-body">
                        <!-- 处理结果摘要 -->
                        <div class="alert ${alertClass} mb-4">
                            <i class="bi bi-info-circle me-2"></i>
                            <strong>${icon} ${summaryText}</strong><br>
                            ${failedPhotos > 0 ? '' : '<small class="text-muted">所有照片已完成AI内容分析和智能分类</small>'}
                        </div>

                        <div class="row mb-3">
                            <div class="col-md-4">
                                <div class="card text-center">
                                    <div class="card-body">
                                        <h5 class="card-title text-primary">${totalPhotos}</h5>
                                        <p class="card-text">总照片数</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="card text-center">
                                    <div class="card-body">
                                        <h5 class="card-title text-success">${successfulPhotos}</h5>
                                        <p class="card-text">分析成功</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="card text-center">
                                    <div class="card-body">
                                        <h5 class="card-title text-danger">${failedPhotos}</h5>
                                        <p class="card-text">分析失败</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        ${failedPhotos > 0 ? `
                        <div class="mt-4">
                            <h6>处理详情：</h6>
                            <div class="alert alert-info">
                                <i class="bi bi-info-circle me-2"></i>
                                有 ${failedPhotos} 张照片AI分析失败；
                                请检查API密钥配置，然后在照片展示区选择这些照片，点击该区域的"AI分析"按钮，尝试再次处理。
                            </div>
                        </div>
                        ` : `
                        <div class="mt-4">
                            <div class="alert alert-success">
                                <i class="bi bi-check-circle me-2"></i>
                                所有照片已成功完成AI分析，现在您可以享受完整的智能搜索和分类功能了！
                            </div>
                        </div>
                        `}
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
    const existingModal = document.getElementById('aiProcessDetailsModal');
    if (existingModal) {
        console.log('移除已存在的模态框');
        existingModal.remove();
    }

    // 添加新的模态框
    console.log('添加新的模态框到DOM');
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // 显示模态框
    const modalElement = document.getElementById('aiProcessDetailsModal');
    if (modalElement) {
        console.log('模态框元素已创建，准备显示');
        const modal = new bootstrap.Modal(modalElement);
        modal.show();
        console.log('模态框已显示');
    } else {
        console.error('模态框元素创建失败');
    }
}

window.showBatchProcessDetails = showBatchProcessDetails;
window.showBasicProcessDetails = showBasicProcessDetails;
window.showAIProcessDetails = showAIProcessDetails;
window.debounce = debounce;
window.setLoading = setLoading;
window.showEmptyState = showEmptyState;
window.hideEmptyState = hideEmptyState;
window.updatePhotoCount = updatePhotoCount;
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.showInfo = showInfo;
