#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
حل متقدم لتحويل ملفات .bok 
يستخدم Access إذا كان متوفر أو يقترح بدائل
"""

import os
import subprocess
import tempfile
import shutil
from pathlib import Path

class AdvancedBokConverter:
    def __init__(self):
        self.access_path = self.find_access_installation()
        
    def find_access_installation(self):
        """البحث عن Access مثبت"""
        possible_paths = [
            r"C:\Program Files\Microsoft Office\root\Office16\MSACCESS.EXE",
            r"C:\Program Files (x86)\Microsoft Office\root\Office16\MSACCESS.EXE",
            r"C:\Program Files\Microsoft Office\Office16\MSACCESS.EXE",
            r"C:\Program Files (x86)\Microsoft Office\Office16\MSACCESS.EXE",
            r"C:\Program Files\Microsoft Office\Office15\MSACCESS.EXE",
            r"C:\Program Files (x86)\Microsoft Office\Office15\MSACCESS.EXE"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                print(f"✅ تم العثور على Access: {path}")
                return path
        
        print("❌ Access غير مثبت")
        return None
    
    def create_vbs_converter(self, bok_path, output_path):
        """إنشاء سكريپت VBS لتحويل Access"""
        vbs_content = f'''
On Error Resume Next

' إنشاء كائن Access
Dim accessApp
Set accessApp = CreateObject("Access.Application")

If Err.Number <> 0 Then
    WScript.Echo "ERROR: فشل في إنشاء كائن Access"
    WScript.Quit 1
End If

' إخفاء Access
accessApp.Visible = False

' فتح قاعدة البيانات الأصلية
Dim originalDb
Set originalDb = accessApp.OpenDatabase("{bok_path}")

If Err.Number <> 0 Then
    WScript.Echo "ERROR: فشل في فتح الملف الأصلي"
    accessApp.Quit
    WScript.Quit 1
End If

' إنشاء قاعدة بيانات جديدة
accessApp.NewCurrentDatabase "{output_path}"

If Err.Number <> 0 Then
    WScript.Echo "ERROR: فشل في إنشاء ملف جديد"
    originalDb.Close
    accessApp.Quit
    WScript.Quit 1
End If

' نسخ الجداول
Dim tbl
For Each tbl In originalDb.TableDefs
    If Left(tbl.Name, 4) <> "MSys" Then
        ' نسخ الجدول
        accessApp.DoCmd.TransferDatabase acImport, "Microsoft Access", "{bok_path}", acTable, tbl.Name, tbl.Name
        
        If Err.Number <> 0 Then
            WScript.Echo "WARNING: فشل في نسخ جدول " & tbl.Name
            Err.Clear
        Else
            WScript.Echo "SUCCESS: تم نسخ جدول " & tbl.Name
        End If
    End If
Next

' إغلاق قواعد البيانات
originalDb.Close
accessApp.CloseCurrentDatabase

' إنهاء Access
accessApp.Quit
Set accessApp = Nothing

WScript.Echo "COMPLETED: تم التحويل بنجاح"
'''
        
        # حفظ السكريپت
        script_path = os.path.join(tempfile.gettempdir(), "convert_bok_advanced.vbs")
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(vbs_content)
        
        return script_path
    
    def convert_bok_with_access(self, bok_path, output_dir=None):
        """تحويل ملف .bok باستخدام Access"""
        if not self.access_path:
            print("❌ Access غير متوفر - لا يمكن التحويل")
            return None
        
        try:
            print(f"🔄 بدء التحويل المتقدم: {os.path.basename(bok_path)}")
            
            # تحديد مسار الحفظ
            if output_dir is None:
                output_dir = os.path.dirname(bok_path)
            
            base_name = os.path.splitext(os.path.basename(bok_path))[0]
            output_path = os.path.join(output_dir, f"{base_name}_fixed.accdb")
            
            # إنشاء سكريپت VBS
            vbs_script = self.create_vbs_converter(bok_path, output_path)
            
            print("📝 تشغيل سكريپت التحويل...")
            
            # تشغيل السكريپت
            result = subprocess.run(
                ['cscript', '//NoLogo', vbs_script], 
                capture_output=True, 
                text=True,
                timeout=300  # 5 دقائق timeout
            )
            
            # حذف السكريپت المؤقت
            try:
                os.remove(vbs_script)
            except:
                pass
            
            if result.returncode == 0:
                print("✅ تم التحويل بنجاح!")
                print("📋 نتائج التحويل:")
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        print(f"   {line}")
                
                if os.path.exists(output_path):
                    return output_path
                else:
                    print("⚠️ الملف لم ينشأ رغم نجاح السكريپت")
                    return None
            else:
                print("❌ فشل في التحويل")
                print("خطأ:", result.stderr)
                return None
                
        except subprocess.TimeoutExpired:
            print("❌ انتهت مهلة التحويل (5 دقائق)")
            return None
        except Exception as e:
            print(f"❌ خطأ في التحويل: {e}")
            return None
    
    def batch_convert_with_access(self, bok_folder, output_folder=None):
        """تحويل مجمع باستخدام Access"""
        if not self.access_path:
            print("❌ Access غير متوفر للتحويل المجمع")
            return []
        
        print("🔄 بدء التحويل المجمع باستخدام Access...")
        
        bok_files = list(Path(bok_folder).glob("*.bok"))
        
        if not bok_files:
            print("❌ لم يتم العثور على ملفات .bok")
            return []
        
        if output_folder:
            os.makedirs(output_folder, exist_ok=True)
        
        converted_files = []
        
        for i, bok_file in enumerate(bok_files, 1):
            print(f"\n[{i}/{len(bok_files)}] معالجة: {bok_file.name}")
            
            converted_path = self.convert_bok_with_access(str(bok_file), output_folder)
            
            if converted_path:
                converted_files.append(converted_path)
                print(f"✅ نجح: {os.path.basename(converted_path)}")
            else:
                print(f"❌ فشل: {bok_file.name}")
        
        print(f"\n📊 النتائج النهائية:")
        print(f"   نجح: {len(converted_files)}/{len(bok_files)}")
        
        return converted_files

def create_manual_instructions():
    """إنشاء تعليمات يدوية مفصلة"""
    instructions = """
