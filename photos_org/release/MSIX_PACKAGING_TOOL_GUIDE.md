# MSIX Packaging Tool 使用详细指南

本文档详细说明如何使用 MSIX Packaging Tool 打包 PhotoSystem 应用。

---

## 📋 重要提示

MSIX Packaging Tool 有两种打包模式：

1. **"New package"（新建程序包）** - 用于将传统安装程序（.msi、.exe）转换为 MSIX
   - ⚠️ **不适用于我们的情况**

2. **"Application package"（应用程序包）** - 用于直接打包已准备好的应用程序目录
   - ✅ **这是我们需要的模式**

---

## 🚀 详细步骤

### 第一步：打开 MSIX Packaging Tool

1. 从开始菜单搜索 "MSIX Packaging Tool"
2. 打开应用程序

### 第二步：选择打包类型

在欢迎界面，选择 **"Application package"**（应用程序包）

⚠️ **重要**：不要选择 "New package"，那是用于转换安装程序的。

### 第三步：选择源目录

1. 在 "Select source location"（选择源位置）区域
2. 点击 "Browse..."（浏览）按钮
3. 导航到脚本准备好的目录：
   ```
   F:\Photos-System\photos_org\release\msix_build\PhotoSystem
   ```
4. **选择该目录**（注意：选择包含以下内容的目录）：
   - `PhotoSystem.exe` - 主程序
   - `AppxManifest.xml` - 应用清单文件
   - `Assets/` - 图标资源目录
   - `PhotoSystem/` - 应用文件目录

### 第四步：选择输出位置

1. 在 "Select output location"（选择输出位置）区域
2. 点击 "Browse..." 按钮
3. 选择要保存 MSIX 文件的目录
   - 建议：`F:\Photos-System\photos_org\release`
   - MSIX 文件名将自动生成，例如：`PhotoSystem_5.1.8.0.msix`

### 第五步：配置包信息

按照向导完成以下配置：

#### 5.1 Package Information（包信息）

- **Package name**（包名称）：
  - 默认：`PhotoSystem`
  - 可以保持默认，或修改为自定义名称

- **Version**（版本号）：
  - 输入：`5.1.8.0`
  - ⚠️ 必须与 `AppxManifest.xml` 中的版本号一致

- **Publisher**（发布者）：
  - 默认：`CN=Alpha_Xu`
  - ⚠️ 必须与 `AppxManifest.xml` 中的 Publisher 匹配
  - ⚠️ 必须与代码签名证书的发布者信息匹配

#### 5.2 Package Files（包文件）

- 工具会自动检测并包含以下文件：
  - `AppxManifest.xml` - 应用清单
  - `PhotoSystem.exe` - 主程序
  - `PhotoSystem/_internal/` - 所有依赖文件
  - `Assets/` - 图标资源
  - 其他配置文件

- **检查清单**：
  - ✅ 确保 `AppxManifest.xml` 已包含
  - ✅ 确保 `Assets/` 目录包含所有 5 个 PNG 图标文件
  - ✅ 确保所有必需的文件都已包含

#### 5.3 Signing（签名）

- **选项一：使用代码签名证书**（发布到 Microsoft Store 必需）
  - 选择 "Sign the package"（签名包）
  - 点击 "Browse..." 选择证书文件（.pfx）
  - 输入证书密码
  - ⚠️ 证书的发布者信息必须与 AppxManifest.xml 中的 Publisher 匹配

- **选项二：跳过签名**（仅用于本地测试）
  - 选择 "Skip signing"（跳过签名）
  - ⚠️ 未签名的包无法发布到 Microsoft Store
  - ⚠️ 未签名的包在安装时会有警告

### 第六步：创建包

1. 检查所有配置信息
2. 点击 "Create"（创建）按钮
3. 等待打包完成
   - 打包时间取决于文件大小（通常几分钟）
   - 可以在进度窗口中查看详细进度

### 第七步：验证生成的 MSIX 文件

1. 打包完成后，MSIX 文件将保存在输出目录
2. 文件名格式：`PhotoSystem_5.1.8.0.msix`（或类似格式）
3. 可以右键点击 MSIX 文件，选择 "安装" 进行测试

---

## 🔍 常见问题

### Q1: 我应该选择 "New package" 还是 "Application package"？

**A:** 选择 **"Application package"**。因为：
- 我们已经准备好了完整的应用程序目录
- 已经包含了 `AppxManifest.xml` 清单文件
- 不需要转换安装程序

### Q2: 如果选择 "New package" 会怎样？

**A:** 如果选择了 "New package"，工具会要求：
- 选择一个安装程序（.exe、.msi 等）
- 工具会运行安装程序并监视文件更改
- 这对于我们的便携式应用（无需安装）不适用

### Q3: 源目录应该选择哪个？

**A:** 选择脚本准备好的目录：
```
F:\Photos-System\photos_org\release\msix_build\PhotoSystem
```

这个目录包含：
- `PhotoSystem.exe` - 主程序
- `AppxManifest.xml` - 清单文件
- `Assets/` - 图标资源
- `PhotoSystem/` - 应用文件

### Q4: 版本号在哪里填写？

**A:** 版本号在 "Package Information" 步骤中填写：
- 输入：`5.1.8.0`
- 必须与 `AppxManifest.xml` 中的版本号一致

### Q5: 签名证书是必需的吗？

**A:** 
- **本地测试**：可以跳过签名
- **发布到 Microsoft Store**：必须使用有效的代码签名证书

### Q6: 打包后文件在哪里？

**A:** MSIX 文件保存在您在 "Select output location" 中指定的目录。

---

## 📝 检查清单

打包前，请确认：

- [ ] 已运行 `build_msix.py` 脚本准备打包目录
- [ ] `msix_build/PhotoSystem` 目录包含所有必需文件
- [ ] `Assets/` 目录包含所有 5 个 PNG 图标文件
- [ ] `AppxManifest.xml` 文件存在且配置正确
- [ ] 版本号与 `AppxManifest.xml` 中的版本号一致
- [ ] 如果有代码签名证书，证书的发布者信息与 AppxManifest.xml 匹配

---

## 🎯 快速参考

**源目录路径**：
```
F:\Photos-System\photos_org\release\msix_build\PhotoSystem
```

**输出目录**（建议）：
```
F:\Photos-System\photos_org\release
```

**版本号**：`5.1.8.0`

**发布者**：`CN=Alpha_Xu`

---

**最后更新**：2025年1月  
**版本**：5.1.8

