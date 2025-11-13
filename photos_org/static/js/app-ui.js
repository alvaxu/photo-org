/**
 * 家庭版智能照片系统 - UI交互模块
 * 包含UI组件初始化、模态框管理、视图切换等交互功能
 */

// ============ UI组件初始化 ============

function initializeUI() {
    // 初始化UI组件

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


    // 存储在全局对象中
    window.modals = {
        photoModal,
        importModal
    };

    // 初始化搜索和筛选栏的展开/收起功能
    initializeSearchFilterCollapse();

    // 添加全局关闭函数
    window.closeModal = function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            // 关闭模态框
            
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

    // 同步AppState与HTML元素的默认值
    if (elements.sortBy && elements.sortOrder) {
        AppState.searchFilters.sortBy = elements.sortBy.value;
        AppState.searchFilters.sortOrder = elements.sortOrder.value;
        // 同步AppState排序默认值
    }

    // 模态框初始化完成

    // 添加测试函数
    window.testModalClose = function() {
        // 测试模态框关闭功能
        const modals = ['importModal', 'photoModal'];
        modals.forEach(modalId => {
            const modal = document.getElementById(modalId);
            if (modal) {
                // 检查模态框和关闭按钮
                const closeButtons = modal.querySelectorAll('[data-bs-dismiss="modal"]');
            }
        });
    };

    // 添加紧急清理函数
    window.forceCleanup = function() {
        // 强制清理页面状态
        
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
        
        // 强制清理完成
    };

    // 监听模态框事件并确保正确清理
    // 监听模态框显示事件
    document.addEventListener('shown.bs.modal', function(e) {
        // 特别检查importModal的显示，调用重置函数
        if (e.target.id === 'importModal') {
            resetImportModalState();
        }

    });
    
    // 监听模态框隐藏事件
    document.addEventListener('hidden.bs.modal', function(e) {
        // 确保清理所有可能的遮罩层
        setTimeout(() => {
            const backdrops = document.querySelectorAll('.modal-backdrop');
            backdrops.forEach(backdrop => backdrop.remove());

            // 确保body恢复正常状态
            document.body.classList.remove('modal-open');
            document.body.style.overflow = '';
            document.body.style.paddingRight = '';

            // 清理完成
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

    // 模态框事件监听器已在上方定义

    // 初始化工具提示
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// ============ 模态框管理 ============

function showImportModal() {
    console.log('🚀 showImportModal 被调用');

    // 使用Bootstrap API显示模态窗口
    const modal = new bootstrap.Modal(elements.importModal);
    modal.show();

    console.log('✅ showImportModal 执行完成');
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

    // 重置单选按钮状态
    const fileImportRadio = document.getElementById('fileImport');
    const folderImportRadio = document.getElementById('folderImport');
    if (fileImportRadio) {
        fileImportRadio.checked = true;
    }
    if (folderImportRadio) {
        folderImportRadio.checked = false;
    }

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
    
    // 获取photoModal元素（支持elements对象或直接查找）
    const photoModal = (typeof elements !== 'undefined' && elements.photoModal) 
        ? elements.photoModal 
        : document.getElementById('photoModal');
    
    if (!photoModal) {
        console.error('照片详情模态框未找到');
        alert('照片详情模态框未找到，请刷新页面重试');
        return;
    }
    
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
    
    // 检查是否有人物照片模态框显示，如果有则先隐藏并标记
    const personPhotosModal = document.getElementById('personPhotosModal');
    let wasPersonPhotosModalVisible = false;
    if (personPhotosModal && personPhotosModal.classList.contains('show')) {
        const personPhotosModalInstance = bootstrap.Modal.getInstance(personPhotosModal);
        if (personPhotosModalInstance) {
            personPhotosModalInstance.hide();
            wasPersonPhotosModalVisible = true;
        }
    }
    
    // 检查是否有聚类照片模态框显示，如果有则先隐藏并标记
    const clusterPhotosModal = document.getElementById('clusterPhotosModal');
    let wasClusterPhotosModalVisible = false;
    if (clusterPhotosModal && clusterPhotosModal.classList.contains('show')) {
        const clusterPhotosModalInstance = bootstrap.Modal.getInstance(clusterPhotosModal);
        if (clusterPhotosModalInstance) {
            clusterPhotosModalInstance.hide();
            wasClusterPhotosModalVisible = true;
        }
    }
    
    // 创建详情模态框内容
    const modalContent = createPhotoDetailModal(photo);
    
    // 更新模态框内容
    const modalBody = photoModal.querySelector('.modal-body');
    modalBody.innerHTML = modalContent;
    
    // 更新模态框标题
    const modalTitle = photoModal.querySelector('#photoModalTitle');
    if (modalTitle) {
        modalTitle.textContent = `照片详情 - ${photo.filename}`;
    }
    
    // 绑定下载按钮事件
    bindPhotoDetailEvents(photo);
    
    // 更新收藏按钮UI状态
    const favoriteBtn = photoModal.querySelector('#addToFavoritesBtn');
    if (favoriteBtn && photo) {
        updateFavoriteButtonUI(favoriteBtn, photo.is_favorite || false);
    }
    
    // 显示模态框
    const modal = new bootstrap.Modal(photoModal);
    modal.show();
    
    // 初始化照片缩放功能（在模态框显示后）
    photoModal.addEventListener('shown.bs.modal', function onModalShown() {
        if (typeof initPhotoZoom === 'function') {
            initPhotoZoom();
        }
        // 只执行一次
        photoModal.removeEventListener('shown.bs.modal', onModalShown);
    }, { once: true });
    
    // 监听详情模态框关闭事件，如果之前有其他模态框显示，则重新显示
    if (wasSimilarModalVisible || wasPersonPhotosModalVisible || wasClusterPhotosModalVisible) {
        photoModal.addEventListener('hidden.bs.modal', function onDetailModalHidden() {
            // 🔥 先清理可能残留的遮罩层
            const backdrops = document.querySelectorAll('.modal-backdrop');
            backdrops.forEach(backdrop => backdrop.remove());
            document.body.classList.remove('modal-open');
            document.body.style.overflow = '';
            document.body.style.paddingRight = '';
            
            // 重新显示之前的模态框
            if (wasSimilarModalVisible && similarModal) {
                const similarModalInstance = bootstrap.Modal.getInstance(similarModal) || new bootstrap.Modal(similarModal);
                similarModalInstance.show();
            } else if (wasPersonPhotosModalVisible && personPhotosModal) {
                // 🔥 尝试使用现有的实例（如果存在）
                let personModalInstance = bootstrap.Modal.getInstance(personPhotosModal);
                if (!personModalInstance && window.peopleManagementStandalone && window.peopleManagementStandalone.personPhotosModal) {
                    personModalInstance = window.peopleManagementStandalone.personPhotosModal;
                }
                if (!personModalInstance) {
                    personModalInstance = new bootstrap.Modal(personPhotosModal);
                }
                personModalInstance.show();
            } else if (wasClusterPhotosModalVisible && clusterPhotosModal) {
                // 🔥 尝试使用现有的实例（如果存在）
                let clusterModalInstance = bootstrap.Modal.getInstance(clusterPhotosModal);
                if (!clusterModalInstance && window.similarPhotosManagement && window.similarPhotosManagement.clusterPhotosModal) {
                    clusterModalInstance = window.similarPhotosManagement.clusterPhotosModal;
                }
                if (!clusterModalInstance) {
                    clusterModalInstance = new bootstrap.Modal(clusterPhotosModal);
                }
                clusterModalInstance.show();
            }
            // 移除事件监听器，避免重复绑定
            photoModal.removeEventListener('hidden.bs.modal', onDetailModalHidden);
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
        // AI内容描述
        if (photo.analysis.description) {
            aiInfo.push(`<div class="mb-2">
                <div><strong>AI内容描述：</strong></div>
                <div class="text-muted small">${photo.analysis.description}</div>
            </div>`);
        }

        // 场景类型
        if (photo.analysis.scene_type) {
            aiInfo.push(`<div class="mb-2">
                <div><strong>场景类型：</strong>${photo.analysis.scene_type}</div>
            </div>`);
        }

        // 检测到的物体
        if (photo.analysis.objects && photo.analysis.objects.length > 0) {
            aiInfo.push(`<div class="mb-2">
                <div><strong>检测到的物体：</strong></div>
                <div class="text-muted small">${photo.analysis.objects.join('、')}</div>
            </div>`);
        }

        // 人物数量
        if (photo.analysis.people_count) {
            aiInfo.push(`<div class="mb-2">
                <div><strong>人物数量：</strong>${photo.analysis.people_count}</div>
            </div>`);
        }

        // 情感
        if (photo.analysis.emotion) {
            aiInfo.push(`<div class="mb-2">
                <div><strong>情感：</strong>${photo.analysis.emotion}</div>
            </div>`);
        }

        // 活动类型
        if (photo.analysis.activity) {
            aiInfo.push(`<div class="mb-2">
                <div><strong>活动类型：</strong>${photo.analysis.activity}</div>
            </div>`);
        }

        // 时间特征
        if (photo.analysis.time_period) {
            aiInfo.push(`<div class="mb-2">
                <div><strong>时间特征：</strong>${photo.analysis.time_period}</div>
            </div>`);
        }

        // 地点类型
        if (photo.analysis.location_type) {
            aiInfo.push(`<div class="mb-2">
                <div><strong>地点类型：</strong>${photo.analysis.location_type}</div>
            </div>`);
        }

        // AI标签
        if (photo.analysis.tags && photo.analysis.tags.length > 0) {
            aiInfo.push(`<div class="mb-2">
                <div><strong>AI标签：</strong></div>
                <div class="text-muted small">${photo.analysis.tags.join('、')}</div>
            </div>`);
        }

        // 置信度
        if (photo.analysis.confidence) {
            aiInfo.push(`<div class="mb-2">
                <div><strong>置信度：</strong>${(photo.analysis.confidence * 100).toFixed(1)}%</div>
            </div>`);
        }

        // 分析时间
        if (photo.analysis.analyzed_at) {
            const analyzedDate = new Date(photo.analysis.analyzed_at);
            const formattedDate = analyzedDate.toLocaleString('zh-CN', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
            aiInfo.push(`<div class="mb-2">
                <div><strong>分析时间：</strong>${formattedDate}</div>
            </div>`);
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
    
    // 判断是否需要双图策略（HEIC/TIFF且有缩略图）
    const fn = photo.filename.toLowerCase();
    const isHeic = fn.endsWith('.heic') || fn.endsWith('.heif');
    const isTiff = fn.endsWith('.tiff') || fn.endsWith('.tif');
    const isWebp = fn.endsWith('.webp');
    const needsDualImage = (isHeic || isTiff || isWebp) && photo.thumbnail_path;
    
    const originalFormat = (function() {
        if (isHeic) return 'heic';
        if (isTiff) return 'tiff';
        if (isWebp) return 'webp';
        return 'other';
    })();
    
    // 标准图片路径
    const standardSrc = '/photos_storage/' + (photo.original_path || photo.thumbnail_path || CONFIG.IMAGE_PLACEHOLDER).replace(/\\/g, '/');
    const thumbnailSrc = photo.thumbnail_path ? '/photos_storage/' + photo.thumbnail_path.replace(/\\/g, '/') : '';
    const originalSrc = photo.original_path ? '/photos_storage/' + photo.original_path.replace(/\\/g, '/') : '';
    
    return `
        <!-- 照片显示区域 -->
        <div class="text-center mb-4">
            <div id="photoImageContainer" style="overflow: hidden; position: relative; height: 60vh; background: #000;">
                <div id="imageZoomWrapper" style="width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; cursor: move; position: relative;">
                    ${needsDualImage ? `
                    <!-- 双图策略：底层显示缩略图（HEIC/TIFF/WebP格式） -->
                    <img id="zoomablePhotoThumbnail" 
                         src="${thumbnailSrc}" 
                         alt="${photo.filename} (缩略图)" 
                         class="img-fluid rounded shadow" 
                         style="max-height: 60vh; max-width: 100%; object-fit: contain; user-select: none; position: absolute; z-index: 1;">
                    <!-- 上层尝试加载原图 -->
                    <img id="zoomablePhoto" 
                         src="${originalSrc}" 
                     alt="${photo.filename}" 
                     class="img-fluid rounded shadow" 
                         style="max-height: 60vh; max-width: 100%; object-fit: contain; user-select: none; transition: transform 0.1s, opacity 0.3s; position: relative; z-index: 2; opacity: 0;"
                         data-thumbnail="${thumbnailSrc}"
                         data-original-format="${originalFormat}"
                     data-original-path="${photo.original_path || ''}"
                     data-photo-id="${photo.id || ''}"
                         data-is-dual-image="true"
                     onerror="handleImageError(this);"
                     onload="handleImageLoad(this);">
                    ` : `
                    <!-- 标准单图策略（JPEG等格式） -->
                    <img id="zoomablePhoto" 
                         src="${standardSrc}" 
                         alt="${photo.filename}" 
                         class="img-fluid rounded shadow" 
                         style="max-height: 60vh; max-width: 100%; object-fit: contain; user-select: none; transition: transform 0.1s;"
                         data-thumbnail="${thumbnailSrc}"
                         data-original-format="${originalFormat}"
                         data-original-path="${photo.original_path || ''}"
                         data-photo-id="${photo.id || ''}"
                         data-is-dual-image="false"
                         onerror="handleImageError(this);"
                         onload="handleImageLoad(this);">
                    `}
                </div>
                
                <!-- 缩放控制按钮 -->
                <div class="zoom-controls" style="position: absolute; bottom: 10px; left: 50%; transform: translateX(-50%); background: rgba(0,0,0,0.7); border-radius: 20px; padding: 5px 15px; display: flex; align-items: center; gap: 10px;">
                    <button class="btn btn-sm btn-outline-light" onclick="zoomOutPhoto()" title="缩小">
                        <i class="bi bi-dash"></i>
                    </button>
                    <span id="zoomLevel" style="color: white; min-width: 50px; text-align: center; font-size: 12px;">100%</span>
                    <button class="btn btn-sm btn-outline-light" onclick="zoomInPhoto()" title="放大">
                        <i class="bi bi-plus"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-light" onclick="resetZoom()" title="重置">
                        <i class="bi bi-arrow-clockwise"></i>
                    </button>
                </div>
            </div>
            
            <!-- HEIC格式提示（移到容器外面） -->
                <div id="heicFormatTip" class="alert alert-info mt-2" style="display: none;">
                    <i class="bi bi-info-circle me-2"></i>
                    <strong>HEIC 格式提示：</strong>您的浏览器无法直接显示 HEIC 格式原图，当前显示的是 JPEG 缩略图。
                    <br>
                    <small class="text-muted">
                        • Chrome 浏览器：请安装 <a href="https://chrome.google.com/webstore/search/heic" target="_blank">HEIC 插件</a> 查看原图,可能需科学上网<br>
                        • Safari 浏览器：通常原生支持 HEIC 格式<br>
                    • 其他浏览器如EDGE浏览器：请尝试安装HEIC转换插件来显示高清图
                    </small>
                    <br>
                    <small class="text-muted">
                    你也可以点击右上角下载按钮下载原图后用电脑自带图片查看工具查看。
                    </small>
                </div>
            
            <small class="text-muted d-block mt-2">💡 提示：滚动鼠标滚轮可缩放照片，双击可重置，拖拽可移动</small>
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
            <!-- AI分析结果 - 占用更多宽度以适应内容 -->
            <div class="col-md-8">
                <div class="card h-100">
                    <div class="card-header">
                        <h6 class="card-title mb-0"><i class="bi bi-robot me-2"></i>AI分析结果</h6>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <!-- 左侧列：主要分析结果 -->
                            <div class="col-md-6">
                                ${aiInfo.slice(0, Math.ceil(aiInfo.length / 2)).join('')}
                            </div>
                            <!-- 右侧列：其他分析信息 -->
                            <div class="col-md-6">
                                ${aiInfo.slice(Math.ceil(aiInfo.length / 2)).join('')}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            ` : ''}
            
            <!-- 右侧信息区域 -->
            <div class="col-md-4">
                <div class="row g-3">
                    ${descriptionInfo.length > 0 ? `
                    <!-- 用户照片描述 -->
                    <div class="col-12">
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
                    <div class="col-12">
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
                    <div class="col-12">
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
                    <div class="col-12">
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

// ============ 搜索和筛选栏展开/收起功能 ============

/**
 * 初始化搜索和筛选栏的展开/收起功能
 */
function initializeSearchFilterCollapse() {
    const searchFilterContent = document.getElementById('searchFilterContent');
    const searchFilterToggle = document.getElementById('searchFilterToggle');
    const searchFilterToggleIcon = document.getElementById('searchFilterToggleIcon');
    
    if (!searchFilterContent || !searchFilterToggle) {
        return;
    }
    
    // 初始化Bootstrap Collapse
    let searchFilterCollapse = null;
    if (typeof bootstrap !== 'undefined') {
        searchFilterCollapse = new bootstrap.Collapse(searchFilterContent, { toggle: false });
    }
    
    // 按钮点击事件
    searchFilterToggle.addEventListener('click', () => {
        if (searchFilterCollapse) {
            searchFilterCollapse.toggle();
        }
    });
    
    // 监听展开事件
    searchFilterContent.addEventListener('shown.bs.collapse', () => {
        if (searchFilterToggleIcon) {
            searchFilterToggleIcon.classList.replace('bi-chevron-down', 'bi-chevron-up');
        }
        // 更新按钮文本
        const button = searchFilterToggle;
        Array.from(button.childNodes).forEach(node => {
            if (node.nodeType === Node.TEXT_NODE) {
                node.remove();
            }
        });
        button.appendChild(document.createTextNode('点击收起'));
    });
    
    // 监听收起事件
    searchFilterContent.addEventListener('hidden.bs.collapse', () => {
        if (searchFilterToggleIcon) {
            searchFilterToggleIcon.classList.replace('bi-chevron-up', 'bi-chevron-down');
        }
        // 更新按钮文本
        const button = searchFilterToggle;
        Array.from(button.childNodes).forEach(node => {
            if (node.nodeType === Node.TEXT_NODE) {
                node.remove();
            }
        });
        button.appendChild(document.createTextNode('点击展开'));
    });
    
    // 存储到全局，方便其他地方使用
    window.searchFilterCollapse = searchFilterCollapse;
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
async function toggleFavorite(photoId) {
    try {
        console.log('切换收藏状态:', photoId);
        
        // 获取收藏按钮
        const favoriteBtn = elements.photoModal.querySelector('#addToFavoritesBtn');
        if (!favoriteBtn) {
            console.error('收藏按钮未找到');
            return;
        }
        
        // 获取当前收藏状态（从按钮的 data 属性或通过 API 获取）
        let currentFavoriteState = false;
        if (favoriteBtn.dataset.isFavorite !== undefined) {
            currentFavoriteState = favoriteBtn.dataset.isFavorite === 'true';
        } else {
            // 如果没有保存状态，先获取照片信息
            try {
                const response = await fetch(`/api/v1/photos/${photoId}`);
                if (response.ok) {
                    const photoData = await response.json();
                    currentFavoriteState = photoData.is_favorite || false;
                }
            } catch (e) {
                console.warn('获取照片信息失败，使用默认状态:', e);
            }
        }
        
        // 切换收藏状态
        const newFavoriteState = !currentFavoriteState;
        
        // 显示加载状态
        const originalHTML = favoriteBtn.innerHTML;
        favoriteBtn.disabled = true;
        favoriteBtn.innerHTML = '<i class="bi bi-hourglass-split"></i>';
        
        // 调用API更新收藏状态
        const response = await fetch(`/api/v1/photos/${photoId}/favorite`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                is_favorite: newFavoriteState
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || '更新收藏状态失败');
        }
        
        const result = await response.json();
        
        // 更新按钮UI（按钮颜色和图标已经能够清楚地显示状态，无需额外提示）
        updateFavoriteButtonUI(favoriteBtn, result.is_favorite);
        
    } catch (error) {
        console.error('切换收藏状态失败:', error);
        if (typeof showError === 'function') {
            showError('收藏操作失败: ' + error.message);
        } else {
            alert('收藏操作失败: ' + error.message);
        }
        
        // 恢复按钮状态
        const favoriteBtn = elements.photoModal.querySelector('#addToFavoritesBtn');
        if (favoriteBtn) {
            favoriteBtn.disabled = false;
            // 尝试恢复原始状态（如果可能）
            const currentState = favoriteBtn.dataset.isFavorite === 'true';
            updateFavoriteButtonUI(favoriteBtn, currentState);
        }
    }
}

/**
 * 更新收藏按钮的UI状态
 * @param {HTMLElement} button - 收藏按钮元素
 * @param {boolean} isFavorite - 是否收藏
 */
function updateFavoriteButtonUI(button, isFavorite) {
    if (!button) return;
    
    // 更新按钮状态
    button.disabled = false;
    button.dataset.isFavorite = isFavorite.toString();
    
    // 更新按钮样式和图标
    if (isFavorite) {
        // 已收藏：实心图标 + 红色样式
        button.className = 'btn btn-sm btn-danger';
        button.innerHTML = '<i class="bi bi-heart-fill"></i>';
        button.title = '取消收藏';
    } else {
        // 未收藏：空心图标 + 绿色边框样式
        button.className = 'btn btn-sm btn-outline-success';
        button.innerHTML = '<i class="bi bi-heart"></i>';
        button.title = '添加到收藏';
    }
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
    
    // 检查图片格式（支持 HEIC、TIFF、WebP）
    const imgSrcLower = img.src.toLowerCase();
    const originalFormat = img.dataset.originalFormat || 'other';
    const isDualImage = img.dataset.isDualImage === 'true';
    
    const isHeicFormat = originalFormat === 'heic' || imgSrcLower.includes('.heic') || imgSrcLower.includes('.heif');
    const isTiffFormat = originalFormat === 'tiff' || imgSrcLower.includes('.tiff') || imgSrcLower.includes('.tif');
    const isWebpFormat = originalFormat === 'webp' || imgSrcLower.includes('.webp');
    const isBrowserUnsupportedFormat = isHeicFormat || isTiffFormat || isWebpFormat;
    
    if (isDualImage && isBrowserUnsupportedFormat) {
        // 双图策略：原图加载失败，保持隐藏状态，让底层缩略图显示
        console.log(`${originalFormat.toUpperCase()}原图加载失败（双图策略），底层缩略图继续显示`);
        img.errorHandled = true;
        img.style.opacity = '0';  // 确保原图隐藏
        showFormatTip(originalFormat);
    } else if (isBrowserUnsupportedFormat && !isDualImage) {
        // 单图策略：浏览器不支持的格式，尝试缩略图降级
        console.log(`${originalFormat.toUpperCase()}图片加载失败，尝试缩略图降级`);
        img.errorHandled = true;
        showFormatTip(originalFormat);
        tryThumbnailFallback(img);
    } else {
        // 其他格式：直接显示占位符
        img.errorHandled = true;
        showGenericPlaceholder(img);
    }
}

/**
 * 处理图片加载成功
 * @param {HTMLImageElement} img - 图片元素
 */
function handleImageLoad(img) {
    console.log('图片加载成功:', img.src);
    
    const originalFormat = img.dataset.originalFormat || 'other';
    const isBrowserUnsupportedFormat = originalFormat === 'heic' || originalFormat === 'tiff' || originalFormat === 'webp';
    const isDualImage = img.dataset.isDualImage === 'true';
    
    if (isDualImage) {
        // 双图策略：原图加载成功，显示原图（覆盖缩略图）
        console.log(`${originalFormat.toUpperCase()}原图加载成功（浏览器支持或已转换），覆盖缩略图显示`);
        img.style.opacity = '1';  // 让原图显示，覆盖底层缩略图
        hideAllFormatTips();
    } else {
        // 单图策略
        if (isBrowserUnsupportedFormat) {
            const isCurrentlyShowingThumbnail = img.src.includes('/thumbnails/') || img.src.includes('_thumb.');
            if (isCurrentlyShowingThumbnail) {
                // 显示的是缩略图（原图加载失败后降级）
                console.log(`${originalFormat.toUpperCase()}原图加载失败，显示缩略图`);
                showThumbnailFallbackTip(originalFormat);
            } else {
                // 显示的是原图（浏览器支持或转换成功）
                console.log(`${originalFormat.toUpperCase()}原图加载成功（浏览器支持或已转换）`);
                hideAllFormatTips();
            }
        } else {
            // 其他格式
            hideAllFormatTips();
        }
    }
}

/**
 * 显示格式提示（支持 HEIC、TIFF、WebP）
 * @param {string} format - 图片格式 ('heic', 'tiff', 'webp')
 */
function showFormatTip(format) {
    const tipElement = document.getElementById('heicFormatTip'); // 复用同一个元素
    if (!tipElement) {
        console.error('未找到格式提示元素');
        return;
    }
    
    let formatName, formatUpper, tipContent;
    
    switch(format) {
        case 'heic':
            formatName = 'HEIC';
            formatUpper = 'HEIC';
            tipContent = `
            <i class="bi bi-info-circle me-2"></i>
            <strong>HEIC 格式提示：</strong>您的浏览器无法直接显示 HEIC 格式原图，当前显示的是 JPEG 缩略图。
            <br>
            <small class="text-muted">
                • Chrome 浏览器：请安装 <a href="https://chrome.google.com/webstore/search/heic" target="_blank">HEIC 插件</a> 查看原图,可能需科学上网<br>
                • Safari 浏览器：通常原生支持 HEIC 格式<br>
                    • 其他浏览器如EDGE浏览器：请尝试安装HEIC转换插件来显示高清图
            </small>
            <br>
            <small class="text-muted">
                    你也可以点击右上角下载按钮下载原图后用电脑自带图片查看工具查看。
            </small>
        `;
            break;
        case 'tiff':
            formatName = 'TIFF';
            formatUpper = 'TIFF';
            tipContent = `
                <i class="bi bi-info-circle me-2"></i>
                <strong>TIFF 格式提示：</strong>您的浏览器无法直接显示 TIFF 格式原图，当前显示的是 JPEG 缩略图。
                <br>
                <small class="text-muted">
                    • 大多数浏览器不支持直接显示 TIFF 格式<br>
                    • 你可以点击右上角下载按钮下载原图后用电脑自带图片查看工具查看<br>
                    • 或者使用专业的图片查看软件（如 Photoshop、Windows 照片查看器等）
                </small>
            `;
            break;
        case 'webp':
            formatName = 'WebP';
            formatUpper = 'WebP';
            tipContent = `
                <i class="bi bi-info-circle me-2"></i>
                <strong>WebP 格式提示：</strong>您的浏览器可能无法直接显示 WebP 格式原图，当前显示的是 JPEG 缩略图。
                <br>
                <small class="text-muted">
                    • 现代浏览器（Chrome、Edge、Firefox 等）通常支持 WebP 格式<br>
                    • 如果原图无法显示，当前显示的是 JPEG 缩略图<br>
                    • 你可以点击右上角下载按钮下载原图查看
                </small>
            `;
            break;
        default:
            console.warn('未知的格式类型:', format);
            return;
    }
    
    tipElement.innerHTML = tipContent;
        tipElement.style.display = 'block';
    console.log(`${formatUpper} 格式初始提示已显示`);
}

/**
 * 显示 HEIC 格式初始提示（兼容旧代码）
 */
function showHeicFormatTipInitial() {
    showFormatTip('heic');
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
 * @param {string} format - 图片格式 ('heic', 'tiff', 'webp')
 */
function showThumbnailFallbackTip(format = 'heic') {
    showFormatTip(format);
}

/**
 * 隐藏缩略图降级提示
 */
function hideThumbnailFallbackTip() {
    hideAllFormatTips();
}

/**
 * 隐藏所有格式提示（支持 HEIC、TIFF、WebP）
 */
function hideAllFormatTips() {
    const tipElement = document.getElementById('heicFormatTip');
    if (tipElement) {
        tipElement.style.display = 'none';
        console.log('所有格式提示已隐藏');
    }
}

/**
 * 隐藏所有 HEIC 格式提示（兼容旧代码）
 */
function hideAllHeicTips() {
    hideAllFormatTips();
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

// ============ 照片缩放功能 ============

let photoZoomState = {
    scale: 1,
    translateX: 0,
    translateY: 0,
    isDragging: false,
    startX: 0,
    startY: 0,
    currentTranslateX: 0,
    currentTranslateY: 0
};

/**
 * 初始化照片缩放功能
 */
function initPhotoZoom() {
    try {
        const container = document.getElementById('photoImageContainer');
        const wrapper = document.getElementById('imageZoomWrapper');
        const img = document.getElementById('zoomablePhoto');
        
        if (!container || !wrapper || !img) {
            return;
        }
        
        // 确保状态已初始化
        if (!window.photoZoomState) {
            window.photoZoomState = {
                scale: 1,
                translateX: 0,
                translateY: 0,
                isDragging: false,
                startX: 0,
                startY: 0,
                currentTranslateX: 0,
                currentTranslateY: 0
            };
        }
        const zoomState = window.photoZoomState;
        
        // 重置缩放状态
        zoomState.scale = 1;
        zoomState.translateX = 0;
        zoomState.translateY = 0;
        
        // 重置样式（支持双图策略）
        const thumbnailImg = document.getElementById('zoomablePhotoThumbnail');
        if (thumbnailImg) {
            thumbnailImg.style.transform = 'scale(1)';
        }
        img.style.transform = 'scale(1)';
        wrapper.style.transform = 'translate(0, 0)';
        wrapper.style.cursor = 'move';
        
        const zoomLevel = document.getElementById('zoomLevel');
        if (zoomLevel) {
            zoomLevel.textContent = '100%';
        }
        
        // 绑定滚轮事件
        container.addEventListener('wheel', (e) => {
            e.preventDefault();
            const delta = e.deltaY > 0 ? -0.1 : 0.1;
            updateZoom(delta);
        }, { passive: false });
        
        // 绑定双击事件（重置）
        img.addEventListener('dblclick', () => {
            resetZoom();
        });
        
        // 绑定拖拽事件
        let isDragging = false;
        let startX, startY, currentX = 0, currentY = 0;
        
        wrapper.addEventListener('mousedown', (e) => {
            if (zoomState.scale > 1) {
                isDragging = true;
                startX = e.clientX - currentX;
                startY = e.clientY - currentY;
                wrapper.style.cursor = 'grabbing';
            }
        });
        
        document.addEventListener('mousemove', (e) => {
            if (isDragging && zoomState.scale > 1) {
                e.preventDefault();
                currentX = e.clientX - startX;
                currentY = e.clientY - startY;
                
                // 限制拖拽范围（使用原始图片尺寸计算）
                const containerRect = container.getBoundingClientRect();
                const originalWidth = img.naturalWidth || img.width;
                const originalHeight = img.naturalHeight || img.height;
                
                // 计算实际缩放后的尺寸
                const scaledWidth = originalWidth * zoomState.scale;
                const scaledHeight = originalHeight * zoomState.scale;
                
                // 允许拖拽的范围
                const maxX = Math.max(0, (scaledWidth - containerRect.width) / 2);
                const maxY = Math.max(0, (scaledHeight - containerRect.height) / 2);
                
                // 应用边界限制
                currentX = Math.max(-maxX, Math.min(maxX, currentX));
                currentY = Math.max(-maxY, Math.min(maxY, currentY));
                
                wrapper.style.transform = `translate(${currentX}px, ${currentY}px)`;
            }
        });
        
        document.addEventListener('mouseup', () => {
            if (isDragging) {
                isDragging = false;
                wrapper.style.cursor = zoomState.scale > 1 ? 'grab' : 'move';
            }
        });
        
        // 更新样式
        wrapper.style.cursor = zoomState.scale > 1 ? 'grab' : 'move';
    } catch (error) {
        console.error('照片缩放功能初始化失败:', error);
    }
}

/**
 * 更新缩放
 */
function updateZoom(delta) {
    const zoomState = window.photoZoomState || { scale: 1 };
    const newScale = Math.max(0.5, Math.min(zoomState.scale + delta, 5));
    
    if (newScale !== zoomState.scale) {
        zoomState.scale = newScale;
        applyZoom();
    }
}

/**
 * 应用缩放变换（支持双图策略）
 */
function applyZoom() {
    const zoomState = window.photoZoomState || { scale: 1 };
    const img = document.getElementById('zoomablePhoto');
    const thumbnailImg = document.getElementById('zoomablePhotoThumbnail');
    const zoomLevel = document.getElementById('zoomLevel');
    
    // 同时缩放原图和缩略图（双图策略）
    if (img) {
        img.style.transform = `scale(${zoomState.scale})`;
    }
    if (thumbnailImg) {
        thumbnailImg.style.transform = `scale(${zoomState.scale})`;
    }
    
    if (zoomLevel) {
        zoomLevel.textContent = `${Math.round(zoomState.scale * 100)}%`;
    }
}

/**
 * 放大照片
 */
function zoomInPhoto() {
    updateZoom(0.2);
}

/**
 * 缩小照片
 */
function zoomOutPhoto() {
    updateZoom(-0.2);
}

/**
 * 重置缩放
 */
function resetZoom() {
    const zoomState = window.photoZoomState || { scale: 1, translateX: 0, translateY: 0 };
    zoomState.scale = 1;
    zoomState.translateX = 0;
    zoomState.translateY = 0;
    
    const img = document.getElementById('zoomablePhoto');
    const thumbnailImg = document.getElementById('zoomablePhotoThumbnail');
    const wrapper = document.getElementById('imageZoomWrapper');
    const zoomLevel = document.getElementById('zoomLevel');
    
    // 重置原图和缩略图（双图策略）
    if (img) {
        img.style.transform = 'scale(1)';
    }
    if (thumbnailImg) {
        thumbnailImg.style.transform = 'scale(1)';
    }
    
    if (wrapper) {
        wrapper.style.transform = 'translate(0, 0)';
        wrapper.style.cursor = 'move';
    }
    
    if (zoomLevel) {
        zoomLevel.textContent = '100%';
    }
}

// 导出缩放函数供全局使用
window.zoomInPhoto = zoomInPhoto;
window.zoomOutPhoto = zoomOutPhoto;
window.resetZoom = resetZoom;

