/**
 * 家庭版智能照片系统 - UI组件脚本
 */

// JS文件版本号（与HTML中的?v=参数保持一致）
const UI_COMPONENTS_VERSION = '20250120_01';

// UI组件管理器
class UIComponents {
    constructor() {
        this.components = {};
        this.eventListeners = {};
    }

    // 初始化所有UI组件
    init() {
        this.initLoadingSpinner();
        this.initProgressBars();
        this.initTooltips();
        this.initModals();
        this.initDropdowns();
    }

    // 初始化加载动画
    initLoadingSpinner() {
        // 创建全局加载指示器
        if (!document.getElementById('globalLoading')) {
            const spinner = document.createElement('div');
            spinner.id = 'globalLoading';
            spinner.className = 'global-loading-overlay d-none';
            spinner.innerHTML = `
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">加载中...</span>
                </div>
            `;
            document.body.appendChild(spinner);
        }
    }

    // 显示全局加载
    showGlobalLoading() {
        const overlay = document.getElementById('globalLoading');
        if (overlay) {
            overlay.classList.remove('d-none');
        }
    }

    // 隐藏全局加载
    hideGlobalLoading() {
        const overlay = document.getElementById('globalLoading');
        if (overlay) {
            overlay.classList.add('d-none');
        }
    }

    // 初始化进度条
    initProgressBars() {
        this.progressBars = {};

        // 为所有进度条元素创建控制器
        document.querySelectorAll('[data-progress-id]').forEach(element => {
            const progressId = element.dataset.progressId;
            this.progressBars[progressId] = new ProgressController(element);
        });
    }

    // 获取进度条控制器
    getProgressBar(progressId) {
        return this.progressBars[progressId];
    }

    // 初始化工具提示
    initTooltips() {
        // 初始化所有Bootstrap工具提示
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // 初始化模态框
    initModals() {
        // 存储模态框实例
        this.modals = {};

        document.querySelectorAll('.modal').forEach(modal => {
            const modalId = modal.id;
            if (modalId) {
                this.modals[modalId] = new bootstrap.Modal(modal);
            }
        });
    }

    // 获取模态框实例
    getModal(modalId) {
        return this.modals[modalId];
    }

    // 初始化下拉菜单
    initDropdowns() {
        // 初始化所有Bootstrap下拉菜单
        const dropdownTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="dropdown"]'));
        dropdownTriggerList.map(function (dropdownTriggerEl) {
            return new bootstrap.Dropdown(dropdownTriggerEl);
        });
    }

