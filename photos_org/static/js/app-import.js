/**
 * 家庭单机版智能照片整理系统 - 导入功能模块
 * 
 * 功能：
 * 1. 导入方式切换
 * 2. 文件导入处理
 * 3. 文件夹导入处理
 * 4. 导入进度监控
 * 5. 批量处理功能
 */

/**
 * 切换导入方式
 * 
 * @param {string} method - 导入方式 ('file' 或 'folder')
 */
function switchImportMethod(method) {
    console.log('切换导入方式:', method);
    
    const fileSection = document.getElementById('fileImportSection');
    const folderSection = document.getElementById('folderImportSection');
    
    if (method === 'file') {
        fileSection.classList.remove('d-none');
        fileSection.style.display = 'block';
        folderSection.classList.add('d-none');
        folderSection.style.display = 'none';
    } else if (method === 'folder') {
        fileSection.classList.add('d-none');
        fileSection.style.display = 'none';
        folderSection.classList.remove('d-none');
        folderSection.style.display = 'block';
    }
}

/**
 * 处理文件夹路径变化
 */
function handleFolderPathChange() {
    const hasPath = elements.folderPath.value.trim().length > 0;
    elements.startImportBtn.disabled = !hasPath;
    
    if (hasPath) {
        elements.startImportBtn.textContent = '开始导入';
    } else {
        elements.startImportBtn.textContent = '请先选择文件夹';
    }
}

/**
 * 浏览文件夹
 */
function browseFolder() {
    console.log('🔍 点击浏览文件夹按钮');
    // 触发隐藏的文件夹选择输入框
    const folderFilesInput = document.getElementById('folderFiles');
    console.log('文件夹输入框:', folderFilesInput);
    if (folderFilesInput) {
        console.log('✅ 触发文件夹选择对话框');
        folderFilesInput.click();
    } else {
        console.error('❌ 找不到文件夹输入框');
    }
}

/**
 * 处理文件夹选择事件
 * 
 * @param {Event} event - 文件选择事件
 */
function handleFolderSelection(event) {
    /**
     * 处理文件夹选择事件
     * 
     * @param {Event} event - 文件选择事件
     */
    console.log('📁 文件夹选择事件触发');
    const files = event.target.files;
    console.log('选择的文件数量:', files?.length || 0);
    
    if (files && files.length > 0) {
        // 获取第一个文件的路径，去掉文件名得到文件夹路径
        const firstFile = files[0];
        const filePath = firstFile.webkitRelativePath || firstFile.name;
        const folderPath = filePath.substring(0, filePath.lastIndexOf('/'));
        
        console.log('文件夹路径:', folderPath);
        
        // 显示文件夹路径
        elements.folderPath.value = folderPath;
        
        // 显示选择的文件数量
        const imageFiles = Array.from(files).filter(file => file.type.startsWith('image/'));
        console.log(`选择了文件夹，包含 ${imageFiles.length} 个图片文件`);
        
        // 更新导入按钮状态
        handleFolderPathChange();
        
        // 显示选择结果
        showSuccess(`已选择文件夹，发现 ${imageFiles.length} 个图片文件`);
        
        // 自动开始导入
        console.log('🚀 准备自动开始文件夹导入...');
        console.log('CONFIG 对象:', window.CONFIG);
        console.log('AppState 对象:', window.AppState);
        
        // 确保导入方式设置为文件夹
        const folderRadio = document.querySelector('input[name="importMethod"][value="folder"]');
        if (folderRadio) {
            folderRadio.checked = true;
            console.log('✅ 已设置导入方式为文件夹');
        } else {
            console.error('❌ 找不到文件夹导入单选按钮');
        }
        
        setTimeout(() => {
            console.log('⏰ 延迟后开始执行文件夹导入...');
            startFolderImport();
        }, 1000); // 增加延迟时间到1秒
    } else {
        console.log('❌ 没有选择任何文件');
    }
}

/**
 * 验证文件夹路径格式
 * 
 * @param {string} path - 路径字符串
 * @returns {boolean} 是否有效
 */
