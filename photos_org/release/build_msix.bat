@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title PhotoSystem MSIX Packaging Script

echo.
echo ========================================
echo PhotoSystem MSIX 打包脚本
echo ========================================
echo.

REM 检查 Python 环境
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python 未找到
    echo 请安装 Python 3.8+ 并添加到 PATH
    pause
    exit /b 1
)

echo [INFO] Python 环境检查通过
echo.

REM 检查 ZIP 文件是否存在
set "ZIP_FILE=PhotoSystem-Portable.zip"
if not exist "%ZIP_FILE%" (
    echo ERROR: 未找到 ZIP 文件: %ZIP_FILE%
    echo 请先运行 build_installer_en.bat 生成 ZIP 文件
    pause
    exit /b 1
)

echo [INFO] 找到 ZIP 文件: %ZIP_FILE%
echo.

REM 检查 build_msix.py 是否存在
if not exist "build_msix.py" (
    echo ERROR: 未找到 build_msix.py
    pause
    exit /b 1
)

echo [INFO] 开始 MSIX 打包流程...
echo.

REM 运行 Python 脚本
python build_msix.py --zip "%ZIP_FILE%" --version 6.0.0.0

if errorlevel 1 (
    echo.
    echo ERROR: MSIX 打包失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo [SUCCESS] MSIX 打包完成！
echo ========================================
echo.
echo 下一步操作：
echo    1. 检查生成的 .msix 文件
echo    2. 如需代码签名，请使用 --cert 参数
echo    3. 提交到 Microsoft Store Partner Center
echo.
echo 示例签名命令：
echo    python build_msix.py --zip "%ZIP_FILE%" --version 6.0.0.0 --cert certificate.pfx --cert-password "your_password"
echo.

pause

