# -*- mode: python ; coding: utf-8 -*-
"""
ملف إعدادات PyInstaller لمحول كتب الشاملة
Shamela Books Converter PyInstaller Spec File
"""

import sys
import os
from pathlib import Path

# تحديد المسار الأساسي
base_path = Path.cwd()
src_path = base_path / 'src'

# تحديد الملفات الإضافية المطلوبة
added_files = [
    # ملف دعم BOK
    (str(src_path / 'simple_bok_support.py'), '.'),
    # ملف إعدادات قاعدة البيانات إذا كان موجوداً
    (str(src_path / 'db_settings.json'), '.') if (src_path / 'db_settings.json').exists() else None,
    # ملف requirements.txt للمرجع
    (str(base_path / 'requirements.txt'), '.'),
]

# تحديد مسار مكتبات MySQL
venv_path = Path(sys.executable).parent.parent
mysql_vendor_path = venv_path / 'Lib' / 'site-packages' / 'mysql' / 'vendor'
mysql_plugin_path = mysql_vendor_path / 'plugin'

# إضافة مكتبات MySQL المطلوبة
if mysql_vendor_path.exists():
    # إضافة مكتبات DLL الأساسية
    for dll_file in mysql_vendor_path.glob('*.dll'):
        added_files.append((str(dll_file), 'mysql/vendor'))
    
    # إضافة plugins المطلوبة للمصادقة
    if mysql_plugin_path.exists():
        for plugin_file in mysql_plugin_path.glob('*.dll'):
            added_files.append((str(plugin_file), 'mysql/vendor/plugin'))

# إزالة العناصر الفارغة
added_files = [f for f in added_files if f is not None]

# تحديد المكتبات المخفية المطلوبة
hidden_imports = [
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'tkinter.scrolledtext',
    'threading',
    'queue',
    'json',
    'os',
    'datetime',
    'pyodbc',
    'mysql.connector',
    'pathlib',
    'tempfile',
    'shutil',
    'simple_bok_support',
    # مكتبات إضافية قد تكون مطلوبة
    'mysql.connector.locales.eng',
    'mysql.connector.constants',
    'mysql.connector.cursor',
    'mysql.connector.errors',
    'mysql.connector.authentication',
    'mysql.connector.plugins',
    'mysql.connector.network',
    'mysql.connector.protocol',
    'pywin32',
]

# تحليل الملف الرئيسي
a = Analysis(
    [str(src_path / 'shamela_gui.py')],
    pathex=[str(base_path), str(src_path)],
    binaries=[],
    datas=added_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # استبعاد المكتبات غير المطلوبة لتقليل حجم الملف
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'cv2',
        'tensorflow',
        'torch',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# إزالة الملفات المكررة
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# إنشاء الملف التنفيذي
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='shamela_converter_v2',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # إخفاء نافذة وحدة التحكم
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # إضافة أيقونة إذا كانت متوفرة
    icon=None,  # يمكن إضافة مسار الأيقونة هنا
    # معلومات الإصدار
    version_file=None,
)

# إنشاء مجلد التوزيع (اختياري)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='محول_كتب_الشاملة_dist'
)