function validateFolderPath(path) {
    /**
     * 验证文件夹路径格式
     * 
     * @param {string} path - 路径字符串
     * @returns {boolean} 是否有效
     */
    if (!path || path.trim().length === 0) {
        return false;
    }
    
    // 检查是否包含非法字符
    const invalidChars = /[<>:"|?*]/;
    if (invalidChars.test(path)) {
        return false;
    }
    
    // 检查路径长度
    if (path.length > 260) {
        return false;
    }
    
    return true;
}

/**
 * 开始导入
 */
async function startImport() {
    console.log('🚀 开始导入，检查配置和状态...');
    console.log('CONFIG 对象:', window.CONFIG);
    console.log('AppState 对象:', window.AppState);
    
    const importMethod = document.querySelector('input[name="importMethod"]:checked').value;
    console.log('选择的导入方式:', importMethod);
    
    if (importMethod === 'file') {
        console.log('执行文件导入...');
        await startFileImport();
    } else if (importMethod === 'folder') {
        console.log('执行文件夹导入...');
        await startFolderImport();
    } else {
        console.error('未知的导入方式:', importMethod);
        showError('未知的导入方式，请重新选择');
    }
}

/**
 * 开始文件导入
 */
async function startFileImport() {
    console.log('开始文件导入');
    const files = elements.photoFiles.files;
    
    if (files.length === 0) {
        showError('请先选择要导入的照片文件');
        return;
    }
    
    // 显示进度
    elements.importProgress.classList.remove('d-none');
    elements.startImportBtn.disabled = true;
    elements.importStatus.textContent = `正在处理 ${files.length} 个图片文件...`;
    
    try {
        // 创建FormData对象
        const formData = new FormData();
        Array.from(files).forEach(file => {
            formData.append('files', file);
        });
        
        // 发送请求
        const response = await fetch(`${CONFIG.API_BASE_URL}/import/upload`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            const importedCount = data.data.imported_photos || 0;
            const totalFiles = data.data.total_files || files.length;
            const failedFiles = data.data.failed_files || [];
            
            // 直接处理完成
            if (failedFiles.length > 0) {
                const failedList = failedFiles.slice(0, 10).map(f => `• ${f}`).join('\n');
                const moreText = failedFiles.length > 10 ? `\n... 还有 ${failedFiles.length - 10} 个失败文件` : '';
                showWarning(`部分导入成功：${importedCount}/${totalFiles} 张照片\n\n失败的文件：\n${failedList}${moreText}`);
            } else {
                showSuccess(`成功导入 ${importedCount} 张照片！\n\n请手动点击"批量处理"按钮进行智能分析。`);
            }
            
            // 重新加载照片列表
            await loadPhotos();
            // 关闭导入模态框
            const modal = bootstrap.Modal.getInstance(elements.importModal);
            if (modal) {
                modal.hide();
            }
        } else {
            // 根据错误类型显示不同的错误信息
            const errorMessage = data.message || '文件导入失败';
            showError(`文件导入失败：${errorMessage}`);
        }
    } catch (error) {
        console.error('文件导入失败:', error);
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            showError('网络连接失败，请检查服务器是否正常运行');
        } else {
            showError(`文件导入失败：${error.message}\n\n请稍后重试或检查网络连接`);
        }
    } finally {
        elements.importProgress.classList.add('d-none');
        elements.startImportBtn.disabled = false;
        elements.importStatus.textContent = '正在导入...';
    }
}

/**
 * 开始文件夹导入
 */
async function startFolderImport() {
    console.log('开始目录扫描导入');
    console.log('CONFIG.API_BASE_URL:', window.CONFIG?.API_BASE_URL);
    
    // 获取选择的文件
    const folderFilesInput = document.getElementById('folderFiles');
    console.log('文件夹输入框:', folderFilesInput);
    const files = folderFilesInput.files;
    console.log('选择的文件数量:', files?.length || 0);
    
    if (!files || files.length === 0) {
        console.error('没有选择任何文件');
        showError('请先选择照片目录');
        return;
    }
    
    // 过滤出图片文件
    const imageFiles = Array.from(files).filter(file => file.type.startsWith('image/'));
    console.log('图片文件数量:', imageFiles.length);
    
    if (imageFiles.length === 0) {
        showError('选择的目录中没有找到图片文件');
        return;
    }
    
    // 显示进度
    elements.importProgress.classList.remove('d-none');
    elements.startImportBtn.disabled = true;
    elements.importStatus.textContent = `正在处理 ${imageFiles.length} 个图片文件...`;
    
    try {
        // 直接使用文件上传API处理选择的文件
        const formData = new FormData();
        imageFiles.forEach(file => {
            formData.append('files', file);
        });
        
        const apiUrl = `${window.CONFIG.API_BASE_URL}/import/upload`;
        console.log('API URL:', apiUrl);
        console.log('发送的文件数量:', imageFiles.length);
        
        const response = await fetch(apiUrl, {
            method: 'POST',
            body: formData
        });
        
        console.log('API响应状态:', response.status);
        
        const data = await response.json();
        
        if (data.success) {
            const importedCount = data.data.imported_photos || 0;
            const totalFiles = data.data.total_files || imageFiles.length;
            const failedFiles = data.data.failed_files || [];
            
            // 直接处理完成
            if (failedFiles.length > 0) {
                const failedList = failedFiles.slice(0, 10).map(f => `• ${f}`).join('\n');
                const moreText = failedFiles.length > 10 ? `\n... 还有 ${failedFiles.length - 10} 个失败文件` : '';
                showWarning(`部分导入成功：${importedCount}/${totalFiles} 张照片\n\n失败的文件：\n${failedList}${moreText}`);
            } else {
                showSuccess(`成功导入 ${importedCount} 张照片！\n\n请手动点击"批量处理"按钮进行智能分析。`);
            }
            
            // 重新加载照片列表
            await loadPhotos();
            // 关闭导入模态框
            const modal = bootstrap.Modal.getInstance(elements.importModal);
            if (modal) {
                modal.hide();
            }
        } else {
            // 根据错误类型显示不同的错误信息
            const errorMessage = data.message || '文件夹导入失败';
            showError(`文件夹导入失败：${errorMessage}`);
        }
    } catch (error) {
        console.error('文件夹导入失败:', error);
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            showError('网络连接失败，请检查服务器是否正常运行');
        } else {
            showError(`文件夹导入失败：${error.message}\n\n请稍后重试或检查网络连接`);
        }
    } finally {
        elements.importProgress.classList.add('d-none');
        elements.startImportBtn.disabled = false;
        elements.importStatus.textContent = '正在导入...';
    }
}

