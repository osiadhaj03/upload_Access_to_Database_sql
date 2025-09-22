#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
وحدة دعم ملفات .bok للشاملة
تضيف دعم ملفات .bok للسكريپت الحالي
"""

import os
import shutil
import tempfile
import time
from pathlib import Path

class BokFileHandler:
    """معالج ملفات .bok"""
    
    def __init__(self):
        self.temp_files = []  # قائمة الملفات المؤقتة للتنظيف
    
    def is_bok_file(self, file_path):
        """فحص إذا كان الملف .bok"""
        return file_path.lower().endswith('.bok')
    
    def validate_bok_file(self, file_path):
        """التحقق من صحة ملف .bok"""
        try:
            if not os.path.exists(file_path):
                return False, "الملف غير موجود"
            
            # فحص header الملف
            with open(file_path, 'rb') as f:
                header = f.read(32)
                
            # فحص إذا كان Access Database
            if header.startswith(b'\x00\x01\x00\x00Standard Jet DB'):
                return True, "ملف Access Jet Database صحيح"
            elif header.startswith(b'\x00\x01\x00\x00Standard ACE DB'):
                return True, "ملف Access ACE Database صحيح"
            else:
                return False, "ليس ملف Access Database صحيح"
                
        except Exception as e:
            return False, f"خطأ في فحص الملف: {str(e)}"
    
    def convert_bok_to_accdb(self, bok_path, callback=None):
        """تحويل ملف .bok إلى .accdb مؤقت"""
        try:
            if callback:
                callback(f"بدء تحويل ملف .bok: {os.path.basename(bok_path)}")
            
            # التحقق من صحة الملف
            is_valid, message = self.validate_bok_file(bok_path)
            if not is_valid:
                raise Exception(f"ملف .bok غير صحيح: {message}")
            
            if callback:
                callback(f"تم التحقق من صحة الملف: {message}")
            
            # إنشاء ملف مؤقت
            temp_dir = tempfile.gettempdir()
            timestamp = int(time.time())
            temp_name = f"shamela_bok_{timestamp}_{os.getpid()}.accdb"
            temp_path = os.path.join(temp_dir, temp_name)
            
            if callback:
                callback(f"إنشاء ملف مؤقت: {temp_name}")
            
            # نسخ الملف
            shutil.copy2(bok_path, temp_path)
            
            # إضافة للقائمة للتنظيف لاحقاً
            self.temp_files.append(temp_path)
            
            if callback:
                callback(f"تم تحويل ملف .bok بنجاح إلى: {temp_path}")
            
            return temp_path, True
            
        except Exception as e:
            if callback:
                callback(f"خطأ في تحويل ملف .bok: {str(e)}")
            return None, False
    
    def cleanup_temp_files(self, callback=None):
        """تنظيف الملفات المؤقتة"""
        cleaned_count = 0
        
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    cleaned_count += 1
                    if callback:
                        callback(f"تم حذف الملف المؤقت: {os.path.basename(temp_file)}")
            except Exception as e:
                if callback:
                    callback(f"تحذير: لم يتم حذف {os.path.basename(temp_file)}: {str(e)}")
        
        self.temp_files.clear()
        
        if callback and cleaned_count > 0:
            callback(f"تم تنظيف {cleaned_count} ملف مؤقت")
        
        return cleaned_count
    
    def get_file_info(self, file_path):
        """الحصول على معلومات الملف"""
        try:
            info = {
                'name': os.path.basename(file_path),
                'size': os.path.getsize(file_path),
                'size_mb': round(os.path.getsize(file_path) / (1024*1024), 2),
                'is_bok': self.is_bok_file(file_path),
                'is_valid': False,
                'type': 'Unknown'
            }
            
            if info['is_bok']:
                is_valid, message = self.validate_bok_file(file_path)
                info['is_valid'] = is_valid
                info['validation_message'] = message
                
                if is_valid:
                    # تحديد نوع قاعدة البيانات
                    with open(file_path, 'rb') as f:
                        header = f.read(32)
                    
                    if b'Jet DB' in header:
                        info['type'] = 'Access Jet Database'
                    elif b'ACE DB' in header:
                        info['type'] = 'Access ACE Database'
            
            return info
            
        except Exception as e:
            return {
                'name': os.path.basename(file_path),
                'error': str(e),
                'is_bok': self.is_bok_file(file_path),
                'is_valid': False
            }

def update_file_types_for_bok():
    """تحديث أنواع الملفات لدعم .bok"""
    return [
        ("ملفات الشاملة", "*.accdb;*.bok"),
        ("Access Database", "*.accdb"),
        ("ملفات BOK", "*.bok"),
        ("كل الملفات", "*.*")
    ]

def process_file_with_bok_support(file_path, converter_callback, progress_callback=None):
    """معالج الملفات مع دعم .bok"""
    
    bok_handler = BokFileHandler()
    
    try:
        # فحص نوع الملف
        if bok_handler.is_bok_file(file_path):
            if progress_callback:
                progress_callback("اكتشاف ملف .bok - بدء المعالجة الخاصة")
            
            # الحصول على معلومات الملف
            file_info = bok_handler.get_file_info(file_path)
            
            if progress_callback:
                progress_callback(f"معلومات الملف: {file_info['name']} ({file_info['size_mb']} MB)")
            
            if not file_info['is_valid']:
                error_msg = file_info.get('validation_message', 'ملف .bok غير صحيح')
                raise Exception(error_msg)
            
            # تحويل إلى .accdb مؤقت
            temp_path, success = bok_handler.convert_bok_to_accdb(file_path, progress_callback)
            
            if not success:
                raise Exception("فشل في تحويل ملف .bok")
            
            try:
                # معالجة الملف المؤقت
                if progress_callback:
                    progress_callback("بدء معالجة الملف المؤقت...")
                
                result = converter_callback(temp_path)
                
                if progress_callback:
                    progress_callback("تم تحويل ملف .bok بنجاح")
                
                return result
                
            finally:
                # تنظيف الملفات المؤقتة
                if progress_callback:
                    progress_callback("تنظيف الملفات المؤقتة...")
                bok_handler.cleanup_temp_files(progress_callback)
        
        else:
            # ملف عادي (.accdb)
            if progress_callback:
                progress_callback("معالجة ملف .accdb عادي")
            
            return converter_callback(file_path)
    
    except Exception as e:
        # تنظيف في حالة الخطأ
        bok_handler.cleanup_temp_files()
        raise e

# دالة مساعدة للاستخدام في GUI
def get_supported_file_extensions():
    """الحصول على قائمة الامتدادات المدعومة"""
    return ['.accdb', '.bok']

def create_file_filter_string():
    """إنشاء نص فلتر الملفات للـ GUI"""
    return "ملفات الشاملة (*.accdb *.bok);;Access Database (*.accdb);;ملفات BOK (*.bok);;كل الملفات (*.*)"

# مثال للاستخدام في الكود الحالي
def integrate_bok_support_example():
    """مثال على كيفية دمج دعم .bok في الكود الحالي"""
    
    example_code = '''
# في shamela_gui.py - تحديث دالة اختيار الملف

def browse_file(self):
    """اختيار ملف للتحويل مع دعم .bok"""
    from bok_support import create_file_filter_string
    
    file_path = filedialog.askopenfilename(
        title="اختر ملف الشاملة",
        filetypes=create_file_filter_string()
    )
    
    if file_path:
        self.file_path.set(file_path)
        
        # فحص نوع الملف
        if file_path.lower().endswith('.bok'):
            self.log_message("تم اختيار ملف .bok - سيتم التحويل التلقائي")

# في shamela_gui.py - تحديث دالة التحويل

def convert_file(self):
    """تحويل الملف مع دعم .bok"""
    from bok_support import process_file_with_bok_support
    from shamela_converter import convert_file
    
    try:
        # استخدام المعالج الجديد
        result = process_file_with_bok_support(
            file_path=self.file_path.get(),
            converter_callback=lambda path: convert_file(path, self.get_db_config(), self.log_message),
            progress_callback=self.log_message
        )
        
        self.log_message("تم التحويل بنجاح!")
        
    except Exception as e:
        self.log_message(f"خطأ في التحويل: {str(e)}")
    '''
    
    return example_code

if __name__ == "__main__":
    # اختبار الوحدة
    print("=== اختبار وحدة دعم ملفات .bok ===")
    
    # إنشاء معالج
    handler = BokFileHandler()
    
    # اختبار على ملف .bok موجود
    test_file = r"d:\test3\bok file\مقدمة الصلاة للفناري 834.bok"
    
    if os.path.exists(test_file):
        print(f"اختبار ملف: {test_file}")
        
        # فحص معلومات الملف
        info = handler.get_file_info(test_file)
        print(f"معلومات الملف: {info}")
        
        # اختبار التحويل
        temp_path, success = handler.convert_bok_to_accdb(test_file, print)
        
        if success:
            print(f"نجح التحويل إلى: {temp_path}")
            print(f"الملف المؤقت موجود: {os.path.exists(temp_path)}")
            
            # تنظيف
            handler.cleanup_temp_files(print)
        else:
            print("فشل التحويل")
    else:
        print("ملف الاختبار غير موجود")
    
    print("انتهى الاختبار")
