/**
 * 家庭版智能照片系统 - 混合设备交互管理
 * 
 * 功能：
 * 1. 检测设备类型和输入方式
 * 2. 管理照片卡片的触摸/鼠标交互
 * 3. 处理按钮显示/隐藏逻辑
 * 4. 支持混合设备的动态输入切换
 */


/**
 * 混合设备输入管理器
 */
const HybridInputManager = {
    currentInputType: null,
    lastInputTime: 0,
    touchCooldown: 500, // 触摸后500ms内忽略鼠标事件
    
    /**
     * 检测输入类型
     * @param {Event} event - 事件对象
     * @returns {boolean} 是否应该响应此事件
     */
    detectInputType(event) {
        const now = Date.now();
        
        if (event.type.includes('touch')) {
            this.currentInputType = 'touch';
            this.lastInputTime = now;
            return true;
        } else if (event.type.includes('mouse')) {
            // 检查是否是触摸后的鼠标事件
            if (now - this.lastInputTime > this.touchCooldown) {
                this.currentInputType = 'mouse';
                return true;
            } else {
                // 触摸后的鼠标事件，忽略
                return false;
            }
        }
        
        return false;
    },
    
    /**
     * 判断是否应该响应事件
     * @param {Event} event - 事件对象
     * @returns {boolean} 是否应该响应
     */
    shouldRespond(event) {
        return this.detectInputType(event);
    },
    
    /**
     * 获取当前输入类型
     * @returns {string|null} 当前输入类型
     */
    getCurrentInputType() {
        return this.currentInputType;
    }
};

/**
 * 照片交互管理器
 */
