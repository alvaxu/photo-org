#!/bin/bash

# PhotoSystem - Linux/macOS Install Script

echo ""
echo "========================================"
echo "PhotoSystem"
echo "Installer"
echo "========================================"
echo ""

echo "Starting installer..."
echo ""

if [ -f "installer.py" ]; then
    echo "Running installer..."
    python3 installer.py
    if [ $? -ne 0 ]; then
        echo "ERROR: Installation failed"
        read -p "Press Enter to exit..."
        exit 1
    fi
else
    echo "ERROR: Installer script installer.py not found"
    echo "Please ensure all files are properly extracted"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

echo ""
echo "Installation completed!"
read -p "Press Enter to exit..."
