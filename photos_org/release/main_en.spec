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
        
        # ===== OpenCV Data Files =====
        # OpenCV cascade classifiers and data files (required for image processing)
        (str(VENV_DIR / 'Lib' / 'site-packages' / 'cv2' / 'data'), 'cv2/data'),
        
        # ===== InsightFace Data Files =====
        # InsightFace model data files (required for face recognition)
        (str(VENV_DIR / 'Lib' / 'site-packages' / 'insightface' / 'data'), 'insightface/data'),

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
        
        # HEIC format support
        'PIL._heif',        # HEIC image format support
        'pillow_heif',      # HEIC format support library
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
        'app.api.maps',
        'app.api.person_management',
        'app.api.face',
        
        # Face recognition modules
        'insightface',
        'insightface.app',
        'insightface.app.face_analysis',
        'insightface.data',
        'insightface.model_zoo',
        'insightface.model_zoo.landmark',
        'insightface.model_zoo.arcface_onnx',
        'insightface.model_zoo.retinaface',
        'insightface.utils',
        'insightface.utils.transform',
        'onnx',
        'onnxruntime',
        'onnxruntime.capi',
        'onnxruntime.capi.onnxruntime_inference_collection',
        'sklearn.cluster',
        'sklearn.metrics',
        'sklearn.metrics.pairwise',
        'tqdm',                  # Progress bar - NEEDED by InsightFace
        
        # Matplotlib for InsightFace (non-interactive mode)
        'matplotlib',
        'matplotlib.pyplot',
        'matplotlib.backends',
        'matplotlib.backends.backend_agg',
        
        # HTTP client for InsightFace
        'requests',
        'requests.adapters',
        'requests.auth',
        'requests.cookies',
        'requests.exceptions',
        'requests.models',
        'requests.sessions',
        'requests.utils',
        'urllib3',
        
        # ===== NumPy Core Modules Only =====
        # Essential numpy modules for debugging
        'numpy.core._multiarray_umath',      # Core array operations
        'numpy.core._internal',              # Internal array functions
        'numpy.core._methods',               # Array methods
        'numpy.core._exceptions',            # NumPy exceptions
        
        # ===== NumPy Linear Algebra Modules =====
        # Required for InsightFace transform.py estimate_affine_matrix_3d23d
        'numpy.linalg',                      # Linear algebra module
        'numpy.linalg.lapack_lite',          # LAPACK functions
        'numpy.linalg._umath_linalg',        # Linear algebra ufuncs
        'numpy.linalg._linalg',              # Core linear algebra
        'numpy.linalg.linalg',               # Linear algebra functions
        'numpy.linalg._solve_triangular',   # Triangular solver
        'numpy.linalg._solve_utils',         # Solve utilities
        
        # ===== Additional NumPy Modules =====
        # Required for array operations in transform.py
        'numpy.lib.stride_tricks',           # Array stride tricks
        'numpy.lib.function_base',           # Function base utilities
        'numpy.lib.mixins',                  # Array mixins
        'numpy.lib.npyio',                   # Array I/O
        'numpy.lib.utils',                   # Array utilities
        
        # ===== NumPy Array Creation =====
        # Required for np.ones, np.hstack in transform.py
        'numpy.core.fromnumeric',            # Array creation functions
        'numpy.core.defchararray',           # Character arrays
        'numpy.core.records',                # Record arrays
        
        # ===== Additional Critical NumPy Modules =====
        # Force import all critical numpy components
        'numpy.core._dtype_ctypes',          # Data type ctypes
        'numpy.core._ufunc_config',          # Ufunc configuration
        'numpy.core._asarray',               # Array conversion
        'numpy.core._multiarray_tests',      # Multiarray tests
        'numpy.core._operand_flag_tests',    # Operand flag tests
        'numpy.core._struct_ufunc_tests',    # Struct ufunc tests
        'numpy.core._umath_tests',           # Umath tests
        'numpy.core.arrayprint',             # Array printing
        'numpy.core.defchararray',           # Character arrays
        'numpy.core.einsumfunc',             # Einsum functions
        'numpy.core.function_base',          # Function base
        'numpy.core.getlimits',              # Get limits
        'numpy.core.machar',                 # Machine characteristics
        'numpy.core.memmap',                 # Memory mapping
        'numpy.core.multiarray',             # Multiarray
        'numpy.core.numeric',                # Numeric functions
        'numpy.core.overrides',              # Overrides
        'numpy.core.shape_base',             # Shape base
        'numpy.core.umath',                  # Universal math functions
        
        # ===== NumPy Array Functions =====
        # Required for transform.py functions
        'numpy.core._multiarray_umath',      # Multiarray umath
        'numpy.core._internal',              # Internal functions
        'numpy.core._methods',                # Array methods
        'numpy.core._exceptions',             # NumPy exceptions
        
        # ===== NumPy Linear Algebra Extensions =====
        # Additional linalg functions used in transform.py
        'numpy.linalg._solve_triangular',    # Triangular solver
        'numpy.linalg._solve_utils',         # Solve utilities
        'numpy.linalg.linalg',               # Linear algebra functions
    ],

    hookspath=[],  # Hook paths
    runtime_hooks=[],  # Runtime hooks
    collect_all=[  # Force collect all dependencies for these packages
        'numpy',            # Numerical computing library (ALL modules)
        'numpy.linalg',    # Linear algebra (force collect all)
        'numpy.core',      # Core numpy modules (force collect all)
        'numpy.lib',       # NumPy library modules (force collect all)
        'sklearn',          # Machine learning library
        'scipy',            # Scientific computing library
        'chinese_calendar', # Chinese holiday detection
        'geopy',            # Geographic calculations
        'multipart',        # File upload support
        'dotenv',           # Environment variables
        'jieba',            # Chinese text segmentation
        'opencv-python',    # Computer vision library
        'pillow',           # Image processing library
        'pillow-heif',      # HEIC format support library
        'numpy',            # Numerical computing library
        # 'insightface',      # Face recognition library - NEEDED for face recognition
        # 'onnx',             # ONNX for InsightFace - NEEDED for face recognition
        # 'onnxruntime',     # ONNX Runtime for InsightFace - NEEDED for face recognition
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
        # 'matplotlib',      # Required by InsightFace (but slow to initialize)
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
        
        # Deep Learning and AI (needed for face recognition)
        # 'onnx',            # ONNX - NEEDED for InsightFace
        # 'onnx.*',          # All ONNX submodules - NEEDED for InsightFace
        # 'onnxruntime',     # ONNX Runtime - NEEDED for InsightFace
        # 'onnxruntime.*',   # All ONNX Runtime submodules - NEEDED for InsightFace
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
        # 'requests',        # HTTP client - NEEDED for InsightFace
        # 'tqdm',            # Progress bar - NEEDED by InsightFace
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
