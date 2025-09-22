#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
محول .bok فائق التطور
يقرأ البيانات الفعلية ويحولها لقاعدة بيانات قابلة للاستخدام
"""

import os
import sqlite3
import pandas as pd
import struct
import re
from pathlib import Path

class UltimateBokConverter:
    """المحول النهائي لملفات .bok"""
    
    def __init__(self):
        self.jet_page_size = 4096
        self.extracted_data = {}
    
    def read_jet_pages(self, file_path):
        """قراءة صفحات قاعدة بيانات Jet"""
        try:
            with open(file_path, 'rb') as f:
                file_size = os.path.getsize(file_path)
                pages = []
                
                # قراءة الصفحات
                for offset in range(0, file_size, self.jet_page_size):
                    f.seek(offset)
                    page_data = f.read(self.jet_page_size)
                    
                    if len(page_data) < self.jet_page_size:
                        break
                    
                    pages.append({
                        'offset': offset,
                        'data': page_data
                    })
                
                return pages
                
        except Exception as e:
            print(f"خطأ في قراءة الصفحات: {e}")
            return []
    
    def extract_text_from_pages(self, pages):
        """استخراج النصوص من صفحات البيانات"""
        all_text = []
        
        for page in pages:
            try:
                # محاولة فك التشفير بطرق مختلفة
                for encoding in ['utf-16le', 'utf-8', 'cp1256']:
                    try:
                        text = page['data'].decode(encoding, errors='ignore')
                        
                        # البحث عن نصوص عربية
                        arabic_matches = re.findall(r'[\u0600-\u06FF]+[\u0600-\u06FF\s\d\u060C\u061B\u061F]*', text)
                        
                        for match in arabic_matches:
                            if len(match.strip()) > 5:  # نصوص أطول من 5 أحرف
                                all_text.append({
                                    'text': match.strip(),
                                    'page_offset': page['offset'],
                                    'encoding': encoding,
                                    'length': len(match.strip())
                                })
                        
                        if arabic_matches:
                            break  # إذا وجدنا نصوص، لا نحتاج encoding آخر
                            
                    except:
                        continue
                        
            except Exception as e:
                continue
        
        return all_text
    
    def organize_shamela_data(self, texts, table_info):
        """تنظيم البيانات حسب نمط الشاملة"""
        organized = {
            'content': [],
            'index': [],
            'metadata': {}
        }
        
        # فرز النصوص حسب الطول والموقع
        texts.sort(key=lambda x: (x['page_offset'], -x['length']))
        
        page_counter = 1
        current_chapter = "مقدمة"
        
        for i, text_entry in enumerate(texts):
            text = text_entry['text']
            
            # تصنيف النص
            if self.is_chapter_title(text):
                current_chapter = text
                organized['index'].append({
                    'id': len(organized['index']) + 1,
                    'title': text,
                    'page_start': page_counter,
                    'page_end': page_counter,
                    'level': 1
                })
            
            elif self.is_content_text(text):
                organized['content'].append({
                    'id': len(organized['content']) + 1,
                    'nass': text,
                    'page': page_counter,
                    'part': 1,
                    'chapter': current_chapter
                })
                
                # زيادة رقم الصفحة كل عدة نصوص
                if (i + 1) % 3 == 0:
                    page_counter += 1
        
        # استخراج معلومات الكتاب
        if texts:
            # أول نص طويل عادة يكون عنوان الكتاب
            long_texts = [t for t in texts if t['length'] > 20]
            if long_texts:
                organized['metadata']['title'] = long_texts[0]['text']
                organized['metadata']['author'] = "غير محدد"
                organized['metadata']['total_pages'] = page_counter
        
        return organized
    
    def is_chapter_title(self, text):
        """تحديد إذا كان النص عنوان فصل"""
        chapter_indicators = [
            'باب', 'فصل', 'كتاب', 'مقدمة', 'خاتمة',
            'الباب', 'الفصل', 'الكتاب', 'المقدمة'
        ]
        
        # عنوان الفصل عادة قصير ويحتوي على كلمات مفتاحية
        return (len(text) < 100 and 
                any(indicator in text for indicator in chapter_indicators))
    
    def is_content_text(self, text):
        """تحديد إذا كان النص محتوى عادي"""
        # المحتوى عادة نص طويل ولا يحتوي على عناوين
        return (len(text) > 20 and 
                not self.is_chapter_title(text) and
                not text.isdigit())
    
    def create_compatible_database(self, organized_data, table_info, output_path):
        """إنشاء قاعدة بيانات متوافقة مع النظام الأصلي"""
        try:
            # حذف قاعدة البيانات إذا كانت موجودة
            if os.path.exists(output_path):
                os.remove(output_path)
            
            conn = sqlite3.connect(output_path)
            cursor = conn.cursor()
            
            # إنشاء جدول المحتوى (b + رقم)
            content_table = f"b{table_info.get('book_id', '40000')}"
            cursor.execute(f'''
                CREATE TABLE {content_table} (
                    id INTEGER PRIMARY KEY,
                    nass TEXT NOT NULL,
                    page INTEGER,
                    part INTEGER DEFAULT 1
                )
            ''')
            
            # إدراج بيانات المحتوى
            for item in organized_data['content']:
                cursor.execute(f'''
                    INSERT INTO {content_table} (nass, page, part)
                    VALUES (?, ?, ?)
                ''', (item['nass'], item['page'], item['part']))
            
            # إنشاء جدول الفهرس (t + رقم)
            index_table = f"t{table_info.get('book_id', '40000')}"
            cursor.execute(f'''
                CREATE TABLE {index_table} (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    page_start INTEGER,
                    page_end INTEGER,
                    level INTEGER DEFAULT 1
                )
            ''')
            
            # إدراج بيانات الفهرس
            for item in organized_data['index']:
                cursor.execute(f'''
                    INSERT INTO {index_table} (title, page_start, page_end, level)
                    VALUES (?, ?, ?, ?)
                ''', (item['title'], item['page_start'], item['page_end'], item['level']))
            
            # إنشاء جدول معلومات الكتاب
            cursor.execute('''
                CREATE TABLE book_info (
                    id INTEGER PRIMARY KEY,
                    title TEXT,
                    author TEXT,
                    total_pages INTEGER,
                    content_table TEXT,
                    index_table TEXT
                )
            ''')
            
            metadata = organized_data['metadata']
            cursor.execute('''
                INSERT INTO book_info (title, author, total_pages, content_table, index_table)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                metadata.get('title', 'غير محدد'),
                metadata.get('author', 'غير محدد'),
                metadata.get('total_pages', 0),
                content_table,
                index_table
            ))
            
            conn.commit()
            conn.close()
            
            return {
                'database_path': output_path,
                'content_table': content_table,
                'index_table': index_table,
                'total_content': len(organized_data['content']),
                'total_chapters': len(organized_data['index']),
                'metadata': metadata
            }
            
        except Exception as e:
            print(f"خطأ في إنشاء قاعدة البيانات: {e}")
            return None
    
    def convert_bok_file(self, bok_path, output_dir=None):
        """تحويل ملف .bok واحد"""
        print(f"\n🚀 تحويل متطور: {os.path.basename(bok_path)}")
        
        try:
            # تحديد مجلد الحفظ
            if output_dir is None:
                output_dir = os.path.dirname(bok_path)
            
            # قراءة صفحات الملف
            print("📖 قراءة صفحات البيانات...")
            pages = self.read_jet_pages(bok_path)
            
            if not pages:
                print("❌ فشل في قراءة الصفحات")
                return None
            
            print(f"   تم قراءة {len(pages)} صفحة")
            
            # استخراج النصوص
            print("🔍 استخراج النصوص...")
            texts = self.extract_text_from_pages(pages)
            
            if not texts:
                print("❌ لم يتم العثور على نصوص")
                return None
            
            print(f"   تم استخراج {len(texts)} نص")
            
            # تنظيم البيانات
            print("📋 تنظيم البيانات...")
            
            # استخراج معرف الكتاب من اسم الملف أو النصوص
            book_id = self.extract_book_id(bok_path, texts)
            
            table_info = {
                'book_id': book_id,
                'file_name': os.path.basename(bok_path)
            }
            
            organized = self.organize_shamela_data(texts, table_info)
            
            print(f"   محتوى: {len(organized['content'])} عنصر")
            print(f"   فهرس: {len(organized['index'])} فصل")
            
            # إنشاء قاعدة البيانات
            print("🗄️ إنشاء قاعدة البيانات...")
            
            base_name = os.path.splitext(os.path.basename(bok_path))[0]
            output_path = os.path.join(output_dir, f"{base_name}_ultimate.db")
            
            result = self.create_compatible_database(organized, table_info, output_path)
            
            if result:
                print("✅ تم التحويل بنجاح!")
                print(f"   قاعدة البيانات: {result['database_path']}")
                print(f"   جدول المحتوى: {result['content_table']}")
                print(f"   جدول الفهرس: {result['index_table']}")
                print(f"   إجمالي المحتوى: {result['total_content']}")
                print(f"   إجمالي الفصول: {result['total_chapters']}")
                
                if result['metadata'].get('title'):
                    print(f"   عنوان الكتاب: {result['metadata']['title'][:50]}...")
                
                return result
            else:
                print("❌ فشل في إنشاء قاعدة البيانات")
                return None
                
        except Exception as e:
            print(f"❌ خطأ في التحويل: {e}")
            return None
    
    def extract_book_id(self, bok_path, texts):
        """استخراج معرف الكتاب"""
        # محاولة استخراج من اسم الملف
        filename = os.path.basename(bok_path)
        numbers = re.findall(r'\d+', filename)
        
        if numbers:
            return numbers[-1]  # آخر رقم في اسم الملف
        
        # إذا لم يوجد، استخدم رقم افتراضي
        return str(40000 + len(texts) % 1000)

def main():
    """الدالة الرئيسية"""
    print("=== محول .bok فائق التطور ===")
    print("=" * 45)
    
    # مجلد ملفات .bok
    bok_folder = Path("d:/test3/bok file")
    output_folder = Path("d:/test3/ultimate_converted")
    
    # إنشاء مجلد الحفظ
    output_folder.mkdir(exist_ok=True)
    
    bok_files = list(bok_folder.glob("*.bok"))
    
    if not bok_files:
        print("❌ لم يتم العثور على ملفات .bok")
        return
    
    converter = UltimateBokConverter()
    successful_conversions = []
    
    for i, bok_file in enumerate(bok_files, 1):
        print(f"\n{'='*60}")
        print(f"[{i}/{len(bok_files)}] معالجة: {bok_file.name}")
        print(f"{'='*60}")
        
        result = converter.convert_bok_file(str(bok_file), str(output_folder))
        
        if result:
            successful_conversions.append(result)
        
        print("-" * 60)
    
    # النتائج النهائية
    print(f"\n🎉 النتائج النهائية:")
    print(f"   نجح: {len(successful_conversions)}/{len(bok_files)}")
    
    if successful_conversions:
        print(f"\n📁 الملفات المحولة في: {output_folder}")
        print(f"📋 قواعد البيانات الجديدة:")
        
        for result in successful_conversions:
            print(f"   ✅ {os.path.basename(result['database_path'])}")
            print(f"      المحتوى: {result['total_content']} | الفصول: {result['total_chapters']}")
    
    print(f"\n💡 الخطوة التالية: اختبار قواعد البيانات الجديدة في التطبيق الرئيسي")

if __name__ == "__main__":
    main()
