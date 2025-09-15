#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
محول ملفات .bok مباشر لـ MySQL
يقرأ .bok بنفس طريقة ultimate_bok_converter لكن ينقل لـ MySQL مباشرة
"""

import os
import struct
import mysql.connector
from datetime import datetime

class DirectBokToMySQLConverter:
    def __init__(self, db_config, callback=None):
        self.db_config = db_config
        self.callback = callback or print
        self.mysql_conn = None
    
    def log(self, message, level="INFO"):
        """رسائل السجل"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_msg = f"[{timestamp}] {level}: {message}"
        self.callback(log_msg, level)
        print(log_msg)
    
    def connect_mysql(self):
        """الاتصال بـ MySQL"""
        try:
            self.mysql_conn = mysql.connector.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                database=self.db_config['database'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci'
            )
            self.log("تم الاتصال بقاعدة بيانات MySQL بنجاح")
            return True
        except Exception as e:
            self.log(f"خطأ في الاتصال بـ MySQL: {e}", "ERROR")
            return False
    
    def read_bok_header(self, file_path):
        """قراءة header ملف .bok"""
        try:
            with open(file_path, 'rb') as f:
                signature = f.read(16)
                if not signature.startswith(b'\x00\x01\x00\x00Standard Jet DB'):
                    return None
                
                f.seek(20)
                version = struct.unpack('<I', f.read(4))[0]
                
                return {
                    'format': 'Jet Database',
                    'version': version,
                    'valid': True
                }
        except Exception as e:
            self.log(f"خطأ في قراءة header: {e}", "ERROR")
            return None
    
    def find_tables_in_bok(self, file_path):
        """البحث عن الجداول في ملف .bok"""
        try:
            self.log(f"البحث عن الجداول في: {os.path.basename(file_path)}")
            
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # البحث عن أنماط أسماء الجداول
            table_patterns = []
            
            # البحث عن جداول b + رقم (المحتوى)
            for i in range(10000, 99999):  # نطاق أرقام الكتب المحتملة
                pattern = f'b{i}'.encode('ascii')
                if pattern in content:
                    table_patterns.append(f'b{i}')
            
            # البحث عن جداول t + رقم (الفهرس)
            for i in range(10000, 99999):
                pattern = f't{i}'.encode('ascii')
                if pattern in content:
                    table_patterns.append(f't{i}')
            
            self.log(f"تم العثور على {len(table_patterns)} جدول محتمل")
            return table_patterns
            
        except Exception as e:
            self.log(f"خطأ في البحث عن الجداول: {e}", "ERROR")
            return []
    
    def extract_data_from_bok(self, file_path):
        """استخراج البيانات من ملف .bok بطريقة متقدمة"""
        try:
            self.log(f"استخراج البيانات من: {os.path.basename(file_path)}")
            
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # استخراج البيانات العربية
            extracted_data = {
                'content_entries': [],
                'index_entries': [],
                'book_info': None
            }
            
            # البحث عن النصوص العربية
            text_parts = []
            
            # تجريب encoding مختلفة
            for encoding in ['utf-16le', 'utf-16be', 'cp1256', 'utf-8']:
                try:
                    decoded = content.decode(encoding, errors='ignore')
                    
                    # البحث عن أنماط عربية
                    import re
                    arabic_pattern = r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+'
                    matches = re.findall(arabic_pattern, decoded)
                    
                    if matches:
                        text_parts.extend(matches)
                        
                except:
                    continue
            
            # تنظيف وتصفية النصوص
            clean_texts = []
            for text in text_parts:
                text = text.strip()
                if len(text) > 5 and len(text) < 10000:  # نصوص معقولة الطول
                    clean_texts.append(text)
            
            # تحليل النصوص لاستخراج المحتوى والفهرس
            content_id = 1
            for i, text in enumerate(clean_texts[:5000]):  # أول 5000 نص
                # تحديد إذا كان فهرس أم محتوى
                is_index = any(keyword in text for keyword in ['باب', 'فصل', 'كتاب', 'مقدمة'])
                
                if is_index:
                    extracted_data['index_entries'].append({
                        'id': len(extracted_data['index_entries']) + 1,
                        'title': text[:500],  # أول 500 حرف
                        'level': 1,
                        'page_start': i + 1,
                        'page_end': i + 1
                    })
                else:
                    extracted_data['content_entries'].append({
                        'id': content_id,
                        'page': i + 1,
                        'content': text,
                        'part': 1
                    })
                    content_id += 1
            
            # استخراج عنوان الكتاب
            if clean_texts:
                extracted_data['book_info'] = {
                    'title': clean_texts[0][:200] if clean_texts[0] else 'كتاب غير معروف',
                    'author': 'غير معروف',
                    'book_id': self.extract_book_id_from_path(file_path)
                }
            
            self.log(f"تم استخراج {len(extracted_data['content_entries'])} محتوى و {len(extracted_data['index_entries'])} فهرس")
            return extracted_data
            
        except Exception as e:
            self.log(f"خطأ في استخراج البيانات: {e}", "ERROR")
            return None
    
    def extract_book_id_from_path(self, file_path):
        """استخراج معرف الكتاب من اسم الملف"""
        filename = os.path.basename(file_path)
        import re
        
        # البحث عن أرقام في اسم الملف
        numbers = re.findall(r'\d+', filename)
        if numbers:
            return int(numbers[-1])  # آخر رقم في الاسم
        
        # إذا لم يوجد رقم، استخدم hash اسم الملف
        return abs(hash(filename)) % 100000
    
    def insert_book_data(self, book_data):
        """إدراج بيانات الكتاب في MySQL"""
        try:
            cursor = self.mysql_conn.cursor()
            
            # إدراج الكتاب
            book_info = book_data['book_info']
            insert_book_query = """
            INSERT INTO books (title, author, book_id, hijri_year, publisher, pages_count, parts_count, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            book_values = (
                book_info['title'],
                book_info['author'],
                book_info['book_id'],
                None,  # hijri_year
                'مكتبة الشاملة',  # publisher
                len(book_data['content_entries']),  # pages_count
                1,  # parts_count
                datetime.now()
            )
            
            cursor.execute(insert_book_query, book_values)
            book_db_id = cursor.lastrowid
            
            self.log(f"تم إدراج الكتاب: {book_info['title']} (ID: {book_db_id})")
            
            # إنشاء مجلد افتراضي
            folder_query = """
            INSERT INTO folders (name, parent_id, book_count, created_at)
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(folder_query, ('مجلد افتراضي', None, 1, datetime.now()))
            folder_id = cursor.lastrowid
            
            # ربط الكتاب بالمجلد
            book_folder_query = """
            INSERT INTO book_folders (book_id, folder_id)
            VALUES (%s, %s)
            """
            cursor.execute(book_folder_query, (book_db_id, folder_id))
            
            # إدراج الفصول
            chapter_count = 0
            for index_entry in book_data['index_entries']:
                chapter_query = """
                INSERT INTO chapters (book_id, title, level, page_start, page_end, part)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                
                chapter_values = (
                    book_db_id,
                    index_entry['title'],
                    index_entry['level'],
                    index_entry['page_start'],
                    index_entry['page_end'],
                    1  # part
                )
                
                cursor.execute(chapter_query, chapter_values)
                chapter_count += 1
            
            self.log(f"تم إدراج {chapter_count} فصل")
            
            # إدراج الصفحات
            page_count = 0
            for content_entry in book_data['content_entries']:
                page_query = """
                INSERT INTO pages (book_id, page_number, content, part)
                VALUES (%s, %s, %s, %s)
                """
                
                page_values = (
                    book_db_id,
                    content_entry['page'],
                    content_entry['content'],
                    content_entry['part']
                )
                
                try:
                    cursor.execute(page_query, page_values)
                    page_count += 1
                except mysql.connector.IntegrityError:
                    # تجاهل الصفحات المكررة
                    continue
            
            self.log(f"تم إدراج {page_count} صفحة")
            
            # حفظ التغييرات
            self.mysql_conn.commit()
            
            self.log(f"تم حفظ جميع بيانات الكتاب بنجاح")
            return True
            
        except Exception as e:
            self.log(f"خطأ في إدراج البيانات: {e}", "ERROR")
            if self.mysql_conn:
                self.mysql_conn.rollback()
            return False
    
    def convert_bok_file(self, file_path):
        """تحويل ملف .bok إلى MySQL"""
        try:
            self.log(f"بدء تحويل ملف: {os.path.basename(file_path)}")
            
            # فحص header الملف
            header_info = self.read_bok_header(file_path)
            if not header_info or not header_info['valid']:
                self.log("ملف .bok غير صحيح", "ERROR")
                return False
            
            self.log(f"ملف .bok صحيح: {header_info['format']}")
            
            # استخراج البيانات
            book_data = self.extract_data_from_bok(file_path)
            if not book_data:
                self.log("فشل في استخراج البيانات", "ERROR")
                return False
            
            # إدراج في MySQL
            success = self.insert_book_data(book_data)
            
            if success:
                self.log(f"تم تحويل {os.path.basename(file_path)} بنجاح")
                return True
            else:
                self.log(f"فشل تحويل {os.path.basename(file_path)}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"خطأ عام في التحويل: {e}", "ERROR")
            return False

def test_direct_converter():
    """اختبار المحول المباشر"""
    
    # إعدادات قاعدة البيانات
    db_config = {
        'host': 'srv1800.hstgr.io',
        'port': 3306,
        'database': 'u994369532_test',
        'user': 'u994369532_shamela',
        'password': 'mT8$pR3@vK9#'
    }
    
    # إنشاء المحول
    converter = DirectBokToMySQLConverter(db_config)
    
    # الاتصال بـ MySQL
    if not converter.connect_mysql():
        print("فشل الاتصال بـ MySQL")
        return
    
    # اختبار على ملف واحد
    test_file = r"d:\test3\bok file\مقدمة الصلاة للفناري 834.bok"
    
    if os.path.exists(test_file):
        print(f"اختبار التحويل المباشر على: {os.path.basename(test_file)}")
        result = converter.convert_bok_file(test_file)
        
        if result:
            print("✅ نجح الاختبار!")
        else:
            print("❌ فشل الاختبار")
    else:
        print("ملف الاختبار غير موجود")
    
    # إغلاق الاتصال
    if converter.mysql_conn:
        converter.mysql_conn.close()

if __name__ == "__main__":
    test_direct_converter()
