/**
 * 家庭版智能照片系统 - 幻灯片播放器核心模块
 *
 * 功能：
 * 1. SlideshowPlayer核心类 - 播放控制和状态管理
 * 2. SlideshowDataManager类 - 智能预加载和缓存管理
 * 3. SlideshowUI类 - 界面渲染和管理
 * 4. 播放列表生成和管理
 */

/**
 * 幻灯片播放器核心类
 */
class SlideshowPlayer {
    constructor(dataManager, options = {}) {
        this.dataManager = dataManager; // 数据管理器
        this.playlist = [];           // 播放列表
        this.currentIndex = 0;        // 当前播放索引
        this.isPlaying = false;       // 播放状态
        this.interval = 3000;         // 播放间隔(ms)
        this.timer = null;            // 播放定时器
        this.mode = 'auto';           // 播放模式: auto, manual
        this.loop = false;            // 是否循环播放
        this.showInfo = true;         // 是否显示照片信息
        this.ui = null;               // 新增：UI实例引用，用于检查加载状态
        this.onStateChange = null;    // 状态变更回调
        this.onPhotoChange = null;    // 照片切换回调

        // 初始化选项
        Object.assign(this, options);
    }

    // 播放列表管理
    setPlaylist(photos, startIndex = 0) {
        this.playlist = [...photos];
        this.currentIndex = Math.max(0, Math.min(startIndex, photos.length - 1));
        this.notifyStateChange();
    }

    // 播放控制
    play() {
        if (this.isPlaying) return;
        this.isPlaying = true;
        this.startTimer();
        this.notifyStateChange();
    }

    pause() {
        if (!this.isPlaying) return;
        this.isPlaying = false;
        this.stopTimer();
        this.notifyStateChange();
    }

    next() {
        this.goToPhoto(this.currentIndex + 1);
    }

    previous() {
        this.goToPhoto(this.currentIndex - 1);
    }

    goToPhoto(index) {
        // 如果播放列表为空，直接返回
        if (!this.playlist || this.playlist.length === 0) {
            console.warn('播放列表为空，无法切换照片');
            return;
        }

        if (index < 0) {
            index = this.loop ? this.playlist.length - 1 : 0;
        } else if (index >= this.playlist.length) {
            index = this.loop ? 0 : this.playlist.length - 1;
        }

        // 额外检查：确保索引在有效范围内
        if (index < 0) index = 0;
        if (index >= this.playlist.length) index = this.playlist.length - 1;

        if (index !== this.currentIndex) {
            this.currentIndex = index;

            // 切换照片时更新预加载
            this.dataManager.preloadAround(this.currentIndex, this.playlist);

            this.notifyPhotoChange();
        }
    }

    // 播放速度控制
    setSpeed(interval) {
        this.interval = interval;
        if (this.isPlaying) {
            this.restartTimer();
        }
    }

    // 播放模式控制
    setLoop(enabled) {
        this.loop = enabled;

        // 如果启用循环播放，确保当前索引有效
        if (enabled && this.playlist && this.playlist.length > 0) {
            if (this.currentIndex < 0) {
                this.currentIndex = 0;
            } else if (this.currentIndex >= this.playlist.length) {
                this.currentIndex = this.playlist.length - 1;
            }
        }

        this.notifyStateChange();
    }

    // 信息显示控制
    setShowInfo(enabled) {
        this.showInfo = enabled;
        this.notifyStateChange();
    }

    // 获取当前照片
    getCurrentPhoto() {
        if (!this.playlist || this.playlist.length === 0) {
            return null;
        }

        if (this.currentIndex < 0 || this.currentIndex >= this.playlist.length) {
            console.warn(`照片索引超出范围: ${this.currentIndex}, 播放列表长度: ${this.playlist.length}`);
            return null;
        }

        return this.playlist[this.currentIndex] || null;
    }

    // 获取播放信息
    getPlaybackInfo() {
        return {
            currentIndex: this.currentIndex,
            totalCount: this.playlist.length,
            currentPhoto: this.getCurrentPhoto(),
            isPlaying: this.isPlaying,
            interval: this.interval,
            loop: this.loop,
            showInfo: this.showInfo
        };
    }

