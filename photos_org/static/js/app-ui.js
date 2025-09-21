/**
 * 家庭版智能照片系统 - UI交互模块
 * 包含UI组件初始化、模态框管理、视图切换等交互功能
 */

// ============ UI组件初始化 ============

function initializeUI() {
    console.log('🎨 初始化UI组件');

    // 设置初始搜索框placeholder
    if (elements.searchInput) {
        elements.searchInput.placeholder = searchTypePlaceholders['all'] || '搜索照片、文件名、描述...';
    }

    // 设置搜索范围提示
    if (elements.searchScopeHint) {
        elements.searchScopeHint.textContent = searchScopeHints['all'] || '支持搜索照片全部文本内容';
    }

    // 初始化Bootstrap模态框
    const photoModal = new bootstrap.Modal(elements.photoModal);
    const importModal = new bootstrap.Modal(elements.importModal);
    const batchModal = new bootstrap.Modal(elements.batchModal);

    // 存储在全局对象中
    window.modals = {
        photoModal,
        importModal,
        batchModal
    };

    // 添加全局关闭函数
    window.closeModal = function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            console.log('🔒 全局关闭模态框:', modalId);
            
            // 使用Bootstrap API关闭模态框
            const modalInstance = bootstrap.Modal.getInstance(modal);
            if (modalInstance) {
                modalInstance.hide();
            } else {
                // 如果Bootstrap实例不存在，创建一个新的
                const newModalInstance = new bootstrap.Modal(modal);
                newModalInstance.hide();
            }
        }
    };

    // 添加调试信息
    console.log('📱 模态框初始化完成:', {
        photoModal: !!photoModal,
        importModal: !!importModal,
        batchModal: !!batchModal
    });

    // 添加测试函数
    window.testModalClose = function() {
        console.log('🧪 测试模态框关闭功能');
        const modals = ['importModal', 'batchModal', 'photoModal'];
        modals.forEach(modalId => {
            const modal = document.getElementById(modalId);
            if (modal) {
                console.log(`模态框 ${modalId} 存在:`, modal);
                const closeButtons = modal.querySelectorAll('[data-bs-dismiss="modal"]');
                console.log(`关闭按钮数量:`, closeButtons.length);
            }
        });
    };

    // 添加紧急清理函数
    window.forceCleanup = function() {
        console.log('🚨 强制清理页面状态');
        
        // 关闭所有模态框
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            modal.classList.remove('show');
            modal.style.display = 'none';
            modal.setAttribute('aria-hidden', 'true');
            modal.removeAttribute('aria-modal');
        });
        
        // 移除所有遮罩层
        const backdrops = document.querySelectorAll('.modal-backdrop');
        backdrops.forEach(backdrop => backdrop.remove());
        
        // 恢复body状态
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
        
        console.log('✅ 强制清理完成');
    };

    // 监听模态框事件并确保正确清理
    document.addEventListener('show.bs.modal', function(e) {
        console.log('📱 模态框显示:', e.target.id);
    });
    
    document.addEventListener('hide.bs.modal', function(e) {
        console.log('📱 模态框隐藏:', e.target.id);
        
        // 确保清理所有可能的遮罩层
        setTimeout(() => {
            const backdrops = document.querySelectorAll('.modal-backdrop');
            backdrops.forEach(backdrop => backdrop.remove());
            
            // 确保body恢复正常状态
            document.body.classList.remove('modal-open');
            document.body.style.overflow = '';
            document.body.style.paddingRight = '';
            
            console.log('🧹 清理完成，页面应该可以正常点击了');
        }, 100);
    });
    
    // 页面加载时检查并清理遮罩层
    function checkAndCleanupOverlay() {
        const backdrops = document.querySelectorAll('.modal-backdrop');
        if (backdrops.length > 0) {
            console.log('发现残留遮罩层，正在清理...');
            window.forceCleanup();
        }
    }

    // 页面加载完成后检查
    document.addEventListener('DOMContentLoaded', checkAndCleanupOverlay);
    
    // 页面完全加载后再次检查
    window.addEventListener('load', checkAndCleanupOverlay);

    // 监听模态框完全隐藏后的事件
    document.addEventListener('hidden.bs.modal', function(e) {
        console.log('📱 模态框完全隐藏:', e.target.id);
        
        // 再次确保清理
        const backdrops = document.querySelectorAll('.modal-backdrop');
        backdrops.forEach(backdrop => backdrop.remove());
        
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
    });

    // 初始化工具提示
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// ============ 模态框管理 ============

