/**
 * 家庭版智能照片系统 - 照片操作模块
 * 
 * 功能：
 * 1. 照片卡片和列表项创建
 * 2. 照片选择操作
 * 3. 照片删除操作
 * 4. 页面导航和显示
 */

// 旧的触摸延迟处理函数已移除，现在使用新的混合设备交互管理器

/**
 * 获取照片处理状态
 *
 * @param {Object} photo - 照片对象
 * @returns {Object} 状态信息对象
 */
function getProcessingStatus(photo) {
    // 处理中状态 - 优先级最高
    if (photo.status === 'analyzing') {
        return {
            status: 'analyzing',
            iconClass: 'bi-hourglass-split',
            text: '分析中',
            className: 'status-analyzing',
            canProcess: false
        };
    }

    // 根据精确状态判断
    if (photo.status === 'completed') {
        return {
            status: 'completed',
            iconClass: 'bi-check-circle-fill',
            text: '完整分析完成',
            className: 'status-completed',
            canProcess: true  // 支持重新处理
        };
    }

    if (photo.status === 'quality_completed') {
        return {
            status: 'quality_completed',
            iconClass: 'bi-check-circle',
            text: '基础分析完成',
            className: 'status-quality-completed',
            canProcess: true  // 支持继续AI分析或重新处理
        };
    }

    if (photo.status === 'content_completed') {
        return {
            status: 'content_completed',
            iconClass: 'bi-check-circle',
            text: 'AI分析完成',
            className: 'status-content-completed',
            canProcess: true  // 支持继续基础分析或重新处理
        };
    }

    if (photo.status === 'error') {
        return {
            status: 'error',
            iconClass: 'bi-exclamation-triangle',
            text: '分析失败',
            className: 'status-error',
            canProcess: true,  // 支持重新处理
            showRetryButton: true,  // 显示重试按钮
            retryAction: 'ai_analysis',  // 重试操作类型
            errorMessage: photo.analysis?.error || '分析过程中出现错误'  // 显示具体错误信息
        };
    }

    // 未处理状态 - 默认状态
    return {
        status: 'imported',
        iconClass: 'bi-robot',
        text: '未分析',
        className: 'status-unprocessed',
        canProcess: true
    };
}

/**
 * 创建照片卡片
 *
 * @param {Object} photo - 照片对象
 * @returns {string} HTML字符串
 */
function createPhotoCard(photo) {
    const allTags = photo.tags || [];
    const visibleTags = allTags.slice(0, 5);
    const hiddenTagsCount = allTags.length - 5;
    
    const visibleTagsHtml = visibleTags.map(tag =>
        `<span class="photo-tag">${tag}</span>`
    ).join('');
    
    const hiddenTagsHtml = allTags.slice(5).map(tag =>
        `<span class="photo-tag">${tag}</span>`
    ).join('');

    // 获取质量状态和AI分析状态
    const qualityStatus = getQualityStatus(photo);
    const aiStatus = getAIAnalysisStatus(photo);

    // 根据照片尺寸判断方向并添加CSS类
    let containerClass = 'photo-card selectable';
    if (photo.width && photo.height) {
        if (photo.height > photo.width) {
            containerClass += ' portrait';  // 竖版
        } else if (photo.height === photo.width) {
            containerClass += ' square';    // 正方形
        } else {
            containerClass += ' landscape'; // 横版
        }
    }

    // 获取照片处理状态
    const processingStatus = getProcessingStatus(photo);

    // GPS状态判断
    const hasGps = photo.location_lat && photo.location_lng;
    const hasAddress = photo.location_name && photo.location_name.trim() !== '';

    return `
        <div class="${containerClass}" data-photo-id="${photo.id}" data-has-gps="${hasGps}" data-has-address="${hasAddress}">
            <!-- 永久选择框 - 位于最顶层 -->
            <div class="photo-selection-checkbox"
                 data-photo-id="${photo.id}"
                 onclick="event.stopPropagation(); togglePhotoSelection(${photo.id}, event);"
                 title="选择照片">
            </div>
            <div class="photo-image-container">
                <img src="/photos_storage/${(photo.thumbnail_path || CONFIG.IMAGE_PLACEHOLDER).replace(/\\/g, '/')}"
                     alt="${photo.filename}"
                     class="photo-image"
                     loading="lazy"
                     onclick="viewPhotoDetail(${photo.id})">
                <div class="photo-overlay">
                    <button class="btn btn-light btn-sm" data-photo-id="${photo.id}" data-action="view" title="查看详情">
                        <i class="bi bi-eye"></i>
                    </button>
                    <button class="btn btn-warning btn-sm" data-photo-id="${photo.id}" data-action="edit" title="编辑">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-danger btn-sm" data-photo-id="${photo.id}" data-action="delete" title="删除">
                        <i class="bi bi-trash"></i>
                    </button>
                    <button class="btn btn-info btn-sm" data-photo-id="${photo.id}" data-action="similar" title="相似照片">
                        <i class="bi bi-search"></i>
                    </button>
                </div>
            </div>
            <div class="photo-info">
                <div class="photo-header">
                    <div class="photo-title">${photo.filename}</div>
                    <div class="photo-quality-container">
                        <i class="bi ${qualityStatus.icon} quality-icon ${qualityStatus.isAssessed ? 'quality-assessed' : 'quality-unassessed'}"
                           data-level="${qualityStatus.level}"
                           data-photo-id="${photo.id}"
                           onclick="event.stopPropagation(); forceBasicAnalysis(${photo.id})"
                           title="${qualityStatus.title}"
                           style="color: ${qualityStatus.color}"></i>
                        <i class="bi ${aiStatus.iconClass} ai-status-icon ${aiStatus.hasAIAnalysis ? 'ai-analyzed' : 'ai-not-analyzed'}"
                           data-photo-id="${photo.id}"
                           onclick="event.stopPropagation(); forceAIAnalysis(${photo.id})"
                           title="${aiStatus.title}"
                           style="${aiStatus.hasAIAnalysis ? '' : 'color: #6c757d;'}"></i>
                        ${hasGps ? `<i class="bi bi-geo-alt-fill gps-icon ${hasAddress ? 'gps-resolved' : 'gps-unresolved'}" data-photo-id="${photo.id}" onclick="event.stopPropagation(); resolvePhotoAddress(${photo.id}, ${hasAddress})" title="${hasAddress ? '点击重新解析地址' : '点击解析地址'}"></i>` : ''}
                        <i class="bi bi-download download-icon" 
                           data-photo-id="${photo.id}" 
                           onclick="event.stopPropagation(); downloadSinglePhoto(${photo.id})" 
                           title="下载照片"></i>
                    </div>
                </div>
                <div class="photo-meta">
                    <i class="bi bi-calendar me-1"></i>${formatDate(photo.taken_at)} (拍摄日期)
                    ${hasAddress ? `<div class="photo-address" title="${photo.location_name}">
                        <i class="bi bi-geo-alt me-1"></i>
                        <span class="address-text">${photo.location_name.length > 30 ? photo.location_name.substring(0, 30) + '...' : photo.location_name}</span>
                    </div>` : ''}
                </div>
                <div class="photo-tags">
                    <div class="visible-tags">
                        ${visibleTagsHtml}
                        ${hiddenTagsCount > 0 ? `
                            <span class="tag-toggle" onclick="toggleTags(this, event)" data-photo-id="${photo.id}">
                                +${hiddenTagsCount} 更多
                            </span>
                        ` : ''}
                    </div>
                    ${hiddenTagsCount > 0 ? `
                        <div class="hidden-tags" style="display: none;">
                            ${hiddenTagsHtml}
                        </div>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
}

/**
 * 创建照片列表项
 * 
 * @param {Object} photo - 照片对象
 * @returns {string} HTML字符串
 */
