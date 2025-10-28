// 统计面板管理类
class StatsPanel {
    constructor() {
        this.elements = {
            toggleButton: document.getElementById('toggleStatsPanel'),
            statsPanel: document.getElementById('statsPanel'),
            statsToggleIcon: document.getElementById('statsToggleIcon'),
            totalPhotosCount: document.getElementById('totalPhotosCount'),
            totalStorageSize: document.getElementById('totalStorageSize'),
            timeSpan: document.getElementById('timeSpan'),
            avgQuality: document.getElementById('avgQuality'),
            qualityChartCanvas: document.getElementById('qualityChart'),
            yearChartCanvas: document.getElementById('yearChart'),
            faceCountChartCanvas: document.getElementById('faceCountChart'),
            formatList: document.getElementById('formatList'),
            cameraList: document.getElementById('cameraList')
        };
        this.data = {};
        this.charts = {};
        this.isRenderingCharts = false; // 防止重复渲染图表
        this.init();
    }

    init() {
        if (this.elements.toggleButton) {
            this.elements.toggleButton.addEventListener('click', () => this.togglePanel());
        }
        this.bsCollapse = new bootstrap.Collapse(this.elements.statsPanel, { toggle: false });
        this.elements.statsPanel.addEventListener('shown.bs.collapse', () => this.onPanelShown());
        this.elements.statsPanel.addEventListener('hidden.bs.collapse', () => this.onPanelHidden());
    }

    togglePanel() {
        this.bsCollapse.toggle();
    }

    onPanelShown() {
        this.elements.statsToggleIcon.classList.replace('bi-chevron-down', 'bi-chevron-up');
        
        // 更新按钮文本
        const button = this.elements.toggleButton;
        // 查找并删除所有文本节点，然后添加新的文本节点
        Array.from(button.childNodes).forEach(node => {
            if (node.nodeType === Node.TEXT_NODE) {
                node.remove();
            }
        });
        // 添加新的文本节点
        button.appendChild(document.createTextNode('点击收起'));

        // 确保Canvas有正确的尺寸
        setTimeout(() => {
            this.resizeCanvases();
            this.renderCharts();
        }, 100); // 等待Collapse动画完成
    }

    onPanelHidden() {
        this.elements.statsToggleIcon.classList.replace('bi-chevron-up', 'bi-chevron-down');
        
        // 更新按钮文本
        const button = this.elements.toggleButton;
        // 查找并删除所有文本节点，然后添加新的文本节点
        Array.from(button.childNodes).forEach(node => {
            if (node.nodeType === Node.TEXT_NODE) {
                node.remove();
            }
        });
        // 添加新的文本节点
        button.appendChild(document.createTextNode('点击展开'));
    }

    resizeCanvases() {
        // 设置所有Canvas的尺寸
        const canvases = [
            this.elements.qualityChartCanvas,
            this.elements.yearChartCanvas,
            this.elements.faceCountChartCanvas
        ];

        canvases.forEach(canvas => {
            if (canvas && canvas.parentElement) {
                const rect = canvas.parentElement.getBoundingClientRect();
                // 确保有有效的尺寸
                const width = Math.max(rect.width, 100);
                const height = Math.max(rect.height || 250, 100); // 默认250px高度
                canvas.width = width;
                canvas.height = height;
                console.log(`Canvas resized: ${canvas.id} - ${canvas.width}x${canvas.height} (parent: ${rect.width}x${rect.height})`);
            }
        });

        // 调用全局Canvas尺寸检查函数
        if (window.checkCanvasSizes) {
            window.checkCanvasSizes();
        }
    }

