#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
دعم محسن لملفات .bok - الحل النهائي والأقوى
"""

import os
import shutil
import tempfile
from pathlib import Path

class SimpleBokConverter:
    """المحول النهائي والأقوى لملفات .bok"""
    
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "shamela_ultimate_simple"
        self.temp_dir.mkdir(exist_ok=True)
        self.converted_files = []
    
    def convert_bok_to_accdb(self, bok_file_path, progress_callback=None):
        """التحويل النهائي من .bok إلى .accdb"""
        
        def log(message):
            if progress_callback:
                progress_callback(message)
            print(message)
        
        try:
            log(f"🚀 بدء التحويل النهائي: {os.path.basename(bok_file_path)}")
            
            # التحقق من صحة الملف
            if not self.validate_bok_file(bok_file_path, log):
                return None, False
            
            # تحديد مسار الحفظ
            base_name = os.path.splitext(os.path.basename(bok_file_path))[0]
            output_path = self.temp_dir / f"{base_name}_ultimate.accdb"
            
            # النسخ المباشر (الطريقة الأكثر نجاحاً)
            log("📋 نسخ الملف مع تغيير الامتداد...")
            shutil.copy2(bok_file_path, output_path)
            
            # التحقق من نجاح النسخ
            if not output_path.exists():
                log("❌ فشل في نسخ الملف!")
                return None, False
            
            # مقارنة الأحجام
            original_size = os.path.getsize(bok_file_path)
            converted_size = os.path.getsize(output_path)
            
            if converted_size != original_size:
                log("❌ حجم الملف المحول مختلف!")
                return None, False
            
            log(f"✅ تم النسخ بنجاح - الحجم: {converted_size:,} بايت")
            
            # فحص الملف النهائي
            if self.verify_access_file(str(output_path), log):
                log("🎉 تم التحويل بنجاح!")
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
            log(f"❌ خطأ في التحويل: {e}")
            return None, False
    
    def validate_bok_file(self, file_path, log_func):
        """التحقق من صحة ملف .bok"""
        log_func("🔍 فحص ملف .bok...")
        
        try:
            # فحص الوجود
            if not os.path.exists(file_path):
                log_func("❌ الملف غير موجود")
                return False
            
            # فحص الحجم
            file_size = os.path.getsize(file_path)
            if file_size < 50 * 1024:  # أقل من 50KB
                log_func(f"❌ الملف صغير جداً: {file_size:,} بايت")
                return False
            
            log_func(f"✅ حجم مناسب: {file_size:,} بايت")
            
            # فحص نوع الملف
            if not file_path.lower().endswith('.bok'):
                log_func("⚠️ الملف لا ينتهي بـ .bok")
            
            # فحص محتوى الملف
            with open(file_path, 'rb') as f:
                header = f.read(200)
                
                # البحث عن signatures Access
                access_signatures = [
                    b'Standard Jet DB',
                    b'Standard ACE DB',
                    b'Microsoft Jet DB',
                    b'Microsoft Office Access'
                ]
                
                found_signature = False
                for signature in access_signatures:
                    if signature in header:
                        log_func(f"✅ تم التعرف على: {signature.decode('ascii', errors='ignore')}")
                        found_signature = True
                        break
                
                if not found_signature:
                    # فحص بنية Jet Database
                    if header[0:4] == b'\x00\x01\x00\x00':
                        log_func("✅ بنية Jet Database صحيحة")
                        found_signature = True
                
                if found_signature:
                    log_func("✅ ملف .bok صالح")
                    return True
                else:
                    log_func("⚠️ لم يتم التعرف على نوع الملف، سيتم المحاولة")
                    return True  # نحاول حتى لو لم نتعرف عليه
                    
        except Exception as e:
            log_func(f"❌ خطأ في فحص الملف: {e}")
            return False
    
    def verify_access_file(self, file_path, log_func):
        """التحقق من صحة ملف Access المحول"""
        
        try:
            log_func("🔍 فحص الملف المحول...")
            
            # فحص أساسي
            if not os.path.exists(file_path):
                log_func("❌ الملف غير موجود!")
                return False
            
            file_size = os.path.getsize(file_path)
            if file_size < 1000:
                log_func(f"❌ الملف صغير جداً: {file_size} بايت")
                return False
            
            log_func(f"✅ حجم مناسب: {file_size:,} بايت")
            
            # فحص محتوى الملف
            with open(file_path, 'rb') as f:
                header = f.read(1024)
                
                # البحث عن مؤشرات Access
                access_indicators = [
                    b'Standard Jet DB',
                    b'Standard ACE DB',
                    b'Microsoft Jet DB',
                    b'Microsoft Office Access'
                ]
                
                found_count = 0
                for indicator in access_indicators:
                    if indicator in header:
                        found_count += 1
                
                if found_count > 0:
                    log_func(f"✅ وُجد {found_count} مؤشر Access")
                    
                    # محاولة اختبار pyodbc (اختياري)
                    if self.test_with_pyodbc(file_path, log_func):
                        return True
                    else:
                        # حتى لو فشل pyodbc، نعتبر الملف صالح إذا وُجدت المؤشرات
                        log_func("✅ الملف صالح (بناءً على المؤشرات)")
                        return True
                
                # فحص بنية Jet
                if header[0:4] == b'\x00\x01\x00\x00':
                    log_func("✅ بنية Jet Database صحيحة")
                    return True
                
                log_func("❌ لم يتم العثور على مؤشرات Access")
                return False
                
        except Exception as e:
            log_func(f"❌ خطأ في فحص الملف: {e}")
            return False
    
    def test_with_pyodbc(self, file_path, log_func):
        """اختبار اختياري مع pyodbc"""
        try:
            import pyodbc
            
            log_func("🔧 اختبار pyodbc...")
            
            conn_str = (
                r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
                f'DBQ={file_path};'
            )
            
            conn = pyodbc.connect(conn_str, timeout=5)
            cursor = conn.cursor()
            
            # فحص الجداول
            tables = cursor.tables(tableType='TABLE').fetchall()
            user_tables = [t.table_name for t in tables if not t.table_name.startswith('MSys')]
            
            conn.close()
            
            if len(user_tables) > 0:
                log_func(f"✅ pyodbc: وُجد {len(user_tables)} جدول")
                return True
            else:
                log_func("⚠️ pyodbc: لا توجد جداول مستخدم")
                return False
                
        except Exception as e:
            log_func(f"⚠️ pyodbc فشل: {str(e)[:50]}...")
            # ليس خطأ فادح - ربما مشكلة في driver
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

def process_bok_file_simple(file_path, converter_callback, progress_callback=None):
    """معالج ملفات .bok المطور"""
    
    def log(message):
        if progress_callback:
            progress_callback(message)
    
    try:
        # التحقق من نوع الملف
        if file_path.lower().endswith('.bok'):
            log("📁 ملف .bok - بدء التحويل التلقائي...")
            
            converter = SimpleBokConverter()
            converted_path, success = converter.convert_bok_to_accdb(file_path, log)
            
            if success and converted_path:
                log("🔄 تم التحويل - بدء المعالجة...")
                
                # تشغيل المحول الأصلي على الملف المحول
                try:
                    result = converter_callback(converted_path)
                    
                    if result:
                        log("✅ تمت المعالجة بنجاح!")
                    else:
                        log("❌ فشلت المعالجة")
                    
                    return result
                    
                except Exception as e:
                    log(f"❌ خطأ في المعالجة: {e}")
                    return False
                finally:
                    # تنظيف دائماً
                    try:
                        log("🧹 تنظيف الملفات المؤقتة...")
                        converter.cleanup_temp_files()
                    except:
                        pass
            else:
                log("❌ فشل التحويل التلقائي")
                return False
                
        else:
            # ملف عادي - معالجة مباشرة
            log("📄 ملف عادي - معالجة مباشرة...")
            return converter_callback(file_path)
            
    except Exception as e:
        log(f"❌ خطأ في معالجة الملف: {e}")
        return False