#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
محول ملفات Access و BOK إلى JSON
يقوم بقراءة ملفات .accdb أو .bok وتحويلها إلى ملف JSON بالبنية المطلوبة

المطور: مساعد الذكي الاصطناعي
التاريخ: 2025
"""

import pyodbc
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional

class AccessToJSONConverter:
    def __init__(self, message_callback=None):
        """
        إنشاء محول Access إلى JSON
        message_callback: دالة لإرسال الرسائل إلى الواجهة
        """
        self.access_conn = None
        self.conversion_log = []
        self.message_callback = message_callback
        
    def log_message(self, message: str, level: str = "INFO"):
        """تسجيل رسالة في السجل"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        self.conversion_log.append(log_entry)
        print(log_entry)
        
        if self.message_callback:
            self.message_callback(message, level)
    
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
    
    def clean_text(self, text: str) -> str:
        """تنظيف النص من الأحرف غير المرغوب فيها"""
        if not text or text == "":
            return ""
        
        # تحويل إلى نص إذا لم يكن كذلك
        text = str(text).strip()
        
        # إذا كان النص فارغاً أو null
        if not text or text.lower() in ['null', 'none', '']:
            return ""
        
        # إزالة الأحرف الخاصة والتحكم
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        # تنظيف المسافات الزائدة
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def analyze_database_structure(self) -> Dict:
        """تحليل بنية قاعدة البيانات وتحديد جداول المعلومات والفهرس والمحتوى"""
        try:
            cursor = self.access_conn.cursor()
            tables = []
            for table_info in cursor.tables(tableType='TABLE'):
                table_name = table_info.table_name
                if not table_name.startswith('MSys'):  # تجاهل جداول النظام
                    tables.append(table_name)
            
            structure = {
                "all_tables": tables,
                "book_info_table": None,
                "index_tables": [],
                "content_tables": []
            }
            
            # تحديد جدول معلومات الكتاب
            for table in tables:
                if table.lower() in ['main', 'book_info', 'info']:
                    structure["book_info_table"] = table
                    break
            
            # تحديد جداول الفهرس
            for table in tables:
                table_lower = table.lower()
                if any(keyword in table_lower for keyword in ['title', 'index', 'fihris', 'فهرس', 'عنوان']):
                    structure["index_tables"].append(table)
                elif table.startswith('t') and table[1:].isdigit():  # جداول العناوين مثل t39299
                    structure["index_tables"].append(table)
            
            # تحديد جداول المحتوى
            for table in tables:
                if table.startswith('b') and table[1:].isdigit():  # جداول المحتوى مثل b39299
                    structure["content_tables"].append(table)
                elif table.lower() in ['content', 'nass', 'text', 'محتوى']:
                    structure["content_tables"].append(table)
            
            self.log_message(f"تحليل بنية قاعدة البيانات:")
            self.log_message(f"  - جدول معلومات الكتاب: {structure['book_info_table']}")
            self.log_message(f"  - جداول الفهرس: {structure['index_tables']}")
            self.log_message(f"  - جداول المحتوى: {structure['content_tables']}")
            
            return structure
            
        except Exception as e:
            self.log_message(f"خطأ في تحليل بنية قاعدة البيانات: {str(e)}", "ERROR")
            return {
                "all_tables": [],
                "book_info_table": "Main",
                "index_tables": [],
                "content_tables": []
            }
    def get_table_names(self) -> List[str]:
        """الحصول على أسماء الجداول في قاعدة البيانات"""
        try:
            cursor = self.access_conn.cursor()
            tables = []
            for table_info in cursor.tables(tableType='TABLE'):
                table_name = table_info.table_name
                if not table_name.startswith('MSys'):  # تجاهل جداول النظام
                    tables.append(table_name)
            
            self.log_message(f"تم العثور على {len(tables)} جدول: {', '.join(tables)}")
            return tables
            
        except Exception as e:
            self.log_message(f"خطأ في الحصول على أسماء الجداول: {str(e)}", "ERROR")
            return []
    
    def examine_table_structure(self, table_name: str) -> Dict:
        """فحص بنية جدول معين"""
        try:
            cursor = self.access_conn.cursor()
            cursor.execute(f"SELECT TOP 1 * FROM [{table_name}]")
            
            columns = [column[0] for column in cursor.description]
            sample_row = cursor.fetchone()
            
            structure = {
                "table_name": table_name,
                "columns": columns,
                "sample_data": dict(zip(columns, sample_row)) if sample_row else {}
            }
            
            self.log_message(f"جدول {table_name}: الأعمدة = {columns}")
            return structure
            
        except Exception as e:
            self.log_message(f"خطأ في فحص جدول {table_name}: {str(e)}", "ERROR")
            return {"table_name": table_name, "columns": [], "sample_data": {}}
    
    def extract_book_info(self) -> Optional[Dict]:
        """استخراج معلومات الكتاب من جدول Main"""
        try:
            cursor = self.access_conn.cursor()
            cursor.execute("SELECT * FROM Main")
            row = cursor.fetchone()
            
            if not row:
                self.log_message("لا توجد بيانات في جدول Main", "WARNING")
                return {
                    "title": "غير معروف",
                    "author": "غير معروف",
                    "publisher": "غير معروف",
                    "publication_year": None,
                    "description": "غير معروف",
                    "original_id": "غير معروف"
                }
            
            # الحصول على أسماء الأعمدة
            columns = [column[0] for column in cursor.description]
            book_data = dict(zip(columns, row))
            
            # تنظيف البيانات وتحويلها للبنية المطلوبة
            book_info = {
                "title": self.clean_text(book_data.get('Bk')) or "غير معروف",
                "author": self.clean_text(book_data.get('Auth')) or "غير معروف", 
                "publisher": self.clean_text(book_data.get('Publisher')) or "غير معروف",
                "publication_year": book_data.get('Year') or None,
                "description": self.clean_text(book_data.get('Description')) or "غير معروف",
                "original_id": str(book_data.get('ID')) if book_data.get('ID') else "غير معروف"
            }
            
            self.log_message(f"تم استخراج معلومات الكتاب: {book_info['title']}")
            return book_info
            
        except Exception as e:
            self.log_message(f"خطأ في استخراج معلومات الكتاب: {str(e)}", "ERROR")
            return {
                "title": "غير معروف",
                "author": "غير معروف", 
                "publisher": "غير معروف",
                "publication_year": None,
                "description": "غير معروف",
                "original_id": "غير معروف"
            }
    
    def extract_content(self, db_structure: Dict = None) -> List[Dict]:
        """استخراج محتوى الكتاب من جداول المحتوى المخصصة"""
        try:
            if not db_structure:
                db_structure = self.analyze_database_structure()
            
            content_tables = db_structure.get('content_tables', [])
            
            if not content_tables:
                # إذا لم نجد جداول محتوى مخصصة، نبحث عن جداول تبدأ بـ b
                all_tables = db_structure.get('all_tables', [])
                content_tables = [t for t in all_tables if t.startswith('b') and t[1:].isdigit()]
            
            if not content_tables:
                self.log_message("لم يتم العثور على جداول المحتوى", "WARNING")
                return []
            
            # استخدام أول جدول محتوى (عادة الأكبر)
            table_name = content_tables[0]
            self.log_message(f"استخراج المحتوى من جدول: {table_name}")
            
            # فحص بنية الجدول
            table_structure = self.examine_table_structure(table_name)
            columns = table_structure.get('columns', [])
            
            cursor = self.access_conn.cursor()
            
            # محاولة استعلامات مختلفة حسب وجود العمود
            try:
                if 'id' in [col.lower() for col in columns]:
                    cursor.execute(f"SELECT * FROM [{table_name}] ORDER BY id")
                else:
                    cursor.execute(f"SELECT * FROM [{table_name}]")
            except:
                try:
                    cursor.execute(f"SELECT * FROM [{table_name}]")
                except:
                    self.log_message(f"لا يمكن قراءة جدول {table_name}", "ERROR")
                    return []
            
            table_columns = [column[0] for column in cursor.description]
            content_data = []
            
            for i, row in enumerate(cursor.fetchall(), 1):
                row_data = dict(zip(table_columns, row))
                
                # استخراج النص الرئيسي من عدة حقول محتملة
                text_content = ""
                for text_field in ['nass', 'text', 'content', 'body', 'نص', 'Nass', 'Text']:
                    if text_field in row_data and row_data[text_field]:
                        text_content = self.clean_text(row_data[text_field])
                        break
                
                if not text_content:
                    text_content = "غير معروف"
                
                # استخراج رقم الصفحة
                page_number = i  # افتراضي
                for page_field in ['page', 'pg', 'صفحة', 'Page']:
                    if page_field in row_data and row_data[page_field]:
                        try:
                            page_number = int(row_data[page_field])
                            break
                        except:
                            pass
                
                # استخراج رقم الجزء
                part_number = 1  # افتراضي
                for part_field in ['part', 'pt', 'جزء', 'Part']:
                    if part_field in row_data and row_data[part_field]:
                        try:
                            part_number = int(row_data[part_field])
                            break
                        except:
                            pass
                
                # استخراج معلومات الفصل
                chapter_title = "غير معروف"
                for chapter_field in ['chapter', 'فصل', 'Chapter']:
                    if chapter_field in row_data and row_data[chapter_field]:
                        chapter_title = self.clean_text(row_data[chapter_field]) or "غير معروف"
                        break
                
                content_item = {
                    "id": i,
                    "text": text_content,
                    "page_number": page_number,
                    "volume_number": None,  # دائماً null
                    "part_number": part_number,
                    "chapter_info": {
                        "title": chapter_title,
                        "level": 1
                    }
                }
                
                content_data.append(content_item)
            
            self.log_message(f"تم استخراج {len(content_data)} عنصر من المحتوى")
            return content_data
            
        except Exception as e:
            self.log_message(f"خطأ في استخراج المحتوى: {str(e)}", "ERROR")
            return []
    
    def extract_index(self, db_structure: Dict = None) -> List[Dict]:
        """استخراج فهرس الكتاب من جداول الفهرس المخصصة"""
        try:
            if not db_structure:
                db_structure = self.analyze_database_structure()
            
            index_tables = db_structure.get('index_tables', [])
            
            if not index_tables:
                self.log_message("لم يتم العثور على جداول الفهرس", "WARNING")
                return []
            
            all_index_data = []
            
            # استخراج الفهرس من جميع جداول الفهرس
            for table_name in index_tables:
                self.log_message(f"استخراج الفهرس من جدول: {table_name}")
                
                # فحص بنية الجدول أولاً
                table_structure = self.examine_table_structure(table_name)
                columns = table_structure.get('columns', [])
                
                cursor = self.access_conn.cursor()
                
                # محاولة الاستعلام مع ترتيب حسب id إذا كان موجوداً
                try:
                    if 'id' in [col.lower() for col in columns]:
                        cursor.execute(f"SELECT * FROM [{table_name}] ORDER BY id")
                    else:
                        cursor.execute(f"SELECT * FROM [{table_name}]")
                except:
                    try:
                        cursor.execute(f"SELECT * FROM [{table_name}]")
                    except:
                        self.log_message(f"لا يمكن قراءة جدول {table_name}", "ERROR")
                        continue
                
                table_columns = [column[0] for column in cursor.description]
                
                for i, row in enumerate(cursor.fetchall(), 1):
                    row_data = dict(zip(table_columns, row))
                    
                    # البحث عن عنوان الفهرس في عدة حقول محتملة
                    title = ""
                    for title_field in ['tit', 'title', 'name', 'heading', 'عنوان', 'Tit', 'Title']:
                        if title_field in row_data and row_data[title_field]:
                            title = self.clean_text(row_data[title_field])
                            break
                    
                    if not title or title == "غير معروف":
                        continue  # تجاهل العناصر بدون عنوان
                    
                    # استخراج معلومات إضافية
                    level = 1
                    for level_field in ['level', 'lvl', 'مستوى', 'Level']:
                        if level_field in row_data and row_data[level_field]:
                            try:
                                level = int(row_data[level_field])
                                break
                            except:
                                pass
                    
                    page_reference = 1
                    for page_field in ['page', 'pg', 'صفحة', 'Page']:
                        if page_field in row_data and row_data[page_field]:
                            try:
                                page_reference = int(row_data[page_field])
                                break
                            except:
                                pass
                    
                    parent_id = None
                    for parent_field in ['parent_id', 'parent', 'والد', 'Parent']:
                        if parent_field in row_data and row_data[parent_field]:
                            try:
                                parent_id = int(row_data[parent_field])
                                break
                            except:
                                pass
                    
                    index_item = {
                        "id": len(all_index_data) + 1,
                        "title": title,
                        "level": level,
                        "page_reference": page_reference,
                        "parent_id": parent_id,
                        "source_table": table_name
                    }
                    
                    all_index_data.append(index_item)
            
            self.log_message(f"تم استخراج {len(all_index_data)} عنصر من الفهرس")
            return all_index_data
            
        except Exception as e:
            self.log_message(f"خطأ في استخراج الفهرس: {str(e)}", "ERROR")
            return []
    
    def extract_chapters_from_content(self, content_data: List[Dict]) -> List[Dict]:
        """استخراج فهرس الفصول من المحتوى"""
        try:
            chapters = []
            chapter_id = 1
            
            for item in content_data:
                chapter_title = item.get('chapter_info', {}).get('title', '')
                if chapter_title and chapter_title != "غير معروف":
                    # التحقق من أن الفصل غير موجود مسبقاً
                    existing = False
                    for ch in chapters:
                        if ch['title'] == chapter_title:
                            existing = True
                            break
                    
                    if not existing:
                        chapters.append({
                            "id": chapter_id,
                            "title": chapter_title,
                            "level": item.get('chapter_info', {}).get('level', 1),
                            "page_reference": item.get('page_number', 1),
                            "parent_id": None
                        })
                        chapter_id += 1
            
            # إضافة فصل افتراضي إذا لم نجد أي فصول
            if not chapters:
                chapters.append({
                    "id": 1,
                    "title": "المحتوى الرئيسي",
                    "level": 1,
                    "page_reference": 1,
                    "parent_id": None
                })
            
            self.log_message(f"تم استخراج {len(chapters)} فصل من المحتوى")
            return chapters
            
        except Exception as e:
            self.log_message(f"خطأ في استخراج الفصول من المحتوى: {str(e)}", "ERROR")
            return [{
                "id": 1,
                "title": "المحتوى الرئيسي",
                "level": 1,
                "page_reference": 1,
                "parent_id": None
            }]
    
    def log_to_output_file(self, json_file_path: str, book_info: Dict, content_data: List[Dict], index_data: List[Dict], db_structure: Dict = None):
        """كتابة المخرجات في ملف السجل"""
        try:
            output_log_path = "d:\\test3\\json_outputs_log.txt"
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with open(output_log_path, 'a', encoding='utf-8') as f:
                f.write(f"\n\n--- مخرجات تحويل محسن ---\n")
                f.write(f"التاريخ والوقت: {timestamp}\n")
                f.write(f"ملف JSON: {json_file_path}\n")
                f.write(f"عنوان الكتاب: {book_info['title']}\n")
                f.write(f"المؤلف: {book_info['author']}\n")
                f.write(f"الناشر: {book_info['publisher']}\n")
                f.write(f"سنة النشر: {book_info['publication_year']}\n")
                f.write(f"عدد صفحات المحتوى: {len(content_data)}\n")
                f.write(f"عدد عناصر الفهرس: {len(index_data)}\n")
                
                if db_structure:
                    f.write(f"\n--- تحليل قاعدة البيانات ---\n")
                    f.write(f"جدول معلومات الكتاب: {db_structure.get('book_info_table', 'غير محدد')}\n")
                    f.write(f"جداول الفهرس: {', '.join(db_structure.get('index_tables', ['لا يوجد']))}\n")
                    f.write(f"جداول المحتوى: {', '.join(db_structure.get('content_tables', ['لا يوجد']))}\n")
                    f.write(f"إجمالي الجداول: {len(db_structure.get('all_tables', []))}\n")
                
                f.write(f"\nالبنية الجديدة: book_info -> chapters_index -> content -> metadata\n")
                f.write(f"volume_number: دائماً null\n")
                f.write("="*60)
                
        except Exception as e:
            self.log_message(f"خطأ في كتابة ملف المخرجات: {str(e)}", "ERROR")
    
    def convert_access_to_json(self, access_file_path: str, output_json_path: str) -> bool:
        """تحويل ملف Access إلى JSON مع تحليل محسن للبنية"""
        try:
            # الاتصال بملف Access
            if not self.connect_access(access_file_path):
                return False
            
            # تحليل بنية قاعدة البيانات أولاً
            self.log_message("تحليل بنية قاعدة البيانات...")
            db_structure = self.analyze_database_structure()
            
            # استخراج البيانات حسب التحليل
            book_info = self.extract_book_info()
            content_data = self.extract_content(db_structure)
            index_data = self.extract_index(db_structure)
            
            # إذا لم نجد فهرس منفصل، نستخرج الفصول من المحتوى
            if not index_data:
                self.log_message("لم يتم العثور على فهرس منفصل، استخراج الفصول من المحتوى...")
                chapters_from_content = self.extract_chapters_from_content(content_data)
                index_data = chapters_from_content
            
            # تجميع البيانات في البنية الجديدة
            json_data = {
                "book_info": book_info,
                "chapters_index": index_data,  # الفهرس بين معلومات الكتاب والمحتوى
                "content": content_data,
                "metadata": {
                    "database_structure": db_structure,
                    "extraction_timestamp": datetime.now().isoformat(),
                    "total_tables": len(db_structure.get('all_tables', [])),
                    "index_sources": [item.get('source_table') for item in index_data if 'source_table' in item]
                }
            }
            
            # حفظ ملف JSON
            with open(output_json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            # كتابة المخرجات في ملف السجل
            self.log_to_output_file(output_json_path, book_info, content_data, index_data, db_structure)
            
            self.log_message(f"تم حفظ ملف JSON: {output_json_path}")
            self.log_message(f"الكتاب: {book_info['title']}")
            self.log_message(f"عدد صفحات المحتوى: {len(content_data)}")
            self.log_message(f"عدد عناصر الفهرس: {len(index_data)}")
            self.log_message(f"الجداول المستخدمة: {db_structure}")
            
            return True
            
        except Exception as e:
            self.log_message(f"خطأ في تحويل ملف Access إلى JSON: {str(e)}", "ERROR")
            return False
        
        finally:
            if self.access_conn:
                self.access_conn.close()
    
    def save_log(self, log_file_path: str):
        """حفظ سجل العمليات في ملف"""
        try:
            with open(log_file_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(self.conversion_log))
            print(f"تم حفظ السجل في: {log_file_path}")
        except Exception as e:
            print(f"خطأ في حفظ السجل: {str(e)}")


def main():
    """الدالة الرئيسية للاختبار"""
    print("=== محول ملفات Access إلى JSON ===")
    print("المطور: مساعد الذكي الاصطناعي")
    print("="*50)
    
    # ملفات Access للتحويل
    access_files = [
        r"d:\test3\access file\shamela_book.accdb",
        r"d:\test3\access file\مقدمة الصلاة للفناري 834.accdb"
    ]
    
    converter = AccessToJSONConverter()
    
    for access_file in access_files:
        if not os.path.exists(access_file):
            print(f"الملف غير موجود: {access_file}")
            continue
        
        # تحديد اسم ملف JSON الخرج
        base_name = os.path.splitext(os.path.basename(access_file))[0]
        output_json = f"{base_name}_converted.json"
        
        print(f"\nتحويل: {os.path.basename(access_file)}")
        success = converter.convert_access_to_json(access_file, output_json)
        
        if success:
            print(f"✓ تم التحويل بنجاح: {output_json}")
        else:
            print(f"✗ فشل التحويل: {access_file}")
    
    # حفظ السجل
    log_file = f"access_to_json_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    converter.save_log(log_file)
    
    print(f"\nتم حفظ السجل في: {log_file}")


if __name__ == "__main__":
    main()