    // 私有方法
    startTimer() {
        this.stopTimer();

        // 对于HEIC且浏览器支持的情况，使用特殊处理
        if (this.ui && this.ui.heicSupported && this.currentIndex >= 0 && this.playlist[this.currentIndex]) {
            const currentPhoto = this.playlist[this.currentIndex];
            const isHeicFormat = currentPhoto.filename.toLowerCase().endsWith('.heic') ||
                               currentPhoto.filename.toLowerCase().endsWith('.heif');

            if (isHeicFormat) {
                console.log('检测到HEIC图片且浏览器支持，启动智能等待模式');

                // 检查是否已经在加载中
                if (this.ui.isLoadingImage) {
                    console.log('HEIC正在加载中，暂时不启动定时器，等待加载完成');
                    // 不启动定时器，等待UI加载完成后重新启动
                    return;
                } else {
                    // HEIC已经加载完成，启动正常定时器
                    console.log('HEIC已加载完成，启动正常播放定时器');
                }
            }
        }

        // 启动定时器
        this.timer = setInterval(() => {
            // 检查UI是否正在加载图片或错误恢复中，如果是则跳过本次切换
            if (this.ui && (this.ui.isLoadingImage || this.ui.isRecoveringFromError)) {
                // 图片加载中或错误恢复中，跳过本次自动切换
                return;
            }

            // 检查当前图片是否是HEIC且浏览器支持，如果正在加载则等待
            if (this.ui && this.ui.heicSupported && this.currentIndex >= 0 && this.playlist[this.currentIndex]) {
                const currentPhoto = this.playlist[this.currentIndex];
                const isHeicFormat = currentPhoto.filename.toLowerCase().endsWith('.heic') ||
                                   currentPhoto.filename.toLowerCase().endsWith('.heif');

                if (isHeicFormat && this.ui.isLoadingImage) {
                    // HEIC图片正在加载中，等待完成后再切换
                    console.log('HEIC图片仍在加载中，继续等待...');
                    return;
                }
            }

            this.next();
        }, this.interval);
    }

    stopTimer() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
    }

    restartTimer() {
        if (this.isPlaying) {
            this.startTimer();
        }
    }

    notifyStateChange() {
        if (this.onStateChange) {
            this.onStateChange(this.getPlaybackInfo());
        }
    }

    notifyPhotoChange() {
        if (this.onPhotoChange) {
            this.onPhotoChange(this.getPlaybackInfo());
        }
    }

    // 清理资源
    destroy() {
        this.stopTimer();
        this.playlist = [];
        this.currentIndex = 0;
        this.isPlaying = false;
        this.loop = false;
        this.showInfo = true;
        this.onStateChange = null;
        this.onPhotoChange = null;
        // 不清理dataManager引用，因为它可能被其他地方使用
    }
}

/**
 * 幻灯片数据管理器 - 智能预加载和缓存
 */
class SlideshowDataManager {
    constructor() {
        this.imageCache = new Map();    // 图片缓存：智能缓存
        this.metadataCache = new Map(); // 元数据缓存：所有照片元数据（内存占用小）
        this.preloadDistance = 1;       // 预加载距离：改为1，前后各一张，减少并发请求
        this.activeTimeouts = new Set(); // 新增：跟踪活跃的超时定时器
        this.preloadPaused = false;     // 新增：预加载暂停标志
    }

    // 智能预加载 - 只缓存当前及下一张照片
    preloadAround(currentIndex, playlist) {
        // 如果预加载已暂停，直接返回
        if (this.preloadPaused) {
            console.log('预加载已暂停，跳过预加载操作');
            return;
        }

        const indicesToCache = [
            currentIndex,                         // 当前（必须预加载）
            currentIndex + this.preloadDistance   // 下一张（用于流畅切换）
        ].filter(index => index >= 0 && index < playlist.length);

        // 清理不在预加载范围内的缓存
        const indicesSet = new Set(indicesToCache);
        for (const [index, img] of this.imageCache) {
            if (!indicesSet.has(parseInt(index))) {
                // 清理DOM引用，释放内存
                img.removeAttribute('src');
                img.src = '';
                this.imageCache.delete(index);
            }
        }

        // 预加载需要的新照片
        indicesToCache.forEach(index => {
            if (!this.imageCache.has(index)) {
                const photo = playlist[index];
                this.preloadPhoto(index, photo);
            }
        });
    }

