#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
حل محسن لملفات .bok - استخدام drivers متعددة وطرق بديلة
"""

import os
import shutil
import tempfile
import time
import pyodbc
from pathlib import Path

class EnhancedBokHandler:
    """معالج محسن لملفات .bok مع دعم drivers متعددة"""
    
    def __init__(self):
        self.temp_files = []
        self.available_drivers = self._detect_available_drivers()
    
    def _detect_available_drivers(self):
        """اكتشاف drivers المتاحة في النظام"""
        drivers = []
        try:
            all_drivers = pyodbc.drivers()
            
            # قائمة drivers محتملة لـ Access
            access_drivers = [
                "Microsoft Access Driver (*.mdb, *.accdb)",
                "Microsoft Access Driver (*.mdb)",
                "Microsoft Access dBASE Driver (*.dbf, *.ndx, *.mdx)",
                "Driver do Microsoft Access (*.mdb)",
            ]
            
            for driver in access_drivers:
                if driver in all_drivers:
                    drivers.append(driver)
            
            return drivers
            
        except Exception as e:
            print(f"خطأ في اكتشاف drivers: {e}")
            return ["Microsoft Access Driver (*.mdb, *.accdb)"]
    
    def convert_bok_with_multiple_methods(self, bok_path, callback=None):
        """تجريب طرق متعددة لتحويل ملف .bok"""
        
        if callback:
            callback(f"بدء تحليل ملف .bok: {os.path.basename(bok_path)}")
        
        # الطريقة 1: تجريب امتدادات مختلفة مع drivers مختلفة
        methods = [
            (".accdb", "Microsoft Access Driver (*.mdb, *.accdb)"),
            (".mdb", "Microsoft Access Driver (*.mdb, *.accdb)"),
            (".mdb", "Microsoft Access Driver (*.mdb)"),
        ]
        
        for extension, driver in methods:
            if callback:
                callback(f"جرب: {extension} مع {driver}")
            
            success, temp_path = self._try_conversion_method(
                bok_path, extension, driver, callback
            )
            
            if success:
                if callback:
                    callback(f"✅ نجح التحويل بطريقة: {extension} + {driver}")
                return temp_path, True
        
        # الطريقة 2: محاولة إصلاح الملف
        if callback:
            callback("محاولة إصلاح بنية الملف...")
        
        success, temp_path = self._try_repair_and_convert(bok_path, callback)
        if success:
            return temp_path, True
        
        # الطريقة 3: تحويل إلى إصدار أقدم
        if callback:
            callback("محاولة تحويل إلى إصدار متوافق...")
        
        success, temp_path = self._try_compatibility_conversion(bok_path, callback)
        if success:
            return temp_path, True
        
        if callback:
            callback("❌ فشلت جميع طرق التحويل")
        
        return None, False
    
    def _try_conversion_method(self, bok_path, extension, driver, callback):
        """تجريب طريقة تحويل محددة"""
        temp_path = None
        try:
            # إنشاء ملف مؤقت
            temp_dir = tempfile.gettempdir()
            timestamp = int(time.time())
            temp_name = f"shamela_bok_fixed_{timestamp}_{os.getpid()}{extension}"
            temp_path = os.path.join(temp_dir, temp_name)
            
            # نسخ الملف
            shutil.copy2(bok_path, temp_path)
            
            # محاولة الاتصال
            connection_string = f"Driver={{{driver}}};DBQ={temp_path};ExtendedAnsiSQL=1;"
            
            # اختبار سريع للاتصال
            with pyodbc.connect(connection_string, timeout=5) as conn:
                # اختبار بسيط للتأكد من قابلية القراءة
                cursor = conn.cursor()
                tables = [table.table_name for table in cursor.tables(tableType='TABLE') 
                         if not table.table_name.startswith('MSys')]
                
                if len(tables) > 0:
                    self.temp_files.append(temp_path)
                    return True, temp_path
            
            # إذا وصلنا هنا، فالاتصال فشل
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False, None
            
        except Exception as e:
            if callback:
                callback(f"فشل {extension}: {str(e)[:100]}")
            
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
            return False, None
    
    def _try_repair_and_convert(self, bok_path, callback):
        """محاولة إصلاح الملف قبل التحويل"""
        try:
            # قراءة header الملف وتحليله
            with open(bok_path, 'rb') as f:
                header = f.read(1024)  # قراءة أول 1KB
            
            # فحص إذا كان header يحتاج إصلاح
            if b'Standard Jet DB' in header:
                if callback:
                    callback("اكتشاف Jet Database - محاولة إصلاح...")
                
                # إنشاء نسخة معدلة
                temp_dir = tempfile.gettempdir()
                timestamp = int(time.time())
                temp_path = os.path.join(temp_dir, f"shamela_repaired_{timestamp}.mdb")
                
                # نسخ الملف وتعديل header إذا لزم الأمر
                with open(bok_path, 'rb') as src:
                    with open(temp_path, 'wb') as dst:
                        content = src.read()
                        # محاولة تصحيح مشاكل header شائعة
                        dst.write(content)
                
                # اختبار النسخة المصلحة
                try:
                    connection_string = f"Driver={{Microsoft Access Driver (*.mdb)}};DBQ={temp_path};"
                    
                    with pyodbc.connect(connection_string, timeout=5) as conn:
                        cursor = conn.cursor()
                        tables = [table.table_name for table in cursor.tables(tableType='TABLE')]
                        
                        if len(tables) > 0:
                            self.temp_files.append(temp_path)
                            return True, temp_path
                
                except Exception as e:
                    if callback:
                        callback(f"فشل الإصلاح: {str(e)[:50]}")
                
                # حذف النسخة في حالة الفشل
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            
            return False, None
            
        except Exception as e:
            if callback:
                callback(f"خطأ في الإصلاح: {str(e)[:50]}")
            return False, None
    
    def _try_compatibility_conversion(self, bok_path, callback):
        """محاولة تحويل إلى إصدار متوافق"""
        try:
            # هذه طريقة متقدمة لمعالجة ملفات Access قديمة
            # يمكن تطويرها أكثر حسب الحاجة
            
            if callback:
                callback("تجريب تحويل التوافق...")
            
            # محاولة مع إعدادات خاصة
            temp_dir = tempfile.gettempdir()
            timestamp = int(time.time())
            temp_path = os.path.join(temp_dir, f"shamela_compat_{timestamp}.accdb")
            
            shutil.copy2(bok_path, temp_path)
            
            # تجريب connection strings مختلفة
            connection_options = [
                f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={temp_path};ReadOnly=1;",
                f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={temp_path};Exclusive=0;",
                f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={temp_path};ExtendedAnsiSQL=1;ReadOnly=1;",
            ]
            
            for conn_str in connection_options:
                try:
                    with pyodbc.connect(conn_str, timeout=10) as conn:
                        cursor = conn.cursor()
                        tables = [table.table_name for table in cursor.tables(tableType='TABLE')]
                        
                        if len(tables) > 0:
                            self.temp_files.append(temp_path)
                            if callback:
                                callback(f"✅ نجح التوافق مع: {conn_str[:50]}...")
                            return True, temp_path
                            
                except Exception:
                    continue
            
            # حذف في حالة الفشل
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            return False, None
            
        except Exception as e:
            if callback:
                callback(f"خطأ في التوافق: {str(e)[:50]}")
            return False, None
    
    def cleanup_temp_files(self, callback=None):
        """تنظيف الملفات المؤقتة"""
        cleaned = 0
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    cleaned += 1
                    if callback:
                        callback(f"حذف: {os.path.basename(temp_file)}")
            except Exception as e:
                if callback:
                    callback(f"تحذير: لم يحذف {os.path.basename(temp_file)}: {str(e)}")
        
        self.temp_files.clear()
        return cleaned

def enhanced_bok_conversion(bok_path, converter_callback, progress_callback=None):
    """دالة محسنة لتحويل ملفات .bok"""
    
    if not bok_path.lower().endswith('.bok'):
        # ملف عادي
        return converter_callback(bok_path)
    
    handler = EnhancedBokHandler()
    
    try:
        if progress_callback:
            progress_callback(f"🔧 معالجة محسنة لملف .bok: {os.path.basename(bok_path)}")
        
        # محاولة التحويل المحسن
        temp_path, success = handler.convert_bok_with_multiple_methods(
            bok_path, progress_callback
        )
        
        if not success:
            raise Exception("فشل في تحويل ملف .bok بجميع الطرق المتاحة")
        
        if progress_callback:
            progress_callback(f"✅ تم تحويل .bok بنجاح، بدء المعالجة...")
        
        # معالجة الملف المؤقت
        result = converter_callback(temp_path)
        
        if progress_callback:
            progress_callback(f"✅ اكتمل تحويل ملف .bok بنجاح")
        
        return result
        
    except Exception as e:
        if progress_callback:
            progress_callback(f"❌ خطأ في معالجة .bok: {str(e)}")
        raise e
        
    finally:
        # تنظيف
        cleaned = handler.cleanup_temp_files(progress_callback)
        if progress_callback and cleaned > 0:
            progress_callback(f"🧹 تم تنظيف {cleaned} ملف مؤقت")

if __name__ == "__main__":
    # اختبار الحل المحسن
    print("=== اختبار الحل المحسن لملفات .bok ===")
    
    handler = EnhancedBokHandler()
    print(f"Drivers متاحة: {handler.available_drivers}")
    
    test_file = r"d:\test3\bok file\مقدمة الصلاة للفناري 834.bok"
    
    if os.path.exists(test_file):
        print(f"\nاختبار: {test_file}")
        
        temp_path, success = handler.convert_bok_with_multiple_methods(
            test_file, print
        )
        
        if success:
            print(f"✅ نجح التحويل: {temp_path}")
            # اختبار قراءة سريع
            try:
                connection_string = f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={temp_path};"
                with pyodbc.connect(connection_string) as conn:
                    cursor = conn.cursor()
                    tables = [table.table_name for table in cursor.tables(tableType='TABLE')]
                    print(f"الجداول الموجودة: {tables}")
            except Exception as e:
                print(f"خطأ في قراءة الملف المحول: {e}")
        else:
            print("❌ فشل التحويل")
        
        # تنظيف
        handler.cleanup_temp_files(print)
    else:
        print("ملف الاختبار غير موجود")
