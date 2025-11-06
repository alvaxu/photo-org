# MSIX 打包指南

将 PyInstaller 打包的 ZIP 文件转换为 MSIX 格式，用于 Microsoft Store 发布。

---

## 📋 前置要求

### 1. 必需工具

- **Windows 10/11 SDK**（包含 `makeappx.exe` 和 `signtool.exe`）
  - 下载地址：https://developer.microsoft.com/windows/downloads/windows-sdk/
  - 或使用 Visual Studio Installer 安装 "Windows 10/11 SDK"

- **MSIX Packaging Tool**（可选，GUI 工具）
  - Microsoft Store 下载：https://www.microsoft.com/store/productId/9N5LW3JBCXKF

### 2. 代码签名证书（发布到 Microsoft Store 必需）

- **从证书颁发机构购买**（推荐）
  - DigiCert、GlobalSign、Sectigo 等
  - 费用：约 $200-400/年
  
- **或使用 Microsoft Store 开发者账号的证书**
  - 注册 Microsoft Partner Center 后可以获得

### 3. 应用资源文件

MSIX 需要以下 PNG 格式的图标和启动画面：

- `Logo.png` (150x150) - 应用图标
- `Square150x150Logo.png` (150x150) - 磁贴图标
- `Square44x44Logo.png` (44x44) - 小图标
- `Wide310x150Logo.png` (310x150) - 宽磁贴图标
- `SplashScreen.png` (620x300) - 启动画面

**转换 ICO 到 PNG（推荐方法）：**
```bash
# 方法一：使用项目提供的 Python 脚本（推荐，最简单）
cd release
convert_ico.bat

# 或直接运行 Python 脚本
python convert_ico_to_png.py

# 优点：无需安装额外工具，使用项目已有的 Pillow 库
# 自动生成所有所需尺寸，保持透明背景
```

---

## 🚀 快速开始

### 方法一：使用自动化脚本（推荐）

```bash
# 1. 转换 ICO 图标为 PNG 格式（如果还没有）
cd release
convert_ico.bat

# 2. 确保已生成 PhotoSystem-Portable.zip
build_installer_en.bat

# 3. 运行 MSIX 打包脚本
build_msix.bat
```

### 方法二：使用 Python 脚本

```bash
cd release

# 基本打包（使用 makeappx.exe）
python build_msix.py --zip PhotoSystem-Portable.zip --version 5.1.8.0

# 带代码签名
python build_msix.py --zip PhotoSystem-Portable.zip --version 5.1.8.0 \
    --cert certificate.pfx --cert-password "your_password"

# 使用 MSIX Packaging Tool（GUI）
python build_msix.py --zip PhotoSystem-Portable.zip --version 5.1.8.0 --packaging-tool
```

---

## 📝 详细步骤

### 步骤 1：准备应用资源

1. **转换 ICO 图标为 PNG 格式**（推荐使用项目提供的脚本）：
   ```bash
   cd release
   convert_ico.bat
   ```
   脚本会自动：
   - 读取 `xuwh.ico` 文件
   - 生成所有所需尺寸的 PNG 图标
   - 保存到 `Assets` 目录

2. **验证生成的图标文件**：
   ```bash
   dir Assets\*.png
   ```
   应该看到所有 5 个 PNG 文件

3. **手动转换（如果脚本不可用）**：
   - 使用在线工具或 Photoshop/GIMP
   - 将 `xuwh.ico` 转换为所需尺寸的 PNG
   - 放入 `Assets` 目录

### 步骤 2：配置 AppxManifest.xml

编辑 `release/AppxManifest.xml`，修改以下内容：

- **Identity Name**: 包标识符（反向域名格式）
- **Publisher**: 发布者信息（需要与证书匹配）
- **Version**: 版本号（格式：主.次.构建.修订）
- **DisplayName**: 应用显示名称
- **Description**: 应用描述

### 步骤 3：运行打包脚本

```bash
# Windows
build_msix.bat

# 或直接使用 Python
python build_msix.py --zip PhotoSystem-Portable.zip --version 5.1.8.0
```

### 步骤 4：代码签名（可选但推荐）

```bash
python build_msix.py \
    --zip PhotoSystem-Portable.zip \
    --version 5.1.8.0 \
    --cert "path/to/certificate.pfx" \
    --cert-password "your_password"
```

### 步骤 5：使用 MSIX Packaging Tool（GUI 方式）

如果使用 MSIX Packaging Tool 进行打包，按照以下步骤操作：

#### 5.1 打开 MSIX Packaging Tool

1. 从开始菜单搜索并打开 "MSIX Packaging Tool"
2. 在欢迎界面，选择 **"Application package"**（应用程序包）
   - ⚠️ **重要**：不要选择 "New package"（新建程序包），那是用于转换传统安装程序的

#### 5.2 选择源目录

1. 在 "Select source location"（选择源位置）中
2. 点击 "Browse..."（浏览）按钮
3. 导航到脚本准备好的目录：
   ```
   F:\Photos-System\photos_org\release\msix_build\PhotoSystem
   ```
4. 选择该目录（注意：选择包含 `PhotoSystem.exe` 和 `AppxManifest.xml` 的目录）

#### 5.3 选择输出位置

1. 在 "Select output location"（选择输出位置）中
2. 点击 "Browse..." 按钮
3. 选择要保存 MSIX 文件的目录（例如：`release` 目录）

#### 5.4 配置打包选项

按照向导完成以下步骤：

- **Package information**（包信息）：
  - 包名称：`PhotoSystem`（或保持默认）
  - 版本号：`5.1.8.0`（应与 AppxManifest.xml 中的版本号一致）
  - 发布者：`CN=Alpha_Xu`（应与 AppxManifest.xml 中的 Publisher 匹配）

