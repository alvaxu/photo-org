/**
 * 家庭版智能照片系统 - 事件处理模块
 * 
 * 功能：
 * 1. 基础事件监听器绑定
 * 2. 文件选择事件处理
 * 3. 键盘事件处理
 * 4. 导入相关事件处理
 */

/**
 * 绑定基础事件监听器
 */
function bindBasicEvents() {
    console.log('🔗 绑定基础事件监听器');
    console.log('🔍 检查DOM元素:', {
        browseFolderBtn: window.elements.browseFolderBtn,
        folderFilesInput: document.getElementById('folderFiles')
    });

    // 导航事件
    window.elements.navPhotos.addEventListener('click', (e) => {
        e.preventDefault();
        switchSection('photos');
    });

    // 导入相关事件
    window.elements.importFirstBtn.addEventListener('click', showImportModal);
    window.elements.photoFiles.addEventListener('change', handleFileSelection);
    window.elements.startImportBtn.addEventListener('click', startImport);
    
    // 导入方式切换事件
    window.elements.fileImport.addEventListener('change', () => switchImportMethod('file'));
    window.elements.folderImport.addEventListener('change', () => switchImportMethod('folder'));
    window.elements.folderPath.addEventListener('input', handleFolderPathChange);
    
    // 浏览文件夹按钮事件
    console.log('🔗 绑定浏览文件夹按钮事件:', window.elements.browseFolderBtn);
    if (window.elements.browseFolderBtn) {
        window.elements.browseFolderBtn.addEventListener('click', browseFolder);
        console.log('✅ 浏览文件夹按钮事件绑定成功');
    } else {
        console.error('❌ 找不到浏览文件夹按钮');
    }
    
    // 绑定文件夹选择事件
    const folderFilesInput = document.getElementById('folderFiles');
    if (folderFilesInput) {
        folderFilesInput.addEventListener('change', handleFolderSelection);
    }

    // 智能处理事件
    // 注意：batchBtn 使用 data-bs-toggle="modal" 自动处理，不需要手动监听
    window.elements.startBatchBtn.addEventListener('click', startBatchProcess);
    
    // 添加调试信息
    console.log('智能处理按钮绑定状态:', {
        batchBtn: !!window.elements.batchBtn,
        startBatchBtn: !!window.elements.startBatchBtn
    });

    // 选择操作事件
    window.elements.selectAllBtn.addEventListener('click', selectAllPhotos);
    window.elements.clearSelectionBtn.addEventListener('click', clearSelection);
    window.elements.deleteSelectedBtn.addEventListener('click', deleteSelectedPhotos);

    // 键盘快捷键
    document.addEventListener('keydown', handleKeyboard);
}

/**
 * 处理文件选择事件
 * 
 * @param {Event} event - 文件选择事件
 */
function handleFileSelection(event) {
    const files = event.target.files;
    
    if (files && files.length > 0) {
        // 更新导入按钮状态
        elements.startImportBtn.disabled = false;
        
        // 显示选择的文件数量
        const imageFiles = Array.from(files).filter(file => file.type.startsWith('image/'));
        console.log(`选择了 ${imageFiles.length} 个图片文件`);
        
        // 显示选择结果
        // 已删除选择文件的通知，避免冗余
    }
}

/**
 * 处理键盘事件
 * 
 * @param {KeyboardEvent} event - 键盘事件
 */
function handleKeyboard(event) {
    // Ctrl+A 全选
    if (event.ctrlKey && event.key === 'a') {
        event.preventDefault();
        selectAllPhotos();
    }
    
    // ESC 取消选择
    if (event.key === 'Escape') {
        clearSelection();
    }
    
    // Delete 删除选中
    if (event.key === 'Delete') {
        const selectedIds = window.PhotoManager ? window.PhotoManager.getSelectedPhotoIds() : [];
        if (selectedIds.length > 0) {
            deleteSelectedPhotos();
        }
    }
}

// ============ 全局导出 ============

// 将函数导出到全局作用域
window.bindBasicEvents = bindBasicEvents;
window.handleFileSelection = handleFileSelection;
window.handleKeyboard = handleKeyboard;
