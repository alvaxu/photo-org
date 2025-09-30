// 高德地图API配置页面脚本
// static/js/help_gaode_api_key.js

/**
 * 高德地图API配置页面专用脚本
 * 处理API Key的测试和保存功能
 */

// 页面初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('高德API配置页面已加载');

    // 绑定表单提交事件
    const apiKeyForm = document.getElementById('apiKeyForm');
    if (apiKeyForm) {
        apiKeyForm.addEventListener('submit', handleApiKeySave);
    }

    // 加载当前配置
    loadCurrentApiKey();
});

/**
 * 加载当前配置的API Key
 */
async function loadCurrentApiKey() {
    try {
        const response = await fetch('/api/maps/config');
        if (response.ok) {
            const config = await response.json();
            const apiKeyInput = document.getElementById('apiKey');
            if (config.api_key && apiKeyInput) {
                apiKeyInput.value = config.api_key;
            }
        }
    } catch (error) {
        console.error('加载API Key失败:', error);
    }
}

/**
 * 处理API Key保存
 */
async function handleApiKeySave(event) {
    event.preventDefault();

    const apiKey = document.getElementById('apiKey').value.trim();
    const saveBtn = document.getElementById('saveBtn');

    if (!validateApiKey(apiKey)) {
        showResult('请输入有效的32位API Key', 'danger');
        return;
    }

    // 显示保存中状态
    const originalText = saveBtn.innerHTML;
    setButtonLoading(saveBtn, true, '保存中...');

    try {
        const response = await fetch('/api/maps/config', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({api_key: apiKey})
        });

        const result = await response.json();

        if (response.ok) {
            showResult('API Key配置成功！', 'success');
        } else {
            showResult(`配置失败：${result.detail}`, 'danger');
        }

    } catch (error) {
        showResult('保存失败，请检查网络', 'danger');
    } finally {
        setButtonLoading(saveBtn, false, originalText);
    }
}

/**
 * 测试API Key
 */
async function testApiKey() {
    const apiKey = document.getElementById('apiKey').value.trim();
    const testBtn = document.getElementById('testBtn');

    if (!validateApiKey(apiKey)) {
        showResult('请输入有效的32位API Key', 'danger');
        return;
    }

    // 显示测试中状态
    const originalText = testBtn.innerHTML;
    setButtonLoading(testBtn, true, '测试中...');

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
            showResult(`API Key测试成功！地址：${result.address}`, 'success');
        } else {
            showResult(`API Key测试失败：${result.detail}`, 'danger');
        }

    } catch (error) {
        showResult('测试请求失败，请检查网络', 'danger');
    } finally {
        setButtonLoading(testBtn, false, originalText);
    }
}

/**
 * 验证API Key格式
 */
function validateApiKey(apiKey) {
    return apiKey && apiKey.length === 32;
}

/**
 * 显示结果消息
 */
function showResult(message, type) {
    const resultDiv = document.getElementById('testResult');
    const messageSpan = document.getElementById('testMessage');
    const alertDiv = resultDiv.querySelector('.alert');

    if (messageSpan && alertDiv) {
        messageSpan.textContent = message;
        alertDiv.className = `alert alert-${type}`;
        resultDiv.style.display = 'block';

        // 自动隐藏成功消息
        if (type === 'success') {
            setTimeout(() => {
                resultDiv.style.display = 'none';
            }, 5000);
        }
    }
}

/**
 * 设置按钮加载状态
 */
function setButtonLoading(button, loading, text) {
    if (!button) return;

    button.disabled = loading;
    if (loading) {
        button.innerHTML = `<i class="bi bi-hourglass-split"></i> ${text}`;
    } else {
        button.innerHTML = text;
    }
}

/**
 * 显示Toast提示
 */
function showToast(message, type = 'info') {
    // 如果有全局Toast函数，使用它；否则使用alert
    if (typeof showToast === 'function' && showToast !== this.showToast) {
        window.showToast(message, type);
    } else {
        alert(message);
    }
}

// 导出函数供HTML内联脚本调用
window.testApiKey = testApiKey;
window.handleApiKeySave = handleApiKeySave;
