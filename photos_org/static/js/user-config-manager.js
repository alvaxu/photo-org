/**
 * 用户配置管理模块
 * 功能：配置加载、保存、重置、导出等
 */

class UserConfigManager {
    constructor() {
        this.config = {};
        this.originalConfig = {};
        this.isLoading = false;
        this.hasChanges = false;
        
        this.init();
    }

    /**
     * 初始化配置管理器
     */
    init() {
        this.bindEvents();
        this.loadConfig();
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

        // 路径选择按钮
        document.getElementById('selectPhotosPath').addEventListener('click', () => {
            this.selectDirectory('photosPath');
        });
        
        document.getElementById('selectDatabasePath').addEventListener('click', () => {
            this.selectFile('databasePath');
        });

        // 帮助按钮
        const helpBtn = document.getElementById('helpApiKeyBtn');
        if (helpBtn) {
            helpBtn.addEventListener('click', () => {
                this.openHelpPage();
            });
        }
    }

    /**
     * 绑定滑块事件
     */
    bindRangeSliders() {
        const sliders = [
            'thumbnailQuality', 'thumbnailSize', 'similarityThreshold', 'duplicateThreshold'
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
            'aiModel', 'maxFileSize', 'photosPerPage', 'similarPhotosLimit', 
            'hotTagsLimit', 'hotCategoriesLimit'
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
                        } else if (id === 'hotTagsLimit' || id === 'hotCategoriesLimit') {
                            currentValueDisplay.textContent = value + '个';
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
            
            // 并行加载用户配置和可用模型列表
            const [configResponse, modelsResponse] = await Promise.all([
                fetch('/api/v1/config/user'),
                fetch('/api/v1/config/models')
            ]);
            
            if (!configResponse.ok) {
                throw new Error(`HTTP ${configResponse.status}: ${configResponse.statusText}`);
            }
            
            const result = await configResponse.json();
            if (result.success) {
                this.config = result.data;
                this.originalConfig = JSON.parse(JSON.stringify(result.data));
                
                // 加载可用模型列表
                if (modelsResponse.ok) {
                    const modelsResult = await modelsResponse.json();
                    if (modelsResult.success && modelsResult.data && modelsResult.data.available_models) {
                        this.populateModelOptions(modelsResult.data.available_models);
                    }
                }
                
                this.populateForm();
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

        // 存储配置
        const photosPath = this.config.storage?.base_path || 'D:/photo_data/storage';
        const photosPathInput = document.getElementById('photosPath');
        if (photosPathInput) {
            photosPathInput.value = photosPath;
        }
        this.updateCurrentValue('photosPathCurrent', photosPath);
        
        const databasePath = this.config.database?.path || 'D:/photo_data/db/photos.db';
        const databasePathInput = document.getElementById('databasePath');
        if (databasePathInput) {
            databasePathInput.value = databasePath;
        }
        this.updateCurrentValue('databasePathCurrent', databasePath);
        
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
        
        const hotTagsLimit = this.config.ui?.hot_tags_limit || 10;
        this.setSelectValue('hotTagsLimit', hotTagsLimit);
        this.updateCurrentValue('hotTagsLimitCurrent', hotTagsLimit + '个');
        
        const hotCategoriesLimit = this.config.ui?.hot_categories_limit || 10;
        this.setSelectValue('hotCategoriesLimit', hotCategoriesLimit);
        this.updateCurrentValue('hotCategoriesLimitCurrent', hotCategoriesLimit + '个');

        // 搜索配置
        const similarityThreshold = this.config.search?.similarity_threshold || 0.8;
        this.setRangeValue('similarityThreshold', similarityThreshold);
        this.updateCurrentValue('similarityThresholdCurrent', similarityThreshold.toString());
        
        const duplicateThreshold = this.config.analysis?.duplicate_threshold || 5;
        this.setRangeValue('duplicateThreshold', duplicateThreshold);
        this.updateCurrentValue('duplicateThresholdCurrent', duplicateThreshold.toString());
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
                base_path: document.getElementById('photosPath').value,
                thumbnail_quality: parseInt(document.getElementById('thumbnailQuality').value),
                thumbnail_size: parseInt(document.getElementById('thumbnailSize').value)
            },
            database: {
                path: document.getElementById('databasePath').value
            },
            system: {
                max_file_size: parseInt(document.getElementById('maxFileSize').value)
            },
            ui: {
                photos_per_page: parseInt(document.getElementById('photosPerPage').value),
                similar_photos_limit: parseInt(document.getElementById('similarPhotosLimit').value),
                hot_tags_limit: parseInt(document.getElementById('hotTagsLimit').value),
                hot_categories_limit: parseInt(document.getElementById('hotCategoriesLimit').value)
            },
            search: {
                similarity_threshold: parseFloat(document.getElementById('similarityThreshold').value)
            },
            analysis: {
                duplicate_threshold: parseInt(document.getElementById('duplicateThreshold').value)
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
        if (!confirm('确定要重置所有配置为默认值吗？此操作不可撤销。')) {
            return;
        }

        try {
            this.showLoading(true);
            
            const response = await fetch('/api/v1/config/user/reset', {
                method: 'POST'
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            if (result.success) {
                this.config = result.data;
                this.originalConfig = JSON.parse(JSON.stringify(result.data));
                this.populateForm();
                this.hasChanges = false;
                this.updateSaveButton();
                this.showStatus('配置已重置为默认值', 'success');
            } else {
                throw new Error(result.message || '重置配置失败');
            }
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

            const result = await response.json();
            if (result.success) {
                // 创建下载链接
                const blob = new Blob([JSON.stringify(result.data, null, 2)], {
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
            } else {
                throw new Error(result.message || '导出配置失败');
            }
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
    
    /**
     * 选择文件
     */
    async selectFile(inputId) {
        const input = document.getElementById(inputId);
        
        try {
            const response = await fetch('/api/v1/config/select-database-file', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const result = await response.json();
            
            if (result.success) {
                input.value = result.path;
                this.markAsChanged();
                this.updateCurrentValue(inputId + 'Current', result.path);
                console.log('选择的数据库文件:', result.path);
            } else {
                if (result.message === '用户取消选择') {
                    console.log('用户取消选择数据库文件');
                } else {
                    console.error('选择数据库文件失败:', result.message);
                    alert('选择数据库文件失败: ' + result.message);
                }
            }
        } catch (error) {
            console.error('选择数据库文件失败:', error);
            alert('选择数据库文件失败: ' + error.message);
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
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    // 避免重复初始化
    if (!window.configManager) {
        window.configManager = new UserConfigManager();
    }
});