function createPhotoListItem(photo) {
    const allTags = photo.tags || [];
    const visibleTags = allTags.slice(0, 5);
    const hiddenTagsCount = allTags.length - 5;
    
    const visibleTagsHtml = visibleTags.map(tag =>
        `<span class="badge bg-secondary me-1 mb-1">${tag}</span>`
    ).join('');
    
    const hiddenTagsHtml = allTags.slice(5).map(tag =>
        `<span class="badge bg-secondary me-1 mb-1">${tag}</span>`
    ).join('');

    // 获取质量状态和AI分析状态（列表视图）
    const qualityStatus = getQualityStatus(photo);
    const aiStatus = getAIAnalysisStatus(photo);

    // GPS状态判断
    const hasGps = photo.location_lat && photo.location_lng;
    const hasAddress = photo.location_name && photo.location_name.trim() !== '';

    // 根据照片尺寸判断方向并添加CSS类
    let containerClass = 'photo-list-item';
    if (photo.width && photo.height) {
        if (photo.height > photo.width) {
            containerClass += ' portrait';  // 竖版
        } else if (photo.height === photo.width) {
            containerClass += ' square';    // 正方形
        } else {
            containerClass += ' landscape'; // 横版
        }
    }

    // 格式化文件大小
    const formatFileSize = (bytes) => {
        if (!bytes) return '未知';
        const units = ['B', 'KB', 'MB', 'GB'];
        let size = bytes;
        let unitIndex = 0;
        while (size >= 1024 && unitIndex < units.length - 1) {
            size /= 1024;
            unitIndex++;
        }
        return `${size.toFixed(1)} ${units[unitIndex]}`;
    };

    // 格式化分辨率
    const resolution = photo.width && photo.height ? `${photo.width} × ${photo.height}` : '未知';

    return `
        <div class="${containerClass}" data-photo-id="${photo.id}" data-has-gps="${hasGps}" data-has-address="${hasAddress}">
            <!-- 永久选择框 - 位于最顶层 -->
            <div class="photo-selection-checkbox"
                 data-photo-id="${photo.id}"
                 onclick="event.stopPropagation(); togglePhotoSelection(${photo.id}, event);"
                 title="选择照片">
            </div>
            <div class="photo-thumbnail-container">
                <img src="/photos_storage/${(photo.thumbnail_path || CONFIG.IMAGE_PLACEHOLDER).replace(/\\/g, '/')}"
                     alt="${photo.filename}"
                     class="photo-thumbnail"
                     onclick="viewPhotoDetail(${photo.id})">
                <div class="photo-overlay">
                    <button class="btn btn-light btn-sm" data-photo-id="${photo.id}" data-action="view" title="查看详情">
                        <i class="bi bi-eye"></i>
                    </button>
                    <button class="btn btn-warning btn-sm" data-photo-id="${photo.id}" data-action="edit" title="编辑">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-danger btn-sm" data-photo-id="${photo.id}" data-action="delete" title="删除">
                        <i class="bi bi-trash"></i>
                    </button>
                    <button class="btn btn-info btn-sm" data-photo-id="${photo.id}" data-action="similar" title="相似照片">
                        <i class="bi bi-search"></i>
                    </button>
                </div>
            </div>
            <div class="photo-details">
                <div class="photo-header">
                    <div class="photo-title-container">
                        <div class="photo-title">${photo.filename}</div>
                        <div class="photo-quality-container">
                            <i class="bi ${qualityStatus.icon} quality-icon ${qualityStatus.isAssessed ? 'quality-assessed' : 'quality-unassessed'}"
                               data-level="${qualityStatus.level}"
                               data-photo-id="${photo.id}"
                               onclick="event.stopPropagation(); forceBasicAnalysis(${photo.id})"
                               title="${qualityStatus.title}"
                               style="color: ${qualityStatus.color}"></i>
                            <i class="bi ${aiStatus.iconClass} ai-status-icon ${aiStatus.hasAIAnalysis ? 'ai-analyzed' : 'ai-not-analyzed'}"
                               data-photo-id="${photo.id}"
                               onclick="event.stopPropagation(); forceAIAnalysis(${photo.id})"
                               title="${aiStatus.title}"
                               style="${aiStatus.hasAIAnalysis ? '' : 'color: #6c757d;'}"></i>
                            ${hasGps ? `<i class="bi bi-geo-alt-fill gps-icon ${hasAddress ? 'gps-resolved' : 'gps-unresolved'}" data-photo-id="${photo.id}" onclick="event.stopPropagation(); resolvePhotoAddress(${photo.id}, ${hasAddress})" title="${hasAddress ? '点击重新解析地址' : '点击解析地址'}"></i>` : ''}
                            <i class="bi bi-download download-icon" 
                               data-photo-id="${photo.id}" 
                               onclick="event.stopPropagation(); downloadSinglePhoto(${photo.id})" 
                               title="下载照片"></i>
                        </div>
                    </div>
                    <div class="photo-actions">
                        <!-- 操作按钮可以在这里添加 -->
                    </div>
                </div>
                <div class="photo-meta">
                    <div class="meta-row">
                        <span class="meta-item">
                            <i class="bi bi-calendar me-1"></i>
                            ${formatDate(photo.taken_at)} (拍摄日期)
                        </span>
                        <span class="meta-item">
                            <i class="bi bi-geo-alt me-1"></i>
                            ${photo.location_name || '未知位置'}
                        </span>
                        <span class="meta-item">
                            <i class="bi bi-camera me-1"></i>
                            ${photo.camera_make || '未知'} ${photo.camera_model || ''}
                        </span>
                    </div>
                    <div class="meta-row">
                        <span class="meta-item">
                            <i class="bi bi-image me-1"></i>
                            ${resolution}
                        </span>
                        <span class="meta-item">
                            <i class="bi bi-file-earmark me-1"></i>
                            ${formatFileSize(photo.file_size)}
                        </span>
                        <span class="meta-item">
                            <i class="bi bi-clock me-1"></i>
                            ${formatDateTime(photo.created_at)}
                        </span>
                    </div>
                </div>
                <div class="photo-description">
                    ${photo.analysis?.description || '暂无描述'}
                </div>
                <div class="photo-tags">
                    <div class="visible-tags">
                        ${visibleTagsHtml}
                    </div>
                    ${hiddenTagsCount > 0 ? `
                        <div class="hidden-tags" style="display: none;">
                            ${hiddenTagsHtml}
                        </div>
                        <span class="tag-toggle" onclick="toggleTags(this, event)" data-photo-id="${photo.id}">
                            +${hiddenTagsCount} 更多
                        </span>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
}


/**
 * 全选照片
 */
function selectAllPhotos() {
    if (window.PhotoManager) {
        // 直接执行全选
        window.PhotoManager.selectAllPhotos();
    } else {
        console.error('PhotoManager 未初始化');
        showError('照片管理器未初始化，请刷新页面重试');
    }
}

/**
 * 取消选择
 */
function clearSelection() {
    // 取消选择
    if (window.PhotoManager) {
        window.PhotoManager.clearSelection();
    } else {
        console.error('PhotoManager 未初始化');
        showError('照片管理器未初始化，请刷新页面重试');
    }
}

/**
 * 删除选中照片
 */
function deleteSelectedPhotos() {
    // 删除选中照片
    if (window.PhotoManager) {
        const selectedIds = window.PhotoManager.getSelectedPhotoIds();
        if (selectedIds.length > 0) {
            window.PhotoManager.deletePhotos(selectedIds);
        } else {
            showWarning('请先选择要删除的照片');
        }
    } else {
        console.error('PhotoManager 未初始化');
        showError('照片管理器未初始化，请刷新页面重试');
    }
}

/**
 * 切换页面
 * 
 * @param {string} section - 页面名称
 */
function switchSection(section) {
    // 切换页面
    
    // 更新导航状态
    updateNavigation(section);
    
    // 根据页面显示不同内容
    switch(section) {
        case 'photos':
            showPhotosSection();
            break;
        default:
            showPhotosSection();
    }
}

/**
 * 更新导航状态
 * 
 * @param {string} activeSection - 当前激活的页面
 */
function updateNavigation(activeSection) {
    // 移除所有导航项的激活状态
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    
    // 激活当前导航项
    const activeLink = document.querySelector(`[data-section="${activeSection}"]`);
    if (activeLink) {
        activeLink.classList.add('active');
    }
}

/**
 * 显示照片页面
 */
function showPhotosSection() {
    // 显示照片网格区域
    const mainContent = document.querySelector('.row:has(.col-md-9)');
    if (mainContent) {
        mainContent.style.display = 'block';
    }
    
    // 加载照片数据
    loadPhotos();
}

// ============ 照片操作函数 ============

/**
 * 查看照片详情
 * @param {number} photoId - 照片ID
 */
async function viewPhotoDetail(photoId) {
    // 总是从API获取最新的照片详情，确保显示最新数据
    try {
        console.log('从API获取照片详情:', photoId);
        const response = await fetch(`${CONFIG.API_BASE_URL}/search/photos/${photoId}`);

        if (response.ok) {
            const result = await response.json();
            if (result.success) {
                const photo = result.data;
                showPhotoDetail(photo);
            } else {
                console.error('API返回错误:', result.message);
                alert('获取照片信息失败: ' + result.message);
            }
        } else {
            console.error('API请求失败:', response.status);
            alert('获取照片信息失败: HTTP ' + response.status);
        }
    } catch (error) {
        console.error('获取照片详情失败:', error);
        alert('获取照片信息失败: ' + error.message);
    }
}

/**
 * 编辑照片
 * @param {number} photoId - 照片ID
 */
async function editPhoto(photoId) {
    // 编辑照片
    
    // 检查是否有相似照片模态框显示，如果有则先隐藏并标记
    const similarModal = document.getElementById('similarPhotosModal');
    let wasSimilarModalVisible = false;
    if (similarModal && similarModal.classList.contains('show')) {
        const similarModalInstance = bootstrap.Modal.getInstance(similarModal);
        if (similarModalInstance) {
            similarModalInstance.hide();
            wasSimilarModalVisible = true;
        }
    }
    
    // 首先从当前显示的照片中查找
    let photo = AppState.photos.find(p => p.id === photoId);
    
    if (!photo) {
        // 如果本地找不到，通过API获取照片详情
        try {
            console.log('从API获取照片详情用于编辑:', photoId);
            const response = await fetch(`${CONFIG.API_BASE_URL}/search/photos/${photoId}`);
            
            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    photo = result.data;
                } else {
                    console.error('API返回错误:', result.message);
                    alert('获取照片信息失败: ' + result.message);
                    return;
                }
            } else {
                console.error('API请求失败:', response.status);
                alert('获取照片信息失败: HTTP ' + response.status);
                return;
            }
        } catch (error) {
            console.error('获取照片详情失败:', error);
            alert('获取照片信息失败: ' + error.message);
            return;
        }
    }
    
    // 显示编辑模态框
    showPhotoEditModal(photo);
    
    // 监听编辑模态框关闭事件，如果之前有相似搜索页显示，则重新显示
    if (wasSimilarModalVisible) {
        const editModal = document.getElementById('editPhotoModal');
        if (editModal) {
            editModal.addEventListener('hidden.bs.modal', function onEditModalHidden() {
                // 重新显示相似搜索页
                if (similarModal) {
                    const similarModalInstance = new bootstrap.Modal(similarModal);
                    similarModalInstance.show();
                }
                // 移除事件监听器，避免重复绑定
                editModal.removeEventListener('hidden.bs.modal', onEditModalHidden);
            }, { once: true });
        }
    }
}

/**
 * 删除照片
 * @param {number} photoId - 照片ID
 */
async function deletePhoto(photoId) {
    if (!confirm('确定要删除这张照片吗？')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/v1/photos/${photoId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            // 删除成功，重新加载照片
            loadPhotos();
            loadStats();
            
            // 刷新人脸识别统计（如果人物管理页面已加载）
            if (window.peopleManagementStandalone) {
                window.peopleManagementStandalone.loadPeopleData();
            }
            
            // 刷新人脸筛选栏统计（如果已加载）
            if (window.portraitFilterPanel) {
                window.portraitFilterPanel.loadClusters();
            }
            
            alert('照片删除成功');
        } else {
            const error = await response.json();
            alert('删除失败: ' + (error.detail || '未知错误'));
        }
    } catch (error) {
        console.error('删除照片失败:', error);
        alert('删除失败: ' + error.message);
    }
}

/**
 * 搜索相似照片（带服务选择）
 * @param {number} photoId - 照片ID
 */
async function searchSimilarPhotos(photoId) {
    console.log('搜索相似照片:', photoId);
    
    // 检查用户设置，决定是否显示服务选择（默认使用智能分析相似搜索）
    const defaultService = localStorage.getItem('defaultSimilarPhotoSearch') || 'enhanced';
    
    if (defaultService === 'ask') {
        // 显示服务选择弹窗
        openSimilarPhotoSearchModal(photoId);
    } else {
        // 直接使用默认服务
        await searchSimilarPhotosByService(photoId, defaultService);
    }
}

/**
 * 打开相似照片搜索服务选择弹窗
 * @param {number} photoId - 照片ID
 */
function openSimilarPhotoSearchModal(photoId) {
    // 存储当前照片ID
    window.currentSimilarPhotoSearch = {
        id: photoId
    };
    
    // 重置选择状态
    selectedSimilarSearchService = null;
    const confirmBtn = document.getElementById('confirmSimilarSearch');
    if (confirmBtn) {
        confirmBtn.disabled = true;
    }
    document.querySelectorAll('#similarPhotoSearchModal .service-option').forEach(opt => {
        opt.classList.remove('selected');
    });
    
    // 显示弹窗
    const modal = new bootstrap.Modal(document.getElementById('similarPhotoSearchModal'));
    modal.show();
}

/**
 * 根据服务类型执行相似照片搜索
 * @param {number} photoId - 照片ID
 * @param {string} serviceType - 服务类型 ('hash' | 'enhanced')
 */
