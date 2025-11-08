# MSIX 应用资源文件

本目录包含 MSIX 打包所需的应用图标和启动画面资源。

## 📋 必需文件

请将以下 PNG 格式的文件放入此目录：

1. **Logo.png** (150x150)
   - 应用主图标
   - 用于应用列表和设置页面

2. **Square150x150Logo.png** (150x150)
   - 方形磁贴图标
   - 用于开始菜单磁贴

3. **Square44x44Logo.png** (44x44)
   - 小图标
   - 用于任务栏和应用切换器

4. **Wide310x150Logo.png** (310x150)
   - 宽磁贴图标
   - 用于宽磁贴布局

5. **SplashScreen.png** (620x300)
   - 启动画面
   - 应用启动时显示

## 🛠️ 转换 ICO 到 PNG

如果已有 `xuwh.ico` 图标文件，可以使用以下方法转换：

### 方法一：使用 Python 脚本（推荐，最简单）

项目已包含自动转换脚本，使用项目已有的 Pillow 库：

```bash
# Windows - 一键转换
convert_ico.bat

# 或直接使用 Python 脚本
python convert_ico_to_png.py

# 指定 ICO 文件路径
python convert_ico_to_png.py --ico path/to/icon.ico
```

**优点：**
- ✅ 无需安装额外工具
- ✅ 使用项目已有的 Pillow 库
- ✅ 自动生成所有所需尺寸
- ✅ 保持透明背景

### 方法二：使用 ImageMagick（如果已安装）

```bash
# 转换图标
magick convert ..\xuwh.ico -resize 150x150 Logo.png
magick convert ..\xuwh.ico -resize 150x150 Square150x150Logo.png
magick convert ..\xuwh.ico -resize 44x44 Square44x44Logo.png
magick convert ..\xuwh.ico -resize 310x150 Wide310x150Logo.png
magick convert ..\xuwh.ico -resize 620x300 SplashScreen.png
```

### 方法三：使用在线工具

1. 访问在线 ICO 转 PNG 工具
2. 上传 `xuwh.ico`
3. 下载不同尺寸的 PNG 文件
4. 重命名为对应文件名

### 方法四：使用 Photoshop/GIMP

1. 打开 `xuwh.ico`
2. 导出为 PNG 格式
3. 调整到所需尺寸
4. 保存为对应文件名

## 📝 注意事项

- 所有文件必须是 **PNG 格式**
- 尺寸必须精确匹配（不能有偏差）
- 建议使用透明背景
- 图标应清晰，避免模糊
- 启动画面建议使用应用的主题色

## ✅ 验证

打包前请确认所有文件已存在：

```bash
dir /b Assets\*.png
```

应该看到：
- Logo.png
- Square150x150Logo.png
- Square44x44Logo.png
- Wide310x150Logo.png
- SplashScreen.png

如果文件缺失，MSIX 打包可能会失败或显示默认图标。

