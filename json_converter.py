#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
محول مبسط يحفظ النتائج في ملف JSON لاختبار النظام الجديد
"""

import pyodbc
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class JSONShamelaConverter:
    def __init__(self):
        self.conversion_log = []
        
    def log_message(self, message: str, level: str = "INFO"):
        """تسجيل رسالة في السجل"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        self.conversion_log.append(log_entry)
        print(log_entry)
    
    def clean_text(self, text: str) -> str:
        """تنظيف النص من الأحرف غير المرغوب فيها"""
        if not text:
            return ""
        
        import re
        # إزالة الأحرف الخاصة والتحكم
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', str(text))
        # تنظيف المسافات الزائدة
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def extract_book_info(self, cursor) -> Optional[Dict]:
        """استخراج معلومات الكتاب من جدول Main"""
        try:
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
            
            title = cleaned_data.get('Bk', 'غير محدد')
            self.log_message(f"تم استخراج معلومات الكتاب: {title}")
            return cleaned_data
            
        except Exception as e:
            self.log_message(f"خطأ في استخراج معلومات الكتاب: {str(e)}", "ERROR")
            return None
    
    def extract_book_content(self, cursor, table_name: str) -> List[Dict]:
        """استخراج محتوى الكتاب من جدول المحتوى"""
        try:
            # فحص هيكل الجدول أولاً
            cursor.execute(f"SELECT * FROM [{table_name}] WHERE 1=0")
            columns = [column[0] for column in cursor.description]
            self.log_message(f"أعمدة الجدول {table_name}: {columns}")
            
            # قراءة البيانات مرتبة حسب ID
            cursor.execute(f"SELECT * FROM [{table_name}] ORDER BY id")
            
            content_data = []
            for row in cursor.fetchall():
                row_data = dict(zip(columns, row))
                
                # تنظيف النص
                if 'nass' in row_data and row_data['nass']:
                    row_data['nass'] = self.clean_text(str(row_data['nass']))
                
                content_data.append(row_data)
            
            self.log_message(f"تم استخراج {len(content_data)} صف من جدول {table_name}")
            return content_data
            
        except Exception as e:
            self.log_message(f"خطأ في استخراج محتوى الكتاب من {table_name}: {str(e)}", "ERROR")
            return []
    
    def extract_book_index(self, cursor, table_name: str) -> List[Dict]:
        """استخراج فهرس الكتاب من جدول الفهرس"""
        try:
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
    
    def process_chapters_and_pages(self, content_data: List[Dict], index_data: List[Dict]) -> Dict:
        """معالجة الفصول والصفحات وإنشاء الربط الصحيح"""
        try:
            # 1. إنشاء نطاقات الفصول بناءً على ID من Access
            chapter_data = {}
            sorted_index = sorted(index_data, key=lambda x: x.get('id', 0))
            
            self.log_message(f"بدء معالجة {len(sorted_index)} فصل بناءً على ID من Access")
            
            for i, index_item in enumerate(sorted_index):
                chapter_start_id = index_item.get('id')
                chapter_title = self.clean_text(index_item.get('tit', f'فصل {chapter_start_id}'))
                chapter_level = index_item.get('lvl', 1)
                
                # تحديد نطاق ID للفصل
                start_id = chapter_start_id
                if i < len(sorted_index) - 1:
                    end_id = sorted_index[i + 1].get('id') - 1
                else:
                    # الفصل الأخير
                    end_id = max([item.get('id', 0) for item in content_data])
                
                chapter_data[chapter_start_id] = {
                    'title': chapter_title,
                    'start_id': start_id,
                    'end_id': end_id,
                    'level': chapter_level,
                    'pages': []
                }
                
                self.log_message(f"فصل '{chapter_title}': ID من {start_id} إلى {end_id}")
            
            # 2. ربط الصفحات بالفصول بناءً على ID من Access
            pages_without_chapter = 0
            pages_with_chapter = 0
            part_stats = {}
            
            self.log_message(f"بدء ربط {len(content_data)} صفحة بالفصول...")
            
            for content_item in content_data:
                content_id = content_item.get('id', 0)
                page_num = content_item.get('page', content_id)
                content_text = content_item.get('nass', '')
                part_value = content_item.get('part')
                
                # تتبع إحصائيات الأجزاء
                part_key = part_value if part_value is not None else "بدون جزء"
                if part_key not in part_stats:
                    part_stats[part_key] = 0
                part_stats[part_key] += 1
                
                # العثور على الفصل المناسب
                chapter_found = False
                for ch_access_id, ch_info in chapter_data.items():
                    if ch_info['start_id'] <= content_id <= ch_info['end_id']:
                        ch_info['pages'].append({
                            'access_id': content_id,
                            'page_number': page_num,
                            'content': content_text[:200] + "..." if len(content_text) > 200 else content_text,
                            'part': part_value
                        })
                        pages_with_chapter += 1
                        chapter_found = True
                        break
                
                if not chapter_found:
                    pages_without_chapter += 1
            
            # 3. إنشاء الإحصائيات
            result = {
                'book_info': {},
                'chapters': list(chapter_data.values()),
                'statistics': {
                    'total_chapters': len(chapter_data),
                    'total_pages': len(content_data),
                    'pages_with_chapter': pages_with_chapter,
                    'pages_without_chapter': pages_without_chapter,
                    'success_rate': (pages_with_chapter / len(content_data)) * 100,
                    'part_distribution': part_stats
                },
                'chapter_details': {}
            }
            
            # 4. تفاصيل كل فصل
            chapters_with_pages = 0
            chapters_without_pages = 0
            
            for ch_access_id, ch_info in chapter_data.items():
                page_count = len(ch_info['pages'])
                if page_count > 0:
                    chapters_with_pages += 1
                else:
                    chapters_without_pages += 1
                
                result['chapter_details'][ch_access_id] = {
                    'title': ch_info['title'],
                    'id_range': f"{ch_info['start_id']}-{ch_info['end_id']}",
                    'page_count': page_count,
                    'has_pages': page_count > 0
                }
            
            result['statistics']['chapters_with_pages'] = chapters_with_pages
            result['statistics']['chapters_without_pages'] = chapters_without_pages
            
            # طباعة الإحصائيات
            self.log_message("=== إحصائيات الربط النهائية ===")
            self.log_message(f"إجمالي الفصول: {len(chapter_data)}")
            self.log_message(f"فصول مع صفحات: {chapters_with_pages}")
            self.log_message(f"فصول بدون صفحات: {chapters_without_pages}")
            self.log_message(f"إجمالي الصفحات: {len(content_data)}")
            self.log_message(f"صفحات مربوطة: {pages_with_chapter}")
            self.log_message(f"صفحات غير مربوطة: {pages_without_chapter}")
            self.log_message(f"نسبة نجاح الربط: {(pages_with_chapter/len(content_data))*100:.1f}%")
            
            return result
            
        except Exception as e:
            self.log_message(f"خطأ في معالجة الفصول والصفحات: {str(e)}", "ERROR")
            return {}
    
    def convert_access_file(self, access_file_path: str) -> bool:
        """تحويل ملف Access وحفظ النتائج في JSON"""
        try:
            self.log_message(f"بدء تحويل ملف: {os.path.basename(access_file_path)}")
            
            # الاتصال بملف Access
            if not os.path.exists(access_file_path):
                self.log_message(f"ملف Access غير موجود: {access_file_path}", "ERROR")
                return False
            
            conn_str = f'DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={access_file_path};'
            connection = pyodbc.connect(conn_str)
            cursor = connection.cursor()
            
            self.log_message(f"تم الاتصال بملف Access: {os.path.basename(access_file_path)}")
            
            # استخراج معلومات الكتاب
            book_info = self.extract_book_info(cursor)
            
            # تحديد الجداول
            content_table = "b40674"
            index_table = "t40674"
            
            # استخراج البيانات
            content_data = self.extract_book_content(cursor, content_table)
            index_data = self.extract_book_index(cursor, index_table)
            
            if not content_data:
                self.log_message("لا يوجد محتوى للتحويل", "WARNING")
                return False
            
            # معالجة البيانات
            result = self.process_chapters_and_pages(content_data, index_data)
            result['book_info'] = book_info
            result['conversion_log'] = self.conversion_log
            
            # حفظ النتائج في ملف JSON
            output_file = f"conversion_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            self.log_message(f"تم حفظ النتائج في: {output_file}")
            
            connection.close()
            return True
            
        except Exception as e:
            self.log_message(f"خطأ في تحويل الملف: {str(e)}", "ERROR")
            return False

def main():
    """الدالة الرئيسية"""
    print("=== محول كتب الشاملة - اختبار النظام الجديد ===")
    print("المطور: مساعد الذكي الاصطناعي")
    print("="*60)
    
    access_file = r"c:\Users\osaidsalah002\Documents\test3_v00\access file\خلاصة.accdb"
    
    converter = JSONShamelaConverter()
    success = converter.convert_access_file(access_file)
    
    if success:
        print("\n🎉 تم التحويل بنجاح!")
    else:
        print("\n❌ فشل التحويل!")

if __name__ == "__main__":
    main()