async function searchSimilarPhotosByService(photoId, serviceType) {
    try {
        // 确保配置已加载
        if (!userConfig) {
            await loadUserConfig();
        }
        
        // Hash搜索：使用配置文件中的阈值，如果配置值过高（>0.6）或未设置，则使用0.5
        // 注意：纯hash搜索有局限性，只考虑图像结构相似性，不考虑颜色、时间、位置等
        // 对于视觉相似但颜色/亮度不同的照片，hash可能差异较大
        // 建议使用智能分析搜索，它综合了12个特征（hash、时间、位置、相机、AI分析等）
        // 智能搜索：使用配置文件中的阈值，默认0.85
        const configThreshold = userConfig?.search?.similarity_threshold;
        const hashThreshold = (configThreshold && configThreshold <= 0.6) ? configThreshold : 0.5;  // Hash搜索保持0.5，避免误匹配
        const enhancedThreshold = configThreshold || 0.85;  // 智能搜索保持原有阈值
        const limit = userConfig?.ui?.similar_photos_limit || 8;
        
        // 显示加载状态
        showSimilarPhotosModal(photoId);
        
        let response;
        let data;
        
        if (serviceType === 'hash') {
            // Hash相似搜索：使用简单API（注意路径是 /api/v1/search/similar）
            response = await fetch(`/api/v1/search/similar/${photoId}?threshold=${hashThreshold}&limit=${limit}`);
            
            // 检查HTTP响应状态
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: '网络请求失败' }));
                console.error('Hash相似搜索HTTP错误:', response.status, errorData);
                
                // 清理加载状态
                const resultsContainer = document.getElementById('similarPhotosResults');
                if (resultsContainer) {
                    resultsContainer.innerHTML = `
                        <div class="col-12 text-center">
                            <p class="text-danger">搜索失败</p>
                            <p class="text-muted small">${errorData.detail || 'HTTP ' + response.status}</p>
                        </div>
                    `;
                }
                alert(`搜索相似照片失败: ${errorData.detail || 'HTTP ' + response.status}`);
                return;
            }
            
            data = await response.json();
            
            if (data.success && data.data) {
                // 检查是否有相似照片
                if (!data.data.similar_photos || data.data.similar_photos.length === 0) {
                    // 没有找到相似照片，但搜索成功
                    const resultsContainer = document.getElementById('similarPhotosResults');
                    if (resultsContainer) {
                        resultsContainer.innerHTML = `
                            <div class="col-12 text-center">
                                <p class="text-muted">没有找到相似照片</p>
                                <p class="text-muted small">提示：可以尝试降低相似度阈值或使用智能分析相似搜索</p>
                            </div>
                        `;
                    }
                    return;
                }
                
                // 转换格式以适配displaySimilarPhotos函数
                const formattedData = {
                    reference_photo: data.data.reference_photo,
                    similar_photos: data.data.similar_photos.map(photo => ({
                        ...photo,
                        similarity: photo.similarity || 0
                    })),
                    total: data.data.total || data.data.similar_photos.length,
                    showPreciseMatch: false,
                    referencePhotoId: photoId
                };
                displaySimilarPhotos(formattedData);
            } else {
                console.error('Hash相似搜索失败:', data);
                
                // 清理加载状态
                const resultsContainer = document.getElementById('similarPhotosResults');
                if (resultsContainer) {
                    resultsContainer.innerHTML = `
                        <div class="col-12 text-center">
                            <p class="text-danger">搜索失败</p>
                            <p class="text-muted small">${data.detail || data.message || '未知错误'}</p>
                        </div>
                    `;
                }
                alert(`搜索相似照片失败: ${data.detail || data.message || '未知错误'}`);
            }
        } else {
            // 智能分析相似搜索：使用增强API（现有逻辑）
            response = await fetch(`/api/v1/enhanced-search/similar/first-layer/${photoId}?threshold=${enhancedThreshold}&limit=${limit}`);
            
            // 检查HTTP响应状态
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: '网络请求失败' }));
                console.error('智能相似搜索HTTP错误:', response.status, errorData);
                
                // 清理加载状态
                const resultsContainer = document.getElementById('similarPhotosResults');
                if (resultsContainer) {
                    resultsContainer.innerHTML = `
                        <div class="col-12 text-center">
                            <p class="text-danger">搜索失败</p>
                            <p class="text-muted small">${errorData.detail || 'HTTP ' + response.status}</p>
                        </div>
                    `;
                }
                alert(`搜索相似照片失败: ${errorData.detail || 'HTTP ' + response.status}`);
                return;
            }
            
            data = await response.json();
            
            if (data.success && data.data) {
                data.data.showPreciseMatch = false;
                data.data.referencePhotoId = photoId;
                displaySimilarPhotos(data.data);
            } else {
                console.error('智能相似搜索失败:', data);
                
                // 清理加载状态
                const resultsContainer = document.getElementById('similarPhotosResults');
                if (resultsContainer) {
                    resultsContainer.innerHTML = `
                        <div class="col-12 text-center">
                            <p class="text-danger">搜索失败</p>
                            <p class="text-muted small">${data.detail || data.message || '未知错误'}</p>
                        </div>
                    `;
                }
                alert(`搜索相似照片失败: ${data.detail || data.message || '未知错误'}`);
            }
        }
    } catch (error) {
        console.error('搜索相似照片出错:', error);
        
        // 清理加载状态
        const resultsContainer = document.getElementById('similarPhotosResults');
        if (resultsContainer) {
            resultsContainer.innerHTML = `
                <div class="col-12 text-center">
                    <p class="text-danger">搜索出错</p>
                    <p class="text-muted small">${error.message}</p>
                </div>
            `;
        }
        alert('搜索相似照片出错: ' + error.message);
    }
}

async function searchPreciseSimilarPhotos(photoIds, referencePhotoId) {
    try {
        // 调用第二层API精确匹配
        const photoIdsStr = photoIds.join(',');
        const response = await fetch(`/api/v1/enhanced-search/similar/second-layer/${referencePhotoId}?photo_ids=${photoIdsStr}&threshold=0.05`);
        const data = await response.json();
        
        if (data.success && data.data) {
            displaySimilarPhotos(data.data);
        } else {
            console.error('精确匹配失败:', data);
            alert('精确匹配失败');
        }
    } catch (error) {
        console.error('精确匹配出错:', error);
        alert('精确匹配出错: ' + error.message);
    }
}

// 全局变量存储当前搜索结果
let currentSimilarPhotos = null;
let currentReferencePhotoId = null;

function triggerPreciseMatch() {
    if (currentSimilarPhotos && currentReferencePhotoId) {
        const photoIds = currentSimilarPhotos.map(photo => photo.id);
        searchPreciseSimilarPhotos(photoIds, currentReferencePhotoId);
    }
}

/**
 * 显示相似照片模态框
 * @param {number} photoId - 照片ID
 */
function showSimilarPhotosModal(photoId) {
    // 检查是否有详情模态框显示，如果有则先隐藏并标记
    const photoModal = document.getElementById('photoModal');
    let wasPhotoModalVisible = false;
    if (photoModal && photoModal.classList.contains('show')) {
        const photoModalInstance = bootstrap.Modal.getInstance(photoModal);
        if (photoModalInstance) {
            photoModalInstance.hide();
            wasPhotoModalVisible = true;
        }
    }
    
    // 创建或获取相似照片模态框
    let modal = document.getElementById('similarPhotosModal');
    if (!modal) {
        modal = createSimilarPhotosModal();
        document.body.appendChild(modal);
    }
    
    // 显示模态框
    const modalInstance = new bootstrap.Modal(modal);
    modalInstance.show();
    
    // 监听相似搜索模态框关闭事件，如果之前有详情页显示，则重新显示
    if (wasPhotoModalVisible) {
        modal.addEventListener('hidden.bs.modal', function onSimilarModalHidden() {
            // 重新显示详情页
            if (photoModal) {
                const photoModalInstance = new bootstrap.Modal(photoModal);
                photoModalInstance.show();
            }
            // 移除事件监听器，避免重复绑定
            modal.removeEventListener('hidden.bs.modal', onSimilarModalHidden);
        }, { once: true });
    }
    
    // 显示加载状态
    const resultsContainer = modal.querySelector('#similarPhotosResults');
    resultsContainer.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"><span class="visually-hidden">搜索中...</span></div><p class="mt-2">正在搜索相似照片...</p></div>';
}

/**
 * 创建相似照片模态框
 */
function createSimilarPhotosModal() {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.id = 'similarPhotosModal';
    modal.setAttribute('tabindex', '-1');
    modal.innerHTML = `
        <div class="modal-dialog modal-xl">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">相似照片搜索结果</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div id="similarPhotosResults" class="row g-3">
                        <!-- 相似照片结果将在这里显示 -->
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                </div>
            </div>
        </div>
    `;
    return modal;
}

/**
 * 显示相似照片结果（V1 API格式，保留兼容性）
 * @param {Object} data - API返回的数据
 */
function displaySimilarPhotos(data) {
    const resultsContainer = document.getElementById('similarPhotosResults');
    
    // 存储当前搜索结果
    currentSimilarPhotos = data.similar_photos;
    currentReferencePhotoId = data.referencePhotoId;
    
    if (!data.similar_photos || data.similar_photos.length === 0) {
        resultsContainer.innerHTML = '<div class="col-12 text-center"><p class="text-muted">没有找到相似照片</p></div>';
        return;
    }
    
    // 显示参考照片信息
    const referencePhoto = data.reference_photo;
    let html = `
        <div class="col-12 mb-3">
            <h6>参考照片</h6>
            <div class="card">
                <div class="card-body">
                    <div class="row align-items-center">
                        <div class="col-md-2">
                            <img src="/photos_storage/${(referencePhoto.thumbnail_path || CONFIG.IMAGE_PLACEHOLDER).replace(/\\\\/g, '/')}" 
                                 class="img-thumbnail" alt="${referencePhoto.filename}">
                        </div>
                        <div class="col-md-8">
                            <h6>${referencePhoto.filename}</h6>
                            <p class="text-muted mb-0">找到 ${data.total} 张相似照片</p>
                        </div>
                        <div class="col-md-2">
                            ${data.showPreciseMatch ? `
                                <button class="btn btn-primary btn-sm" onclick="triggerPreciseMatch()">
                                    <i class="fas fa-search-plus"></i> 精确匹配
                                </button>
                            ` : ''}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 显示相似照片
    html += '<div class="col-12"><h6>相似照片</h6></div>';
    
    data.similar_photos.forEach(photo => {
        const similarityPercent = Math.round(photo.similarity * 100);
        
        // 根据照片尺寸判断方向并添加CSS类
        let containerClass = 'similar-photo-card';
        if (photo.width && photo.height) {
            if (photo.height > photo.width) {
                containerClass += ' portrait';  // 竖版
            } else if (photo.height === photo.width) {
                containerClass += ' square';    // 正方形
            } else {
                containerClass += ' landscape'; // 横版
            }
        }
        
        html += `
            <div class="col-md-3 col-sm-6 mb-3">
                <div class="card h-100">
                    <div class="position-relative similar-photo-image-container ${containerClass}">
                        <img src="/photos_storage/${(photo.thumbnail_path || CONFIG.IMAGE_PLACEHOLDER).replace(/\\\\/g, '/')}" 
                             class="card-img-top similar-photo-image" 
                             alt="${photo.filename}">
                        <div class="position-absolute top-0 end-0 m-2">
                            <span class="badge bg-primary">${similarityPercent}%</span>
                        </div>
                    </div>
                    <div class="card-body p-2">
                        <h6 class="card-title small">${photo.filename}</h6>
                        <p class="card-text small text-muted">相似度: ${similarityPercent}%</p>
                    </div>
                    <div class="card-footer p-2">
                        <div class="btn-group w-100" role="group">
                            <button class="btn btn-outline-primary btn-sm" onclick="viewPhotoDetail(${photo.id})" title="查看详情">
                                <i class="bi bi-eye"></i>
                            </button>
                            <button class="btn btn-outline-warning btn-sm" onclick="editPhoto(${photo.id})" title="编辑">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button class="btn btn-outline-danger btn-sm" onclick="deletePhoto(${photo.id})" title="删除">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    resultsContainer.innerHTML = html;
}