# تعليمات التحويل اليدوي لملفات .bok

## الطريقة الصحيحة (مضمونة 100%):

### الخطوة 1: فتح Microsoft Access
1. شغل Microsoft Access
2. اختر "Open Other Files" أو "فتح ملفات أخرى"

### الخطوة 2: فتح ملف .bok
1. اختر "Browse" أو "استعراض"
2. في نافذة اختيار الملف:
   - غير نوع الملف إلى "All Files (*.*)"
   - اختر ملف .bok المطلوب
3. اضغط "Open"

### الخطوة 3: حفظ كـ .accdb جديد
1. من القائمة: File → Save As
2. اختر "Access Database (*.accdb)"
3. اختر موقع الحفظ
4. اكتب اسم جديد للملف
5. اضغط "Save"

### الخطوة 4: التحقق من النتيجة
1. أغلق Access
2. جرب فتح الملف الجديد في التطبيق
3. إذا عمل بدون أخطاء = نجح التحويل ✅

## نصائح مهمة:
- احتفظ بالملف الأصلي .bok كنسخة احتياطية
- استخدم أسماء واضحة للملفات الجديدة
- تأكد من وجود مساحة كافية على القرص
- لا تقاطع عملية الحفظ

## إذا فشلت الطريقة اليدوية:
1. تأكد من أن Access محدث لآخر إصدار
2. جرب إعادة تشغيل الكمبيوتر
3. تأكد من صلاحيات الكتابة في مجلد الحفظ
4. جرب حفظ الملف في مجلد مختلف
"""
    
    with open("manual_conversion_guide.md", "w", encoding="utf-8") as f:
        f.write(instructions)
    
    print("📄 تم إنشاء دليل التحويل اليدوي: manual_conversion_guide.md")

def main():
    """الدالة الرئيسية"""
    print("=== محول ملفات .bok المتقدم ===")
    print("=" * 40)
    
    converter = AdvancedBokConverter()
    
    if converter.access_path:
        print("✅ Access متوفر - يمكن التحويل التلقائي")
        
        # التحويل التلقائي
        bok_folder = r"d:\test3\bok file"
        output_folder = r"d:\test3\fixed_books"
        
        converted_files = converter.batch_convert_with_access(bok_folder, output_folder)
        
        if converted_files:
            print("\n🎉 تم التحويل بنجاح!")
            print("الملفات الجديدة:")
            for file in converted_files:
                print(f"   📁 {os.path.basename(file)}")
        else:
            print("\n❌ فشل التحويل التلقائي")
            print("💡 استخدم الطريقة اليدوية")
    else:
        print("❌ Access غير متوفر")
        print("💡 ستحتاج التحويل اليدوي")
    
    # إنشاء دليل التحويل اليدوي
    create_manual_instructions()
    
    print(f"\n{'='*40}")
    print("انتهى المحول المتقدم")

if __name__ == "__main__":
    main()
