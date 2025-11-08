"""
MSIX 打包脚本

将 PyInstaller 打包的 ZIP 文件转换为 MSIX 格式，用于 Microsoft Store 发布。

功能：
1. 解压 PhotoSystem-Portable.zip
2. 准备 MSIX 打包所需的目录结构
3. 复制 AppxManifest.xml
4. 准备应用资源（图标、启动画面等）
5. 调用 MSIX Packaging Tool 或 makeappx.exe 创建 MSIX 包
6. 可选：代码签名

作者：AI助手
创建日期：2025年1月
"""

import os
import sys
import shutil
import zipfile
import subprocess
import xml.etree.ElementTree as ET
import time
import re
from pathlib import Path
from typing import Optional, Tuple
import argparse


class MSIXBuilder:
    """MSIX 打包构建器"""
    
    def __init__(self, zip_path: str, output_dir: str = None, version: str = "6.0.0.0", publisher: str = None):
        """
        初始化 MSIX 构建器
        
        :param zip_path: PyInstaller 生成的 ZIP 文件路径
        :param output_dir: 输出目录（默认为 release 目录）
        :param version: 应用版本号（格式：主版本.次版本.构建号.修订号）
        :param publisher: Publisher 名称（可选，用于覆盖 AppxManifest.xml 中的 Publisher）
        """
        self.zip_path = Path(zip_path)
        self.version = version
        self.publisher = publisher
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).parent
        self.work_dir = self.output_dir / "msix_build"
        self.app_dir = self.work_dir / "PhotoSystem"
        self.assets_dir = self.app_dir / "Assets"
        
    def prepare_work_directory(self):
        """准备工作目录"""
        print("📁 准备工作目录...")
        
        # 清理旧的工作目录
        if self.work_dir.exists():
            print(f"🗑️  清理旧的工作目录: {self.work_dir}")
            try:
                # 尝试删除目录
                shutil.rmtree(self.work_dir)
                print("✅ 旧目录已删除")
            except PermissionError as e:
                print(f"⚠️  无法删除旧目录（可能被其他程序占用）: {e}")
                print("   尝试重命名旧目录...")
                try:
                    # 尝试重命名旧目录
                    old_dir = self.work_dir.with_name(f"{self.work_dir.name}_old_{int(time.time())}")
                    self.work_dir.rename(old_dir)
                    print(f"✅ 旧目录已重命名为: {old_dir}")
                except Exception as rename_error:
                    print(f"❌ 重命名也失败: {rename_error}")
                    print(f"   请手动删除或重命名目录: {self.work_dir}")
                    raise PermissionError(
                        f"无法清理工作目录。请手动删除或重命名:\n"
                        f"   {self.work_dir}\n"
                        f"   然后重新运行脚本。"
                    )
            except Exception as e:
                print(f"⚠️  清理目录时出错: {e}")
                print("   尝试继续...")
        
        # 创建目录结构
        try:
            self.work_dir.mkdir(parents=True, exist_ok=True)
            self.app_dir.mkdir(parents=True, exist_ok=True)
            self.assets_dir.mkdir(parents=True, exist_ok=True)
            print(f"✅ 工作目录已创建: {self.work_dir}")
        except PermissionError as e:
            print(f"❌ 创建目录失败（权限不足）: {e}")
            print(f"   目标目录: {self.work_dir}")
            print()
            print("💡 解决方案：")
            print("   1. 检查目录权限，确保有写入权限")
            print("   2. 关闭可能占用该目录的程序（如文件管理器、MSIX Packaging Tool 等）")
            print("   3. 尝试以管理员身份运行脚本")
            print("   4. 或者手动删除/重命名以下目录：")
            print(f"      {self.work_dir}")
            raise
        except Exception as e:
            print(f"❌ 创建目录时出错: {e}")
            raise
        
    def extract_zip(self):
        """解压 ZIP 文件并整理目录结构"""
        print(f"📦 解压 ZIP 文件: {self.zip_path}")
        
        if not self.zip_path.exists():
            raise FileNotFoundError(f"ZIP 文件不存在: {self.zip_path}")
        
        # 创建临时解压目录
        temp_extract_dir = self.work_dir / "temp_extract"
        temp_extract_dir.mkdir(parents=True, exist_ok=True)
        
        # 解压到临时目录
        with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_extract_dir)
        
        print(f"✅ ZIP 文件已解压到临时目录: {temp_extract_dir}")
        
        # 查找主要的可执行文件（保持原始目录结构）
        main_exe = None
        possible_exe_names = ["PhotoSystem.exe", "main.exe", "app.exe"]
        
        # 检查是否有 PhotoSystem 子目录（PyInstaller 打包的常见结构）
        photo_system_dir = temp_extract_dir / "PhotoSystem"
        if photo_system_dir.exists() and photo_system_dir.is_dir():
            print(f"📁 发现 PhotoSystem 子目录，保持原始目录结构...")
            # 将整个 PhotoSystem 目录移动到 app_dir（保持目录结构）
            dest_photo_system = self.app_dir / "PhotoSystem"
            if dest_photo_system.exists():
                shutil.rmtree(dest_photo_system)
            shutil.move(str(photo_system_dir), str(dest_photo_system))
            print(f"   ✅ 已移动 PhotoSystem 目录（保持原始结构）")
            
            # 在 PhotoSystem 目录中查找可执行文件
            for exe_name in possible_exe_names:
                exe_path = dest_photo_system / exe_name
                if exe_path.exists():
                    main_exe = f"PhotoSystem/{exe_name}"
                    print(f"   ✅ 找到主可执行文件: {main_exe}")
                    break
            
            if main_exe is None:
                # 尝试查找 PhotoSystem 目录中的任何 .exe 文件
                exe_files = list(dest_photo_system.glob("*.exe"))
                if exe_files:
                    exe_rel = exe_files[0].relative_to(self.app_dir)
                    main_exe = str(exe_rel).replace("\\", "/")
                    print(f"   ✅ 找到可执行文件: {main_exe}")
        else:
            # 如果没有子目录，直接将所有内容移动到 app_dir
            print(f"📁 未发现子目录，直接移动所有内容...")
            for item in temp_extract_dir.iterdir():
                if item.name == "temp_extract":
                    continue
                dest = self.app_dir / item.name
                if dest.exists():
                    if dest.is_file():
                        dest.unlink()
                    else:
                        shutil.rmtree(dest)
                shutil.move(str(item), str(dest))
            
            # 在根目录查找可执行文件
            for exe_name in possible_exe_names:
                exe_path = self.app_dir / exe_name
                if exe_path.exists():
                    main_exe = exe_name
                    print(f"   ✅ 找到主可执行文件: {exe_name}")
                    break
            
            if main_exe is None:
                # 尝试查找任何 .exe 文件
                exe_files = list(self.app_dir.glob("*.exe"))
                if exe_files:
                    main_exe = exe_files[0].name
                    print(f"   ✅ 找到可执行文件: {main_exe}")
        
        # 清理临时目录
        try:
            shutil.rmtree(temp_extract_dir)
        except:
            pass
        
        if main_exe is None:
            print("⚠️  警告: 未找到可执行文件，请检查 ZIP 文件结构")
            main_exe = "PhotoSystem/PhotoSystem.exe"  # 默认值
        
        print(f"✅ ZIP 文件已解压到: {self.app_dir}（保持原始目录结构）")
        return main_exe
        
    def prepare_manifest(self, executable_name: str = "PhotoSystem.exe"):
        """
        准备 AppxManifest.xml
        
        使用字符串替换方式更新版本号和可执行文件名，避免破坏 XML 格式和命名空间声明
        """
        print("📄 准备 AppxManifest.xml...")
        
        manifest_source = Path(__file__).parent / "AppxManifest.xml"
        if not manifest_source.exists():
            raise FileNotFoundError(f"AppxManifest.xml 模板不存在: {manifest_source}")
        
        # 读取原始 XML 内容
        with open(manifest_source, 'r', encoding='utf-8') as f:
            manifest_content = f.read()
        
        # 使用正则表达式更新版本号（只匹配 Identity 标签中的 Version 属性，避免误修改 MinVersion/MaxVersionTested）
        # 匹配 <Identity ... Version="x.x.x.x" ... /> 格式，确保只匹配 Identity 标签内的 Version
        identity_version_pattern = r'(<Identity[^>]*Version=")[^"]*(")'
        manifest_content = re.sub(identity_version_pattern, rf'\g<1>{self.version}\g<2>', manifest_content)
        print(f"   ✅ 更新 Identity 版本号为: {self.version}")
        
        # 使用正则表达式更新可执行文件名（匹配 Executable="xxx.exe" 格式）
        executable_pattern = r'Executable="[^"]*"'
        manifest_content = re.sub(executable_pattern, f'Executable="{executable_name}"', manifest_content)
        print(f"   ✅ 更新可执行文件路径为: {executable_name}")
        
        # 保存到工作目录
        manifest_dest = self.app_dir / "AppxManifest.xml"
        with open(manifest_dest, 'w', encoding='utf-8') as f:
            f.write(manifest_content)
        
        print(f"✅ AppxManifest.xml 已准备: {manifest_dest}")
        
    def prepare_assets(self):
        """准备应用资源（图标、启动画面等）"""
        print("🖼️  准备应用资源...")
        
        # 定义需要的所有 PNG 资源文件
        required_assets = [
            "Logo.png",
            "Square150x150Logo.png",
            "Square44x44Logo.png",
            "Wide310x150Logo.png",
            "SplashScreen.png",
        ]
        
        assets_source_dir = Path(__file__).parent / "Assets"
        assets_copied = 0
        assets_missing = []
        
        # 从 release/Assets 目录复制所有 PNG 文件
        for asset_name in required_assets:
            asset_source = assets_source_dir / asset_name
            asset_dest = self.assets_dir / asset_name
            
            if asset_source.exists():
                try:
                    shutil.copy2(asset_source, asset_dest)
                    assets_copied += 1
                    print(f"   ✅ {asset_name} - 已复制")
                except Exception as e:
                    print(f"   ❌ {asset_name} - 复制失败: {e}")
                    assets_missing.append(asset_name)
            else:
                print(f"   ⚠️  {asset_name} - 源文件不存在: {asset_source}")
                assets_missing.append(asset_name)
        
        # 检查是否所有文件都已复制
        if assets_missing:
            print()
            print("⚠️  警告: 以下资源文件缺失或复制失败:")
            for asset in assets_missing:
                print(f"   - {asset}")
            print()
            print("💡 解决方案:")
            print("   1. 运行 convert_ico.bat 生成所有 PNG 图标文件")
            print("   2. 确保 release/Assets 目录包含所有必需的 PNG 文件")
            print()
        else:
            print()
            print(f"✅ 所有 {assets_copied} 个资源文件已成功复制到 Assets 目录")
        
        print(f"📁 Assets 目录: {self.assets_dir}")
        
        # 处理使用说明.pdf（覆盖解压包中的同名文件）
        pdf_source = assets_source_dir / "使用说明.pdf"
        if pdf_source.exists():
            print("\n📄 处理使用说明.pdf...")
            # 在解压包中查找已存在的使用说明.pdf
            existing_pdf = None
            for pdf_path in self.app_dir.rglob("使用说明.pdf"):
                existing_pdf = pdf_path
                break
            
            if existing_pdf:
                # 覆盖已存在的文件
                try:
                    shutil.copy2(pdf_source, existing_pdf)
                    print(f"   ✅ 已覆盖: {existing_pdf.relative_to(self.app_dir)}")
                except Exception as e:
                    print(f"   ❌ 覆盖失败: {e}")
            else:
                # 如果不存在，复制到 Assets 目录
                pdf_dest = self.assets_dir / "使用说明.pdf"
                try:
                    shutil.copy2(pdf_source, pdf_dest)
                    print(f"   ✅ 已复制到 Assets 目录: {pdf_dest.relative_to(self.app_dir)}")
                except Exception as e:
                    print(f"   ❌ 复制失败: {e}")
        else:
            print(f"\n⚠️  使用说明.pdf 源文件不存在: {pdf_source}")
        
        # 创建 MSIX 标记文件（用于运行时环境检测）
        # 注意：标记文件应该与 PhotoSystem.exe 在同一目录
        # 检查是否存在 PhotoSystem 子目录（从 ZIP 解压出来的应用目录）
        photo_system_subdir = self.app_dir / "PhotoSystem"
        if photo_system_subdir.exists() and photo_system_subdir.is_dir():
            # 如果存在 PhotoSystem 子目录，将标记文件放在那里（与 PhotoSystem.exe 同目录）
            marker_file = photo_system_subdir / '.msix'
            print(f"📁 检测到 PhotoSystem 子目录，标记文件将放在: {marker_file.relative_to(self.app_dir)}")
        else:
            # 否则放在 app_dir 根目录
            marker_file = self.app_dir / '.msix'
            print(f"📁 未检测到 PhotoSystem 子目录，标记文件将放在: {marker_file.relative_to(self.app_dir)}")
        
        try:
            marker_file.touch()
            print(f"✅ 已创建 MSIX 标记文件: {marker_file.relative_to(self.app_dir)}")
        except Exception as e:
            print(f"⚠️  创建 MSIX 标记文件失败: {e}")
    
    def verify_package_contents(self):
        """验证打包内容，统计文件数量和大小"""
        print("\n📊 验证打包内容...")
        
        total_files = 0
        total_size = 0
        exe_files = []
        dirs = []
        
        # 统计所有文件（包括 Assets 目录，但单独统计清单文件）
        for item in self.app_dir.rglob("*"):
            if item.is_file():
                # 清单文件单独处理
                if item.name == "AppxManifest.xml":
                    continue
                
                total_files += 1
                size = item.stat().st_size
                total_size += size
                
                if item.suffix.lower() == ".exe":
                    exe_files.append(item.relative_to(self.app_dir))
            elif item.is_dir() and item != self.app_dir:
                rel_path = item.relative_to(self.app_dir)
                if rel_path != Path("Assets"):
                    dirs.append(rel_path)
        
        # 显示统计信息
        print(f"   📁 文件总数: {total_files:,} 个")
        print(f"   💾 总大小: {total_size / 1024 / 1024:.2f} MB")
        
        if exe_files:
            print(f"   🔧 可执行文件 ({len(exe_files)} 个):")
            for exe in exe_files[:5]:  # 只显示前5个
                exe_path = self.app_dir / exe
                size = exe_path.stat().st_size
                print(f"      - {exe} ({size / 1024 / 1024:.2f} MB)")
            if len(exe_files) > 5:
                print(f"      ... 还有 {len(exe_files) - 5} 个可执行文件")
        
        # 显示主要目录
        if dirs:
            print(f"   📂 主要目录 ({len(dirs)} 个):")
            for dir_path in sorted(set([d.parts[0] for d in dirs]))[:10]:  # 只显示顶层目录
                print(f"      - {dir_path}/")
            if len(dirs) > 10:
                print(f"      ... 还有更多目录")
        
        # 验证关键文件
        print("\n   ✅ 关键文件检查:")
        manifest_path = self.app_dir / "AppxManifest.xml"
        if manifest_path.exists():
            print(f"      ✅ AppxManifest.xml 存在")
        else:
            print(f"      ❌ AppxManifest.xml 缺失")
        
        assets_dir = self.app_dir / "Assets"
        if assets_dir.exists():
            asset_count = len(list(assets_dir.glob("*.png")))
            print(f"      ✅ Assets 目录存在 ({asset_count} 个 PNG 图标)")
        else:
            print(f"      ⚠️  Assets 目录缺失")
        
        if total_files == 0:
            print("\n   ⚠️  警告: 未找到任何文件，请检查 ZIP 文件解压是否正确")
        else:
            print(f"\n   ✅ 验证完成，准备打包 {total_files:,} 个文件")
    
    def find_makeappx(self) -> Optional[Path]:
        """查找 makeappx.exe 工具"""
        # 搜索环境变量路径
        for path_str in os.environ.get("PATH", "").split(os.pathsep):
            path = Path(path_str) / "makeappx.exe"
            if path.exists():
                return path
        
        # 自动扫描 Windows SDK 安装目录
        sdk_base_paths = [
            Path("C:/Program Files (x86)/Windows Kits/10/bin"),
            Path("C:/Program Files/Windows Kits/10/bin"),
        ]
        
        # 优先使用 x64 版本，如果没有则使用 x86 版本
        for arch in ["x64", "x86"]:
            for sdk_base in sdk_base_paths:
                if not sdk_base.exists():
                    continue
                
                # 查找所有版本号目录
                try:
                    version_dirs = sorted(
                        [d for d in sdk_base.iterdir() if d.is_dir() and d.name.startswith("10.0.")],
                        reverse=True  # 优先使用最新版本
                    )
                    
                    for version_dir in version_dirs:
                        makeappx_path = version_dir / arch / "makeappx.exe"
                        if makeappx_path.exists():
                            print(f"✅ 找到 makeappx.exe: {makeappx_path}")
                            return makeappx_path
                except Exception as e:
                    print(f"⚠️  扫描 {sdk_base} 时出错: {e}")
                    continue
        
        # 如果自动扫描失败，尝试一些常见路径（向后兼容）
        possible_paths = [
            Path("C:/Program Files (x86)/Windows Kits/10/bin/10.0.26100.0/x64/makeappx.exe"),
            Path("C:/Program Files (x86)/Windows Kits/10/bin/10.0.22621.0/x64/makeappx.exe"),
            Path("C:/Program Files (x86)/Windows Kits/10/bin/10.0.19041.0/x64/makeappx.exe"),
            Path("C:/Program Files (x86)/Windows Kits/10/bin/10.0.17763.0/x64/makeappx.exe"),
        ]
        
        for path in possible_paths:
            if path.exists():
                print(f"✅ 找到 makeappx.exe: {path}")
                return path
        
        return None
    
    def find_signtool(self) -> Optional[Path]:
        """查找 signtool.exe 工具"""
        # 搜索环境变量路径
        for path_str in os.environ.get("PATH", "").split(os.pathsep):
            path = Path(path_str) / "signtool.exe"
            if path.exists():
                return path
        
        # 自动扫描 Windows SDK 安装目录
        sdk_base_paths = [
            Path("C:/Program Files (x86)/Windows Kits/10/bin"),
            Path("C:/Program Files/Windows Kits/10/bin"),
        ]
        
        # 优先使用 x64 版本，如果没有则使用 x86 版本
        for arch in ["x64", "x86"]:
            for sdk_base in sdk_base_paths:
                if not sdk_base.exists():
                    continue
                
                # 查找所有版本号目录
                try:
                    version_dirs = sorted(
                        [d for d in sdk_base.iterdir() if d.is_dir() and d.name.startswith("10.0.")],
                        reverse=True  # 优先使用最新版本
                    )
                    
                    for version_dir in version_dirs:
                        signtool_path = version_dir / arch / "signtool.exe"
                        if signtool_path.exists():
                            print(f"✅ 找到 signtool.exe: {signtool_path}")
                            return signtool_path
                except Exception as e:
                    print(f"⚠️  扫描 {sdk_base} 时出错: {e}")
                    continue
        
        # 如果自动扫描失败，尝试一些常见路径（向后兼容）
        possible_paths = [
            Path("C:/Program Files (x86)/Windows Kits/10/bin/10.0.26100.0/x64/signtool.exe"),
            Path("C:/Program Files (x86)/Windows Kits/10/bin/10.0.22621.0/x64/signtool.exe"),
            Path("C:/Program Files (x86)/Windows Kits/10/bin/10.0.19041.0/x64/signtool.exe"),
            Path("C:/Program Files (x86)/Windows Kits/10/bin/10.0.17763.0/x64/signtool.exe"),
        ]
        
        for path in possible_paths:
            if path.exists():
                print(f"✅ 找到 signtool.exe: {path}")
                return path
        
        return None
    
    def find_msix_packaging_tool(self) -> Optional[Path]:
        """查找 MSIX Packaging Tool（GUI 工具）"""
        # 常见的安装路径
        possible_paths = [
            Path("C:/Program Files (x86)/Windows Kits/10/App Certification Kit/msixpackagingtool.exe"),
            Path("C:/Program Files/Windows Kits/10/App Certification Kit/msixpackagingtool.exe"),
            Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WindowsApps" / "Microsoft.MsixPackagingTool_8wekyb3d8bbwe" / "msixpackagingtool.exe",
            Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "WindowsApps" / "Microsoft.MsixPackagingTool_8wekyb3d8bbwe" / "msixpackagingtool.exe",
        ]
        
        # 搜索环境变量路径
        for path_str in os.environ.get("PATH", "").split(os.pathsep):
            path = Path(path_str) / "msixpackagingtool.exe"
            if path.exists():
                return path
        
        # 搜索常见路径
        for path in possible_paths:
            if path.exists():
                return path
        
        # 尝试通过 Windows 应用协议打开（如果已安装但路径不同）
        try:
            # 检查是否可以通过 start 命令打开
            result = subprocess.run(
                ["powershell", "-Command", "Get-AppxPackage -Name *MsixPackagingTool*"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                # 找到了，返回一个标记路径
                return Path("msix-packaging-tool://")
        except:
            pass
        
        return None
        
    def build_msix(self, use_packaging_tool: bool = False) -> Path:
        """
        构建 MSIX 包
        
        :param use_packaging_tool: 是否使用 MSIX Packaging Tool（GUI）
        :return: MSIX 文件路径
        """
        print("🔨 构建 MSIX 包...")
        
        # 检查工具可用性
        makeappx = self.find_makeappx()
        packaging_tool = self.find_msix_packaging_tool()
        
        # 如果明确要求使用 MSIX Packaging Tool，或者没有 makeappx.exe
        if use_packaging_tool or (makeappx is None and packaging_tool is not None):
            # 使用 MSIX Packaging Tool（GUI）
            print("=" * 60)
            print("📦 使用 MSIX Packaging Tool (GUI) 进行打包")
            print("=" * 60)
            print()
            print(f"✅ 已准备打包目录: {self.app_dir}")
            print()
            print("📝 操作步骤：")
            print("   1. 打开 MSIX Packaging Tool")
            print("   2. 选择 'Application package'")
            print("   3. 在 'Select source location' 中，选择以下目录：")
            print(f"      {self.app_dir}")
            print("   4. 在 'Select output location' 中，选择输出目录")
            print("   5. 按照向导完成打包")
            print()
            
            # 尝试打开 MSIX Packaging Tool
            if packaging_tool and packaging_tool != Path("msix-packaging-tool://"):
                print(f"🔄 正在尝试打开 MSIX Packaging Tool...")
                try:
                    subprocess.Popen([str(packaging_tool)], shell=True)
                    print("✅ MSIX Packaging Tool 已打开")
                except Exception as e:
                    print(f"⚠️  无法自动打开，请手动打开 MSIX Packaging Tool")
            elif packaging_tool == Path("msix-packaging-tool://"):
                print("🔄 正在尝试通过 PowerShell 打开 MSIX Packaging Tool...")
                try:
                    # 使用 PowerShell 打开 Windows Store 应用
                    subprocess.Popen([
                        "powershell",
                        "-Command",
                        "Start-Process 'ms-windows-store://pdp/?ProductId=9N5LW3JBCXKF'"
                    ], shell=False)
                    # 或者尝试直接启动应用
                    try:
                        subprocess.Popen(["msixpackagingtool"], shell=True)
                    except:
                        pass
                    print("✅ 正在打开 MSIX Packaging Tool")
                except Exception as e:
                    print("⚠️  无法自动打开，请手动打开 MSIX Packaging Tool")
                    print("   可以从开始菜单搜索 'MSIX Packaging Tool' 打开")
            else:
                print("⚠️  未找到 MSIX Packaging Tool，请手动打开")
                print("   下载地址: https://www.microsoft.com/store/productId/9N5LW3JBCXKF")
                print("   或从开始菜单搜索 'MSIX Packaging Tool'")
            
            print()
            print("=" * 60)
            print("💡 提示：打包完成后，MSIX 文件将保存在您指定的输出目录")
            print("=" * 60)
            return None
        elif makeappx is None:
            # 没有找到任何工具
            error_msg = [
                "❌ 未找到 MSIX 打包工具",
                "",
                "可选方案：",
                "",
                "方案一：安装 Windows SDK（推荐，命令行工具）",
                "   - 下载: https://developer.microsoft.com/windows/downloads/windows-sdk/",
                "   - 安装后包含 makeappx.exe（命令行工具）",
                "",
                "方案二：使用 MSIX Packaging Tool（GUI 工具）",
                "   - 下载: https://www.microsoft.com/store/productId/9N5LW3JBCXKF",
                "   - 使用 --packaging-tool 参数运行脚本",
                "",
                "使用 MSIX Packaging Tool 的步骤：",
                f"   python build_msix.py --zip PhotoSystem-Portable.zip --version 6.0.0.0 --packaging-tool"
            ]
            raise FileNotFoundError("\n".join(error_msg))
        else:
            # 使用 makeappx.exe（命令行）
            msix_path = self.output_dir / f"PhotoSystem_{self.version.replace('.', '_')}.msix"
            
            # 构建命令
            cmd = [
                str(makeappx),
                "pack",
                "/d", str(self.app_dir),
                "/p", str(msix_path),
                "/o"
            ]
            
            print(f"执行命令: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
            
            if result.returncode != 0:
                print(f"❌ 构建失败 (返回码: {result.returncode}):")
                if result.stdout:
                    print("标准输出:")
                    print(result.stdout)
                if result.stderr:
                    print("错误输出:")
                    print(result.stderr)
                if not result.stdout and not result.stderr:
                    print("未获取到错误信息，请检查命令是否正确执行")
                error_msg = result.stderr if result.stderr else result.stdout if result.stdout else "未知错误"
                raise RuntimeError(f"MSIX 构建失败: {error_msg}")
            
            print(f"✅ MSIX 包已创建: {msix_path}")
            return msix_path
            
    def sign_msix(self, msix_path: Path, cert_path: str = None, cert_password: str = None, cert_thumbprint: str = None):
        """
        签名 MSIX 包
        
        注意：为了保留未签名的包用于 Store 提交，签名时会创建副本并重命名。
        原文件保持不变，签名后的文件会添加 _Signed 后缀。
        
        :param msix_path: MSIX 文件路径
        :param cert_path: 证书文件路径（.pfx），如果提供则从文件签名
        :param cert_password: 证书密码（仅当使用 cert_path 时）
        :param cert_thumbprint: 证书指纹，如果提供则从证书存储签名（优先于 cert_path）
        :return: 签名后的文件路径
        """
        if cert_thumbprint is None and cert_path is None:
            print("⚠️  跳过代码签名（未提供证书）")
            print("   注意: Microsoft Store 发布需要代码签名证书")
            return None
        
        print("🔐 签名 MSIX 包...")
        
        # 查找 signtool.exe
        signtool_path = self.find_signtool()
        
        if signtool_path is None:
            raise FileNotFoundError(
                "未找到 signtool.exe。请安装 Windows SDK 或确保已安装 Windows SDK Signing Tools 组件。"
            )
        
        print(f"   使用签名工具: {signtool_path}")
        
        # 检查 MSIX 文件是否被锁定
        msix_path_abs = msix_path.resolve()
        try:
            # 尝试以写入模式打开文件，检查是否被锁定
            with open(msix_path_abs, 'r+b') as f:
                pass
        except PermissionError:
            raise RuntimeError(
                f"MSIX 文件被锁定或无法访问: {msix_path_abs}\n"
                f"请确保：\n"
                f"1. 文件没有被其他程序打开\n"
                f"2. 文件没有被安装或正在使用\n"
                f"3. 您有足够的权限访问该文件"
            )
        
        # 创建签名后的文件路径（添加 _Signed 后缀，保留原文件用于 Store 提交）
        msix_signed_path = msix_path_abs.parent / f"{msix_path_abs.stem}_Signed{msix_path_abs.suffix}"
        
        # 复制原文件到新路径
        print(f"   复制文件到: {msix_signed_path.name}（保留原文件用于 Store 提交）")
        shutil.copy2(msix_path_abs, msix_signed_path)
        
        # 对副本进行签名
        print(f"   对副本进行签名...")
        
        # 构建签名命令
        cmd = [
            str(signtool_path),
            "sign",
            "/v",  # 详细输出
            "/fd", "SHA256",  # 文件摘要算法
            "/ph",  # 页面哈希（适用于 MSIX）
        ]
        
        # 优先使用证书存储中的证书（通过指纹）
        if cert_thumbprint:
            print(f"   使用证书存储中的证书（指纹: {cert_thumbprint}）")
            cmd.extend([
                "/sha1", cert_thumbprint,  # 使用证书指纹从证书存储签名
            ])
        elif cert_path:
            # 从 PFX 文件签名
            cert_path_abs = Path(cert_path).resolve()
            if not cert_path_abs.exists():
                raise FileNotFoundError(f"证书文件不存在: {cert_path_abs}")
            
            print(f"   使用证书文件: {cert_path_abs}")
            cmd.extend([
                "/f", str(cert_path_abs),  # 证书文件路径（使用绝对路径）
                "/p", cert_password or "",  # 证书密码
            ])
        
        # 添加 MSIX 文件路径（对副本进行签名）
        cmd.append(str(msix_signed_path))
        
        print(f"   执行命令: {' '.join(cmd[:4])} ... <MSIX文件>")
        
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        
        # 输出详细日志
        if result.stdout:
            print("   签名工具输出:")
            for line in result.stdout.splitlines():
                print(f"     {line}")
        
        if result.returncode != 0:
            # 签名失败，删除副本
            if msix_signed_path.exists():
                msix_signed_path.unlink()
                print(f"   已删除失败的签名副本")
            
            print(f"❌ 签名失败 (返回码: {result.returncode}):")
            if result.stderr:
                print("   错误信息:")
                for line in result.stderr.splitlines():
                    print(f"     {line}")
            if result.stdout:
                print("   详细输出:")
                for line in result.stdout.splitlines():
                    print(f"     {line}")
            
            # 提供常见问题的解决建议
            error_msg = result.stderr or result.stdout or "未知错误"
            if "password" in error_msg.lower() or "密码" in error_msg:
                raise RuntimeError(
                    f"MSIX 签名失败: 证书密码错误或证书文件格式不正确。\n"
                    f"请检查：\n"
                    f"1. 证书密码是否正确\n"
                    f"2. 证书文件是否为有效的 PFX 格式\n"
                    f"3. 证书是否包含私钥\n"
                    f"4. 建议：使用证书指纹从证书存储签名，避免密码问题"
                )
            elif "certificate" in error_msg.lower() or "证书" in error_msg or "thumbprint" in error_msg.lower():
                raise RuntimeError(
                    f"MSIX 签名失败: 证书无效或未找到。\n"
                    f"请检查：\n"
                    f"1. 证书指纹是否正确（如果使用指纹签名）\n"
                    f"2. 证书是否在证书存储中（如果使用指纹签名）\n"
                    f"3. 证书文件是否为有效的 PFX 格式（如果使用文件签名）\n"
                    f"4. 证书是否包含代码签名扩展\n"
                    f"5. 证书是否已过期"
                )
            else:
                raise RuntimeError(f"MSIX 签名失败: {error_msg}")
        
        print(f"✅ MSIX 包已签名: {msix_signed_path.name}")
        print(f"   📦 未签名包（用于 Store 提交）: {msix_path_abs.name}")
        print(f"   🔐 已签名包（用于本地测试）: {msix_signed_path.name}")
        
        return msix_signed_path
        
    def build(self, use_packaging_tool: bool = False, 
              cert_path: str = None, cert_password: str = None, cert_thumbprint: str = None) -> Path:
        """
        执行完整的构建流程
        
        :param use_packaging_tool: 是否使用 MSIX Packaging Tool
        :param cert_path: 证书路径（可选，.pfx 文件）
        :param cert_password: 证书密码（可选，仅当使用 cert_path 时）
        :param cert_thumbprint: 证书指纹（可选，优先于 cert_path，从证书存储签名）
        :return: MSIX 文件路径
        """
        print("=" * 60)
        print("🚀 开始 MSIX 打包流程")
        print("=" * 60)
        
        # 检查工具可用性
        makeappx = self.find_makeappx()
        packaging_tool = self.find_msix_packaging_tool()
        
        # 如果没有指定使用 GUI 工具，但找不到 makeappx.exe，自动切换到 GUI 工具
        if not use_packaging_tool and makeappx is None and packaging_tool is not None:
            print("ℹ️  检测到已安装 MSIX Packaging Tool，但未找到 makeappx.exe")
            print("ℹ️  将使用 MSIX Packaging Tool (GUI) 进行打包")
            print()
            use_packaging_tool = True
        
        try:
            # 1. 准备工作目录
            self.prepare_work_directory()
            
            # 2. 解压 ZIP 并获取可执行文件名
            executable_name = self.extract_zip()
            if executable_name is None:
                executable_name = "PhotoSystem.exe"  # 默认值
                print(f"⚠️  使用默认可执行文件名: {executable_name}")
            
            # 3. 准备清单文件（使用找到的可执行文件名）
            self.prepare_manifest(executable_name)
            
            # 4. 准备资源
            self.prepare_assets()
            
            # 4.5 验证打包内容（统计文件数量和大小）
            self.verify_package_contents()
            
            # 5. 构建 MSIX
            msix_path = self.build_msix(use_packaging_tool)
            
            # 6. 签名（如果提供了证书且成功创建了 MSIX 文件）
            signed_msix_path = None
            if msix_path and (cert_thumbprint or cert_path):
                signed_msix_path = self.sign_msix(msix_path, cert_path, cert_password, cert_thumbprint)
            
            print("=" * 60)
            if msix_path:
                print("✅ MSIX 打包完成！")
                print("=" * 60)
                if signed_msix_path:
                    # 如果已签名，显示两个文件
                    print(f"📦 未签名包（用于 Store 提交）: {msix_path.name}")
                    print(f"   📊 文件大小: {msix_path.stat().st_size / 1024 / 1024:.2f} MB")
                    print(f"🔐 已签名包（用于本地测试）: {signed_msix_path.name}")
                    print(f"   📊 文件大小: {signed_msix_path.stat().st_size / 1024 / 1024:.2f} MB")
                else:
                    # 未签名，只显示一个文件
                    print(f"📦 MSIX 文件: {msix_path.name}")
                    print(f"📊 文件大小: {msix_path.stat().st_size / 1024 / 1024:.2f} MB")
            else:
                print("✅ 打包准备完成！")
                print("=" * 60)
                print("📝 请按照上述步骤在 MSIX Packaging Tool 中完成打包")
            
            return msix_path
            
        except Exception as e:
            print("=" * 60)
            print(f"❌ 打包失败: {e}")
            print("=" * 60)
            raise


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="将 PyInstaller ZIP 转换为 MSIX 格式")
    parser.add_argument("--zip", type=str, 
                       default="PhotoSystem-Portable.zip",
                       help="PyInstaller 生成的 ZIP 文件路径")
    parser.add_argument("--version", type=str,
                       default="6.0.0.0",
                       help="应用版本号（格式: 主.次.构建.修订）")
    parser.add_argument("--output", type=str,
                       help="输出目录（默认: release 目录）")
    parser.add_argument("--packaging-tool", action="store_true",
                       help="使用 MSIX Packaging Tool（GUI）而不是命令行")
    parser.add_argument("--cert", type=str,
                       help="代码签名证书路径（.pfx 文件）")
    parser.add_argument("--cert-password", type=str,
                       help="证书密码（仅当使用 --cert 时）")
    parser.add_argument("--cert-thumbprint", type=str,
                       help="证书指纹（从证书存储签名，优先于 --cert）")
    parser.add_argument("--sign-only", type=str,
                       help="仅对已存在的 MSIX 文件进行签名（指定 MSIX 文件路径）")
    
    args = parser.parse_args()
    
    # 如果只是签名已存在的 MSIX 文件
    if args.sign_only:
        msix_path = Path(args.sign_only).resolve()
        if not msix_path.exists():
            print(f"❌ MSIX 文件不存在: {msix_path}")
            return
        
        if not (args.cert_thumbprint or args.cert):
            print("❌ 签名需要提供证书（--cert-thumbprint 或 --cert）")
            return
        
        # 创建构建器（仅用于签名功能）
        builder = MSIXBuilder(
            zip_path="",  # 不需要 ZIP
            output_dir=args.output,
            version=args.version
        )
        
        # 直接签名
        builder.sign_msix(
            msix_path=msix_path,
            cert_path=args.cert,
            cert_password=args.cert_password,
            cert_thumbprint=args.cert_thumbprint
        )
        print("=" * 60)
        print("✅ MSIX 签名完成！")
        print("=" * 60)
        return
    
    # 创建构建器
    builder = MSIXBuilder(
        zip_path=args.zip,
        output_dir=args.output,
        version=args.version
    )
    
    # 执行构建
    builder.build(
        use_packaging_tool=args.packaging_tool,
        cert_path=args.cert,
        cert_password=args.cert_password,
        cert_thumbprint=args.cert_thumbprint
    )


if __name__ == "__main__":
    main()