/**
 * 格式化文件大小
 * @param {number} bytes - 字节数
 * @returns {string} 格式化后的文件大小
 */
function formatFileSize(bytes) {
    if (!bytes) return '未知';
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;
    while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024;
        unitIndex++;
    }
    return `${size.toFixed(1)} ${units[unitIndex]}`;
}

/**
 * 显示照片编辑模态框
 * @param {Object} photo - 照片对象
 */
function showPhotoEditModal(photo) {
    console.log('显示编辑模态框:', photo);
    
    // 填充照片信息
    document.getElementById('editPhotoId').value = photo.id;
    document.getElementById('editPhotoPreview').src = `/photos_storage/${(photo.thumbnail_path || CONFIG.IMAGE_PLACEHOLDER).replace(/\\/g, '/')}`;
    
    // 填充元数据（只显示不可编辑的信息）
    const meta = [];
    if (photo.width && photo.height) meta.push(`分辨率: ${photo.width} × ${photo.height}`);
    if (photo.file_size) meta.push(`文件大小: ${formatFileSize(photo.file_size)}`);
    if (photo.format) meta.push(`格式: ${photo.format}`);
    document.getElementById('editPhotoMeta').textContent = meta.join(' | ');
    
    // 填充文件名
    document.getElementById('editPhotoFilename').value = photo.filename || '';
    
    // 填充拍摄时间（转换为datetime-local格式）
    // 🔥 修复：不考虑时区，直接使用数据库中的时间（已经是本地时间）
    if (photo.taken_at) {
        const date = new Date(photo.taken_at);
        // 使用本地时间的年月日和时分，不转换时区
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        const localDateTime = `${year}-${month}-${day}T${hours}:${minutes}`;
        document.getElementById('editPhotoTakenAt').value = localDateTime;
    } else {
        document.getElementById('editPhotoTakenAt').value = '';
    }
    
    // 填充位置名称
    document.getElementById('editPhotoLocationName').value = photo.location_name || '';
    
    // 填充描述
    document.getElementById('editPhotoDescription').value = photo.description || '';
    
    // 填充标签
    const tags = photo.tags || [];
    selectedTags = [...tags]; // 存储选中的标签
    renderSelectedTags();
    
    // 加载标签选项
    loadTagsForEdit();
    
    // 显示模态框
    const modal = new bootstrap.Modal(document.getElementById('photoEditModal'));
    modal.show();
}

// 选中的标签数组
let selectedTags = [];

/**
 * 加载分类选项
 */

/**
 * 加载标签选项
 */
async function loadTagsForEdit() {
    try {
        const response = await fetch('/api/v1/tags');
        if (response.ok) {
            const data = await response.json();
            const container = document.getElementById('availableTags');
            container.innerHTML = '';
            
            data.forEach(tag => {
                const tagElement = document.createElement('span');
                tagElement.className = 'badge bg-secondary me-1 mb-1';
                tagElement.style.cursor = 'pointer';
                tagElement.textContent = tag.name;
                tagElement.onclick = () => toggleTag(tag.name);
                container.appendChild(tagElement);
            });
        }
    } catch (error) {
        console.error('加载标签失败:', error);
    }
}

/**
 * 渲染选中的标签
 */
function renderSelectedTags() {
    const container = document.getElementById('selectedTags');
    container.innerHTML = '';
    
    selectedTags.forEach(tag => {
        const tagElement = document.createElement('span');
        tagElement.className = 'badge bg-primary me-1 mb-1';
        tagElement.innerHTML = `${tag} <i class="bi bi-x" style="cursor: pointer; margin-left: 4px;"></i>`;
        tagElement.onclick = () => removeTag(tag);
        container.appendChild(tagElement);
    });
}

/**
 * 切换标签选择状态
 */
function toggleTag(tagName) {
    if (selectedTags.includes(tagName)) {
        removeTag(tagName);
    } else {
        addTag(tagName);
    }
}

/**
 * 添加标签
 */
function addTag(tagName) {
    if (tagName && !selectedTags.includes(tagName)) {
        selectedTags.push(tagName);
        renderSelectedTags();
    }
}

/**
 * 移除标签
 */
function removeTag(tagName) {
    const index = selectedTags.indexOf(tagName);
    if (index > -1) {
        selectedTags.splice(index, 1);
        renderSelectedTags();
    }
}

/**
 * 保存照片编辑
 */
async function savePhotoEdit() {
    const photoId = document.getElementById('editPhotoId').value;
    const filename = document.getElementById('editPhotoFilename').value.trim();
    const takenAt = document.getElementById('editPhotoTakenAt').value;
    const locationName = document.getElementById('editPhotoLocationName').value.trim();
    const description = document.getElementById('editPhotoDescription').value.trim();
    
    // 使用选中的标签
    const tags = selectedTags;
    
    // 准备更新数据
    const updateData = {};
    
    // 文件名必须提供（不能为空）
    if (filename) {
        updateData.filename = filename;
    } else {
        alert('文件名不能为空');
        return;
    }
    
    // 拍摄时间：如果有值则更新，如果清空则设为空字符串（后端会处理为null）
    // 🔥 修复：不考虑时区，直接使用datetime-local的值（补全秒数）
    if (takenAt) {
        // datetime-local格式是 YYYY-MM-DDTHH:mm，补全秒数为 YYYY-MM-DDTHH:mm:00
        // 不转换为ISO（避免时区转换），后端会当作本地时间解析
        updateData.taken_at = takenAt + ':00';
    } else {
        // 允许清空时间
        updateData.taken_at = '';
    }
    
    // 位置名称：允许清空
    updateData.location_name = locationName || null;
    
    // 描述：允许清空
    updateData.description = description || null;
    
    // 标签
    updateData.tags = tags;
    
    try {
        const response = await fetch(`/api/v1/photos/${photoId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updateData)
        });
        
        if (response.ok) {
            // 保存成功，关闭模态框并重新加载照片
            const modal = bootstrap.Modal.getInstance(document.getElementById('photoEditModal'));
            modal.hide();

            // 🔥 修复：保持当前页面，不回到首页
            // 获取当前页码（如果有的话），否则使用第1页
            const currentPage = (typeof AppState !== 'undefined' && AppState.currentPage) ? AppState.currentPage : 1;
            loadPhotos(currentPage);
            loadStats();

            alert('照片信息更新成功');
        } else {
            const error = await response.json();
            alert('保存失败: ' + (error.detail || '未知错误'));
        }
    } catch (error) {
        console.error('保存照片编辑失败:', error);
        alert('保存失败: ' + error.message);
    }
}

// ============ 全局导出 ============

/**
 * 照片选择管理器
 */
class PhotoSelector {
    constructor() {
        this.selectedPhotos = new Set();
        this.initializeEventListeners();
    }

    // 初始化事件监听器
    initializeEventListeners() {
        console.log('=== 初始化PhotoSelector事件监听器 ===');

        // 监听照片卡片点击（Ctrl+点击选择）
        document.addEventListener('click', (e) => {
            const photoCard = e.target.closest('.photo-card.selectable');
            if (photoCard && !e.target.closest('.photo-overlay') && !e.target.closest('.photo-select-overlay')) {
                if (e.ctrlKey || e.metaKey) {
                    console.log('检测到Ctrl+点击照片:', photoCard.dataset.photoId);
                    e.preventDefault();
                    const photoId = photoCard.dataset.photoId;
                    const isSelected = photoCard.classList.contains('selected');
                    console.log('照片当前选中状态:', isSelected);
                    this.togglePhotoSelection(photoId, !isSelected);
                }
            }
        });
    }

    // 切换单张照片选择状态
    togglePhotoSelection(photoId, isSelected) {
        console.log('切换照片选择状态:', photoId, isSelected);

        const photoCard = document.querySelector(`[data-photo-id="${photoId}"]`);
        console.log('找到的照片卡片:', !!photoCard);

        if (isSelected) {
            this.selectedPhotos.add(parseInt(photoId));
            photoCard?.classList.add('selected');
        } else {
            this.selectedPhotos.delete(parseInt(photoId));
            photoCard?.classList.remove('selected');
        }

        console.log('当前选中照片数量:', this.selectedPhotos.size);
        console.log('准备调用updateUI');
        this.updateUI();
    }

    // 全选功能
    toggleSelectAll() {
        const allPhotoCards = document.querySelectorAll('.photo-card.selectable[data-photo-id]');
        const allSelected = allPhotoCards.length === this.selectedPhotos.size && allPhotoCards.length > 0;

        if (allSelected) {
            // 已经全部选中，清空选择
            this.clearSelection();
        } else {
            // 未全部选中，执行全选
            allPhotoCards.forEach(card => {
                const photoId = parseInt(card.dataset.photoId);
                this.selectedPhotos.add(photoId);
                card.classList.add('selected');
            });
        }

        this.updateUI();
    }

    // 取消选择
    clearSelection() {
        this.selectedPhotos.clear();
        document.querySelectorAll('.photo-card.selected').forEach(card => {
            card.classList.remove('selected');
        });
        this.updateUI();
    }

    // 更新UI状态
    updateUI() {
        const selectedCount = this.selectedPhotos.size;
        console.log('更新UI，选中数量:', selectedCount);

        if (selectedCount > 0) {
            // 启用智能处理按钮
            console.log('选中数量 > 0，启用智能处理按钮');
            this.enableProcessButtons();
        } else {
            // 禁用智能处理按钮
            console.log('选中数量 = 0，禁用智能处理按钮');
            this.disableProcessButtons();
        }

        // 更新全选按钮状态（如果存在）
        this.updateSelectAllButton();
    }

    // 更新状态统计
    updateStatusSummary() {
        const statusCounts = {
            imported: 0,
            analyzing: 0,
            quality_completed: 0,
            content_completed: 0,
            completed: 0,
            error: 0
        };

        this.selectedPhotos.forEach(photoId => {
            const photoCard = document.querySelector(`[data-photo-id="${photoId}"]`);
            if (photoCard) {
                const statusBadge = photoCard.querySelector('.photo-status-badge');
                if (statusBadge) {
                    const statusClass = Array.from(statusBadge.classList)
                        .find(cls => cls.startsWith('status-'));
                    if (statusClass) {
                        const status = statusClass.replace('status-', '');
                        statusCounts[status] = (statusCounts[status] || 0) + 1;
                    }
                }
            }
        });

        const summaryParts = [];
        if (statusCounts.imported > 0) {
            summaryParts.push(`${statusCounts.imported}张未分析`);
        }
        if (statusCounts.analyzing > 0) {
            summaryParts.push(`${statusCounts.analyzing}张分析中`);
        }
        if (statusCounts.quality_completed > 0) {
            summaryParts.push(`${statusCounts.quality_completed}张基础分析完成`);
        }
        if (statusCounts.content_completed > 0) {
            summaryParts.push(`${statusCounts.content_completed}张AI分析完成`);
        }
        if (statusCounts.completed > 0) {
            summaryParts.push(`${statusCounts.completed}张完整分析完成`);
        }
        if (statusCounts.error > 0) {
            summaryParts.push(`${statusCounts.error}张分析失败`);
        }

        document.getElementById('statusSummary').textContent =
            summaryParts.length > 0 ? ` (${summaryParts.join(', ')})` : '';
    }

    // 更新全选按钮（按钮始终显示"全选"）
    updateSelectAllButton() {
        const selectAllBtn = document.getElementById('selectAllBtn');
        if (selectAllBtn) {
            // 按钮始终显示"全选"，不再切换文本
            selectAllBtn.textContent = '全选';
        }
    }

    // 启用分析按钮
    enableProcessButtons() {
        console.log('=== 启用分析按钮 ===');
        const basicBtn = document.getElementById('basicProcessSelectedBtn');
        const aiBtn = document.getElementById('aiProcessSelectedBtn');
        const downloadBtn = document.getElementById('downloadSelectedBtn');

        if (basicBtn) {
            basicBtn.disabled = false;
            basicBtn.innerHTML = '<i class="bi bi-graph-up"></i> 基础分析';
            console.log('基础分析按钮已启用');
        } else {
            console.error('未找到基础分析按钮');
        }

        if (aiBtn) {
            aiBtn.disabled = false;
            aiBtn.innerHTML = '<i class="bi bi-robot"></i> AI分析';
            console.log('AI分析按钮已启用');
        } else {
            console.error('未找到AI分析按钮');
        }

        if (downloadBtn) {
            downloadBtn.disabled = false;
            const selectedCount = this.selectedPhotos.size;
            downloadBtn.innerHTML = selectedCount > 0 ?
                `<i class="bi bi-download"></i> 下载选中 (${selectedCount})` :
                `<i class="bi bi-download"></i> 下载选中`;
            console.log('下载按钮已启用');
        }
    }

    // 禁用分析按钮
    disableProcessButtons() {
        console.log('禁用分析按钮');
        const basicBtn = document.getElementById('basicProcessSelectedBtn');
        const aiBtn = document.getElementById('aiProcessSelectedBtn');
        const downloadBtn = document.getElementById('downloadSelectedBtn');

        if (basicBtn) {
            basicBtn.disabled = true;
            basicBtn.innerHTML = '<i class="bi bi-graph-up"></i> 基础分析';
            console.log('基础分析按钮已禁用');
        } else {
            console.error('未找到基础分析按钮');
        }

        if (aiBtn) {
            aiBtn.disabled = true;
            aiBtn.innerHTML = '<i class="bi bi-robot"></i> AI分析';
            console.log('AI分析按钮已禁用');
        } else {
            console.error('未找到AI分析按钮');
        }

        if (downloadBtn) {
            downloadBtn.disabled = true;
            downloadBtn.innerHTML = '<i class="bi bi-download"></i> 下载选中';
        }
    }

    // 获取选中的照片ID列表
    getSelectedPhotoIds() {
        return Array.from(this.selectedPhotos);
    }

    // 获取照片详情（用于状态判断）
    async getPhotoDetails(photoId) {
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/photos/${photoId}`);
            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.error('获取照片详情失败:', error);
        }
        return null;
    }
}

