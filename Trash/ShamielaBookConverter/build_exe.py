#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت بناء ملف EXE لمحول كتب الشاملة
يستخدم PyInstaller لإنشاء ملف تنفيذي مستقل

المطور: GitHub Copilot AI Assistant
الإصدار: 2.0
"""

import os
import sys
import shutil
import subprocess
import tempfile
from pathlib import Path

class ShamielaBuilder:
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.src_dir = self.project_dir / "src"
        self.build_dir = self.project_dir / "build"
        self.dist_dir = self.project_dir / "dist"
        self.resources_dir = self.project_dir / "resources"
        
        # معلومات التطبيق
        self.app_name = "ShamielaConverter"
        self.app_version = "2.0.0"
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
        """تنظيف مجلدات البناء"""
        print("🧹 تنظيف مجلدات البناء...")
        
        dirs_to_clean = [self.build_dir, self.dist_dir]
        
        for dir_path in dirs_to_clean:
            if dir_path.exists():
                try:
                    shutil.rmtree(dir_path)
                    print(f"✅ تم حذف: {dir_path.name}")
                except Exception as e:
                    print(f"⚠️ تعذر حذف {dir_path.name}: {e}")
        
        # إنشاء المجلدات من جديد
        self.build_dir.mkdir(exist_ok=True)
        self.dist_dir.mkdir(exist_ok=True)
    
    def create_version_file(self):
        """إنشاء ملف معلومات الإصدار"""
        version_info = f"""# UTF-8
#
# معلومات إصدار محول كتب الشاملة
#
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({self.app_version.replace('.', ', ')}, 0),
    prodvers=({self.app_version.replace('.', ', ')}, 0),
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
        
        version_file = self.build_dir / "version_info.txt"
        with open(version_file, 'w', encoding='utf-8') as f:
            f.write(version_info)
        
        return version_file
    
    def create_spec_file(self):
        """إنشاء ملف .spec مخصص"""
        
        # إعداد المسارات
        icon_path = self.resources_dir / "icons" / "app_icon.ico"
        if not icon_path.exists():
            icon_path = None
        
        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

# المسارات
project_dir = Path(r"{self.project_dir}")
src_dir = project_dir / "src"
resources_dir = project_dir / "resources"

# إضافة مجلد src إلى مسار Python
sys.path.insert(0, str(src_dir))

# تحديد الملفات المطلوبة
a = Analysis(
    [str(project_dir / "main.py")],
    pathex=[str(project_dir), str(src_dir)],
    binaries=[],
    datas=[
        (str(resources_dir), "resources"),
    ],
    hiddenimports=[
        "tkinter",
        "tkinter.ttk",
        "tkinter.filedialog",
        "tkinter.messagebox",
        "tkinter.scrolledtext",
        "pyodbc",
        "mysql.connector",
        "queue",
        "threading",
        "json",
        "datetime",
        "pathlib",
        "uuid",
        "re",
        "os",
        "sys",
        "shutil",
        "tempfile",
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        "test",
        "tests",
        "unittest",
        "doctest",
        "pdb",
        "pydoc",
        "difflib",
    ],
    noarchive=False,
    optimize=0,
)

