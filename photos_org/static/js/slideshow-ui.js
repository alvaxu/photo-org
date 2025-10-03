/**
 * 家庭版智能照片系统 - 幻灯片播放器UI模块
 *
 * 功能：
 * 1. SlideshowUI类 - 界面渲染和管理
 * 2. 全屏播放器界面管理
 * 3. 控制面板交互
 * 4. 键盘事件处理
 */

/**
 * 幻灯片播放器UI管理类
 */
class SlideshowUI {
    constructor(player, dataManager) {
        this.player = player;
        this.dataManager = dataManager;
        this.modal = null;
        this.controlsVisible = true;
        this.controlsHideTimer = null;

        // 绑定事件
        this.bindPlayerEvents();

        // 初始化UI
        this.init();
    }

    // 初始化UI
    init() {
        this.createModal();
        this.bindEvents();
        this.bindKeyboardEvents();
    }

    // 创建播放器模态框
    createModal() {
        const modalHtml = `
            <div class="modal slideshow-modal" id="slideshowModal" tabindex="-1" role="dialog" aria-modal="true" aria-labelledby="slideshowTitle" aria-describedby="slideshowMeta">
                <div class="modal-dialog modal-fullscreen">
                    <div class="modal-content slideshow-content">
                        <!-- 照片显示区域 -->
                        <div class="slideshow-display" role="img" aria-live="polite" aria-atomic="true">
                            <img id="slideshowImage" src="" alt="" class="slideshow-image" aria-hidden="true">
                            <!-- 照片信息 -->
                            <div id="slideshowInfo" class="slideshow-info" aria-live="polite">
                                <h5 id="slideshowTitle" class="slideshow-title"></h5>
                                <p id="slideshowMeta" class="slideshow-meta"></p>
                            </div>
                        </div>

                        <!-- 控制面板 -->
                        <div id="slideshowControls" class="slideshow-controls" role="toolbar" aria-label="幻灯片播放控制">
                            <!-- 播放控制按钮 -->
                            <div class="control-buttons">
                                <button class="btn btn-light btn-lg" id="slideshowPrev" title="上一张" aria-label="播放上一张照片" aria-describedby="slideshowProgress">
                                    <i class="bi bi-chevron-left" aria-hidden="true"></i>
                                </button>
                                <button class="btn btn-light btn-lg" id="slideshowPlayPause" title="播放/暂停" aria-label="播放或暂停幻灯片" aria-pressed="false">
                                    <i class="bi bi-play-fill" aria-hidden="true"></i>
                                </button>
                                <button class="btn btn-light btn-lg" id="slideshowNext" title="下一张" aria-label="播放下一张照片" aria-describedby="slideshowProgress">
                                    <i class="bi bi-chevron-right" aria-hidden="true"></i>
                                </button>
                            </div>

                            <!-- 播放信息 -->
                            <div class="play-info">
                                <span id="slideshowProgress" aria-live="polite" aria-atomic="true">1 / 10</span>
                            </div>

                            <!-- 设置面板 -->
                            <div class="settings-panel">
                                <div class="speed-control">
                                    <label>播放速度:</label>
                                    <select id="slideshowSpeed">
                                        <option value="5000">慢速 (5秒)</option>
                                        <option value="3000" selected>中速 (3秒)</option>
                                        <option value="1500">快速 (1.5秒)</option>
                                    </select>
                                </div>
                                <div class="loop-control">
                                    <label>
                                        <input type="checkbox" id="slideshowLoop"> 循环播放
                                    </label>
                                </div>
                                <div class="info-control">
                                    <label>
                                        <input type="checkbox" id="slideshowShowInfo" checked> 显示信息
                                    </label>
                                </div>
                            </div>

                            <!-- 退出按钮 -->
                            <button class="btn btn-outline-light" id="slideshowExit" title="退出播放">
                                <i class="bi bi-x-lg"></i> 退出
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // 添加到页面
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // 获取DOM元素
        this.modal = document.getElementById('slideshowModal');
        this.imageElement = document.getElementById('slideshowImage');
        this.titleElement = document.getElementById('slideshowTitle');
        this.metaElement = document.getElementById('slideshowMeta');
        this.progressElement = document.getElementById('slideshowProgress');
        this.controlsElement = document.getElementById('slideshowControls');

        // 初始化控制面板显示
        this.showControls();
    }

    // 显示播放器
    show() {
        if (this.modal) {
            const modal = new bootstrap.Modal(this.modal, {
                backdrop: 'static',
                keyboard: false
            });
            modal.show();

            // 更新显示
            this.updateDisplay();
        }
    }

    // 隐藏播放器
    hide() {
        if (this.modal) {
            const modalInstance = bootstrap.Modal.getInstance(this.modal);
            if (modalInstance) {
                modalInstance.hide();
            }
        }
    }

    // 更新显示内容
    updateDisplay() {
        try {
            const info = this.player.getPlaybackInfo();
            const photo = info.currentPhoto;

            if (!photo) {
                console.warn('当前没有照片数据，尝试恢复播放状态');

                // 如果播放列表不为空但索引异常，尝试修正索引
                if (info.totalCount > 0) {
                    console.log(`播放列表有 ${info.totalCount} 张照片，尝试修正索引`);
                    // 直接修正索引，避免递归调用
                    const validIndex = Math.max(0, Math.min(info.currentIndex, info.totalCount - 1));
                    this.player.currentIndex = validIndex;
                    console.log(`索引已修正为: ${validIndex}`);

                    // 重新尝试获取照片
                    const correctedInfo = this.player.getPlaybackInfo();
                    const correctedPhoto = correctedInfo.currentPhoto;

                    if (correctedPhoto) {
                        console.log('索引修正成功，继续显示照片');
                        // 递归调用但传入修正后的信息
                        setTimeout(() => this.updateDisplay(), 0);
                        return;
                    }
                }

                // 如果播放列表确实为空，显示错误
                this.showErrorState('没有可播放的照片');
                return;
            }

            // 更新图片 - 总是优先尝试原图，确保最佳质量
            this.imageElement.src = this.dataManager.getPhotoUrl(photo);
            this.imageElement.alt = photo.filename || '照片';
            this.imageElement.classList.add('active');

            // 监听加载状态
            this.imageElement.onload = () => {
                this.imageElement.classList.add('active');
                console.log('照片显示成功:', photo.filename);
            };

            this.imageElement.onerror = () => {
                console.warn('原图加载失败，尝试使用缩略图:', photo.filename);

                // 如果原图加载失败，尝试使用缩略图
                if (photo.thumbnail_path && photo.original_path !== photo.thumbnail_path) {
                    this.imageElement.src = `/photos_storage/${photo.thumbnail_path.replace(/\\/g, '/')}`;
                    console.log('回退到缩略图:', photo.filename);

                    // 重新设置错误处理
                    this.imageElement.onerror = () => {
                        console.error('缩略图也加载失败:', photo.filename);
                        this.handleImageError(photo);
                    };
                } else {
                    // 没有缩略图，直接显示错误
                    this.handleImageError(photo);
                }
            };

            // 更新照片信息
            this.titleElement.textContent = photo.filename || '未命名照片';

            const metaInfo = [];
        if (photo.created_at) {
            const date = new Date(photo.created_at);
            metaInfo.push(`拍摄时间: ${date.toLocaleString()}`);
        }
        if (photo.width && photo.height) {
            metaInfo.push(`尺寸: ${photo.width} × ${photo.height}`);
        }
        if (photo.file_size) {
            const size = this.formatFileSize(photo.file_size);
            metaInfo.push(`大小: ${size}`);
        }

        this.metaElement.textContent = metaInfo.join(' | ');

        // 更新播放进度
        this.progressElement.textContent = `${info.currentIndex + 1} / ${info.totalCount}`;

        // 更新播放/暂停按钮
        const playPauseBtn = document.getElementById('slideshowPlayPause');
        const icon = playPauseBtn.querySelector('i');
        if (info.isPlaying) {
            icon.className = 'bi bi-pause-fill';
            playPauseBtn.title = '暂停';
            playPauseBtn.setAttribute('aria-label', '暂停幻灯片播放');
            playPauseBtn.setAttribute('aria-pressed', 'true');
        } else {
            icon.className = 'bi bi-play-fill';
            playPauseBtn.title = '播放';
            playPauseBtn.setAttribute('aria-label', '开始幻灯片播放');
            playPauseBtn.setAttribute('aria-pressed', 'false');
        }

        // 更新循环播放复选框
        const loopCheckbox = document.getElementById('slideshowLoop');
        loopCheckbox.checked = info.loop;

        // 更新显示信息复选框
        const infoCheckbox = document.getElementById('slideshowShowInfo');
        infoCheckbox.checked = info.showInfo;

        // 控制信息显示区域的可见性
        const infoElement = document.getElementById('slideshowInfo');
        if (infoElement) {
            if (info.showInfo) {
                infoElement.classList.remove('hidden');
            } else {
                infoElement.classList.add('hidden');
            }
        }

        // 触发预加载
        this.dataManager.preloadAround(info.currentIndex, this.player.playlist);

        } catch (error) {
            console.error('更新播放器显示失败:', error);
            this.showErrorState('播放器显示错误，请重试');
        }
    }

    // 显示控制面板
    showControls() {
        if (this.controlsElement) {
            this.controlsElement.style.opacity = '1';
            this.controlsVisible = true;

            // 设置自动隐藏定时器
            this.resetControlsHideTimer();
        }
    }

    // 隐藏控制面板
    hideControls() {
        if (this.controlsElement && this.controlsVisible) {
            this.controlsElement.style.opacity = '0';
            this.controlsVisible = false;

            // 清除定时器
            if (this.controlsHideTimer) {
                clearTimeout(this.controlsHideTimer);
                this.controlsHideTimer = null;
            }
        }
    }

    // 重置控制面板隐藏定时器
    resetControlsHideTimer() {
        if (this.controlsHideTimer) {
            clearTimeout(this.controlsHideTimer);
        }

        this.controlsHideTimer = setTimeout(() => {
            // 只有在播放状态下才自动隐藏
            if (this.player.isPlaying) {
                this.hideControls();
            }
        }, 3000); // 3秒后自动隐藏
    }

    // 绑定播放器事件
    bindPlayerEvents() {
        this.player.onPhotoChange = (info) => {
            this.updateDisplay();
        };

        this.player.onStateChange = (info) => {
            this.updateDisplay();
        };
    }

    // 绑定UI事件
    bindEvents() {
        // 播放/暂停按钮
        document.getElementById('slideshowPlayPause').addEventListener('click', () => {
            if (this.player.isPlaying) {
                this.player.pause();
            } else {
                this.player.play();
            }
        });

        // 上一张/下一张按钮
        document.getElementById('slideshowPrev').addEventListener('click', () => {
            this.player.previous();
        });

        document.getElementById('slideshowNext').addEventListener('click', () => {
            this.player.next();
        });

        // 播放速度选择
        document.getElementById('slideshowSpeed').addEventListener('change', (e) => {
            const interval = parseInt(e.target.value);
            this.player.setSpeed(interval);
        });

        // 循环播放复选框
        document.getElementById('slideshowLoop').addEventListener('change', (e) => {
            this.player.setLoop(e.target.checked);
        });

        // 显示信息复选框
        document.getElementById('slideshowShowInfo').addEventListener('change', (e) => {
            this.player.setShowInfo(e.target.checked);
        });

        // 退出按钮
        document.getElementById('slideshowExit').addEventListener('click', () => {
            this.hide();
        });

        // 点击照片区域显示/隐藏控制面板
        const displayArea = this.modal.querySelector('.slideshow-display');
        displayArea.addEventListener('click', () => {
            if (this.controlsVisible) {
                this.hideControls();
            } else {
                this.showControls();
            }
        });

        // 鼠标移动显示控制面板
        this.controlsElement.addEventListener('mouseenter', () => {
            if (this.controlsHideTimer) {
                clearTimeout(this.controlsHideTimer);
                this.controlsHideTimer = null;
            }
        });

        this.controlsElement.addEventListener('mouseleave', () => {
            this.resetControlsHideTimer();
        });
    }

    // 绑定键盘事件
    bindKeyboardEvents() {
        const handleKeydown = (e) => {
            // 只在播放器激活时响应快捷键
            if (!this.modal || !this.modal.classList.contains('show')) {
                return;
            }

            switch (e.key) {
                case ' ': // 空格键 - 播放/暂停
                    e.preventDefault();
                    if (this.player.isPlaying) {
                        this.player.pause();
                        this.announceToScreenReader('幻灯片播放已暂停');
                    } else {
                        this.player.play();
                        this.announceToScreenReader('幻灯片播放已开始');
                    }
                    break;

                case 'ArrowLeft': // 左箭头 - 上一张
                    e.preventDefault();
                    this.player.previous();
                    this.announceToScreenReader('切换到上一张照片');
                    break;

                case 'ArrowRight': // 右箭头 - 下一张
                    e.preventDefault();
                    this.player.next();
                    this.announceToScreenReader('切换到下一张照片');
                    break;

                case 'Escape': // ESC - 退出播放
                    e.preventDefault();
                    this.hide();
                    this.announceToScreenReader('退出幻灯片播放');
                    break;
            }
        };

        // 监听全局键盘事件
        document.addEventListener('keydown', handleKeydown);

        // 播放器关闭时移除事件监听器
        this.modal.addEventListener('hidden.bs.modal', () => {
            document.removeEventListener('keydown', handleKeydown);
            this.cleanup();
        });
    }

    // 屏幕阅读器语音提示
    announceToScreenReader(message) {
        // 创建临时元素用于屏幕阅读器提示
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'assertive');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'sr-only';
        announcement.textContent = message;

        document.body.appendChild(announcement);

        // 延迟移除元素
        setTimeout(() => {
            document.body.removeChild(announcement);
        }, 1000);
    }

    // 格式化文件大小
    formatFileSize(bytes) {
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

    // 处理图片加载错误
    handleImageError(photo) {
        // 使用简单的颜色背景作为错误状态
        this.imageElement.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjhmOWZhIi8+PHRleHQgeD0iNTAlIiB5PSI0NSUiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZpbGw9IiNkYzM1NDUiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxNCI+56eB5a2Q5Yqf5aSx5L2gPC90ZXh0Pjx0ZXh0IHg9IjUwJSIgeT0iNjUlIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmaWxsPSIjNmM3NTdkIiBmb250LWZhbWlseT0iQXJpYWwsIHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTIiPkltYWdlIExvYWQgRmFpbGVkPC90ZXh0Pjwvc3ZnPg==';
        this.imageElement.alt = '照片加载失败';
        this.imageElement.classList.add('active');

        // 更新照片信息显示错误
        this.titleElement.textContent = photo.filename || '未知文件';
        this.metaElement.textContent = '照片加载失败，3秒后自动播放下一张';

        console.log('显示错误占位图 for photo:', photo.filename);

        // 自动跳到下一张（延迟3秒）
        setTimeout(() => {
            if (this.player && this.player.isPlaying) {
                this.player.next();
            }
        }, 3000);
    }

    // 显示错误状态
    showErrorState(message) {
        // 隐藏正常内容
        this.imageElement.style.display = 'none';
        this.titleElement.style.display = 'none';
        this.metaElement.style.display = 'none';

        // 显示错误信息
        if (!this.errorElement) {
            this.errorElement = document.createElement('div');
            this.errorElement.className = 'slideshow-error';
            this.modal.querySelector('.slideshow-display').appendChild(this.errorElement);
        }

        this.errorElement.innerHTML = `
            <i class="bi bi-exclamation-triangle"></i>
            <h5>播放错误</h5>
            <p>${message}</p>
            <button class="btn btn-outline-light mt-3" onclick="window.location.reload()">
                刷新页面
            </button>
        `;
        this.errorElement.style.display = 'block';
    }

    // 隐藏错误状态
    hideErrorState() {
        if (this.errorElement) {
            this.errorElement.style.display = 'none';
        }

        this.imageElement.style.display = '';
        this.titleElement.style.display = '';
        this.metaElement.style.display = '';
    }

    // 清理资源
    cleanup() {
        if (this.controlsHideTimer) {
            clearTimeout(this.controlsHideTimer);
            this.controlsHideTimer = null;
        }

        // 清理图片缓存
        this.dataManager.clearCache();

        // 销毁播放器
        this.player.destroy();

        // 清理错误状态
        this.hideErrorState();
    }
}

// 全局函数：开始幻灯片播放
async function startSlideshowFromCurrent(currentPhotoId) {
    try {
        // 显示加载提示
        showLoading('正在准备播放列表...');

        // 生成播放列表
        let playlistData = await generateSlideshowPlaylist(currentPhotoId);

        // 如果播放列表为空，等待一下再重试一次（处理可能的时序问题）
        if (!playlistData || playlistData.photos.length === 0) {
            console.warn('播放列表为空，等待重试:', playlistData);
            await new Promise(resolve => setTimeout(resolve, 200));
            playlistData = await generateSlideshowPlaylist(currentPhotoId);
        }

        if (!playlistData || playlistData.photos.length === 0) {
            throw new Error('没有找到可播放的照片，请稍后重试');
        }

        // 创建播放器和数据管理器
        const dataManager = new SlideshowDataManager();
        const player = new SlideshowPlayer(dataManager);

        // 设置播放列表
        player.setPlaylist(playlistData.photos, playlistData.startIndex);

        // 创建UI
        const ui = new SlideshowUI(player, dataManager);

        // 显示播放器
        ui.show();

    } catch (error) {
        console.error('开始幻灯片播放失败:', error);
        showError(error.message || '启动播放失败，请稍后重试');
    } finally {
        hideLoading();
    }
}

// 全局函数：从选中照片开始播放
async function startSlideshowFromSelection() {
    try {
        // 使用PhotoManager的状态，确保与UI同步
        const selectedIds = window.PhotoManager ? window.PhotoManager.selectedPhotos : new Set();

        if (selectedIds.size === 0) {
            showWarning('请先选择要播放的照片');
            return;
        }

        showLoading('正在准备播放列表...');

        // 生成播放列表
        const playlistData = await generateSlideshowPlaylistFromSelection(selectedIds);

        if (!playlistData || playlistData.photos.length === 0) {
            throw new Error('没有找到可播放的照片');
        }

        // 创建播放器和数据管理器
        const dataManager = new SlideshowDataManager();
        const player = new SlideshowPlayer(dataManager);

        // 设置播放列表
        player.setPlaylist(playlistData.photos, 0);

        // 创建UI
        const ui = new SlideshowUI(player, dataManager);

        // 显示播放器
        ui.show();

    } catch (error) {
        console.error('批量播放失败:', error);
        showError(error.message || '启动播放失败，请稍后重试');
    } finally {
        hideLoading();
    }
}

// 开始播放全部照片（当前筛选条件下的所有照片）
async function startSlideshowFromAll() {
    try {
        // 显示加载提示
        showLoading('正在准备播放列表...');

        // 生成播放列表 - 播放当前筛选条件下的所有照片
        let playlistData = await generateSlideshowPlaylistAll();

        // 如果播放列表为空，等待一下再重试一次（处理可能的时序问题）
        if (!playlistData || playlistData.photos.length === 0) {
            console.warn('播放列表为空，等待重试:', playlistData);
            await new Promise(resolve => setTimeout(resolve, 200));
            playlistData = await generateSlideshowPlaylistAll();
        }

        if (!playlistData || playlistData.photos.length === 0) {
            console.warn('播放列表仍为空:', playlistData);
            throw new Error('当前筛选条件下没有找到可播放的照片，请稍后重试或调整筛选条件');
        }

        // 创建播放器和数据管理器
        const dataManager = new SlideshowDataManager();
        const player = new SlideshowPlayer(dataManager);

        // 设置播放列表
        player.setPlaylist(playlistData.photos, 0);

        // 创建UI
        const ui = new SlideshowUI(player, dataManager);

        // 显示播放器
        ui.show();

    } catch (error) {
        console.error('播放全部照片失败:', error);
        showError(error.message || '启动播放失败，请稍后重试');
    } finally {
        hideLoading();
    }
}

// 导出UI类和函数
window.SlideshowUI = SlideshowUI;
window.startSlideshowFromCurrent = startSlideshowFromCurrent;
window.startSlideshowFromSelection = startSlideshowFromSelection;
window.startSlideshowFromAll = startSlideshowFromAll;
