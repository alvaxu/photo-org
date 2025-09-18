@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title PhotoSystem Build Script

REM Force CMD environment for compatibility
if not "%1"=="CMD_MODE" (
    cmd /c "%~f0" CMD_MODE
    goto :eof
)

echo.
echo ========================================
echo PhotoSystem Build Script
echo ========================================
echo.

echo Checking environment...
echo.

REM Check Python environment
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found
    echo Please install Python 3.8+ and add to PATH
    pause
    exit /b 1
)

echo SUCCESS: Python environment OK

REM Check PyInstaller
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo ERROR: PyInstaller not found
    echo Installing PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo ERROR: PyInstaller installation failed
        pause
        exit /b 1
    )
)

echo SUCCESS: PyInstaller OK

echo.
echo Building executable...
echo.

REM Install dependencies from requirements.txt
echo Installing dependencies from requirements.txt...
pip install -r ..\requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies from requirements.txt
    pause
    exit /b 1
)

REM Build with PyInstaller (using --collect-all for all packages)
if exist main_en.spec (
    pyinstaller --clean main_en.spec
) else if exist ..\main_en.spec (
    pyinstaller --clean ..\main_en.spec
) else if exist main.spec (
    pyinstaller --clean main.spec
) else if exist ..\main.spec (
    pyinstaller --clean ..\main.spec
) else (
    echo ERROR: main.spec file not found
    pause
    exit /b 1
)

if errorlevel 1 (
    echo ERROR: Build failed
    pause
    exit /b 1
)

echo SUCCESS: Executable built

echo.
echo Preparing distribution...
echo.

REM Check if single file mode or directory mode
echo Checking for existing executable...

REM Priority: Check for latest build first
if exist "build\main_en\PhotoSystem.exe" (
    echo INFO: Found latest executable in build directory, using it...
    REM Clean old dist files
    if exist "dist\PhotoSystem.exe" del "dist\PhotoSystem.exe"

    REM If dist\PhotoSystem exists and has _internal directory, use it directly
    if exist "dist\PhotoSystem\_internal" (
        echo INFO: Using existing directory mode with _internal folder
        set "BUILD_MODE=directory"
        set "EXE_PATH=dist\PhotoSystem\PhotoSystem.exe"
        goto :build_mode_determined
    ) else (
        REM Clean old dist files if no _internal directory
        if exist "dist\PhotoSystem" rmdir /s /q "dist\PhotoSystem"
        REM Copy latest build
        mkdir "dist\PhotoSystem"
        copy "build\main_en\PhotoSystem.exe" "dist\PhotoSystem\PhotoSystem.exe" >nul
        if exist "dist\PhotoSystem\PhotoSystem.exe" (
            echo SUCCESS: Latest executable copied to directory mode
            set "BUILD_MODE=directory"
            set "EXE_PATH=dist\PhotoSystem\PhotoSystem.exe"
            goto :build_mode_determined
        ) else (
            echo ERROR: Failed to copy executable to directory
            pause
            exit /b 1
        )
    )
)

REM Fallback: Check for existing directory mode
if exist "dist\PhotoSystem\PhotoSystem.exe" (
    echo SUCCESS: Directory mode executable found
    set "BUILD_MODE=directory"
    set "EXE_PATH=dist\PhotoSystem\PhotoSystem.exe"
    goto :build_mode_determined
)

REM Fallback: Check for existing single file mode
if exist "dist\PhotoSystem.exe" (
    echo SUCCESS: Single file executable found
    set "BUILD_MODE=single"
    set "EXE_PATH=dist\PhotoSystem.exe"
    goto :build_mode_determined
)

REM If none of the above conditions are met, show error
echo ERROR: Build output not found
echo Expected locations:
echo   - build\main_en\PhotoSystem.exe (latest build)
echo   - dist\PhotoSystem\PhotoSystem.exe (directory mode)
echo   - dist\PhotoSystem.exe (single file mode)
pause
exit /b 1

:build_mode_determined

REM Debug: Show current BUILD_MODE
echo DEBUG: BUILD_MODE is set to: !BUILD_MODE!
echo DEBUG: EXE_PATH is set to: !EXE_PATH!