    // 创建确认对话框
    createConfirmDialog(options = {}) {
        const {
            title = '确认操作',
            message = '确定要执行此操作吗？',
            confirmText = '确定',
            cancelText = '取消',
            confirmClass = 'btn-danger',
            onConfirm = () => {},
            onCancel = () => {}
        } = options;

        const modalHtml = `
            <div class="modal fade" id="confirmDialog" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">${title}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <p class="mb-0">${message}</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">${cancelText}</button>
                            <button type="button" class="btn ${confirmClass}" id="confirmBtn">${confirmText}</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // 移除现有的确认对话框
        const existingDialog = document.getElementById('confirmDialog');
        if (existingDialog) {
            existingDialog.remove();
        }

        // 添加新的对话框
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // 获取模态框实例
        const modal = new bootstrap.Modal(document.getElementById('confirmDialog'));

        // 绑定事件
        document.getElementById('confirmBtn').addEventListener('click', () => {
            onConfirm();
            modal.hide();
        });

        // 显示对话框
        modal.show();

        // 对话框关闭后清理DOM
        document.getElementById('confirmDialog').addEventListener('hidden.bs.modal', () => {
            document.getElementById('confirmDialog').remove();
        });
    }

    // 创建消息提示
    createAlert(options = {}) {
        const {
            type = 'info', // success, error, warning, info
            title = '',
            message = '',
            duration = 5000,
            dismissible = true
        } = options;

        const alertClasses = {
            'success': 'alert-success',
            'error': 'alert-danger',
            'warning': 'alert-warning',
            'info': 'alert-info'
        };

        const alertClass = alertClasses[type] || 'alert-info';
        const iconClass = this.getAlertIcon(type);

        const alertHtml = `
            <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
                ${iconClass ? `<i class="${iconClass} me-2"></i>` : ''}
                ${title ? `<strong>${title}</strong> ` : ''}
                ${message}
                ${dismissible ? '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>' : ''}
            </div>
        `;

        // 创建警告容器（如果不存在）
        let alertContainer = document.querySelector('.alert-container');
        if (!alertContainer) {
            alertContainer = document.createElement('div');
            alertContainer.className = 'alert-container position-fixed top-0 start-50 translate-middle-x mt-3';
            alertContainer.style.zIndex = '9999';
            document.body.appendChild(alertContainer);
        }

        // 添加警告
        alertContainer.insertAdjacentHTML('beforeend', alertHtml);

        // 自动消失
        if (duration > 0) {
            setTimeout(() => {
                const alert = alertContainer.lastElementChild;
                if (alert) {
                    const bsAlert = new bootstrap.Alert(alert);
                    bsAlert.close();
                }
            }, duration);
        }

        return alertContainer.lastElementChild;
    }

    // 获取警告图标
    getAlertIcon(type) {
        const icons = {
            'success': 'bi bi-check-circle-fill',
            'error': 'bi bi-exclamation-triangle-fill',
            'warning': 'bi bi-exclamation-triangle-fill',
            'info': 'bi bi-info-circle-fill'
        };
        return icons[type];
    }

    // 创建加载遮罩
    createLoadingOverlay(targetElement, options = {}) {
        const {
            text = '加载中...',
            spinnerSize = 'md'
        } = options;

        const spinnerClasses = {
            'sm': 'spinner-border-sm',
            'md': '',
            'lg': 'spinner-border-lg'
        };

        const spinnerClass = spinnerClasses[spinnerSize] || '';

        const overlayHtml = `
            <div class="loading-overlay d-flex flex-column justify-content-center align-items-center">
                <div class="spinner-border text-primary ${spinnerClass}" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <div class="mt-2 text-muted">${text}</div>
            </div>
        `;

        // 添加样式
        if (!document.getElementById('loading-overlay-styles')) {
            const style = document.createElement('style');
            style.id = 'loading-overlay-styles';
            style.textContent = `
                .loading-overlay {
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(255, 255, 255, 0.8);
                    backdrop-filter: blur(2px);
                    z-index: 1000;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                }
                .loading-overlay .spinner-border-lg {
                    width: 3rem;
                    height: 3rem;
                }
            `;
            document.head.appendChild(style);
        }

        targetElement.style.position = 'relative';
        targetElement.insertAdjacentHTML('beforeend', overlayHtml);

        return targetElement.querySelector('.loading-overlay');
    }

    // 移除加载遮罩
    removeLoadingOverlay(targetElement) {
        const overlay = targetElement.querySelector('.loading-overlay');
        if (overlay) {
            overlay.remove();
        }
    }

    // 创建空状态提示
    createEmptyState(targetElement, options = {}) {
        const {
            icon = 'bi bi-images',
            title = '暂无数据',
            message = '这里还没有任何内容',
            actionText = '',
            onAction = () => {}
        } = options;

        const emptyStateHtml = `
            <div class="empty-state text-center py-5">
                <i class="${icon} display-1 text-muted mb-3"></i>
                <h4 class="text-muted mb-2">${title}</h4>
                <p class="text-muted mb-4">${message}</p>
                ${actionText ? `<button class="btn btn-primary" onclick="${onAction}">${actionText}</button>` : ''}
            </div>
        `;

        targetElement.innerHTML = emptyStateHtml;
    }

    // 创建骨架屏
    createSkeleton(targetElement, type = 'card', count = 3) {
        const skeletons = [];

        for (let i = 0; i < count; i++) {
            if (type === 'card') {
                skeletons.push(`
                    <div class="col">
                        <div class="card skeleton-card">
                            <div class="skeleton-image"></div>
                            <div class="card-body">
                                <div class="skeleton-title"></div>
                                <div class="skeleton-text"></div>
                                <div class="skeleton-tags"></div>
                            </div>
                        </div>
                    </div>
                `);
            } else if (type === 'list') {
                skeletons.push(`
                    <div class="skeleton-list-item">
                        <div class="skeleton-thumbnail"></div>
                        <div class="skeleton-content">
                            <div class="skeleton-title"></div>
                            <div class="skeleton-text"></div>
                            <div class="skeleton-meta"></div>
                        </div>
                    </div>
                `);
            }
        }

        // 添加骨架屏样式
        if (!document.getElementById('skeleton-styles')) {
            const style = document.createElement('style');
            style.id = 'skeleton-styles';
            style.textContent = `
                .skeleton-card {
                    animation: pulse 2s infinite;
                }
                .skeleton-image {
                    height: 200px;
                    background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
                    background-size: 200% 100%;
                    animation: skeleton-loading 1.5s infinite;
                }
                .skeleton-title {
                    height: 1.2rem;
                    background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
                    background-size: 200% 100%;
                    animation: skeleton-loading 1.5s infinite;
                    border-radius: 4px;
                    margin-bottom: 0.5rem;
                }
                .skeleton-text {
                    height: 1rem;
                    background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
                    background-size: 200% 100%;
                    animation: skeleton-loading 1.5s infinite;
                    border-radius: 4px;
                    margin-bottom: 0.5rem;
                    width: 80%;
                }
                .skeleton-tags {
                    height: 1rem;
                    background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
                    background-size: 200% 100%;
                    animation: skeleton-loading 1.5s infinite;
                    border-radius: 12px;
                    width: 60%;
                }
                .skeleton-list-item {
                    display: flex;
                    padding: 1rem;
                    border: 1px solid #e9ecef;
                    border-radius: 8px;
                    margin-bottom: 0.5rem;
                    animation: pulse 2s infinite;
                }
                .skeleton-thumbnail {
                    width: 80px;
                    height: 60px;
                    background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
                    background-size: 200% 100%;
                    animation: skeleton-loading 1.5s infinite;
                    border-radius: 4px;
                    margin-right: 1rem;
                    flex-shrink: 0;
                }
                .skeleton-content {
                    flex: 1;
                }
                .skeleton-meta {
                    height: 0.8rem;
                    background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
                    background-size: 200% 100%;
                    animation: skeleton-loading 1.5s infinite;
                    border-radius: 4px;
                    width: 40%;
                }
                @keyframes skeleton-loading {
                    0% { background-position: -200% 0; }
                    100% { background-position: 200% 0; }
                }
                @keyframes pulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.7; }
                }
            `;
            document.head.appendChild(style);
        }

        targetElement.innerHTML = skeletons.join('');
    }

    // 创建图片懒加载
    initLazyLoading() {
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src || img.src;
                        img.classList.remove('lazy');
                        imageObserver.unobserve(img);
                    }
                });
            });

            document.querySelectorAll('img[data-src]').forEach(img => {
                imageObserver.observe(img);
            });
        }
    }

    // 创建响应式图片库
    createResponsiveGallery(container, images, options = {}) {
        const {
            columns = { xs: 1, sm: 2, md: 3, lg: 4, xl: 5 },
            gap = '1rem',
            aspectRatio = '4/3'
        } = options;

        const galleryHtml = `
            <div class="responsive-gallery" style="
                display: grid;
                grid-template-columns: repeat(${columns.xs}, 1fr);
                gap: ${gap};
            ">
                ${images.map(img => `
                    <div class="gallery-item">
                        <img src="${img.src}" alt="${img.alt || ''}"
                             style="width: 100%; aspect-ratio: ${aspectRatio}; object-fit: cover; border-radius: 8px;">
                    </div>
                `).join('')}
            </div>
        `;

        // 添加响应式样式
        if (!document.getElementById('gallery-styles')) {
            const style = document.createElement('style');
            style.id = 'gallery-styles';
            style.textContent = `
                @media (min-width: 576px) {
                    .responsive-gallery { grid-template-columns: repeat(${columns.sm}, 1fr); }
                }
                @media (min-width: 768px) {
                    .responsive-gallery { grid-template-columns: repeat(${columns.md}, 1fr); }
                }
                @media (min-width: 992px) {
                    .responsive-gallery { grid-template-columns: repeat(${columns.lg}, 1fr); }
                }
                @media (min-width: 1200px) {
                    .responsive-gallery { grid-template-columns: repeat(${columns.xl}, 1fr); }
                }
                .gallery-item {
                    transition: transform 0.3s ease;
                }
                .gallery-item:hover {
                    transform: scale(1.05);
                }
            `;
            document.head.appendChild(style);
        }

        container.innerHTML = galleryHtml;
    }
}

// 进度条控制器
class ProgressController {
    constructor(element) {
        this.element = element;
        this.progressBar = element.querySelector('.progress-bar');
        this.progressText = element.querySelector('.progress-text');
    }

    setProgress(percent, text = '') {
        if (this.progressBar) {
            this.progressBar.style.width = `${percent}%`;
        }

        if (this.progressText && text) {
            this.progressText.textContent = text;
        }
    }

    show() {
        this.element.style.display = 'block';
    }

    hide() {
        this.element.style.display = 'none';
    }

    reset() {
        this.setProgress(0, '');
    }
}

// 创建全局UI组件管理器实例
const uiComponents = new UIComponents();

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    uiComponents.init();
});

// 导出到全局作用域
window.UIComponents = uiComponents;

// 注册版本号（用于版本检测）
if (typeof window.registerJSVersion === 'function') {
    window.registerJSVersion('ui-components.js', UI_COMPONENTS_VERSION);
}