    // 预加载单张照片
    preloadPhoto(index, photo) {
        const img = new Image();
        let timeoutId;

        // 设置10秒超时，防止无限等待
        timeoutId = setTimeout(() => {
            // 图片预加载超时，清理资源
            img.src = '';  // 取消加载
            this.imageCache.delete(index);
            // 释放内存
            img.removeAttribute('src');
            img.onload = null;
            img.onerror = null;
            this.activeTimeouts.delete(timeoutId);
        }, 10000);

        // 记录超时ID
        this.activeTimeouts.add(timeoutId);

        img.onload = () => {
            clearTimeout(timeoutId);
            this.activeTimeouts.delete(timeoutId);
            // 照片加载成功，加入缓存
            this.imageCache.set(index, img);
        };

        img.onerror = () => {
            clearTimeout(timeoutId);
            this.activeTimeouts.delete(timeoutId);

            // 原图加载失败，尝试加载缩略图
            if (photo.thumbnail_path && photo.original_path !== photo.thumbnail_path) {
                console.log('预加载原图失败，延迟尝试缩略图:', photo.filename);

                // 延迟创建缩略图请求，避免ConnectionResetError
                setTimeout(() => {
                    const thumbnailUrl = `/photos_storage/${photo.thumbnail_path.replace(/\\/g, '/')}`;

                    const retryImg = new Image();
                    let retryTimeoutId;

                    // 为缩略图也设置超时
                    retryTimeoutId = setTimeout(() => {
                        console.log('缩略图预加载超时:', photo.filename);
                        retryImg.src = '';
                        this.activeTimeouts.delete(retryTimeoutId);
                    }, 5000);

                    this.activeTimeouts.add(retryTimeoutId);

                    retryImg.onload = () => {
                        clearTimeout(retryTimeoutId);
                        this.activeTimeouts.delete(retryTimeoutId);
                        console.log('缩略图预加载成功:', photo.filename);
                        this.imageCache.set(index, retryImg);
                    };

                    retryImg.onerror = () => {
                        clearTimeout(retryTimeoutId);
                        this.activeTimeouts.delete(retryTimeoutId);
                        // 缩略图也失败，使用占位符并缓存
                        console.log('缩略图预加载也失败，使用占位符:', photo.filename);
                        const placeholder = new Image();
                        placeholder.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjE1MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjhmOWZhIi8+PGNpcmNsZSBjeD0iMTAwIiBjeT0iNjAiIHI9IjIwIiBmaWxsPSIjNmM3NTdkIiBvcGFjaXR5PSIwLjMiLz48dGV4dCB4PSIxMDAiIHk9IjkwIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmaWxsPSIjNmM3NTdkIiBmc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjhmOWZhIi8+PGNpcmNsZSBjeD0iMTAwIiBjeT0iNjAiIHI9IjIwIiBmaWxsPSIjNmM3NTdkIiBvcGFjaXR5PSIwLjMiLz48dGV4dCB4PSIxMDAiIHk9IjkwIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmaWxsPSIjNmM3NTdkIiBmb250LWZhbWlseT0iQXJpYWwsIHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTAiPkxvYWRpbmcuLi48L3RleHQ+PC9zdmc+';
                        this.imageCache.set(index, placeholder);
                    };

                    retryImg.src = thumbnailUrl;
                }, 200); // 200ms延迟，避免ConnectionResetError
            } else {
                // 没有缩略图，使用占位符并缓存
                console.log('原图预加载失败且无缩略图，使用占位符:', photo.filename);
                const placeholder = new Image();
                placeholder.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjE1MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjhmOWZhIi8+PGNpcmNsZSBjeD0iMTAwIiBjeT0iNjAiIHI9IjIwIiBmaWxsPSIjNmM3NTdkIiBvcGFjaXR5PSIwLjMiLz48dGV4dCB4PSIxMDAiIHk9IjkwIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmaWxsPSIjNmM3NTdkIiBmb250LWZhbWlseT0iQXJpYWwsIHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTAiPkxvYWRpbmcuLi48L3RleHQ+PC9zdmc+';
                this.imageCache.set(index, placeholder);
            }
        };

        img.src = this.getPhotoUrl(photo);
    }

    // 获取照片显示URL
    getPhotoUrl(photo) {
        // 根据浏览器HEIC支持情况和图片格式决定加载策略
        let url;
        const isHeicFormat = photo.filename.toLowerCase().endsWith('.heic') || photo.filename.toLowerCase().endsWith('.heif');

        if (photo.original_path) {
            // 对于HEIC格式，根据浏览器支持情况决定
            if (isHeicFormat) {
                // 检查UI实例是否已初始化并检测到HEIC支持
                const ui = this.getUI();
                if (ui && ui.heicSupported === false) {
                    // 浏览器不支持HEIC，直接使用缩略图
                    if (photo.thumbnail_path) {
                        url = `/photos_storage/${photo.thumbnail_path.replace(/\\/g, '/')}`;
                        console.log('浏览器不支持HEIC，使用缩略图:', photo.filename, '->', url);
                    } else {
                        url = '/static/images/qr-code-placeholder.jpg';
                        console.log('HEIC不支持且无缩略图，使用占位图:', photo.filename);
                    }
                } else {
                    // 浏览器支持HEIC或检测中，尝试原图
                    url = `/photos_storage/${photo.original_path.replace(/\\/g, '/')}`;
                    console.log('尝试HEIC原图:', photo.filename, '->', url);
                }
            } else {
                // 非HEIC格式，正常使用原图
                url = `/photos_storage/${photo.original_path.replace(/\\/g, '/')}`;
                console.log('使用原图:', photo.filename, '->', url);
            }
        } else if (photo.thumbnail_path) {
            url = `/photos_storage/${photo.thumbnail_path.replace(/\\/g, '/')}`;
            console.log('使用缩略图 (无原图):', photo.filename, '->', url);
        } else {
            url = '/static/images/qr-code-placeholder.jpg'; // 默认占位图
            console.log('使用默认占位图:', photo.filename);
        }

        return url;
    }

