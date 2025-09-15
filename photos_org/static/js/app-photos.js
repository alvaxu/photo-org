/**
 * 家庭单机版智能照片整理系统 - 照片操作模块
 * 
 * 功能：
 * 1. 照片卡片和列表项创建
 * 2. 照片选择操作
 * 3. 照片删除操作
 * 4. 页面导航和显示
 */

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

    // 获取质量信息
    const qualityLevel = photo.quality?.level || photo.analysis?.quality_rating || '';
    const qualityClass = getQualityClass(qualityLevel);
    const qualityText = getQualityText(qualityLevel);

    return `
        <div class="photo-card" data-photo-id="${photo.id}">
            <div class="photo-image-container">
                <img src="/photos_storage/${(photo.thumbnail_path || CONFIG.IMAGE_PLACEHOLDER).replace(/\\/g, '/')}"
                     alt="${photo.filename}"
                     class="photo-image"
                     loading="lazy">
                <div class="photo-overlay">
                    <button class="btn btn-light btn-sm" onclick="event.stopPropagation(); viewPhotoDetail(${photo.id})" title="查看详情">
                        <i class="bi bi-eye"></i>
                    </button>
                    <button class="btn btn-warning btn-sm" onclick="event.stopPropagation(); editPhoto(${photo.id})" title="编辑">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-danger btn-sm" onclick="event.stopPropagation(); deletePhoto(${photo.id})" title="删除">
                        <i class="bi bi-trash"></i>
                    </button>
                    <button class="btn btn-info btn-sm" onclick="event.stopPropagation(); searchSimilarPhotos(${photo.id})" title="相似照片">
                        <i class="bi bi-search"></i>
                    </button>
                </div>
            </div>
            <div class="photo-info">
                <div class="photo-title">${photo.filename}</div>
                <div class="photo-meta">
                    <i class="bi bi-calendar me-1"></i>${formatDate(photo.taken_at)} (拍摄日期)
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
                <div class="photo-quality ${qualityClass}">
                    ${qualityText}
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

    const qualityClass = getQualityClass(photo.quality?.level || '');
    const qualityText = getQualityText(photo.quality?.level || '');

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
        <div class="photo-list-item" data-photo-id="${photo.id}">
            <div class="photo-thumbnail-container">
                <img src="/photos_storage/${(photo.thumbnail_path || CONFIG.IMAGE_PLACEHOLDER).replace(/\\/g, '/')}"
                     alt="${photo.filename}"
                     class="photo-thumbnail">
                <div class="photo-overlay">
                    <button class="btn btn-light btn-sm" onclick="event.stopPropagation(); viewPhotoDetail(${photo.id})" title="查看详情">
                        <i class="bi bi-eye"></i>
                    </button>
                    <button class="btn btn-warning btn-sm" onclick="event.stopPropagation(); editPhoto(${photo.id})" title="编辑">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-danger btn-sm" onclick="event.stopPropagation(); deletePhoto(${photo.id})" title="删除">
                        <i class="bi bi-trash"></i>
                    </button>
                    <button class="btn btn-info btn-sm" onclick="event.stopPropagation(); searchSimilarPhotos(${photo.id})" title="相似照片">
                        <i class="bi bi-search"></i>
                    </button>
                </div>
            </div>
            <div class="photo-details">
                <div class="photo-header">
                    <div class="photo-title">${photo.filename}</div>
                    <div class="photo-actions">
                        <span class="badge ${qualityClass}">${qualityText}</span>
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
    console.log('全选照片');
    if (window.PhotoManager) {
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
    console.log('取消选择');
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
    console.log('删除选中照片');
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
    console.log('📄 切换到页面:', section);
    
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
function viewPhotoDetail(photoId) {
    // 从当前显示的照片中找到对应的照片对象
    const photo = AppState.photos.find(p => p.id === photoId);
    if (photo) {
        showPhotoDetail(photo);
    } else {
        console.error('未找到照片:', photoId);
        alert('未找到照片信息');
    }
}

/**
 * 编辑照片
 * @param {number} photoId - 照片ID
 */
function editPhoto(photoId) {
    console.log('编辑照片:', photoId);
    
    // 从当前显示的照片中找到对应的照片对象
    const photo = AppState.photos.find(p => p.id === photoId);
    if (!photo) {
        console.error('未找到照片:', photoId);
        alert('未找到照片信息');
        return;
    }
    
    // 显示编辑模态框
    showPhotoEditModal(photo);
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
 * 搜索相似照片
 * @param {number} photoId - 照片ID
 */
async function searchSimilarPhotos(photoId) {
    console.log('搜索相似照片:', photoId);
    
    try {
        // 确保配置已加载
        if (!userConfig) {
            await loadUserConfig();
        }
        
        // 从配置中获取相似度阈值和限制数量
        const threshold = userConfig?.search?.similarity_threshold || 0.85;
        const limit = userConfig?.search?.similar_photos_limit || 8;
        
        // 显示加载状态
        showSimilarPhotosModal(photoId);
        
        // 调用第一层API快速筛选相似照片
        const response = await fetch(`/api/v1/enhanced-search/similar/first-layer/${photoId}?threshold=${threshold}&limit=${limit}`);
        const data = await response.json();
        
        if (data.success && data.data) {
            // 暂时禁用精确匹配按钮
            data.data.showPreciseMatch = false;
            data.data.referencePhotoId = photoId;
            displaySimilarPhotos(data.data);
        } else {
            console.error('搜索相似照片失败:', data);
            alert('搜索相似照片失败');
        }
    } catch (error) {
        console.error('搜索相似照片出错:', error);
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
    // 创建或获取相似照片模态框
    let modal = document.getElementById('similarPhotosModal');
    if (!modal) {
        modal = createSimilarPhotosModal();
        document.body.appendChild(modal);
    }
    
    // 显示模态框
    const modalInstance = new bootstrap.Modal(modal);
    modalInstance.show();
    
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
 * 显示相似照片结果（V2 API格式）
 * @param {Array} similarPhotos - 相似照片数组
 * @param {number} referencePhotoId - 参考照片ID
 */
function displaySimilarPhotosV2(similarPhotos, referencePhotoId) {
    const resultsContainer = document.getElementById('similarPhotosResults');
    
    if (!similarPhotos || similarPhotos.length === 0) {
        resultsContainer.innerHTML = '<div class="col-12 text-center"><p class="text-muted">没有找到相似照片</p></div>';
        return;
    }
    
    // 获取参考照片信息
    const referencePhoto = AppState.photos.find(p => p.id === referencePhotoId);
    
    let html = `
        <div class="col-12 mb-3">
            <h6>参考照片</h6>
            <div class="card">
                <div class="card-body">
                    <div class="row align-items-center">
                        <div class="col-md-2">
                            <img src="/photos_storage/${(referencePhoto?.thumbnail_path || CONFIG.IMAGE_PLACEHOLDER).replace(/\\\\/g, '/')}" 
                                 class="img-thumbnail" alt="${referencePhoto?.filename || '未知'}">
                        </div>
                        <div class="col-md-10">
                            <h6>${referencePhoto?.filename || '未知'}</h6>
                            <p class="text-muted mb-0">找到 ${similarPhotos.length} 张相似照片</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 显示相似照片
    html += '<div class="col-12"><h6>相似照片</h6></div>';
    
    similarPhotos.forEach(photo => {
        const similarityPercent = Math.round(photo.similarity * 100);
        html += `
            <div class="col-md-3 col-sm-6 mb-3">
                <div class="card h-100">
                    <div class="position-relative">
                        <img src="/photos_storage/${(photo.thumbnail_path || CONFIG.IMAGE_PLACEHOLDER).replace(/\\\\/g, '/')}" 
                             class="card-img-top" style="height: 200px; object-fit: cover;" 
                             alt="${photo.filename}">
                        <div class="position-absolute top-0 end-0 m-2">
                            <span class="badge bg-primary">${similarityPercent}%</span>
                        </div>
                    </div>
                    <div class="card-body p-2">
                        <h6 class="card-title small">${photo.filename}</h6>
                        <p class="card-text small text-muted">相似度: ${similarityPercent}%</p>
                        ${photo.similarities ? `
                            <div class="small text-muted">
                                <div>感知哈希: ${Math.round(photo.similarities.perceptual_hash * 100)}%</div>
                                <div>描述相似: ${Math.round(photo.similarities.description * 100)}%</div>
                                <div>对象相似: ${Math.round(photo.similarities.objects * 100)}%</div>
                            </div>
                        ` : ''}
                    </div>
                    <div class="card-footer p-2">
                        <div class="btn-group w-100" role="group">
                            <button class="btn btn-outline-primary btn-sm" onclick="viewPhotoDetail(${photo.photo_id})" title="查看详情">
                                <i class="bi bi-eye"></i>
                            </button>
                            <button class="btn btn-outline-warning btn-sm" onclick="editPhoto(${photo.photo_id})" title="编辑">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button class="btn btn-outline-danger btn-sm" onclick="deletePhoto(${photo.photo_id})" title="删除">
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
        html += `
            <div class="col-md-3 col-sm-6 mb-3">
                <div class="card h-100">
                    <div class="position-relative">
                        <img src="/photos_storage/${(photo.thumbnail_path || CONFIG.IMAGE_PLACEHOLDER).replace(/\\\\/g, '/')}" 
                             class="card-img-top" style="height: 200px; object-fit: cover;" 
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
    document.getElementById('editPhotoFilename').textContent = photo.filename;
    
    // 填充元数据
    const meta = [];
    if (photo.taken_at) meta.push(`拍摄时间: ${formatDate(photo.taken_at)}`);
    if (photo.width && photo.height) meta.push(`分辨率: ${photo.width} × ${photo.height}`);
    if (photo.file_size) meta.push(`文件大小: ${formatFileSize(photo.file_size)}`);
    document.getElementById('editPhotoMeta').textContent = meta.join(' | ');
    
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
    const description = document.getElementById('editPhotoDescription').value;
    
    // 使用选中的标签
    const tags = selectedTags;
    
    // 准备更新数据
    const updateData = {
        description: description || null,
        tags: tags
    };
    
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
            
            // 重新加载照片
            loadPhotos();
            
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
window.displaySimilarPhotosV2 = displaySimilarPhotosV2;
window.displaySimilarPhotos = displaySimilarPhotos;
window.showPhotoEditModal = showPhotoEditModal;
window.savePhotoEdit = savePhotoEdit;