function showImportModal() {
    // 重置模态框状态
    resetImportModalState();

    // 使用Bootstrap API显示模态窗口
    const modal = new bootstrap.Modal(elements.importModal);
    modal.show();
}

function showBatchModal() {
    // 使用Bootstrap API显示模态窗口
    const modal = new bootstrap.Modal(elements.batchModal);
    modal.show();
}

// ============ 模态框重置 ============

/**
 * 重置导入模态框状态
 */
function resetImportModalState() {
    console.log('开始重置导入模态框状态...');

    // 隐藏错误信息
    hideImportError();

    // 清空文件选择
    const photoFiles = document.getElementById('photoFiles');
    if (photoFiles) {
        photoFiles.value = '';
    }

    // 清空文件夹路径
    const folderPath = document.getElementById('folderPath');
    if (folderPath) {
        folderPath.value = '';
    }

    // 重置导入方式为默认
    switchImportMethod('file');

    // 隐藏进度条区域
    const progressArea = document.getElementById('importProgress');
    if (progressArea) {
        progressArea.classList.add('d-none');
    }

    // 重置进度条
    const progressBar = document.getElementById('importProgressBar');
    if (progressBar) {
        progressBar.style.width = '0%';
    }

    // 重置状态文本
    const statusText = document.getElementById('importStatus');
    if (statusText) {
        statusText.textContent = '准备开始导入...';
    }

    // 隐藏文件预览区域
    hideFilePreview();
    hideFolderPreview();

    // 确保文件夹预览区域完全隐藏
    const folderPreview = document.getElementById('folderPreview');
    if (folderPreview) {
        folderPreview.style.display = 'none';
    }

    // 隐藏文件导入确认区域
    const fileConfirm = document.getElementById('fileImportConfirmation');
    if (fileConfirm) {
        fileConfirm.innerHTML = '';
        fileConfirm.style.display = 'none';
    }

    console.log('导入模态框状态已重置');
}

// ============ 视图切换 ============

function switchView(viewType) {
    AppState.currentView = viewType;
    renderPhotos();
}

// ============ 照片详情 ============

function showPhotoDetail(photo) {
    console.log('显示照片详情:', photo);
    
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
    
    // 创建详情模态框内容
    const modalContent = createPhotoDetailModal(photo);
    
    // 更新模态框内容
    const modalBody = elements.photoModal.querySelector('.modal-body');
    modalBody.innerHTML = modalContent;
    
    // 更新模态框标题
    const modalTitle = elements.photoModal.querySelector('#photoModalTitle');
    if (modalTitle) {
        modalTitle.textContent = `照片详情 - ${photo.filename}`;
    }
    
    // 绑定下载按钮事件
    bindPhotoDetailEvents(photo);
    
    // 显示模态框
    const modal = new bootstrap.Modal(elements.photoModal);
    modal.show();
    
    // 监听详情模态框关闭事件，如果之前有相似搜索页显示，则重新显示
    if (wasSimilarModalVisible) {
        elements.photoModal.addEventListener('hidden.bs.modal', function onDetailModalHidden() {
            // 重新显示相似搜索页
            if (similarModal) {
                const similarModalInstance = new bootstrap.Modal(similarModal);
                similarModalInstance.show();
            }
            // 移除事件监听器，避免重复绑定
            elements.photoModal.removeEventListener('hidden.bs.modal', onDetailModalHidden);
        }, { once: true });
    }
}

