/**
 * 设置页面初始化脚本
 * 解决Edge浏览器加载混乱问题
 */

// JS文件版本号（与HTML中的?v=参数保持一致）
const SETTINGS_INIT_VERSION = '20250119_80';

// 清理模态框遮罩层
function cleanupModalBackdrops() {
    const backdrops = document.querySelectorAll('.modal-backdrop');
    if (backdrops.length > 0) {
        console.log('🧹 清理残留遮罩层');
        backdrops.forEach(backdrop => backdrop.remove());
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
    }
}

// 页面加载完成后清理遮罩层
document.addEventListener('DOMContentLoaded', () => {
    // 延迟清理，确保Bootstrap已加载
    setTimeout(cleanupModalBackdrops, 100);
});

// 页面完全加载后再次检查
window.addEventListener('load', () => {
    cleanupModalBackdrops();
});

// 导出清理函数到全局作用域
window.cleanupModalBackdrops = cleanupModalBackdrops;

// 注册版本号（用于版本检测）
if (typeof window.registerJSVersion === 'function') {
    window.registerJSVersion('settings-init.js', SETTINGS_INIT_VERSION);
}
