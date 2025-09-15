#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
حل شامل لمشكلة "لم يتم العثور على جدول المحتوى"
يدعم أنماط مختلفة من ملفات الشاملة
"""

import pyodbc
import mysql.connector
import os
import re
from typing import List, Dict, Optional, Tuple

class EnhancedShamelaConverter:
    """محول محسن يدعم أنماط متعددة من ملفات الشاملة"""
    
    def __init__(self, mysql_config: dict):
        self.mysql_config = mysql_config
        self.access_conn = None
        self.mysql_conn = None
        
    def log_message(self, message: str, level: str = "INFO"):
        """تسجيل الرسائل"""
        print(f"[{level}] {message}")
        
    def connect_access(self, file_path: str) -> bool:
        """الاتصال بملف Access"""
        try:
            conn_str = f'DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={file_path};'
            self.access_conn = pyodbc.connect(conn_str)
            self.log_message(f"تم الاتصال بملف Access: {os.path.basename(file_path)}")
            return True
        except Exception as e:
            self.log_message(f"خطأ في الاتصال بـ Access: {e}", "ERROR")
            return False
            
    def find_content_tables(self) -> List[Tuple[str, str, int]]:
        """البحث الذكي عن جداول المحتوى بأنماط مختلفة"""
        if not self.access_conn:
            return []
            
        cursor = self.access_conn.cursor()
        tables = [table.table_name for table in cursor.tables(tableType='TABLE') 
                 if not table.table_name.startswith('MSys')]
        
        self.log_message(f"الجداول الموجودة: {tables}")
        
        potential_tables = []
        
        for table in tables:
            try:
                # فحص عدد الصفوف
                cursor.execute(f"SELECT COUNT(*) FROM [{table}]")
                row_count = cursor.fetchone()[0]
                
                # فحص الأعمدة
                cursor.execute(f"SELECT * FROM [{table}] WHERE 1=0")
                columns = [desc[0].lower() for desc in cursor.description]
                
                # حساب نقاط للجدول حسب خصائصه
                score = 0
                table_type = "unknown"
                
                # النمط التقليدي: b### للمحتوى
                if re.match(r'^b\d+$', table):
                    score += 100
                    table_type = "content_traditional"
                    
                # النمط التقليدي: t### للفهرس
                elif re.match(r'^t\d+$', table):
                    score += 50
                    table_type = "index_traditional"
                    
                # البحث عن جداول المحتوى بالخصائص
                elif row_count > 50:  # جداول كبيرة محتملة
                    # البحث عن أعمدة نصية
                    text_indicators = ['nass', 'text', 'content', 'matn', 'متن', 'نص']
                    page_indicators = ['page', 'sahefa', 'safha', 'صفحة', 'صحيفة']
                    
                    text_score = sum(1 for indicator in text_indicators 
                                   if any(indicator in col for col in columns))
                    page_score = sum(1 for indicator in page_indicators 
                                   if any(indicator in col for col in columns))
                    
                    if text_score > 0:
                        score += 30 + (text_score * 10)
                        table_type = "content_detected"
                        
                    if page_score > 0:
                        score += 20 + (page_score * 5)
                        
                    # حجم الجدول
                    if row_count > 1000:
                        score += 15
                    elif row_count > 500:
                        score += 10
                    elif row_count > 100:
                        score += 5
                        
                if score > 0:
                    potential_tables.append((table, table_type, score))
                    self.log_message(f"جدول محتمل: {table} - نوع: {table_type} - نقاط: {score} - صفوف: {row_count}")
                    
            except Exception as e:
                self.log_message(f"خطأ في فحص الجدول {table}: {e}", "WARNING")
                
        # ترتيب حسب النقاط
        potential_tables.sort(key=lambda x: x[2], reverse=True)
        return potential_tables
        
    def analyze_table_structure(self, table_name: str) -> Dict:
        """تحليل هيكل الجدول"""
        cursor = self.access_conn.cursor()
        
        try:
            # معلومات الأعمدة
            cursor.execute(f"SELECT * FROM [{table_name}] WHERE 1=0")
            columns = [(desc[0], desc[1]) for desc in cursor.description]
            
            # عدد الصفوف
            cursor.execute(f"SELECT COUNT(*) FROM [{table_name}]")
            row_count = cursor.fetchone()[0]
            
            # عينة من البيانات
            cursor.execute(f"SELECT TOP 3 * FROM [{table_name}]")
            sample_data = cursor.fetchall()
            
            return {
                'columns': columns,
                'row_count': row_count,
                'sample_data': sample_data
            }
            
        except Exception as e:
            self.log_message(f"خطأ في تحليل الجدول {table_name}: {e}", "ERROR")
            return {}
            
    def extract_content_adaptive(self, table_name: str) -> List[Dict]:
        """استخراج المحتوى بطريقة تكيفية"""
        cursor = self.access_conn.cursor()
        
        try:
            # الحصول على هيكل الجدول
            structure = self.analyze_table_structure(table_name)
            if not structure:
                return []
                
            columns = [col[0] for col in structure['columns']]
            self.log_message(f"أعمدة الجدول {table_name}: {columns}")
            
            # تحديد الأعمدة المهمة
            text_column = None
            page_column = None
            id_column = None
            
            # البحث عن عمود النص
            for col in columns:
                col_lower = col.lower()
                if any(indicator in col_lower for indicator in ['nass', 'text', 'content', 'matn']):
                    text_column = col
                    break
                    
            # البحث عن عمود الصفحة
            for col in columns:
                col_lower = col.lower()
                if any(indicator in col_lower for indicator in ['page', 'sahefa', 'safha']):
                    page_column = col
                    break
                    
            # البحث عن عمود المعرف
            for col in columns:
                col_lower = col.lower()
                if any(indicator in col_lower for indicator in ['id', 'معرف', 'رقم']):
                    id_column = col
                    break
                    
            # إذا لم نجد الأعمدة، نأخذ الأعمدة الأولى
            if not text_column and len(columns) > 1:
                text_column = columns[1]  # عادة العمود الثاني يحتوي على النص
                
            if not page_column and len(columns) > 2:
                page_column = columns[2]  # عادة العمود الثالث يحتوي على رقم الصفحة
                
            if not id_column:
                id_column = columns[0]  # عادة العمود الأول يحتوي على المعرف
                
            self.log_message(f"الأعمدة المحددة - النص: {text_column}, الصفحة: {page_column}, المعرف: {id_column}")
            
            # استخراج البيانات
            query = f"SELECT [{id_column}]"
            if text_column:
                query += f", [{text_column}]"
            if page_column:
                query += f", [{page_column}]"
            query += f" FROM [{table_name}]"
            
            self.log_message(f"استعلام الاستخراج: {query}")
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            content_data = []
            for row in rows:
                item = {
                    'id': row[0] if len(row) > 0 else None,
                    'text': row[1] if len(row) > 1 and text_column else '',
                    'page': row[2] if len(row) > 2 and page_column else 1
                }
                
                # تنظيف النص
                if item['text']:
                    item['text'] = str(item['text']).strip()
                    
                content_data.append(item)
                
            self.log_message(f"تم استخراج {len(content_data)} عنصر من {table_name}")
            return content_data
            
        except Exception as e:
            self.log_message(f"خطأ في استخراج المحتوى من {table_name}: {e}", "ERROR")
            return []
            
    def convert_file_enhanced(self, file_path: str) -> bool:
        """تحويل محسن للملف"""
        self.log_message(f"بدء التحويل المحسن لـ: {os.path.basename(file_path)}")
        
        # الاتصال بـ Access
        if not self.connect_access(file_path):
            return False
            
        # البحث عن جداول المحتوى
        potential_tables = self.find_content_tables()
        
        if not potential_tables:
            self.log_message("لم يتم العثور على أي جداول محتوى محتملة!", "ERROR")
            return False
            
        # اختيار أفضل جدول
        best_table = potential_tables[0]
        table_name, table_type, score = best_table
        
        self.log_message(f"تم اختيار الجدول: {table_name} (نوع: {table_type}, نقاط: {score})")
        
        # استخراج المحتوى
        content_data = self.extract_content_adaptive(table_name)
        
        if not content_data:
            self.log_message("لم يتم استخراج أي محتوى!", "ERROR")
            return False
            
        self.log_message(f"تم استخراج {len(content_data)} عنصر بنجاح")
        
        # هنا يمكن إضافة منطق الحفظ في MySQL
        return True

def test_enhanced_converter():
    """اختبار المحول المحسن"""
    
    # إعدادات قاعدة البيانات (يمكن تخصيصها)
    mysql_config = {
        'host': 'srv1800.hstgr.io',
        'port': 3306,
        'database': 'u994369532_test',
        'user': 'u994369532_shamela',
        'password': 'mT8$pR3@vK9#'
    }
    
    # إنشاء المحول
    converter = EnhancedShamelaConverter(mysql_config)
    
    # اختبار مع ملف وهمي (يحتاج إلى ملف حقيقي للاختبار)
    print("🔍 البحث عن ملفات للاختبار...")
    
    # البحث عن ملفات في مجلدات مختلفة
    import glob
    test_files = glob.glob("*.accdb") + glob.glob("*.bok")
    
    if test_files:
        print(f"تم العثور على {len(test_files)} ملف:")
        for file in test_files:
            print(f"  - {file}")
            
        # اختبار أول ملف
        test_file = test_files[0]
        print(f"\n🚀 اختبار الملف: {test_file}")
        result = converter.convert_file_enhanced(test_file)
        
        if result:
            print("✅ نجح الاختبار!")
        else:
            print("❌ فشل الاختبار!")
    else:
        print("❌ لم يتم العثور على ملفات للاختبار!")
        print("💡 ضع ملفات .accdb أو .bok في نفس مجلد هذا الملف للاختبار")

if __name__ == "__main__":
    test_enhanced_converter()
