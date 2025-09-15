#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
محول تلقائي من .bok إلى .accdb - طريقة مباشرة وقوية
يحاكي الطريقة اليدوية التي تعمل بشكل ممتاز
"""

import os
import shutil
import subprocess
import time
from pathlib import Path
import win32com.client
import pythoncom

class AutomaticBokToAccessConverter:
    """محول تلقائي قوي من .bok إلى .accdb"""
    
    def __init__(self):
        self.temp_dir = Path("d:/test3/temp_conversion")
        self.temp_dir.mkdir(exist_ok=True)
        
    def convert_bok_to_access_method1(self, bok_file_path, output_dir=None):
        """الطريقة الأولى: استخدام Access Automation"""
        try:
            print(f"🔄 بدء التحويل التلقائي: {os.path.basename(bok_file_path)}")
            
            if output_dir is None:
                output_dir = os.path.dirname(bok_file_path)
            
            base_name = os.path.splitext(os.path.basename(bok_file_path))[0]
            output_path = os.path.join(output_dir, f"{base_name}_converted.accdb")
            
            # تهيئة COM
            pythoncom.CoInitialize()
            
            try:
                # إنشاء تطبيق Access
                access_app = win32com.client.Dispatch("Access.Application")
                access_app.Visible = False
                
                print("📂 فتح ملف .bok في Access...")
                
                # محاولة فتح ملف .bok مباشرة
                try:
                    access_app.OpenCurrentDatabase(bok_file_path)
                    
                    print("💾 حفظ كملف .accdb...")
                    
                    # حفظ بصيغة Access 2016
                    access_app.Application.CompactRepair(bok_file_path, output_path)
                    
                    access_app.CloseCurrentDatabase()
                    access_app.Quit()
                    
                    print(f"✅ تم التحويل بنجاح: {output_path}")
                    return output_path, True
                    
                except Exception as e:
                    print(f"❌ فشل في فتح الملف مباشرة: {e}")
                    access_app.Quit()
                    return None, False
                    
            finally:
                pythoncom.CoUninitialize()
                
        except Exception as e:
            print(f"❌ خطأ في الطريقة الأولى: {e}")
            return None, False
    
    def convert_bok_to_access_method2(self, bok_file_path, output_dir=None):
        """الطريقة الثانية: نسخ وإعادة تسمية مع إصلاح البنية"""
        try:
            print(f"🔄 الطريقة الثانية: {os.path.basename(bok_file_path)}")
            
            if output_dir is None:
                output_dir = os.path.dirname(bok_file_path)
            
            base_name = os.path.splitext(os.path.basename(bok_file_path))[0]
            temp_path = self.temp_dir / f"{base_name}_temp.accdb"
            output_path = os.path.join(output_dir, f"{base_name}_converted.accdb")
            
            # نسخ الملف
            print("📋 نسخ الملف...")
            shutil.copy2(bok_file_path, temp_path)
            
            # محاولة إصلاح الملف باستخدام Access
            print("🔧 إصلاح بنية الملف...")
            
            pythoncom.CoInitialize()
            
            try:
                access_app = win32com.client.Dispatch("Access.Application")
                access_app.Visible = False
                
                # إصلاح وضغط الملف
                access_app.CompactRepair(str(temp_path), output_path)
                access_app.Quit()
                
                # تنظيف الملف المؤقت
                if temp_path.exists():
                    temp_path.unlink()
                
                print(f"✅ تم التحويل والإصلاح: {output_path}")
                return output_path, True
                
            except Exception as e:
                print(f"❌ فشل في إصلاح الملف: {e}")
                access_app.Quit()
                return None, False
                
            finally:
                pythoncom.CoUninitialize()
                
        except Exception as e:
            print(f"❌ خطأ في الطريقة الثانية: {e}")
            return None, False
    
    def convert_bok_to_access_method3(self, bok_file_path, output_dir=None):
        """الطريقة الثالثة: استخدام أدوات خارجية"""
        try:
            print(f"🔄 الطريقة الثالثة: {os.path.basename(bok_file_path)}")
            
            if output_dir is None:
                output_dir = os.path.dirname(bok_file_path)
            
            base_name = os.path.splitext(os.path.basename(bok_file_path))[0]
            output_path = os.path.join(output_dir, f"{base_name}_converted.accdb")
            
            # محاولة استخدام PowerShell مع Access
            ps_script = f'''
            $access = New-Object -ComObject Access.Application
            $access.Visible = $false
            try {{
                $access.OpenCurrentDatabase("{bok_file_path}")
                $access.CompactRepair("{bok_file_path}", "{output_path}")
                $access.CloseCurrentDatabase()
            }}
            catch {{
                Write-Error "فشل في التحويل: $_"
            }}
            finally {{
                $access.Quit()
                [System.Runtime.Interopservices.Marshal]::ReleaseComObject($access)
            }}
            '''
            
            # تشغيل PowerShell script
            result = subprocess.run([
                "powershell", "-Command", ps_script
            ], capture_output=True, text=True, encoding='utf-8')
            
            if os.path.exists(output_path):
                print(f"✅ تم التحويل بـ PowerShell: {output_path}")
                return output_path, True
            else:
                print(f"❌ فشل التحويل بـ PowerShell: {result.stderr}")
                return None, False
                
        except Exception as e:
            print(f"❌ خطأ في الطريقة الثالثة: {e}")
            return None, False
    
    def convert_bok_file(self, bok_file_path, output_dir=None):
        """تحويل ملف .bok مع تجريب كل الطرق"""
        
        print(f"\n{'='*60}")
        print(f"🚀 بدء التحويل التلقائي الشامل")
        print(f"📁 ملف المصدر: {bok_file_path}")
        print(f"{'='*60}")
        
        if not os.path.exists(bok_file_path):
            print("❌ الملف غير موجود!")
            return None, False
        
        # تجريب الطرق الثلاث
        methods = [
            ("الطريقة الأولى - Access Automation", self.convert_bok_to_access_method1),
            ("الطريقة الثانية - نسخ وإصلاح", self.convert_bok_to_access_method2),
            ("الطريقة الثالثة - PowerShell", self.convert_bok_to_access_method3)
        ]
        
        for method_name, method_func in methods:
            print(f"\n🔄 تجريب {method_name}...")
            try:
                output_path, success = method_func(bok_file_path, output_dir)
                
                if success and output_path and os.path.exists(output_path):
                    # التحقق من صحة الملف المحول
                    if self.verify_converted_file(output_path):
                        print(f"✅ نجح التحويل مع {method_name}")
                        return output_path, True
                    else:
                        print(f"⚠️ الملف المحول غير صالح - حذف الملف")
                        try:
                            os.remove(output_path)
                        except:
                            pass
                
            except Exception as e:
                print(f"❌ فشل {method_name}: {e}")
        
        print("❌ فشل جميع طرق التحويل!")
        return None, False
    
    def verify_converted_file(self, file_path):
        """التحقق من صحة الملف المحول"""
        try:
            # فحص حجم الملف
            file_size = os.path.getsize(file_path)
            if file_size < 1000:  # ملف صغير جداً
                print(f"⚠️ الملف صغير جداً: {file_size} بايت")
                return False
            
            # محاولة فتح الملف مع pyodbc للتحقق
            import pyodbc
            
            conn_str = (
                r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
                f'DBQ={file_path};'
                'PWD=;'
            )
            
            try:
                conn = pyodbc.connect(conn_str)
                cursor = conn.cursor()
                
                # فحص الجداول
                tables = cursor.tables(tableType='TABLE').fetchall()
                table_count = len([t for t in tables if not t.table_name.startswith('MSys')])
                
                conn.close()
                
                if table_count > 0:
                    print(f"✅ ملف صالح - يحتوي على {table_count} جدول")
                    return True
                else:
                    print("⚠️ الملف لا يحتوي على جداول")
                    return False
                    
            except Exception as e:
                print(f"⚠️ لا يمكن فتح الملف: {e}")
                return False
                
        except Exception as e:
            print(f"❌ خطأ في التحقق: {e}")
            return False
    
    def batch_convert_bok_files(self, bok_folder, output_folder=None):
        """تحويل مجموعة من ملفات .bok"""
        
        bok_folder = Path(bok_folder)
        if output_folder:
            output_folder = Path(output_folder)
            output_folder.mkdir(exist_ok=True)
        else:
            output_folder = bok_folder
        
        bok_files = list(bok_folder.glob("*.bok"))
        
        if not bok_files:
            print("❌ لم يتم العثور على ملفات .bok")
            return []
        
        print(f"🔍 تم العثور على {len(bok_files)} ملف .bok")
        
        successful_conversions = []
        
        for i, bok_file in enumerate(bok_files, 1):
            print(f"\n{'='*80}")
            print(f"[{i}/{len(bok_files)}] معالجة: {bok_file.name}")
            print(f"{'='*80}")
            
            output_path, success = self.convert_bok_file(str(bok_file), str(output_folder))
            
            if success:
                successful_conversions.append({
                    'source': str(bok_file),
                    'output': output_path,
                    'size': os.path.getsize(output_path)
                })
                print(f"✅ تم بنجاح: {os.path.basename(output_path)}")
            else:
                print(f"❌ فشل: {bok_file.name}")
        
        # النتائج النهائية
        print(f"\n{'='*80}")
        print(f"🎉 النتائج النهائية:")
        print(f"   نجح: {len(successful_conversions)}/{len(bok_files)} ملف")
        print(f"{'='*80}")
        
        if successful_conversions:
            print("\n📁 الملفات المحولة:")
            for result in successful_conversions:
                size_mb = result['size'] / (1024*1024)
                print(f"   ✅ {os.path.basename(result['output'])} ({size_mb:.1f} MB)")
        
        return successful_conversions

def main():
    """الدالة الرئيسية"""
    print("=== محول تلقائي من .bok إلى .accdb ===")
    print("=" * 45)
    
    # مجلد ملفات .bok
    bok_folder = Path("d:/test3/bok file")
    output_folder = Path("d:/test3/auto_converted")
    
    if not bok_folder.exists():
        print(f"❌ مجلد .bok غير موجود: {bok_folder}")
        return
    
    # إنشاء مجلد الحفظ
    output_folder.mkdir(exist_ok=True)
    
    converter = AutomaticBokToAccessConverter()
    
    # تحويل جميع الملفات
    results = converter.batch_convert_bok_files(bok_folder, output_folder)
    
    if results:
        print(f"\n💡 الخطوة التالية:")
        print(f"   استخدم الملفات المحولة في {output_folder}")
        print(f"   يمكن الآن تحميلها في التطبيق الرئيسي")
    else:
        print("\n❌ لم يتم تحويل أي ملف بنجاح")
        print("   تحقق من:")
        print("   • وجود Microsoft Access مثبت")
        print("   • صحة ملفات .bok")
        print("   • صلاحيات الكتابة في المجلد")

if __name__ == "__main__":
    main()