    // 获取UI实例引用
    getUI() {
        // 通过player获取UI实例
        return this.player && this.player.ui ? this.player.ui : null;
    }

    // 获取缓存的照片
    getCachedImage(index) {
        return this.imageCache.get(index);
    }

    // 检查照片是否已缓存
    isImageCached(index) {
        return this.imageCache.has(index);
    }

    // 清理所有缓存
    clearCache() {
        // 取消所有超时定时器
        for (const timeoutId of this.activeTimeouts) {
            clearTimeout(timeoutId);
        }
        this.activeTimeouts.clear();

        // 清理图片缓存
        for (const img of this.imageCache.values()) {
            img.removeAttribute('src');
            img.src = '';
            // 清理事件监听器
            img.onload = null;
            img.onerror = null;
        }
        this.imageCache.clear();
        this.metadataCache.clear();
    }

    // 暂停预加载
    pausePreloading() {
        console.log('暂停预加载');
        this.preloadPaused = true;
        // 取消所有活跃的超时定时器
        for (const timeoutId of this.activeTimeouts) {
            clearTimeout(timeoutId);
        }
        this.activeTimeouts.clear();

        // 清理所有正在预加载的图片，释放资源
        for (const img of this.imageCache.values()) {
            if (img && img.src) {
                // 中断正在进行的加载
                img.src = '';
                img.removeAttribute('src');
                img.onload = null;
                img.onerror = null;
            }
        }
        // 清空缓存，防止使用不完整的图片
        this.imageCache.clear();
        console.log('已清理预加载缓存，释放资源');
    }

    // 恢复预加载
    resumePreloading() {
        console.log('恢复预加载');
        this.preloadPaused = false;
    }

    // 获取缓存统计信息
    getCacheStats() {
        return {
            imageCacheSize: this.imageCache.size,
            metadataCacheSize: this.metadataCache.size,
            preloadPaused: this.preloadPaused
        };
    }
}

/**
 * 生成幻灯片播放列表
 * @param {number} currentPhotoId - 当前查看的照片ID
 * @returns {Promise<{photos: Array, startIndex: number, totalCount: number, hasMore: boolean}>}
 */
async function generateSlideshowPlaylist(currentPhotoId) {
    try {
        // 等待一小段时间，确保筛选状态稳定（避免快速切换筛选条件时的时序问题）
        await new Promise(resolve => setTimeout(resolve, 100));

        // 获取当前筛选条件
        const filters = AppState.searchFilters;

        // 构建API参数 - 获取符合条件的照片（API最大限制500）
        const params = new URLSearchParams({
            offset: 0,
            limit: 500,  // API最大限制为500
            sort_by: filters.sortBy,
            sort_order: filters.sortOrder,
            keyword: filters.keyword,
            search_type: filters.searchType,
            date_filter: filters.dateFilter,
            quality_filter: filters.qualityFilter
        });

        // 添加标签筛选参数
        if (filters.selectedTags.length > 0) {
            params.append('tag_ids', filters.selectedTags.join(','));
        }

        // 添加分类筛选参数
        if (filters.selectedCategories.length > 0) {
            params.append('category_ids', filters.selectedCategories.join(','));
        }

        // 添加自定义日期范围参数
        if (filters.dateFilter === 'custom') {
            if (window.elements?.startDate?.value) {
                params.append('start_date', window.elements.startDate.value);
            }
            if (window.elements?.endDate?.value) {
                params.append('end_date', window.elements.endDate.value);
            }
        }

        console.log('生成播放列表:', `${window.CONFIG.API_BASE_URL}/search/photos?${params}`);

        const response = await fetch(`${window.CONFIG.API_BASE_URL}/search/photos?${params}`);
        const data = await response.json();

        if (data.success) {
            const allPhotos = data.data || data.photos || [];
            const totalCount = data.total || 0;

            // 找到当前照片的索引
            const startIndex = allPhotos.findIndex(p => p.id === currentPhotoId);

            return {
                photos: allPhotos,
                startIndex: Math.max(0, startIndex),
                totalCount: totalCount,
                hasMore: allPhotos.length >= 200 && allPhotos.length < totalCount  // 如果返回了200张但总数更多，说明被截断
            };
        } else {
            throw new Error(data.message || '获取照片列表失败');
        }
    } catch (error) {
        console.error('生成播放列表失败:', error);
        throw error;
    }
}

