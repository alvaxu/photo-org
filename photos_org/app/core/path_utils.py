"""
路径解析工具模块

提供统一的路径解析函数，根据运行环境（开发环境、PyInstaller portable、MSIX）正确解析相对路径和绝对路径。

作者：AI助手
创建日期：2025年1月
"""

from pathlib import Path
import sys


def resolve_resource_path(config_path: str) -> Path:
    """
    根据当前运行环境解析资源路径（模型路径、数据库路径等）
    
    此函数会根据运行环境自动判断基准目录：
    - 开发环境：相对于项目根目录（main.py所在目录）
    - PyInstaller打包环境（包括portable和MSIX）：相对于可执行文件目录
    
    :param config_path: 配置中的路径（可能是相对路径或绝对路径）
    :return: 解析后的绝对路径
    """
    path_obj = Path(config_path)
    
    # 如果已经是绝对路径，直接返回
    if path_obj.is_absolute():
        return path_obj.resolve()
    
    # 相对路径：根据运行环境解析
    if getattr(sys, 'frozen', False):
        # PyInstaller打包环境（包括portable和MSIX）
        exe_dir = Path(sys.executable).parent
        return (exe_dir / path_obj).resolve()
    else:
        # 开发环境：相对于项目根目录
        # 项目根目录是包含 main.py 的目录
        # 从当前文件向上查找，直到找到包含 main.py 的目录
        current_path = Path(__file__).resolve()
        project_root = current_path.parent.parent  # app/core/path_utils.py -> app -> project_root
        
        # 验证：确保项目根目录包含 main.py
        if not (project_root / 'main.py').exists():
            # 如果不在 app/core/ 下调用，尝试其他方式
            # 从当前工作目录查找（作为后备方案）
            import os
            cwd = Path(os.getcwd())
            if (cwd / 'main.py').exists():
                project_root = cwd
            else:
                # 如果都找不到，使用当前文件所在目录的父目录的父目录
                # 这适用于大多数情况（app/ 下的文件）
                project_root = current_path.parent.parent
        
        return (project_root / path_obj).resolve()

