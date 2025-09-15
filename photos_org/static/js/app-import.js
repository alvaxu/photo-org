/**
 * 家庭单机版智能照片整理系统 - 导入功能模块
 * 
 * 功能：
 * 1. 导入方式切换
 * 2. 文件导入处理
 * 3. 文件夹导入处理
 * 4. 导入进度监控
 * 5. 智能处理功能
 * 6. 智能通知系统（统一格式、详细结果、模态框展示）
 * 
 * 更新日志：
 * - 2025-01-19: 完善导入和智能处理通知系统
 *   - 统一通知格式：显示总数、成功、跳过、失败数量
 *   - 添加图标区分：✅全部成功、⚠️有跳过、❌有失败
 *   - 添加"查看详情"按钮，显示详细结果模态框
 *   - 通知不再自动消失，需用户手动关闭
 *   - 智能处理模态框在显示结果后自动关闭
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
        
        // 显示选择结果（已删除，避免冗余通知）
        
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
            // 直接显示导入结果详情模态框
            showImportDetails(data.data);
            
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
            // 直接显示导入结果详情模态框
            showImportDetails(data.data);
            
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
                const skipped = statusData.skipped_count || 0;
                const failed = statusData.failed_count || 0;
                
                // 更新进度条
                elements.importProgressBar.style.width = `${progress}%`;
                elements.importStatus.textContent = `正在处理: ${processed}/${totalFiles} (${progress}%) - 已导入: ${imported}, 跳过: ${skipped}, 失败: ${failed}`;
                
                // 检查是否完成
                if (statusData.status === 'completed') {
                    clearInterval(progressInterval);
                    
                    // 直接显示导入结果详情模态框
                    showImportDetails(statusData);
                    
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
 * 开始智能处理
 */