// 创建全局实例
console.log('=== 创建PhotoSelector实例 ===');
window.photoSelector = new PhotoSelector();
console.log('PhotoSelector实例创建完成:', !!window.photoSelector);

// 将函数导出到全局作用域
window.createPhotoCard = createPhotoCard;
window.createPhotoListItem = createPhotoListItem;
window.selectAllPhotos = selectAllPhotos;
window.clearSelection = clearSelection;
window.deleteSelectedPhotos = deleteSelectedPhotos;
window.switchSection = switchSection;
window.updateNavigation = updateNavigation;
window.showPhotosSection = showPhotosSection;
window.viewPhotoDetail = viewPhotoDetail;
window.editPhoto = editPhoto;
window.deletePhoto = deletePhoto;
window.searchSimilarPhotos = searchSimilarPhotos;
window.openSimilarPhotoSearchModal = openSimilarPhotoSearchModal;
window.searchSimilarPhotosByService = searchSimilarPhotosByService;
window.displaySimilarPhotos = displaySimilarPhotos;
window.showPhotoEditModal = showPhotoEditModal;
window.savePhotoEdit = savePhotoEdit;

// 照片选择相关函数
window.processSelectedPhotos = () => {
    console.log('processSelectedPhotos函数被调用');
    console.log('智能处理功能已移除，请使用基础分析或AI分析功能');
    showWarning('智能处理功能已移除，请使用基础分析或AI分析功能');
};

window.reprocessSelectedPhotos = () => {
    console.log('reprocessSelectedPhotos函数被调用');
    console.log('智能处理功能已移除，请使用基础分析或AI分析功能');
    showWarning('智能处理功能已移除，请使用基础分析或AI分析功能');
};

/**
 * 切换照片选择状态
 * @param {number} photoId - 照片ID
 * @param {Event} event - 点击事件
 */
function togglePhotoSelection(photoId, event) {
    // 完全阻止事件传播和默认行为
    event.preventDefault();
    event.stopPropagation();
    event.stopImmediatePropagation();

    console.log('切换照片选择状态:', photoId);

    if (window.PhotoManager) {
        // 获取当前选择状态
        const isSelected = window.PhotoManager.getSelectedPhotoIds().includes(photoId);

        if (isSelected) {
            // 取消选择
            window.PhotoManager.clearSelectionForPhoto(photoId);
        } else {
            // 选择照片
            window.PhotoManager.selectPhoto(photoId);
        }

        // 更新选择框视觉状态
        updateSelectionCheckboxVisual(photoId);
    } else {
        console.error('PhotoManager 未初始化');
    }

    return false; // 额外确保不执行默认行为
}

/**
 * 更新选择框的视觉状态
 * @param {number} photoId - 照片ID
 */
function updateSelectionCheckboxVisual(photoId) {
    const checkbox = document.querySelector(`.photo-selection-checkbox[data-photo-id="${photoId}"]`);
    const photoCard = document.querySelector(`.photo-card[data-photo-id="${photoId}"], .photo-list-item[data-photo-id="${photoId}"]`);

    if (checkbox && photoCard) {
        const isSelected = window.PhotoManager ?
            window.PhotoManager.getSelectedPhotoIds().includes(photoId) : false;

        if (isSelected) {
            checkbox.classList.add('selected');
            photoCard.classList.add('selected');
        } else {
            checkbox.classList.remove('selected');
            photoCard.classList.remove('selected');
        }
    }
}

/**
 * 初始化所有选择框的视觉状态
 */
function initializeSelectionCheckboxes() {
    if (!window.PhotoManager) {
        console.warn('PhotoManager 未初始化，跳过选择框初始化');
        return;
    }

    const selectedPhotoIds = window.PhotoManager.getSelectedPhotoIds();

    // 更新所有已选择照片的选择框状态
    selectedPhotoIds.forEach(photoId => {
        updateSelectionCheckboxVisual(photoId);
    });

    console.log('选择框视觉状态初始化完成');
}

/**
 * GPS转地址功能
 */
async function resolvePhotoAddress(photoId, hasExistingAddress) {
    const gpsIcon = document.querySelector(`.gps-icon[data-photo-id="${photoId}"]`);
    if (!gpsIcon) return;

    // 检查用户设置，决定是否显示服务选择
    const defaultService = localStorage.getItem('defaultGeocodingService') || 'ask';
    
    if (defaultService === 'ask') {
        // 显示服务选择弹窗
        openGeocodingServiceModal(photoId, hasExistingAddress);
    } else {
        // 直接使用默认服务
        await convertPhotoAddress(photoId, defaultService, hasExistingAddress);
    }
}

/**
 * 打开服务选择弹窗
 */
function openGeocodingServiceModal(photoId, hasExistingAddress) {
    // 存储当前照片信息
    window.currentGeocodingPhoto = {
        id: photoId,
        hasExistingAddress: hasExistingAddress
    };
    
    // 重置选择状态
    selectedGeocodingService = null;
    document.getElementById('confirmGeocoding').disabled = true;
    document.querySelectorAll('.service-option').forEach(opt => {
        opt.classList.remove('selected');
    });
    
    // 检查服务状态
    checkServiceStatus();
    
    // 显示弹窗
    const modal = new bootstrap.Modal(document.getElementById('geocodingServiceModal'));
    modal.show();
}

/**
 * 转换照片地址
 */
async function convertPhotoAddress(photoId, service, hasExistingAddress) {
    const gpsIcon = document.querySelector(`.gps-icon[data-photo-id="${photoId}"]`);
    if (!gpsIcon) return;

    const originalClass = gpsIcon.className;

    try {
        // 显示加载状态
        gpsIcon.className = 'bi bi-geo-alt-fill gps-icon processing';
        gpsIcon.title = '解析中...';

        const force = hasExistingAddress; // 如果已有地址，强制更新

        const response = await fetch(`/api/maps/photos/${photoId}/convert-gps-address`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                service: service,
                force: force
            })
        });

        const result = await response.json();

        if (response.ok && result.success) {
            // 更新UI显示地址和GPS图标状态
            updatePhotoAddress(photoId, result.address);
            showServiceResult(result.service, result.address, result.cached);
        } else {
            // 恢复原来的状态
            gpsIcon.className = originalClass;
            gpsIcon.title = hasExistingAddress ? '点击重新解析地址' : '点击解析地址';
            showToast(result.message || '地址解析失败', 'error');
        }

    } catch (error) {
        console.error('地址解析失败:', error);
        // 恢复原来的状态
        gpsIcon.className = originalClass;
        gpsIcon.title = hasExistingAddress ? '点击重新解析地址' : '点击解析地址';
        showToast('地址解析失败，请检查网络连接', 'error');
    }
}

/**
 * 显示服务结果
 */