/**
 * 生成全部照片播放列表（当前筛选条件下的所有照片）
 * @returns {Promise<{photos: Array, startIndex: number, totalCount: number, hasMore: boolean}>}
 */
async function generateSlideshowPlaylistAll() {
    try {
        // 等待一小段时间，确保筛选状态稳定（避免快速切换筛选条件时的时序问题）
        await new Promise(resolve => setTimeout(resolve, 100));

        // 获取当前筛选条件
        const filters = AppState.searchFilters;

        // 构建API参数 - 获取符合条件的照片（API最大限制1000）
        const params = new URLSearchParams({
            offset: 0,
            limit: 1000,  // API最大限制为1000
            sort_by: filters.sortBy,
            sort_order: filters.sortOrder,
            keyword: filters.keyword || '',
            search_type: filters.searchType || 'all',
            date_filter: filters.dateFilter || '',
            quality_filter: filters.qualityFilter || ''
        });

        // 添加筛选参数（与loadPhotos保持一致）
        if (filters.faceCountFilter) {
            params.append('face_count_filter', filters.faceCountFilter);
        }
        if (filters.formatFilter) {
            params.append('format_filter', filters.formatFilter);
        }
        if (filters.cameraFilter) {
            params.append('camera_filter', filters.cameraFilter);
        }
        if (filters.person_filter && filters.person_filter !== 'all') {
            params.append('person_filter', filters.person_filter);
        }

        // 添加标签筛选参数
        if (filters.selectedTags && filters.selectedTags.length > 0) {
            params.append('tag_ids', filters.selectedTags.join(','));
        }

        // 添加分类筛选参数
        if (filters.selectedCategories && filters.selectedCategories.length > 0) {
            params.append('category_ids', filters.selectedCategories.join(','));
        }

        // 添加收藏筛选参数
        if (filters.favorite_filter) {
            params.append('is_favorite', 'true');
        }

        // 添加自定义日期范围参数
        if (filters.dateFilter === 'custom') {
            if (window.elements?.startDate?.value) {
                params.append('start_date', window.elements.startDate.value);
            }
            if (window.elements?.endDate?.value) {
                params.append('end_date', window.elements.endDate.value);
            }
        }

        const response = await fetch(`${window.CONFIG.API_BASE_URL}/search/photos?${params}`);
        const data = await response.json();

        if (data.success) {
            const allPhotos = data.data || data.photos || [];
            const totalCount = data.total || 0;

            return {
                photos: allPhotos,
                startIndex: 0,  // 从第一张开始播放
                totalCount: totalCount,
                hasMore: allPhotos.length >= 200 && allPhotos.length < totalCount  // 如果返回了200张但总数更多，说明被截断
            };
        } else {
            throw new Error(data.message || '获取照片列表失败');
        }
    } catch (error) {
        console.error('生成全部照片播放列表失败:', error);
        throw error;
    }
}

/**
 * 从选中的照片生成播放列表
 * @param {Set<number>} selectedPhotoIds - 选中的照片ID集合
 * @returns {Promise<{photos: Array, startIndex: number}>}
 */
async function generateSlideshowPlaylistFromSelection(selectedPhotoIds) {
    try {
        // 将ID转换为照片对象
        const selectedIds = Array.from(selectedPhotoIds);

        // 批量获取照片详情
        const photoPromises = selectedIds.map(id =>
            fetch(`${window.CONFIG.API_BASE_URL}/search/photos/${id}`)
                .then(res => res.json())
                .then(data => data.success ? data.data : null)
        );

        const photos = await Promise.all(photoPromises);
        const validPhotos = photos.filter(p => p !== null);

        return {
            photos: validPhotos,
            startIndex: 0
        };
    } catch (error) {
        console.error('生成选中照片播放列表失败:', error);
        throw error;
    }
}

// 导出核心类和函数
window.SlideshowPlayer = SlideshowPlayer;
window.SlideshowDataManager = SlideshowDataManager;
window.generateSlideshowPlaylist = generateSlideshowPlaylist;
window.generateSlideshowPlaylistAll = generateSlideshowPlaylistAll;
window.generateSlideshowPlaylistFromSelection = generateSlideshowPlaylistFromSelection;

