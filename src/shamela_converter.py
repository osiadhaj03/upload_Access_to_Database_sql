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

import pyodbc
import mysql.connector
import uuid
import os
import re
import json
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
            
            self.mysql_conn = mysql.connector.connect(**connection_params)
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


def main():
    """الدالة الرئيسية"""
    print("=== محول كتب الشاملة من Access إلى MySQL ===")
    print("المطور: مساعد الذكي الاصطناعي")
    print("="*50)
    
    # إعدادات قاعدة البيانات MySQL
    mysql_config = {
        'host': 'srv1800.hstgr.io',
        'port': 3306,
        'user': 'u994369532_test',
        'password': 'Test20205',
        'database': 'u994369532_test',
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