function showServiceResult(service, address, cached) {
    const serviceNames = {
        'amap': '高德地图API',
        'offline': '离线数据库',
        'nominatim': 'Nominatim API',
        'cache': '缓存'
    };
    
    let message;
    if (cached) {
        message = `使用缓存地址 (来源: ${serviceNames[service]})`;
    } else {
        message = `地址解析成功！\n服务: ${serviceNames[service]}\n地址: ${address}`;
    }
    
    showToast(message, 'success');
}

/**
 * 检查服务状态
 */
async function checkServiceStatus() {
    try {
        const response = await fetch('/api/maps/service-status');
        const status = await response.json();
        
        // 更新高德API状态
        const amapStatus = document.getElementById('amap-status');
        const amapStatusText = document.getElementById('amap-status-text');
        
        if (status.amap.available) {
            amapStatus.className = 'status-indicator ready';
            amapStatusText.textContent = '服务可用';
        } else {
            amapStatus.className = 'status-indicator error';
            amapStatusText.textContent = status.amap.reason || '服务不可用';
        }
        
        // 更新Nominatim API状态
        const nominatimStatus = document.getElementById('nominatim-status');
        const nominatimStatusText = document.getElementById('nominatim-status-text');
        
        if (status.nominatim.available) {
            nominatimStatus.className = 'status-indicator ready';
            nominatimStatusText.textContent = '服务可用';
        } else {
            nominatimStatus.className = 'status-indicator error';
            nominatimStatusText.textContent = status.nominatim.reason || '服务不可用';
        }
    } catch (error) {
        const amapStatus = document.getElementById('amap-status');
        const amapStatusText = document.getElementById('amap-status-text');
        amapStatus.className = 'status-indicator error';
        amapStatusText.textContent = '检查失败';
        
        const nominatimStatus = document.getElementById('nominatim-status');
        const nominatimStatusText = document.getElementById('nominatim-status-text');
        nominatimStatus.className = 'status-indicator error';
        nominatimStatusText.textContent = '检查失败';
    }
}

// 全局变量
let selectedGeocodingService = null;
let selectedSimilarSearchService = null;

// 服务选择事件处理
document.addEventListener('DOMContentLoaded', function() {
    // GPS转地址服务选择事件
    document.querySelectorAll('#geocodingServiceModal .service-option').forEach(option => {
        option.addEventListener('click', function() {
            // 移除其他选中状态
            document.querySelectorAll('#geocodingServiceModal .service-option').forEach(opt => {
                opt.classList.remove('selected');
            });
            
            // 添加选中状态
            this.classList.add('selected');
            selectedGeocodingService = this.dataset.service;
            
            // 启用确认按钮
            document.getElementById('confirmGeocoding').disabled = false;
        });
    });

    // GPS转地址确认选择
    document.getElementById('confirmGeocoding').addEventListener('click', async function() {
        if (!selectedGeocodingService || !window.currentGeocodingPhoto) return;
        
        const { id: photoId, hasExistingAddress } = window.currentGeocodingPhoto;
        await convertPhotoAddress(photoId, selectedGeocodingService, hasExistingAddress);
        
        // 关闭弹窗
        const modal = bootstrap.Modal.getInstance(document.getElementById('geocodingServiceModal'));
        modal.hide();
    });

    // GPS转地址取消选择
    document.getElementById('geocodingServiceModal').addEventListener('hidden.bs.modal', function() {
        window.currentGeocodingPhoto = null;
        selectedGeocodingService = null;
    });

    // 相似照片搜索服务选择事件
    document.querySelectorAll('#similarPhotoSearchModal .service-option').forEach(option => {
        option.addEventListener('click', function() {
            // 移除其他选中状态
            document.querySelectorAll('#similarPhotoSearchModal .service-option').forEach(opt => {
                opt.classList.remove('selected');
            });
            
            // 添加选中状态
            this.classList.add('selected');
            selectedSimilarSearchService = this.dataset.service;
            
            // 启用确认按钮
            document.getElementById('confirmSimilarSearch').disabled = false;
        });
    });

    // 相似照片搜索确认选择
    document.getElementById('confirmSimilarSearch').addEventListener('click', async function() {
        if (!selectedSimilarSearchService || !window.currentSimilarPhotoSearch) return;
        
        const { id: photoId } = window.currentSimilarPhotoSearch;
        await searchSimilarPhotosByService(photoId, selectedSimilarSearchService);
        
        // 关闭弹窗
        const modal = bootstrap.Modal.getInstance(document.getElementById('similarPhotoSearchModal'));
        modal.hide();
    });

    // 相似照片搜索取消选择
    document.getElementById('similarPhotoSearchModal').addEventListener('hidden.bs.modal', function() {
        window.currentSimilarPhotoSearch = null;
        selectedSimilarSearchService = null;
    });
});

function updatePhotoAddress(photoId, address) {
    console.log('开始更新照片地址:', photoId, address);
    const photoCard = document.querySelector(`.photo-card[data-photo-id="${photoId}"], .photo-list-item[data-photo-id="${photoId}"]`);
    if (!photoCard) {
        console.warn('未找到照片卡片:', photoId);
        return;
    }
    console.log('找到照片卡片:', photoCard.className);

    // 更新data属性
    photoCard.setAttribute('data-has-address', 'true');

    // 查找或创建地址显示元素
    let addressDiv = photoCard.querySelector('.photo-address');
    if (!addressDiv) {
        // 如果不存在，添加到photo-meta中
        const photoMeta = photoCard.querySelector('.photo-meta');
        if (photoMeta) {
            addressDiv = document.createElement('div');
            addressDiv.className = 'photo-address';
            addressDiv.innerHTML = `
                <i class="bi bi-geo-alt me-1"></i>
                <span class="address-text">${address.length > 30 ? address.substring(0, 30) + '...' : address}</span>
            `;
            addressDiv.title = address;
            photoMeta.appendChild(addressDiv);
        }
    } else {
        // 更新现有地址
        const addressText = addressDiv.querySelector('.address-text');
        if (addressText) {
            addressText.textContent = address.length > 30 ? address.substring(0, 30) + '...' : address;
            addressDiv.title = address;
        }
    }

    // 更新GPS图标状态为已解析
    const gpsIcon = photoCard.querySelector('.gps-icon');
    if (gpsIcon) {
        gpsIcon.className = 'bi bi-geo-alt-fill gps-icon gps-resolved';
        gpsIcon.title = '点击重新解析地址';
        gpsIcon.onclick = (e) => {
            e.stopPropagation();
            resolvePhotoAddress(photoId, true);
        };
        console.log('GPS图标状态已更新为已解析:', photoId);
    } else {
        console.warn('未找到GPS图标，无法更新状态:', photoId);
    }
}

window.getProcessingStatus = getProcessingStatus;
window.togglePhotoSelection = togglePhotoSelection;
window.updateSelectionCheckboxVisual = updateSelectionCheckboxVisual;
window.initializeSelectionCheckboxes = initializeSelectionCheckboxes;
window.resolvePhotoAddress = resolvePhotoAddress;
window.updatePhotoAddress = updatePhotoAddress;
window.downloadSinglePhoto = downloadSinglePhoto;
window.downloadSelectedPhotos = downloadSelectedPhotos;

/**
 * 强制基础分析单张照片（同步处理）
 */
async function forceBasicAnalysis(photoId) {
    const qualityIcon = document.querySelector(`.quality-icon[data-photo-id="${photoId}"]`);
    if (!qualityIcon) return;

    // 确认对话框
    const isAssessed = qualityIcon.classList.contains('quality-assessed');
    const confirmMessage = isAssessed 
        ? '确定要强制重新进行基础分析吗？' 
        : '确定要进行基础分析吗？';
    
    if (!confirm(confirmMessage)) {
        return;
    }

    // 保存原始状态
    const originalClass = qualityIcon.className;
    const originalTitle = qualityIcon.title;
    
    try {
        // 显示加载状态
        qualityIcon.className = 'quality-icon processing';
        qualityIcon.title = '分析中...';
        qualityIcon.style.opacity = '0.5';

        // 调用同步API（暂用异步接口，等待后续添加同步接口）
        const response = await fetch(`${CONFIG.API_BASE_URL}/analysis/photos/${photoId}/analyze-quality`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        });

        const result = await response.json();

        if (response.ok && result.success) {
            // 🔥 修复：保持当前页面，不回到首页
            // 获取当前页码（如果有的话），否则使用第1页
            const currentPage = (typeof AppState !== 'undefined' && AppState.currentPage) ? AppState.currentPage : 1;
            await window.loadPhotos(currentPage);
            await window.loadStats();
            
            showToast('基础分析完成', 'success');
        } else {
            // 恢复原状态
            qualityIcon.className = originalClass;
            qualityIcon.title = originalTitle;
            qualityIcon.style.opacity = '';
            showToast(result.message || '基础分析失败', 'error');
        }

    } catch (error) {
        console.error('基础分析失败:', error);
        // 恢复原状态
        qualityIcon.className = originalClass;
        qualityIcon.title = originalTitle;
        qualityIcon.style.opacity = '';
        showToast('基础分析失败，请检查网络连接', 'error');
    }
}

window.forceBasicAnalysis = forceBasicAnalysis;

/**
 * 强制AI分析单张照片（同步处理）
 */
async function forceAIAnalysis(photoId) {
    const aiIcon = document.querySelector(`.ai-status-icon[data-photo-id="${photoId}"]`);
    if (!aiIcon) return;

    // 确认对话框
    const hasAnalysis = aiIcon.classList.contains('ai-analyzed');
    const confirmMessage = hasAnalysis 
        ? '确定要强制重新进行AI分析吗？' 
        : '确定要进行AI分析吗？';
    
    if (!confirm(confirmMessage)) {
        return;
    }

    // 保存原始状态
    const originalClass = aiIcon.className;
    const originalTitle = aiIcon.title;
    const originalStyle = aiIcon.getAttribute('style') || '';
    
    try {
        // 显示加载状态
        aiIcon.className = 'ai-status-icon processing';
        aiIcon.title = '分析中...';
        aiIcon.style.opacity = '0.5';

        // 调用同步API
        const response = await fetch(`${CONFIG.API_BASE_URL}/analysis/photos/${photoId}/analyze-ai`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        });

        const result = await response.json();

        if (response.ok && result.success) {
            // 🔥 修复：保持当前页面，不回到首页
            // 获取当前页码（如果有的话），否则使用第1页
            const currentPage = (typeof AppState !== 'undefined' && AppState.currentPage) ? AppState.currentPage : 1;
            await window.loadPhotos(currentPage);
            await window.loadStats();
            
            showToast('AI分析完成', 'success');
        } else {
            // 恢复原状态
            aiIcon.className = originalClass;
            aiIcon.title = originalTitle;
            aiIcon.setAttribute('style', originalStyle);
            showToast(result.message || 'AI分析失败', 'error');
        }

    } catch (error) {
        console.error('AI分析失败:', error);
        // 恢复原状态
        aiIcon.className = originalClass;
        aiIcon.title = originalTitle;
        aiIcon.setAttribute('style', originalStyle);
        showToast('AI分析失败，请检查网络连接', 'error');
    }
}

