/**
 * 家庭单机版智能照片整理系统 - 工具函数模块
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

function createToastContainer() {
    const container = document.createElement('div');
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}

// ============ 导入详情显示函数 ============

function showImportDetails(detailsData) {
    const modalHtml = `
        <div class="modal fade" id="importDetailsModal" tabindex="-1" aria-labelledby="importDetailsModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="importDetailsModalLabel">导入结果详情</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="关闭"></button>
                    </div>
                    <div class="modal-body">
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
                            <h6>详细信息：</h6>
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
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 移除已存在的模态框
    const existingModal = document.getElementById('importDetailsModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // 添加新的模态框
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // 显示模态框
    const modal = new bootstrap.Modal(document.getElementById('importDetailsModal'));
    modal.show();
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
    elements.photoCount.textContent = count;
}

// ============ 全局导出 ============

// 将函数添加到全局作用域，确保向后兼容
window.formatDate = formatDate;
window.formatDateTime = formatDateTime;
window.getQualityClass = getQualityClass;
window.getQualityText = getQualityText;
window.showError = showError;
window.showSuccess = showSuccess;
window.showWarning = showWarning;
window.createToastContainer = createToastContainer;
window.showImportDetails = showImportDetails;
window.debounce = debounce;
window.setLoading = setLoading;
window.showEmptyState = showEmptyState;
window.hideEmptyState = hideEmptyState;
window.updatePhotoCount = updatePhotoCount;