const PhotoInteractionManager = {
    activePhotoId: null,
    autoHideTimer: null,
    
    /**
     * 初始化事件监听
     */
    init() {
        // 为每个照片卡片添加事件监听
        this.setupPhotoCards();
        
        // 监听按钮点击事件
        this.setupButtonEvents();
        
        // 监听点击其他区域隐藏按钮
        this.setupGlobalEvents();
    },
    
    /**
     * 设置照片卡片事件
     */
    setupPhotoCards() {
        // 使用事件委托，监听所有照片卡片（网格模式和列表模式）
        document.addEventListener('touchstart', (e) => {
            if (e.target && e.target.closest) {
                const card = e.target.closest('.photo-card, .photo-list-item');
                if (card && HybridInputManager.shouldRespond(e)) {
                    // 检查是否点击的是照片图片区域（不是按钮区域）
                    const photoImage = e.target.closest('.photo-image, .photo-thumbnail');
                    const photoOverlay = e.target.closest('.photo-overlay');
                    
                    if (photoImage && !photoOverlay) {
                        e.preventDefault();
                        e.stopPropagation();
                        const photoId = card.dataset.photoId;
                        this.handleTouchStart(photoId, card);
                    }
                }
            }
        }, { passive: false });
        
        document.addEventListener('touchend', (e) => {
            if (e.target && e.target.closest) {
                const card = e.target.closest('.photo-card, .photo-list-item');
                if (card && HybridInputManager.getCurrentInputType() === 'touch') {
                    // 检查是否点击的是照片图片区域（不是按钮区域）
                    const photoImage = e.target.closest('.photo-image, .photo-thumbnail');
                    const photoOverlay = e.target.closest('.photo-overlay');
                    
                    if (photoImage && !photoOverlay) {
                        e.preventDefault();
                        e.stopPropagation();
                        const photoId = card.dataset.photoId;
                        this.handleTouchEnd(photoId, card);
                    }
                }
            }
        }, { passive: false });
        
        document.addEventListener('mouseenter', (e) => {
            if (e.target && e.target.closest) {
                const card = e.target.closest('.photo-card, .photo-list-item');
                if (card && HybridInputManager.shouldRespond(e)) {
                    // 检查是否悬停在照片区域（图片区域或按钮区域）
                    const photoImage = e.target.closest('.photo-image, .photo-thumbnail');
                    const photoOverlay = e.target.closest('.photo-overlay');
                    
                    if (photoImage || photoOverlay) {
                        const photoId = card.dataset.photoId;
                        this.handleMouseEnter(photoId, card);
                    }
                }
            }
        }, true);
        
        document.addEventListener('mouseleave', (e) => {
            if (e.target && e.target.closest) {
                const card = e.target.closest('.photo-card, .photo-list-item');
                if (card && HybridInputManager.shouldRespond(e)) {
                    // 检查是否离开照片区域（图片区域或按钮区域）
                    const photoImage = e.target.closest('.photo-image, .photo-thumbnail');
                    const photoOverlay = e.target.closest('.photo-overlay');
                    
                    if (photoImage || photoOverlay) {
                        const photoId = card.dataset.photoId;
                        this.handleMouseLeave(photoId, card);
                    }
                }
            }
        }, true);
        
        // 移除click事件，避免与触摸事件冲突
    },
    
    /**
     * 设置按钮事件
     */
    setupButtonEvents() {
        // 使用touchstart和touchend处理触摸设备的按钮点击
        document.addEventListener('touchstart', (e) => {
            if (e.target && e.target.closest) {
                const button = e.target.closest('.photo-overlay .btn');
                if (button) {
                    e.preventDefault();
                    e.stopPropagation();
                    e.stopImmediatePropagation(); // 阻止同一元素上的其他事件监听器
                    
                    const photoId = button.dataset.photoId;
                    const action = button.dataset.action;
                    
                    // 检查按钮是否可用
                    if (this.activePhotoId === photoId) {
                        // 执行按钮动作
                        this.executeButtonAction(action, photoId);
                        // 隐藏按钮
                        this.hideButtons(photoId);
                    }
                    
                    return false; // 进一步阻止事件传播
                }
            }
        }, { passive: false, capture: true }); // 使用捕获阶段，确保在其他事件之前处理
        
        // 使用click处理鼠标设备的按钮点击
        document.addEventListener('click', (e) => {
            if (e.target && e.target.closest) {
                const button = e.target.closest('.photo-overlay .btn');
                if (button && HybridInputManager.getCurrentInputType() === 'mouse') {
                    e.preventDefault();
                    e.stopPropagation();
                    e.stopImmediatePropagation(); // 阻止同一元素上的其他事件监听器
                    
                    const photoId = button.dataset.photoId;
                    const action = button.dataset.action;
                    
                    // 检查按钮是否可用
                    if (this.activePhotoId === photoId) {
                        // 执行按钮动作
                        this.executeButtonAction(action, photoId);
                        // 隐藏按钮
                        this.hideButtons(photoId);
                    }
                    
                    return false; // 进一步阻止事件传播
                }
            }
        }, { passive: false, capture: true }); // 使用捕获阶段，确保在其他事件之前处理
    },
    
    /**
     * 设置全局事件
     */
    setupGlobalEvents() {
        // 点击其他区域隐藏按钮
        document.addEventListener('click', (e) => {
            if (e.target && e.target.closest && !e.target.closest('.photo-card, .photo-list-item')) {
                this.hideAllButtons();
            }
        });
        
        // 触摸其他区域隐藏按钮
        document.addEventListener('touchstart', (e) => {
            if (e.target && e.target.closest && !e.target.closest('.photo-card, .photo-list-item')) {
                this.hideAllButtons();
            }
        });
    },
    
    /**
     * 触摸开始处理
     * @param {string} photoId - 照片ID
     * @param {HTMLElement} card - 照片卡片元素
     */
    handleTouchStart(photoId, card) {
        this.showButtons(photoId, card);
    },
    
    /**
     * 触摸结束处理
     * @param {string} photoId - 照片ID
     * @param {HTMLElement} card - 照片卡片元素
     */
    handleTouchEnd(photoId, card) {
        // 触摸结束只显示按钮，不执行其他动作
        this.showButtons(photoId, card);
    },
    
    /**
     * 鼠标悬停处理
     * @param {string} photoId - 照片ID
     * @param {HTMLElement} card - 照片卡片元素
     */
    handleMouseEnter(photoId, card) {
        this.showButtons(photoId, card);
    },
    
    /**
     * 鼠标离开处理
     * @param {string} photoId - 照片ID
     * @param {HTMLElement} card - 照片卡片元素
     */
    handleMouseLeave(photoId, card) {
        this.hideButtons(photoId, card);
    },
    
    /**
     * 显示按钮
     * @param {string} photoId - 照片ID
     * @param {HTMLElement} card - 照片卡片元素
     */
    showButtons(photoId, card) {
        // 如果切换了照片，先隐藏之前的按钮
        if (this.activePhotoId && this.activePhotoId !== photoId) {
            this.hideAllButtons();
        }
        
        this.activePhotoId = photoId;
        card.classList.add('buttons-active');
        
        // 清除之前的自动隐藏定时器
        if (this.autoHideTimer) {
            clearTimeout(this.autoHideTimer);
            this.autoHideTimer = null;
        }
        
        // 设置新的自动隐藏定时器
        this.setAutoHide(photoId, card);
    },
    
    /**
     * 隐藏按钮
     * @param {string} photoId - 照片ID
     * @param {HTMLElement} card - 照片卡片元素
     */
    hideButtons(photoId, card) {
        if (this.activePhotoId === photoId) {
            this.activePhotoId = null;
            if (card) {
                card.classList.remove('buttons-active');
            } else {
                // 如果没有传入card，查找对应的卡片
                const targetCard = document.querySelector(`[data-photo-id="${photoId}"]`);
                if (targetCard) {
                    targetCard.classList.remove('buttons-active');
                }
            }
        }
        
        if (this.autoHideTimer) {
            clearTimeout(this.autoHideTimer);
            this.autoHideTimer = null;
        }
    },
    
    /**
     * 隐藏所有按钮
     */
    hideAllButtons() {
        if (this.activePhotoId) {
            const card = document.querySelector(`[data-photo-id="${this.activePhotoId}"]`);
            this.hideButtons(this.activePhotoId, card);
        }
    },
    
    /**
     * 设置自动隐藏
     * @param {string} photoId - 照片ID
     * @param {HTMLElement} card - 照片卡片元素
     */
    setAutoHide(photoId, card) {
        this.autoHideTimer = setTimeout(() => {
            if (this.activePhotoId === photoId) {
                this.hideButtons(photoId, card);
            }
        }, 3000); // 3秒后自动隐藏
    },
    
    /**
     * 执行按钮动作
     * @param {string} action - 动作类型
     * @param {string} photoId - 照片ID
     */
    executeButtonAction(action, photoId) {
        const photoIdNum = parseInt(photoId);
        
        switch (action) {
            case 'view':
                if (window.viewPhotoDetail) {
                    window.viewPhotoDetail(photoIdNum);
                }
                break;
            case 'edit':
                if (window.editPhoto) {
                    window.editPhoto(photoIdNum);
                }
                break;
            case 'delete':
                if (window.deletePhoto) {
                    window.deletePhoto(photoIdNum);
                }
                break;
            case 'similar':
                if (window.searchSimilarPhotos) {
                    window.searchSimilarPhotos(photoIdNum);
                }
                break;
            default:
                // 未知的按钮动作
        }
    }
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    PhotoInteractionManager.init();
});

// 导出供其他模块使用
window.HybridInputManager = HybridInputManager;
window.PhotoInteractionManager = PhotoInteractionManager;