/**
 * 批量下载选中的照片
 * 
 * :param photoIds: 照片ID数组
 */
async function downloadSelectedPhotos(photoIds) {
    if (!photoIds || photoIds.length === 0) {
        showToast('请先选择要下载的照片', 'warning');
        return;
    }

    const downloadBtn = document.getElementById('downloadSelectedBtn');
    const originalText = downloadBtn ? downloadBtn.innerHTML : '';

    try {
        // 更新按钮状态
        if (downloadBtn) {
            downloadBtn.disabled = true;
            downloadBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> 下载中...';
        }

        showToast(`开始下载 ${photoIds.length} 张照片...`, 'info');

        // 依次下载每张照片
        for (let i = 0; i < photoIds.length; i++) {
            const photoId = photoIds[i];
            const downloadUrl = `${CONFIG.API_BASE_URL}/photos/${photoId}/download`;

            // 创建隐藏的下载链接
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.download = '';
            link.style.display = 'none';
            document.body.appendChild(link);

            // 触发下载
            link.click();

            // 清理
            document.body.removeChild(link);

            // 添加延迟，避免浏览器阻止多个下载
            if (i < photoIds.length - 1) {
                await new Promise(resolve => setTimeout(resolve, 200));
            }
        }

        console.log('批量下载完成:', photoIds.length, '张照片');

        // 恢复按钮状态
        if (downloadBtn) {
            downloadBtn.disabled = false;
            downloadBtn.innerHTML = originalText;
        }

        showToast(`成功下载 ${photoIds.length} 张照片`, 'success');

    } catch (error) {
        console.error('批量下载失败:', error);

        // 恢复按钮状态
        if (downloadBtn) {
            downloadBtn.disabled = false;
            downloadBtn.innerHTML = originalText;
        }

        showToast('批量下载失败，请重试', 'error');
    }
}

/**
 * 下载单张照片
 * 
 * :param photoId: 照片ID
 */
async function downloadSinglePhoto(photoId) {
    const downloadIcon = document.querySelector(`.download-icon[data-photo-id="${photoId}"]`);
    if (!downloadIcon) return;

    const originalClass = downloadIcon.className;
    const originalTitle = downloadIcon.title;

    try {
        // 更新图标状态
        downloadIcon.className = 'bi bi-hourglass-split download-icon processing';
        downloadIcon.title = '下载中...';
        downloadIcon.style.opacity = '0.5';

        // 构建下载URL
        const downloadUrl = `${CONFIG.API_BASE_URL}/photos/${photoId}/download`;

        // 创建隐藏的下载链接
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = ''; // 让服务器决定文件名
        link.style.display = 'none';
        document.body.appendChild(link);

        // 触发下载
        link.click();

        // 清理
        document.body.removeChild(link);

        console.log('照片下载已开始:', photoId);

        // 恢复图标状态
        setTimeout(() => {
            downloadIcon.className = originalClass;
            downloadIcon.title = originalTitle;
            downloadIcon.style.opacity = '';
            showToast('下载已开始', 'success');
        }, 1000);

    } catch (error) {
        console.error('下载照片失败:', error);
        
        // 恢复图标状态
        downloadIcon.className = originalClass;
        downloadIcon.title = originalTitle;
        downloadIcon.style.opacity = '';
        
        showToast('下载失败，请重试', 'error');
    }
}

window.forceAIAnalysis = forceAIAnalysis;

/**
 * 批量编辑选中照片
 */
function batchEditSelectedPhotos() {
    if (!window.PhotoManager) {
        showError('照片管理器未初始化，请刷新页面重试');
        return;
    }

    const selectedIds = window.PhotoManager.getSelectedPhotoIds();
    if (selectedIds.length === 0) {
        showWarning('请先选择要编辑的照片');
        return;
    }

    // 显示批量编辑模态框
    showBatchEditModal(selectedIds);
}

/**
 * 显示批量编辑模态框
 * @param {number[]} photoIds - 选中的照片ID列表
 */
function showBatchEditModal(photoIds) {
    // 更新选中数量
    document.getElementById('batchEditSelectedCount').textContent = `已选择 ${photoIds.length} 张照片`;
    
    // 重置表单和状态
    document.getElementById('batchEditForm').reset();
    batchEditSelectedTags = [];
    batchEditRemoveTags = [];
    document.getElementById('batchEditSelectedTags').innerHTML = '';
    document.getElementById('batchEditRemoveTags').innerHTML = '';
    
    // 隐藏所有输入区域
    document.getElementById('batchEditTagsInput').style.display = 'none';
    document.getElementById('batchEditTagsToRemove').style.display = 'none';
    document.getElementById('batchEditCategoriesInput').style.display = 'none';
    document.getElementById('batchEditTakenAtInput').style.display = 'none';
    document.getElementById('batchEditLocationInput').style.display = 'none';
    document.getElementById('batchEditDescriptionInput').style.display = 'none';
    document.getElementById('batchEditFilenameInput').style.display = 'none';
    document.getElementById('batchEditFilenamePrefixInput').style.display = 'none';
    document.getElementById('batchEditFilenameSuffixInput').style.display = 'none';
    document.getElementById('batchEditFilenameTemplateInput').style.display = 'none';
    // 重置起始序号为默认值1
    const startIndexInput = document.getElementById('batchEditFilenameStartIndex');
    if (startIndexInput) {
        startIndexInput.value = '1';
    }
    
    // 加载分类选项
    loadCategoriesForBatchEdit();
    
    // 绑定标签操作选择器的事件
    bindBatchEditTagOperationEvents();
    bindBatchEditCategoriesOperationEvents();
    bindBatchEditTakenAtOperationEvents();
    bindBatchEditLocationOperationEvents();
    bindBatchEditDescriptionOperationEvents();
    bindBatchEditFilenameOperationEvents();
    bindBatchEditTagInputEvents();
    
    // 显示模态框
    const modal = new bootstrap.Modal(document.getElementById('batchEditModal'));
    modal.show();
}

/**
 * 绑定标签操作选择器事件
 */
function bindBatchEditTagOperationEvents() {
    const select = document.getElementById('batchEditTagsOperation');
    if (!select) return;
    
    // 移除旧的事件监听器
    const newSelect = select.cloneNode(true);
    select.parentNode.replaceChild(newSelect, select);
    
    newSelect.addEventListener('change', function() {
        const inputDiv = document.getElementById('batchEditTagsInput');
        const removeDiv = document.getElementById('batchEditTagsToRemove');
        const value = this.value;
        
        if (value === '' || value === 'clear') {
            // 不修改标签或清空所有标签，都不需要输入框
            inputDiv.style.display = 'none';
            removeDiv.style.display = 'none';
            batchEditSelectedTags = [];
            batchEditRemoveTags = [];
            document.getElementById('batchEditSelectedTags').innerHTML = '';
            document.getElementById('batchEditRemoveTags').innerHTML = '';
        } else if (value === 'remove') {
            // 移除标签：需要输入框来输入要移除的标签
            inputDiv.style.display = 'block';
            removeDiv.style.display = 'block';
            batchEditSelectedTags = [];
            document.getElementById('batchEditSelectedTags').innerHTML = '';
        } else {
            // 追加或替换标签：需要输入框来输入要添加的标签
            inputDiv.style.display = 'block';
            removeDiv.style.display = 'none';
            batchEditRemoveTags = [];
            document.getElementById('batchEditRemoveTags').innerHTML = '';
        }
    });
}

/**
 * 绑定分类操作选择器事件
 */
function bindBatchEditCategoriesOperationEvents() {
    const select = document.getElementById('batchEditCategoriesOperation');
    if (!select) return;
    
    const newSelect = select.cloneNode(true);
    select.parentNode.replaceChild(newSelect, select);
    
    newSelect.addEventListener('change', function() {
        const inputDiv = document.getElementById('batchEditCategoriesInput');
        const value = this.value;
        
        if (value === '' || value === 'clear') {
            // 不修改分类或清空所有分类，都不需要输入框
            inputDiv.style.display = 'none';
        } else {
            // 追加、移除或替换分类：需要输入框来选择分类
            inputDiv.style.display = 'block';
        }
    });
}

/**
 * 绑定拍摄时间操作选择器事件
 */
function bindBatchEditTakenAtOperationEvents() {
    const select = document.getElementById('batchEditTakenAtOperation');
    if (!select) return;
    
    const newSelect = select.cloneNode(true);
    select.parentNode.replaceChild(newSelect, select);
    
    newSelect.addEventListener('change', function() {
        const inputDiv = document.getElementById('batchEditTakenAtInput');
        const value = this.value;
        
        if (value === '' || value === 'clear') {
            inputDiv.style.display = 'none';
        } else {
            inputDiv.style.display = 'block';
        }
    });
}

/**
 * 绑定位置操作选择器事件
 */
function bindBatchEditLocationOperationEvents() {
    const select = document.getElementById('batchEditLocationOperation');
    if (!select) return;
    
    const newSelect = select.cloneNode(true);
    select.parentNode.replaceChild(newSelect, select);
    
    newSelect.addEventListener('change', function() {
        const inputDiv = document.getElementById('batchEditLocationInput');
        const value = this.value;
        
        if (value === '' || value === 'clear') {
            inputDiv.style.display = 'none';
        } else {
            inputDiv.style.display = 'block';
        }
    });
}

/**
 * 绑定描述操作选择器事件
 */
function bindBatchEditDescriptionOperationEvents() {
    const select = document.getElementById('batchEditDescriptionOperation');
    if (!select) return;
    
    const newSelect = select.cloneNode(true);
    select.parentNode.replaceChild(newSelect, select);
    
    newSelect.addEventListener('change', function() {
        const inputDiv = document.getElementById('batchEditDescriptionInput');
        const value = this.value;
        
        if (value === '' || value === 'clear') {
            inputDiv.style.display = 'none';
        } else {
            inputDiv.style.display = 'block';
        }
    });
}

/**
 * 绑定文件名操作选择器事件
 */
function bindBatchEditFilenameOperationEvents() {
    const select = document.getElementById('batchEditFilenameOperation');
    if (!select) return;
    
    const newSelect = select.cloneNode(true);
    select.parentNode.replaceChild(newSelect, select);
    
    newSelect.addEventListener('change', function() {
        const inputDiv = document.getElementById('batchEditFilenameInput');
        const prefixInput = document.getElementById('batchEditFilenamePrefixInput');
        const suffixInput = document.getElementById('batchEditFilenameSuffixInput');
        const templateInput = document.getElementById('batchEditFilenameTemplateInput');
        const value = this.value;
        
        if (value === '') {
            inputDiv.style.display = 'none';
            prefixInput.style.display = 'none';
            suffixInput.style.display = 'none';
            templateInput.style.display = 'none';
        } else {
            inputDiv.style.display = 'block';
            if (value === 'add_prefix') {
                prefixInput.style.display = 'block';
                suffixInput.style.display = 'none';
                templateInput.style.display = 'none';
            } else if (value === 'add_suffix') {
                prefixInput.style.display = 'none';
                suffixInput.style.display = 'block';
                templateInput.style.display = 'none';
            } else if (value === 'set') {
                prefixInput.style.display = 'none';
                suffixInput.style.display = 'none';
                templateInput.style.display = 'block';
                // 重置起始序号为默认值1
                document.getElementById('batchEditFilenameStartIndex').value = '1';
            }
        }
    });
}

