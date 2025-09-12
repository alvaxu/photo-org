/**
 * 相似照片搜索功能
 */

// 相似照片搜索状态
const SimilarSearchState = {
    // 当前参考照片
    referencePhoto: null,
    
    // 相似度阈值
    similarityThreshold: 0.8,
    
    // 相似照片结果
    similarPhotos: [],
    
    // 加载状态
    isLoading: false
};

/**
 * 初始化相似照片搜索功能
 */
document.addEventListener('DOMContentLoaded', function() {
    initializeSimilarSearch();
});

/**
 * 初始化相似照片搜索
 */
function initializeSimilarSearch() {
    console.log('初始化相似照片搜索功能');
    
    // 为搜索结果中的照片添加相似搜索按钮
    addSimilarSearchButtons();
    
    // 绑定相似搜索模态框事件
    bindSimilarSearchEvents();
}

/**
 * 为搜索结果中的照片添加相似搜索按钮
 */
function addSimilarSearchButtons() {
    // 监听搜索结果更新
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList') {
                addSimilarSearchButtonsToResults();
            }
        });
    });
    
    observer.observe(document.getElementById('searchResults'), {
        childList: true,
        subtree: true
    });
}

/**
 * 为搜索结果添加相似搜索按钮
 */
function addSimilarSearchButtonsToResults() {
    const resultItems = document.querySelectorAll('.search-result-item');
    
    resultItems.forEach(item => {
        const photoId = item.dataset.photoId;
        const overlay = item.querySelector('.result-overlay');
        
        if (overlay && !overlay.querySelector('.similar-search-btn')) {
            const similarBtn = document.createElement('button');
            similarBtn.className = 'btn btn-info btn-sm similar-search-btn';
            similarBtn.innerHTML = '<i class="bi bi-search"></i>';
            similarBtn.title = '搜索相似照片';
            similarBtn.onclick = (e) => {
                e.stopPropagation();
                openSimilarSearchModal(photoId);
            };
            
            overlay.appendChild(similarBtn);
        }
    });
}

/**
 * 绑定相似搜索模态框事件
 */
function bindSimilarSearchEvents() {
    const modal = document.getElementById('similarSearchModal');
    const searchBtn = document.getElementById('searchSimilarBtn');
    const thresholdSlider = document.getElementById('similarityThreshold');
    const thresholdValue = document.getElementById('similarityValue');
    
    // 相似度阈值滑块
    thresholdSlider.addEventListener('input', function() {
        const value = Math.round(this.value * 100);
        thresholdValue.textContent = `${value}%`;
        SimilarSearchState.similarityThreshold = this.value;
    });
    
    // 搜索相似照片按钮
    searchBtn.addEventListener('click', function() {
        if (SimilarSearchState.referencePhoto) {
            searchSimilarPhotos();
        }
    });
    
    // 模态框关闭时清理状态
    modal.addEventListener('hidden.bs.modal', function() {
        clearSimilarSearchState();
    });
}

/**
 * 打开相似照片搜索模态框
 */
async function openSimilarSearchModal(photoId) {
    try {
        // 获取照片详情
        const response = await fetch(`/api/v1/photos/${photoId}`);
        
        if (!response.ok) {
            throw new Error('获取照片详情失败');
        }
        
        const photo = await response.json();
        
        // 设置参考照片
        SimilarSearchState.referencePhoto = photo;
        
        // 更新模态框内容
        updateSimilarSearchModal(photo);
        
        // 显示模态框
        const modal = new bootstrap.Modal(document.getElementById('similarSearchModal'));
        modal.show();
        
    } catch (error) {
        console.error('打开相似搜索模态框失败:', error);
        alert('无法打开相似照片搜索');
    }
}

/**
 * 更新相似搜索模态框内容
 */
function updateSimilarSearchModal(photo) {
    const referenceImage = document.getElementById('referenceImage');
    const referenceFilename = document.getElementById('referenceFilename');
    
    // 设置参考照片
    referenceImage.src = `/${(photo.thumbnail_path || '/static/images/placeholder.jpg').replace(/\\/g, '/')}`;
    referenceFilename.textContent = photo.filename;
    
    // 清空相似照片结果
    const similarResults = document.getElementById('similarResults');
    similarResults.innerHTML = '<p class="text-muted text-center">点击"搜索相似照片"开始搜索</p>';
}

/**
 * 搜索相似照片
 */
