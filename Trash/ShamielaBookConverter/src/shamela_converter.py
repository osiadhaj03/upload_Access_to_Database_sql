#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ================================
# تعليمات التشغيل:
# 1. تأكد من تثبيت الحزم المطلوبة عبر:
#    pip install pyodbc mysql-connector-python
# 2. يجب أن يكون لديك Microsoft Access ODBC Driver (عادة موجود في ويندوز أو نزله من موقع مايكروسوفت)
# 3. شغل السكريبت عبر:
#    python shamela_converter.py
# ================================

# فحص الحزم المطلوبة وإظهار رسالة واضحة إذا كانت غير مثبتة
try:
    import pyodbc
except ImportError:
    print("[خطأ] مكتبة pyodbc غير مثبتة. ثبّتها بالأمر: pip install pyodbc")
    exit(1)
try:
    import mysql.connector
except ImportError:
    print("[خطأ] مكتبة mysql-connector-python غير مثبتة. ثبّتها بالأمر: pip install mysql-connector-python")
    exit(1)

"""
سكريبت تحويل كتب الشاملة من Access إلى MySQL
يقوم بقراءة ملفات .accdb وتحويلها إلى قاعدة بيانات MySQL

النظام الجديد للصفحات:
- page_number: رقم الصفحة الأصلي من ملف Access (يمكن تكراره)
- internal_index: ترقيم تسلسلي فريد للصفحات (1, 2, 3, ...) لكامل الكتاب
- استخدام internal_index في ربط الصفحات مع الفصول والعمليات الداخلية
- الحفاظ على page_number للمرجعية والعرض

المطور: مساعد الذكي الاصطناعي
التاريخ: 2025 - محدث لدعم internal_index
"""
import os
import re
import sys
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class ShamelaConverter:
    def __init__(self, mysql_config: dict, message_callback=None):
        """
        إنشاء محول جديد
        mysql_config: قاموس يحتوي على إعدادات اتصال MySQL
        message_callback: دالة لإرسال الرسائل إلى الواجهة
        """
        self.mysql_config = mysql_config
        self.mysql_conn = None
        self.access_conn = None
        self.conversion_log = []
        self.message_callback = message_callback
        
    def log_message(self, message: str, level: str = "INFO"):
        """تسجيل رسالة في السجل"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        self.conversion_log.append(log_entry)
        print(log_entry)
        
        # إرسال الرسالة للواجهة إذا كان هناك callback
        if self.message_callback:
            self.message_callback(message, level)
    
    def connect_mysql(self) -> bool:
        """الاتصال بقاعدة بيانات MySQL"""
        try:
            # إعداد معاملات الاتصال
            connection_params = self.mysql_config.copy()
            
            # إزالة كلمة المرور إذا كانت فارغة
            if not connection_params.get('password'):
                connection_params.pop('password', None)
            
            # إضافة إعدادات إضافية لحل مشكلة authentication plugin
            connection_params.update({
                'auth_plugin': 'mysql_native_password',
                'autocommit': True,
                'sql_mode': 'TRADITIONAL',
                'connect_timeout': 30,
                'use_pure': True  # استخدام Python pure implementation
            })
            
            self.mysql_conn = mysql.connector.connect(**connection_params)
            self.log_message("تم الاتصال بقاعدة بيانات MySQL بنجاح")
            
            # التحقق من هيكل قاعدة البيانات وإصلاحها
            self.check_and_fix_database_schema()
            
            return True
        except mysql.connector.Error as e:
            # معالجة خاصة لأخطاء MySQL
            if e.errno == 2059:  # Authentication plugin error
                self.log_message("محاولة الاتصال بطريقة بديلة...", "WARNING")
                return self.connect_mysql_alternative()
            else:
                self.log_message(f"خطأ في الاتصال بقاعدة بيانات MySQL: {str(e)}", "ERROR")
                return False
        except Exception as e:
            self.log_message(f"خطأ عام في الاتصال بقاعدة بيانات MySQL: {str(e)}", "ERROR")
            return False
    
    def connect_mysql_alternative(self) -> bool:
        """طريقة بديلة للاتصال بـ MySQL"""
        try:
            # محاولة بدون auth_plugin
            connection_params = self.mysql_config.copy()
            
            if not connection_params.get('password'):
                connection_params.pop('password', None)
            
            # إعدادات مبسطة
            connection_params.update({
                'autocommit': True,
                'use_pure': True,
                'connect_timeout': 30
            })
            
            self.mysql_conn = mysql.connector.connect(**connection_params)
            self.log_message("تم الاتصال بقاعدة البيانات باستخدام الطريقة البديلة")
            
            # التحقق من هيكل قاعدة البيانات وإصلاحها
            self.check_and_fix_database_schema()
            
            return True
        except Exception as e:
            self.log_message(f"فشل في الطريقة البديلة: {str(e)}", "ERROR")
            return False
    
    def check_and_fix_database_schema(self):
        """التحقق من هيكل قاعدة البيانات وإصلاحها للنظام الجديد"""
        try:
            cursor = self.mysql_conn.cursor()
            
            # إنشاء الجداول إذا لم تكن موجودة
            self.create_tables_if_not_exist(cursor)
            
            # التحقق من وجود قيد UNIQUE على page_number
            cursor.execute("""
                SELECT CONSTRAINT_NAME 
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'pages' 
                AND COLUMN_NAME = 'page_number'
                AND CONSTRAINT_NAME LIKE '%unique%'
            """, (self.mysql_config['database'],))
            
            unique_constraints = cursor.fetchall()
            
            if unique_constraints:
                # إزالة قيود UNIQUE من page_number
                for constraint in unique_constraints:
                    try:
                        cursor.execute(f"ALTER TABLE pages DROP INDEX {constraint[0]}")
                        self.log_message(f"تم إزالة قيد UNIQUE: {constraint[0]}")
                    except Exception as e:
                        self.log_message(f"لا يمكن إزالة قيد {constraint[0]}: {e}")
            
            # التحقق من وجود عمود internal_index
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'pages' 
                AND COLUMN_NAME = 'internal_index'
            """, (self.mysql_config['database'],))
            
            internal_index_exists = cursor.fetchone()
            
            if not internal_index_exists:
                # إضافة عمود internal_index
                try:
                    cursor.execute("""
                        ALTER TABLE pages 
                        ADD COLUMN internal_index INT AUTO_INCREMENT UNIQUE FIRST,
                        ADD INDEX idx_internal_index (internal_index)
                    """)
                    self.log_message("تم إضافة عمود internal_index")
                except Exception as e:
                    self.log_message(f"تعذر إضافة internal_index: {e}", "WARNING")
            
            # التحقق من أعمدة internal_index في جدول chapters
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'chapters' 
                AND COLUMN_NAME IN ('start_page_internal_index', 'end_page_internal_index')
            """, (self.mysql_config['database'],))
            
            chapter_columns = [row[0] for row in cursor.fetchall()]
            
            if 'start_page_internal_index' not in chapter_columns:
                try:
                    cursor.execute("ALTER TABLE chapters ADD COLUMN start_page_internal_index INT")
                    self.log_message("تم إضافة عمود start_page_internal_index إلى جدول chapters")
                except Exception as e:
                    self.log_message(f"تعذر إضافة start_page_internal_index: {e}", "WARNING")
            
            if 'end_page_internal_index' not in chapter_columns:
                try:
                    cursor.execute("ALTER TABLE chapters ADD COLUMN end_page_internal_index INT")
                    self.log_message("تم إضافة عمود end_page_internal_index إلى جدول chapters")
                except Exception as e:
                    self.log_message(f"تعذر إضافة end_page_internal_index: {e}", "WARNING")
            
            self.mysql_conn.commit()
            cursor.close()
            
        except Exception as e:
            self.log_message(f"خطأ في فحص هيكل قاعدة البيانات: {str(e)}", "ERROR")
    
    def create_tables_if_not_exist(self, cursor):
        """إنشاء الجداول إذا لم تكن موجودة"""
        try:
            # جدول المؤلفين
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS authors (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # جدول الناشرين
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS publishers (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # جدول الكتب
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS books (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(500) NOT NULL,
                    author_id INT,
                    publisher_id INT,
                    publication_year INT,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (author_id) REFERENCES authors(id),
                    FOREIGN KEY (publisher_id) REFERENCES publishers(id),
                    INDEX idx_book_name (name),
                    INDEX idx_author (author_id),
                    INDEX idx_publisher (publisher_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # جدول الصفحات
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pages (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    book_id INT NOT NULL,
                    page_number INT NOT NULL,
                    volume_number INT DEFAULT 1,
                    content LONGTEXT,
                    html_content LONGTEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
                    INDEX idx_book_page (book_id, page_number),
                    INDEX idx_volume (volume_number),
                    FULLTEXT(content)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # جدول الفصول
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chapters (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    book_id INT NOT NULL,
                    title VARCHAR(500) NOT NULL,
                    level INT DEFAULT 1,
                    start_page_number INT,
                    end_page_number INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
                    INDEX idx_book_chapter (book_id, level),
                    INDEX idx_page_range (start_page_number, end_page_number)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            self.log_message("تم التحقق من وجود جميع الجداول المطلوبة")
            
        except Exception as e:
            self.log_message(f"خطأ في إنشاء الجداول: {str(e)}", "ERROR")
    
    def connect_access(self, access_file_path: str) -> bool:
        """الاتصال بقاعدة بيانات Access"""
        try:
            conn_str = (
                r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
                f'DBQ={access_file_path};'
            )
            self.access_conn = pyodbc.connect(conn_str)
            self.log_message(f"تم الاتصال بملف Access: {os.path.basename(access_file_path)}")
            return True
        except Exception as e:
            self.log_message(f"خطأ في الاتصال بملف Access: {str(e)}", "ERROR")
            return False
    
    def generate_uuid(self) -> str:
        """إنشاء معرف فريد UUID"""
        return str(uuid.uuid4())
    
    def clean_text(self, text: str) -> str:
        """تنظيف النص من الأحرف غير المرغوب فيها مع الحفاظ على التشكيل العربي"""
        if not text:
            return ""
        
        # إزالة الأحرف الخاصة والتحكم مع الحفاظ على التشكيل العربي
        # نطاق التشكيل العربي: U+064B إلى U+065F, U+0670, U+06D6-U+06ED
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', str(text))
        # تنظيف المسافات الزائدة مع الحفاظ على فواصل الأسطر
        text = re.sub(r'[ \t]+', ' ', text)  # استبدال المسافات والتابات المتعددة بمسافة واحدة
        text = re.sub(r'\n\s*\n', '\n\n', text)  # تنظيف الأسطر الفارغة المتعددة
        return text.strip()
    
    def preserve_arabic_diacritics(self, text: str) -> str:
        """الحفاظ على التشكيل والحركات العربية"""
        if not text:
            return ""
        
        # التأكد من أن النص يحتوي على أحرف عربية
        arabic_pattern = r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]'
        if not re.search(arabic_pattern, text):
            return text
        
        # الحفاظ على جميع علامات التشكيل العربية
        # التشكيل الأساسي: الفتحة، الضمة، الكسرة، السكون، الشدة، التنوين
        diacritics_pattern = r'[\u064B-\u065F\u0670\u06D6-\u06ED]'
        
        # إزالة الأحرف غير المرغوب فيها مع الحفاظ على التشكيل
        # إزالة أحرف التحكم فقط وليس التشكيل
        control_chars = r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]'
        text = re.sub(control_chars, '', text)
        
        return text
    
    def format_text_to_html(self, text: str) -> str:
        """تحويل النص إلى تنسيق HTML مع وسوم <p> و <br>"""
        if not text:
            return ""
        
        # الحفاظ على التشكيل أولاً
        text = self.preserve_arabic_diacritics(text)
        
        # معالجة الخطوط الفاصلة === و __________ و ـــــــــ لتكون في أسطر منفصلة
        # أولاً: معالجة ¬__________ في أي مكان في النص وتوحيدها
        text = re.sub(r'¬_{3,}', '¬__________', text)
        # ثانياً: التأكد من أن ¬__________ في سطر منفصل
        text = re.sub(r'(?<!\n)\s*¬__________\s*(?!\n)', '\n¬__________\n', text)
        # إضافة أسطر فارغة قبل وبعد === إذا لم تكن موجودة
        text = re.sub(r'(?<!\n)\s*===\s*(?!\n)', '\n===\n', text)
        # إضافة أسطر فارغة قبل وبعد __________ إذا لم تكن موجودة (ولكن ليس إذا كانت جزءاً من ¬__________)
        # نستخدم negative lookbehind للتأكد من عدم وجود ¬ في السطر السابق
        lines_temp = text.split('\n')
        for i, line in enumerate(lines_temp):
            if line.strip().startswith('__________') and not (i > 0 and '¬' in lines_temp[i-1]):
                if i > 0 and lines_temp[i-1].strip() != '':
                    lines_temp[i] = '\n' + line
                if i < len(lines_temp) - 1 and lines_temp[i+1].strip() != '':
                    lines_temp[i] = line + '\n'
        text = '\n'.join(lines_temp)
        # إضافة أسطر فارغة قبل وبعد ـــــــــ إذا لم تكن موجودة
        text = re.sub(r'(?<!\n)\s*ـ{5,}\s*(?!\n)', '\n' + 'ـ' * 20 + '\n', text)
        
        # تقسيم النص إلى أسطر للمعالجة
        lines = text.split('\n')
        html_content = []
        current_paragraph = []
        
        for line in lines:
            line = line.strip()
            
            # إذا كان السطر فارغ، أنهي الفقرة الحالية
            if not line:
                if current_paragraph:
                    paragraph_text = ' '.join(current_paragraph)
                    html_content.append(f'<p>{paragraph_text}</p>')
                    current_paragraph = []
            # إذا كان السطر يحتوي على فاصل، اعتبره عنصر منفصل
            elif line in ['===', '¬__________'] or line.startswith('__________') or 'ـ' * 5 in line:
                # أنهي الفقرة الحالية أولاً
                if current_paragraph:
                    paragraph_text = ' '.join(current_paragraph)
                    html_content.append(f'<p>{paragraph_text}</p>')
                    current_paragraph = []
                # أضف الفاصل كعنصر منفصل
                html_content.append(f'<p><strong>{line}</strong></p>')
            else:
                # أضف السطر للفقرة الحالية
                current_paragraph.append(line)
        
        # إضافة آخر فقرة إن وجدت
        if current_paragraph:
            paragraph_text = ' '.join(current_paragraph)
            html_content.append(f'<p>{paragraph_text}</p>')
        
        # ربط الفقرات
        return '\n'.join(html_content)
    
    def extract_arabic_text_enhanced(self, text: str) -> str:
        """استخراج وتحسين النص العربي مع الحفاظ على التشكيل"""
        if not text:
            return ""
        
        # تنظيف أولي مع الحفاظ على التشكيل
        text = self.preserve_arabic_diacritics(text)
        
        # إزالة الأحرف غير العربية غير المرغوب فيها مع الحفاظ على علامات الترقيم العربية
        # الحفاظ على: الأحرف العربية، التشكيل، علامات الترقيم، الأرقام العربية والإنجليزية، الرموز الخاصة مثل === و « » والرمز ¬
        allowed_pattern = r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF\u064B-\u065F\u0670\u06D6-\u06ED0-9\s\n\r.,;:!?()\[\]{}"\'-=«»¬_]'
        
        # استخراج الأحرف المسموحة فقط
        cleaned_chars = re.findall(allowed_pattern, text)
        cleaned_text = ''.join(cleaned_chars)
        
        # تنظيف المسافات مع الحفاظ على بنية النص
        cleaned_text = re.sub(r'[ \t]+', ' ', cleaned_text)
        cleaned_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned_text)
        
        return cleaned_text.strip()
    
    def extract_book_info(self) -> Optional[Dict]:
        """استخراج معلومات الكتاب من جدول Main"""
        try:
            cursor = self.access_conn.cursor()
            
            # البحث عن جدول Main أو 0 بطريقة آمنة
            main_tables = []
            
            # محاولة البحث في MSysObjects أولاً
            try:
                cursor.execute("SELECT Name FROM MSysObjects WHERE Type=1 AND Name IN ('Main', '0')")
                main_tables = [row.Name for row in cursor.fetchall()]
                self.log_message("تم الوصول لجدول MSysObjects بنجاح")
            except Exception as msy_error:
                self.log_message(f"تعذر الوصول لـ MSysObjects: {str(msy_error)}", "WARNING")
                
                # البحث المباشر في الجداول المحتملة
                possible_tables = ['Main', '0', 'main', 'book_info', 'info']
                for table_name in possible_tables:
                    try:
                        cursor.execute(f"SELECT TOP 1 * FROM [{table_name}]")
                        main_tables.append(table_name)
                        self.log_message(f"تم العثور على جدول: {table_name}")
                        break
                    except:
                        continue
            
            if not main_tables:
                self.log_message("لم يتم العثور على جدول معلومات الكتاب", "WARNING")
                return self.create_default_book_info()
            
            main_table = main_tables[0]
            self.log_message(f"استخدام جدول المعلومات: {main_table}")
            
            cursor.execute(f"SELECT * FROM [{main_table}]")
            columns = [column[0] for column in cursor.description]
            row = cursor.fetchone()
            
            if row:
                book_info = dict(zip(columns, row))
                self.log_message(f"تم استخراج معلومات الكتاب: {book_info.get('bkname', book_info.get('name', 'غير محدد'))}")
                return book_info
            
            return self.create_default_book_info()
            
        except Exception as e:
            self.log_message(f"خطأ في استخراج معلومات الكتاب: {str(e)}", "ERROR")
            return self.create_default_book_info()
    
    def create_default_book_info(self) -> Dict:
        """إنشاء معلومات كتاب افتراضية"""
        return {
            'bkname': 'كتاب غير معروف',
            'auth_name': 'مؤلف غير معروف', 
            'publisher': 'ناشر غير معروف',
            'pub_year': None,
            'description': 'تم استخراجه من ملف Access'
        }
    
    def find_content_table_smart(self, tables: List[str], cursor) -> str:
        """البحث الذكي عن جدول المحتوى"""
        try:
            # أولوية البحث عن الجداول
            priority_tables = ['b', 'book', 'content', 'محتوى', 'كتاب']
            
            # البحث بالأولوية
            for priority in priority_tables:
                for table in tables:
                    if table.lower() == priority:
                        cursor.execute(f"SELECT COUNT(*) FROM [{table}]")
                        count = cursor.fetchone()[0]
                        if count > 0:
                            self.log_message(f"تم العثور على جدول المحتوى بالأولوية: {table} ({count} سجل)")
                            return table
            
            # البحث عن جداول تحتوي على أعمدة مميزة
            content_indicators = ['nass', 'text', 'content', 'نص', 'محتوى', 'page', 'صفحة']
            
            for table in tables:
                try:
                    cursor.execute(f"SELECT TOP 1 * FROM [{table}]")
                    columns = [column[0].lower() for column in cursor.description]
                    
                    # عد الأعمدة المطابقة
                    matches = sum(1 for indicator in content_indicators 
                                if any(indicator in col for col in columns))
                    
                    if matches >= 2:  # على الأقل مؤشرين
                        cursor.execute(f"SELECT COUNT(*) FROM [{table}]")
                        count = cursor.fetchone()[0]
                        if count > 10:  # يجب أن يحتوي على محتوى كافي
                            self.log_message(f"تم العثور على جدول المحتوى: {table} (مؤشرات: {matches}, سجلات: {count})")
                            return table
                            
                except Exception:
                    continue
            
            # كحل أخير، البحث عن أكبر جدول
            largest_table = self.find_largest_table(tables, cursor)
            if largest_table:
                self.log_message(f"استخدام أكبر جدول كجدول محتوى: {largest_table}")
                return largest_table
            
            return None
            
        except Exception as e:
            self.log_message(f"خطأ في البحث عن جدول المحتوى: {str(e)}", "ERROR")
            return None
    
    def find_largest_table(self, tables: List[str], cursor) -> str:
        """العثور على أكبر جدول كحل أخير"""
        try:
            table_sizes = []
            
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM [{table}]")
                    count = cursor.fetchone()[0]
                    table_sizes.append((table, count))
                except Exception:
                    continue
            
            if table_sizes:
                # ترتيب حسب الحجم
                table_sizes.sort(key=lambda x: x[1], reverse=True)
                largest = table_sizes[0]
                self.log_message(f"أكبر جدول: {largest[0]} ({largest[1]} سجل)")
                return largest[0]
            
            return None
            
        except Exception as e:
            self.log_message(f"خطأ في العثور على أكبر جدول: {str(e)}", "ERROR")
            return None
    
    def extract_book_content(self, table_name: str) -> List[Dict]:
        """استخراج محتوى الكتاب من جدول المحتوى مع معلومات الصفحات والمجلدات"""
        try:
            cursor = self.access_conn.cursor()
            cursor.execute(f"SELECT * FROM [{table_name}] ORDER BY id")
            
            columns = [column[0] for column in cursor.description]
            self.log_message(f"أعمدة جدول {table_name}: {', '.join(columns)}")
            
            content_data = []
            row_count = 0
            
            for row in cursor.fetchall():
                row_count += 1
                if row_count % 1000 == 0:
                    self.log_message(f"تم معالجة {row_count} سجل...")
                
                try:
                    record = dict(zip(columns, row))
                    
                    # استخراج وتنظيف النص
                    text_content = ""
                    for col in ['nass', 'text', 'content', 'النص', 'المحتوى']:
                        if col in record and record[col]:
                            text_content = str(record[col])
                            break
                    
                    if not text_content:
                        # البحث في أي عمود يحتوي على نص
                        for col, value in record.items():
                            if value and isinstance(value, str) and len(str(value)) > 50:
                                text_content = str(value)
                                break
                    
                    if not text_content:
                        continue
                    
                    # تنظيف وتحسين النص
                    cleaned_text = self.extract_arabic_text_enhanced(text_content)
                    if len(cleaned_text.strip()) < 10:
                        continue
                    
                    # تحويل النص إلى HTML
                    html_content = self.format_text_to_html(cleaned_text)
                    
                    # استخراج معلومات الصفحة والمجلد
                    page_info = self.extract_page_info(record)
                    
                    content_record = {
                        'id': record.get('id', row_count),
                        'text': cleaned_text,
                        'html_content': html_content,
                        'page_number': page_info['page_number'],
                        'volume_number': page_info['volume_number'],
                        'raw_record': record
                    }
                    
                    content_data.append(content_record)
                    
                except Exception as e:
                    self.log_message(f"خطأ في معالجة السجل {row_count}: {str(e)}", "WARNING")
                    continue
            
            self.log_message(f"تم استخراج {len(content_data)} سجل من جدول المحتوى")
            return content_data
            
        except Exception as e:
            self.log_message(f"خطأ في استخراج محتوى الكتاب: {str(e)}", "ERROR")
            return []
    
    def extract_page_info(self, record: Dict) -> Dict:
        """استخراج معلومات الصفحة والمجلد من السجل"""
        page_info = {
            'page_number': 1,
            'volume_number': 1
        }
        
        # البحث عن رقم الصفحة
        page_fields = ['page', 'page_num', 'pagenum', 'صفحة', 'رقم_الصفحة']
        for field in page_fields:
            if field in record and record[field] is not None:
                try:
                    page_info['page_number'] = int(record[field])
                    break
                except (ValueError, TypeError):
                    continue
        
        # البحث عن رقم المجلد
        volume_fields = ['volume', 'vol', 'part', 'مجلد', 'جزء']
        for field in volume_fields:
            if field in record and record[field] is not None:
                try:
                    page_info['volume_number'] = int(record[field])
                    break
                except (ValueError, TypeError):
                    continue
        
        return page_info
    
    def extract_book_index(self, table_name: str) -> List[Dict]:
        """استخراج فهرس الكتاب من جدول الفهرس"""
        try:
            cursor = self.access_conn.cursor()
            
            # البحث عن جدول فهرس
            cursor.execute("SELECT Name FROM MSysObjects WHERE Type=1")
            all_tables = [row.Name for row in cursor.fetchall()]
            
            index_tables = [t for t in all_tables if any(keyword in t.lower() 
                          for keyword in ['index', 'فهرس', 'contents', 'toc'])]
            
            if not index_tables:
                self.log_message("لم يتم العثور على جدول فهرس", "INFO")
                return []
            
            index_table = index_tables[0]
            cursor.execute(f"SELECT * FROM [{index_table}]")
            
            # معالجة بيانات الفهرس
            index_data = []
            for row in cursor.fetchall():
                # معالجة بيانات الفهرس هنا
                pass
            
            return index_data
            
        except Exception as e:
            self.log_message(f"خطأ في استخراج فهرس الكتاب: {str(e)}", "ERROR")
            return []
    
    def insert_author(self, author_name: str) -> int:
        """إدراج مؤلف جديد وإرجاع معرفه"""
        try:
            cursor = self.mysql_conn.cursor()
            
            # البحث عن المؤلف الموجود
            cursor.execute("SELECT id FROM authors WHERE name = %s", (author_name,))
            result = cursor.fetchone()
            
            if result:
                return result[0]
            
            # إدراج مؤلف جديد
            cursor.execute("""
                INSERT INTO authors (name, created_at) 
                VALUES (%s, %s)
            """, (author_name, datetime.now()))
            
            author_id = cursor.lastrowid
            self.mysql_conn.commit()
            cursor.close()
            
            self.log_message(f"تم إدراج مؤلف جديد: {author_name}")
            return author_id
            
        except Exception as e:
            self.log_message(f"خطأ في إدراج المؤلف: {str(e)}", "ERROR")
            return 1  # معرف افتراضي
    
    def insert_publisher(self, publisher_name: str) -> int:
        """إدراج ناشر جديد وإرجاع معرفه"""
        try:
            cursor = self.mysql_conn.cursor()
            
            # البحث عن الناشر الموجود
            cursor.execute("SELECT id FROM publishers WHERE name = %s", (publisher_name,))
            result = cursor.fetchone()
            
            if result:
                return result[0]
            
            # إدراج ناشر جديد
            cursor.execute("""
                INSERT INTO publishers (name, created_at) 
                VALUES (%s, %s)
            """, (publisher_name, datetime.now()))
            
            publisher_id = cursor.lastrowid
            self.mysql_conn.commit()
            cursor.close()
            
            self.log_message(f"تم إدراج ناشر جديد: {publisher_name}")
            return publisher_id
            
        except Exception as e:
            self.log_message(f"خطأ في إدراج الناشر: {str(e)}", "ERROR")
            return 1  # معرف افتراضي
    
    def insert_book(self, book_info: Dict, author_id: int, publisher_id: int) -> int:
        """إدراج كتاب جديد"""
        try:
            cursor = self.mysql_conn.cursor()
            
            book_name = book_info.get('bkname', 'كتاب غير معروف')
            
            cursor.execute("""
                INSERT INTO books (
                    name, author_id, publisher_id, 
                    publication_year, description, 
                    created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                book_name,
                author_id,
                publisher_id,
                book_info.get('pub_year'),
                book_info.get('description', ''),
                datetime.now(),
                datetime.now()
            ))
            
            book_id = cursor.lastrowid
            self.mysql_conn.commit()
            cursor.close()
            
            self.log_message(f"تم إدراج كتاب جديد: {book_name}")
            return book_id
            
        except Exception as e:
            self.log_message(f"خطأ في إدراج الكتاب: {str(e)}", "ERROR")
            return 0
    
    def insert_pages_and_chapters(self, book_id: int, content_data: List[Dict], index_data: List[Dict]):
        """إدراج الصفحات والفصول مع ربط صحيح بناءً على ID من Access"""
        try:
            cursor = self.mysql_conn.cursor()
            
            self.log_message(f"بدء إدراج {len(content_data)} صفحة...")
            
            # إدراج الصفحات
            page_mappings = {}  # خريطة ربط بين ID الأصلي و internal_index
            internal_index = 1
            
            for i, content in enumerate(content_data):
                if i % 500 == 0:
                    self.log_message(f"تم إدراج {i} صفحة...")
                
                try:
                    # إدراج الصفحة
                    cursor.execute("""
                        INSERT INTO pages (
                            book_id, page_number, volume_number, 
                            content, html_content, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        book_id,
                        content['page_number'],
                        content['volume_number'],
                        content['text'],
                        content['html_content'],
                        datetime.now()
                    ))
                    
                    # الحصول على internal_index (يتم إنشاؤه تلقائياً)
                    page_id = cursor.lastrowid
                    cursor.execute("SELECT internal_index FROM pages WHERE id = %s", (page_id,))
                    internal_index_result = cursor.fetchone()
                    
                    if internal_index_result:
                        current_internal_index = internal_index_result[0]
                        page_mappings[content['id']] = current_internal_index
                    
                    # commit دوري لتجنب timeout
                    if (i + 1) % 100 == 0:
                        self.mysql_conn.commit()
                    
                except Exception as e:
                    self.log_message(f"خطأ في إدراج الصفحة {i}: {str(e)}", "WARNING")
                    continue
            
            # commit نهائي للصفحات
            self.mysql_conn.commit()
            self.log_message(f"تم إدراج {len(content_data)} صفحة بنجاح")
            
            # إدراج الفصول إذا كانت متوفرة
            if index_data:
                self.log_message(f"بدء إدراج {len(index_data)} فصل...")
                
                for chapter in index_data:
                    try:
                        # ربط الفصل بالصفحات باستخدام internal_index
                        start_internal_index = page_mappings.get(chapter.get('start_page_id'))
                        end_internal_index = page_mappings.get(chapter.get('end_page_id'))
                        
                        cursor.execute("""
                            INSERT INTO chapters (
                                book_id, title, level, 
                                start_page_internal_index, end_page_internal_index,
                                created_at
                            ) VALUES (%s, %s, %s, %s, %s, %s)
                        """, (
                            book_id,
                            chapter.get('title', ''),
                            chapter.get('level', 1),
                            start_internal_index,
                            end_internal_index,
                            datetime.now()
                        ))
                        
                    except Exception as e:
                        self.log_message(f"خطأ في إدراج فصل: {str(e)}", "WARNING")
                        continue
                
                self.mysql_conn.commit()
                self.log_message(f"تم إدراج الفصول بنجاح")
            
            cursor.close()
            
        except Exception as e:
            self.log_message(f"خطأ في إدراج الصفحات والفصول: {str(e)}", "ERROR")
            if self.mysql_conn:
                self.mysql_conn.rollback()
    
    def convert_access_file(self, access_file_path: str) -> bool:
        """تحويل ملف Access واحد"""
        try:
            self.log_message(f"بدء تحويل الملف: {os.path.basename(access_file_path)}")
            
            # الاتصال بملف Access
            if not self.connect_access(access_file_path):
                return False
            
            # استخراج معلومات الكتاب
            book_info = self.extract_book_info()
            if not book_info:
                self.log_message("لم يتم العثور على معلومات الكتاب", "WARNING")
                book_info = {
                    'bkname': os.path.splitext(os.path.basename(access_file_path))[0],
                    'auth_name': 'مؤلف غير معروف',
                    'publisher': 'ناشر غير معروف'
                }
            
            # إدراج المؤلف والناشر
            author_id = self.insert_author(book_info.get('auth_name', 'مؤلف غير معروف'))
            publisher_id = self.insert_publisher(book_info.get('publisher', 'ناشر غير معروف'))
            
            # إدراج الكتاب
            book_id = self.insert_book(book_info, author_id, publisher_id)
            if book_id == 0:
                return False
            
            # العثور على جدول المحتوى
            cursor = self.access_conn.cursor()
            cursor.execute("SELECT Name FROM MSysObjects WHERE Type=1 AND Name NOT LIKE 'MSys%'")
            user_tables = [row.Name for row in cursor.fetchall()]
            
            content_table = self.find_content_table_smart(user_tables, cursor)
            if not content_table:
                self.log_message("لم يتم العثور على جدول المحتوى", "ERROR")
                return False
            
            # استخراج محتوى الكتاب
            content_data = self.extract_book_content(content_table)
            if not content_data:
                self.log_message("لم يتم استخراج أي محتوى", "ERROR")
                return False
            
            # استخراج فهرس الكتاب
            index_data = self.extract_book_index(content_table)
            
            # إدراج الصفحات والفصول
            self.insert_pages_and_chapters(book_id, content_data, index_data)
            
            self.log_message(f"تم تحويل الكتاب بنجاح: {book_info.get('bkname')}")
            return True
            
        except Exception as e:
            self.log_message(f"خطأ في تحويل الملف: {str(e)}", "ERROR")
            return False
        finally:
            if self.access_conn:
                self.access_conn.close()
    
    def convert_file(self, access_file_path: str) -> bool:
        """
        تحويل ملف واحد
        
        Args:
            access_file_path: مسار ملف Access
            
        Returns:
            bool: نجح التحويل أم لا
        """
        try:
            # فحص وجود الملف
            if not os.path.exists(access_file_path):
                self.log_message(f"الملف غير موجود: {access_file_path}", "ERROR")
                return False
            
            # فحص امتداد الملف
            file_ext = os.path.splitext(access_file_path)[1].lower()
            if file_ext not in ['.accdb', '.mdb']:
                self.log_message(f"نوع ملف غير مدعوم: {file_ext}", "ERROR")
                return False
            
            # الاتصال بقاعدة بيانات MySQL
            if not self.connect_mysql():
                return False
            
            try:
                # تحويل الملف
                success = self.convert_access_file(access_file_path)
                
                if success:
                    self.log_message(f"تم تحويل الملف بنجاح: {os.path.basename(access_file_path)}")
                else:
                    self.log_message(f"فشل في تحويل الملف: {os.path.basename(access_file_path)}", "ERROR")
                
                return success
                
            finally:
                if self.mysql_conn:
                    self.mysql_conn.close()
                    
        except Exception as e:
            self.log_message(f"خطأ عام في تحويل الملف: {str(e)}", "ERROR")
            return False

    def convert_multiple_files(self, access_files: List[str]) -> Dict[str, bool]:
        """تحويل عدة ملفات Access"""
        results = {}
        
        if not self.connect_mysql():
            return results
        
        try:
            total_files = len(access_files)
            self.log_message(f"بدء تحويل {total_files} ملف...")
            
            for i, file_path in enumerate(access_files, 1):
                self.log_message(f"[{i}/{total_files}] معالجة: {os.path.basename(file_path)}")
                
                try:
                    success = self.convert_access_file(file_path)
                    results[os.path.basename(file_path)] = success
                except Exception as e:
                    self.log_message(f"خطأ في ملف {os.path.basename(file_path)}: {str(e)}", "ERROR")
                    results[os.path.basename(file_path)] = False
            
        except Exception as e:
            self.log_message(f"خطأ عام في تحويل الملفات: {str(e)}", "ERROR")
        
        finally:
            if self.mysql_conn:
                self.mysql_conn.close()
        
        return results
    
    def save_log(self, log_file_path: str):
        """حفظ سجل العمليات في ملف"""
        try:
            with open(log_file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.conversion_log))
        except Exception as e:
            print(f"خطأ في حفظ السجل: {e}")


def main():
    """الدالة الرئيسية"""
    print("=== محول كتب الشاملة من Access إلى MySQL ===")
    print("المطور: مساعد الذكي الاصطناعي")
    print("="*50)
    
    # إعدادات قاعدة البيانات MySQL
    mysql_config = {
        'host': '145.223.98.97',
        'port': 3306,
        'user': 'bms',
        'password': 'bms2025',
        'database': 'bms',
        'charset': 'utf8mb4',
        'use_unicode': True
    }
    
    # ملفات Access للتحويل
    access_files = [
        r"c:\Users\osaidsalah002\Documents\test3_v00\access file\خلاصة.accdb"
    ]
    
    # إنشاء المحول
    converter = ShamelaConverter(mysql_config)
    
    # تحويل الملفات
    results = converter.convert_multiple_files(access_files)
    
    # عرض النتائج
    print("\n=== نتائج التحويل ===")
    for file_name, success in results.items():
        status = "نجح" if success else "فشل"
        print(f"{file_name}: {status}")
    
    # حفظ السجل
    log_file = f"conversion_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    converter.save_log(log_file)
    
    print(f"\nتم الانتهاء من عملية التحويل. راجع ملف السجل: {log_file}")


if __name__ == "__main__":
    main()