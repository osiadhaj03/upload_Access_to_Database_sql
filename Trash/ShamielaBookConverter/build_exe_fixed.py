#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت بناء ملف EXE لمحول كتب الشاملة - محسن لحل مشكلة MySQL
يستخدم PyInstaller لإنشاء ملف تنفيذي مستقل

المطور: GitHub Copilot AI Assistant
الإصدار: 2.0 - إصلاح MySQL
"""

import os
import sys
import shutil
import subprocess
import tempfile
from pathlib import Path

class ShamielaBuilderFixed:
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.src_dir = self.project_dir / "src"
        self.build_dir = self.project_dir / "build"
        self.dist_dir = self.project_dir / "dist"
        self.resources_dir = self.project_dir / "resources"
        
        # معلومات التطبيق
        self.app_name = "ShamielaConverter"
        self.app_version = "2.0.1"
        self.app_description = "محول كتب الشاملة"
        
    def check_requirements(self):
        """فحص المتطلبات المطلوبة للبناء"""
        print("🔍 فحص متطلبات البناء...")
        
        # فحص PyInstaller
        try:
            import PyInstaller
            print(f"✅ PyInstaller {PyInstaller.__version__}")
        except ImportError:
            print("❌ PyInstaller غير مثبت. ثبته بالأمر:")
            print("pip install pyinstaller")
            return False
        
        # فحص mysql.connector
        try:
            import mysql.connector
            print(f"✅ MySQL Connector")
        except ImportError:
            print("❌ MySQL Connector غير مثبت")
            return False
        
        # فحص pyodbc
        try:
            import pyodbc
            print(f"✅ pyodbc")
        except ImportError:
            print("❌ pyodbc غير مثبت")
            return False
        
        # فحص الملفات الأساسية
        required_files = [
            self.project_dir / "main.py",
            self.src_dir / "shamela_gui.py", 
            self.src_dir / "shamela_converter.py",
            self.src_dir / "simple_bok_support.py"
        ]
        
        for file_path in required_files:
            if file_path.exists():
                print(f"✅ {file_path.name}")
            else:
                print(f"❌ ملف مفقود: {file_path}")
                return False
        
        return True
    
    def clean_build_dirs(self):
        """تنظيف مجلدات البناء القديمة"""
        print("🧹 تنظيف مجلدات البناء...")
        
        dirs_to_clean = [self.build_dir, self.dist_dir]
        for dir_path in dirs_to_clean:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                print(f"🗑️ تم حذف: {dir_path}")
        
        # إنشاء المجلدات الجديدة
        self.build_dir.mkdir(exist_ok=True)
        self.dist_dir.mkdir(exist_ok=True)
    
    def find_mysql_libs(self):
        """البحث عن مكتبات MySQL"""
        mysql_paths = []
        
        try:
            import mysql.connector
            mysql_path = Path(mysql.connector.__file__).parent
            mysql_paths.append(str(mysql_path))
            print(f"🔍 وُجدت مكتبة MySQL في: {mysql_path}")
        except:
            pass
        
        return mysql_paths
    
    def create_fixed_spec_file(self):
        """إنشاء ملف .spec محسن لحل مشكلة MySQL"""
        
        mysql_paths = self.find_mysql_libs()
        icon_path = self.resources_dir / "icons" / "app_icon.ico"
        
        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
# ملف .spec محسن لحل مشكلة MySQL authentication plugin

import os
import sys
from pathlib import Path

# المسارات
project_dir = Path(r"{self.project_dir}")
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
    hooksconfig={{}},
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
    name='{self.app_name}',
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
    {"icon='" + str(icon_path) + "'," if icon_path.exists() else ""}
    version='version_info.txt'
)
'''
        
        spec_file = self.project_dir / f"{self.app_name}.spec"
        with open(spec_file, 'w', encoding='utf-8') as f:
            f.write(spec_content)
        
        print(f"📄 تم إنشاء ملف .spec: {spec_file}")
        return spec_file
    
    def create_version_file(self):
        """إنشاء ملف معلومات الإصدار"""
        version_info = f"""# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(2, 0, 1, 0),
    prodvers=(2, 0, 1, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'GitHub Copilot AI Assistant'),
        StringStruct(u'FileDescription', u'{self.app_description}'),
        StringStruct(u'FileVersion', u'{self.app_version}'),
        StringStruct(u'InternalName', u'{self.app_name}'),
        StringStruct(u'LegalCopyright', u'© 2025 GitHub Copilot AI Assistant'),
        StringStruct(u'OriginalFilename', u'{self.app_name}.exe'),
        StringStruct(u'ProductName', u'{self.app_description}'),
        StringStruct(u'ProductVersion', u'{self.app_version}')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)"""
        
        version_file = self.project_dir / "version_info.txt"
        with open(version_file, 'w', encoding='utf-8') as f:
            f.write(version_info)
        
        return version_file
    
    def build_exe_fixed(self):
        """بناء ملف EXE محسن لحل مشكلة MySQL"""
        print("🚀 بدء بناء ملف EXE المحسن...")
        
        # تنظيف المجلدات القديمة
        self.clean_build_dirs()
        
        # إنشاء ملف .spec محسن
        spec_file = self.create_fixed_spec_file()
        
        # إنشاء ملف معلومات الإصدار
        version_file = self.create_version_file()
        
        # تشغيل PyInstaller مع ملف .spec
        pyinstaller_args = [
            "pyinstaller",
            "--distpath", str(self.dist_dir),
            "--workpath", str(self.build_dir),
            str(spec_file)
        ]
        
        print("📋 أوامر PyInstaller:")
        print(" ".join(pyinstaller_args))
        
        try:
            # تشغيل PyInstaller
            result = subprocess.run(pyinstaller_args,
                                  capture_output=True,
                                  text=True,
                                  cwd=str(self.project_dir))
            
            if result.returncode == 0:
                print("✅ تم بناء ملف EXE بنجاح!")
                
                # نسخ الملفات الإضافية
                self.copy_additional_files()
                
                # إظهار معلومات الملف النهائي
                self.show_build_info()
                
                return True
            else:
                print("❌ فشل في بناء ملف EXE:")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                return False
                
        except Exception as e:
            print(f"❌ خطأ في تشغيل PyInstaller: {e}")
            return False
    
    def copy_additional_files(self):
        """نسخ ملفات إضافية إلى مجلد التوزيع"""
        print("📁 نسخ ملفات إضافية...")
        
        # ملفات للنسخ
        files_to_copy = [
            ("README.md", "اقرأني.txt"),
            ("requirements.txt", "المتطلبات.txt"),
        ]
        
        for src_name, dst_name in files_to_copy:
            src_file = self.project_dir / src_name
            dst_file = self.dist_dir / dst_name
            
            if src_file.exists():
                shutil.copy2(src_file, dst_file)
                print(f"📄 تم نسخ: {dst_name}")
    
    def show_build_info(self):
        """إظهار معلومات البناء النهائية"""
        exe_file = self.dist_dir / f"{self.app_name}.exe"
        
        if exe_file.exists():
            file_size = exe_file.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            
            print("\n" + "="*60)
            print("🎉 تم إنشاء ملف EXE بنجاح!")
            print("="*60)
            print(f"📁 المجلد: {self.dist_dir}")
            print(f"📄 الملف: {exe_file.name}")
            print(f"📏 الحجم: {file_size_mb:.2f} ميغابايت")
            print(f"🔢 الإصدار: {self.app_version}")
            print("="*60)
            print("💡 نصائح التشغيل:")
            print("- تأكد من اتصال الإنترنت لقاعدة البيانات")
            print("- تأكد من تثبيت Microsoft Access ODBC Driver")
            print("- شغل البرنامج كمدير إذا واجهت مشاكل في الصلاحيات")
            print("="*60)
        else:
            print("❌ لم يتم العثور على ملف EXE")
    
    def run_build(self):
        """تشغيل عملية البناء الكاملة"""
        print("🚀 بدء عملية بناء محول كتب الشاملة المحسن")
        print("="*60)
        
        # فحص المتطلبات
        if not self.check_requirements():
            print("❌ فشل في فحص المتطلبات")
            return False
        
        # بناء ملف EXE
        if not self.build_exe_fixed():
            print("❌ فشل في بناء ملف EXE")
            return False
        
        print("\n🎉 تمت عملية البناء بنجاح!")
        return True

def main():
    """الدالة الرئيسية"""
    builder = ShamielaBuilderFixed()
    
    try:
        success = builder.run_build()
        if success:
            print("\n✅ تمت العملية بنجاح!")
            print("يمكنك الآن تشغيل ملف EXE من مجلد dist")
        else:
            print("\n❌ فشلت العملية!")
            
    except KeyboardInterrupt:
        print("\n⏹️ تم إلغاء العملية بواسطة المستخدم")
    except Exception as e:
        print(f"\n❌ خطأ غير متوقع: {e}")

if __name__ == "__main__":
    main()