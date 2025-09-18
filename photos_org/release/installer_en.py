#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhotoSystem - Installation Helper Script

This script is used for:
1. Interactive user installation
2. Path selection and configuration
3. Shortcut creation
4. System environment checking

Author: AI Assistant
Created: September 17, 2025
"""

import os
import sys
import json
import shutil
import platform
from pathlib import Path

# Try to use bundled Python runtime from _internal directory
current_dir = Path(__file__).parent
internal_dir = current_dir / "_internal"

if internal_dir.exists():
    # Add _internal directory to Python path
    internal_path = str(internal_dir)
    if internal_path not in sys.path:
        sys.path.insert(0, internal_path)

    # Also add the base_library.zip if it exists
    base_library = internal_dir / "base_library.zip"
    if base_library.exists():
        sys.path.insert(0, str(base_library))


class PhotoSystemInstaller:
    """PhotoSystem Installer"""

    def __init__(self):
        self.system = platform.system().lower()
        self.install_path = None
        self.storage_path = None

        # Set project root based on execution environment
        if getattr(sys, 'frozen', False):
            # Running in PyInstaller bundle
            exe_path = Path(sys.executable)
            # For installer, files are in the same directory as the exe
            self.project_root = exe_path.parent
            print(f"DEBUG: Running in PyInstaller bundle, exe_path: {exe_path}")
            print(f"DEBUG: Running in PyInstaller bundle, project_root: {self.project_root}")
        else:
            # Running as regular Python script
            self.project_root = Path(__file__).parent
            print(f"DEBUG: Running as Python script, project_root: {self.project_root}")

    def print_banner(self):
        """Print installer banner"""
        banner = """
========================================
PhotoSystem
Installer
========================================

