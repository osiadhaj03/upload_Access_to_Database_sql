#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إعداد إضافي لحل مشاكل MySQL في PyInstaller
"""

import os
import sys
import site
import shutil
from pathlib import Path

def fix_mysql_for_pyinstaller():
    """إصلاح مشكلة MySQL مع PyInstaller"""
    print("🔧 إصلاح مشكلة MySQL للـ PyInstaller...")
    
    try:
        import mysql.connector
        mysql_path = Path(mysql.connector.__file__).parent
        
        print(f"📍 مكتبة MySQL موجودة في: {mysql_path}")
        
        # نسخ مكتبات MySQL إلى مجلد مؤقت
        temp_mysql = Path("temp_mysql_libs")
        if temp_mysql.exists():
            shutil.rmtree(temp_mysql)
        
        # نسخ المكتبات المطلوبة
        important_files = [
            "authentication.py",
            "constants.py", 
            "conversion.py",
            "cursor.py",
            "errors.py",
            "network.py",
            "protocol.py",
            "utils.py",
            "abstracts.py",
            "pooling.py",
            "locales"
        ]
        
        temp_mysql.mkdir(exist_ok=True)
        
        for item in important_files:
            src = mysql_path / item
            if src.exists():
                if src.is_file():
                    shutil.copy2(src, temp_mysql)
                    print(f"✅ نسخ ملف: {item}")
                elif src.is_dir():
                    shutil.copytree(src, temp_mysql / item)
                    print(f"✅ نسخ مجلد: {item}")
        
        print("✅ تم إعداد مكتبات MySQL بنجاح")
        return True
        
    except Exception as e:
        print(f"❌ خطأ في إعداد MySQL: {e}")
        return False

def create_mysql_hook():
    """إنشاء hook خاص لـ MySQL"""
    
    hook_content = '''"""
PyInstaller hook لمكتبة mysql.connector
"""

from PyInstaller.utils.hooks import collect_all, collect_submodules

# جمع جميع الوحدات الفرعية
hiddenimports = collect_submodules('mysql.connector')

# إضافة وحدات مخفية إضافية
hiddenimports += [
    'mysql.connector.locales.eng.client_error',
    'mysql.connector.constants',
    'mysql.connector.conversion', 
    'mysql.connector.cursor',
    'mysql.connector.errors',
    'mysql.connector.network',
    'mysql.connector.protocol',
    'mysql.connector.utils',
    'mysql.connector.abstracts',
    'mysql.connector.pooling',
    'mysql.connector.authentication',
    'mysql.connector.charsets',
    'mysql.connector.custom_types',
    'mysql.connector.dbapi',
    'mysql.connector.fabric',
    'mysql.connector.optionfiles',
]

# جمع جميع البيانات
datas, binaries, hiddenimports_collected = collect_all('mysql.connector')
hiddenimports += hiddenimports_collected
'''
    
    hook_file = Path("hook-mysql.connector.py")
    with open(hook_file, 'w', encoding='utf-8') as f:
        f.write(hook_content)
    
    print(f"📄 تم إنشاء hook: {hook_file}")
    return hook_file

def main():
    print("🔧 إعداد حل مشكلة MySQL...")
    
    # إصلاح MySQL
    if fix_mysql_for_pyinstaller():
        print("✅ تم إصلاح MySQL")
    
    # إنشاء hook
    hook_file = create_mysql_hook()
    if hook_file:
        print("✅ تم إنشاء hook")
    
    print("\n💡 الآن شغل build_exe_fixed.py لبناء ملف EXE محسن")

if __name__ == "__main__":
    main()