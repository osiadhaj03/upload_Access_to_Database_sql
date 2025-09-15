#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
حل شامل ونهائي لملفات .bok
تحويل مباشر ومعالجة ذكية للمشاكل
"""

import os
import shutil
import tempfile
import subprocess
from pathlib import Path

class UltimateBokSolution:
    """الحل النهائي والشامل لملفات .bok"""
    
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "shamela_ultimate"
        self.temp_dir.mkdir(exist_ok=True)
        self.converted_files = []
        
    def convert_bok_to_accdb_ultimate(self, bok_file_path, progress_callback=None):
        """التحويل النهائي والأقوى من .bok إلى .accdb"""
        
        def log(message):
            if progress_callback:
                progress_callback(message)
            print(message)
        
        try:
            log(f"🚀 بدء الحل النهائي: {os.path.basename(bok_file_path)}")
            
            # التحقق من الملف
            if not self.validate_bok_file(bok_file_path, log):
                return None, False
            
            # المحاولة الأولى: النسخ المباشر
            result = self.method_direct_copy(bok_file_path, log)
            if result[1]:
                return result
            
            # المحاولة الثانية: تحويل بـ Access Database Engine
            result = self.method_access_engine(bok_file_path, log)
            if result[1]:
                return result
            
            # المحاولة الثالثة: إصلاح الملف
            result = self.method_repair_and_convert(bok_file_path, log)
            if result[1]:
                return result
            
            # المحاولة الرابعة: تحويل البيانات مباشرة
            result = self.method_extract_data(bok_file_path, log)
            if result[1]:
                return result
                
            log("❌ فشلت جميع طرق التحويل")
            return None, False
            
        except Exception as e:
            log(f"❌ خطأ عام: {e}")
            return None, False
    
    def validate_bok_file(self, file_path, log_func):
        """التحقق من صحة ملف .bok"""
        log_func("🔍 فحص ملف .bok...")
        
        try:
            # فحص الوجود والحجم
            if not os.path.exists(file_path):
                log_func("❌ الملف غير موجود")
                return False
            
            file_size = os.path.getsize(file_path)
            if file_size < 50 * 1024:  # أقل من 50KB
                log_func(f"❌ الملف صغير جداً: {file_size:,} بايت")
                return False
            
            log_func(f"✅ حجم الملف مناسب: {file_size:,} بايت")
            
            # فحص header
            with open(file_path, 'rb') as f:
                header = f.read(200)
                
                # البحث عن signatures
                if b'Standard Jet DB' in header or b'Standard ACE DB' in header:
                    log_func("✅ تم التعرف على ملف Access")
                    return True
                elif header[0:4] == b'\x00\x01\x00\x00':
                    log_func("✅ بنية Jet Database صحيحة")
                    return True
                else:
                    log_func("⚠️ لم يتم التعرف على نوع الملف بوضوح، سيتم المحاولة")
                    return True
                    
        except Exception as e:
            log_func(f"❌ خطأ في الفحص: {e}")
            return False
    
    def method_direct_copy(self, bok_file_path, log_func):
        """الطريقة الأولى: النسخ المباشر"""
        log_func("📋 الطريقة 1: النسخ المباشر...")
        
        try:
            base_name = os.path.splitext(os.path.basename(bok_file_path))[0]
            output_path = self.temp_dir / f"{base_name}_ultimate.accdb"
            
            # نسخ الملف
            shutil.copy2(bok_file_path, output_path)
            
            if self.test_access_file(str(output_path), log_func):
                log_func("✅ نجح النسخ المباشر!")
                self.converted_files.append(str(output_path))
                return str(output_path), True
            else:
                try:
                    output_path.unlink()
                except:
                    pass
                log_func("❌ فشل النسخ المباشر")
                return None, False
                
        except Exception as e:
            log_func(f"❌ خطأ في النسخ المباشر: {e}")
            return None, False
    
    def method_access_engine(self, bok_file_path, log_func):
        """الطريقة الثانية: استخدام Access Database Engine"""
        log_func("🔧 الطريقة 2: Access Database Engine...")
        
        try:
            base_name = os.path.splitext(os.path.basename(bok_file_path))[0]
            output_path = self.temp_dir / f"{base_name}_engine.accdb"
            
            # استخدام compact و repair من Windows
            compact_cmd = [
                'compact', '/src', f'"{bok_file_path}"',
                '/dest', f'"{output_path}"'
            ]
            
            result = subprocess.run(
                ' '.join(compact_cmd), 
                shell=True, 
                capture_output=True, 
                timeout=60
            )
            
            if output_path.exists() and self.test_access_file(str(output_path), log_func):
                log_func("✅ نجح تحويل Access Engine!")
                self.converted_files.append(str(output_path))
                return str(output_path), True
            else:
                log_func("❌ فشل Access Engine")
                return None, False
                
        except Exception as e:
            log_func(f"❌ خطأ في Access Engine: {e}")
            return None, False
    
    def method_repair_and_convert(self, bok_file_path, log_func):
        """الطريقة الثالثة: إصلاح وتحويل"""
        log_func("🛠️ الطريقة 3: إصلاح وتحويل...")
        
        try:
            base_name = os.path.splitext(os.path.basename(bok_file_path))[0]
            temp_path = self.temp_dir / f"{base_name}_temp.bok"
            output_path = self.temp_dir / f"{base_name}_repaired.accdb"
            
            # نسخ إلى temp أولاً
            shutil.copy2(bok_file_path, temp_path)
            
            # محاولة إصلاح الملف باستخدام PowerShell
            ps_script = f'''
try {{
    Add-Type -AssemblyName "Microsoft.Office.Interop.Access"
    $access = New-Object -ComObject Access.Application
    $access.Visible = $false
    
    $access.CompactRepair("{temp_path}", "{output_path}")
    $access.Quit()
    
    Write-Output "SUCCESS"
}} catch {{
    Write-Output "ERROR: $_"
}} finally {{
    try {{ $access.Quit() }} catch {{}}
}}
'''
            
            result = subprocess.run([
                "powershell", "-ExecutionPolicy", "Bypass", 
                "-Command", ps_script
            ], capture_output=True, text=True, timeout=90)
            
            if output_path.exists() and self.test_access_file(str(output_path), log_func):
                log_func("✅ نجح الإصلاح والتحويل!")
                self.converted_files.append(str(output_path))
                return str(output_path), True
            else:
                log_func("❌ فشل الإصلاح والتحويل")
                return None, False
                
        except Exception as e:
            log_func(f"❌ خطأ في الإصلاح: {e}")
            return None, False
        finally:
            # تنظيف temp
            try:
                if temp_path.exists():
                    temp_path.unlink()
            except:
                pass
    
    def method_extract_data(self, bok_file_path, log_func):
        """الطريقة الرابعة: استخراج البيانات مباشرة"""
        log_func("📊 الطريقة 4: استخراج البيانات...")
        
        try:
            # هذه طريقة متقدمة لاستخراج البيانات
            # يمكن تطويرها لاحقاً إذا احتجناها
            log_func("⚠️ الطريقة 4 تحت التطوير")
            return None, False
            
        except Exception as e:
            log_func(f"❌ خطأ في استخراج البيانات: {e}")
            return None, False
    
    def test_access_file(self, file_path, log_func, quick_test=True):
        """اختبار ملف Access"""
        
        try:
            # فحص أساسي
            if not os.path.exists(file_path):
                return False
            
            file_size = os.path.getsize(file_path)
            if file_size < 1000:
                return False
            
            if quick_test:
                # اختبار سريع - فحص header فقط
                with open(file_path, 'rb') as f:
                    header = f.read(100)
                    access_indicators = [
                        b'Standard Jet DB',
                        b'Standard ACE DB',
                        b'Microsoft Jet DB'
                    ]
                    
                    for indicator in access_indicators:
                        if indicator in header:
                            log_func("✅ ملف Access صالح (فحص سريع)")
                            return True
                    
                    if header[0:4] == b'\x00\x01\x00\x00':
                        log_func("✅ بنية Jet صحيحة (فحص سريع)")
                        return True
                
                return False
            else:
                # اختبار كامل بـ pyodbc
                try:
                    import pyodbc
                    conn_str = (
                        r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
                        f'DBQ={file_path};'
                    )
                    
                    conn = pyodbc.connect(conn_str, timeout=5)
                    cursor = conn.cursor()
                    tables = cursor.tables(tableType='TABLE').fetchall()
                    conn.close()
                    
                    user_tables = [t for t in tables if not t.table_name.startswith('MSys')]
                    log_func(f"✅ ملف صالح - {len(user_tables)} جدول")
                    return len(user_tables) > 0
                    
                except:
                    # إذا فشل pyodbc نستخدم الفحص السريع
                    return self.test_access_file(file_path, log_func, quick_test=True)
                    
        except Exception as e:
            log_func(f"❌ خطأ في اختبار الملف: {e}")
            return False
    
    def cleanup_temp_files(self, progress_callback=None):
        """تنظيف شامل للملفات المؤقتة"""
        cleaned = 0
        
        try:
            for file_path in self.converted_files:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        cleaned += 1
                        if progress_callback:
                            progress_callback(f"تم حذف: {os.path.basename(file_path)}")
                except Exception as e:
                    if progress_callback:
                        progress_callback(f"فشل حذف: {os.path.basename(file_path)}")
            
            self.converted_files.clear()
            
        except Exception as e:
            if progress_callback:
                progress_callback(f"خطأ في التنظيف: {e}")
        
        return cleaned

def test_ultimate_solution():
    """اختبار الحل النهائي"""
    print("=== اختبار الحل النهائي لملفات .bok ===")
    
    bok_folder = Path("d:/test3/bok file")
    bok_files = list(bok_folder.glob("*.bok"))
    
    if not bok_files:
        print("❌ لم يتم العثور على ملفات .bok")
        return
    
    solution = UltimateBokSolution()
    
    for i, bok_file in enumerate(bok_files, 1):
        print(f"\n{'='*70}")
        print(f"[{i}/{len(bok_files)}] معالجة: {bok_file.name}")
        print(f"{'='*70}")
        
        def progress_log(message):
            print(f"   {message}")
        
        converted_path, success = solution.convert_bok_to_accdb_ultimate(
            str(bok_file),
            progress_log
        )
        
        if success and converted_path:
            print(f"✅ نجح التحويل: {os.path.basename(converted_path)}")
            
            # اختبار الملف المحول
            file_size = os.path.getsize(converted_path)
            print(f"   📊 حجم الملف: {file_size:,} بايت")
        else:
            print(f"❌ فشل التحويل: {bok_file.name}")
    
    print(f"\n{'='*70}")
    print("انتهى الاختبار")

if __name__ == "__main__":
    test_ultimate_solution()