    renderStats() {
        console.log('StatsPanel: renderStats called with data:', this.data);
        // 使用overview数据，如果没有则使用根级别数据
        const overview = this.data.overview || this.data;

        // 更新详细统计面板的概览卡片
        this.elements.totalPhotosCount.textContent = overview.total_photos !== undefined ? overview.total_photos.toLocaleString() : '-';
        this.elements.totalStorageSize.textContent = overview.total_storage_gb !== undefined ? overview.total_storage_gb.toFixed(1) : '-';
        this.elements.timeSpan.textContent = overview.time_span_years !== undefined ? overview.time_span_years.toLocaleString() : '-';
        this.elements.avgQuality.textContent = overview.avg_quality !== undefined ? overview.avg_quality.toFixed(1) : '-';

        // 更新分析状态卡片
        const photosUnanalyzed = document.getElementById('photosUnanalyzed');
        const photosBasicAnalyzed = document.getElementById('photosBasicAnalyzed');
        const photosAiAnalyzed = document.getElementById('photosAiAnalyzed');
        const photosFullyAnalyzed = document.getElementById('photosFullyAnalyzed');
        const photosWithGps = document.getElementById('photosWithGps');
        const photosGeocoded = document.getElementById('photosGeocoded');

        if (photosUnanalyzed) photosUnanalyzed.textContent = this.data.photos_unanalyzed !== undefined ? this.data.photos_unanalyzed.toLocaleString() : '-';
        if (photosBasicAnalyzed) photosBasicAnalyzed.textContent = this.data.photos_basic_analyzed !== undefined ? this.data.photos_basic_analyzed.toLocaleString() : '-';
        if (photosAiAnalyzed) photosAiAnalyzed.textContent = this.data.photos_ai_analyzed !== undefined ? this.data.photos_ai_analyzed.toLocaleString() : '-';
        if (photosFullyAnalyzed) photosFullyAnalyzed.textContent = this.data.photos_fully_analyzed !== undefined ? this.data.photos_fully_analyzed.toLocaleString() : '-';
        if (photosWithGps) photosWithGps.textContent = this.data.photos_with_gps !== undefined ? this.data.photos_with_gps.toLocaleString() : '-';
        if (photosGeocoded) photosGeocoded.textContent = this.data.photos_geocoded !== undefined ? this.data.photos_geocoded.toLocaleString() : '-';

        // 更新标题行的统计图标
        this.renderHeaderStats();

        if (this.elements.statsPanel.classList.contains('show')) {
            this.renderCharts();
        } else {
            console.log('StatsPanel: panel is hidden, skipping chart rendering');
        }
    }

    renderHeaderStats() {
        const stats = this.data;
        const qualityLevels = stats.charts?.quality?.labels?.length || 0;

        const statsIconsHtml = `
            <span class="stats-icon" data-bs-toggle="tooltip" data-bs-placement="top" title="总照片数: ${stats.total_photos || 0}">
                <i class="bi bi-images text-primary"></i>${stats.total_photos || 0}
            </span>
            <span class="stats-icon" data-bs-toggle="tooltip" data-bs-placement="top" title="总标签数: ${stats.total_tags || 0}">
                <i class="bi bi-tags text-success"></i>${stats.total_tags || 0}
            </span>
            <span class="stats-icon" data-bs-toggle="tooltip" data-bs-placement="top" title="总分类数: ${stats.total_categories || 0}">
                <i class="bi bi-collection text-info"></i>${stats.total_categories || 0}
            </span>
            <span class="stats-icon" data-bs-toggle="tooltip" data-bs-placement="top" title="质量等级数: ${qualityLevels}">
                <i class="bi bi-star text-warning"></i>${qualityLevels}
            </span>
            <span class="stats-icon" data-bs-toggle="tooltip" data-bs-placement="top" title="总存储量: ${stats.total_storage_gb || 0} GB">
                <i class="bi bi-hdd text-success"></i>${stats.total_storage_gb || 0}GB
            </span>
            <span class="stats-icon" data-bs-toggle="tooltip" data-bs-placement="top" title="时间跨度: ${stats.time_span_years || 0} 年">
                <i class="bi bi-calendar text-info"></i>${stats.time_span_years || 0}年
            </span>
            <span class="stats-icon" data-bs-toggle="tooltip" data-bs-placement="top" title="平均质量分: ${stats.avg_quality || 0}">
                <i class="bi bi-graph-up text-warning"></i>${stats.avg_quality ? stats.avg_quality.toFixed(1) : 0}
            </span>
            <span class="stats-icon" data-bs-toggle="tooltip" data-bs-placement="top" title="未分析照片: ${stats.photos_unanalyzed || 0}">
                <i class="bi bi-circle text-secondary"></i>${stats.photos_unanalyzed || 0}
            </span>
            <span class="stats-icon" data-bs-toggle="tooltip" data-bs-placement="top" title="仅基础分析完成: ${stats.photos_basic_analyzed || 0}">
                <i class="bi bi-check-circle text-info"></i>${stats.photos_basic_analyzed || 0}
            </span>
            <span class="stats-icon" data-bs-toggle="tooltip" data-bs-placement="top" title="仅AI分析完成: ${stats.photos_ai_analyzed || 0}">
                <i class="bi bi-robot text-warning"></i>${stats.photos_ai_analyzed || 0}
            </span>
            <span class="stats-icon" data-bs-toggle="tooltip" data-bs-placement="top" title="全部分析完成: ${stats.photos_fully_analyzed || 0}">
                <i class="bi bi-check-circle-fill text-success"></i>${stats.photos_fully_analyzed || 0}
            </span>
            <span class="stats-icon" data-bs-toggle="tooltip" data-bs-placement="top" title="有GPS信息: ${stats.photos_with_gps || 0}">
                <i class="bi bi-geo-alt text-primary"></i>${stats.photos_with_gps || 0}
            </span>
            <span class="stats-icon" data-bs-toggle="tooltip" data-bs-placement="top" title="已转地址: ${stats.photos_geocoded || 0}">
                <i class="bi bi-house text-info"></i>${stats.photos_geocoded || 0}
            </span>
        `;

        const statsHeaderIcons = document.getElementById('statsHeaderIcons');
        if (statsHeaderIcons) {
            statsHeaderIcons.innerHTML = statsIconsHtml;
            // 初始化Bootstrap tooltips
            const tooltipTriggerList = statsHeaderIcons.querySelectorAll('[data-bs-toggle="tooltip"]');
            const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
        }
    }