# إزالة الملفات غير المطلوبة
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="{self.app_name}",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # لا نريد نافذة وحدة التحكم
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=r"{icon_path}" if {icon_path is not None} else None,
    version=r"{self.create_version_file()}",
)'''

        spec_file = self.build_dir / f"{self.app_name}.spec"
        with open(spec_file, 'w', encoding='utf-8') as f:
            f.write(spec_content)
        
        return spec_file
    
    def build_executable(self):
        """بناء الملف التنفيذي"""
        print("🔨 بناء الملف التنفيذي...")
        
        # إنشاء ملف .spec
        spec_file = self.create_spec_file()
        print(f"✅ تم إنشاء: {spec_file.name}")
        
        # تشغيل PyInstaller
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--distpath", str(self.dist_dir),
            "--workpath", str(self.build_dir / "work"),
            "--clean",
            str(spec_file)
        ]
        
        print("🚀 تشغيل PyInstaller...")
        print(f"الأمر: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, cwd=self.project_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ تم بناء الملف التنفيذي بنجاح!")
                return True
            else:
                print("❌ فشل في بناء الملف التنفيذي:")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                return False
                
        except Exception as e:
            print(f"❌ خطأ في تشغيل PyInstaller: {e}")
            return False
    
    def test_executable(self):
        """اختبار الملف التنفيذي"""
        exe_path = self.dist_dir / f"{self.app_name}.exe"
        
        if not exe_path.exists():
            print(f"❌ الملف التنفيذي غير موجود: {exe_path}")
            return False
        
        print("🧪 اختبار الملف التنفيذي...")
        
        # فحص حجم الملف
        file_size = exe_path.stat().st_size
        print(f"📏 حجم الملف: {file_size:,} بايت ({file_size/1024/1024:.1f} MB)")
        
        if file_size < 1024 * 1024:  # أقل من 1 MB
            print("⚠️ حجم الملف صغير جداً، قد يكون هناك مشكلة")
        
        # محاولة تشغيل سريع للتحقق من عدم وجود أخطاء فادحة
        try:
            result = subprocess.run([str(exe_path), "--version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("✅ الملف التنفيذي يعمل بشكل أساسي")
            else:
                print("⚠️ قد تكون هناك مشاكل في التشغيل")
        except subprocess.TimeoutExpired:
            print("⚠️ انتهت مهلة الاختبار - قد يحتاج لتدخل المستخدم")
        except Exception as e:
            print(f"⚠️ تعذر اختبار التشغيل: {e}")
        
        return True
    
    def create_package_info(self):
        """إنشاء ملف معلومات الحزمة"""
        exe_path = self.dist_dir / f"{self.app_name}.exe"
        
        if not exe_path.exists():
            return
        
        info = f"""
محول كتب الشاملة - الإصدار {self.app_version}
Shamela Books Converter - Version {self.app_version}

معلومات الحزمة:
- اسم الملف: {exe_path.name}
- حجم الملف: {exe_path.stat().st_size:,} بايت
- تاريخ البناء: {exe_path.stat().st_mtime}

متطلبات التشغيل:
- نظام التشغيل: Windows 10 أو أحدث
- Microsoft Access Database Engine (يأتي مع Office عادة)
- اتصال بالإنترنت (للاتصال بقاعدة البيانات)

طريقة الاستخدام:
1. شغل الملف {exe_path.name}
2. اختر ملفات الكتب (.accdb أو .bok)
3. أدخل إعدادات قاعدة البيانات
4. اضغط "بدء التحويل"

المطور: GitHub Copilot AI Assistant
التاريخ: 2025
        """
        
        info_file = self.dist_dir / "معلومات_التطبيق.txt"
        with open(info_file, 'w', encoding='utf-8') as f:
            f.write(info.strip())
        
        print(f"✅ تم إنشاء: {info_file.name}")
    
    def build(self):
        """بناء التطبيق كاملاً"""
        print("=" * 60)
        print("         بناء محول كتب الشاملة")
        print("        Shamela Books Converter Builder")
        print("=" * 60)
        
        # فحص المتطلبات
        if not self.check_requirements():
            return False
        
        # تنظيف المجلدات
        self.clean_build_dirs()
        
        # بناء الملف التنفيذي
        if not self.build_executable():
            return False
        
        # اختبار الملف التنفيذي
        if not self.test_executable():
            return False
        
        # إنشاء ملف المعلومات
        self.create_package_info()
        
        print("=" * 60)
        print("🎉 تم بناء التطبيق بنجاح!")
        print(f"📁 الملف التنفيذي: {self.dist_dir / f'{self.app_name}.exe'}")
        print("=" * 60)
        
        return True

def main():
    """الدالة الرئيسية"""
    builder = ShamielaBuilder()
    
    if builder.build():
        print("\n✅ انتهى البناء بنجاح!")
        
        # سؤال المستخدم عن فتح مجلد النتائج
        try:
            response = input("\nهل تريد فتح مجلد النتائج؟ (y/n): ").lower()
            if response in ['y', 'yes', 'نعم', 'ن']:
                import subprocess
                subprocess.run(['explorer', str(builder.dist_dir)], shell=True)
        except KeyboardInterrupt:
            pass
        
        return 0
    else:
        print("\n❌ فشل في البناء!")
        input("اضغط Enter للخروج...")
        return 1

if __name__ == "__main__":
    sys.exit(main())