function createPhotoDetailModal(photo) {
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
    
    // 格式化拍摄时间
    const formatDateTime = (dateString) => {
        if (!dateString) return '未知时间';
        try {
            const date = new Date(dateString);
            return date.toLocaleString('zh-CN', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        } catch (e) {
            return dateString;
        }
    };
    
    // 获取质量信息
    const qualityLevel = photo.quality?.level || photo.analysis?.quality_rating || '';
    const qualityClass = getQualityClass(qualityLevel);
    const qualityText = getQualityText(qualityLevel);
    
    // 构建EXIF信息
    const exifInfo = [];
    if (photo.camera_make) exifInfo.push(`相机品牌：${photo.camera_make}`);
    if (photo.camera_model) exifInfo.push(`相机型号：${photo.camera_model}`);
    if (photo.lens_model) exifInfo.push(`镜头信息：${photo.lens_model}`);
    if (photo.aperture) exifInfo.push(`光圈：f/${photo.aperture}`);
    if (photo.shutter_speed) exifInfo.push(`快门：1/${photo.shutter_speed}s`);
    if (photo.iso) exifInfo.push(`ISO：${photo.iso}`);
    if (photo.focal_length) exifInfo.push(`焦距：${photo.focal_length}mm`);
    if (photo.flash !== undefined) exifInfo.push(`闪光灯：${photo.flash ? '开启' : '关闭'}`);
    
    // 构建位置信息
    const locationInfo = [];
    if (photo.location_name) locationInfo.push(`拍摄地点：${photo.location_name}`);
    if (photo.latitude && photo.longitude) locationInfo.push(`经纬度：${photo.latitude}, ${photo.longitude}`);
    if (photo.altitude) locationInfo.push(`海拔：${photo.altitude}m`);
    
    // 构建用户描述信息
    const descriptionInfo = [];
    if (photo.description) {
        descriptionInfo.push(`<p><strong>用户照片描述：</strong>${photo.description}</p>`);
    }
    
    // 构建AI分析信息
    const aiInfo = [];
    if (photo.analysis) {
        if (photo.analysis.description) aiInfo.push(`<p><strong>AI内容描述：</strong>${photo.analysis.description}</p>`);
        if (photo.analysis.scene_type) aiInfo.push(`<p><strong>场景类型：</strong>${photo.analysis.scene_type}</p>`);
        if (photo.analysis.objects && photo.analysis.objects.length > 0) {
            aiInfo.push(`<p><strong>检测到的物体：</strong>${photo.analysis.objects.join(', ')}</p>`);
        }
        if (photo.analysis.tags && photo.analysis.tags.length > 0) {
            aiInfo.push(`<p><strong>AI标签：</strong>${photo.analysis.tags.join(', ')}</p>`);
        }
        if (photo.analysis.confidence) {
            aiInfo.push(`<p><strong>置信度：</strong>${(photo.analysis.confidence * 100).toFixed(1)}%</p>`);
        }
    }
    
    // 构建分类信息
    const categoryInfo = [];
    if (photo.categories && photo.categories.length > 0) {
        categoryInfo.push(`<p><strong>分类：</strong>${photo.categories.map(cat => `<span class="badge bg-primary me-1">${cat}</span>`).join('')}</p>`);
    }
    
    // 构建文件信息
    const fileInfo = [];
    if (photo.original_path) fileInfo.push(`原始路径：${photo.original_path}`);
    if (photo.thumbnail_path) fileInfo.push(`缩略图路径：${photo.thumbnail_path}`);
    if (photo.file_size) fileInfo.push(`文件大小：${formatFileSize(photo.file_size)}`);
    if (photo.created_at) fileInfo.push(`创建时间：${formatDateTime(photo.created_at)}`);
    if (photo.updated_at) fileInfo.push(`修改时间：${formatDateTime(photo.updated_at)}`);
    if (photo.file_hash) fileInfo.push(`文件哈希：${photo.file_hash}`);
    
    return `
        <!-- 照片显示区域 -->
        <div class="text-center mb-4">
            <div id="photoImageContainer">
                <img src="/photos_storage/${(photo.original_path || photo.thumbnail_path || CONFIG.IMAGE_PLACEHOLDER).replace(/\\/g, '/')}" 
                     alt="${photo.filename}" 
                     class="img-fluid rounded shadow" 
                     style="max-height: 60vh; object-fit: contain;"
                     data-thumbnail="${photo.thumbnail_path ? '/photos_storage/' + photo.thumbnail_path.replace(/\\/g, '/') : ''}"
                     data-original-format="${photo.filename.toLowerCase().endsWith('.heic') || photo.filename.toLowerCase().endsWith('.heif') ? 'heic' : 'other'}"
                     data-original-path="${photo.original_path || ''}"
                     data-photo-id="${photo.id || ''}"
                     onerror="handleImageError(this);"
                     onload="handleImageLoad(this);">
                
                <!-- HEIC格式提示 -->
                <div id="heicFormatTip" class="alert alert-info mt-2" style="display: none;">
                    <i class="bi bi-info-circle me-2"></i>
                    <strong>HEIC 格式提示：</strong>您的浏览器无法直接显示 HEIC 格式原图，当前显示的是 JPEG 缩略图。
                    <br>
                    <small class="text-muted">
                        • Chrome 浏览器：请安装 <a href="https://chrome.google.com/webstore/search/heic" target="_blank">HEIC 插件</a> 查看原图,可能需科学上网<br>
                        • Safari 浏览器：通常原生支持 HEIC 格式<br>
                        • 其他浏览器：请先确认该浏览器是否支持、或者是否可以安装HEIC插件查看HEIC格式原图
                    </small>
                    <br>
                    <small class="text-muted">
                        你也可以点击下方按钮下载原图后用本地自带图片查看工具查看。
                    </small>
                </div>
            </div>
        </div>
        
        <div class="row g-3">
            <!-- 基本信息 -->
            <div class="col-md-6 col-lg-4">
                <div class="card h-100">
                    <div class="card-header">
                        <h6 class="card-title mb-0"><i class="bi bi-info-circle me-2"></i>基本信息</h6>
                    </div>
                    <div class="card-body">
                        <p><strong>文件名：</strong>${photo.filename}</p>
                        <p><strong>拍摄时间：</strong>${formatDateTime(photo.taken_at)}</p>
                        <p><strong>分辨率：</strong>${photo.width || '未知'} × ${photo.height || '未知'}</p>
                        <p><strong>质量评级：</strong><span class="badge ${qualityClass}">${qualityText}</span></p>
                    </div>
                </div>
            </div>
            
            ${exifInfo.length > 0 ? `
            <!-- 相机信息 -->
            <div class="col-md-6 col-lg-4">
                <div class="card h-100">
                    <div class="card-header">
                        <h6 class="card-title mb-0"><i class="bi bi-camera me-2"></i>相机信息</h6>
                    </div>
                    <div class="card-body">
                        ${exifInfo.map(info => `<p class="mb-1">${info}</p>`).join('')}
                    </div>
                </div>
            </div>
            ` : ''}
            
            ${locationInfo.length > 0 ? `
            <!-- 位置信息 -->
            <div class="col-md-6 col-lg-4">
                <div class="card h-100">
                    <div class="card-header">
                        <h6 class="card-title mb-0"><i class="bi bi-geo-alt me-2"></i>位置信息</h6>
                    </div>
                    <div class="card-body">
                        ${locationInfo.map(info => `<p class="mb-1">${info}</p>`).join('')}
                    </div>
                </div>
            </div>
            ` : ''}
            
            ${aiInfo.length > 0 ? `
            <!-- AI分析结果 -->
            <div class="col-md-6 col-lg-4">
                <div class="card h-100">
                    <div class="card-header">
                        <h6 class="card-title mb-0"><i class="bi bi-robot me-2"></i>AI分析结果</h6>
                    </div>
                    <div class="card-body">
                        ${aiInfo.join('')}
                    </div>
                </div>
            </div>
            ` : ''}
            
            ${descriptionInfo.length > 0 ? `
            <!-- 用户照片描述 -->
            <div class="col-md-6 col-lg-4">
                <div class="card h-100">
                    <div class="card-header">
                        <h6 class="card-title mb-0"><i class="bi bi-chat-text me-2"></i>用户描述</h6>
                    </div>
                    <div class="card-body">
                        ${descriptionInfo.join('')}
                    </div>
                </div>
            </div>
            ` : ''}
            
            <!-- 标签 -->
            <div class="col-md-6 col-lg-4">
                <div class="card h-100">
                    <div class="card-header">
                        <h6 class="card-title mb-0"><i class="bi bi-tags me-2"></i>标签</h6>
                    </div>
                    <div class="card-body">
                        ${photo.tags && photo.tags.length > 0 ? 
                            photo.tags.map(tag => `<span class="badge bg-secondary me-1 mb-1">${tag}</span>`).join('') : 
                            '<p class="text-muted mb-0">暂无标签</p>'
                        }
                    </div>
                </div>
            </div>
            
            ${categoryInfo.length > 0 ? `
            <!-- 分类 -->
            <div class="col-md-6 col-lg-4">
                <div class="card h-100">
                    <div class="card-header">
                        <h6 class="card-title mb-0"><i class="bi bi-folder me-2"></i>分类</h6>
                    </div>
                    <div class="card-body">
                        ${categoryInfo.join('')}
                    </div>
                </div>
            </div>
            ` : ''}
            
            <!-- 文件信息 -->
            <div class="col-md-6 col-lg-4">
                <div class="card h-100">
                    <div class="card-header">
                        <h6 class="card-title mb-0"><i class="bi bi-file-earmark me-2"></i>文件信息</h6>
                    </div>
                    <div class="card-body">
                        ${fileInfo.map(info => `<p class="small mb-1">${info}</p>`).join('')}
                    </div>
                </div>
            </div>
        </div>
    `;
}

// ============ 标签展开/收起功能 ============

function toggleTags(element, event) {
    event.stopPropagation(); // 阻止事件冒泡，避免触发照片选择
    
    const photoId = element.getAttribute('data-photo-id');
    const photoCard = document.querySelector(`[data-photo-id="${photoId}"]`);
    const hiddenTags = photoCard.querySelector('.hidden-tags');
    const toggleText = element;
    
    if (hiddenTags.style.display === 'none') {
        // 展开标签
        hiddenTags.style.display = 'block';
        toggleText.textContent = '收起';
        toggleText.classList.add('expanded');
    } else {
        // 收起标签
        hiddenTags.style.display = 'none';
        toggleText.textContent = `+${hiddenTags.children.length} 更多`;
        toggleText.classList.remove('expanded');
    }
}

// ============ 全局导出 ============

// 导出UI初始化函数
window.initializeUI = initializeUI;

// 导出模态框管理函数
window.showImportModal = showImportModal;
window.showBatchModal = showBatchModal;
window.resetImportModalState = resetImportModalState;

// 导出视图切换函数
window.switchView = switchView;

// 绑定照片详情事件
function bindPhotoDetailEvents(photo) {
    // 绑定下载按钮事件
    const downloadBtn = elements.photoModal.querySelector('#downloadPhotoBtn');
    if (downloadBtn) {
        downloadBtn.onclick = () => downloadPhoto(photo.id);
    }
    
    // 绑定搜索相似照片按钮事件
    const searchSimilarBtn = elements.photoModal.querySelector('#searchSimilarBtn');
    if (searchSimilarBtn) {
        searchSimilarBtn.onclick = () => {
            // 关闭当前详情模态框
            const modal = bootstrap.Modal.getInstance(elements.photoModal);
            if (modal) {
                modal.hide();
            }
            // 搜索相似照片
            searchSimilarPhotos(photo.id);
        };
    }
    
    // 绑定编辑按钮事件
    const editBtn = elements.photoModal.querySelector('#editPhotoBtn');
    if (editBtn) {
        editBtn.onclick = () => editPhoto(photo.id);
    }
    
    // 绑定收藏按钮事件
    const favoriteBtn = elements.photoModal.querySelector('#addToFavoritesBtn');
    if (favoriteBtn) {
        favoriteBtn.onclick = () => toggleFavorite(photo.id);
    }
    
    // 绑定删除按钮事件
    const deleteBtn = elements.photoModal.querySelector('#deletePhotoBtn');
    if (deleteBtn) {
        deleteBtn.onclick = () => deletePhoto(photo.id);
    }
}

// 下载照片功能
async function downloadPhoto(photoId) {
    try {
        console.log('开始下载照片:', photoId);
        
        // 显示下载状态
        const downloadBtn = elements.photoModal.querySelector('#downloadPhotoBtn');
        if (downloadBtn) {
            const originalText = downloadBtn.innerHTML;
            downloadBtn.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>下载中...';
            downloadBtn.disabled = true;
        }
        
        // 构建下载URL
        const downloadUrl = `/api/v1/photos/${photoId}/download`;
        
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
        
        console.log('照片下载已开始');
        
        // 恢复按钮状态
        setTimeout(() => {
            if (downloadBtn) {
                downloadBtn.innerHTML = '<i class="bi bi-download me-2"></i>下载原图';
                downloadBtn.disabled = false;
            }
        }, 2000);
        
    } catch (error) {
        console.error('下载照片失败:', error);
        alert('下载照片失败，请重试');
        
        // 恢复按钮状态
        const downloadBtn = elements.photoModal.querySelector('#downloadPhotoBtn');
        if (downloadBtn) {
            downloadBtn.innerHTML = '<i class="bi bi-download me-2"></i>下载原图';
            downloadBtn.disabled = false;
        }
    }
}

// 编辑照片功能（占位符）
function editPhoto(photoId) {
    console.log('编辑照片:', photoId);
    alert('编辑功能暂未实现');
}

// 切换收藏状态（占位符）
function toggleFavorite(photoId) {
    console.log('切换收藏状态:', photoId);
    alert('收藏功能待开发');
}

// 删除照片功能（占位符）
function deletePhoto(photoId) {
    console.log('删除照片:', photoId);
    if (confirm('确定要删除这张照片吗？此操作不可撤销。')) {
        alert('删除功能暂未实现');
    }
}

// 导出照片详情函数
window.showPhotoDetail = showPhotoDetail;
window.createPhotoDetailModal = createPhotoDetailModal;
window.downloadPhoto = downloadPhoto;

// 导出标签功能
window.toggleTags = toggleTags;

// ============ HEIC 格式图片处理 ============

/**
 * 处理图片加载错误（防止无限重试）
 * @param {HTMLImageElement} img - 图片元素
 */
function handleImageError(img) {
    console.log('图片加载失败:', img.src);
    
    // 防止重复处理
    if (img.errorHandled) {
        return;
    }
    
    // 检查是否为 HEIC 格式
    const isHeicFormat = img.src.toLowerCase().includes('.heic') || img.src.toLowerCase().includes('.heif');
    
    if (isHeicFormat) {
        // HEIC 格式：显示初始提示，尝试缩略图
        showHeicFormatTipInitial();
        tryThumbnailFallback(img);
    } else {
        // 非 HEIC 格式：直接显示占位符
        showGenericPlaceholder(img);
    }
}

/**
 * 处理图片加载成功
 * @param {HTMLImageElement} img - 图片元素
 */
function handleImageLoad(img) {
    console.log('图片加载成功:', img.src);
    
    const isOriginalPhotoHeic = img.dataset.originalFormat === 'heic';
    const isCurrentlyShowingThumbnail = img.src.includes('/thumbnails/') || img.src.includes('_thumb.');
    const isHeicPluginActive = img.dataset.heicOverlay === 'true';
    
    if (isOriginalPhotoHeic && isHeicPluginActive) {
        // 原始 HEIC 图片，且插件已激活（说明原图通过插件成功显示）
        hideAllHeicTips();
    } else if (isOriginalPhotoHeic && isCurrentlyShowingThumbnail && !isHeicPluginActive) {
        // 原始图片是 HEIC，显示缩略图，且插件未激活（说明原图加载失败，降级显示）
        showThumbnailFallbackTip();
    } else {
        // 其他情况：非 HEIC 格式，或 HEIC 原图直接成功加载
        hideAllHeicTips();
    }
}

/**
 * 显示 HEIC 格式初始提示
 */
function showHeicFormatTipInitial() {
    const tipElement = document.getElementById('heicFormatTip');
    if (tipElement) {
        // 设置初始提示内容
        tipElement.innerHTML = `
            <i class="bi bi-info-circle me-2"></i>
            <strong>HEIC 格式提示：</strong>您的浏览器无法直接显示 HEIC 格式原图，当前显示的是 JPEG 缩略图。
            <br>
            <small class="text-muted">
                • Chrome 浏览器：请安装 <a href="https://chrome.google.com/webstore/search/heic" target="_blank">HEIC 插件</a> 查看原图,可能需科学上网<br>
                • Safari 浏览器：通常原生支持 HEIC 格式<br>
                • 其他浏览器：请先确认该浏览器是否支持、或者是否可以安装HEIC插件查看HEIC格式原图
            </small>
            <br>
            <small class="text-muted">
                你也可以点击下方按钮下载原图后用本地自带图片查看工具查看。
            </small>
        `;
        tipElement.style.display = 'block';
        console.log('HEIC 格式初始提示已显示');
    } else {
        console.error('未找到 heicFormatTip 元素');
    }
}

/**
 * 显示 HEIC 格式提示
 */
function showHeicFormatTip() {
    const tipElement = document.getElementById('heicFormatTip');
    if (tipElement) {
        tipElement.style.display = 'block';
        console.log('HEIC 格式提示已显示');
    } else {
        console.error('未找到 heicFormatTip 元素');
    }
}

/**
 * 隐藏 HEIC 格式提示
 */
function hideHeicFormatTip() {
    const tipElement = document.getElementById('heicFormatTip');
    if (tipElement) {
        tipElement.style.display = 'none';
        console.log('HEIC 格式提示已隐藏');
    }
}

/**
 * 显示缩略图降级提示
 */
function showThumbnailFallbackTip() {
    const tipElement = document.getElementById('heicFormatTip');
    if (tipElement) {
        // 修改提示内容
        tipElement.innerHTML = `
            <i class="bi bi-info-circle me-2"></i>
            <strong>HEIC 格式提示：</strong>您的浏览器无法直接显示 HEIC 格式原图，当前显示的是 JPEG 缩略图。
            <br>
            <small class="text-muted">
                • Chrome 浏览器：请安装 <a href="https://chrome.google.com/webstore/search/heic" target="_blank">HEIC 插件</a> 查看原图,可能需科学上网<br>
                • Safari 浏览器：通常原生支持 HEIC 格式<br>
                • 其他浏览器：请先确认该浏览器是否支持、或者是否可以安装HEIC插件查看HEIC格式原图
            </small>
            <br>
            <small class="text-muted">
                你也可以点击下方按钮下载原图后用本地自带图片查看工具查看。
            </small>
        `;
        tipElement.style.display = 'block';
        console.log('缩略图降级提示已显示');
    } else {
        console.error('未找到 heicFormatTip 元素');
    }
}

/**
 * 隐藏缩略图降级提示
 */
function hideThumbnailFallbackTip() {
    const tipElement = document.getElementById('heicFormatTip');
    if (tipElement) {
        tipElement.style.display = 'none';
        console.log('缩略图降级提示已隐藏');
    }
}

/**
 * 隐藏所有 HEIC 格式提示
 */
function hideAllHeicTips() {
    const tipElement = document.getElementById('heicFormatTip');
    if (tipElement) {
        tipElement.style.display = 'none';
        console.log('所有 HEIC 格式提示已隐藏');
    }
}

/**
 * 尝试显示缩略图作为备用
 * @param {HTMLImageElement} img - 图片元素
 */
function tryThumbnailFallback(img) {
    const originalSrc = img.src;
    
    // 从图片元素获取缩略图路径（如果存在）
    let thumbnailSrc = null;
    
    // 检查是否有 data-thumbnail 属性
    if (img.dataset.thumbnail) {
        thumbnailSrc = img.dataset.thumbnail;
    } else {
        // 尝试从原始路径构建缩略图路径
        if (originalSrc.includes('/originals/')) {
            // 从 /photos_storage/originals/ 替换为 /photos_storage/thumbnails/
            thumbnailSrc = originalSrc.replace('/photos_storage/originals/', '/photos_storage/thumbnails/');
        } else {
            // 从 /photos_storage/ 替换为 /photos_storage/thumbnails/
            thumbnailSrc = originalSrc.replace('/photos_storage/', '/photos_storage/thumbnails/');
        }
    }
    
    console.log('尝试缩略图备用方案:', { originalSrc, thumbnailSrc });
    
    if (thumbnailSrc !== originalSrc) {
        // 设置新的错误处理器，避免循环
        img.onerror = function() {
            console.log('缩略图也加载失败，显示占位符');
            this.errorHandled = true;
            
            // 使用 SVG 占位符
            const svgPlaceholder = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(`
                <svg width="400" height="300" xmlns="http://www.w3.org/2000/svg">
                    <rect width="100%" height="100%" fill="#f8f9fa"/>
                    <text x="50%" y="50%" text-anchor="middle" dy=".3em" fill="#6c757d" font-family="Arial, sans-serif" font-size="16">
                        Image Not Available
                    </text>
                </svg>
            `)}`;
            
            this.src = svgPlaceholder;
            this.onerror = null; // 移除错误处理器
        };
        
        // 设置新的加载成功处理器
        img.onload = function() {
            handleImageLoad(this);
        };
        
        img.src = thumbnailSrc;
    } else {
        // 没有缩略图，直接显示占位符
        console.log('没有缩略图，直接显示占位符');
        showGenericPlaceholder(img);
    }
}

/**
 * 显示通用占位符
 * @param {HTMLImageElement} img - 图片元素
 */
function showGenericPlaceholder(img) {
    console.log('显示通用占位符');
    img.errorHandled = true;
    
    // 使用一个简单的 SVG 占位符，避免 404 错误
    const svgPlaceholder = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(`
        <svg width="400" height="300" xmlns="http://www.w3.org/2000/svg">
            <rect width="100%" height="100%" fill="#f8f9fa"/>
            <text x="50%" y="50%" text-anchor="middle" dy=".3em" fill="#6c757d" font-family="Arial, sans-serif" font-size="16">
                Image Not Available
            </text>
        </svg>
    `)}`;
    
    img.src = svgPlaceholder;
    img.onerror = null; // 移除错误处理器，避免无限循环
}

// 导出 HEIC 处理函数
window.handleImageError = handleImageError;
window.handleImageLoad = handleImageLoad;

// ============ 调试和测试函数 ============

/**
 * 测试 HEIC 图片加载
 * @param {string} imagePath - 图片路径
 */
function testHeicImageLoad(imagePath) {
    console.log('🧪 开始测试 HEIC 图片加载:', imagePath);
    
    // 创建测试图片元素
    const testImg = document.createElement('img');
    testImg.style.maxWidth = '200px';
    testImg.style.border = '2px solid red';
    
    // 添加事件监听器
    testImg.onload = function() {
        console.log('✅ 测试图片加载成功:', this.src);
        document.body.appendChild(this);
    };
    
    testImg.onerror = function() {
        console.log('❌ 测试图片加载失败:', this.src);
        console.log('错误详情:', this.error);
        
        // 检查浏览器支持
        checkBrowserHeicSupport();
    };
    
    // 设置图片源
    testImg.src = imagePath;
    
    // 添加到页面
    document.body.appendChild(testImg);
}

/**
 * 检查浏览器 HEIC 支持
 */
function checkBrowserHeicSupport() {
    console.log('🔍 检查浏览器 HEIC 支持...');
    
    // 检查用户代理
    const userAgent = navigator.userAgent;
    console.log('用户代理:', userAgent);
    
    // 检查是否为 Edge
    const isEdge = userAgent.includes('Edg');
    const isChrome = userAgent.includes('Chrome') && !userAgent.includes('Edg');
    const isSafari = userAgent.includes('Safari') && !userAgent.includes('Chrome');
    
    console.log('浏览器类型:', { isEdge, isChrome, isSafari });
    
    // 检查插件支持
    if (isEdge) {
        console.log('🌐 Edge 浏览器检测到，请确认：');
        console.log('1. 已安装 HEIC 插件');
        console.log('2. 插件已启用');
        console.log('3. 插件权限已授予');
    }
}

/**
 * 手动测试 HEIC 提示显示
 */
function testHeicTipDisplay() {
    console.log('🧪 测试 HEIC 提示显示...');
    showHeicFormatTip();
    
    // 3秒后隐藏
    setTimeout(() => {
        hideHeicFormatTip();
        console.log('HEIC 提示已隐藏');
    }, 3000);
}

// 导出测试函数
window.testHeicImageLoad = testHeicImageLoad;
window.checkBrowserHeicSupport = checkBrowserHeicSupport;
window.testHeicTipDisplay = testHeicTipDisplay;