async function startBatchProcess() {
    console.log('开始智能处理');
    console.log('智能处理按钮点击事件触发');
    
    // 智能处理默认执行所有三种分析类型
    const enableAIAnalysis = true;
    const enableQualityAssessment = true;
    const enableClassification = true;
    
    // 显示进度
    window.elements.batchProgress.classList.remove('d-none');
    window.elements.startBatchBtn.disabled = true;
    window.elements.batchProgressBar.style.width = '0%';
    window.elements.batchStatus.textContent = '正在准备智能处理...';
    
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
        if (response.ok) {
            if (data.total_photos === 0) {
                // 没有照片需要处理的情况
                showSuccess(`✅ ${data.message || '没有需要处理的照片，所有照片都已完成分析'}`);
                window.elements.startBatchBtn.disabled = false;
                
                // 等待2秒后自动关闭模态框
                setTimeout(() => {
                    const modal = bootstrap.Modal.getInstance(window.elements.batchModal);
                    if (modal) {
                        modal.hide();
                    }
                }, 2000);
                return;
            }
            
            // 有照片需要处理的情况
            // 已删除智能处理开始通知，避免冗余（模态框已有进度条显示）
            
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
                         // 立即停止状态检查
                         clearInterval(statusCheckInterval);
                         
                         window.elements.batchProgressBar.style.width = '100%';
                         window.elements.batchStatus.textContent = '智能处理完成！';
                         
                         // 重置按钮状态
                         window.elements.startBatchBtn.disabled = false;
                         
                         // 立即关闭智能处理模态框
                         const modal = bootstrap.Modal.getInstance(window.elements.batchModal);
                         if (modal) {
                             modal.hide();
                             
                             // 监听模态框关闭事件
                             window.elements.batchModal.addEventListener('hidden.bs.modal', function onModalHidden() {
                                 console.log('智能处理模态框已完全关闭，准备显示结果详情...', statusData);
                                 
                                 // 移除事件监听器，避免重复执行
                                 window.elements.batchModal.removeEventListener('hidden.bs.modal', onModalHidden);
                                 
                                 try {
                                     showBatchProcessDetails(statusData);
                                     console.log('智能处理结果详情模态框已调用');
                                 } catch (error) {
                                     console.error('显示智能处理结果详情模态框失败:', error);
                                     showError('显示处理结果失败: ' + error.message);
                                 }
                             }, { once: true });
                         } else {
                             // 如果无法获取模态框实例，直接显示结果详情
                             console.log('无法获取智能处理模态框实例，直接显示结果详情...', statusData);
                             try {
                                 showBatchProcessDetails(statusData);
                                 console.log('智能处理结果详情模态框已调用');
                             } catch (error) {
                                 console.error('显示智能处理结果详情模态框失败:', error);
                                 showError('显示处理结果失败: ' + error.message);
                             }
                         }
                         
                         // 等待3秒确保数据库事务完成，然后刷新照片列表和统计信息
                         setTimeout(async () => {
                             console.log('重新加载照片列表和统计信息...');
                             try {
                                 await window.loadPhotos();
                                 await window.loadStats();
                                 console.log('照片列表和统计信息重新加载完成');
                             } catch (error) {
                                 console.error('刷新数据失败:', error);
                                 // 如果刷新失败，显示错误提示
                                 showError('数据刷新失败，请手动刷新页面');
                             }
                         }, 3000);
                         
                         // 直接返回，避免继续执行后续的状态检查逻辑
                         return;
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
                    showWarning('智能处理超时，请手动检查结果');
                    window.elements.startBatchBtn.disabled = false;
                }
            }, 1000);
            
        } else {
            showError(data.detail || '智能处理启动失败');
            window.elements.startBatchBtn.disabled = false;
        }
    } catch (error) {
        console.error('智能处理失败:', error);
        showError('智能处理失败');
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
/**
 * 获取需要处理的照片数量
 * 包括imported和error状态的照片
 */
async function getPhotoCounts() {
    try {
        console.log('获取照片数量统计...');
        
        // 获取imported状态的照片数量
        const importedResponse = await fetch(`${window.CONFIG.API_BASE_URL}/photos?limit=1&filters=${encodeURIComponent(JSON.stringify({status: 'imported'}))}`);
        const importedData = await importedResponse.json();
        
        // 获取error状态的照片数量
        const errorResponse = await fetch(`${window.CONFIG.API_BASE_URL}/photos?limit=1&filters=${encodeURIComponent(JSON.stringify({status: 'error'}))}`);
        const errorData = await errorResponse.json();
        
        if (importedResponse.ok && errorResponse.ok) {
            const importedCount = importedData.total || 0;
            const errorCount = errorData.total || 0;
            const totalCount = importedCount + errorCount;
            
            console.log(`照片数量统计 - 未处理: ${importedCount}, 失败: ${errorCount}, 总计: ${totalCount}`);
            
            // 更新显示
            const photoCountInfo = document.getElementById('photoCountInfo');
            const photoCountText = document.getElementById('photoCountText');
            
            if (totalCount > 0) {
                photoCountText.innerHTML = `共有 <strong>${totalCount}</strong> 张照片需要处理（未处理: ${importedCount}张，失败重试: ${errorCount}张）`;
                photoCountInfo.style.display = 'block';
            } else {
                photoCountText.innerHTML = '所有照片都已完成智能处理';
                photoCountInfo.style.display = 'block';
            }
        } else {
            console.error('获取照片数量失败:', importedData, errorData);
            // 隐藏统计信息
            document.getElementById('photoCountInfo').style.display = 'none';
        }
    } catch (error) {
        console.error('获取照片数量异常:', error);
        // 隐藏统计信息
        document.getElementById('photoCountInfo').style.display = 'none';
    }
}

/**
 * 智能处理弹窗显示时的处理
 */
function onBatchModalShow() {
    console.log('智能处理弹窗显示，重置状态并获取照片数量...');
    
    // 重置智能处理模态框的状态
    resetBatchModalState();
    
    // 获取照片数量
    getPhotoCounts();
}

/**
 * 重置智能处理模态框的状态
 */
function resetBatchModalState() {
    // 重置进度条
    const progressBar = document.getElementById('batchProgressBar');
    if (progressBar) {
        progressBar.style.width = '0%';
    }
    
    // 重置状态文本
    const statusText = document.getElementById('batchStatus');
    if (statusText) {
        statusText.textContent = '准备开始处理...';
    }
    
    // 隐藏进度区域
    const progressArea = document.getElementById('batchProgress');
    if (progressArea) {
        progressArea.classList.add('d-none');
    }
    
    // 重置开始处理按钮状态
    const startBtn = document.getElementById('startBatchBtn');
    if (startBtn) {
        startBtn.disabled = false;
        startBtn.textContent = '开始处理';
    }
    
    console.log('智能处理模态框状态已重置');
}

// 添加弹窗显示事件监听器
document.addEventListener('DOMContentLoaded', function() {
    const batchModal = document.getElementById('batchModal');
    if (batchModal) {
        batchModal.addEventListener('shown.bs.modal', onBatchModalShow);
    }
});

window.startImport = startImport;
window.startFileImport = startFileImport;
window.startFolderImport = startFolderImport;
window.monitorScanProgress = monitorScanProgress;
window.startBatchProcess = startBatchProcess;
window.getPhotoCounts = getPhotoCounts;
window.resetBatchModalState = resetBatchModalState;