Make photo management simple and smart!
========================================
        """
        print(banner)

    def get_user_input(self, prompt, default=""):
        """Get user input"""
        if default:
            result = input(f"{prompt} (default: {default}): ").strip()
            return result if result else default
        else:
            while True:
                result = input(f"{prompt}: ").strip()
                if result:
                    return result
                print("Input cannot be empty, please try again.")

    def select_install_path(self):
        """Select installation path"""
        print("\nStep 1: Select Installation Path")
        print("System will create program files in the specified directory")

        if self.system == "windows":
            default_path = "C:\\Program Files\\PhotoSystem"
        else:
            default_path = "/opt/photosystem"

        self.install_path = Path(self.get_user_input(
            "Please enter installation path",
            default_path
        ))

        # Check if path exists
        if self.install_path.exists():
            if self.install_path.is_file():
                print("ERROR: Installation path is a file, please select a directory path")
                return self.select_install_path()
        else:
            # Create directory
            try:
                self.install_path.mkdir(parents=True, exist_ok=True)
                print(f"SUCCESS: Created installation directory: {self.install_path}")
            except Exception as e:
                print(f"ERROR: Failed to create directory: {e}")
                return self.select_install_path()

        print(f"SUCCESS: Installation path: {self.install_path}")

    def select_storage_path(self):
        """Select storage path"""
        print("\nStep 2: Select Photo Storage Path")
        print("System will store your photo files in the specified directory")

        if self.system == "windows":
            default_path = str(Path.home() / "Documents" / "PhotoSystem")
        else:
            default_path = str(Path.home() / "PhotoSystem")

        self.storage_path = Path(self.get_user_input(
            "Please enter photo storage path",
            default_path
        ))

        # Check if path exists
        if not self.storage_path.exists():
            try:
                self.storage_path.mkdir(parents=True, exist_ok=True)
                print(f"SUCCESS: Created storage directory: {self.storage_path}")
            except Exception as e:
                print(f"ERROR: Failed to create storage directory: {e}")
                return self.select_storage_path()

        print(f"SUCCESS: Storage path: {self.storage_path}")

    def copy_files(self):
        """Copy program files"""
        print("\nStep 3: Copy Program Files")

        try:
            # Files to copy
            files_to_copy = [
                'PhotoSystem.exe',
                'config.json',
                'config_default.json',
                'README.md',
                'README.html',
                'installer.py',
                'startup.bat'
            ]

            dirs_to_copy = [
                'app',
                'static',
                'templates',
                '_internal'
            ]

            # Copy files
            for file in files_to_copy:
                src = self.project_root / file
                dst = self.install_path / file
                if src.exists():
                    shutil.copy2(src, dst)
                    print(f"SUCCESS: Copied file: {file}")
                else:
                    print(f"WARNING: File not found: {file} at {src}")

            # Copy directories
            for dir_name in dirs_to_copy:
                src = self.project_root / dir_name
                dst = self.install_path / dir_name
                if src.exists():
                    if dst.exists():
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                    print(f"SUCCESS: Copied directory: {dir_name}")

        except Exception as e:
            print(f"ERROR: Failed to copy files: {e}")
            return False

        return True

    def update_config(self):
        """Update configuration file"""
        print("\nStep 4: Update Configuration File")

        try:
            config_path = self.install_path / 'config.json'

            if not config_path.exists():
                print("WARNING: Configuration file does not exist, skipping config update")
                return True

            # Read config
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Update storage path
            if 'storage' not in config:
                config['storage'] = {}
            config['storage']['base_path'] = str(self.storage_path)

            # Record installation path for uninstaller
            if 'installation' not in config:
                config['installation'] = {}
            config['installation']['install_path'] = str(self.install_path)

            # Save config
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            print(f"SUCCESS: Configuration updated: {config_path}")
            print(f"   Storage path: {self.storage_path}")
            print(f"   Install path: {self.install_path}")

        except Exception as e:
            print(f"ERROR: Failed to update configuration: {e}")
            return False

        return True

    def create_shortcut(self):
        """Create desktop shortcut"""
        print("\nStep 5: Create Shortcut")

        try:
            if self.system == "windows":
                self._create_windows_shortcut()
            elif self.system == "linux":
                self._create_linux_shortcut()
            elif self.system == "darwin":  # macOS
                self._create_macos_shortcut()
            else:
                print(f"WARNING: Unsupported operating system: {self.system}")

        except Exception as e:
            print(f"ERROR: Failed to create shortcut: {e}")

    def _create_windows_shortcut(self):
        """Create Windows shortcut using PowerShell pointing to startup.bat"""
        try:
            # Shortcut target (point to startup.bat)
            target = str(self.install_path / 'startup.bat')
            working_dir = str(self.install_path)

            # Convert Windows paths to PowerShell format (forward slashes)
            target = target.replace('\\', '/')
            working_dir = working_dir.replace('\\', '/')

            # Desktop path
            desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
            shortcut_path = os.path.join(desktop, 'PhotoSystem.lnk')

            # Icon path - always use PhotoSystem.exe for the icon
            icon_path = str(self.install_path / 'PhotoSystem.exe')

            # Convert Windows path to PowerShell format (forward slashes)
            icon_path = icon_path.replace('\\', '/')

            # Verify the exe exists for icon
            exe_path = str(self.install_path / 'PhotoSystem.exe')
            if not os.path.exists(exe_path):
                # Fallback to ico file if exe doesn't exist
                ico_path = str(self.install_path / 'xuwh.ico')
                if os.path.exists(ico_path):
                    icon_path = ico_path.replace('\\', '/')
                else:
                    # Final fallback to favicon
                    favicon_path = str(self.install_path / 'static' / 'images' / 'favicon.ico')
                    if os.path.exists(favicon_path):
                        icon_path = favicon_path.replace('\\', '/')

            # Create shortcut using PowerShell
            ps_script = f'''
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{target}"
$Shortcut.WorkingDirectory = "{working_dir}"
$Shortcut.IconLocation = "{icon_path},0"
$Shortcut.Description = "PhotoSystem - 智能照片管理系统"
$Shortcut.Save()
'''
            
            # Write PowerShell script to temporary file
            ps_file = self.install_path / 'create_shortcut.ps1'
            with open(ps_file, 'w', encoding='utf-8') as f:
                f.write(ps_script)
            
            # Execute PowerShell script
            import subprocess
            result = subprocess.run([
                'powershell', '-ExecutionPolicy', 'Bypass', '-File', str(ps_file)
            ], capture_output=True, text=True)
            
            # Clean up temporary file
            os.remove(ps_file)
            
            if result.returncode == 0:
                print(f"SUCCESS: Windows shortcut created: {shortcut_path}")
            else:
                print(f"WARNING: Failed to create shortcut: {result.stderr}")
                print("   You can manually create a shortcut pointing to: PhotoSystem.exe")
                
        except Exception as e:
            print(f"WARNING: Failed to create shortcut: {e}")
            print("   You can manually create a shortcut pointing to: PhotoSystem.exe")

    def _create_linux_shortcut(self):
        """Create Linux desktop file"""
        # Icon path (use xuwh.ico if available, otherwise favicon.ico, then executable)
        icon_path = str(self.install_path / 'xuwh.ico')
        if not os.path.exists(icon_path):
            icon_path = str(self.install_path / 'static' / 'images' / 'favicon.ico')
        if not os.path.exists(icon_path):
            icon_path = str(self.install_path / 'PhotoSystem')
        
        desktop_file = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=PhotoSystem
Comment=智能照片管理系统
Exec={self.install_path}/PhotoSystem
Path={self.install_path}
Icon={icon_path}
Terminal=false
Categories=Utility;Application;Graphics;
"""

        # Create desktop file
        desktop_path = Path.home() / '.local' / 'share' / 'applications'
        desktop_path.mkdir(parents=True, exist_ok=True)

        desktop_file_path = desktop_path / 'photosystem.desktop'
        with open(desktop_file_path, 'w', encoding='utf-8') as f:
            f.write(desktop_file)

        # Set execution permission
        os.chmod(desktop_file_path, 0o755)

        print(f"SUCCESS: Linux desktop file created: {desktop_file_path}")

    def _create_macos_shortcut(self):
        """Create macOS shortcut"""
        # Create a simple shell script for macOS
        script_content = f'''#!/bin/bash
# PhotoSystem Launch Script
cd "{self.install_path}"
./PhotoSystem
'''

        script_path = self.install_path / 'launch.sh'
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        # Make it executable
        os.chmod(script_path, 0o755)

        print(f"SUCCESS: macOS launch script created: {script_path}")
        print("   You can drag this script to your Dock or create an alias")
        print("   Double-click this script to launch the program")

    def create_startup_script(self):
        """Create startup script"""
        print("\nStep 6: Create Startup Script")

        if self.system == "windows":
            self._create_windows_batch()
        else:
            self._create_unix_script()

    def _create_windows_batch(self):
        """Create Windows batch file"""
        batch_content = f"""@echo off
chcp 65001 >nul
title PhotoSystem

echo.
echo ========================================
echo PhotoSystem
echo ========================================
echo.

cd /d "{self.install_path}"

echo Starting system（first time will be a little longer) ...
echo Installation path: {self.install_path}
echo Storage path: {self.storage_path}
echo.

PhotoSystem.exe

echo.
echo System closed, press any key to exit...
pause >nul
"""

        batch_path = self.install_path / 'startup.bat'
        with open(batch_path, 'w', encoding='utf-8') as f:
            f.write(batch_content)

        print(f"SUCCESS: Windows startup script created: {batch_path}")

    def _create_unix_script(self):
        """Create Unix startup script"""
        script_content = f"""#!/bin/bash

echo ""
echo "========================================"
echo "PhotoSystem"
echo "========================================"
echo ""

cd "{self.install_path}"

echo "Starting system（first time will be a little longer) ..."
echo "Installation path: {self.install_path}"
echo "Storage path: {self.storage_path}"
echo ""

./PhotoSystem

echo ""
echo "System closed, press Enter to exit..."
read
"""

        script_path = self.install_path / 'startup.sh'
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)

        # Set execution permission
        os.chmod(script_path, 0o755)

        print(f"SUCCESS: Unix startup script created: {script_path}")

    def print_summary(self):
        """Print installation summary"""
        print("\n" + "="*60)
        print("Installation Completed!")
        print("="*60)
        print(f"Installation path: {self.install_path}")
        print(f"Storage path: {self.storage_path}")
        print()
        print("Launch methods:")
        if self.system == "windows":
            print(f"   1. Double-click desktop shortcut")
            print(f"   2. Run: {self.install_path}\\startup.bat")
        else:
            print(f"   1. Double-click desktop icon")
            print(f"   2. Run: {self.install_path}/startup.sh")
        print()
        print("Access URL: http://localhost:8000")

        # Open README.html in browser
        self.open_readme_in_browser()

        print("="*60)

    def open_readme_in_browser(self):
        """Open README.html in default browser"""
        try:
            import os
            import webbrowser

            readme_html_path = os.path.join(self.install_path, "README.html")

            # Convert to absolute path and normalize
            readme_html_path = os.path.abspath(readme_html_path)

            if os.path.exists(readme_html_path):
                print("\n📖 Opening user guide in browser...")

                # Use file:// URL scheme for local files
                file_url = f"file://{readme_html_path.replace(os.sep, '/')}"

                # Try to open with default browser
                try:
                    # First try with webbrowser module (most reliable)
                    webbrowser.open(file_url)
                    print("✅ User guide opened in browser (webbrowser)")
                except:
                    # Fallback to system commands
                    if self.system == "windows":
                        os.startfile(readme_html_path)
                        print("✅ User guide opened in browser (os.startfile)")
                    else:
                        # For Linux/macOS, try alternative methods
                        import subprocess
                        if self.system == "darwin":
                            subprocess.run(["open", readme_html_path], check=False)
                        else:
                            subprocess.run(["xdg-open", readme_html_path], check=False)
                        print("✅ User guide opened in browser (system command)")
            else:
                print("⚠️  User guide file not found")
                print(f"   Expected location: {readme_html_path}")

        except Exception as e:
            print(f"⚠️  Could not open user guide: {e}")
            print("   You can manually open README.html in your installation directory")

    def run(self):
        """Run installer"""
        try:
            self.print_banner()

            # Step 1: Select installation path
            self.select_install_path()

            # Step 2: Select storage path
            self.select_storage_path()

            # Step 3: Copy files
            if not self.copy_files():
                print("ERROR: Installation failed - file copy error")
                return False

            # Step 4: Update configuration
            if not self.update_config():
                print("ERROR: Installation failed - configuration update error")
                return False

            # Step 5: Create shortcut
            self.create_shortcut()

            # Step 6: Create startup script
            self.create_startup_script()

            # Step 7: Print summary
            self.print_summary()

            return True

        except KeyboardInterrupt:
            print("\n\nWARNING: Installation cancelled")
            return False
        except Exception as e:
            print(f"\nERROR: Error occurred during installation: {e}")
            return False


def main():
    """Main function"""
    installer = PhotoSystemInstaller()
    success = installer.run()

    if success:
        input("\nPress Enter to exit installer...")
    else:
        input("\nPress Enter to exit...")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