/**
 * 绑定标签输入框事件
 */
function bindBatchEditTagInputEvents() {
    const input = document.getElementById('batchEditTags');
    const addBtn = document.getElementById('batchEditAddTagBtn');
    
    if (!input || !addBtn) return;
    
    // 移除旧的事件监听器
    const newInput = input.cloneNode(true);
    input.parentNode.replaceChild(newInput, input);
    
    const newAddBtn = addBtn.cloneNode(true);
    addBtn.parentNode.replaceChild(newAddBtn, addBtn);
    
    // Enter键添加标签
    newInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            const tagName = this.value.trim();
            if (tagName) {
                addBatchEditTag(tagName);
            }
        }
    });
    
    // 按钮点击添加标签
    newAddBtn.addEventListener('click', function() {
        const tagName = document.getElementById('batchEditTags').value.trim();
        if (tagName) {
            addBatchEditTag(tagName);
        }
    });
    
    // 支持逗号分隔的多个标签
    newInput.addEventListener('blur', function() {
        const value = this.value.trim();
        if (value.includes(',')) {
            const tags = value.split(',').map(t => t.trim()).filter(t => t);
            tags.forEach(tag => addBatchEditTag(tag));
            this.value = '';
        }
    });
}

// 批量编辑相关的变量
let batchEditSelectedTags = [];
let batchEditRemoveTags = [];

/**
 * 加载分类选项供批量编辑使用
 */
async function loadCategoriesForBatchEdit() {
    try {
        const response = await fetch('/api/v1/categories');
        if (response.ok) {
            const categories = await response.json();
            const select = document.getElementById('batchEditCategoryIds');
            select.innerHTML = '';
            categories.forEach(cat => {
                const option = document.createElement('option');
                option.value = cat.id;
                option.textContent = cat.name;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('加载分类失败:', error);
    }
}

/**
 * 保存批量编辑
 */
async function saveBatchEdit() {
    if (!window.PhotoManager) {
        showError('照片管理器未初始化');
        return;
    }

    const selectedIds = window.PhotoManager.getSelectedPhotoIds();
    if (selectedIds.length === 0) {
        showWarning('没有选中的照片');
        return;
    }

    // 准备请求数据
    const requestData = {
        photo_ids: selectedIds
    };

    // 标签操作
    const tagsOperation = document.getElementById('batchEditTagsOperation').value;
    if (tagsOperation) {
        requestData.tags_operation = tagsOperation;
        if (tagsOperation === 'add' || tagsOperation === 'replace') {
            requestData.tags = batchEditSelectedTags;
        }
        if (tagsOperation === 'remove') {
            requestData.tags_to_remove = batchEditRemoveTags;
        }
    }

    // 分类操作
    const categoriesOperation = document.getElementById('batchEditCategoriesOperation').value;
    if (categoriesOperation) {
        requestData.categories_operation = categoriesOperation;
        const categorySelect = document.getElementById('batchEditCategoryIds');
        const selectedCategories = Array.from(categorySelect.selectedOptions).map(opt => parseInt(opt.value));
        if (categoriesOperation === 'add' || categoriesOperation === 'replace') {
            requestData.category_ids = selectedCategories;
        }
        if (categoriesOperation === 'remove') {
            requestData.category_ids_to_remove = selectedCategories;
        }
    }

    // 拍摄时间操作
    const takenAtOperation = document.getElementById('batchEditTakenAtOperation').value;
    if (takenAtOperation) {
        requestData.taken_at_operation = takenAtOperation;
        if (takenAtOperation === 'set' || takenAtOperation === 'fill_empty') {
            const takenAt = document.getElementById('batchEditTakenAt').value;
            if (takenAt) {
                requestData.taken_at = takenAt + ':00';  // 补全秒数
            }
        }
    }

    // 位置操作
    const locationOperation = document.getElementById('batchEditLocationOperation').value;
    if (locationOperation) {
        requestData.location_name_operation = locationOperation;
        if (locationOperation === 'set' || locationOperation === 'fill_empty') {
            requestData.location_name = document.getElementById('batchEditLocationName').value.trim();
        }
    }

    // 描述操作
    const descriptionOperation = document.getElementById('batchEditDescriptionOperation').value;
    if (descriptionOperation) {
        requestData.description_operation = descriptionOperation;
        if (descriptionOperation === 'set' || descriptionOperation === 'append') {
            requestData.description = document.getElementById('batchEditDescription').value.trim();
        }
    }

    // 文件名操作
    const filenameOperation = document.getElementById('batchEditFilenameOperation').value;
    if (filenameOperation) {
        requestData.filename_operation = filenameOperation;
        if (filenameOperation === 'add_prefix') {
            requestData.filename_prefix = document.getElementById('batchEditFilenamePrefix').value.trim();
            if (!requestData.filename_prefix) {
                showWarning('请输入文件名前缀');
                return;
            }
        } else if (filenameOperation === 'add_suffix') {
            requestData.filename_suffix = document.getElementById('batchEditFilenameSuffix').value.trim();
            if (!requestData.filename_suffix) {
                showWarning('请输入文件名后缀');
                return;
            }
        } else if (filenameOperation === 'set') {
            requestData.filename_template = document.getElementById('batchEditFilenameTemplate').value.trim();
            if (!requestData.filename_template) {
                showWarning('请输入文件名模板');
                return;
            }
            // 读取起始序号，如果为空或无效则使用默认值1
            const startIndexInput = document.getElementById('batchEditFilenameStartIndex').value;
            const startIndex = parseInt(startIndexInput);
            if (!isNaN(startIndex) && startIndex >= 1) {
                requestData.filename_start_index = startIndex;
            } else {
                requestData.filename_start_index = 1;  // 默认从1开始
            }
        }
    }

    // 检查是否有任何操作
    if (!tagsOperation && !categoriesOperation && !takenAtOperation && !locationOperation && !descriptionOperation && !filenameOperation) {
        showWarning('请至少选择一种操作');
        return;
    }

    try {
        // 显示加载状态
        const saveBtn = document.getElementById('saveBatchEdit');
        const originalText = saveBtn.textContent;
        saveBtn.disabled = true;
        saveBtn.textContent = '保存中...';

        const response = await fetch('/api/v1/photos/batch-edit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });

        if (response.ok) {
            const result = await response.json();
            // 关闭模态框
            const modal = bootstrap.Modal.getInstance(document.getElementById('batchEditModal'));
            modal.hide();

            // 刷新照片列表（保持当前页面）
            const currentPage = (typeof AppState !== 'undefined' && AppState.currentPage) ? AppState.currentPage : 1;
            await window.loadPhotos(currentPage);
            await window.loadStats();

            // 显示成功消息
            const details = [];
            if (result.details.tags_updated > 0) details.push(`标签: ${result.details.tags_updated}`);
            if (result.details.categories_updated > 0) details.push(`分类: ${result.details.categories_updated}`);
            if (result.details.taken_at_updated > 0) details.push(`拍摄时间: ${result.details.taken_at_updated}`);
            if (result.details.taken_at_filled > 0) details.push(`拍摄时间(填充): ${result.details.taken_at_filled}`);
            if (result.details.location_name_updated > 0) details.push(`位置: ${result.details.location_name_updated}`);
            if (result.details.location_name_filled > 0) details.push(`位置(填充): ${result.details.location_name_filled}`);
            if (result.details.description_updated > 0) details.push(`描述: ${result.details.description_updated}`);
            if (result.details.description_appended > 0) details.push(`描述(追加): ${result.details.description_appended}`);
            if (result.details.filename_updated > 0) details.push(`文件名: ${result.details.filename_updated}`);

            const message = `批量编辑完成：成功 ${result.successful_edits}/${result.total_requested} 张照片${details.length > 0 ? '\n' + details.join(', ') : ''}`;
            showToast(message, 'success');
        } else {
            const error = await response.json();
            showToast('批量编辑失败: ' + (error.detail || '未知错误'), 'error');
        }
    } catch (error) {
        console.error('批量编辑失败:', error);
        showToast('批量编辑失败: ' + error.message, 'error');
    } finally {
        const saveBtn = document.getElementById('saveBatchEdit');
        saveBtn.disabled = false;
        saveBtn.textContent = '保存修改';
    }
}

// 批量编辑标签管理
function addBatchEditTag(tagName) {
    const operation = document.getElementById('batchEditTagsOperation').value;
    if (operation === 'remove') {
        if (!batchEditRemoveTags.includes(tagName)) {
            batchEditRemoveTags.push(tagName);
            renderBatchEditRemoveTags();
        }
    } else {
        if (!batchEditSelectedTags.includes(tagName)) {
            batchEditSelectedTags.push(tagName);
            renderBatchEditSelectedTags();
        }
    }
    document.getElementById('batchEditTags').value = '';
}

function removeBatchEditTag(tagName) {
    const operation = document.getElementById('batchEditTagsOperation').value;
    if (operation === 'remove') {
        batchEditRemoveTags = batchEditRemoveTags.filter(t => t !== tagName);
        renderBatchEditRemoveTags();
    } else {
        batchEditSelectedTags = batchEditSelectedTags.filter(t => t !== tagName);
        renderBatchEditSelectedTags();
    }
}

function renderBatchEditSelectedTags() {
    const container = document.getElementById('batchEditSelectedTags');
    container.innerHTML = batchEditSelectedTags.map(tag => 
        `<span class="badge bg-primary me-1 mb-1" style="cursor: pointer;" onclick="removeBatchEditTag('${tag}')">${tag} <i class="bi bi-x"></i></span>`
    ).join('');
}

function renderBatchEditRemoveTags() {
    const container = document.getElementById('batchEditRemoveTags');
    container.innerHTML = batchEditRemoveTags.map(tag => 
        `<span class="badge bg-danger me-1 mb-1" style="cursor: pointer;" onclick="removeBatchEditTag('${tag}')">${tag} <i class="bi bi-x"></i></span>`
    ).join('');
}

// 绑定批量编辑保存按钮事件
document.addEventListener('DOMContentLoaded', function() {
    const saveBatchEditBtn = document.getElementById('saveBatchEdit');
    if (saveBatchEditBtn) {
        saveBatchEditBtn.addEventListener('click', saveBatchEdit);
    }
});

// 导出到全局
window.batchEditSelectedPhotos = batchEditSelectedPhotos;
window.saveBatchEdit = saveBatchEdit;
window.addBatchEditTag = addBatchEditTag;
window.removeBatchEditTag = removeBatchEditTag;
