/**
 * 家庭单机版智能照片整理系统 - UI交互模块
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
        elements.searchScopeHint.textContent = searchScopeHints['all'] || '支持搜索：照片名、用户照片描述、AI分析结果';
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
    // 使用Bootstrap API显示模态窗口
    const modal = new bootstrap.Modal(elements.importModal);
    modal.show();
}

function showBatchModal() {
    // 使用Bootstrap API显示模态窗口
    const modal = new bootstrap.Modal(elements.batchModal);
    modal.show();
}

// ============ 视图切换 ============

function switchView(viewType) {
    AppState.currentView = viewType;
    renderPhotos();
}

// ============ 照片详情 ============

function showPhotoDetail(photo) {
    console.log('显示照片详情:', photo);
    
    // 创建详情模态框内容
    const modalContent = createPhotoDetailModal(photo);
    
    // 更新模态框内容
    const modalBody = elements.photoModal.querySelector('.modal-body');
    modalBody.innerHTML = modalContent;
    
    // 更新模态框标题
    const modalTitle = elements.photoModal.querySelector('.modal-title');
    modalTitle.textContent = photo.filename;
    
    // 显示模态框
    const modal = new bootstrap.Modal(elements.photoModal);
    modal.show();
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
        <div class="row">
            <div class="col-md-6">
                <div class="text-center mb-3">
                    <img src="/photos_storage/${(photo.original_path || photo.thumbnail_path || CONFIG.IMAGE_PLACEHOLDER).replace(/\\/g, '/')}" 
                         alt="${photo.filename}" 
                         class="img-fluid rounded" 
                         style="max-height: 500px; object-fit: contain;">
                </div>
            </div>
            <div class="col-md-6">
                <div class="row">
                    <div class="col-12 mb-3">
                        <h5>基本信息</h5>
                        <div class="card">
                            <div class="card-body">
                                <p><strong>文件名：</strong>${photo.filename}</p>
                                <p><strong>拍摄时间：</strong>${formatDateTime(photo.taken_at)}</p>
                                <p><strong>分辨率：</strong>${photo.width || '未知'} × ${photo.height || '未知'}</p>
                                <p><strong>质量评级：</strong><span class="badge ${qualityClass}">${qualityText}</span></p>
                            </div>
                        </div>
                    </div>
                    
                    ${descriptionInfo.length > 0 ? `
                    <div class="col-12 mb-3">
                        <h5>用户照片描述</h5>
                        <div class="card">
                            <div class="card-body">
                                ${descriptionInfo.join('')}
                            </div>
                        </div>
                    </div>
                    ` : ''}
                    
                    ${exifInfo.length > 0 ? `
                    <div class="col-12 mb-3">
                        <h5>相机信息</h5>
                        <div class="card">
                            <div class="card-body">
                                ${exifInfo.map(info => `<p>${info}</p>`).join('')}
                            </div>
                        </div>
                    </div>
                    ` : ''}
                    
                    ${locationInfo.length > 0 ? `
                    <div class="col-12 mb-3">
                        <h5>位置信息</h5>
                        <div class="card">
                            <div class="card-body">
                                ${locationInfo.map(info => `<p>${info}</p>`).join('')}
                            </div>
                        </div>
                    </div>
                    ` : ''}
                    
                    ${aiInfo.length > 0 ? `
                    <div class="col-12 mb-3">
                        <h5>AI分析结果</h5>
                        <div class="card">
                            <div class="card-body">
                                ${aiInfo.join('')}
                            </div>
                        </div>
                    </div>
                    ` : ''}
                    
                    <div class="col-12 mb-3">
                        <h5>标签</h5>
                        <div class="card">
                            <div class="card-body">
                                ${photo.tags && photo.tags.length > 0 ? 
                                    photo.tags.map(tag => `<span class="badge bg-secondary me-1 mb-1">${tag}</span>`).join('') : 
                                    '<p class="text-muted">暂无标签</p>'
                                }
                            </div>
                        </div>
                    </div>
                    
                    ${categoryInfo.length > 0 ? `
                    <div class="col-12 mb-3">
                        <h5>分类</h5>
                        <div class="card">
                            <div class="card-body">
                                ${categoryInfo.join('')}
                            </div>
                        </div>
                    </div>
                    ` : ''}
                    
                    <div class="col-12 mb-3">
                        <h5>文件信息</h5>
                        <div class="card">
                            <div class="card-body">
                                ${fileInfo.map(info => `<p class="small">${info}</p>`).join('')}
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

// ============ 全局导出 ============

// 导出UI初始化函数
window.initializeUI = initializeUI;

// 导出模态框管理函数
window.showImportModal = showImportModal;
window.showBatchModal = showBatchModal;

// 导出视图切换函数
window.switchView = switchView;

// 导出照片详情函数
window.showPhotoDetail = showPhotoDetail;
window.createPhotoDetailModal = createPhotoDetailModal;

// 导出标签功能
window.toggleTags = toggleTags;
