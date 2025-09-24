# -*- mode: python ; coding: utf-8 -*-
# ملف .spec محسن لحل مشكلة MySQL authentication plugin

import os
import sys
from pathlib import Path

# المسارات
project_dir = Path(r"C:\Users\osaidsalah002\upload_Access_to_Database_sql\ShamielaBookConverter")
src_dir = project_dir / "src"
resources_dir = project_dir / "resources"

# إضافة مجلد src إلى مسار Python
sys.path.insert(0, str(src_dir))

# تحليل الملفات والمكتبات
a = Analysis(
    [str(project_dir / "main.py")],
    pathex=[str(project_dir), str(src_dir)],
    binaries=[],
    datas=[
        (str(resources_dir), "resources"),
    ],
    hiddenimports=[
        # MySQL connector - الحل الرئيسي للمشكلة
        'mysql.connector',
        'mysql.connector.locales',
        'mysql.connector.locales.eng',
        'mysql.connector.locales.eng.client_error',
        'mysql.connector.conversion',
        'mysql.connector.cursor',
        'mysql.connector.errors',
        'mysql.connector.network',
        'mysql.connector.protocol',
        'mysql.connector.utils',
        'mysql.connector.constants',
        'mysql.connector.abstracts',
        'mysql.connector.pooling',
        'mysql.connector.authentication',
        'mysql.connector.charsets',
        'mysql.connector.custom_types',
        'mysql.connector.dbapi',
        'mysql.connector.fabric',
        'mysql.connector.optionfiles',
        
        # pyodbc
        'pyodbc',
        
        # tkinter
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.scrolledtext',
        
        # مكتبات أخرى
        'queue',
        'threading',
        'json',
        'pathlib',
        'tempfile',
        'shutil',
        'uuid',
        'datetime',
        're',
        'time',
        'os',
        'sys',
        'traceback',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

# تجميع الملفات
pyz = PYZ(a.pure)

# إنشاء ملف EXE واحد
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ShamielaConverter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # تغيير إلى True للاختبار
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    
    version='version_info.txt'
)