async function searchSimilarPhotos() {
    if (!SimilarSearchState.referencePhoto) {
        alert('请先选择参考照片');
        return;
    }
    
    SimilarSearchState.isLoading = true;
    
    try {
        // 显示加载状态
        showSimilarSearchLoading();
        
        // 调用相似照片搜索API
        const response = await fetch(`/api/v1/search/similar/${SimilarSearchState.referencePhoto.id}?threshold=${SimilarSearchState.similarityThreshold}&limit=20`);
        
        if (!response.ok) {
            throw new Error('搜索相似照片失败');
        }
        
        const data = await response.json();
        
        // 更新相似照片结果
        SimilarSearchState.similarPhotos = data.similar_photos || [];
        
        // 渲染相似照片结果
        renderSimilarPhotos();
        
    } catch (error) {
        console.error('搜索相似照片失败:', error);
        showSimilarSearchError('搜索相似照片失败，请重试');
    } finally {
        SimilarSearchState.isLoading = false;
        hideSimilarSearchLoading();
    }
}

/**
 * 渲染相似照片结果
 */
function renderSimilarPhotos() {
    const similarResults = document.getElementById('similarResults');
    
    if (SimilarSearchState.similarPhotos.length === 0) {
        similarResults.innerHTML = '<p class="text-muted text-center">没有找到相似照片</p>';
        return;
    }
    
    similarResults.innerHTML = SimilarSearchState.similarPhotos.map(photo => `
        <div class="col-md-3 col-6">
            <div class="similar-photo-item" data-photo-id="${photo.photo_id}">
                <img src="/${(photo.thumbnail_path || '/static/images/placeholder.jpg').replace(/\\/g, '/')}" 
                     alt="${photo.filename}" 
                     class="similar-photo-image"
                     loading="lazy">
                <div class="similar-photo-info">
                    <div class="similarity-score">相似度: ${Math.round(photo.similarity * 100)}%</div>
                    <div class="photo-filename" title="${photo.filename}">${photo.filename}</div>
                </div>
            </div>
        </div>
    `).join('');
    
    // 绑定相似照片点击事件
    bindSimilarPhotoEvents();
}

/**
 * 绑定相似照片事件
 */
function bindSimilarPhotoEvents() {
    const similarItems = document.querySelectorAll('.similar-photo-item');
    
    similarItems.forEach(item => {
        item.addEventListener('click', function() {
            const photoId = this.dataset.photoId;
            viewSimilarPhoto(photoId);
        });
    });
}

/**
 * 查看相似照片详情
 */
function viewSimilarPhoto(photoId) {
    // 在主搜索页面中搜索这张照片
    const photo = SimilarSearchState.similarPhotos.find(p => p.photo_id == photoId);
    
    if (photo) {
        // 设置搜索条件为这张照片的文件名
        elements.keywordInput.value = photo.filename;
        elements.searchType.value = 'filename';
        
        // 执行搜索
        updateSearchFilters();
        performSearch();
        
        // 关闭相似搜索模态框
        const modal = bootstrap.Modal.getInstance(document.getElementById('similarSearchModal'));
        modal.hide();
    }
}

/**
 * 显示相似搜索加载状态
 */
function showSimilarSearchLoading() {
    const similarResults = document.getElementById('similarResults');
    similarResults.innerHTML = `
        <div class="col-12 text-center py-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">搜索中...</span>
            </div>
            <p class="mt-2">正在搜索相似照片...</p>
        </div>
    `;
}

/**
 * 隐藏相似搜索加载状态
 */
function hideSimilarSearchLoading() {
    // 加载状态会在渲染结果时被替换
}

/**
 * 显示相似搜索错误
 */
function showSimilarSearchError(message) {
    const similarResults = document.getElementById('similarResults');
    similarResults.innerHTML = `
        <div class="col-12 text-center py-4">
            <i class="bi bi-exclamation-triangle text-warning" style="font-size: 2rem;"></i>
            <p class="mt-2 text-muted">${message}</p>
        </div>
    `;
}

/**
 * 清理相似搜索状态
 */
function clearSimilarSearchState() {
    SimilarSearchState.referencePhoto = null;
    SimilarSearchState.similarPhotos = [];
    SimilarSearchState.isLoading = false;
}

/**
 * 处理相似照片（批量操作）
 */
function processSimilarPhotos(action) {
    if (SimilarSearchState.similarPhotos.length === 0) {
        alert('没有相似照片可以处理');
        return;
    }
    
    const photoIds = SimilarSearchState.similarPhotos.map(photo => photo.photo_id);
    
    switch (action) {
        case 'delete':
            batchDeleteSimilarPhotos(photoIds);
            break;
        case 'keep_best':
            keepBestSimilarPhoto(photoIds);
            break;
        case 'group':
            groupSimilarPhotos(photoIds);
            break;
        default:
            console.warn('未知的相似照片处理动作:', action);
    }
}