REM Ensure distribution directory exists
echo DEBUG: Ensuring distribution directory exists...
if not exist "dist\PhotoSystem" (
    echo ERROR: PhotoSystem directory should have been created
    pause
    exit /b 1
) else (
    echo DEBUG: PhotoSystem directory exists
)
set "DIST_DIR=dist\PhotoSystem"

echo DEBUG: DIST_DIR is set to: !DIST_DIR!

REM Clean old files
echo DEBUG: Cleaning old files...
if exist !DIST_DIR!\install.bat del !DIST_DIR!\install.bat
if exist !DIST_DIR!\installer.py del !DIST_DIR!\installer.py

REM Copy necessary files
echo DEBUG: Copying config files...
copy "..\config.json" "!DIST_DIR!\" >nul
if errorlevel 1 (
    echo ERROR: Failed to copy config.json
    pause
    exit /b 1
)
copy "..\config_default.json" "!DIST_DIR!\" >nul
if errorlevel 1 (
    echo ERROR: Failed to copy config_default.json
    pause
    exit /b 1
)
copy "..\README.md" "!DIST_DIR!\" >nul
if errorlevel 1 (
    echo ERROR: Failed to copy README.md
    pause
    exit /b 1
)
copy "INSTALL_README.md" "!DIST_DIR!\" >nul
if errorlevel 1 (
    echo ERROR: Failed to copy INSTALL_README.md
    pause
    exit /b 1
)
echo DEBUG: Config files copied successfully

echo DEBUG: Copying icon files...
copy "xuwh.ico" "!DIST_DIR!\" >nul
if errorlevel 1 (
    echo ERROR: Failed to copy xuwh.ico
    pause
    exit /b 1
)

echo DEBUG: Copying install scripts...
copy "installer_en.py" "!DIST_DIR!\installer.py" >nul
if errorlevel 1 (
    echo ERROR: Failed to copy installer_en.py
    pause
    exit /b 1
)
copy "install_en.bat" "!DIST_DIR!\install.bat" >nul
if errorlevel 1 (
    echo ERROR: Failed to copy install_en.bat
    pause
    exit /b 1
)
copy "install_en.sh" "!DIST_DIR!\install.sh" >nul
if errorlevel 1 (
    echo ERROR: Failed to copy install_en.sh
    pause
    exit /b 1
)
echo DEBUG: Install scripts copied successfully

echo Copying documentation...
REM Note: doc directory is excluded from package to reduce size
REM if exist ..\doc (
REM     xcopy ..\doc dist\PhotoSystem\doc\ /E /I /H /Y >nul
REM )

echo DEBUG: Creating startup script...
echo DEBUG: Creating startup.bat...

REM Create startup script - using simple approach
echo @echo off > !DIST_DIR!\startup.bat
echo chcp 65001 ^>nul >> !DIST_DIR!\startup.bat
echo title PhotoSystem >> !DIST_DIR!\startup.bat
echo. >> !DIST_DIR!\startup.bat
echo echo. >> !DIST_DIR!\startup.bat
echo echo ======================================== >> !DIST_DIR!\startup.bat
echo echo PhotoSystem >> !DIST_DIR!\startup.bat
echo echo ======================================== >> !DIST_DIR!\startup.bat
echo echo. >> !DIST_DIR!\startup.bat
echo. >> !DIST_DIR!\startup.bat
echo cd /d "%%~dp0" >> !DIST_DIR!\startup.bat
echo. >> !DIST_DIR!\startup.bat
echo echo Starting system... >> !DIST_DIR!\startup.bat
echo echo Program path: %%~dp0 >> !DIST_DIR!\startup.bat
echo echo. >> !DIST_DIR!\startup.bat
echo. >> !DIST_DIR!\startup.bat
echo PhotoSystem.exe >> !DIST_DIR!\startup.bat
echo. >> !DIST_DIR!\startup.bat
echo echo. >> !DIST_DIR!\startup.bat
echo echo System closed, press any key to exit... >> !DIST_DIR!\startup.bat
echo pause ^>nul >> !DIST_DIR!\startup.bat

echo DEBUG: Startup script created successfully

echo.
echo DEBUG: Creating installation guide...
echo DEBUG: Creating install_guide.txt...

