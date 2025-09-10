/**
 * 家庭单机版智能照片整理系统 - 照片管理脚本
 */

// 照片管理器类
class PhotoManager {
    constructor() {
        this.selectedPhotos = new Set();
        this.isSelectionMode = false;
    }

    // 显示照片详情
    showPhotoDetail(photo) {
        const modal = document.getElementById('photoModal');
        const modalTitle = document.getElementById('photoModalTitle');
        const modalImage = document.getElementById('photoModalImage');
        const modalInfo = document.getElementById('photoModalInfo');

        // 设置模态框标题
        modalTitle.textContent = photo.filename;

        // 设置照片图片
        modalImage.src = photo.thumbnail_path || CONFIG.IMAGE_PLACEHOLDER;
        modalImage.alt = photo.filename;

        // 生成照片信息
        const infoHtml = this.generatePhotoInfoHtml(photo);
        modalInfo.innerHTML = infoHtml;

        // 显示模态框
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    }

    // 生成照片信息HTML
    generatePhotoInfoHtml(photo) {
        const tagsHtml = (photo.tags || []).map(tag =>
            `<span class="badge bg-primary me-1">${tag}</span>`
        ).join('');

        const categoriesHtml = (photo.categories || []).map(category =>
            `<span class="badge bg-success me-1">${category}</span>`
        ).join('');

        const qualityClass = this.getQualityBadgeClass(photo.quality?.level || '');
        const qualityText = this.getQualityText(photo.quality?.level || '');

        return `
            <div class="row g-3">
                <div class="col-12">
                    <h6><i class="bi bi-info-circle me-2"></i>基本信息</h6>
                    <table class="table table-sm">
                        <tbody>
                            <tr>
                                <td class="text-muted" style="width: 100px;">文件名</td>
                                <td>${photo.filename}</td>
                            </tr>
                            <tr>
                                <td class="text-muted">拍摄时间</td>
                                <td>${this.formatDateTime(photo.taken_at)}</td>
                            </tr>
                            <tr>
                                <td class="text-muted">文件大小</td>
                                <td>${this.formatFileSize(photo.file_size)}</td>
                            </tr>
                            <tr>
                                <td class="text-muted">分辨率</td>
                                <td>${photo.width} × ${photo.height}</td>
                            </tr>
                            <tr>
                                <td class="text-muted">相机</td>
                                <td>${photo.camera_make || '未知'} ${photo.camera_model || ''}</td>
                            </tr>
                            <tr>
                                <td class="text-muted">位置</td>
                                <td>${photo.location_name || '未知'}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                ${photo.analysis ? `
                <div class="col-12">
                    <h6><i class="bi bi-robot me-2"></i>AI分析结果</h6>
                    <div class="card">
                        <div class="card-body">
                            <p class="mb-2">${photo.analysis.description || '暂无描述'}</p>
                            <div class="mb-2">
                                <strong>场景类型：</strong>${photo.analysis.scene_type || '未知'}
                            </div>
                            <div class="mb-2">
                                <strong>识别物体：</strong>${(photo.analysis.objects || []).join('、') || '无'}
                            </div>
                            <div class="mb-2">
                                <strong>AI标签：</strong>${(photo.analysis.tags || []).join('、') || '无'}
                            </div>
                            <div>
                                <strong>置信度：</strong>
                                <div class="progress" style="height: 6px;">
                                    <div class="progress-bar bg-success" style="width: ${(photo.analysis.confidence || 0) * 100}%"></div>
                                </div>
                                <small class="text-muted">${Math.round((photo.analysis.confidence || 0) * 100)}%</small>
                            </div>
                        </div>
                    </div>
                </div>
                ` : ''}

                ${photo.quality ? `
                <div class="col-12">
                    <h6><i class="bi bi-star me-2"></i>质量评估</h6>
                    <div class="card">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <span>综合质量</span>
                                <span class="badge ${qualityClass}">${qualityText}</span>
                            </div>
                            <div class="row g-2">
                                <div class="col-6">
                                    <div class="text-center">
                                        <div class="small text-muted">清晰度</div>
                                        <div class="progress" style="height: 4px;">
                                            <div class="progress-bar bg-info" style="width: ${photo.quality.sharpness * 100}%"></div>
                                        </div>
                                        <small>${Math.round(photo.quality.sharpness * 100)}%</small>
                                    </div>
                                </div>
                                <div class="col-6">
                                    <div class="text-center">
                                        <div class="small text-muted">亮度</div>
                                        <div class="progress" style="height: 4px;">
                                            <div class="progress-bar bg-warning" style="width: ${photo.quality.brightness * 100}%"></div>
                                        </div>
                                        <small>${Math.round(photo.quality.brightness * 100)}%</small>
                                    </div>
                                </div>
                                <div class="col-6">
                                    <div class="text-center">
                                        <div class="small text-muted">对比度</div>
                                        <div class="progress" style="height: 4px;">
                                            <div class="progress-bar bg-secondary" style="width: ${photo.quality.contrast * 100}%"></div>
                                        </div>
                                        <small>${Math.round(photo.quality.contrast * 100)}%</small>
                                    </div>
                                </div>
                                <div class="col-6">
                                    <div class="text-center">
                                        <div class="small text-muted">色彩</div>
                                        <div class="progress" style="height: 4px;">
                                            <div class="progress-bar bg-primary" style="width: ${photo.quality.color * 100}%"></div>
                                        </div>
                                        <small>${Math.round(photo.quality.color * 100)}%</small>
                                    </div>
                                </div>
                            </div>
                            ${photo.quality.issues && photo.quality.issues.issues && photo.quality.issues.issues.length > 0 ? `
                            <div class="mt-3">
                                <div class="small text-muted mb-1">技术问题：</div>
                                <div class="small">
                                    ${photo.quality.issues.issues.map(issue => `<span class="badge bg-danger me-1">${issue}</span>`).join('')}
                                </div>
                            </div>
                            ` : ''}
                        </div>
                    </div>
                </div>
                ` : ''}

                <div class="col-12">
                    <h6><i class="bi bi-tags me-2"></i>标签和分类</h6>
                    <div class="mb-2">
                        <strong>标签：</strong>
                        ${tagsHtml || '<span class="text-muted">无标签</span>'}
                    </div>
                    <div>
                        <strong>分类：</strong>
                        ${categoriesHtml || '<span class="text-muted">未分类</span>'}
                    </div>
                </div>
            </div>
        `;
    }

