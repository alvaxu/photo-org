# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Build Configuration File
Used to package PhotoSystem into standalone executable

Author: AI Assistant
Created: September 17, 2025
"""

import os
import sys
from pathlib import Path

# Project root directory
ROOT_DIR = Path(os.getcwd()).parent

# Virtual environment path
VENV_DIR = ROOT_DIR / 'venv'

# Analyze main program
a = Analysis(
    [str(ROOT_DIR / 'main.py')],  # Main program file
    pathex=[
        str(ROOT_DIR),  # Project root
        str(VENV_DIR / 'Lib' / 'site-packages'),  # Virtual environment packages
        str(VENV_DIR / 'Scripts'),  # Virtual environment scripts
    ],  # Python path
    binaries=[
        # OpenCV DLLs from virtual environment
        (str(VENV_DIR / 'Lib' / 'site-packages' / 'cv2' / '*.dll'), 'cv2'),
        
        # Pillow-HEIF related DLLs (in site-packages root)
        (str(VENV_DIR / 'Lib' / 'site-packages' / '*.dll'), '.'),
    ],  # Binary files (like .dll, .so)

    # Data files (files and directories to include in package)
    datas=[
        # ===== Core Application Files =====
        # Entire app directory (contains all Python modules)
        (str(ROOT_DIR / 'app'), 'app'),

        # ===== Frontend Resources =====
        # Frontend static files (CSS, JS, images, etc.)
        (str(ROOT_DIR / 'static'), 'static'),

        # HTML template files
        (str(ROOT_DIR / 'templates'), 'templates'),

        # ===== Configuration Files =====
        # Configuration files (required for runtime)
        (str(ROOT_DIR / 'config.json'), '.'),
        (str(ROOT_DIR / 'config_default.json'), '.'),
        
        # ===== Icon Files =====
        # Application icon
        (str(ROOT_DIR / 'release' / 'xuwh.ico'), '.'),

        # ===== Documentation =====
        # Essential documentation only
        (str(ROOT_DIR / 'release' / 'README.md'), '.'),

        # ===== Important Notes =====
        # [OK] config.json      - User configuration file (required)
        # [OK] config_default.json - System default configuration (required)
        # [OK] All Python modules and frontend files
        # [NO] doc/             - Documentation directory (excluded to reduce size)
        # [NO] utilities/       - Development tools (excluded to reduce size)
        # [NO] requirements.txt - Dependencies file (not needed at runtime)
        # [NO] INSTALL_README.md - Detailed docs (excluded to reduce size)

        # ===== Excluded File Types =====
        # [NO] __pycache__/     - Python bytecode cache (generated at runtime)
        # [NO] *.pyc            - Python bytecode files (generated at runtime)
        # [NO] .git/            - Git version control files
        # [NO] venv/            - Python virtual environment
        # [NO] node_modules/    - Node.js dependencies
        # [NO] *.log            - Log files
        # [NO] .DS_Store        - macOS metadata
        # [NO] Thumbs.db        - Windows thumbnail cache
    ],

    # Hidden imports (modules PyInstaller might not detect)
    hiddenimports=[
        # FastAPI related
        'fastapi',
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.websockets',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',

        # SQLAlchemy related
        'sqlalchemy',
        'sqlalchemy.ext',
        'sqlalchemy.ext.declarative',
        'sqlalchemy.orm',
        'sqlalchemy.pool',
        'sqlalchemy.engine',
        'sqlalchemy.engine.base',
        'sqlalchemy.sql',
        'sqlalchemy.sql.expression',

        # Image processing (essential for photo management)
        'PIL',
        'PIL.Image',
        'PIL.ImageOps',
        'PIL.ImageFilter',
        'PIL.ImageEnhance',
        'imagehash',
        'cv2',              # OpenCV for image quality assessment
        # Core modules - PyInstaller will auto-collect dependencies with --collect-all
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        
        # Text processing
        'jieba',            # Chinese text segmentation
        
        # HTTP client
        'httpx',            # HTTP client for DashScope service
        
        # File processing
        'python-multipart', # File upload support
        'python-dotenv',    # Environment variables
        
        # Calendar
        'chinese_calendar', # Chinese holiday detection
        
        # Data validation
        'pydantic',
        'pydantic.fields',
        'pydantic.main',
        'pydantic.types',
        
        # Web framework components
        'starlette',
        'starlette.responses',
        'starlette.requests',
        'starlette.routing',
        'starlette.templating',
        'starlette.staticfiles',
        'jinja2',
        'jinja2.ext',
        'jinja2.filters',
        'markupsafe',
        
        # AI services
        'dashscope',
        
        # Utilities
        'click',
        'colorama',

        # Project internal modules
        'app.core.config',
        'app.core.logging',
        'app.db.session',
        'app.models.base',
        'app.models.photo',
        'app.services.storage_service',
        'app.services.photo_service',
        'app.services.analysis_service',
        'app.services.classification_service',
        'app.services.dashscope_service',
        'app.services.fts_service',
        'app.services.search_service',
        'app.services.duplicate_detection_service',
        'app.services.photo_quality_service',
        'app.services.enhanced_similarity_service',
        'app.services.migration_service',
        'app.services.init_system_categories',
        
        # Windows specific modules
        'win32api',
        'win32con', 
        'win32gui',
        'win32process',
        'pywintypes',
        
        'app.api.photos',
        'app.api.analysis',
        'app.api.categories',
        'app.api.config',
        'app.api.search',
        'app.api.storage',
        'app.api.tags',
        'app.api.health',
        'app.api.enhanced_search',
        'app.api.import_photos',
    ],

    hookspath=[],  # Hook paths
    runtime_hooks=[],  # Runtime hooks
    collect_all=[  # Force collect all dependencies for these packages
        'sklearn',          # Machine learning library
        'scipy',            # Scientific computing library
        'chinese_calendar', # Chinese holiday detection
        'geopy',            # Geographic calculations
        'multipart',        # File upload support
        'dotenv',           # Environment variables
        'jieba',            # Chinese text segmentation
        'opencv-python',    # Computer vision library
        'pillow',           # Image processing library
        'numpy',            # Numerical computing library
    ],
    excludes=[  # Excluded modules (reduce package size)
        # Python cache and temporary files
        '__pycache__',     # Python bytecode cache directory
        '*.pyc',           # Python bytecode files
        '*.pyo',           # Python optimized bytecode files
        '*.pyd',           # Python extension modules
        '.DS_Store',       # macOS file system metadata
        'Thumbs.db',       # Windows thumbnail cache

        # Documentation and development tools (excluded to reduce size)
        'doc',             # Documentation directory
        'doc.*',           # Any doc-related modules
        'utilities',       # Development tools directory
        'utilities.*',     # Any utilities-related modules
        
        # Testing and development frameworks
        'pytest',          # Testing framework
        'pytest-cov',      # Test coverage
        'pytest-html',     # Test reports
        'pytest-metadata', # Test metadata
        'pytest-xdist',    # Distributed testing
        'coverage',        # Coverage tools
        'black',           # Code formatting
        'flake8',          # Code checking
        'mypy',            # Type checking
        'isort',           # Import sorting
        'pre-commit',      # Git hooks
        'bandit',          # Security checking
        'safety',          # Dependency security checking
        'pip-tools',       # Dependency management
        'pipdeptree',      # Dependency tree
        'pip-audit',       # Dependency auditing
        
        # GUI and plotting libraries
        'tkinter',         # GUI library
        'matplotlib',      # Plotting library
        'IPython',         # Jupyter related
        'jupyter',         # Jupyter related
        'notebook',        # Jupyter related
        'ipykernel',       # Jupyter related
        'nbconvert',       # Jupyter related
        'nbformat',        # Jupyter related
        'ipywidgets',      # Jupyter related
        'widgetsnbextension', # Jupyter related
        'jupyterlab',      # Jupyter related
        'jupyterlab_server', # Jupyter related
        'jupyterlab_launcher', # Jupyter related
        
        # Machine Learning Libraries (major size reducers)
        'tensorflow',      # TensorFlow (920MB+)
        'tensorflow.*',    # All TensorFlow submodules
        'torch',           # PyTorch (240MB+)
        'torch.*',         # All PyTorch submodules
        'torchvision',     # TorchVision
        'torchaudio',      # TorchAudio
        'transformers',    # Hugging Face Transformers
        'keras',           # Keras
        'keras.*',         # All Keras submodules
        
        # Scientific Computing (reduce unnecessary footprint)
        # 'scipy',           # SciPy (large, not used) - REMOVED to allow collect_all
        # 'scipy.*',         # All SciPy submodules - REMOVED to allow collect_all
        'pandas',          # Pandas (large, not used)
        'pandas.*',        # All Pandas submodules
        
        # Deep Learning and AI (not needed for photo management)
        'onnx',            # ONNX
        'onnx.*',          # All ONNX submodules
        'onnxruntime',     # ONNX Runtime (13MB+)
        'onnxruntime.*',   # All ONNX Runtime submodules
        'faiss',           # Facebook AI Similarity Search
        'faiss.*',         # All FAISS submodules
        'stablehlo',       # StableHLO
        'stablehlo.*',     # All StableHLO submodules
        
        # Video Processing (not needed for photo management)
        'ffmpeg',          # FFmpeg
        'ffmpeg.*',        # All FFmpeg submodules
        'x264',            # x264 codec
        'x265',            # x265 codec
        'libx264',         # libx264
        'libx265',         # libx265
        
        # Unused dependencies
        'requests',        # HTTP client (using httpx instead)
        'tqdm',            # Progress bar (not used in core functionality)
    ],

# Windows specific options
win_no_prefer_redirects=False,  # Don't redirect standard I/O
win_private_assemblies=False,  # Don't use private assemblies

    cipher=None,  # No encryption
    noarchive=False,  # Create archive file
)

# Compress Python code
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Create executable file (for directory mode)
exe = EXE(
    pyz,
    a.scripts,
    [],  # No binaries in exe for directory mode
    exclude_binaries=True,  # Create directory mode executable
    name='PhotoSystem',  # Executable file name
    debug=False,  # Don't enable debug mode
    bootloader_ignore_signals=False,  # Don't ignore signals
    strip=False,  # Don't strip debug information
    upx=False,  # Disable UPX compression for better compatibility
    console=True,  # Show console window
    disable_windowed_traceback=False,  # Don't disable windowed traceback
    argv_emulation=False,  # Don't emulate argv
    target_arch=None,  # Target architecture
    codesign_identity=None,  # Code signing identity
    entitlements_file=None,  # Entitlements file
    icon=str(ROOT_DIR / 'release' / 'xuwh.ico'),  # Icon file
)

# Directory mode - create the directory structure with all files
coll = COLLECT(
    exe,  # The executable
    a.binaries,  # All binary files
    a.zipfiles,  # Python bytecode
    a.datas,  # Data files
    strip=False,
    upx=False,
    upx_exclude=[],
    name='PhotoSystem'  # Output directory name
)
