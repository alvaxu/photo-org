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
        this.isLoadingImage = false;     // 新增：当前是否正在加载图片
        this.pendingPhotoIndex = -1;     // 新增：等待加载的照片索引
        this.consecutiveFailures = 0;    // 新增：连续失败计数
        this.maxConsecutiveFailures = 3; // 新增：最大连续失败次数
        this.isRecoveringFromError = false; // 新增：是否正在错误恢复中
        this.heicSupported = null;       // 新增：浏览器是否支持HEIC
        this.heicLoadTimeout = 30000;    // 新增：HEIC加载超时时间（30秒）

        // 检测HEIC支持
        this.detectHeicSupport();

        // 绑定事件
        this.bindPlayerEvents();

        // 初始化UI
        this.init();
    }

    // 检测浏览器HEIC支持
    async detectHeicSupport() {
        if (this.heicSupported !== null) {
            return this.heicSupported;
        }

        console.log('开始检测浏览器HEIC支持...');

        // 方法1: 使用Canvas API测试（最可靠）
        try {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');

            // 创建一个小的测试HEIC图片
            const img = new Image();
            const testPromise = new Promise((resolve, reject) => {
                img.onload = () => {
                    try {
                        // 尝试在canvas上绘制HEIC图片
                        canvas.width = img.naturalWidth;
                        canvas.height = img.naturalHeight;
                        ctx.drawImage(img, 0, 0);

                        // 如果能成功绘制，说明浏览器支持HEIC
                        const imageData = ctx.getImageData(0, 0, 1, 1);
                        if (imageData.data[3] > 0) { // 检查alpha通道
                            this.heicSupported = true;
                            console.log('✅ 浏览器支持HEIC格式（Canvas测试成功）');
                            resolve(true);
                        } else {
                            throw new Error('Canvas绘制失败');
                        }
                    } catch (e) {
                        reject(e);
                    }
                };

                img.onerror = () => reject(new Error('HEIC图片加载失败'));
                img.src = '/static/images/heic-test.heic';
            });

            // 设置超时
            const timeoutPromise = new Promise((_, reject) => {
                setTimeout(() => reject(new Error('HEIC检测超时')), 10000);
            });

            await Promise.race([testPromise, timeoutPromise]);
            return this.heicSupported;

        } catch (e) {
            console.log('❌ Canvas测试失败:', e.message);
        }

        // 方法2: 检查MIME类型支持
        try {
            // 现代浏览器支持检查
            if ('supported' in navigator && navigator.supported) {
                // 一些浏览器可能暴露支持信息
            }

            // 检查是否为Safari（通常支持HEIC）
            const isSafari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent);
            if (isSafari) {
                this.heicSupported = true;
                console.log('✅ 检测到Safari浏览器，默认支持HEIC');
                return true;
            }
        } catch (e) {
            console.log('MIME类型检查失败:', e.message);
        }

        // 方法3: 简单图片加载测试
        try {
            const testResult = await this.testHeicLoading('/static/images/heic-test.heic');
            this.heicSupported = testResult;
            console.log(`📊 简单加载测试结果: ${testResult ? '支持' : '不支持'}`);
            return testResult;
        } catch (e) {
            console.warn('所有HEIC检测方法失败，默认不支持');
            this.heicSupported = false;
            return false;
        }
    }

    // 测试HEIC图片加载
    testHeicLoading(url) {
        return new Promise((resolve) => {
            const img = new Image();
            const timeout = setTimeout(() => {
                img.src = '';
                resolve(false);
            }, 5000); // 5秒超时

            img.onload = () => {
                clearTimeout(timeout);
                // 检查图片是否真的加载成功（不是错误占位符）
                resolve(img.naturalWidth > 1 && img.naturalHeight > 1);
            };

            img.onerror = () => {
                clearTimeout(timeout);
                resolve(false);
            };

            img.src = url;
        });
    }

    // 初始化UI
    init() {
        this.createModal();
        this.bindEvents();
        this.bindKeyboardEvents();
    }

    // 创建播放器模态框
    createModal() {
        // 如果已存在模态框，先移除
        const existingModal = document.getElementById('slideshowModal');
        if (existingModal) {
            existingModal.remove();
        }

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
            // 检查连续失败次数，防止无限重试
            if (this.consecutiveFailures >= this.maxConsecutiveFailures) {
                console.warn(`连续失败 ${this.consecutiveFailures} 次，停止播放以保护系统`);
                this.showErrorState('图片加载连续失败，请检查网络连接或图片文件', false);
                this.player.stopTimer(); // 彻底停止播放
                return;
            }

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

            // 如果正在加载图片，记录待显示的照片索引，等待加载完成
            if (this.isLoadingImage) {
                console.log('图片正在加载中，记录待显示照片:', info.currentIndex);
                this.pendingPhotoIndex = info.currentIndex;
                return;
            }

            // 标记开始加载
            this.isLoadingImage = true;


            // 更新图片 - 根据格式和浏览器支持情况调整策略
            const isHeicFormat = photo.filename.toLowerCase().endsWith('.heic') || photo.filename.toLowerCase().endsWith('.heif');

            // 设置加载超时时间
            let loadTimeout;
            if (isHeicFormat && this.heicSupported) {
                // HEIC格式且浏览器支持：给予更长的时间，并暂停定时器等待加载
                loadTimeout = this.heicLoadTimeout; // 30秒
                console.log(`HEIC原图加载中，给予 ${loadTimeout/1000} 秒超时时间，暂停自动切换:`, photo.filename);

                // 暂停播放定时器，等待HEIC加载完成
                if (this.player && this.player.timer) {
                    console.log('暂停播放定时器，等待HEIC加载完成');
                    this.player.stopTimer();
                }
            } else {
                // 普通格式或不支持HEIC：使用标准超时
                loadTimeout = 15000; // 15秒
                console.log(`图片加载中，使用 ${loadTimeout/1000} 秒超时时间:`, photo.filename);
            }

            this.imageElement.src = this.dataManager.getPhotoUrl(photo);
            this.imageElement.alt = photo.filename || '照片';
            this.imageElement.classList.add('active');

            // 设置显示图片的超时
            let displayTimeoutId = setTimeout(() => {
                console.log(`图片加载超时 (${loadTimeout/1000}秒)，强制处理:`, photo.filename);
                this.isLoadingImage = false; // 清除加载状态
                this.handleImageError(photo); // 调用错误处理
            }, loadTimeout);

            // 通用图片加载成功处理函数
            const handleImageLoadSuccess = () => {
                clearTimeout(displayTimeoutId);
                this.imageElement.classList.add('active');

                // 检查是否为HEIC格式且浏览器支持
                const isHeicFormat = photo.filename.toLowerCase().endsWith('.heic') || photo.filename.toLowerCase().endsWith('.heif');
                const isHeicSupported = this.heicSupported;

                if (isHeicFormat && isHeicSupported) {
                    console.log('HEIC原图加载成功:', photo.filename);
                } else {
                    console.log('照片显示成功:', photo.filename);
                }

                // 加载完成，清除加载状态
                this.isLoadingImage = false;

                // 重置连续失败计数
                this.consecutiveFailures = 0;

                // 确保预加载已恢复（以防被意外暂停）
                this.dataManager.resumePreloading();

                // 如果有待显示的照片，立即切换
                if (this.pendingPhotoIndex !== -1) {
                    const currentIndex = this.player.currentIndex;
                    if (this.pendingPhotoIndex !== currentIndex) {
                        console.log('加载完成，切换到待显示照片:', this.pendingPhotoIndex);
                        this.player.goToPhoto(this.pendingPhotoIndex);
                    }
                    this.pendingPhotoIndex = -1;
                }

                // 对于HEIC格式且浏览器支持的情况，加载完成后立即开始下一张的倒计时
                if (isHeicFormat && isHeicSupported && this.player && this.player.isPlaying) {
                    if (!this.player.timer) {
                        console.log('HEIC加载完成，启动播放定时器');
                        // 重新启动定时器，从现在开始计算interval
                        this.player.startTimer();
                    } else {
                        console.log('HEIC加载完成，定时器已在运行中');
                    }
                }
            };

            // 监听加载状态
            this.imageElement.onload = handleImageLoadSuccess;

            this.imageElement.onerror = () => {
                clearTimeout(displayTimeoutId);
                console.warn('原图加载失败:', photo.filename);

                // 延迟一小段时间再尝试缩略图，避免立即取消请求导致ConnectionResetError
                setTimeout(() => {
                    // 如果原图加载失败，尝试使用缩略图
                    if (photo.thumbnail_path && photo.original_path !== photo.thumbnail_path) {
                        console.log('尝试回退到缩略图:', photo.filename);
                        this.imageElement.src = `/photos_storage/${photo.thumbnail_path.replace(/\\/g, '/')}`;

                        // 为缩略图设置超时
                        let thumbnailTimeoutId = setTimeout(() => {
                            console.log('缩略图显示超时，强制处理:', photo.filename);
                            this.isLoadingImage = false;
                            this.handleImageError(photo);
                        }, 10000);

                        // 重新设置加载处理
                        this.imageElement.onload = () => {
                            clearTimeout(thumbnailTimeoutId);
                            handleImageLoadSuccess();
                        };

                        this.imageElement.onerror = () => {
                            clearTimeout(thumbnailTimeoutId);
                            console.error('缩略图也加载失败:', photo.filename);
                            this.handleImageError(photo);
                        };
                    } else {
                        // 没有缩略图，直接显示错误
                        console.log('无缩略图可用，直接显示错误:', photo.filename);
                        this.handleImageError(photo);
                    }
                }, 100); // 短暂延迟，避免ConnectionResetError
            };

            // 更新照片信息
            this.titleElement.textContent = photo.filename || '未命名照片';

            const metaInfo = [];
        if (photo.taken_at) {
            const date = new Date(photo.taken_at);
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
            // 出错时也要清除加载状态
            this.isLoadingImage = false;
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
            // 确保清理状态
            setTimeout(() => this.cleanup(), 100);
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

        // 存储键盘事件处理器引用，用于后续清理
        this.keyboardHandler = handleKeydown;

        // 播放器关闭时移除事件监听器
        this.modal.addEventListener('hidden.bs.modal', () => {
            document.removeEventListener('keydown', this.keyboardHandler);
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
        console.warn('图片加载失败:', photo.filename, '连续失败次数:', this.consecutiveFailures + 1);

        // 增加连续失败计数
        this.consecutiveFailures++;

        // 使用简单的颜色背景作为错误状态
        this.imageElement.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjhmOWZhIi8+PHRleHQgeD0iNTAlIiB5PSI0NSUiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZpbGw9IiNkYzM1NDUiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxNCI+56eB5a2Q5Yqf5aSx5L2gPC90ZXh0Pjx0ZXh0IHg9IjUwJSIgeT0iNjUlIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmaWxsPSIjNmM3NTdkIiBmb250LWZhbWlseT0iQXJpYWwsIHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTIiPkltYWdlIExvYWQgRmFpbGVkPC90ZXh0Pjwvc3ZnPg==';
        this.imageElement.alt = '照片加载失败';
        this.imageElement.classList.add('active');

        // 更新照片信息显示错误
        this.titleElement.textContent = photo.filename || '未知文件';
        this.metaElement.textContent = '照片加载失败，3秒后自动播放下一张';

        console.log('显示错误占位图 for photo:', photo.filename);

        // 加载失败也要清除加载状态
        this.isLoadingImage = false;

        // 暂停定时器，防止竞态条件
        this.player.stopTimer();

        // 暂停预加载，防止并发HTTP请求
        this.dataManager.pausePreloading();

        // 设置错误恢复标志
        this.isRecoveringFromError = true;

        // 延迟重试，重新启动定时器
        setTimeout(() => {
            this.isRecoveringFromError = false; // 清除恢复标志
            if (this.player && this.player.isPlaying) {
                // 恢复预加载
                this.dataManager.resumePreloading();
                // 重新启动定时器
                this.player.startTimer();
                // 切换到下一张
                this.player.next();
            }
        }, 3000);
    }

    // 显示错误状态
    showErrorState(message, isFatal = true) {
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

        if (isFatal) {
            // 严重错误：显示刷新按钮
            this.errorElement.innerHTML = `
                <i class="bi bi-exclamation-triangle"></i>
                <h5>播放错误</h5>
                <p>${message}</p>
                <button class="btn btn-outline-light mt-3" onclick="window.location.reload()">
                    刷新页面
                </button>
            `;
        } else {
            // 临时错误：显示等待信息
            this.errorElement.innerHTML = `
                <i class="bi bi-clock"></i>
                <h5>加载中...</h5>
                <p>${message}</p>
                <small>正在尝试恢复播放...</small>
            `;
        }
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

        // 移除键盘事件监听器
        if (this.keyboardHandler) {
            document.removeEventListener('keydown', this.keyboardHandler);
            this.keyboardHandler = null;
        }

        // 清理图片缓存
        this.dataManager.clearCache();

        // 销毁播放器
        this.player.destroy();

        // 清理错误状态
        this.hideErrorState();

        // 移除模态框DOM元素
        if (this.modal && this.modal.parentNode) {
            this.modal.parentNode.removeChild(this.modal);
        }

        // 清理公告元素
        if (this.announcementElement && this.announcementElement.parentNode) {
            this.announcementElement.parentNode.removeChild(this.announcementElement);
        }

        // 清理加载状态
        this.isLoadingImage = false;
        this.pendingPhotoIndex = -1;
        this.consecutiveFailures = 0;
        this.isRecoveringFromError = false;

        // 清理属性引用
        this.modal = null;
        this.controlsVisible = true;
        this.imageElement = null;
        this.titleElement = null;
        this.metaElement = null;
        this.progressElement = null;
        this.errorElement = null;
        this.announcementElement = null;

        // 清理全局实例引用
        if (currentSlideshowInstance === this) {
            currentSlideshowInstance = null;
        }
    }
}

// 全局播放状态管理 - 防止同时运行多个播放实例
let currentSlideshowInstance = null;

// 全局函数：开始幻灯片播放
async function startSlideshowFromCurrent(currentPhotoId) {
    try {
        // 如果已有播放实例在运行，先清理
        if (currentSlideshowInstance) {
            console.log('检测到已有播放实例，正在清理...');
            try {
                currentSlideshowInstance.cleanup();
            } catch (e) {
                console.warn('清理旧播放实例时出错:', e);
            }
            currentSlideshowInstance = null;
        }

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

        // 设置player的UI引用，用于加载状态检查
        player.ui = ui;

        // 设置全局播放实例引用
        currentSlideshowInstance = ui;

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
        // 如果已有播放实例在运行，先清理
        if (currentSlideshowInstance) {
            console.log('检测到已有播放实例，正在清理...');
            try {
                currentSlideshowInstance.cleanup();
            } catch (e) {
                console.warn('清理旧播放实例时出错:', e);
            }
            currentSlideshowInstance = null;
        }

        // 显示加载提示
        showLoading('正在准备播放列表...');

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

        // 设置player的UI引用，用于加载状态检查
        player.ui = ui;

        // 设置全局播放实例引用
        currentSlideshowInstance = ui;

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
        // 如果已有播放实例在运行，先清理
        if (currentSlideshowInstance) {
            console.log('检测到已有播放实例，正在清理...');
            try {
                currentSlideshowInstance.cleanup();
            } catch (e) {
                console.warn('清理旧播放实例时出错:', e);
            }
            currentSlideshowInstance = null;
        }

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

        // 设置player的UI引用，用于加载状态检查
        player.ui = ui;

        // 设置全局播放实例引用
        currentSlideshowInstance = ui;

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