REM Create installation guide - using simple approach
echo PhotoSystem - Installation Guide > !DIST_DIR!\install_guide.txt
echo ======================================== >> !DIST_DIR!\install_guide.txt
echo. >> !DIST_DIR!\install_guide.txt
echo File Description: >> !DIST_DIR!\install_guide.txt
echo --------- >> !DIST_DIR!\install_guide.txt
echo PhotoSystem.exe        - Main executable >> !DIST_DIR!\install_guide.txt
echo startup.bat            - Startup script (recommended) >> !DIST_DIR!\install_guide.txt
echo install.bat            - Installation script >> !DIST_DIR!\install_guide.txt
echo installer.py           - Python installer >> !DIST_DIR!\install_guide.txt
echo config.json            - Configuration file >> !DIST_DIR!\install_guide.txt
echo config_default.json    - Default configuration >> !DIST_DIR!\install_guide.txt
echo README.md              - Project description >> !DIST_DIR!\install_guide.txt
echo INSTALL_README.md      - Detailed installation guide >> !DIST_DIR!\install_guide.txt
if "!BUILD_MODE!"=="directory" (
    echo _internal\             - Program dependencies (do not delete) >> !DIST_DIR!\install_guide.txt
) else (
    echo Note: Single file mode - all dependencies included in PhotoSystem.exe >> !DIST_DIR!\install_guide.txt
)
echo. >> !DIST_DIR!\install_guide.txt
echo Usage: >> !DIST_DIR!\install_guide.txt
echo --------- >> !DIST_DIR!\install_guide.txt
echo 1. Direct run: Double-click "startup.bat" >> !DIST_DIR!\install_guide.txt
echo 2. Install mode: Double-click "install.bat" for full installation >> !DIST_DIR!\install_guide.txt
echo 3. Manual start: Double-click "PhotoSystem.exe" >> !DIST_DIR!\install_guide.txt
echo. >> !DIST_DIR!\install_guide.txt
echo Notes: >> !DIST_DIR!\install_guide.txt
echo --------- >> !DIST_DIR!\install_guide.txt
echo - First run will automatically create database and storage directories >> !DIST_DIR!\install_guide.txt
echo - Program requires internet connection for AI analysis services >> !DIST_DIR!\install_guide.txt
echo - Recommend using "startup.bat" to start the program >> !DIST_DIR!\install_guide.txt
echo - If problems occur, check INSTALL_README.md >> !DIST_DIR!\install_guide.txt
echo. >> !DIST_DIR!\install_guide.txt
echo Technical Support: >> !DIST_DIR!\install_guide.txt
echo --------- >> !DIST_DIR!\install_guide.txt
echo Contact technical support team if you have any issues >> !DIST_DIR!\install_guide.txt
echo. >> !DIST_DIR!\install_guide.txt

echo DEBUG: Installation guide created successfully

echo.
echo DEBUG: Creating archive...
echo DEBUG: Starting archive creation...

REM Create ZIP archive
if exist PhotoSystem-Installer-Clean.zip (
    del PhotoSystem-Installer-Clean.zip
)

REM Use 7-Zip to create archive
echo DEBUG: Checking for 7-Zip...
if exist "C:\Program Files\7-Zip\7z.exe" (
    echo DEBUG: 7-Zip found, creating archive...
    cd dist
    echo DEBUG: Current directory: %CD%
    echo DEBUG: Creating archive with 7-Zip...
    "C:\Program Files\7-Zip\7z.exe" a -tzip ..\PhotoSystem-Installer-Clean.zip PhotoSystem
    cd ..
    if errorlevel 1 (
        echo ERROR: 7-Zip compression failed
        pause
        exit /b 1
    )
    echo DEBUG: Archive created successfully
) else (
    echo ERROR: 7-Zip not found, please manually compress !DIST_DIR! directory
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build completed successfully!
echo ========================================
echo.
echo Archive location: %CD%\PhotoSystem-Installer-Clean.zip
echo Program directory: %CD%\!DIST_DIR!
echo.
echo Distribution instructions:
echo    1. Send PhotoSystem-Installer-Clean.zip to users
echo    2. Users extract and run "startup.bat" directly
echo    3. Or run "install.bat" for full installation
echo.
echo New features:
echo    - Optimized package size (excluded TensorFlow, PyTorch, OpenCV)
echo    - Single file executable mode for better compatibility
echo    - Fixed Python DLL loading issues
echo    - Improved shortcut icon handling
echo    - Added "startup.bat" startup script
echo    - Added "install_guide.txt" usage guide
echo    - Optimized file structure for clarity
echo.

pause
