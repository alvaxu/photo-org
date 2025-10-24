@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title PhotoSystem Complete Build Script

REM Force CMD environment for compatibility
if not "%1"=="CMD_MODE" (
    cmd /c "%~f0" CMD_MODE
    goto :eof
)

REM Test redirection works
echo DEBUG: Testing redirection...
echo test > test_redirect.txt
if exist test_redirect.txt (
    echo DEBUG: Redirection works
    del test_redirect.txt
) else (
    echo ERROR: Redirection failed
    pause
    exit /b 1
)

REM Build main PhotoSystem executable
echo.
echo ========================================
echo Building PhotoSystem Main Executable
echo ========================================
echo DEBUG: Building PhotoSystem.exe...
python -m PyInstaller --clean --noconfirm main_en.spec
if errorlevel 1 (
    echo ERROR: Failed to build PhotoSystem.exe
    pause
    exit /b 1
)
if exist dist\PhotoSystem\PhotoSystem.exe (
    echo DEBUG: PhotoSystem.exe built successfully
) else (
    echo ERROR: PhotoSystem.exe not found after build
    pause
    exit /b 1
)

REM Skip installer executable generation - using direct execution mode

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
    python -m pip install pyinstaller
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
python -m pip install -r ..\requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies from requirements.txt
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
if exist !DIST_DIR!\installer.py del !DIST_DIR!\installer.py

REM Clean __pycache__ directories
echo DEBUG: Cleaning __pycache__ directories...
if exist !DIST_DIR!\_internal (
    echo DEBUG: Found _internal directory, cleaning all __pycache__ subdirectories...
    for /d /r "!DIST_DIR!\_internal" %%d in (__pycache__) do (
        if exist "%%d" (
            echo DEBUG: Removing %%d
            rmdir /s /q "%%d" 2>nul
        )
    )
)
if exist __pycache__ (
    echo DEBUG: Removing release\__pycache__
    rmdir /s /q __pycache__ 2>nul
)

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
copy "README.md" "!DIST_DIR!\" >nul
if errorlevel 1 (
    echo ERROR: Failed to copy README.md
    pause
    exit /b 1
)
copy "README.html" "!DIST_DIR!\" >nul
if errorlevel 1 (
    echo ERROR: Failed to copy README.html
    pause
    exit /b 1
)
copy "功能说明正式版.pdf" "!DIST_DIR!\" >nul
if errorlevel 1 (
    echo ERROR: Failed to copy 功能说明正式版.pdf
    pause
    exit /b 1
)
echo DEBUG: All files copied successfully

echo DEBUG: Copying icon files...
copy "xuwh.ico" "!DIST_DIR!\" >nul
if errorlevel 1 (
    echo ERROR: Failed to copy xuwh.ico
    pause
    exit /b 1
)

echo DEBUG: Copying images directory...
if exist "images" (
    echo DEBUG: Creating images directory in distribution...
    if not exist "!DIST_DIR!\images" mkdir "!DIST_DIR!\images"
    if errorlevel 1 (
        echo ERROR: Failed to create images directory
        pause
        exit /b 1
    )
    
    echo DEBUG: Copying all files from images directory...
    xcopy "images\*" "!DIST_DIR!\images\" /E /I /H /Y >nul
    if errorlevel 1 (
        echo ERROR: Failed to copy images directory
        pause
        exit /b 1
    )
    echo DEBUG: Images directory copied successfully
) else (
    echo WARNING: images directory not found, skipping...
)