    renderCharts() {
        // 防止重复渲染
        if (this.isRenderingCharts) {
            return;
        }
        this.isRenderingCharts = true;

        // 简单的延迟执行，避免可能的同步问题
        setTimeout(() => this.doRenderCharts(), 10);
    }

    doRenderCharts() {
        try {
            // 检查数据是否存在
            if (!this.data) {
                console.error('StatsPanel: No data available');
                return;
            }
            console.log('StatsPanel: Data exists');

            // 检查Chart.js是否可用
            if (typeof Chart === 'undefined') {
                console.warn('StatsPanel: Chart.js not available, retrying in 500ms...');
                this.isRenderingCharts = false; // 重置标志位
                setTimeout(() => this.doRenderCharts(), 500);
                return;
            }
            console.log('StatsPanel: Chart.js available');

            const chartsData = this.data.charts || {};
            console.log('StatsPanel: Starting chart creation with data keys:', Object.keys(chartsData));

            // 质量分布图表
            if (chartsData.quality && this.elements.qualityChartCanvas) {
                try {
                    this.destroyChart('qualityChart');
                    const ctx = this.elements.qualityChartCanvas.getContext('2d');
                    this.charts.qualityChart = new Chart(ctx, {
                        type: 'pie',
                        data: {
                            labels: chartsData.quality.labels,
                            datasets: [{
                                data: chartsData.quality.data,
                                backgroundColor: chartsData.quality.colors
                            }]
                        },
                        options: {
                            responsive: false, // 禁用响应式，因为我们手动设置尺寸
                            plugins: {
                                legend: {
                                    position: 'right'
                                }
                            },
                            onClick: (event, elements) => {
                                if (elements.length > 0) {
                                    const index = elements[0].index;
                                    const qualityLabel = chartsData.quality.labels[index];
                                    // 直接传递中文标签，filterByQuality函数会处理转换
                                    this.filterByQuality(qualityLabel);
                                }
                            }
                        }
                    });
                    console.log('StatsPanel: Quality chart created successfully');
                } catch (error) {
                    console.error('StatsPanel: Failed to create quality chart:', error);
                }
            }

            // 年份分布图表
            if (chartsData.year && this.elements.yearChartCanvas) {
                try {
                    this.destroyChart('yearChart');
                    const ctx = this.elements.yearChartCanvas.getContext('2d');
                    this.charts.yearChart = new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: chartsData.year.labels,
                            datasets: [{
                                label: '照片数量',
                                data: chartsData.year.data,
                                backgroundColor: chartsData.year.colors
                            }]
                        },
                        options: {
                            responsive: false,
                            scales: {
                                y: {
                                    beginAtZero: true
                                }
                            },
                            onClick: (event, elements) => {
                                if (elements.length > 0) {
                                    const index = elements[0].index;
                                    const year = chartsData.year.labels[index];
                                    this.filterByYear(year);
                                }
                            }
                        }
                    });
                    console.log('StatsPanel: Year chart created successfully');
                } catch (error) {
                    console.error('StatsPanel: Failed to create year chart:', error);
                }
            }

            // 人脸数分布图表
            if (chartsData.face_count && this.elements.faceCountChartCanvas) {
                try {
                    this.destroyChart('faceCountChart');
                    const ctx = this.elements.faceCountChartCanvas.getContext('2d');
                    this.charts.faceCountChart = new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: chartsData.face_count.labels,
                            datasets: [{
                                label: '照片数量',
                                data: chartsData.face_count.data,
                                backgroundColor: chartsData.face_count.colors
                            }]
                        },
                        options: {
                            responsive: false,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: {
                                    display: false
                                }
                            },
                            scales: {
                                y: {
                                    beginAtZero: true
                                },
                                x: {
                                    ticks: {
                                        maxRotation: 45,
                                        minRotation: 0
                                    }
                                }
                            },
                            onClick: (event, elements) => {
                                if (elements.length > 0) {
                                    const index = elements[0].index;
                                    const faceCount = chartsData.face_count.labels[index];
                                    this.filterByFaceCount(faceCount);
                                }
                            }
                        }
                    });
                    console.log('StatsPanel: Face count chart created successfully');
                } catch (error) {
                    console.error('StatsPanel: Failed to create face count chart:', error);
                }
            }

            // 格式分布列表 - 两列显示
            if (chartsData.format && this.elements.formatList) {
                try {
                    // 对格式数据按数量降序排列
                    const formatItems = chartsData.format.labels.map((label, index) => ({
                        label: label,
                        count: chartsData.format.data[index]
                    })).sort((a, b) => b.count - a.count);

                    const totalFormats = formatItems.length;
                    const halfPoint = Math.ceil(totalFormats / 2);

                    // 创建两列布局
                    let formatHtml = '<div class="row">';

                    // 左列
                    formatHtml += '<div class="col-6">';
                    formatHtml += '<ul class="list-group list-group-flush">';
                    for (let i = 0; i < halfPoint; i++) {
                        const item = formatItems[i];
                        formatHtml += `
                            <li class="list-group-item d-flex justify-content-between align-items-center format-list-item"
                                onclick="statsPanel.filterByFormat('${item.label}')">
                                ${item.label}
                                <span class="badge bg-info rounded-pill">${item.count}</span>
                            </li>
                        `;
                    }
                    formatHtml += '</ul>';
                    formatHtml += '</div>';

                    // 右列
                    formatHtml += '<div class="col-6">';
                    formatHtml += '<ul class="list-group list-group-flush">';
                    for (let i = halfPoint; i < totalFormats; i++) {
                        const item = formatItems[i];
                        formatHtml += `
                            <li class="list-group-item d-flex justify-content-between align-items-center format-list-item"
                                onclick="statsPanel.filterByFormat('${item.label}')">
                                ${item.label}
                                <span class="badge bg-info rounded-pill">${item.count}</span>
                            </li>
                        `;
                    }
                    formatHtml += '</ul>';
                    formatHtml += '</div>';

                    formatHtml += '</div>';
                    this.elements.formatList.innerHTML = formatHtml;
                    console.log('StatsPanel: Format list rendered successfully in 2 columns');
                } catch (error) {
                    console.error('StatsPanel: Failed to render format list:', error);
                }
            }

            // 相机分布列表 - 两列显示
            if (chartsData.camera && this.elements.cameraList) {
                try {
                    // 使用后端返回的排序（前9个品牌 + 其他品牌 + 未知相机）
                    const cameraItems = chartsData.camera.labels.map((label, index) => ({
                        label: label,
                        count: chartsData.camera.data[index],
                        color: chartsData.camera.colors[index] || '#6f42c1'
                    }));

                    // 颜色映射函数
                    const getBadgeClass = (color) => {
                        switch (color) {
                            case '#fd7e14': return 'bg-warning';  // 橙色 - 其他品牌
                            case '#dc3545': return 'bg-danger';   // 红色 - 未知相机
                            default: return 'bg-primary';         // 紫色 - 主要品牌
                        }
                    };

                    const totalCameras = cameraItems.length;
                    const halfPoint = Math.ceil(totalCameras / 2);

                    // 创建两列布局
                    let cameraHtml = '<div class="row">';

                    // 左列
                    cameraHtml += '<div class="col-6">';
                    cameraHtml += '<ul class="list-group list-group-flush">';
                    for (let i = 0; i < halfPoint; i++) {
                        const item = cameraItems[i];
                        const badgeClass = getBadgeClass(item.color);
                        cameraHtml += `
                            <li class="list-group-item d-flex justify-content-between align-items-center camera-list-item"
                                onclick="statsPanel.filterByCamera('${item.label}')">
                                ${item.label}
                                <span class="badge ${badgeClass} rounded-pill">${item.count}</span>
                            </li>
                        `;
                    }
                    cameraHtml += '</ul>';
                    cameraHtml += '</div>';

                    // 右列
                    cameraHtml += '<div class="col-6">';
                    cameraHtml += '<ul class="list-group list-group-flush">';
                    for (let i = halfPoint; i < totalCameras; i++) {
                        const item = cameraItems[i];
                        const badgeClass = getBadgeClass(item.color);
                        cameraHtml += `
                            <li class="list-group-item d-flex justify-content-between align-items-center camera-list-item"
                                onclick="statsPanel.filterByCamera('${item.label}')">
                                ${item.label}
                                <span class="badge ${badgeClass} rounded-pill">${item.count}</span>
                            </li>
                        `;
                    }
                    cameraHtml += '</ul>';
                    cameraHtml += '</div>';

                    cameraHtml += '</div>';
                    this.elements.cameraList.innerHTML = cameraHtml;
                    console.log('StatsPanel: Camera list rendered successfully in 2 columns');
                } catch (error) {
                    console.error('StatsPanel: Failed to render camera list:', error);
                }
            }
        } catch (error) {
            console.error('StatsPanel: Error rendering charts:', error);
        } finally {
            // 无论成功还是失败，都重置渲染标志位
            this.isRenderingCharts = false;
        }
    }

    destroyChart(chartId) {
        if (this.charts[chartId]) {
            this.charts[chartId].destroy();
            delete this.charts[chartId];
        }
    }

    filterByQuality(level) {
        if (level === 'all') {
            AppState.searchFilters.qualityFilter = '';
        } else {
            const levelMap = { '优秀': 'excellent', '良好': 'good', '一般': 'average', '较差': 'poor', '很差': 'bad' };
            AppState.searchFilters.qualityFilter = levelMap[level] || '';
        }
        window.loadPhotos(1);
        window.loadStats();
        window.updateFilterStatus();
    }

    filterByYear(year) {
        if (year === 'all') {
            AppState.searchFilters.dateFilter = '';
            window.elements.startDate.value = '';
            window.elements.endDate.value = '';
        } else if (year === '无拍摄时间') {
            // 特殊处理：筛选无拍摄时间的照片
            AppState.searchFilters.dateFilter = 'no_date';
            window.elements.startDate.value = '';
            window.elements.endDate.value = '';
        } else {
            AppState.searchFilters.dateFilter = 'custom';
            window.elements.startDate.value = `${year}-01-01`;
            window.elements.endDate.value = `${year}-12-31`;
        }
        window.loadPhotos(1);
        window.loadStats();
        window.updateFilterStatus();
    }

    filterByFaceCount(faceCount) {
        if (faceCount === 'all') {
            AppState.searchFilters.faceCountFilter = '';
        } else if (faceCount === '9人以上') {
            AppState.searchFilters.faceCountFilter = '9+';
        } else {
            // 提取数字部分，如 "4人" -> "4"
            const number = faceCount.replace('人', '');
            AppState.searchFilters.faceCountFilter = number;
        }
        window.loadPhotos(1);
        window.loadStats();
        window.updateFilterStatus();
    }

    filterByFormat(format) {
        if (format === 'all') {
            AppState.searchFilters.formatFilter = '';
        } else {
            AppState.searchFilters.formatFilter = format.toUpperCase();
        }
        window.loadPhotos(1);
        window.loadStats();
        window.updateFilterStatus();
    }

    filterByCamera(cameraMake) {
        if (cameraMake === 'all') {
            AppState.searchFilters.cameraFilter = '';
        } else if (cameraMake === '未知相机') {
            // 特殊处理：筛选无相机信息的照片
            AppState.searchFilters.cameraFilter = 'unknown';
        } else if (cameraMake === '其他品牌') {
            // 特殊处理：筛选其他品牌的照片（不在前9名中）
            AppState.searchFilters.cameraFilter = 'other';
        } else {
            AppState.searchFilters.cameraFilter = cameraMake;
        }
        window.loadPhotos(1);
        window.loadStats();
        window.updateFilterStatus();
    }
}

// 初始化统计面板
document.addEventListener('DOMContentLoaded', () => {
    window.statsPanel = new StatsPanel();
    console.log('StatsPanel initialized:', !!window.statsPanel);
});
