#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
حل بسيط ومباشر لتحويل .bok إلى .accdb
بدون الحاجة لـ Access المثبت - نسخ ذكي
"""

import os
import shutil
import tempfile
from pathlib import Path

class DirectBokConverter:
    """محول مباشر لملفات .bok - الحل الأبسط والأقوى"""
    
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "shamela_direct_convert"
        self.temp_dir.mkdir(exist_ok=True)
        self.converted_files = []
    
    def convert_bok_to_accdb(self, bok_file_path, progress_callback=None):
        """تحويل مباشر من .bok إلى .accdb"""
        
        def log(message):
            if progress_callback:
                progress_callback(message)
            print(message)
        
        try:
            log(f"بدء التحويل المباشر: {os.path.basename(bok_file_path)}")
            
            # التحقق من وجود الملف
            if not os.path.exists(bok_file_path):
                log("الملف غير موجود!")
                return None, False
            
            # فحص أن الملف .bok صالح
            if not self.is_valid_bok_file(bok_file_path):
                log("الملف ليس ملف .bok صالح!")
                return None, False
            
            # تحديد مسار الحفظ
            base_name = os.path.splitext(os.path.basename(bok_file_path))[0]
            output_path = self.temp_dir / f"{base_name}_direct_converted.accdb"
            
            log("نسخ الملف وتغيير الامتداد...")
            
            # النسخ المباشر مع تغيير الامتداد
            shutil.copy2(bok_file_path, output_path)
            
            # التحقق من نجاح النسخ
            if not output_path.exists():
                log("فشل في نسخ الملف!")
                return None, False
            
            # فحص حجم الملف
            original_size = os.path.getsize(bok_file_path)
            converted_size = os.path.getsize(output_path)
            
            if converted_size != original_size:
                log("حجم الملف المحول مختلف!")
                return None, False
            
            log(f"تم النسخ بنجاح - الحجم: {converted_size:,} بايت")
            
            # محاولة التحقق من الملف
            if self.verify_converted_file(str(output_path), log):
                log("✅ تم التحويل بنجاح!")
                self.converted_files.append(str(output_path))
                return str(output_path), True
            else:
                log("❌ الملف المحول غير صالح")
                try:
                    output_path.unlink()
                except:
                    pass
                return None, False
                
        except Exception as e:
            log(f"خطأ في التحويل: {e}")
            return None, False
    
    def is_valid_bok_file(self, file_path):
        """فحص صحة ملف .bok"""
        try:
            # فحص الامتداد
            if not file_path.lower().endswith('.bok'):
                return False
            
            # فحص الحجم (يجب أن يكون أكبر من 100KB)
            file_size = os.path.getsize(file_path)
            if file_size < 100 * 1024:
                return False
            
            # فحص header الملف
            with open(file_path, 'rb') as f:
                header = f.read(100)
                
                # البحث عن signatures مختلفة لـ Access
                access_signatures = [
                    b'Standard Jet DB',
                    b'Standard ACE DB', 
                    b'\x00\x01\x00\x00',
                    b'Microsoft Jet DB',
                    b'Microsoft Office Access'
                ]
                
                for signature in access_signatures:
                    if signature in header:
                        return True
                
                # إذا لم نجد signature واضح، نتحقق من البنية العامة
                # ملفات Access تبدأ عادة ببايتات معينة
                if header[0:4] == b'\x00\x01\x00\x00':
                    return True
                    
            return False
            
        except Exception as e:
            print(f"خطأ في فحص الملف: {e}")
            return False
    
    def verify_converted_file(self, file_path, log_func=None):
        """التحقق من صحة الملف المحول"""
        
        def log(message):
            if log_func:
                log_func(message)
        
        try:
            log("فحص الملف المحول...")
            
            # فحص وجود الملف
            if not os.path.exists(file_path):
                log("الملف غير موجود!")
                return False
            
            # فحص الحجم
            file_size = os.path.getsize(file_path)
            if file_size < 1000:
                log(f"الملف صغير جداً: {file_size} بايت")
                return False
            
            log(f"حجم الملف مناسب: {file_size:,} بايت")
            
            # محاولة فتح مع pyodbc
            try:
                import pyodbc
                
                log("اختبار الاتصال بـ pyodbc...")
                
                conn_str = (
                    r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
                    f'DBQ={file_path};'
                )
                
                conn = pyodbc.connect(conn_str, timeout=10)
                cursor = conn.cursor()
                
                # فحص الجداول
                log("فحص الجداول...")
                tables = cursor.tables(tableType='TABLE').fetchall()
                
                # تصفية الجداول (تجاهل جداول النظام)
                user_tables = []
                for table in tables:
                    table_name = table.table_name
                    if not table_name.startswith('MSys') and not table_name.startswith('~'):
                        user_tables.append(table_name)
                
                conn.close()
                
                if len(user_tables) > 0:
                    log(f"✅ تم العثور على {len(user_tables)} جدول: {', '.join(user_tables[:3])}")
                    return True
                else:
                    log("⚠️ لا توجد جداول بيانات")
                    return False
                    
            except Exception as pyodbc_error:
                log(f"فشل اختبار pyodbc: {pyodbc_error}")
                
                # فحص بديل - فحص بنية الملف
                log("تجريب فحص بديل...")
                return self.alternative_file_check(file_path, log)
                
        except Exception as e:
            log(f"خطأ في التحقق: {e}")
            return False
    
    def alternative_file_check(self, file_path, log_func=None):
        """فحص بديل لبنية الملف"""
        
        def log(message):
            if log_func:
                log_func(message)
        
        try:
            with open(file_path, 'rb') as f:
                # قراءة بداية الملف
                header = f.read(1024)
                
                # البحث عن مؤشرات Access Database
                indicators = [
                    b'Standard Jet DB',
                    b'Standard ACE DB',
                    b'Microsoft Jet DB',
                    b'Microsoft Office Access'
                ]
                
                found_indicators = 0
                for indicator in indicators:
                    if indicator in header:
                        found_indicators += 1
                        log(f"✓ وُجد: {indicator.decode('ascii', errors='ignore')}")
                
                if found_indicators > 0:
                    log(f"✅ الملف يحتوي على مؤشرات Access صحيحة")
                    return True
                
                # فحص إضافي للبنية
                if header[0:4] == b'\x00\x01\x00\x00':
                    log("✅ بنية Jet Database صحيحة")
                    return True
                
                log("❌ لم يتم العثور على مؤشرات Access")
                return False
                
        except Exception as e:
            log(f"خطأ في الفحص البديل: {e}")
            return False
    
    def cleanup_temp_files(self, progress_callback=None):
        """تنظيف الملفات المؤقتة"""
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

def test_direct_converter():
    """اختبار المحول المباشر"""
    print("=== اختبار المحول المباشر ===")
    
    bok_folder = Path("d:/test3/bok file")
    converter = DirectBokConverter()
    
    bok_files = list(bok_folder.glob("*.bok"))
    
    if not bok_files:
        print("❌ لم يتم العثور على ملفات .bok")
        return
    
    print(f"🔍 العثور على {len(bok_files)} ملف .bok")
    
    for bok_file in bok_files:
        print(f"\n{'='*60}")
        print(f"اختبار: {bok_file.name}")
        print(f"{'='*60}")
        
        output_path, success = converter.convert_bok_to_accdb(str(bok_file))
        
        if success:
            print(f"✅ نجح: {bok_file.name}")
            print(f"   الملف المحول: {output_path}")
        else:
            print(f"❌ فشل: {bok_file.name}")

if __name__ == "__main__":
    test_direct_converter()
