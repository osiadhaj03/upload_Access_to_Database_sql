# -*- mode: python ; coding: utf-8 -*-
"""
ملف PyInstaller Spec لبناء محول كتب الشاملة من مجلد src
Shamela Books Converter PyInstaller Spec File from src folder
"""

import os
from pathlib import Path

# المسارات الأساسية
project_root = Path(os.getcwd())
src_dir = project_root / 'src'
main_script = src_dir / 'shamela_gui.py'

# التأكد من وجود الملف الرئيسي
if not main_script.exists():
    raise FileNotFoundError(f"الملف الرئيسي غير موجود: {main_script}")

# البيانات والملفات الإضافية
added_files = [
    # ملف إعدادات قاعدة البيانات
    (str(project_root / 'db_settings.json'), '.'),
    # ملف إعدادات قاعدة البيانات من مجلد src
    (str(src_dir / 'db_settings.json'), '.'),
]

# التحقق من وجود الملفات الإضافية
for src_path, dest_path in added_files[:]:
    if not os.path.exists(src_path):
        print(f"تحذير: الملف غير موجود: {src_path}")
        added_files.remove((src_path, dest_path))

# المكتبات المخفية المطلوبة
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
    'simple_bok_support',
    'mysql.connector.locales',
    'mysql.connector.locales.eng',
    'mysql.connector.cursor',
    'mysql.connector.pooling',
    'mysql.connector.constants',
    'mysql.connector.conversion',
    'mysql.connector.protocol',
    'mysql.connector.authentication',
    'mysql.connector.charsets',
    'mysql.connector.errors',
    'mysql.connector.network',
    'mysql.connector.utils',
    'pyodbc',
    'tempfile',
    'shutil',
    'time',
    'sys',
    'traceback',
    'logging',
    'sqlite3',
    'csv',
    'io',
    'base64',
    'hashlib',
    'uuid',
    'platform',
    'subprocess',
    'webbrowser',
    'urllib',
    'urllib.parse',
    'urllib.request',
    'http',
    'http.client',
    'ssl',
    'socket',
    'struct',
    'zlib',
    'gzip',
    'zipfile',
    'tarfile',
    'email',
    'email.mime',
    'email.mime.text',
    'email.mime.multipart',
    'mimetypes',
    'collections',
    'collections.abc',
    'itertools',
    'functools',
    'operator',
    'copy',
    'pickle',
    'configparser',
    'xml',
    'xml.etree',
    'xml.etree.ElementTree',
    'html',
    'html.parser',
    'encodings',
    'encodings.utf_8',
    'encodings.cp1256',
    'encodings.latin1',
    'locale',
    'gettext',
    'decimal',
    'fractions',
    'statistics',
    'math',
    'random',
    'secrets',
    'hashlib',
    'hmac',
    'binascii',
    'codecs',
    'unicodedata',
    'string',
    're',
    'fnmatch',
    'glob',
    'linecache',
    'textwrap',
    'pprint',
    'reprlib',
    'enum',
    'types',
    'weakref',
    'gc',
    'inspect',
    'dis',
    'importlib',
    'importlib.util',
    'pkgutil',
    'modulefinder',
    'runpy',
    'argparse',
    'getopt',
    'cmd',
    'shlex',
    'contextlib',
    'abc',
    'atexit',
    'warnings',
    'dataclasses',
    'typing',
    'typing_extensions'
]

# تحليل الملف الرئيسي
a = Analysis(
    [str(main_script)],
    pathex=[str(src_dir), str(project_root)],
    binaries=[],
    datas=added_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'cv2',
        'tensorflow',
        'torch',
        'sklearn',
        'jupyter',
        'notebook',
        'IPython',
        'pytest',
        'sphinx',
        'setuptools',
        'pip',
        'wheel',
        'distutils',
        'pkg_resources'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# إزالة الملفات غير المرغوب فيها
a.datas = [x for x in a.datas if not any([
    'test' in x[0].lower(),
    'example' in x[0].lower(),
    'demo' in x[0].lower(),
    '__pycache__' in x[0],
    '.pyc' in x[0],
    '.pyo' in x[0],
    'LICENSE' in x[0],
    'README' in x[0] and x[0] != 'README.md',
    'CHANGELOG' in x[0],
    'MANIFEST' in x[0],
    'setup.py' in x[0],
    '.git' in x[0],
    '.svn' in x[0],
    'docs/' in x[0],
    'tests/' in x[0],
    'examples/' in x[0]
])]

# إنشاء ملف PYZ
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# إنشاء الملف التنفيذي
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='shamela_converter_src',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # واجهة رسومية بدون نافذة وحدة التحكم
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version=None,
    uac_admin=False,
    uac_uiaccess=False,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    icon=None  # يمكن إضافة أيقونة هنا لاحقاً
)

# معلومات البناء
print("\n" + "="*60)
print("🔧 معلومات بناء محول كتب الشاملة")
print("="*60)
print(f"📁 مجلد المشروع: {project_root}")
print(f"📄 الملف الرئيسي: {main_script}")
print(f"📦 عدد الملفات الإضافية: {len(added_files)}")
print(f"🔗 عدد المكتبات المخفية: {len(hidden_imports)}")
print(f"🎯 اسم الملف التنفيذي: shamela_converter_src.exe")
print("="*60)