    // 导入照片
    async importPhotos(files) {
        const formData = new FormData();

        for (let i = 0; i < files.length; i++) {
            formData.append('files', files[i]);
        }

        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/import/upload`, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                // 刷新照片列表
                window.PhotoApp.loadPhotos(1);
                window.PhotoApp.loadStats();

                // 显示成功消息
                this.showToast('照片导入成功！', 'success');
            } else {
                throw new Error(result.message || '导入失败');
            }
        } catch (error) {
            console.error('导入照片失败:', error);
            this.showToast(`导入失败: ${error.message}`, 'error');
        }
    }

    // 批量处理照片
    async batchProcessPhotos(options) {
        try {
            const params = new URLSearchParams({
                enable_ai: options.enableAIAnalysis,
                enable_quality: options.enableQualityAssessment,
                enable_classification: options.enableClassification
            });

            const response = await fetch(`${CONFIG.API_BASE_URL}/photos/batch-process?${params}`, {
                method: 'POST'
            });

            const result = await response.json();

            if (result.success) {
                // 刷新照片列表
                window.PhotoApp.loadPhotos(1);
                window.PhotoApp.loadStats();

                this.showToast('批量处理完成！', 'success');
            } else {
                throw new Error(result.message || '批量处理失败');
            }
        } catch (error) {
            console.error('批量处理失败:', error);
            this.showToast(`批量处理失败: ${error.message}`, 'error');
        }
    }

    // 删除照片
    async deletePhotos(photoIds) {
        if (!confirm(`确定要删除 ${photoIds.length} 张照片吗？此操作不可恢复！`)) {
            return;
        }

        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/photos/batch-delete`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ photo_ids: photoIds })
            });

            const result = await response.json();

            if (result.success) {
                // 刷新照片列表
                window.PhotoApp.loadPhotos(1);
                window.PhotoApp.loadStats();

                // 清空选择
                this.clearSelection();

                this.showToast('照片删除成功！', 'success');
            } else {
                throw new Error(result.message || '删除失败');
            }
        } catch (error) {
            console.error('删除照片失败:', error);
            this.showToast(`删除失败: ${error.message}`, 'error');
        }
    }

    // 选择/取消选择照片
    togglePhotoSelection(photoId) {
        if (this.selectedPhotos.has(photoId)) {
            this.selectedPhotos.delete(photoId);
        } else {
            this.selectedPhotos.add(photoId);
        }

        this.updateSelectionUI();
    }

    // 全选照片
    selectAllPhotos() {
        const photoCards = document.querySelectorAll('.photo-card, .photo-list-item');
        photoCards.forEach(card => {
            const photoId = card.dataset.photoId;
            if (photoId) {
                this.selectedPhotos.add(photoId);
            }
        });

        this.updateSelectionUI();
    }

    // 取消选择
    clearSelection() {
        this.selectedPhotos.clear();
        this.updateSelectionUI();
    }

    // 更新选择UI
    updateSelectionUI() {
        const photoCards = document.querySelectorAll('.photo-card, .photo-list-item');
        const selectedCount = this.selectedPhotos.size;

        // 更新照片卡片选中状态
        photoCards.forEach(card => {
            const photoId = card.dataset.photoId;
            const isSelected = this.selectedPhotos.has(photoId);

            if (isSelected) {
                card.classList.add('selected');
            } else {
                card.classList.remove('selected');
            }
        });

        // 更新删除按钮状态
        const deleteBtn = document.getElementById('deleteSelectedBtn');
        deleteBtn.disabled = selectedCount === 0;
        deleteBtn.innerHTML = selectedCount > 0 ?
            `<i class="bi bi-trash"></i> 删除选中 (${selectedCount})` :
            `<i class="bi bi-trash"></i> 删除选中`;

        // 更新全选按钮文本
        const selectAllBtn = document.getElementById('selectAllBtn');
        const totalPhotos = photoCards.length;
        selectAllBtn.textContent = selectedCount === totalPhotos ? '取消全选' : '全选';
    }

    // 获取选中的照片ID列表
    getSelectedPhotoIds() {
        return Array.from(this.selectedPhotos);
    }

    // 工具函数
    formatDateTime(dateString) {
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

    formatFileSize(bytes) {
        if (!bytes) return '未知大小';

        const units = ['B', 'KB', 'MB', 'GB'];
        let size = bytes;
        let unitIndex = 0;

        while (size >= 1024 && unitIndex < units.length - 1) {
            size /= 1024;
            unitIndex++;
        }

        return `${size.toFixed(1)} ${units[unitIndex]}`;
    }

    getQualityBadgeClass(level) {
        const classes = {
            'excellent': 'bg-success',
            'good': 'bg-success',
            'average': 'bg-warning',
            'poor': 'bg-danger',
            'bad': 'bg-danger'
        };
        return classes[level] || 'bg-secondary';
    }

    getQualityText(level) {
        const texts = {
            'excellent': '优秀',
            'good': '良好',
            'average': '一般',
            'poor': '较差',
            'bad': '很差'
        };
        return texts[level] || '一般';
    }

    showToast(message, type = 'info') {
        const toastClasses = {
            'success': 'bg-success',
            'error': 'bg-danger',
            'warning': 'bg-warning',
            'info': 'bg-info'
        };

        const toastClass = toastClasses[type] || 'bg-info';

        const toastHtml = `
            <div class="toast align-items-center text-white ${toastClass} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;

        const toastContainer = document.querySelector('.toast-container') || this.createToastContainer();
        toastContainer.insertAdjacentHTML('beforeend', toastHtml);

        const toast = new bootstrap.Toast(toastContainer.lastElementChild);
        toast.show();
    }

    createToastContainer() {
        const container = document.createElement('div');
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
        return container;
    }
}

// 创建全局照片管理器实例
const photoManager = new PhotoManager();

// 导出到全局作用域
window.PhotoManager = photoManager;