echo DEBUG: Copying models directory...
if exist "..\models" (
    echo DEBUG: Creating models directory in distribution...
    if not exist "!DIST_DIR!\models" mkdir "!DIST_DIR!\models"
    if errorlevel 1 (
        echo ERROR: Failed to create models directory
        pause
        exit /b 1
    )
    
    echo DEBUG: Copying all files from models directory...
    xcopy "..\models\*" "!DIST_DIR!\models\" /E /I /H /Y >nul
    if errorlevel 1 (
        echo ERROR: Failed to copy models directory
        pause
        exit /b 1
    )
    echo DEBUG: Models directory copied successfully
    
    REM Show models directory size for verification
    echo DEBUG: Verifying models directory contents...
    if exist "!DIST_DIR!\models\buffalo_l" (
        echo DEBUG: buffalo_l model directory found
        dir "!DIST_DIR!\models\buffalo_l" /s | find "File(s)"
    ) else (
        echo WARNING: buffalo_l model directory not found in distribution
    )
) else (
    echo WARNING: models directory not found, skipping...
    echo WARNING: Face recognition may not work without local models
)

echo DEBUG: Skipping installer scripts - using direct execution mode

echo DEBUG: Creating launcher scripts...
echo DEBUG: DIST_DIR is: !DIST_DIR!
echo DEBUG: Checking if DIST_DIR exists...
if exist "!DIST_DIR!" (
    echo DEBUG: DIST_DIR exists
) else (
    echo ERROR: DIST_DIR does not exist: !DIST_DIR!
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

REM Create startup script with better user experience using safer method
(
echo @echo off
echo chcp 65001 ^> nul
echo title PhotoSystem
echo.
echo echo ========================================
echo echo PhotoSystem
echo echo ========================================
echo echo.
echo echo [INFO] Starting PhotoSystem, please wait...
echo echo.
echo cd /d "%%~dp0"
echo echo [INFO] Program path: %%~dp0
echo echo [INFO] Initializing components...
echo echo.
echo PhotoSystem.exe
echo.
echo echo.
echo echo System closed, press any key to exit...
echo pause ^> nul
) > !DIST_DIR!\startup.bat

echo DEBUG: Startup script created successfully


echo.
echo DEBUG: Creating archive...
echo DEBUG: Starting archive creation...

REM Final cleanup before compression
echo DEBUG: Final cleanup before compression...
if exist "!DIST_DIR!\_internal" (
    echo DEBUG: Starting recursive __pycache__ cleanup...
    pushd "!DIST_DIR!\_internal"
    for /d /r %%d in (__pycache__) do (
        if exist "%%d" (
            echo DEBUG: Final removing %%d
            rmdir /s /q "%%d" 2>nul
        )
    )
    popd
)

REM Create ZIP archive
if exist PhotoSystem-Portable.zip (
    del PhotoSystem-Portable.zip
)
if exist PhotoSystem-Portable.zip.tmp (
    del PhotoSystem-Portable.zip.tmp
)

REM Use 7-Zip to create archive
echo DEBUG: Checking for 7-Zip...
if exist "C:\Program Files\7-Zip\7z.exe" (
    echo DEBUG: 7-Zip found, creating archive...
    cd dist
    echo DEBUG: Current directory: %CD%
    echo DEBUG: Creating archive with 7-Zip...
    "C:\Program Files\7-Zip\7z.exe" a -tzip ..\PhotoSystem-Portable.zip PhotoSystem
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
echo [SUCCESS] Complete Build Successful!
echo ========================================
echo.
echo [OK] README.html generated
echo [OK] PhotoSystem.exe built
echo [OK] All files packaged for direct execution
echo.
echo Archive location: %CD%\PhotoSystem-Portable.zip
echo Program directory: %CD%\!DIST_DIR!
echo.
echo Distribution instructions:
echo    1. Send PhotoSystem-Portable.zip to users
echo    2. Users extract and run "PhotoSystem.exe" directly
echo    3. Or run "startup.bat" for better user experience
echo.
echo New features:
echo    - Optimized package size (excluded TensorFlow, PyTorch)
echo    - Single file executable mode for better compatibility
echo    - Fixed Python DLL loading issues
echo    - Improved shortcut icon handling
echo    - Added "startup.bat" startup script
echo    - Streamlined package structure
echo    - Removed redundant installation files
echo    - Local face recognition models included (offline capability)
echo    - Face recognition models: buffalo_l (~325MB)
echo.

pause
