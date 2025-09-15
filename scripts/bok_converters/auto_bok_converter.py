#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
محول ملفات .bok إلى .accdb تلقائياً
يحاكي عملية Access في تحويل الملفات
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

class AutoBokConverter:
    """محول تلقائي لملفات .bok"""
    
    def __init__(self):
        self.access_installed = self.check_access_installation()
        self.conversion_count = 0
    
    def check_access_installation(self):
        """فحص إذا كان Access مثبت"""
        try:
            # فحص وجود Access
            access_paths = [
                r"C:\Program Files\Microsoft Office\root\Office16\MSACCESS.EXE",
                r"C:\Program Files (x86)\Microsoft Office\root\Office16\MSACCESS.EXE",
                r"C:\Program Files\Microsoft Office\Office16\MSACCESS.EXE",
                r"C:\Program Files (x86)\Microsoft Office\Office16\MSACCESS.EXE"
            ]
            
            for path in access_paths:
                if os.path.exists(path):
                    print(f"✅ تم العثور على Access: {path}")
                    return path
            
            print("❌ Access غير مثبت")
            return None
            
        except Exception as e:
            print(f"❌ خطأ في فحص Access: {e}")
            return None
    
    def convert_bok_to_accdb_manual(self, bok_path, output_dir=None):
        """تحويل يدوي - نسخ وتغيير امتداد"""
        try:
            print(f"🔄 بدء التحويل اليدوي: {os.path.basename(bok_path)}")
            
            # تحديد مجلد الحفظ
            if output_dir is None:
                output_dir = os.path.dirname(bok_path)
            
            # إنشاء اسم الملف الجديد
            base_name = os.path.splitext(os.path.basename(bok_path))[0]
            accdb_path = os.path.join(output_dir, f"{base_name}_converted.accdb")
            
            # نسخ الملف
            shutil.copy2(bok_path, accdb_path)
            
            print(f"✅ تم التحويل: {accdb_path}")
            self.conversion_count += 1
            return accdb_path
            
        except Exception as e:
            print(f"❌ فشل التحويل اليدوي: {e}")
            return None
    
    def convert_bok_with_access(self, bok_path, output_dir=None):
        """تحويل باستخدام Access (إذا كان متوفر)"""
        if not self.access_installed:
            print("❌ Access غير متوفر للتحويل التلقائي")
            return None
        
        try:
            print(f"🔄 بدء التحويل باستخدام Access: {os.path.basename(bok_path)}")
            
            # إنشاء سكريپت VBS للتحويل
            vbs_script = self.create_access_conversion_script(bok_path, output_dir)
            
            # تشغيل السكريپت
            result = subprocess.run(['cscript', vbs_script], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ تم التحويل باستخدام Access بنجاح")
                self.conversion_count += 1
                return self.get_converted_file_path(bok_path, output_dir)
            else:
                print(f"❌ فشل التحويل: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"❌ خطأ في التحويل باستخدام Access: {e}")
            return None
    
    def create_access_conversion_script(self, bok_path, output_dir):
        """إنشاء سكريپت VBS لتحويل Access"""
        # تحديد مسار الحفظ
        if output_dir is None:
            output_dir = os.path.dirname(bok_path)
        
        base_name = os.path.splitext(os.path.basename(bok_path))[0]
        accdb_path = os.path.join(output_dir, f"{base_name}_converted.accdb")
        
        # محتوى السكريپت
        vbs_content = f'''
Dim accessApp, db
Set accessApp = CreateObject("Access.Application")

' فتح ملف .bok
Set db = accessApp.OpenDatabase("{bok_path}")

' حفظ كـ .accdb
accessApp.CompactRepair "{bok_path}", "{accdb_path}", True

' إغلاق
db.Close
accessApp.Quit
Set accessApp = Nothing

WScript.Echo "تم التحويل بنجاح"
'''
        
        # حفظ السكريپت
        script_path = os.path.join(tempfile.gettempdir(), "convert_bok.vbs")
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(vbs_content)
        
        return script_path
    
    def get_converted_file_path(self, bok_path, output_dir):
        """الحصول على مسار الملف المحول"""
        if output_dir is None:
            output_dir = os.path.dirname(bok_path)
        
        base_name = os.path.splitext(os.path.basename(bok_path))[0]
        return os.path.join(output_dir, f"{base_name}_converted.accdb")
    
    def batch_convert_bok_files(self, bok_folder, output_folder=None):
        """تحويل جميع ملفات .bok في مجلد"""
        print(f"🔄 بدء التحويل المجمع للمجلد: {bok_folder}")
        
        bok_files = list(Path(bok_folder).glob("*.bok"))
        
        if not bok_files:
            print("❌ لم يتم العثور على ملفات .bok")
            return []
        
        print(f"📁 تم العثور على {len(bok_files)} ملف .bok")
        
        converted_files = []
        
        for bok_file in bok_files:
            print(f"\n--- معالجة: {bok_file.name} ---")
            
            # جرب التحويل باستخدام Access أولاً
            converted_path = self.convert_bok_with_access(str(bok_file), output_folder)
            
            # إذا فشل، جرب التحويل اليدوي
            if not converted_path:
                converted_path = self.convert_bok_to_accdb_manual(str(bok_file), output_folder)
            
            if converted_path:
                converted_files.append(converted_path)
                print(f"✅ نجح: {os.path.basename(converted_path)}")
            else:
                print(f"❌ فشل: {bok_file.name}")
        
        print(f"\n📊 النتائج النهائية:")
        print(f"   المعالج: {len(bok_files)} ملف")
        print(f"   المحول بنجاح: {self.conversion_count} ملف")
        print(f"   الفاشل: {len(bok_files) - self.conversion_count} ملف")
        
        return converted_files

def main():
    """الدالة الرئيسية"""
    print("=== محول ملفات .bok إلى .accdb ===")
    print("=" * 40)
    
    converter = AutoBokConverter()
    
    # مجلد ملفات .bok
    bok_folder = r"d:\test3\bok file"
    output_folder = r"d:\test3\converted_books"
    
    # إنشاء مجلد الحفظ
    os.makedirs(output_folder, exist_ok=True)
    
    # تحويل جميع الملفات
    converted_files = converter.batch_convert_bok_files(bok_folder, output_folder)
    
    print(f"\n🎉 تم الانتهاء!")
    print(f"الملفات المحولة محفوظة في: {output_folder}")
    
    # عرض قائمة الملفات المحولة
    if converted_files:
        print("\n📋 الملفات المحولة:")
        for file in converted_files:
            print(f"   ✅ {os.path.basename(file)}")

if __name__ == "__main__":
    main()