- **Package files**（包文件）：
  - 工具会自动检测 `AppxManifest.xml` 和所有文件
  - 确保所有文件都包含在内

- **Signing**（签名）：
  - 如果有代码签名证书，选择证书文件（.pfx）
  - 如果没有证书，可以选择 "Skip signing"（跳过签名）
  - ⚠️ 注意：发布到 Microsoft Store 需要有效证书

#### 5.5 完成打包

1. 检查所有配置
2. 点击 "Create"（创建）按钮
3. 等待打包完成
4. MSIX 文件将保存在指定的输出目录

### 步骤 6：验证 MSIX 包

```bash
# 安装并测试
powershell Add-AppxPackage -Path PhotoSystem_5_1_8_0.msix

# 卸载（测试后）
powershell Remove-AppxPackage -PackageName com.alphaxu.PhotoSystem
```

---

## 🔧 配置说明

### AppxManifest.xml 关键配置

#### 1. 包标识

```xml
<Identity
    Name="com.alphaxu.PhotoSystem"
    Publisher="CN=Alpha_Xu"
    Version="5.1.8.0" />
```

- **Name**: 包的唯一标识符（反向域名格式）
- **Publisher**: 发布者（必须与代码签名证书匹配）
- **Version**: 版本号（每次更新必须递增）

#### 2. 功能声明

```xml
<Capabilities>
    <!-- 文件系统访问 -->
    <rescap:Capability Name="broadFileSystemAccess" />
    
    <!-- 网络访问 -->
    <Capability Name="internetClient" />
    <Capability Name="privateNetworkClientServer" />
</Capabilities>
```

根据应用需求声明所需权限。

#### 3. 应用入口

```xml
<Application Id="PhotoSystem"
             Executable="PhotoSystem.exe"
             EntryPoint="Windows.FullTrustApplication">
```

- **Executable**: 主程序文件名
- **EntryPoint**: 桌面桥接应用使用 `Windows.FullTrustApplication`

---

## 📦 发布到 Microsoft Store

### 1. 注册开发者账号

- 访问：https://partner.microsoft.com/
- 注册 Microsoft Partner Center 账号
- 支付开发者注册费用（一次性 $19 或年费 $99）

### 2. 创建应用

1. 登录 Partner Center
2. 创建新应用
3. 填写应用信息（名称、描述、分类等）
4. 上传应用图标和截图

### 3. 提交 MSIX 包

1. 在 "包" 部分上传 `.msix` 文件
2. 填写版本说明
3. 提交审核

### 4. 审核流程

- Microsoft Store 团队会审核应用
- 审核时间：通常 1-7 个工作日
- 审核通过后，应用将上架

---

## ⚠️ 注意事项

### 1. 版本号管理

- 每次更新必须递增版本号
- 格式：`主版本.次版本.构建号.修订号`
- 例如：`5.1.8.0` → `5.1.9.0` → `5.2.0.0`

### 2. 代码签名

- Microsoft Store 发布需要有效代码签名证书
- 证书的发布者信息必须与 AppxManifest.xml 中的 Publisher 匹配
- 证书过期后需要重新签名

### 3. 权限声明

- 只声明应用实际需要的权限
- 某些权限（如 `broadFileSystemAccess`）需要额外审核
- 权限声明会影响用户安装时的提示

### 4. 文件路径

- MSIX 应用在沙箱环境中运行
- 某些文件路径可能需要适配
- 使用 Windows.Storage API 访问用户数据

### 5. 测试

- 在本地测试安装和运行
- 验证所有功能正常
- 检查权限是否足够

---

## 🐛 常见问题

### Q1: 图标转换失败

**A:** 
- 确保 `xuwh.ico` 文件存在于 `release` 目录
- 检查是否安装了 Pillow：`pip install Pillow`
- 如果使用 ImageMagick 失败，请使用项目提供的 Python 脚本：`convert_ico.bat`
- 查看错误信息，确认文件路径和权限

### Q2: 找不到 makeappx.exe

**A:** 安装 Windows SDK：
- 下载 Windows SDK：https://developer.microsoft.com/windows/downloads/windows-sdk/
- 或使用 Visual Studio Installer 安装 "Windows 10/11 SDK"

### Q3: 签名失败

**A:** 检查：
- 证书文件路径是否正确
- 证书密码是否正确
- 证书是否已过期
- Publisher 信息是否与证书匹配

### Q4: 安装失败

**A:** 可能原因：
- 版本号未递增
- 包已损坏
- 签名无效
- 权限不足

### Q5: 应用无法访问文件系统

**A:** MSIX 应用在沙箱中运行：
- 检查是否声明了 `broadFileSystemAccess` 权限
- 用户需要手动授予文件系统访问权限（首次运行时）

### Q6: 如何更新应用

**A:** 
- 递增版本号
- 重新打包 MSIX
- 提交到 Microsoft Store
- 用户将自动收到更新通知

---

## 📚 参考资源

- [MSIX 打包文档](https://docs.microsoft.com/windows/msix/)
- [Microsoft Store 发布指南](https://docs.microsoft.com/windows/uwp/publish/)
- [AppxManifest 参考](https://docs.microsoft.com/uwp/schemas/appxpackage/appx-manifest)
- [代码签名指南](https://docs.microsoft.com/windows/msix/package/packaging-uwp-apps)

---

## 📞 技术支持

如有问题，请参考：
- Microsoft Store 开发者支持：https://docs.microsoft.com/windows/uwp/publish/
- MSIX 社区：https://github.com/microsoft/msix-packaging

---

**最后更新：** 2025年1月  
**版本：** 5.1.8

