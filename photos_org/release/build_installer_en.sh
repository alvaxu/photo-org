#!/bin/bash

# PhotoSystem - Linux/macOS Complete Build Script

echo ""
echo ""
echo "========================================"
echo "PhotoSystem Complete Build Script"
echo "========================================"
echo ""

echo "Checking environment..."
echo ""

# Check Python environment
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 not found"
    echo "Please install Python 3.8+"
    exit 1
fi

echo "SUCCESS: Python environment OK"

# Check PyInstaller
if ! python3 -c "import PyInstaller" &> /dev/null; then
    echo "ERROR: PyInstaller not found"
    echo "Installing PyInstaller..."
    python3 -m pip install pyinstaller
    if [ $? -ne 0 ]; then
        echo "ERROR: PyInstaller installation failed"
        exit 1
    fi
fi

echo "SUCCESS: PyInstaller OK"

echo ""
echo "Building executable..."
echo ""

# Build main PhotoSystem executable
echo ""
echo "========================================"
echo "Building PhotoSystem Main Executable"
echo "========================================"
echo "Building PhotoSystem..."

python3 -m PyInstaller --clean main_en.spec

if [ $? -ne 0 ]; then
    echo "ERROR: Build failed"
    exit 1
fi

if [ -f "dist/PhotoSystem/PhotoSystem" ]; then
    echo "SUCCESS: PhotoSystem executable built"
else
    echo "ERROR: PhotoSystem executable not found after build"
    exit 1
fi

echo ""
echo "Preparing distribution..."
echo ""

# Check for build output and create distribution directory
if [ -d "dist/PhotoSystem" ]; then
    echo "SUCCESS: Directory mode executable found"
    BUILD_MODE="directory"
elif [ -f "dist/PhotoSystem" ]; then
    echo "SUCCESS: Single file executable found"
    BUILD_MODE="single"
    # Create directory for single file mode
    mkdir -p "dist/PhotoSystem"
    cp "dist/PhotoSystem" "dist/PhotoSystem/PhotoSystem"
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to copy single file executable to directory"
        exit 1
    fi
elif [ -f "build/main_en/PhotoSystem" ]; then
    echo "INFO: Found executable in build directory, copying to dist..."
    mkdir -p "dist/PhotoSystem"
    cp "build/main_en/PhotoSystem" "dist/PhotoSystem/PhotoSystem"
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to copy executable from build directory"
        exit 1
    fi
    if [ -f "dist/PhotoSystem/PhotoSystem" ]; then
        echo "SUCCESS: Single file executable copied to dist"
        BUILD_MODE="single"
    else
        echo "ERROR: Failed to copy executable to dist"
        exit 1
    fi
else
    echo "ERROR: Build output not found"
    echo "Expected locations:"
    echo "  - dist/PhotoSystem/ (directory mode)"
    echo "  - dist/PhotoSystem (single file mode)"
    echo "  - build/main_en/PhotoSystem (build directory)"
    exit 1
fi

# Clean __pycache__ directories
echo "Cleaning __pycache__ directories..."
if [ -d "dist/PhotoSystem/_internal" ]; then
    echo "Found _internal directory, cleaning all __pycache__ subdirectories..."
    find "dist/PhotoSystem/_internal" -type d -name "__pycache__" -print -exec rm -rf {} \; 2>/dev/null || true
fi
if [ -d "__pycache__" ]; then
    echo "Removing release/__pycache__"
    rm -rf "__pycache__" 2>/dev/null || true
fi

# Copy necessary files
echo "Copying config files..."
cp "../config.json" "dist/PhotoSystem/"
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to copy config.json"
    exit 1
fi
cp "../config_default.json" "dist/PhotoSystem/"
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to copy config_default.json"
    exit 1
fi
cp "README.md" "dist/PhotoSystem/"
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to copy README.md"
    exit 1
fi
cp "INSTALL_README.md" "dist/PhotoSystem/"
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to copy INSTALL_README.md"
    exit 1
fi
cp "功能说明正式版.pdf" "dist/PhotoSystem/"
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to copy 功能说明正式版.pdf"
    exit 1
fi

echo "Copying icon files..."
cp "xuwh.ico" "dist/PhotoSystem/"
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to copy xuwh.ico"
    exit 1
fi

echo "Skipping installer scripts - using direct execution mode"

# Skip installer executable generation - using direct execution mode

echo "Creating startup script..."
cat > "dist/PhotoSystem/startup.sh" << 'EOF'
#!/bin/bash
# PhotoSystem Startup Script

echo ""
echo "========================================"
echo "PhotoSystem"
echo "========================================"
echo ""

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

echo "Program path: $DIR"
echo "Starting system（first time will be a little longer) ..."
echo ""

# Change to the program directory
cd "$DIR"

# Check if executable exists
if [ ! -f "./PhotoSystem" ]; then
    echo "ERROR: PhotoSystem executable not found"
    echo "Please ensure the installation is complete"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# Run the PhotoSystem executable
./PhotoSystem

echo ""
echo "System closed, press Enter to exit..."
read
EOF

chmod +x "dist/PhotoSystem/startup.sh"
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to set executable permissions on startup.sh"
    exit 1
fi


echo "Copying documentation..."
# Note: doc directory is excluded from package to reduce size
# if [ -d "../doc" ]; then
#     cp -r ../doc dist/PhotoSystem/
# fi

echo ""
echo "Creating archive..."
echo ""

# Final cleanup before compression
echo "Final cleanup before compression..."
if [ -d "dist/PhotoSystem/_internal" ]; then
    echo "Found _internal directory"
    echo "Final cleaning of __pycache__ directories..."
    find "dist/PhotoSystem/_internal" -type d -name "__pycache__" -exec rm -rf {} \; -print 2>/dev/null || true
else
    echo "_internal directory not found"
fi

# Create TAR archive
if [ -f "PhotoSystem-Portable.tar.gz" ]; then
    rm "PhotoSystem-Portable.tar.gz"
fi

tar -czf "PhotoSystem-Portable.tar.gz" -C "dist" "PhotoSystem"

if [ $? -ne 0 ]; then
    echo "ERROR: Compression failed"
    exit 1
fi

echo ""
echo "========================================"
echo "[SUCCESS] Complete Build Successful!"
echo "========================================"
echo ""
echo "[OK] PhotoSystem executable built"
echo "[OK] All files packaged for direct execution"
echo ""
echo "Archive location: $(pwd)/PhotoSystem-Portable.tar.gz"
echo "Program directory: $(pwd)/dist/PhotoSystem"
echo ""
echo "Distribution instructions:"
echo "   1. Send PhotoSystem-Portable.tar.gz to users"
echo "   2. Users extract and run PhotoSystem directly"
echo "   3. Or run startup.sh for better user experience"
echo ""
echo "Usage tips:"
echo "   - Ensure Python environment is properly installed"
echo "   - Installation process will automatically configure paths"
echo "   - Supports custom installation and storage paths"
echo ""

echo "Press Enter to exit..."
read
