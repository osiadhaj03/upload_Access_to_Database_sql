#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إعداد التطبيق لإنشاء ملف تنفيذي .exe
"""

from cx_Freeze import setup, Executable
import sys
import os

# إضافة المجلد الحالي إلى المسار
sys.path.insert(0, os.path.dirname(__file__))

# ملفات إضافية مطلوبة
include_files = [
    # أي ملفات إضافية تريد تضمينها
]

# حزم مطلوبة
packages = [
    "tkinter",
    "pyodbc", 
    "mysql.connector",
    "json",
    "queue",
    "threading",
    "datetime",
    "pathlib",
    "uuid",
    "re",
    "os"
]

# خيارات البناء
build_options = {
    "packages": packages,
    "include_files": include_files,
    "excludes": [],
    "include_msvcrt": True
}

# إعداد الملف التنفيذي
exe = Executable(
    script="shamela_gui.py",
    base="Win32GUI" if sys.platform == "win32" else None,
    target_name="محول_كتب_الشاملة.exe",
    icon=None  # يمكنك إضافة أيقونة هنا
)

setup(
    name="محول كتب الشاملة",
    version="1.0",
    description="تطبيق لتحويل كتب الشاملة من Access إلى MySQL",
    author="مساعد ذكي",
    options={"build_exe": build_options},
    executables=[exe]
)
