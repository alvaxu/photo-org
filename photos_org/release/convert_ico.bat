@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title PhotoSystem ICO 转 PNG 转换工具

echo.
echo ========================================
echo PhotoSystem ICO 转 PNG 图标转换工具
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

REM 检查 ICO 文件
set "ICO_FILE=xuwh.ico"
if not exist "%ICO_FILE%" (
    echo ERROR: 未找到 ICO 文件: %ICO_FILE%
    echo 请确保 xuwh.ico 文件在当前目录
    pause
    exit /b 1
)

echo [INFO] 找到 ICO 文件: %ICO_FILE%
echo.

REM 检查转换脚本
if not exist "convert_ico_to_png.py" (
    echo ERROR: 未找到 convert_ico_to_png.py
    pause
    exit /b 1
)

echo [INFO] 开始转换图标...
echo.

REM 运行 Python 脚本
python convert_ico_to_png.py --ico "%ICO_FILE%"

if errorlevel 1 (
    echo.
    echo ERROR: 图标转换失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo [SUCCESS] 图标转换完成！
echo ========================================
echo.
echo 生成的 PNG 文件已保存在 Assets 目录
echo 下一步：运行 build_msix.bat 进行 MSIX 打包
echo.

pause

