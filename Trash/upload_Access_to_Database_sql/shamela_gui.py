import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
import json
import os
from datetime import datetime, timedelta
import pyodbc
import pymysql
from pathlib import Path
import uuid
import re
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
            
            self.mysql_conn = pymysql.connect(**connection_params)
            self.log_message("تم الاتصال بقاعدة بيانات MySQL بنجاح")
            
            # التحقق من هيكل قاعدة البيانات وإصلاحها
            self.check_and_fix_database_schema()
            
            return True
        except Exception as e:
            self.log_message(f"خطأ في الاتصال بقاعدة بيانات MySQL: {str(e)}", "ERROR")
            return False
    
    def check_and_fix_database_schema(self):
        """التحقق من هيكل قاعدة البيانات وإصلاحها للنظام الجديد"""
        try:
            cursor = self.mysql_conn.cursor()
            
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
                self.log_message("تم اكتشاف قيد UNIQUE على page_number - سيتم إزالته للنظام الجديد")
                
                for constraint in unique_constraints:
                    constraint_name = constraint[0]
                    try:
                        cursor.execute(f"ALTER TABLE pages DROP INDEX {constraint_name}")
                        self.log_message(f"تم إزالة القيد: {constraint_name}")
                    except Exception as drop_error:
                        self.log_message(f"تحذير: لم يتم إزالة القيد {constraint_name}: {str(drop_error)}", "WARNING")
            
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
                self.log_message("إضافة عمود internal_index لجدول pages...")
                cursor.execute("""
                    ALTER TABLE pages 
                    ADD COLUMN internal_index INT NOT NULL AUTO_INCREMENT FIRST,
                    ADD PRIMARY KEY (internal_index)
                """)
                self.log_message("تم إضافة عمود internal_index بنجاح")
            
            # التحقق من أعمدة internal_index في جدول chapters
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'chapters' 
                AND COLUMN_NAME IN ('internal_index_start', 'internal_index_end')
            """, (self.mysql_config['database'],))
            
            chapter_columns = [row[0] for row in cursor.fetchall()]
            
            if 'internal_index_start' not in chapter_columns:
                cursor.execute("ALTER TABLE chapters ADD COLUMN internal_index_start INT")
                self.log_message("تم إضافة عمود internal_index_start لجدول chapters")
                
            if 'internal_index_end' not in chapter_columns:
                cursor.execute("ALTER TABLE chapters ADD COLUMN internal_index_end INT")
                self.log_message("تم إضافة عمود internal_index_end لجدول chapters")
            
            self.mysql_conn.commit()
            self.log_message("تم التحقق من هيكل قاعدة البيانات وإصلاحها للنظام الجديد")
            
        except Exception as e:
            self.log_message(f"خطأ في فحص/إصلاح هيكل قاعدة البيانات: {str(e)}", "ERROR")
    
    def connect_access(self, access_file_path: str) -> bool:
        """الاتصال بقاعدة بيانات Access"""
        try:
            if not os.path.exists(access_file_path):
                self.log_message(f"ملف Access غير موجود: {access_file_path}", "ERROR")
                return False
            
            conn_str = f'DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={access_file_path};'
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
            if re.match(r'^_{3,}$', line.strip()):
                # تحقق من السطر السابق
                if i > 0 and lines_temp[i-1].strip() == '¬':
                    continue  # لا تعالج هذا الخط لأنه جزء من ¬__________
                # إضافة أسطر فارغة قبل وبعد إذا لم تكن موجودة
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
            
            # إذا كان السطر فارغ، إنهاء الفقرة الحالية
            if not line:
                if current_paragraph:
                    paragraph_text = '<br>\n'.join(current_paragraph)
                    html_content.append(f'<p>{paragraph_text}</p>')
                    current_paragraph = []
            # إذا كان السطر يحتوي على === أو خط فاصل
            elif line == '===' or re.match(r'^_{3,}$', line) or re.match(r'^ـ{3,}$', line) or re.match(r'^¬_{3,}$', line):
                # إنهاء الفقرة الحالية إن وجدت
                if current_paragraph:
                    paragraph_text = '<br>\n'.join(current_paragraph)
                    html_content.append(f'<p>{paragraph_text}</p>')
                    current_paragraph = []
                # إضافة الخط الفاصل في سطر منفصل
                html_content.append(f'<p style="text-align: center; margin: 10px 0;">{line}</p>')
            else:
                # إضافة السطر للفقرة الحالية
                current_paragraph.append(line)
        
        # إضافة آخر فقرة إن وجدت
        if current_paragraph:
            paragraph_text = '<br>\n'.join(current_paragraph)
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
            cursor.execute("SELECT * FROM Main")
            row = cursor.fetchone()
            
            if not row:
                self.log_message("لا توجد بيانات في جدول Main", "WARNING")
                return None
            
            # الحصول على أسماء الأعمدة
            columns = [column[0] for column in cursor.description]
            book_data = dict(zip(columns, row))
            
            # تنظيف البيانات
            cleaned_data = {}
            for key, value in book_data.items():
                if isinstance(value, str):
                    cleaned_data[key] = self.clean_text(value)
                else:
                    cleaned_data[key] = value
            
            self.log_message(f"تم استخراج معلومات الكتاب: {cleaned_data.get('Bk', 'غير محدد')}")
            return cleaned_data
            
        except Exception as e:
            self.log_message(f"خطأ في استخراج معلومات الكتاب: {str(e)}", "ERROR")
            return None
    
    def find_content_table_smart(self, tables: List[str], cursor) -> str:
        """البحث الذكي عن جدول المحتوى"""
        try:
            self.log_message("بدء البحث الذكي عن جدول المحتوى...")
            
            candidates = []
            
            for table in tables:
                try:
                    # فحص عدد الصفوف
                    cursor.execute(f"SELECT COUNT(*) FROM [{table}]")
                    row_count = cursor.fetchone()[0]
                    
                    # تجاهل الجداول الصغيرة جداً
                    if row_count < 10:
                        continue
                    
                    # فحص أعمدة الجدول
                    cursor.execute(f"SELECT * FROM [{table}] WHERE 1=0")
                    columns = [desc[0].lower() for desc in cursor.description]
                    
                    score = 0
                    
                    # البحث عن كلمات مفتاحية في أسماء الأعمدة
                    text_indicators = ['nass', 'text', 'content', 'matn', 'متن', 'نص']
                    page_indicators = ['page', 'sahefa', 'safha', 'صفحة', 'صحيفة']
                    id_indicators = ['id', 'معرف', 'رقم']
                    
                    # نقاط للأعمدة النصية
                    for indicator in text_indicators:
                        if any(indicator in col for col in columns):
                            score += 30
                            
                    # نقاط لأعمدة الصفحات
                    for indicator in page_indicators:
                        if any(indicator in col for col in columns):
                            score += 20
                            
                    # نقاط لأعمدة المعرف
                    for indicator in id_indicators:
                        if any(indicator in col for col in columns):
                            score += 10
                    
                    # نقاط حسب حجم الجدول
                    if row_count > 1000:
                        score += 25
                    elif row_count > 500:
                        score += 15
                    elif row_count > 100:
                        score += 10
                    elif row_count > 50:
                        score += 5
                    
                    # نقاط إضافية للجداول التي تحتوي على نصوص طويلة
                    if score > 20:  # فقط إذا كان الجدول مرشح جيد
                        cursor.execute(f"SELECT TOP 1 * FROM [{table}]")
                        sample_row = cursor.fetchone()
                        if sample_row:
                            for value in sample_row:
                                if isinstance(value, str) and len(value) > 100:
                                    score += 15
                                    break
                    
                    if score > 0:
                        candidates.append((table, score, row_count))
                        self.log_message(f"مرشح: {table} - نقاط: {score} - صفوف: {row_count}")
                        
                except Exception as e:
                    self.log_message(f"خطأ في فحص الجدول {table}: {e}", "WARNING")
                    continue
            
            if candidates:
                # ترتيب المرشحين حسب النقاط
                candidates.sort(key=lambda x: x[1], reverse=True)
                best_table = candidates[0][0]
                self.log_message(f"أفضل مرشح: {best_table} بنقاط {candidates[0][1]}")
                return best_table
            
            return None
            
        except Exception as e:
            self.log_message(f"خطأ في البحث الذكي: {e}", "ERROR")
            return None
    
    def find_largest_table(self, tables: List[str], cursor) -> str:
        """العثور على أكبر جدول كحل أخير"""
        try:
            self.log_message("البحث عن أكبر جدول كحل أخير...")
            
            largest_table = None
            max_rows = 0
            
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM [{table}]")
                    row_count = cursor.fetchone()[0]
                    
                    if row_count > max_rows:
                        max_rows = row_count
                        largest_table = table
                        
                except Exception as e:
                    continue
            
            if largest_table and max_rows > 10:
                self.log_message(f"أكبر جدول: {largest_table} ({max_rows} صف)")
                return largest_table
            
            return None
            
        except Exception as e:
            self.log_message(f"خطأ في البحث عن أكبر جدول: {e}", "ERROR")
            return None
    
    def extract_book_content(self, table_name: str) -> List[Dict]:
        """استخراج محتوى الكتاب من جدول المحتوى مع معلومات الصفحات والمجلدات"""
        try:
            cursor = self.access_conn.cursor()
            
            # فحص هيكل الجدول أولاً
            cursor.execute(f"SELECT * FROM [{table_name}] WHERE 1=0")
            columns = [column[0] for column in cursor.description]
            self.log_message(f"أعمدة الجدول {table_name}: {columns}")
            
            # تحديد أعمدة مهمة
            text_column = None
            id_column = None
            page_column = None
            part_column = None
            
            # البحث عن عمود النص
            for col in columns:
                col_lower = col.lower()
                if 'nass' in col_lower or 'text' in col_lower or 'content' in col_lower or 'متن' in col_lower:
                    text_column = col
                    break
            
            # البحث عن عمود المعرف
            for col in columns:
                col_lower = col.lower()
                if col_lower in ['id', 'معرف', 'رقم'] or col_lower.endswith('id'):
                    id_column = col
                    break
            
            # البحث عن عمود الصفحة
            for col in columns:
                col_lower = col.lower()
                if 'page' in col_lower or 'sahefa' in col_lower or 'صفحة' in col_lower:
                    page_column = col
                    break
                    
            # البحث عن عمود الجزء
            for col in columns:
                col_lower = col.lower()
                if 'part' in col_lower or 'juz' in col_lower or 'جزء' in col_lower:
                    part_column = col
                    break
            
            # إذا لم نجد أعمدة محددة، نأخذ أول عمود كمعرف وثاني عمود كنص
            if not id_column and len(columns) > 0:
                id_column = columns[0]
            if not text_column and len(columns) > 1:
                text_column = columns[1]
            
            self.log_message(f"الأعمدة المحددة - المعرف: {id_column}, النص: {text_column}, الصفحة: {page_column}")
            
            # بناء الاستعلام
            try:
                # محاولة الترتيب بالمعرف أولاً
                cursor.execute(f"SELECT * FROM [{table_name}] ORDER BY [{id_column}]")
            except:
                # إذا فشل، نأخذ بدون ترتيب
                cursor.execute(f"SELECT * FROM [{table_name}]")
            
            content_data = []
            
            for row in cursor.fetchall():
                row_data = dict(zip(columns, row))
                
                # استخراج وتحسين النص العربي مع الحفاظ على التشكيل
                raw_text = ""
                if text_column and text_column in row_data and row_data[text_column]:
                    raw_text = str(row_data[text_column])
                elif 'nass' in row_data and row_data['nass']:
                    raw_text = str(row_data['nass'])
                else:
                    # البحث عن أي عمود يحتوي على نص طويل
                    for key, value in row_data.items():
                        if isinstance(value, str) and len(value) > 50:
                            raw_text = str(value)
                            break
                
                # معالجة النص بالطرق الجديدة
                if raw_text:
                    # استخراج النص العربي مع الحفاظ على التشكيل
                    enhanced_text = self.extract_arabic_text_enhanced(raw_text)
                    # تحويل إلى HTML
                    row_data['nass'] = enhanced_text
                    row_data['nass_html'] = self.format_text_to_html(enhanced_text)
                else:
                    row_data['nass'] = ''
                    row_data['nass_html'] = ''
                
                # تحديد رقم الصفحة
                if page_column and page_column in row_data:
                    try:
                        row_data['page'] = int(row_data[page_column])
                    except:
                        row_data['page'] = 1
                elif 'page' not in row_data:
                    row_data['page'] = 1
                
                # تحديد رقم الجزء
                if part_column and part_column in row_data:
                    try:
                        row_data['part'] = int(row_data[part_column])
                    except:
                        row_data['part'] = 1
                elif 'part' not in row_data:
                    row_data['part'] = 1
                
                content_data.append(row_data)
            
            self.log_message(f"تم استخراج {len(content_data)} صف من جدول {table_name}")
            
            # إظهار عينة من البيانات للتأكد
            if content_data:
                sample = content_data[0]
                self.log_message(f"عينة من البيانات: النص={sample.get('nass', '')[:100]}...")
            
            return content_data
            
        except Exception as e:
            self.log_message(f"خطأ في استخراج محتوى الكتاب من {table_name}: {str(e)}", "ERROR")
            return []
    
    def extract_book_index(self, table_name: str) -> List[Dict]:
        """استخراج فهرس الكتاب من جدول الفهرس"""
        try:
            cursor = self.access_conn.cursor()
            cursor.execute(f"SELECT * FROM [{table_name}] ORDER BY id")
            
            columns = [column[0] for column in cursor.description]
            index_data = []
            
            for row in cursor.fetchall():
                row_data = dict(zip(columns, row))
                # تنظيف العنوان
                if 'tit' in row_data and row_data['tit']:
                    row_data['tit'] = self.clean_text(row_data['tit'])
                index_data.append(row_data)
            
            self.log_message(f"تم استخراج {len(index_data)} عنصر من فهرس {table_name}")
            return index_data
            
        except Exception as e:
            self.log_message(f"خطأ في استخراج فهرس الكتاب من {table_name}: {str(e)}", "ERROR")
            return []
    
    def insert_author(self, author_name: str) -> int:
        """إدراج مؤلف جديد وإرجاع معرفه"""
        try:
            cursor = self.mysql_conn.cursor()
            
            # التحقق من وجود المؤلف
            cursor.execute("SELECT id FROM authors WHERE full_name = %s", (author_name,))
            existing = cursor.fetchone()
            
            if existing:
                return existing[0]
            
            # إدراج مؤلف جديد
            insert_query = """
                INSERT INTO authors (full_name, created_at, updated_at)
                VALUES (%s, %s, %s)
            """
            now = datetime.now()
            cursor.execute(insert_query, (author_name, now, now))
            author_id = cursor.lastrowid
            
            self.log_message(f"تم إدراج مؤلف جديد: {author_name}")
            return author_id
            
        except Exception as e:
            self.log_message(f"خطأ في إدراج المؤلف: {str(e)}", "ERROR")
            return 1  # إرجاع معرف افتراضي
    
    def insert_publisher(self, publisher_name: str) -> int:
        """إدراج ناشر جديد وإرجاع معرفه"""
        try:
            cursor = self.mysql_conn.cursor()
            
            # التحقق من وجود الناشر
            cursor.execute("SELECT id FROM publishers WHERE name = %s", (publisher_name,))
            existing = cursor.fetchone()
            
            if existing:
                return existing[0]
            
            # إدراج ناشر جديد
            insert_query = """
                INSERT INTO publishers (name, created_at, updated_at)
                VALUES (%s, %s, %s)
            """
            now = datetime.now()
            cursor.execute(insert_query, (publisher_name, now, now))
            publisher_id = cursor.lastrowid
            
            self.log_message(f"تم إدراج ناشر جديد: {publisher_name}")
            return publisher_id
            
        except Exception as e:
            self.log_message(f"خطأ في إدراج الناشر: {str(e)}", "ERROR")
            return 1  # إرجاع معرف افتراضي
    
    def insert_book(self, book_info: Dict, author_id: int, publisher_id: int) -> int:
        """إدراج كتاب جديد"""
        try:
            cursor = self.mysql_conn.cursor()
            
            # استخراج المعلومات المهمة
            title = book_info.get('Bk', 'كتاب بدون عنوان')
            description = book_info.get('Betaka', '')
            shamela_id = str(book_info.get('BkId', ''))
            
            # إنشاء slug من العنوان مع timestamp لضمان التفرد
            import re
            from datetime import datetime
            slug = re.sub(r'[^\w\s-]', '', title).strip()
            slug = re.sub(r'[-\s]+', '-', slug)
            slug = f"{slug}-{int(datetime.now().timestamp())}"
            
            # إدراج كتاب جديد دائماً
            insert_query = """
                INSERT INTO books (shamela_id, title, description, slug, publisher_id, 
                                 status, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            now = datetime.now()
            cursor.execute(insert_query, (
                shamela_id, title, description, slug, publisher_id,
                'published', now, now
            ))
            
            book_id = cursor.lastrowid
            self.log_message(f"تم إدراج كتاب جديد: {title}")
            return book_id
            
        except Exception as e:
            self.log_message(f"خطأ في إدراج الكتاب: {str(e)}", "ERROR")
            return 1
    
    def insert_pages_and_chapters(self, book_id: int, content_data: List[Dict], index_data: List[Dict]):
        """إدراج الصفحات والفصول مع ربط صحيح بناءً على ID من Access"""
        try:
            cursor = self.mysql_conn.cursor()
            now = datetime.now()
            
            # تحديد قيم الأجزاء الموجودة في البيانات
            parts_in_data = set()
            for content_item in content_data:
                part_value = content_item.get('part') or content_item.get('Part')
                if part_value is not None:
                    try:
                        parts_in_data.add(int(part_value))
                    except:
                        parts_in_data.add(1)  # قيمة افتراضية
                else:
                    parts_in_data.add(1)  # قيمة افتراضية
            
            # إنشاء مجلدات حسب الأجزاء الموجودة
            volume_map = {}  # خريطة part -> volume_id
            
            # تحويل أرقام الأجزاء إلى أسماء عربية
            arabic_ordinals = {
                1: "الأول", 2: "الثاني", 3: "الثالث", 4: "الرابع", 5: "الخامس",
                6: "السادس", 7: "السابع", 8: "الثامن", 9: "التاسع", 10: "العاشر"
            }
            
            for part_num in sorted(parts_in_data):
                ordinal = arabic_ordinals.get(part_num, f"الـ{part_num}")
                volume_title = f"المجلد {ordinal}"
                
                try:
                    volume_query = """
                        INSERT INTO volumes (book_id, number, title, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s)
                    """
                    cursor.execute(volume_query, (book_id, part_num, volume_title, now, now))
                    volume_id = cursor.lastrowid
                    volume_map[part_num] = volume_id
                    self.log_message(f"تم إنشاء {volume_title} برقم {volume_id}")
                    
                except Exception as vol_error:
                    if "Duplicate entry" in str(vol_error):
                        # المجلد موجود مسبقاً، استخدم الموجود
                        cursor.execute("SELECT id FROM volumes WHERE book_id = %s AND number = %s", (book_id, part_num))
                        existing_volume = cursor.fetchone()
                        if existing_volume:
                            volume_id = existing_volume[0]
                            volume_map[part_num] = volume_id
                            self.log_message(f"استخدام {volume_title} الموجود برقم {volume_id}")
                        else:
                            self.log_message(f"خطأ في إنشاء {volume_title}: {str(vol_error)}", "ERROR")
                            return
                    else:
                        self.log_message(f"خطأ في إنشاء {volume_title}: {str(vol_error)}", "ERROR")
                        return
            
            # استخدام المجلد الأول كافتراضي إذا لم يتم العثور على part
            default_volume_id = volume_map.get(1, list(volume_map.values())[0] if volume_map else None)
            if not default_volume_id:
                self.log_message("خطأ: لم يتم إنشاء أي مجلد", "ERROR")
                return
            
            # 1. إدراج الفصول أولاً - استخدام ID من Access كنقاط بداية ونهاية
            chapter_data = {}  # خريطة لحفظ معلومات الفصول {access_id: chapter_db_id}
            chapter_count = 0
            sorted_index = sorted(index_data, key=lambda x: x.get('id', 0))
            
            self.log_message(f"بدء معالجة {len(sorted_index)} فصل بناءً على ID من Access")
            
            for i, index_item in enumerate(sorted_index):
                chapter_start_id = index_item.get('id')  # ID من جدول الفهرس = نقطة البداية
                chapter_title = self.clean_text(index_item.get('tit', f'فصل {chapter_start_id}'))
                chapter_level = index_item.get('lvl', 1)
                
                # تحديد نطاق ID للفصل (هذا هو المفتاح الصحيح!)
                start_id = chapter_start_id
                if i < len(sorted_index) - 1:
                    end_id = sorted_index[i + 1].get('id') - 1  # قبل بداية الفصل التالي
                else:
                    # الفصل الأخير - أخذ آخر ID من المحتوى
                    end_id = max([item.get('id', 0) for item in content_data])
                
                # تحديد المجلد المناسب للفصل بناءً على الجزء الذي تنتمي إليه الصفحة الأولى
                chapter_volume_id = default_volume_id  # قيمة افتراضية
                
                # البحث عن أول صفحة في هذا الفصل لمعرفة الجزء
                for content_item in content_data:
                    content_id = content_item.get('id', 0)
                    if start_id <= content_id <= end_id:
                        # وجدنا صفحة تنتمي لهذا الفصل
                        page_part = content_item.get('part') or content_item.get('Part')
                        if page_part is not None:
                            try:
                                page_part = int(page_part)
                                chapter_volume_id = volume_map.get(page_part, default_volume_id)
                                break  # نأخذ الجزء من أول صفحة فقط
                            except:
                                pass
                
                # إدراج الفصل
                chapter_query = """
                    INSERT INTO chapters (book_id, volume_id, title, level, page_start, page_end, 
                                        `order`, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(chapter_query, (
                    book_id, chapter_volume_id, chapter_title, chapter_level,
                    start_id, end_id, chapter_start_id, now, now
                ))
                
                db_chapter_id = cursor.lastrowid
                chapter_count += 1
                
                # حفظ معلومات الفصل للاستخدام في ربط الصفحات
                chapter_data[chapter_start_id] = {
                    'db_id': db_chapter_id,
                    'start_id': start_id,
                    'end_id': end_id,
                    'title': chapter_title,
                    'volume_id': chapter_volume_id
                }
                
                # الحصول على اسم المجلد للطباعة
                cursor.execute("SELECT title FROM volumes WHERE id = %s", (chapter_volume_id,))
                volume_result = cursor.fetchone()
                volume_title = volume_result[0] if volume_result else "غير معروف"
                
                self.log_message(f"فصل '{chapter_title}': ID من {start_id} إلى {end_id} في {volume_title}")
            
            self.log_message(f"تم إدراج {chapter_count} فصل")
            
            # 2. إدراج الصفحات مع ربطها بالفصول بناءً على ID من Access
            page_count = 0
            pages_without_chapter = 0
            pages_with_chapter = 0
            part_stats = {}  # إحصائيات توزيع الصفحات حسب part
            
            self.log_message(f"بدء معالجة {len(content_data)} صفحة مع ربط بناءً على ID من Access")
            
            for content_item in content_data:
                content_id = content_item.get('id', 0)  # ID الفعلي من Access
                page_num = content_item.get('page', content_id)  # رقم الصفحة المطبوعة
                content_text = content_item.get('nass', '')
                
                # استخراج قيمة part من البيانات
                part_value = content_item.get('part') or content_item.get('Part')
                if part_value is not None:
                    part_value = int(part_value) if str(part_value).strip() != '' else None
                
                # تتبع إحصائيات الأجزاء
                part_key = part_value if part_value is not None else "بدون جزء"
                if part_key not in part_stats:
                    part_stats[part_key] = 0
                part_stats[part_key] += 1
                
                # تحديد الفصل المناسب للصفحة بناءً على ID من Access (هذا هو التصحيح الأساسي!)
                chapter_id_for_page = None
                for ch_access_id, ch_info in chapter_data.items():
                    if ch_info['start_id'] <= content_id <= ch_info['end_id']:
                        chapter_id_for_page = ch_info['db_id']
                        pages_with_chapter += 1
                        break
                
                if not chapter_id_for_page:
                    pages_without_chapter += 1
                
                # إدراج الصفحة
                try:
                    sequential_page_number = page_count + 1
                    
                    # الحصول على النص المحسن بصيغة HTML إذا كان متوفراً
                    content_html = content_item.get('nass_html', '')
                    
                    # التحقق من وجود عمود content_html في جدول pages
                    cursor.execute("""
                        SELECT COUNT(*) FROM information_schema.COLUMNS 
                        WHERE TABLE_SCHEMA = DATABASE() 
                        AND TABLE_NAME = 'pages' 
                        AND COLUMN_NAME = 'content_html'
                    """)
                    
                    has_html_column = cursor.fetchone()[0] > 0
                    
                    if has_html_column and content_html:
                        # إدراج مع عمود HTML
                        page_query = """
                            INSERT INTO pages (book_id, chapter_id, page_number, internal_index, content, content_html, part, created_at, updated_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """
                        cursor.execute(page_query, (
                            book_id, chapter_id_for_page, sequential_page_number, 
                            str(content_id), content_text, content_html, part_value, now, now
                        ))
                    else:
                        # إدراج بدون عمود HTML (الطريقة القديمة)
                        page_query = """
                            INSERT INTO pages (book_id, chapter_id, page_number, internal_index, content, part, created_at, updated_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """
                        cursor.execute(page_query, (
                            book_id, chapter_id_for_page, sequential_page_number, 
                            str(content_id), content_text, part_value, now, now
                        ))
                    
                    page_count += 1
                    
                    # طباعة تقدم كل 100 صفحة
                    if page_count % 100 == 0:
                        self.log_message(f"تم معالجة {page_count} صفحة (page_number: {sequential_page_number}, access_id: {content_id})")
                        
                except Exception as page_error:
                    self.log_message(f"خطأ في إدراج الصفحة (access_id: {content_id}): {str(page_error)}", "ERROR")
                    continue
            
            # طباعة الإحصائيات النهائية
            self.log_message("=== إحصائيات الربط ===")
            self.log_message(f"إجمالي الصفحات: {page_count}")
            self.log_message(f"إجمالي الفصول: {chapter_count}")
            self.log_message(f"الصفحات بدون فصل: {pages_without_chapter}")
            self.log_message(f"الصفحات المربوطة بفصول: {pages_with_chapter}")
            self.log_message(f"نسبة الربط الناجح: {(pages_with_chapter/page_count)*100:.1f}%")
            
            # طباعة إحصائيات توزيع الصفحات حسب part
            self.log_message("=== إحصائيات توزيع الصفحات حسب الأجزاء ===")
            for part_key in sorted(part_stats.keys()):
                count = part_stats[part_key]
                self.log_message(f"الجزء {part_key}: {count} صفحة")
            
            # طباعة إحصائيات توزيع الفصول على المجلدات
            self.log_message("=== إحصائيات توزيع الفصول على المجلدات ===")
            volume_chapter_count = {}
            for ch_info in chapter_data.values():
                vol_id = ch_info['volume_id']
                if vol_id not in volume_chapter_count:
                    volume_chapter_count[vol_id] = 0
                volume_chapter_count[vol_id] += 1
            
            for vol_id, count in volume_chapter_count.items():
                cursor.execute("SELECT title FROM volumes WHERE id = %s", (vol_id,))
                vol_result = cursor.fetchone()
                vol_title = vol_result[0] if vol_result else f"مجلد {vol_id}"
                self.log_message(f"{vol_title}: {count} فصل")
            
            # طباعة ملخص نطاقات الفصول للتأكد
            self.log_message("=== ملخص نطاقات الفصول (Access ID) ===")
            for ch_access_id, ch_info in sorted(chapter_data.items()):
                cursor.execute("""
                    SELECT COUNT(*) FROM pages 
                    WHERE book_id = %s AND chapter_id = %s
                """, (book_id, ch_info['db_id']))
                chapter_page_count = cursor.fetchone()[0]
                
                # الحصول على اسم المجلد
                cursor.execute("SELECT title FROM volumes WHERE id = %s", (ch_info['volume_id'],))
                vol_result = cursor.fetchone()
                vol_title = vol_result[0] if vol_result else "غير معروف"
                
                self.log_message(f"'{ch_info['title']}': ID {ch_info['start_id']}-{ch_info['end_id']} ({chapter_page_count} صفحة) - {vol_title}")
            
            self.log_message(f"تم إدراج {page_count} صفحة و {chapter_count} فصل للكتاب")
            
            # 3. تحديث نطاقات الفصول لتستخدم page_number التسلسلي (للعرض)
            self.log_message("تحديث نطاقات الفصول للعرض بـ page_number التسلسلي...")
            
            for ch_access_id, ch_info in chapter_data.items():
                chapter_id = ch_info['db_id']
                try:
                    # البحث عن أول وآخر page_number (التسلسلي) للصفحات في هذا الفصل
                    cursor.execute("""
                        SELECT MIN(page_number), MAX(page_number)
                        FROM pages 
                        WHERE book_id = %s AND chapter_id = %s
                    """, (book_id, chapter_id))
                    
                    result = cursor.fetchone()
                    if result and result[0] is not None:
                        page_start, page_end = result
                        
                        # تحديث الفصل بنطاق page_number التسلسلي للعرض
                        cursor.execute("""
                            UPDATE chapters 
                            SET page_start = %s, page_end = %s, updated_at = %s
                            WHERE id = %s
                        """, (page_start, page_end, now, chapter_id))
                        
                except Exception as chapter_update_error:
                    self.log_message(f"خطأ في تحديث الفصل {chapter_id}: {str(chapter_update_error)}", "ERROR")
            
            # 4. تحديث عدد الصفحات في جدول books
            try:
                update_book_query = """
                    UPDATE books SET page_count = %s, updated_at = %s
                    WHERE id = %s
                """
                cursor.execute(update_book_query, (page_count, now, book_id))
                self.log_message(f"تم تحديث معلومات الكتاب: {page_count} صفحة")
            except Exception as update_error:
                self.log_message(f"تحذير: لم يتم تحديث معلومات الكتاب: {str(update_error)}", "WARNING")
            
        except Exception as e:
            self.log_message(f"خطأ في إدراج الصفحات والفصول: {str(e)}", "ERROR")
    
    def convert_access_file(self, access_file_path: str) -> bool:
        """تحويل ملف Access واحد"""
        try:
            self.log_message(f"بدء تحويل ملف: {os.path.basename(access_file_path)}")
            
            # الاتصال بملف Access
            if not self.connect_access(access_file_path):
                return False
            
            # استخراج معلومات الكتاب
            book_info = self.extract_book_info()
            if not book_info:
                return False
            
            # تحديد أسماء جداول المحتوى والفهرس بطريقة ذكية
            cursor = self.access_conn.cursor()
            tables = [table.table_name for table in cursor.tables(tableType='TABLE') 
                     if not table.table_name.startswith('MSys')]
            
            self.log_message(f"الجداول الموجودة: {tables}")
            
            content_table = None
            index_table = None
            
            # البحث بالطريقة التقليدية أولاً
            for table in tables:
                if table.startswith('b') and table[1:].isdigit():
                    content_table = table
                elif table.startswith('t') and table[1:].isdigit():
                    index_table = table
            
            # إذا لم نجد بالطريقة التقليدية، نبحث بطريقة ذكية
            if not content_table:
                self.log_message("البحث بالطريقة التقليدية فشل، جارٍ البحث الذكي...")
                content_table = self.find_content_table_smart(tables, cursor)
            
            if not content_table:
                self.log_message("لم يتم العثور على جدول المحتوى حتى بالبحث الذكي", "ERROR")
                self.log_message("المحاولة الأخيرة: استخدام أكبر جدول كجدول محتوى...")
                content_table = self.find_largest_table(tables, cursor)
            
            if not content_table:
                self.log_message("فشل في العثور على أي جدول مناسب للمحتوى", "ERROR")
                return False
            
            self.log_message(f"تم اختيار جدول المحتوى: {content_table}")
            
            # استخراج البيانات
            content_data = self.extract_book_content(content_table)
            index_data = self.extract_book_index(index_table) if index_table else []
            
            if not content_data:
                self.log_message("لا يوجد محتوى للتحويل", "WARNING")
                return False
            
            # إدراج البيانات في MySQL
            author_name = book_info.get('Auth', 'مؤلف غير معروف')
            publisher_name = book_info.get('Publisher', 'ناشر غير معروف')
            
            author_id = self.insert_author(author_name)
            publisher_id = self.insert_publisher(publisher_name)
            book_id = self.insert_book(book_info, author_id, publisher_id)
            
            self.insert_pages_and_chapters(book_id, content_data, index_data)
            
            # إغلاق الاتصال بـ Access
            self.access_conn.close()
            
            self.log_message(f"تم تحويل الملف بنجاح: {os.path.basename(access_file_path)}")
            return True
            
        except Exception as e:
            self.log_message(f"خطأ في تحويل الملف: {str(e)}", "ERROR")
            return False
    
    def convert_file(self, access_file_path: str) -> bool:
        """
        تحويل ملف واحد
        
        Args:
            access_file_path: مسار ملف Access
            
        Returns:
            bool: نجح التحويل أم لا
        """
        try:
            self.log_message(f"INFO: بدء معالجة الملف: {os.path.basename(access_file_path)}")
            
            try:
                # الاتصال بـ MySQL
                self.log_message(f"INFO: محاولة الاتصال بـ MySQL...")
                
                if not self.connect_mysql():
                    self.log_message(f"ERROR: فشل في الاتصال بـ MySQL")
                    return False
                
                # تحويل الملف
                self.log_message(f"INFO: بدء عملية التحويل الفعلية...")
                success = self.convert_access_file(access_file_path)
                
                if success:
                    self.log_message(f"INFO: تم تحويل {os.path.basename(access_file_path)} بنجاح")
                    
                    # التحقق من أن البيانات تم حفظها فعلاً
                    try:
                        cursor = self.mysql_conn.cursor()
                        cursor.execute("SELECT COUNT(*) FROM books")
                        book_count = cursor.fetchone()[0]
                        self.log_message(f"INFO: عدد الكتب في قاعدة البيانات الآن: {book_count}")
                        
                        # حفظ التغييرات
                        self.mysql_conn.commit()
                        self.log_message(f"INFO: تم حفظ التغييرات في قاعدة البيانات")
                        
                    except Exception as e:
                        self.log_message(f"ERROR: خطأ في التحقق من البيانات: {str(e)}")
                else:
                    self.log_message(f"ERROR: فشل تحويل {os.path.basename(access_file_path)}")
                
                return success
                
            finally:
                if self.mysql_conn:
                    self.mysql_conn.close()
                    self.log_message(f"INFO: تم إغلاق اتصال MySQL")
                
        except Exception as e:
            self.log_message(f"ERROR: خطأ في تحويل الملف {os.path.basename(access_file_path)}: {str(e)}")
            return False

    def convert_multiple_files(self, access_files: List[str]) -> Dict[str, bool]:
        """تحويل عدة ملفات Access"""
        results = {}
        
        if not self.connect_mysql():
            return results
        
        try:
            # بدء المعاملة
            self.mysql_conn.start_transaction()
            
            for access_file in access_files:
                file_name = os.path.basename(access_file)
                self.log_message(f"معالجة الملف: {file_name}")
                
                success = self.convert_access_file(access_file)
                results[file_name] = success
                
                if success:
                    self.log_message(f"تم تحويل {file_name} بنجاح")
                else:
                    self.log_message(f"فشل في تحويل {file_name}", "ERROR")
            
            # تأكيد المعاملة
            self.mysql_conn.commit()
            self.log_message("تم حفظ جميع التغييرات في قاعدة البيانات")
            
        except Exception as e:
            # التراجع عن المعاملة في حالة الخطأ
            self.mysql_conn.rollback()
            self.log_message(f"تم التراجع عن التغييرات بسبب خطأ: {str(e)}", "ERROR")
        
        finally:
            if self.mysql_conn:
                self.mysql_conn.close()
        
        return results
    
    def save_log(self, log_file_path: str):
        """حفظ سجل العمليات في ملف"""
        try:
            with open(log_file_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(self.conversion_log))
            print(f"تم حفظ السجل في: {log_file_path}")
        except Exception as e:
            print(f"خطأ في حفظ السجل: {str(e)}")


class ShamelaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Shamela Access to MySQL Uploader")
        self.root.geometry("900x700")
        self.root.configure(bg='#f0f0f0')
        
        # قائمة الملفات المحددة
        self.selected_files = []
        
        # إعدادات قاعدة البيانات الافتراضية
        self.db_config = {
            'host': '145.223.98.97',
            'port': 3306,
            'database': 'bms',
            'user': 'bms',
            'password': 'bms2025'
        }
        
        # قائمة انتظار الرسائل
        self.message_queue = queue.Queue()
        
        # متغيرات حالة التحويل
        self.conversion_running = False
        self.cancel_conversion_flag = False
        self.cancel_requested = False
        
        # متغيرات الوقت والتقدم المتقدمة
        self.start_time = None
        self.all_log_messages = []
        
        # إحصائيات التحويل المتقدمة
        self.total_files = 0
        self.current_file_index = 0
        self.books_stats = []  # قائمة إحصائيات كل كتاب
        self.current_book_stats = None
        
        self.create_widgets()
        self.load_settings()
        # لا نبدأ check_message_queue هنا، سيبدأ عند بدء التحويل
    
    def create_widgets(self):
        # العنوان الرئيسي
        title_label = tk.Label(self.root, text="Upload Access to Database SQL", 
                              font=("Arial", 18, "bold"), 
                              bg='#f0f0f0', fg='#2c3e50')
        title_label.pack(pady=10)
        
        # إطار اختيار الملفات
        files_frame = tk.LabelFrame(self.root, text="اختيار ملفات الكتب (.accdb )", 
                                   font=("Arial", 12, "bold"), 
                                   bg='#f0f0f0', fg='#34495e')
        files_frame.pack(fill="x", padx=20, pady=10)
        
        # زر اختيار الملفات
        select_files_btn = tk.Button(files_frame, text="اختيار ملفات الكتب", 
                                    command=self.select_files,
                                    font=("Arial", 10, "bold"),
                                    bg='#3498db', fg='white',
                                    relief='flat', padx=20, pady=8)
        select_files_btn.pack(side="left", padx=10, pady=10)
        
        # زر مسح الملفات
        clear_files_btn = tk.Button(files_frame, text="مسح القائمة", 
                                   command=self.clear_files,
                                   font=("Arial", 10),
                                   bg='#e74c3c', fg='white',
                                   relief='flat', padx=20, pady=8)
        clear_files_btn.pack(side="left", padx=5, pady=10)
        
        # إطار قائمة الملفات مع أزرار إضافية
        files_list_frame = tk.Frame(files_frame, bg='#f0f0f0')
        files_list_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # قائمة الملفات المحددة
        self.files_listbox = tk.Listbox(files_list_frame, height=4, 
                                       font=("Arial", 9),
                                       bg='white', fg='#2c3e50',
                                       selectmode=tk.SINGLE)
        self.files_listbox.pack(side="left", fill="both", expand=True)
        
        # إطار أزرار إدارة الملفات
        files_buttons_frame = tk.Frame(files_list_frame, bg='#f0f0f0')
        files_buttons_frame.pack(side="right", fill="y", padx=(5, 0))
        
        # زر حذف ملف محدد
        delete_file_btn = tk.Button(files_buttons_frame, text="حذف المحدد", 
                                   command=self.delete_selected_file,
                                   font=("Arial", 8),
                                   bg='#e67e22', fg='white',
                                   relief='flat', padx=10, pady=3)
        delete_file_btn.pack(pady=(0, 2))
        
        # زر معاينة الملف
        preview_file_btn = tk.Button(files_buttons_frame, text="معاينة", 
                                    command=self.preview_selected_file,
                                    font=("Arial", 8),
                                    bg='#9b59b6', fg='white',
                                    relief='flat', padx=10, pady=3)
        preview_file_btn.pack(pady=2)
        
        # إطار إعدادات قاعدة البيانات
        db_frame = tk.LabelFrame(self.root, text="إعدادات قاعدة البيانات", 
                                font=("Arial", 12, "bold"),
                                bg='#f0f0f0', fg='#34495e')
        db_frame.pack(fill="x", padx=20, pady=10)
        
        # Grid لتنظيم الحقول
        db_inner_frame = tk.Frame(db_frame, bg='#f0f0f0')
        db_inner_frame.pack(fill="x", padx=10, pady=10)
        
        # حقول قاعدة البيانات
        tk.Label(db_inner_frame, text="الخادم:", font=("Arial", 10), 
                bg='#f0f0f0').grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.host_entry = tk.Entry(db_inner_frame, font=("Arial", 10), width=25)
        self.host_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(db_inner_frame, text="المنفذ:", font=("Arial", 10), 
                bg='#f0f0f0').grid(row=0, column=2, sticky="e", padx=5, pady=5)
        self.port_entry = tk.Entry(db_inner_frame, font=("Arial", 10), width=8)
        self.port_entry.grid(row=0, column=3, padx=5, pady=5)
        
        tk.Label(db_inner_frame, text="قاعدة البيانات:", font=("Arial", 10), 
                bg='#f0f0f0').grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.database_entry = tk.Entry(db_inner_frame, font=("Arial", 10), width=25)
        self.database_entry.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(db_inner_frame, text="اسم المستخدم:", font=("Arial", 10), 
                bg='#f0f0f0').grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.user_entry = tk.Entry(db_inner_frame, font=("Arial", 10), width=25)
        self.user_entry.grid(row=2, column=1, padx=5, pady=5)
        
        tk.Label(db_inner_frame, text="كلمة المرور:", font=("Arial", 10), 
                bg='#f0f0f0').grid(row=2, column=2, sticky="e", padx=5, pady=5)
        self.password_entry = tk.Entry(db_inner_frame, font=("Arial", 10), width=25, show="*")
        self.password_entry.grid(row=2, column=3, padx=5, pady=5)
        
        # ملاحظة عن كلمة المرور
        note_label = tk.Label(db_inner_frame, text="(اتركها فارغة إذا لم تكن مطلوبة)", 
                             font=("Arial", 8), bg='#f0f0f0', fg='#7f8c8d')
        note_label.grid(row=3, column=2, columnspan=2, sticky="w", padx=5)
        
        # أزرار الإعدادات
        db_buttons_frame = tk.Frame(db_frame, bg='#f0f0f0')
        db_buttons_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        test_db_btn = tk.Button(db_buttons_frame, text="اختبار الاتصال", 
                               command=self.test_connection,
                               font=("Arial", 10),
                               bg='#f39c12', fg='white',
                               relief='flat', padx=15, pady=5)
        test_db_btn.pack(side="left", padx=5)
        
        save_settings_btn = tk.Button(db_buttons_frame, text="حفظ الإعدادات", 
                                     command=self.save_settings,
                                     font=("Arial", 10),
                                     bg='#27ae60', fg='white',
                                     relief='flat', padx=15, pady=5)
        save_settings_btn.pack(side="left", padx=5)
        
        # إطار التحكم المتقدم
        control_frame = tk.Frame(self.root, bg='#f0f0f0')
        control_frame.pack(fill="x", padx=20, pady=10)
        
        # معلومات التقدم
        progress_info_frame = tk.Frame(control_frame, bg='#f0f0f0')
        progress_info_frame.pack(fill="x")
        
        # النص العلوي للحالة
        self.progress_var = tk.StringVar()
        self.progress_var.set("جاهز للبدء")
        progress_label = tk.Label(progress_info_frame, textvariable=self.progress_var,
                                 font=("Arial", 10), bg='#f0f0f0', fg='#7f8c8d')
        progress_label.pack(side="left")
        
        # معلومات التقدم (ملف حالي/إجمالي)
        self.progress_details_var = tk.StringVar()
        self.progress_details_var.set("")
        progress_details_label = tk.Label(progress_info_frame, textvariable=self.progress_details_var,
                                         font=("Arial", 9), bg='#f0f0f0', fg='#95a5a6')
        progress_details_label.pack(side="right")
        
        # شريط التقدم المحدد
        progress_frame = tk.Frame(control_frame, bg='#f0f0f0')
        progress_frame.pack(fill="x", pady=(5, 10))
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', maximum=100)
        self.progress_bar.pack(fill="x")
        
        # متغيرات التقدم
        self.total_files = 0
        self.current_file_index = 0
        
        # إطار أزرار التحكم
        control_buttons_frame = tk.Frame(control_frame, bg='#f0f0f0')
        control_buttons_frame.pack(pady=10)
        
        # زر البدء
        self.start_btn = tk.Button(control_buttons_frame, text="بدء التحويل", 
                                  command=self.start_conversion,
                                  font=("Arial", 12, "bold"),
                                  bg='#2ecc71', fg='white',
                                  relief='flat', padx=30, pady=10)
        self.start_btn.pack(side="left", padx=(0, 10))
        
        # زر الإلغاء/الإيقاف
        self.cancel_btn = tk.Button(control_buttons_frame, text="إيقاف", 
                                   command=self.cancel_conversion,
                                   font=("Arial", 11),
                                   bg='#e74c3c', fg='white',
                                   relief='flat', padx=20, pady=10,
                                   state="disabled")
        self.cancel_btn.pack(side="left", padx=5)
        
        # زر حفظ السجل
        self.save_log_btn = tk.Button(control_buttons_frame, text="حفظ السجل", 
                                     command=self.save_log,
                                     font=("Arial", 10),
                                     bg='#3498db', fg='white',
                                     relief='flat', padx=15, pady=10)
        self.save_log_btn.pack(side="left", padx=5)
        
        # زر تقرير الجلسة
        self.session_report_btn = tk.Button(control_buttons_frame, text="تقرير الجلسة", 
                                           command=self.show_session_report,
                                           font=("Arial", 10),
                                           bg='#9b59b6', fg='white',
                                           relief='flat', padx=15, pady=10)
        self.session_report_btn.pack(side="left", padx=5)
        
        # منطقة سجل الأحداث المتقدمة
        log_frame = tk.LabelFrame(self.root, text="سجل الأحداث", 
                                 font=("Arial", 12, "bold"),
                                 bg='#f0f0f0', fg='#34495e')
        log_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # إطار أدوات السجل
        log_tools_frame = tk.Frame(log_frame, bg='#f0f0f0')
        log_tools_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        # أزرار تصفية الرسائل
        tk.Label(log_tools_frame, text="تصفية:", font=("Arial", 9), 
                bg='#f0f0f0').pack(side="left", padx=(0, 5))
        
        self.filter_var = tk.StringVar(value="الكل")
        filter_options = ["الكل", "معلومات", "نجاح", "خطأ", "تحذير"]
        self.filter_combo = ttk.Combobox(log_tools_frame, textvariable=self.filter_var,
                                        values=filter_options, state="readonly", width=10)
        self.filter_combo.pack(side="left", padx=5)
        self.filter_combo.bind("<<ComboboxSelected>>", self.filter_log_messages)
        
        # زر مسح السجل
        clear_log_btn = tk.Button(log_tools_frame, text="مسح السجل", 
                                 command=self.clear_log,
                                 font=("Arial", 8),
                                 bg='#95a5a6', fg='white',
                                 relief='flat', padx=10, pady=3)
        clear_log_btn.pack(side="right", padx=5)
        
        # إطار السجل مع scroll
        log_display_frame = tk.Frame(log_frame, bg='#f0f0f0')
        log_display_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.log_text = tk.Text(log_display_frame, height=15, 
                               font=("Consolas", 9),
                               bg='#2c3e50', fg='#ecf0f1',
                               insertbackground='#ecf0f1',
                               wrap=tk.WORD)
        
        # إعداد الألوان للرسائل المختلفة
        self.log_text.tag_configure("INFO", foreground="#74b9ff")      # أزرق فاتح
        self.log_text.tag_configure("SUCCESS", foreground="#00b894")   # أخضر
        self.log_text.tag_configure("ERROR", foreground="#e17055")     # أحمر
        self.log_text.tag_configure("WARNING", foreground="#fdcb6e")   # أصفر
        self.log_text.tag_configure("PROGRESS", foreground="#a29bfe")  # بنفسجي
        self.log_text.tag_configure("timestamp", foreground="#636e72") # رمادي
        
        # إضافة scrollbar للسجل
        log_scrollbar = ttk.Scrollbar(log_display_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scrollbar.pack(side="right", fill="y")
        
        # شريط الحالة المتقدم
        status_frame = tk.Frame(self.root, bg='#34495e', height=35)
        status_frame.pack(fill="x", side="bottom")
        status_frame.pack_propagate(False)
        
        # الحالة الرئيسية
        self.status_var = tk.StringVar()
        self.status_var.set("جاهز")
        status_label = tk.Label(status_frame, textvariable=self.status_var,
                               font=("Arial", 9), bg='#34495e', fg='white')
        status_label.pack(side="left", padx=10, pady=8)
        
        # معلومات إضافية
        self.status_details_var = tk.StringVar()
        self.status_details_var.set("")
        status_details_label = tk.Label(status_frame, textvariable=self.status_details_var,
                                       font=("Arial", 8), bg='#34495e', fg='#bdc3c7')
        status_details_label.pack(side="left", padx=(20, 10))
        
        # وقت العملية
        self.time_var = tk.StringVar()
        self.time_var.set("")
        time_label = tk.Label(status_frame, textvariable=self.time_var,
                             font=("Arial", 8), bg='#34495e', fg='#95a5a6')
        time_label.pack(side="right", padx=10, pady=8)
    
    def select_files(self):
        files = filedialog.askopenfilenames(
            title="اختيار ملفات الكتب",
            filetypes=[
                ("Access Database", "*.accdb"),
                ("كل الملفات", "*.*")
            ]
        )
        
        for file in files:
            if file not in self.selected_files:
                self.selected_files.append(file)
                
                file_display = os.path.basename(file)
                self.files_listbox.insert(tk.END, file_display)
        
        self.log_message(f"تم اختيار {len(files)} ملف جديد")
        self.update_status(f"تم تحديد {len(self.selected_files)} ملف")
    
    def delete_selected_file(self):
        """حذف الملف المحدد من القائمة"""
        try:
            selection = self.files_listbox.curselection()
            if not selection:
                messagebox.showwarning("تحذير", "يرجى تحديد ملف للحذف")
                return
            
            index = selection[0]
            file_name = self.files_listbox.get(index)
            
            if messagebox.askyesno("تأكيد الحذف", f"هل تريد حذف الملف:\n{file_name}"):
                # حذف من القائمة المرئية والقائمة الداخلية
                self.files_listbox.delete(index)
                del self.selected_files[index]
                
                self.log_message(f"تم حذف الملف: {file_name}", "INFO")
                self.update_status(f"تم تحديد {len(self.selected_files)} ملف")
                
        except Exception as e:
            self.log_message(f"خطأ في حذف الملف: {str(e)}", "ERROR")
    
    def preview_selected_file(self):
        """معاينة معلومات الملف المحدد"""
        try:
            selection = self.files_listbox.curselection()
            if not selection:
                messagebox.showwarning("تحذير", "يرجى تحديد ملف للمعاينة")
                return
            
            index = selection[0]
            file_path = self.selected_files[index]
            
            # جمع معلومات الملف
            file_info = []
            file_info.append(f"اسم الملف: {os.path.basename(file_path)}")
            file_info.append(f"المسار: {file_path}")
            
            if os.path.exists(file_path):
                stat_info = os.stat(file_path)
                file_size = stat_info.st_size
                
                # تحويل الحجم لوحدة مناسبة
                if file_size < 1024:
                    size_str = f"{file_size} بايت"
                elif file_size < 1024*1024:
                    size_str = f"{file_size/1024:.1f} كيلو بايت"
                else:
                    size_str = f"{file_size/(1024*1024):.1f} ميجا بايت"
                
                file_info.append(f"الحجم: {size_str}")
                
                # تاريخ التعديل
                import time
                mod_time = time.ctime(stat_info.st_mtime)
                file_info.append(f"تاريخ التعديل: {mod_time}")
                
                # نوع الملف
                if file_path.lower().endswith('.bok'):
                    file_info.append("النوع: ملف BOK (مضغوط)")
                elif file_path.lower().endswith('.accdb'):
                    file_info.append("النوع: قاعدة بيانات Access")
            else:
                file_info.append("⚠️ تحذير: الملف غير موجود!")
            
            messagebox.showinfo("معلومات الملف", "\n".join(file_info))
            
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في معاينة الملف:\n{str(e)}")
    
    def cancel_conversion(self):
        """إلغاء عملية التحويل"""
        if not self.conversion_running:
            return
        
        if messagebox.askyesno("تأكيد الإلغاء", "هل تريد إيقاف عملية التحويل؟"):
            self.cancel_requested = True
            self.log_message("تم طلب إيقاف العملية...", "WARNING")
            self.update_status("جاري الإيقاف...")
    
    def save_log(self):
        """حفظ سجل الأحداث في ملف"""
        try:
            if not hasattr(self, 'all_log_messages') or not self.all_log_messages:
                messagebox.showwarning("تحذير", "لا يوجد محتوى في السجل للحفظ")
                return
            
            # تحديد اسم الملف الافتراضي
            try:
                default_filename = f"سجل_الأحداث_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            except:
                default_filename = "سجل_الأحداث.txt"
            
            # اختيار مكان الحفظ
            try:
                file_path = filedialog.asksaveasfilename(
                    title="حفظ سجل الأحداث",
                    defaultextension=".txt",
                    filetypes=[("ملفات نصية", "*.txt"), ("جميع الملفات", "*.*")],
                    initialfile=default_filename
                )
            except Exception as e:
                messagebox.showerror("خطأ", f"خطأ في فتح مربع الحوار:\n{str(e)}")
                return
            
            if not file_path:
                return  # المستخدم ألغى العملية
            
            # التأكد من أن الملف ينتهي بـ .txt
            if not file_path.lower().endswith('.txt'):
                file_path += '.txt'
            
            # حفظ السجل في الملف
            try:
                with open(file_path, 'w', encoding='utf-8', newline='') as f:
                    f.write("=== سجل أحداث محول كتب الشاملة ===\n")
                    f.write(f"تاريخ الإنشاء: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("="*50 + "\n\n")
                    
                    for msg_data in self.all_log_messages:
                        f.write(f"{msg_data['full_message']}\n")
                
                # التحقق من نجاح الحفظ
                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    file_size = os.path.getsize(file_path)
                    success_msg = f"تم حفظ السجل بنجاح في:\n{file_path}\n\nحجم الملف: {file_size} بايت"
                    messagebox.showinfo("تم الحفظ بنجاح", success_msg)
                    self.log_message(f"💾 تم حفظ السجل: {os.path.basename(file_path)}", "SUCCESS")
                else:
                    messagebox.showerror("خطأ", "فشل في إنشاء الملف أو الملف فارغ")
                
            except PermissionError:
                messagebox.showerror("خطأ في الصلاحيات", 
                    f"ليس لديك صلاحية للكتابة في هذا المكان:\n{file_path}\n\nحاول اختيار مكان آخر أو تشغيل البرنامج كمسؤول")
            except Exception as e:
                messagebox.showerror("خطأ في الحفظ", f"فشل في حفظ السجل:\n{str(e)}")
                
        except Exception as e:
            messagebox.showerror("خطأ عام", f"خطأ غير متوقع في حفظ السجل:\n{str(e)}")
    
    def filter_log_messages(self, event=None):
        """تصفية رسائل السجل حسب النوع"""
        try:
            filter_type = self.filter_var.get()
            
            # مسح السجل الحالي
            self.log_text.delete(1.0, tk.END)
            
            # إعادة عرض الرسائل المفلترة
            for msg_data in self.all_log_messages:
                if filter_type == "الكل" or msg_data['type'] == filter_type:
                    self.display_log_message(msg_data)
            
            # التمرير للأسفل
            self.log_text.see(tk.END)
            
        except Exception as e:
            print(f"خطأ في التصفية: {e}")
    
    def show_session_report(self):
        """عرض تقرير مفصل لجلسة التحويل"""
        if not self.books_stats:
            messagebox.showinfo("تقرير الجلسة", "لا توجد بيانات جلسة متاحة")
            return
        
        # إنشاء نافذة التقرير
        report_window = tk.Toplevel(self.root)
        report_window.title("تقرير جلسة التحويل")
        report_window.geometry("800x600")
        report_window.configure(bg='#f0f0f0')
        
        # عنوان التقرير
        title_label = tk.Label(report_window, text="📊 تقرير جلسة التحويل", 
                              font=("Arial", 16, "bold"), 
                              bg='#f0f0f0', fg='#2c3e50')
        title_label.pack(pady=10)
        
        # إطار التقرير مع scroll
        report_frame = tk.Frame(report_window, bg='#f0f0f0')
        report_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        report_text = scrolledtext.ScrolledText(report_frame, 
                                               font=("Consolas", 10),
                                               bg='white', fg='#2c3e50',
                                               wrap=tk.WORD)
        report_text.pack(fill="both", expand=True)
        
        # إعداد الألوان
        report_text.tag_configure("header", foreground="#2c3e50", font=("Arial", 12, "bold"))
        report_text.tag_configure("success", foreground="#27ae60")
        report_text.tag_configure("error", foreground="#e74c3c") 
        report_text.tag_configure("info", foreground="#3498db")
        
        # بناء محتوى التقرير
        report_content = self.generate_session_report()
        
        # إدراج المحتوى مع التنسيق
        lines = report_content.split('\n')
        for line in lines:
            if line.startswith('=') or 'ملخص' in line or 'تقرير' in line:
                report_text.insert(tk.END, line + '\n', "header")
            elif '✅' in line or 'نجح' in line:
                report_text.insert(tk.END, line + '\n', "success")
            elif '❌' in line or 'فشل' in line:
                report_text.insert(tk.END, line + '\n', "error")
            else:
                report_text.insert(tk.END, line + '\n', "info")
        
        report_text.configure(state="disabled")
        
        # أزرار التحكم
        buttons_frame = tk.Frame(report_window, bg='#f0f0f0')
        buttons_frame.pack(pady=10)
        
        # زر حفظ التقرير
        save_report_btn = tk.Button(buttons_frame, text="حفظ التقرير", 
                                   command=self.save_session_report,
                                   font=("Arial", 10),
                                   bg='#27ae60', fg='white',
                                   relief='flat', padx=20, pady=8)
        save_report_btn.pack(side="left", padx=10)
        
        # زر إغلاق
        close_btn = tk.Button(buttons_frame, text="إغلاق", 
                             command=report_window.destroy,
                             font=("Arial", 10),
                             bg='#95a5a6', fg='white',
                             relief='flat', padx=20, pady=8)
        close_btn.pack(side="left", padx=10)
    
    def generate_session_report(self):
        """إنشاء محتوى تقرير الجلسة"""
        report_lines = []
        
        # عنوان التقرير
        report_lines.append("="*60)
        report_lines.append("📊 تقرير جلسة التحويل المفصل")
        report_lines.append("="*60)
        report_lines.append(f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # الإحصائيات العامة
        successful_books = sum(1 for book in self.books_stats if book.get('success', False))
        failed_books = len(self.books_stats) - successful_books
        total_volumes = sum(book.get('volumes', 0) for book in self.books_stats)
        total_chapters = sum(book.get('chapters', 0) for book in self.books_stats)
        total_pages = sum(book.get('pages', 0) for book in self.books_stats)
        
        report_lines.append("📋 الإحصائيات العامة:")
        report_lines.append(f"   📚 إجمالي الكتب: {len(self.books_stats)}")
        report_lines.append(f"   ✅ نجح التحويل: {successful_books}")
        report_lines.append(f"   ❌ فشل التحويل: {failed_books}")
        report_lines.append(f"   📁 إجمالي المجلدات: {total_volumes}")
        report_lines.append(f"   📑 إجمالي الفصول: {total_chapters}")
        report_lines.append(f"   📄 إجمالي الصفحات: {total_pages}")
        
        if self.start_time:
            total_time = datetime.now() - self.start_time
            report_lines.append(f"   ⏱️ إجمالي الوقت: {str(total_time).split('.')[0]}")
        
        report_lines.append("")
        
        # معدل الأداء
        if successful_books > 0 and self.start_time:
            total_seconds = (datetime.now() - self.start_time).total_seconds()
            if total_seconds > 0:
                books_per_minute = (successful_books / total_seconds) * 60
                pages_per_minute = (total_pages / total_seconds) * 60
                report_lines.append("📊 معدل الأداء:")
                report_lines.append(f"   📚 {books_per_minute:.1f} كتاب/دقيقة")
                report_lines.append(f"   📄 {pages_per_minute:.1f} صفحة/دقيقة")
                report_lines.append("")
        
        # تفاصيل كل كتاب
        report_lines.append("📋 تفاصيل الكتب:")
        report_lines.append("-" * 60)
        
        for i, book in enumerate(self.books_stats, 1):
            status_icon = "✅" if book.get('success', False) else "❌"
            report_lines.append(f"{i}. {status_icon} {book['name']}")
            report_lines.append(f"   📊 الحالة: {book.get('status', 'غير محدد')}")
            report_lines.append(f"   📁 المجلدات: {book.get('volumes', 0)}")
            report_lines.append(f"   📑 الفصول: {book.get('chapters', 0)}")
            report_lines.append(f"   📄 الصفحات: {book.get('pages', 0)}")
            
            if 'start_time' in book and 'end_time' in book:
                duration = book['end_time'] - book['start_time']
                report_lines.append(f"   ⏱️ المدة: {str(duration).split('.')[0]}")
            
            report_lines.append("")
        
        report_lines.append("="*60)
        report_lines.append("تم إنشاء التقرير بواسطة محول كتب الشاملة")
        report_lines.append("="*60)
        
        return '\n'.join(report_lines)
    
    def save_session_report(self):
        """حفظ تقرير الجلسة في ملف"""
        try:
            # التحقق من وجود بيانات للتقرير
            if not hasattr(self, 'books_stats') or not self.books_stats:
                messagebox.showwarning("تحذير", "لا توجد بيانات جلسة متاحة للحفظ")
                return
            
            # إنشاء محتوى التقرير
            try:
                report_content = self.generate_session_report()
                if not report_content or len(report_content.strip()) == 0:
                    messagebox.showerror("خطأ", "فشل في إنشاء محتوى التقرير")
                    return
            except Exception as e:
                messagebox.showerror("خطأ", f"خطأ في إنشاء التقرير:\n{str(e)}")
                return
            
            # تحديد اسم الملف الافتراضي
            try:
                default_filename = f"تقرير_جلسة_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            except:
                default_filename = "تقرير_جلسة.txt"
            
            # اختيار مكان الحفظ
            try:
                file_path = filedialog.asksaveasfilename(
                    title="حفظ تقرير الجلسة",
                    defaultextension=".txt",
                    filetypes=[
                        ("ملفات نصية", "*.txt"), 
                        ("جميع الملفات", "*.*")
                    ],
                    initialfile=default_filename
                )
            except Exception as e:
                messagebox.showerror("خطأ", f"خطأ في فتح مربع الحوار:\n{str(e)}")
                return
            
            if not file_path:
                # المستخدم ألغى العملية
                return
            
            # التأكد من أن الملف ينتهي بـ .txt
            if not file_path.lower().endswith('.txt'):
                file_path += '.txt'
            
            # حفظ التقرير في الملف
            try:
                with open(file_path, 'w', encoding='utf-8', newline='') as f:
                    f.write(report_content)
                
                # التحقق من أن الملف تم إنشاؤه بنجاح
                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    success_msg = f"تم حفظ تقرير الجلسة بنجاح في:\n{file_path}"
                    messagebox.showinfo("تم الحفظ بنجاح", success_msg)
                    
                    # تسجيل النجاح في السجل
                    if hasattr(self, 'log_message'):
                        self.log_message(f"💾 تم حفظ تقرير الجلسة: {os.path.basename(file_path)}", "SUCCESS")
                else:
                    messagebox.showerror("خطأ", "فشل في إنشاء الملف أو الملف فارغ")
                    
            except PermissionError:
                messagebox.showerror("خطأ في الصلاحيات", 
                    f"ليس لديك صلاحية للكتابة في هذا المكان:\n{file_path}\n\nحاول اختيار مكان آخر أو تشغيل البرنامج كمسؤول")
            except Exception as e:
                messagebox.showerror("خطأ في الحفظ", f"فشل في حفظ الملف:\n{str(e)}")
                
        except Exception as e:
            # خطأ عام غير متوقع
            error_msg = f"خطأ غير متوقع في حفظ التقرير:\n{str(e)}"
            messagebox.showerror("خطأ عام", error_msg)
            
            # تسجيل الخطأ في السجل إذا أمكن
            try:
                if hasattr(self, 'log_message'):
                    self.log_message(f"❌ خطأ في حفظ التقرير: {str(e)}", "ERROR")
            except:
                pass

    def clear_log(self):
        """مسح سجل الأحداث"""
        if messagebox.askyesno("تأكيد المسح", "هل تريد مسح سجل الأحداث؟"):
            self.log_text.delete(1.0, tk.END)
            self.all_log_messages.clear()
            self.log_message("تم مسح سجل الأحداث", "INFO")
    
    def clear_files(self):
        self.selected_files.clear()
        self.files_listbox.delete(0, tk.END)
        self.log_message("تم مسح قائمة الملفات")
        self.update_status("جاهز")
    
    def test_connection(self):
        self.update_db_config()
        
        try:
            # إعداد معاملات الاتصال
            connection_params = self.db_config.copy()
            
            # إزالة كلمة المرور إذا كانت فارغة
            if not connection_params.get('password'):
                connection_params.pop('password', None)
            
            connection = pymysql.connect(**connection_params)
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            connection.close()
            
            messagebox.showinfo("نجح الاتصال", "تم الاتصال بقاعدة البيانات بنجاح!")
            self.log_message("✅ تم اختبار الاتصال بقاعدة البيانات بنجاح")
            
        except Exception as e:
            messagebox.showerror("فشل الاتصال", f"فشل في الاتصال بقاعدة البيانات:\n{str(e)}")
            self.log_message(f"❌ فشل اختبار الاتصال: {str(e)}")
    
    def save_settings(self):
        self.update_db_config()
        
        try:
            with open("db_settings.json", "w", encoding="utf-8") as f:
                json.dump(self.db_config, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo("تم الحفظ", "تم حفظ إعدادات قاعدة البيانات بنجاح!")
            self.log_message("💾 تم حفظ إعدادات قاعدة البيانات")
            
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في حفظ الإعدادات:\n{str(e)}")
            self.log_message(f"❌ فشل حفظ الإعدادات: {str(e)}")
    
    def load_settings(self):
        try:
            if os.path.exists("db_settings.json"):
                with open("db_settings.json", "r", encoding="utf-8") as f:
                    self.db_config = json.load(f)
                self.log_message("📂 تم تحميل إعدادات قاعدة البيانات")
        except Exception as e:
            self.log_message(f"⚠️ فشل تحميل الإعدادات: {str(e)}")
        
        # تحديث الحقول
        self.host_entry.delete(0, tk.END)
        self.host_entry.insert(0, self.db_config.get('host', ''))
        
        self.port_entry.delete(0, tk.END)
        self.port_entry.insert(0, str(self.db_config.get('port', 3306)))
        
        self.database_entry.delete(0, tk.END)
        self.database_entry.insert(0, self.db_config.get('database', ''))
        
        self.user_entry.delete(0, tk.END)
        self.user_entry.insert(0, self.db_config.get('user', ''))
        
        self.password_entry.delete(0, tk.END)
        self.password_entry.insert(0, self.db_config.get('password', ''))
    
    def update_db_config(self):
        # التحقق من المنفذ وتعيين القيمة الافتراضية
        port_text = self.port_entry.get().strip()
        try:
            port = int(port_text) if port_text else 3306
        except ValueError:
            port = 3306
            
        self.db_config = {
            'host': self.host_entry.get().strip(),
            'port': port,
            'database': self.database_entry.get().strip(),
            'user': self.user_entry.get().strip(),
            'password': self.password_entry.get()  # السماح بكلمة مرور فارغة
        }
    
    def start_conversion(self):
        """بدء عملية التحويل مع إدارة متطورة للحالة"""
        # فحص الملفات المحددة
        if not self.selected_files:
            messagebox.showwarning("تحذير", "يرجى اختيار ملفات الكتب أولاً")
            return
        
        # فحص ما إذا كان التحويل قيد التشغيل
        if self.conversion_running:
            messagebox.showinfo("معلومات", "عملية التحويل قيد التنفيذ بالفعل")
            return
        
        # تحديث وفحص إعدادات قاعدة البيانات
        self.update_db_config()
        required_fields = ['host', 'database', 'user']
        if not all(self.db_config.get(field, '').strip() for field in required_fields):
            messagebox.showwarning("تحذير", "يرجى ملء الحقول المطلوبة: الخادم، قاعدة البيانات، اسم المستخدم")
            return
        
        # اختبار اتصال قاعدة البيانات
        if not self.test_database_connection():
            response = messagebox.askyesno(
                "تحذير", 
                "فشل الاتصال بقاعدة البيانات. هل تريد المتابعة؟"
            )
            if not response:
                return
        
        # إعداد حالة التحويل
        self.conversion_running = True
        self.cancel_conversion_flag = False
        self.start_time = datetime.now()
        
        # تحديث واجهة المستخدم
        self.start_btn.configure(text="جاري التحويل...", state="disabled")
        self.cancel_btn.configure(state="normal")
        self.progress_bar.stop()  # إيقاف الحركة اللامحدودة
        self.progress_bar.configure(mode='determinate')
        self.progress_bar['value'] = 0
        
        # تفريغ السجل وإعداد التقدم
        self.clear_log()
        self.status_var.set("🔄 بدء عملية التحويل...")
        self.progress_var.set("جاري الإعداد...")
        self.progress_details_var.set("0/0 (0%)")
        
        # بدء خيط التحويل
        conversion_thread = threading.Thread(target=self.run_conversion)
        conversion_thread.daemon = True
        conversion_thread.start()
        
        # بدء مراقبة الرسائل
        self.check_message_queue()
        
        self.log_message("🔄 بدء عملية تحويل الملفات المحددة", "PROGRESS")
    
    def run_conversion(self):
        try:
            # إعداد الإحصائيات
            self.total_files = len(self.selected_files)
            self.current_file_index = 0
            self.books_stats = []
            
            self.message_queue.put(('progress', f"إعداد التحويل للـ {self.total_files} ملف..."))
            self.message_queue.put(('update_progress', (0, self.total_files, "بدء التحويل...")))
            self.message_queue.put(('info', f"📊 إعدادات قاعدة البيانات: {self.db_config['host']}:{self.db_config['port']}"))
            
            # The rest of the ACCDB file processing logic will go here.
            # For now, we assume all files are ACCDB.
            regular_files = self.selected_files

            if not regular_files:
                self.message_queue.put(('error', "❌ No processable files found."))
                return
            
            # إنشاء دالة callback لاستقبال رسائل المحول مع تتبع التقدم
            def message_callback(message, level):
                if level == "ERROR":
                    self.message_queue.put(('error', f"❌ {message}"))
                elif level == "WARNING":
                    self.message_queue.put(('info', f"⚠️ {message}"))
                else:
                    # تحليل الرسائل لاستخراج الإحصائيات
                    self.parse_conversion_message(message)
                    self.message_queue.put(('info', f"ℹ️ {message}"))
            
            converter = ShamelaConverter(self.db_config, message_callback)
            
            # اختبار الاتصال أولاً
            self.message_queue.put(('progress', f"اختبار الاتصال بقاعدة البيانات..."))
            if not converter.connect_mysql():
                self.message_queue.put(('error', "❌ فشل في الاتصال بقاعدة البيانات"))
                return
            
            self.message_queue.put(('success', "✅ تم الاتصال بقاعدة البيانات بنجاح"))
            
            successful_conversions = 0
            
            for i, file_path in enumerate(regular_files, 1):
                self.current_file_index = i
                book_name = os.path.basename(file_path)
                
                # إعداد إحصائيات الكتاب الحالي
                self.current_book_stats = {
                    'name': book_name,
                    'file_path': file_path,
                    'start_time': datetime.now(),
                    'volumes': 0,
                    'chapters': 0,
                    'pages': 0,
                    'status': 'جاري المعالجة',
                    'success': False
                }
                
                # تحديث التقدم
                progress_msg = f"📚 الكتاب {i}/{self.total_files}: {book_name}"
                self.message_queue.put(('progress', progress_msg))
                self.message_queue.put(('update_progress', (i-1, self.total_files, progress_msg)))
                self.message_queue.put(('info', f"🔄 بدء معالجة: {book_name}"))
                
                try:
                    result = converter.convert_file(file_path)
                    
                    if result:
                        successful_conversions += 1
                        self.current_book_stats['success'] = True
                        self.current_book_stats['status'] = 'مكتمل بنجاح'
                        self.current_book_stats['end_time'] = datetime.now()
                        
                        # تحديث التقدم لإظهار الكتاب مكتمل
                        progress_msg = f"✅ اكتمل {i}/{self.total_files}: {book_name}"
                        self.message_queue.put(('update_progress', (i, self.total_files, progress_msg)))
                        self.message_queue.put(('success', f"✅ تم تحويل {book_name} بنجاح"))
                        
                        # إضافة ملخص الكتاب
                        self.add_book_summary()
                        
                    else:
                        self.current_book_stats['success'] = False
                        self.current_book_stats['status'] = 'فشل'
                        self.current_book_stats['end_time'] = datetime.now()
                        self.message_queue.put(('error', f"❌ فشل تحويل {book_name}"))
                        
                except Exception as e:
                    self.current_book_stats['success'] = False
                    self.current_book_stats['status'] = f'خطأ: {str(e)[:30]}'
                    self.current_book_stats['end_time'] = datetime.now()
                    self.message_queue.put(('error', f"❌ خطأ في تحويل {book_name}: {str(e)}"))
                
                # حفظ إحصائيات الكتاب
                self.books_stats.append(self.current_book_stats.copy())
            # التحقق من النتائج النهائية
            self.message_queue.put(('progress', f"التحقق من النتائج في قاعدة البيانات..."))
            
            try:
                # فحص عدد الكتب المضافة
                if converter.mysql_conn:
                    cursor = converter.mysql_conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM books")
                    book_count = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM pages")
                    page_count = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM chapters")
                    chapter_count = cursor.fetchone()[0]
                    
                    self.message_queue.put(('info', f"📊 النتائج النهائية:"))
                    self.message_queue.put(('info', f"   📚 عدد الكتب: {book_count}"))
                    self.message_queue.put(('info', f"   📄 عدد الصفحات: {page_count}"))
                    self.message_queue.put(('info', f"   📑 عدد الفصول: {chapter_count}"))
                    
                    if book_count == 0:
                        self.message_queue.put(('error', "⚠️ تحذير: لم يتم إضافة أي كتب إلى قاعدة البيانات!"))
                    
            except Exception as e:
                self.message_queue.put(('error', f"❌ خطأ في التحقق من النتائج: {str(e)}"))
            
            # رسالة الإنهاء مع الملخص الشامل
            self.message_queue.put(('finish', f"تم الانتهاء! نجح تحويل {successful_conversions}/{self.total_files} كتاب"))
            self.message_queue.put(('update_progress', (self.total_files, self.total_files, "اكتمل التحويل")))
            
            # إضافة ملخص شامل للجلسة
            self.add_session_summary(successful_conversions)
            
        except Exception as e:
            self.message_queue.put(('error', f"خطأ عام في عملية التحويل: {str(e)}"))
        
        finally:
            self.message_queue.put(('done', None))
    
    def parse_conversion_message(self, message):
        """تحليل رسائل التحويل لاستخراج الإحصائيات"""
        if not self.current_book_stats:
            return
            
        try:
            # استخراج إحصائيات المجلدات
            if "تم إنشاء المجلد" in message:
                self.current_book_stats['volumes'] += 1
            elif "تم إدراج" in message and "فصل" in message:
                # استخراج عدد الفصول
                import re
                match = re.search(r'تم إدراج (\d+) فصل', message)
                if match:
                    self.current_book_stats['chapters'] = int(match.group(1))
            elif "تم إدراج" in message and "صفحة" in message and "فصل" in message:
                # استخراج عدد الصفحات والفصول معاً
                import re
                # البحث عن النمط: "تم إدراج X صفحة و Y فصل"
                match = re.search(r'تم إدراج (\d+) صفحة و (\d+) فصل', message)
                if match:
                    self.current_book_stats['pages'] = int(match.group(1))
                    self.current_book_stats['chapters'] = int(match.group(2))
            elif "إجمالي الصفحات:" in message:
                # استخراج من رسائل الإحصائيات
                import re
                match = re.search(r'إجمالي الصفحات: (\d+)', message)
                if match:
                    self.current_book_stats['pages'] = int(match.group(1))
            elif "إجمالي الفصول:" in message:
                # استخراج من رسائل الإحصائيات
                import re
                match = re.search(r'إجمالي الفصول: (\d+)', message)
                if match:
                    self.current_book_stats['chapters'] = int(match.group(1))
            elif "تم تحديث معلومات الكتاب:" in message:
                # استخراج عدد الصفحات النهائي
                import re
                match = re.search(r'تم تحديث معلومات الكتاب: (\d+) صفحة', message)
                if match:
                    self.current_book_stats['pages'] = int(match.group(1))
        except Exception as e:
            print(f"خطأ في تحليل الرسالة: {e}")
            pass
    
    def add_book_summary(self):
        """إضافة ملخص للكتاب المكتمل"""
        if not self.current_book_stats:
            return
            
        stats = self.current_book_stats
        duration = ""
        if 'end_time' in stats and 'start_time' in stats:
            duration_delta = stats['end_time'] - stats['start_time']
            duration = str(duration_delta).split('.')[0]
        
        summary_lines = [
            f"📋 ملخص الكتاب: {stats['name']}",
            f"   📁 المجلدات: {stats['volumes']}",
            f"   📑 الفصول: {stats['chapters']}",
            f"   📄 الصفحات: {stats['pages']}",
            f"   ⏱️ المدة: {duration}",
            f"   ✅ الحالة: {stats['status']}"
        ]
        
        for line in summary_lines:
            self.message_queue.put(('success', line))
    
    def add_session_summary(self, successful_conversions):
        """إضافة ملخص شامل للجلسة"""
        self.message_queue.put(('info', "\n" + "="*60))
        self.message_queue.put(('info', "📊 ملخص جلسة التحويل الشامل"))
        self.message_queue.put(('info', "="*60))
        
        # إحصائيات عامة
        total_volumes = sum(book.get('volumes', 0) for book in self.books_stats)
        total_chapters = sum(book.get('chapters', 0) for book in self.books_stats)
        total_pages = sum(book.get('pages', 0) for book in self.books_stats)
        failed_books = self.total_files - successful_conversions
        
        self.message_queue.put(('info', f"📚 إجمالي الكتب المعالجة: {self.total_files}"))
        self.message_queue.put(('success', f"✅ نجح التحويل: {successful_conversions}"))
        if failed_books > 0:
            self.message_queue.put(('error', f"❌ فشل التحويل: {failed_books}"))
        
        self.message_queue.put(('info', f"📁 إجمالي المجلدات المنشأة: {total_volumes}"))
        self.message_queue.put(('info', f"📑 إجمالي الفصول المدرجة: {total_chapters}"))
        self.message_queue.put(('info', f"📄 إجمالي الصفحات المدرجة: {total_pages}"))
        
        # وقت الجلسة الإجمالي
        if self.start_time:
            total_session_time = datetime.now() - self.start_time
            total_session_str = str(total_session_time).split('.')[0]
            self.message_queue.put(('info', f"⏱️ إجمالي وقت الجلسة: {total_session_str}"))
        
        # تفاصيل كل كتاب
        self.message_queue.put(('info', "\n📋 تفاصيل الكتب:"))
        for i, book in enumerate(self.books_stats, 1):
            status_icon = "✅" if book.get('success', False) else "❌"
            self.message_queue.put(('info', f"{i}. {status_icon} {book['name']}"))
            self.message_queue.put(('info', f"   📁 {book.get('volumes', 0)} مجلد | 📑 {book.get('chapters', 0)} فصل | 📄 {book.get('pages', 0)} صفحة"))
            self.message_queue.put(('info', f"   📊 الحالة: {book.get('status', 'غير محدد')}"))
        
        self.message_queue.put(('info', "="*60))

    def check_message_queue(self):
        """فحص ومعالجة رسائل التحويل مع دعم التقدم المحدد المتقدم"""
        try:
            messages_processed = 0
            while messages_processed < 10:  # معالجة حتى 10 رسائل في المرة الواحدة
                message_type, message = self.message_queue.get_nowait()
                messages_processed += 1
                
                if message_type == 'progress':
                    self.progress_var.set(message)
                    self.update_status(message)
                    self.log_message(message, "PROGRESS")
                elif message_type == 'update_progress':
                    # رسالة تحديث التقدم: (current, total, message)
                    current, total, msg = message
                    self.update_progress(current, total, msg)
                elif message_type == 'success':
                    self.log_message(message, "SUCCESS")
                elif message_type == 'info':
                    self.log_message(message, "INFO")
                elif message_type == 'error':
                    self.log_message(message, "ERROR")
                elif message_type == 'warning':
                    self.log_message(message, "WARNING")
                elif message_type == 'finish':
                    self.log_message("\n" + "="*50)
                    self.log_message(message, "SUCCESS")
                    self.log_message("="*50)
                    self.update_status(message)
                    # تحديث التقدم إلى 100%
                    self.progress_bar['value'] = 100
                    self.progress_details_var.set("مكتمل (100%)")
                elif message_type == 'done':
                    self.conversion_running = False
                    self.start_btn.configure(text="بدء التحويل", state="normal")
                    self.cancel_btn.configure(state="disabled")
                    self.progress_bar.stop()
                    self.progress_var.set("تم الانتهاء من التحويل")
                    
                    # حساب الوقت الإجمالي
                    if self.start_time:
                        total_time = datetime.now() - self.start_time
                        total_time_str = str(total_time).split('.')[0]
                        self.time_var.set(f"مكتمل في: {total_time_str}")
                        self.log_message(f"⏱️ إجمالي وقت التحويل: {total_time_str}", "INFO")
                    
                    return  # إنهاء المراقبة
                    
        except queue.Empty:
            pass
        
        # جدولة التحقق التالي
        if self.conversion_running:
            self.root.after(100, self.check_message_queue)
    
    def log_message(self, message, msg_type="INFO"):
        """تسجيل رسالة في السجل مع دعم الألوان والتصفية"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # تحديد نوع الرسالة بناءً على المحتوى إذا لم يحدد
        if msg_type == "INFO":
            if "✅" in message or "تم" in message and "بنجاح" in message:
                msg_type = "SUCCESS"
            elif "❌" in message or "خطأ" in message or "فشل" in message:
                msg_type = "ERROR"
            elif "⚠️" in message or "تحذير" in message:
                msg_type = "WARNING"
            elif "🔄" in message or "جاري" in message or "بدء" in message:
                msg_type = "PROGRESS"
        
        full_message = f"[{timestamp}] {message}"
        
        # حفظ الرسالة للتصفية
        msg_data = {
            'timestamp': timestamp,
            'message': message,
            'type': self.map_message_type(msg_type),
            'full_message': full_message,
            'tag': msg_type
        }
        self.all_log_messages.append(msg_data)
        
        # عرض الرسالة إذا كانت تطابق الفلتر الحالي
        current_filter = self.filter_var.get()
        if current_filter == "الكل" or msg_data['type'] == current_filter:
            self.display_log_message(msg_data)
        
        # التمرير للأسفل
        self.log_text.see(tk.END)
        self.log_text.update()
    
    def map_message_type(self, msg_type):
        """تحويل نوع الرسالة للعربية للتصفية"""
        type_map = {
            "INFO": "معلومات",
            "SUCCESS": "نجاح", 
            "ERROR": "خطأ",
            "WARNING": "تحذير",
            "PROGRESS": "معلومات"
        }
        return type_map.get(msg_type, "معلومات")
    
    def update_status(self, message):
        """تحديث شريط الحالة مع الرموز والألوان"""
        # اقتطاع الرسالة إذا كانت طويلة
        if len(message) > 80:
            message = message[:77] + "..."
        
        # إضافة رمز حسب نوع الرسالة
        if "✅" in message or "تم" in message and "بنجاح" in message:
            status_msg = f"✅ {message}"
        elif "❌" in message or "خطأ" in message or "فشل" in message:
            status_msg = f"❌ {message}"
        elif "⚠️" in message or "تحذير" in message:
            status_msg = f"⚠️ {message}"
        elif "🔄" in message or "جاري" in message or "بدء" in message:
            status_msg = f"🔄 {message}"
        else:
            status_msg = message
        
        self.status_var.set(status_msg)

    def display_log_message(self, msg_data):
        """عرض رسالة واحدة في السجل مع التنسيق"""
        # إدراج timestamp مع لون خاص
        self.log_text.insert(tk.END, f"[{msg_data['timestamp']}] ", "timestamp")
        
        # إدراج الرسالة مع اللون المناسب
        self.log_text.insert(tk.END, f"{msg_data['message']}\n", msg_data['tag'])
    
    def update_progress(self, current, total, message=""):
        """تحديث شريط التقدم والمعلومات"""
        try:
            if total > 0:
                percentage = (current / total) * 100
                self.progress_bar['value'] = percentage
                
                # تحديث النص التفصيلي
                self.progress_details_var.set(f"{current}/{total} ({percentage:.1f}%)")
            
            if message:
                self.progress_var.set(message)
            
            # حساب الوقت المنقضي والمتبقي
            if self.start_time:
                elapsed = datetime.now() - self.start_time
                elapsed_str = str(elapsed).split('.')[0]  # إزالة الميكروثانية
                
                if total > 0 and current > 0:
                    # تقدير الوقت المتبقي
                    rate = current / elapsed.total_seconds()
                    remaining_items = total - current
                    if rate > 0:
                        remaining_seconds = remaining_items / rate
                        remaining_time = str(timedelta(seconds=int(remaining_seconds)))
                        self.time_var.set(f"منقضي: {elapsed_str} | متبقي: {remaining_time}")
                    else:
                        self.time_var.set(f"منقضي: {elapsed_str}")
                else:
                    self.time_var.set(f"منقضي: {elapsed_str}")
            
            self.root.update_idletasks()
            
        except Exception as e:
            print(f"خطأ في تحديث التقدم: {e}")
    
    def update_status(self, message):
        """تحديث شريط الحالة مع الرموز والألوان"""
        # اقتطاع الرسالة إذا كانت طويلة
        if len(message) > 80:
            message = message[:77] + "..."
        
        # إضافة رمز حسب نوع الرسالة
        if "✅" in message or "تم" in message and "بنجاح" in message:
            status_msg = f"✅ {message}"
        elif "❌" in message or "خطأ" in message or "فشل" in message:
            status_msg = f"❌ {message}"
        elif "⚠️" in message or "تحذير" in message:
            status_msg = f"⚠️ {message}"
        elif "🔄" in message or "جاري" in message or "بدء" in message:
            status_msg = f"🔄 {message}"
        else:
            status_msg = message
        
        self.status_var.set(status_msg)
        self.root.update_idletasks()
    
    def test_database_connection(self):
        """اختبار الاتصال بقاعدة البيانات"""
        try:
            # تحديث الإعدادات أولاً
            self.update_db_config()
            
            # محاولة الاتصال
            connection = pymysql.connect(
                host=self.db_config.get('host', 'localhost'),
                port=int(self.db_config.get('port', 3306)),
                user=self.db_config.get('user', ''),
                password=self.db_config.get('password', ''),
                database=self.db_config.get('database', ''),
                charset='utf8mb4'
            )
            
            if connection.is_connected():
                connection.close()
                return True
            
        except Exception as e:
            print(f"خطأ في اختبار الاتصال: {e}")
            return False
        
        return False

def main():
    root = tk.Tk()
    
    # تطبيق الستايل
    style = ttk.Style()
    style.theme_use('clam')
    
    app = ShamelaGUI(root)
    
    # جعل النافذة في المنتصف
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (900 // 2)
    y = (root.winfo_screenheight() // 2) - (700 // 2)
    root.geometry(f"900x700+{x}+{y}")
    
    root.mainloop()

if __name__ == "__main__":
    main()