/**
 * 监控扫描任务进度
 * 
 * @param {string} taskId - 任务ID
 * @param {number} totalFiles - 总文件数
 */
async function monitorScanProgress(taskId, totalFiles) {
    /**
     * 监控扫描任务进度
     * 
     * @param {string} taskId - 任务ID
     * @param {number} totalFiles - 总文件数
     */
    let checkCount = 0;
    const maxChecks = 300; // 最多检查300次，每次2秒，总共10分钟
    
    const progressInterval = setInterval(async () => {
        checkCount++;
        
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/import/scan-status/${taskId}`);
            const statusData = await response.json();
            
            if (response.ok) {
                const progress = statusData.progress_percentage || 0;
                const processed = statusData.processed_files || 0;
                const imported = statusData.imported_count || 0;
                const failed = statusData.failed_count || 0;
                
                // 更新进度条
                elements.importProgressBar.style.width = `${progress}%`;
                elements.importStatus.textContent = `正在处理: ${processed}/${totalFiles} (${progress}%) - 已导入: ${imported}, 失败: ${failed}`;
                
                // 检查是否完成
                if (statusData.status === 'completed') {
                    clearInterval(progressInterval);
                    
                    // 显示最终结果
                    if (failed > 0) {
                        showWarning(`扫描完成！导入 ${imported} 张照片，${failed} 个文件失败`);
                    } else {
                        showSuccess(`扫描完成！成功导入 ${imported} 张照片`);
                    }
                    
                    // 重新加载照片列表
                    await loadPhotos();
                    
                    // 关闭导入模态框
                    const modal = bootstrap.Modal.getInstance(elements.importModal);
                    if (modal) {
                        modal.hide();
                    }
                } else if (statusData.status === 'failed') {
                    clearInterval(progressInterval);
                    showError(`扫描失败：${statusData.error || '未知错误'}`);
                }
            } else {
                console.error('获取扫描状态失败:', statusData);
                if (checkCount >= maxChecks) {
                    clearInterval(progressInterval);
                    showError('扫描超时，请检查服务器状态');
                }
            }
        } catch (error) {
            console.error('监控扫描进度失败:', error);
            if (checkCount >= maxChecks) {
                clearInterval(progressInterval);
                showError('监控扫描进度失败，请检查网络连接');
            }
        }
    }, 2000); // 每2秒检查一次
    
    // 设置超时
    setTimeout(() => {
        clearInterval(progressInterval);
        showError('扫描超时，请检查服务器状态');
    }, 600000); // 10分钟超时
}

/**
 * 开始批量处理
 */
async function startBatchProcess() {
    console.log('开始批量处理');
    console.log('批量处理按钮点击事件触发');
    
    // 获取选中的处理选项
    const enableAIAnalysis = document.getElementById('enableAIAnalysis').checked;
    const enableQualityAssessment = document.getElementById('enableQualityAssessment').checked;
    const enableClassification = document.getElementById('enableClassification').checked;
    
    // 检查是否至少选择了一个选项
    if (!enableAIAnalysis && !enableQualityAssessment && !enableClassification) {
        showWarning('请至少选择一个处理选项');
        return;
    }
    
    // 显示进度
    window.elements.batchProgress.classList.remove('d-none');
    window.elements.startBatchBtn.disabled = true;
    window.elements.batchProgressBar.style.width = '0%';
    window.elements.batchStatus.textContent = '正在准备批量处理...';
    
    try {
        // 首先获取所有照片的ID
        const photosResponse = await fetch(`${window.CONFIG.API_BASE_URL}/photos?limit=1000`);
        const photosData = await photosResponse.json();
        
        if (!photosResponse.ok) {
            showError('获取照片列表失败');
            return;
        }
        
        const photoIds = photosData.photos.map(photo => photo.id);
        
        if (photoIds.length === 0) {
            showWarning('没有找到需要处理的照片');
            return;
        }
        
        // 构建分析类型列表
        const analysisTypes = [];
        if (enableAIAnalysis) analysisTypes.push('content');
        if (enableQualityAssessment) analysisTypes.push('quality');
        if (enableClassification) analysisTypes.push('duplicate');
        
        const response = await fetch(`${window.CONFIG.API_BASE_URL}/analysis/batch-analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                photo_ids: photoIds,
                analysis_types: analysisTypes
            })
        });
        
        const data = await response.json();
        
        // 检查响应是否成功（批量分析API返回BatchAnalysisResponse格式）
        if (response.ok && data.total_photos > 0) {
            showSuccess(`批量处理已开始，正在处理 ${data.total_photos} 张照片`);
            
            // 保存初始总数，用于进度条计算
            const initialTotal = data.total_photos;
            
            // 使用真实的状态检查API
            let checkCount = 0;
            const maxChecks = 120; // 最多检查120次，每次1秒，总共2分钟
            
            const statusCheckInterval = setInterval(async () => {
                checkCount++;
                
                try {
                    // 调用真实的状态检查API，传递初始总数
                    const statusResponse = await fetch(`${window.CONFIG.API_BASE_URL}/analysis/queue/status?initial_total=${initialTotal}`);
                    const statusData = await statusResponse.json();
                    
                    console.log('处理状态:', statusData);
                    
                    // 更新进度条
                    const progress = Math.min(statusData.progress_percentage || 0, 95);
                    window.elements.batchProgressBar.style.width = `${progress}%`;
                    window.elements.batchStatus.textContent = `正在处理... ${Math.round(progress)}% (${statusData.batch_completed_photos}/${statusData.batch_total_photos})`;
                    
                    // 检查是否完成
                    if (statusData.is_complete || statusData.processing_photos === 0) {
                        clearInterval(statusCheckInterval);
                        window.elements.batchProgressBar.style.width = '100%';
                        window.elements.batchStatus.textContent = '批量处理完成！';
                        showSuccess('批量处理完成！');
                        
                        // 重置按钮状态
                        window.elements.startBatchBtn.disabled = false;
                        
                        // 等待2秒确保数据库事务完成，然后刷新照片列表和统计信息
                        setTimeout(async () => {
                            console.log('重新加载照片列表和统计信息...');
                            await window.loadPhotos();
                            await window.loadStats();
                            console.log('照片列表和统计信息重新加载完成');
                            // 关闭模态框
                            const modal = bootstrap.Modal.getInstance(window.elements.batchModal);
                            if (modal) {
                                modal.hide();
                            }
                        }, 2000);
                    }
                } catch (error) {
                    console.error('检查处理状态失败:', error);
                    clearInterval(statusCheckInterval);
                    showError('检查处理状态失败');
                    window.elements.startBatchBtn.disabled = false;
                }
                
                // 超时保护
                if (checkCount >= maxChecks) {
                    clearInterval(statusCheckInterval);
                    showWarning('批量处理超时，请手动检查结果');
                    window.elements.startBatchBtn.disabled = false;
                }
            }, 1000);
            
        } else {
            showError(data.detail || '批量处理启动失败');
            window.elements.startBatchBtn.disabled = false;
        }
    } catch (error) {
        console.error('批量处理失败:', error);
        showError('批量处理失败');
        window.elements.startBatchBtn.disabled = false;
    }
}


// ============ 全局导出 ============

// 将函数导出到全局作用域
window.switchImportMethod = switchImportMethod;
window.handleFolderPathChange = handleFolderPathChange;
window.browseFolder = browseFolder;
window.handleFolderSelection = handleFolderSelection;
window.validateFolderPath = validateFolderPath;
window.startImport = startImport;
window.startFileImport = startFileImport;
window.startFolderImport = startFolderImport;
window.monitorScanProgress = monitorScanProgress;
window.startBatchProcess = startBatchProcess;
