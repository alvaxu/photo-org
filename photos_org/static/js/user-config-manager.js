/**
 * 用户配置管理模块
 * 功能：配置加载、保存、重置、导出等
 */

class UserConfigManager {
    constructor() {
        this.config = {};
        this.defaultConfig = {}; // 添加默认配置缓存
        this.originalConfig = {};
        this.isLoading = false;
        this.hasChanges = false;
        
        this.init();
    }

    /**
     * 初始化配置管理器
     */
    init() {
        this.checkRemoteAccess();
        this.bindEvents();
        this.loadConfig();
    }

    /**
     * 检测是否为远程访问 - 存储目录配置已移除，此函数保留但无实际作用
     */
    checkRemoteAccess() {
        // 存储目录配置已从界面中完全移除，不再需要远程访问检查
        // 此函数保留以保持代码结构完整性
    }

    /**
     * 绑定事件监听器
     */
    bindEvents() {
        // 保存配置按钮
        const saveBtn = document.getElementById('saveConfigBtn');
        if (saveBtn) {
            saveBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.saveConfig();
            });
        }

        // 重置配置按钮
        const resetBtn = document.getElementById('resetConfigBtn');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                this.resetConfig();
            });
        }

        // 导出配置按钮
        const exportBtn = document.getElementById('exportConfigBtn');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => {
                this.exportConfig();
            });
        }

        // 滑块值变化事件
        this.bindRangeSliders();

        // 选择框变化事件
        this.bindSelectBoxes();

        // 路径选择按钮 - 照片存储目录已从用户界面移除
        // document.getElementById('selectPhotosPath').addEventListener('click', () => {
        //     this.selectDirectory('photosPath');
        // });

        // API密钥显示/隐藏切换
        const toggleBtn = document.getElementById('toggleApiKeyVisibility');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => {
                this.toggleApiKeyVisibility();
            });
        }

        // 帮助按钮
        const helpBtn = document.getElementById('helpApiKeyBtn');
        if (helpBtn) {
            helpBtn.addEventListener('click', () => {
                this.openHelpPage();
            });
        }

        // 高德API Key测试按钮
        const testAmapBtn = document.getElementById('testAmapApi');
        if (testAmapBtn) {
            testAmapBtn.addEventListener('click', () => {
                this.testAmapApiKey();
            });
        }
    }

    /**
     * 绑定滑块事件
     */
    bindRangeSliders() {
        const sliders = [
            'thumbnailQuality', 'thumbnailSize', 'featuresSimilarityThreshold', 'similarityThreshold', 'duplicateThreshold'
        ];

        sliders.forEach(id => {
            const slider = document.getElementById(id);
            const valueDisplay = document.getElementById(id + 'Value');
            const currentValueDisplay = document.getElementById(id + 'Current');
            
            if (slider && valueDisplay) {
                slider.addEventListener('input', (e) => {
                    const value = e.target.value;
                    valueDisplay.textContent = value;
                    
                    // 更新当前值显示
                    if (currentValueDisplay) {
                        if (id === 'thumbnailQuality') {
                            currentValueDisplay.textContent = value + '%';
                        } else if (id === 'thumbnailSize') {
                            currentValueDisplay.textContent = value + 'px';
                        } else {
                            currentValueDisplay.textContent = value;
                        }
                    }
                    
                    this.markAsChanged();
                });
            }
        });
    }

    /**
     * 绑定选择框事件
     */
    bindSelectBoxes() {
        const selects = [
            'aiModel', 'maxFileSize', 'photosPerPage', 'similarPhotosLimit'
        ];
        
        selects.forEach(id => {
            const select = document.getElementById(id);
            if (select) {
                select.addEventListener('change', (e) => {
                    const value = e.target.value;
                    const currentValueDisplay = document.getElementById(id + 'Current');
                    
                    // 更新当前值显示
                    if (currentValueDisplay) {
                        if (id === 'maxFileSize') {
                            currentValueDisplay.textContent = this.formatFileSize(parseInt(value));
                        } else if (id === 'photosPerPage' || id === 'similarPhotosLimit') {
                            currentValueDisplay.textContent = value + '张';
                        } else if (id === 'aiModel') {
                            currentValueDisplay.textContent = value || '未设置';
                        } else {
                            currentValueDisplay.textContent = value;
                        }
                    }
                    
                    this.markAsChanged();
                });
            }
        });
    }

    /**
     * 标记配置已更改
     */
    markAsChanged() {
        this.hasChanges = true;
        this.updateSaveButton();
    }

    /**
     * 更新保存按钮状态
     */
    updateSaveButton() {
        const saveBtn = document.getElementById('saveConfigBtn');
        if (saveBtn) {
            if (this.hasChanges) {
                saveBtn.classList.remove('btn-outline-light');
                saveBtn.classList.add('btn-warning');
                saveBtn.innerHTML = '<i class="bi bi-exclamation-triangle"></i> 保存更改';
            } else {
                saveBtn.classList.remove('btn-warning');
                saveBtn.classList.add('btn-outline-light');
                saveBtn.innerHTML = '<i class="bi bi-check-lg"></i> 保存配置';
            }
        }
    }

    /**
     * 加载配置
     */
    async loadConfig() {
        try {
            this.showLoading(true);
            
            // 并行加载用户配置、默认配置、可用模型列表和地图配置
            const [configResponse, defaultsResponse, modelsResponse, mapsResponse] = await Promise.all([
                fetch('/api/v1/config/user'),
                fetch('/api/v1/config/defaults'), // 新增：加载默认配置
                fetch('/api/v1/config/models'),
                fetch('/api/maps/config') // 新增：加载地图配置
            ]);
            
            if (!configResponse.ok) {
                throw new Error(`HTTP ${configResponse.status}: ${configResponse.statusText}`);
            }
            
            const result = await configResponse.json();
            if (result.success) {
                this.config = result.data;
                this.originalConfig = JSON.parse(JSON.stringify(result.data));
                
                // 加载默认配置
                if (defaultsResponse.ok) {
                    const defaultsResult = await defaultsResponse.json();
                    if (defaultsResult.success) {
                        this.defaultConfig = defaultsResult.data;
                    }
                }
                
                // 加载可用模型列表
                if (modelsResponse.ok) {
                    const modelsResult = await modelsResponse.json();
                    if (modelsResult.success && modelsResult.data && modelsResult.data.available_models) {
                        this.populateModelOptions(modelsResult.data.available_models);
                    }
                }
                
                // 加载地图配置
                if (mapsResponse.ok) {
                    const mapsResult = await mapsResponse.json();
                    if (mapsResult.configured) {
                        // 地图配置已设置，但我们无法从API获取具体的API Key（安全考虑）
                        // 这里我们只需要知道配置状态即可
                        this.config.maps = { configured: true };
                    }
                }
                
                this.populateForm();
                this.populateDefaultValues(); // 新增：填充默认值显示
                this.hasChanges = false;
                this.updateSaveButton();
            } else {
                throw new Error(result.message || '加载配置失败');
            }
        } catch (error) {
            console.error('加载配置失败:', error);
            this.showStatus('加载配置失败: ' + error.message, 'danger');
        } finally {
            this.showLoading(false);
        }
    }

    /**
     * 填充大模型选项
     */
    populateModelOptions(models) {
        const select = document.getElementById('aiModel');
        if (!select) return;
        
        select.innerHTML = '';
        
        // 添加默认选项
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = '请选择模型...';
        select.appendChild(defaultOption);
        
        models.forEach(model => {
            const option = document.createElement('option');
            option.value = model;
            option.textContent = model;
            if (model === 'qwen-vl-plus') {
                option.textContent += ' (推荐)';
            }
            select.appendChild(option);
        });
    }

    /**
     * 填充表单数据
     */
    populateForm() {
        // AI服务配置
        const aiModel = this.config.dashscope?.model || '';
        this.setSelectValue('aiModel', aiModel);
        this.updateCurrentValue('aiModelCurrent', aiModel || '未设置');
        
        const apiKey = this.config.dashscope?.api_key || '';
        const apiKeyInput = document.getElementById('apiKey');
        if (apiKeyInput) {
            apiKeyInput.value = apiKey;
        }
        this.updateCurrentValue('apiKeyCurrent', apiKey ? '已设置' : '使用环境变量');

        // 存储配置 - 照片存储目录已从用户界面移除
        // const photosPath = this.config.storage?.base_path || 'D:/photo_data/storage';
        // const photosPathInput = document.getElementById('photosPath');
        // if (photosPathInput) {
        //     photosPathInput.value = photosPath;
        // }
        // this.updateCurrentValue('photosPathCurrent', photosPath);
        
        // 数据库路径已从用户界面移除，但保留在配置中
        
        const thumbnailQuality = this.config.storage?.thumbnail_quality || 85;
        this.setRangeValue('thumbnailQuality', thumbnailQuality);
        this.updateCurrentValue('thumbnailQualityCurrent', thumbnailQuality + '%');
        
        const thumbnailSize = this.config.storage?.thumbnail_size || 300;
        this.setRangeValue('thumbnailSize', thumbnailSize);
        this.updateCurrentValue('thumbnailSizeCurrent', thumbnailSize + 'px');
        
        const maxFileSize = this.config.system?.max_file_size || 52428800;
        this.setSelectValue('maxFileSize', maxFileSize);
        this.updateCurrentValue('maxFileSizeCurrent', this.formatFileSize(maxFileSize));

        // 界面配置
        const photosPerPage = this.config.ui?.photos_per_page || 12;
        this.setSelectValue('photosPerPage', photosPerPage);
        this.updateCurrentValue('photosPerPageCurrent', photosPerPage + '张');
        
        const similarPhotosLimit = this.config.ui?.similar_photos_limit || 8;
        this.setSelectValue('similarPhotosLimit', similarPhotosLimit);
        this.updateCurrentValue('similarPhotosLimitCurrent', similarPhotosLimit + '张');
        
        // 热门标签和分类配置已移除

        // 搜索配置
        // 特征向量搜索相似度阈值
        const featuresSimilarityThreshold = this.config.image_features?.similarity_threshold || 0.75;
        this.setRangeValue('featuresSimilarityThreshold', featuresSimilarityThreshold);
        this.updateCurrentValue('featuresSimilarityThresholdCurrent', featuresSimilarityThreshold.toString());
        
        // 智能分析相似度阈值
        const similarityThreshold = this.config.search?.similarity_threshold || 0.8;
        this.setRangeValue('similarityThreshold', similarityThreshold);
        this.updateCurrentValue('similarityThresholdCurrent', similarityThreshold.toString());
        
        // 重复检测阈值
        const duplicateThreshold = this.config.analysis?.duplicate_threshold || 5;
        this.setRangeValue('duplicateThreshold', duplicateThreshold);
        this.updateCurrentValue('duplicateThresholdCurrent', duplicateThreshold.toString());

        // 地图服务配置
        const amapApiKeyInput = document.getElementById('amapApiKey');
        if (amapApiKeyInput) {
            // 由于安全考虑，API不会返回具体的API Key
            // 我们只显示配置状态，不预填充API Key
            amapApiKeyInput.value = '';
        }
        // 根据配置状态显示当前值
        const isConfigured = this.config.maps?.configured || false;
        this.updateCurrentValue('amapApiKeyCurrent', isConfigured ? '已设置' : '未设置');

        // 地理编码服务配置
        const defaultServiceSelect = document.getElementById('defaultGeocodingService');
        if (defaultServiceSelect) {
            // 从localStorage加载默认服务设置
            const savedService = localStorage.getItem('defaultGeocodingService') || 'ask';
            defaultServiceSelect.value = savedService;
        }

        // 相似照片搜索方式配置
        const defaultSimilarSearchSelect = document.getElementById('defaultSimilarPhotoSearch');
        if (defaultSimilarSearchSelect) {
            // 从localStorage加载默认搜索方式设置（默认每次都询问）
            let savedSearchService = localStorage.getItem('defaultSimilarPhotoSearch') || 'ask';
            // 兼容旧配置：将 'hash' 迁移为 'features'
            if (savedSearchService === 'hash') {
                savedSearchService = 'features';
                localStorage.setItem('defaultSimilarPhotoSearch', 'features');
            }
            defaultSimilarSearchSelect.value = savedSearchService;
        }
    }

    /**
     * 填充默认值显示
     */
    populateDefaultValues() {
        // AI服务配置
        const defaultModel = this.defaultConfig.dashscope?.model || 'qwen-vl-plus';
        this.updateDefaultValue('aiModelDefault', defaultModel);
        
        const defaultApiKey = this.defaultConfig.dashscope?.api_key ? '已设置' : '使用环境变量';
        this.updateDefaultValue('apiKeyDefault', defaultApiKey);

        // 存储配置 - 照片存储目录已从用户界面移除
        // const defaultPhotosPath = this.defaultConfig.storage?.base_path || './storage';
        // this.updateDefaultValue('photosPathDefault', defaultPhotosPath);
        
        // 数据库路径默认值已从用户界面移除
        
        const defaultThumbnailQuality = this.defaultConfig.storage?.thumbnail_quality || 50;
        this.updateDefaultValue('thumbnailQualityDefault', defaultThumbnailQuality + '%');
        
        const defaultThumbnailSize = this.defaultConfig.storage?.thumbnail_size || 300;
        this.updateDefaultValue('thumbnailSizeDefault', defaultThumbnailSize + 'px');
        
        const defaultMaxFileSize = this.defaultConfig.system?.max_file_size || 52428800;
        this.updateDefaultValue('maxFileSizeDefault', this.formatFileSize(defaultMaxFileSize));

        // 界面配置
        const defaultPhotosPerPage = this.defaultConfig.ui?.photos_per_page || 18;
        this.updateDefaultValue('photosPerPageDefault', defaultPhotosPerPage + '张');
        
        const defaultSimilarPhotosLimit = this.defaultConfig.ui?.similar_photos_limit || 8;
        this.updateDefaultValue('similarPhotosLimitDefault', defaultSimilarPhotosLimit + '张');
        
        // 热门标签和分类默认值已移除

        // 搜索配置
        // 特征向量搜索相似度阈值默认值
        const defaultFeaturesSimilarityThreshold = this.defaultConfig.image_features?.similarity_threshold || 0.75;
        this.updateDefaultValue('featuresSimilarityThresholdDefault', defaultFeaturesSimilarityThreshold.toString());
        
        // 智能分析相似度阈值默认值
        const defaultSimilarityThreshold = this.defaultConfig.search?.similarity_threshold || 0.6;
        this.updateDefaultValue('similarityThresholdDefault', defaultSimilarityThreshold.toString());
        
        // 重复检测阈值默认值
        const defaultDuplicateThreshold = this.defaultConfig.analysis?.duplicate_threshold || 5;
        this.updateDefaultValue('duplicateThresholdDefault', defaultDuplicateThreshold.toString());
    }

    /**
     * 更新默认值显示
     */
    updateDefaultValue(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value;
        }
    }

    /**
     * 设置滑块值
     */
    setRangeValue(id, value) {
        const slider = document.getElementById(id);
        const valueDisplay = document.getElementById(id + 'Value');
        
        if (slider && valueDisplay) {
            slider.value = value;
            valueDisplay.textContent = value;
        }
    }

    /**
     * 设置选择框值
     */
    setSelectValue(id, value) {
        const select = document.getElementById(id);
        if (select) {
            select.value = value;
        }
    }

    /**
     * 更新当前值显示
     */
    updateCurrentValue(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value;
        }
    }

    /**
     * 格式化文件大小
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * 收集表单数据
     */
    collectFormData() {
        return {
            dashscope: {
                model: document.getElementById('aiModel').value,
                api_key: document.getElementById('apiKey').value || null
            },
            storage: {
                // base_path 已从用户界面移除，使用配置中的默认值
                thumbnail_quality: parseInt(document.getElementById('thumbnailQuality').value),
                thumbnail_size: parseInt(document.getElementById('thumbnailSize').value)
            },
            // 数据库路径已从用户界面移除，使用配置中的默认值
            system: {
                max_file_size: parseInt(document.getElementById('maxFileSize').value)
            },
            ui: {
                photos_per_page: parseInt(document.getElementById('photosPerPage').value),
                similar_photos_limit: parseInt(document.getElementById('similarPhotosLimit').value)
            },
            search: {
                similarity_threshold: parseFloat(document.getElementById('similarityThreshold').value)
            },
            image_features: {
                similarity_threshold: parseFloat(document.getElementById('featuresSimilarityThreshold').value)
            },
            analysis: {
                duplicate_threshold: parseInt(document.getElementById('duplicateThreshold').value)
            },
            maps: {
                api_key: document.getElementById('amapApiKey').value || null
            },
            geocoding: {
                default_service: document.getElementById('defaultGeocodingService').value || 'ask'
            },
            similar_search: {
                default_service: document.getElementById('defaultSimilarPhotoSearch').value || 'features'
            }
        };
    }

    /**
     * 保存配置
     */
    async saveConfig() {
        try {
            this.showLoading(true);
            
            const configData = this.collectFormData();
            
            // 分离maps配置和geocoding配置，使用专门的API保存
            const mapsConfig = configData.maps;
            const geocodingConfig = configData.geocoding;
            delete configData.maps;
            delete configData.geocoding;
            
            // 保存其他配置
            const response = await fetch('/api/v1/config/user', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(configData)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            if (result.success) {
                // 保存maps配置（如果有的话）
                if (mapsConfig && mapsConfig.api_key) {
                    try {
                        const mapsResponse = await fetch('/api/maps/config', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                api_key: mapsConfig.api_key
                            })
                        });
                        
                        if (!mapsResponse.ok) {
                            const mapsError = await mapsResponse.json();
                            throw new Error(`地图配置保存失败: ${mapsError.detail || mapsResponse.statusText}`);
                        }
                    } catch (mapsError) {
                        console.error('保存地图配置失败:', mapsError);
                        this.showStatus('其他配置保存成功，但地图配置保存失败: ' + mapsError.message, 'warning');
                        return;
                    }
                }
                
                // 保存geocoding配置到localStorage
                if (geocodingConfig && geocodingConfig.default_service) {
                    localStorage.setItem('defaultGeocodingService', geocodingConfig.default_service);
                }
                
                // 保存相似照片搜索方式配置到localStorage
                if (configData.similar_search && configData.similar_search.default_service) {
                    localStorage.setItem('defaultSimilarPhotoSearch', configData.similar_search.default_service);
                }
                
                this.originalConfig = JSON.parse(JSON.stringify(configData));
                this.hasChanges = false;
                this.updateSaveButton();
                this.showStatus('配置保存成功', 'success');
            } else {
                throw new Error(result.message || '保存配置失败');
            }
        } catch (error) {
            console.error('保存配置失败:', error);
            this.showStatus('保存配置失败: ' + error.message, 'danger');
        } finally {
            this.showLoading(false);
        }
    }

    /**
     * 重置配置
     */
    async resetConfig() {
        if (!confirm('确定要将页面配置重置为默认值吗？此操作只会影响页面显示的配置项，其他配置保持不变。')) {
            return;
        }

        try {
            this.showLoading(true);

            // 获取默认配置值
            const response = await fetch('/api/v1/config/defaults');
            if (!response.ok) {
                throw new Error(`获取默认配置失败: HTTP ${response.status}`);
            }

            const defaults = await response.json();
            if (!defaults.success) {
                throw new Error(defaults.message || '获取默认配置失败');
            }

            // 只重置页面管理的配置项
            this.config.dashscope = {
                model: defaults.data.dashscope.model,
                api_key: defaults.data.dashscope.api_key,
                available_models: defaults.data.dashscope.available_models
            };
            this.config.storage.thumbnail_quality = defaults.data.storage.thumbnail_quality;
            this.config.storage.thumbnail_size = defaults.data.storage.thumbnail_size;
            this.config.system.max_file_size = defaults.data.system.max_file_size;
            this.config.ui.photos_per_page = defaults.data.ui.photos_per_page;
            this.config.ui.similar_photos_limit = defaults.data.ui.similar_photos_limit;
            this.config.search.similarity_threshold = defaults.data.search.similarity_threshold;
            if (!this.config.image_features) {
                this.config.image_features = {};
            }
            this.config.image_features.similarity_threshold = defaults.data.image_features?.similarity_threshold || 0.75;
            this.config.analysis.duplicate_threshold = defaults.data.analysis.duplicate_threshold;

            // 更新原始配置副本
            this.originalConfig = JSON.parse(JSON.stringify(this.config));

            // 重新填充表单
            this.populateForm();
            this.hasChanges = false;
            this.updateSaveButton();

            this.showStatus('页面配置已重置为默认值，其他配置保持不变', 'success');
        } catch (error) {
            console.error('重置配置失败:', error);
            this.showStatus('重置配置失败: ' + error.message, 'danger');
        } finally {
            this.showLoading(false);
        }
    }

    /**
     * 导出配置
     */
    async exportConfig() {
        try {
            const response = await fetch('/api/v1/config/export');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            // 获取完整的配置数据（包括所有配置项）
            const configResponse = await fetch('/api/v1/config/user');
            if (!configResponse.ok) {
                throw new Error('获取配置数据失败');
            }

            const configData = await configResponse.json();
            if (!configData.success) {
                throw new Error('获取配置数据失败');
            }

            // 创建下载链接
            const blob = new Blob([JSON.stringify(configData.data, null, 2)], {
                type: 'application/json'
            });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `photos-system-config-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            this.showStatus('配置导出成功', 'success');
        } catch (error) {
            console.error('导出配置失败:', error);
            this.showStatus('导出配置失败: ' + error.message, 'danger');
        }
    }

    /**
     * 显示加载状态
     */
    showLoading(show) {
        this.isLoading = show;
        const container = document.querySelector('.container-fluid');
        
        if (show) {
            container.classList.add('loading');
        } else {
            container.classList.remove('loading');
        }
    }

    /**
     * 显示状态消息
     */
    showStatus(message, type = 'info') {
        const statusDiv = document.getElementById('configStatus');
        if (!statusDiv) return;
        
        statusDiv.className = `alert alert-${type}`;
        statusDiv.innerHTML = `
            <i class="bi bi-info-circle me-2"></i>
            ${message}
        `;
        statusDiv.classList.remove('d-none');
        
        // 3秒后自动隐藏
        setTimeout(() => {
            statusDiv.classList.add('d-none');
        }, 3000);
    }

    /**
     * 选择目录
     */
    async selectDirectory(inputId) {
        const input = document.getElementById(inputId);
        
        try {
            // 调用后端API选择目录
            const response = await fetch('/api/v1/config/select-directory', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                // 更新输入框值
                input.value = result.path;
                this.markAsChanged();
                this.updateCurrentValue(inputId + 'Current', result.path);
                
                console.log('选择的目录:', result.path);
            } else {
                if (result.message === '用户取消选择') {
                    console.log('用户取消选择目录');
                } else {
                    console.error('选择目录失败:', result.message);
                    alert('选择目录失败: ' + result.message);
                }
            }
            
        } catch (error) {
            console.error('选择目录失败:', error);
            alert('选择目录失败: ' + error.message);
        }
    }
    
    // selectFile 方法已移除，因为数据库文件位置已从用户界面移除

    /**
     * 切换API密钥显示/隐藏
     */
    toggleApiKeyVisibility() {
        const input = document.getElementById('apiKey');
        const icon = document.getElementById('apiKeyIcon');

        if (input && icon) {
            if (input.type === 'password') {
                input.type = 'text';
                icon.className = 'bi bi-eye';
            } else {
                input.type = 'password';
                icon.className = 'bi bi-eye-slash';
            }
        }
    }

    /**
     * 打开帮助页面
     */
    openHelpPage() {
        // 在新窗口中打开帮助页面
        const helpWindow = window.open('/help-api-key', '_blank', 'width=1200,height=800,scrollbars=yes,resizable=yes');

        if (!helpWindow) {
            // 如果弹窗被阻止，则直接跳转
            window.location.href = '/help-api-key';
        }
    }

    /**
     * 测试高德API Key
     */
    async testAmapApiKey() {
        const apiKeyInput = document.getElementById('amapApiKey');
        const testBtn = document.getElementById('testAmapApi');
        
        if (!apiKeyInput || !testBtn) return;
        
        const apiKey = apiKeyInput.value.trim();
        
        if (!this.validateAmapApiKey(apiKey)) {
            this.showAmapTestResult('请输入有效的32位API Key', 'danger');
            return;
        }

        // 显示测试中状态
        const originalText = testBtn.innerHTML;
        this.setButtonLoading(testBtn, true, '测试中...');

        try {
            const response = await fetch('/api/maps/test-geocode', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    lat: 39.9042,  // 北京天安门坐标作为测试
                    lng: 116.4074,
                    api_key: apiKey
                })
            });

            const result = await response.json();

            if (response.ok) {
                this.showAmapTestResult(`API Key测试成功！地址：${result.address}`, 'success');
            } else {
                this.showAmapTestResult(`API Key测试失败：${result.detail}`, 'danger');
            }

        } catch (error) {
            this.showAmapTestResult('测试请求失败，请检查网络', 'danger');
        } finally {
            this.setButtonLoading(testBtn, false, originalText);
        }
    }

    /**
     * 验证高德API Key格式
     */
    validateAmapApiKey(apiKey) {
        return apiKey && apiKey.length === 32;
    }

    /**
     * 显示高德API测试结果
     */
    showAmapTestResult(message, type) {
        // 创建或更新测试结果显示区域
        let resultDiv = document.getElementById('amapTestResult');
        if (!resultDiv) {
            resultDiv = document.createElement('div');
            resultDiv.id = 'amapTestResult';
            resultDiv.className = 'mt-2';
            
            // 插入到API Key输入框后面
            const apiKeyInput = document.getElementById('amapApiKey');
            if (apiKeyInput && apiKeyInput.parentNode) {
                apiKeyInput.parentNode.parentNode.appendChild(resultDiv);
            }
        }

        resultDiv.innerHTML = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                <i class="bi bi-${type === 'success' ? 'check-circle' : 'exclamation-triangle'} me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;

        // 自动隐藏成功消息
        if (type === 'success') {
            setTimeout(() => {
                const alert = resultDiv.querySelector('.alert');
                if (alert) {
                    const bsAlert = new bootstrap.Alert(alert);
                    bsAlert.close();
                }
            }, 5000);
        }
    }

    /**
     * 设置按钮加载状态
     */
    setButtonLoading(button, loading, text) {
        if (!button) return;

        button.disabled = loading;
        if (loading) {
            button.innerHTML = `<i class="bi bi-hourglass-split"></i> ${text}`;
        } else {
            button.innerHTML = text;
        }
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    // 避免重复初始化
    if (!window.configManager) {
        window.configManager = new UserConfigManager();
    }
});