/**
 * 批量删除相似照片
 */
async function batchDeleteSimilarPhotos(photoIds) {
    if (!confirm(`确定要删除这 ${photoIds.length} 张相似照片吗？此操作不可撤销。`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/v1/photos/batch-delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                photo_ids: photoIds,
                delete_files: true
            })
        });
        
        if (!response.ok) {
            throw new Error('批量删除失败');
        }
        
        const result = await response.json();
        console.log('批量删除相似照片结果:', result);
        
        // 重新搜索相似照片
        searchSimilarPhotos();
        
        alert(`成功删除 ${result.successful_deletions} 张相似照片`);
        
    } catch (error) {
        console.error('批量删除相似照片失败:', error);
        alert('批量删除失败，请重试');
    }
}

/**
 * 保留最佳相似照片
 */
async function keepBestSimilarPhoto(photoIds) {
    if (photoIds.length < 2) {
        alert('至少需要2张照片才能比较');
        return;
    }
    
    // 找到质量最高的照片
    const bestPhoto = SimilarSearchState.similarPhotos.reduce((best, current) => {
        const bestScore = best.quality_score || 0;
        const currentScore = current.quality_score || 0;
        return currentScore > bestScore ? current : best;
    });
    
    // 删除其他照片
    const otherPhotoIds = photoIds.filter(id => id !== bestPhoto.photo_id);
    
    if (otherPhotoIds.length > 0) {
        await batchDeleteSimilarPhotos(otherPhotoIds);
        alert(`已保留质量最高的照片: ${bestPhoto.filename}`);
    }
}

/**
 * 分组相似照片
 */
function groupSimilarPhotos(photoIds) {
    // TODO: 实现相似照片分组功能
    alert('相似照片分组功能开发中...');
}

/**
 * 添加相似照片处理工具栏
 */
function addSimilarPhotoToolbar() {
    const similarResults = document.getElementById('similarResults');
    
    // 检查是否已存在工具栏
    if (similarResults.querySelector('.similar-photo-toolbar')) {
        return;
    }
    
    const toolbar = document.createElement('div');
    toolbar.className = 'similar-photo-toolbar mb-3';
    toolbar.innerHTML = `
        <div class="d-flex justify-content-between align-items-center">
            <span class="text-muted">找到 ${SimilarSearchState.similarPhotos.length} 张相似照片</span>
            <div class="btn-group btn-group-sm">
                <button class="btn btn-outline-danger" onclick="processSimilarPhotos('delete')" title="删除所有相似照片">
                    <i class="bi bi-trash"></i> 删除全部
                </button>
                <button class="btn btn-outline-success" onclick="processSimilarPhotos('keep_best')" title="保留质量最高的照片">
                    <i class="bi bi-star"></i> 保留最佳
                </button>
                <button class="btn btn-outline-info" onclick="processSimilarPhotos('group')" title="将相似照片分组">
                    <i class="bi bi-collection"></i> 分组管理
                </button>
            </div>
        </div>
    `;
    
    similarResults.insertBefore(toolbar, similarResults.firstChild);
}

/**
 * 更新相似照片结果时添加工具栏
 */
function renderSimilarPhotos() {
    const similarResults = document.getElementById('similarResults');
    
    if (SimilarSearchState.similarPhotos.length === 0) {
        similarResults.innerHTML = '<p class="text-muted text-center">没有找到相似照片</p>';
        return;
    }
    
    // 渲染照片网格
    const photosHtml = SimilarSearchState.similarPhotos.map(photo => `
        <div class="col-md-3 col-6">
            <div class="similar-photo-item" data-photo-id="${photo.photo_id}">
                <img src="/${(photo.thumbnail_path || '/static/images/placeholder.jpg').replace(/\\/g, '/')}" 
                     alt="${photo.filename}" 
                     class="similar-photo-image"
                     loading="lazy">
                <div class="similar-photo-info">
                    <div class="similarity-score">相似度: ${Math.round(photo.similarity * 100)}%</div>
                    <div class="photo-filename" title="${photo.filename}">${photo.filename}</div>
                </div>
            </div>
        </div>
    `).join('');
    
    similarResults.innerHTML = `
        <div class="row g-2">
            ${photosHtml}
        </div>
    `;
    
    // 添加工具栏
    addSimilarPhotoToolbar();
    
    // 绑定相似照片点击事件
    bindSimilarPhotoEvents();
}
