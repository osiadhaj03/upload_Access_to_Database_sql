#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
طريقة CSV لاستخراج البيانات من ملفات .bok
"""

import pandas as pd
import os
import sys
import csv
from pathlib import Path

class CSVBokExtractor:
    """استخراج البيانات من ملفات CSV مُصدرة من Access"""
    
    def __init__(self):
        self.csv_folder = r"d:\test3\data\csv_exports"
        Path(self.csv_folder).mkdir(parents=True, exist_ok=True)
    
    def guide_manual_export(self, bok_file):
        """دليل التصدير اليدوي"""
        print("📋 دليل التصدير اليدوي من Access:")
        print("=" * 50)
        print("1. افتح ملف .bok في Microsoft Access")
        print("2. اذهب إلى External Data > Export > Text File")
        print("3. صدّر الجداول التالية:")
        print("   - Main أو TBMain (محتوى الصفحات)")
        print("   - TBTitles أو Index (فهرس الكتاب)")
        print("   - Books أو BookInfo (معلومات الكتاب)")
        print("4. احفظ الملفات في مجلد:", self.csv_folder)
        print("5. شغّل هذا السكريبت مرة أخرى")
        print("=" * 50)
    
    def process_csv_files(self, book_name):
        """معالجة ملفات CSV"""
        try:
            # البحث عن ملفات CSV
            csv_files = list(Path(self.csv_folder).glob("*.csv"))
            
            if not csv_files:
                print("❌ لم توجد ملفات CSV")
                self.guide_manual_export(None)
                return None
            
            print(f"📁 وُجد {len(csv_files)} ملف CSV:")
            for csv_file in csv_files:
                print(f"  - {csv_file.name}")
            
            # محاولة تحديد الملفات
            content_file = self.find_content_file(csv_files)
            index_file = self.find_index_file(csv_files)
            
            if not content_file:
                print("❌ لم يُعثر على ملف المحتوى")
                return None
            
            # قراءة البيانات
            content_data = self.read_content_csv(content_file)
            index_data = self.read_index_csv(index_file) if index_file else []
            
            return {
                'content_data': content_data,
                'index_data': index_data,
                'book_info': {'title': book_name}
            }
            
        except Exception as e:
            print(f"❌ خطأ في معالجة CSV: {str(e)}")
            return None
    
    def find_content_file(self, csv_files):
        """البحث عن ملف المحتوى"""
        content_keywords = ['main', 'tbmain', 'content', 'pages', 'nass']
        
        for csv_file in csv_files:
            name_lower = csv_file.name.lower()
            if any(keyword in name_lower for keyword in content_keywords):
                print(f"✅ ملف المحتوى: {csv_file.name}")
                return csv_file
        
        # إذا لم نجد، نأخذ أكبر ملف
        largest_file = max(csv_files, key=lambda f: f.stat().st_size)
        print(f"🔍 أخذ أكبر ملف كمحتوى: {largest_file.name}")
        return largest_file
    
    def find_index_file(self, csv_files):
        """البحث عن ملف الفهرس"""
        index_keywords = ['titles', 'tbtitles', 'index', 'fihris', 'chapters']
        
        for csv_file in csv_files:
            name_lower = csv_file.name.lower()
            if any(keyword in name_lower for keyword in index_keywords):
                print(f"✅ ملف الفهرس: {csv_file.name}")
                return csv_file
        
        print("⚠️ لم يُعثر على ملف فهرس")
        return None
    
    def read_content_csv(self, csv_file):
        """قراءة ملف محتوى CSV"""
        try:
            # جرب encodings مختلفة
            encodings = ['utf-8', 'cp1256', 'windows-1256', 'latin1']
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(csv_file, encoding=encoding)
                    print(f"✅ قُرئ بـ {encoding}: {len(df)} سجل")
                    break
                except UnicodeDecodeError:
                    continue
            else:
                print("❌ فشل في قراءة الملف بجميع الترميزات")
                return []
            
            # تحويل إلى تنسيق مناسب
            content_data = []
            
            for _, row in df.iterrows():
                # محاولة تحديد الأعمدة
                page_num = self.extract_page_number(row)
                content = self.extract_content(row)
                part = self.extract_part(row)
                
                if content:  # فقط إذا كان هناك محتوى
                    content_data.append({
                        'page': page_num,
                        'id': page_num,
                        'nass': content,
                        'part': part
                    })
            
            print(f"✅ تم استخراج {len(content_data)} صفحة محتوى")
            return content_data
            
        except Exception as e:
            print(f"❌ خطأ في قراءة ملف المحتوى: {str(e)}")
            return []
    
    def read_index_csv(self, csv_file):
        """قراءة ملف فهرس CSV"""
        try:
            encodings = ['utf-8', 'cp1256', 'windows-1256', 'latin1']
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(csv_file, encoding=encoding)
                    print(f"✅ قُرئ الفهرس بـ {encoding}: {len(df)} سجل")
                    break
                except UnicodeDecodeError:
                    continue
            else:
                return []
            
            # تحويل إلى تنسيق مناسب
            index_data = []
            
            for _, row in df.iterrows():
                page_num = self.extract_page_number(row)
                title = self.extract_title(row)
                level = self.extract_level(row)
                
                if title:  # فقط إذا كان هناك عنوان
                    index_data.append({
                        'id': page_num,
                        'tit': title,
                        'lvl': level or 1
                    })
            
            print(f"✅ تم استخراج {len(index_data)} عنصر فهرس")
            return index_data
            
        except Exception as e:
            print(f"❌ خطأ في قراءة ملف الفهرس: {str(e)}")
            return []
    
    def extract_page_number(self, row):
        """استخراج رقم الصفحة"""
        page_columns = ['page', 'pagenum', 'id', 'رقم_الصفحة', 'رقم']
        
        for col in page_columns:
            if col in row and pd.notna(row[col]):
                try:
                    return int(row[col])
                except:
                    pass
        
        # استخدم الفهرس كرقم صفحة
        return row.name + 1
    
    def extract_content(self, row):
        """استخراج المحتوى"""
        content_columns = ['nass', 'content', 'text', 'محتوى', 'نص']
        
        for col in content_columns:
            if col in row and pd.notna(row[col]):
                return str(row[col]).strip()
        
        # أخذ أطول نص في السطر
        text_values = [str(val) for val in row.values if pd.notna(val) and len(str(val)) > 10]
        return max(text_values, key=len) if text_values else ""
    
    def extract_part(self, row):
        """استخراج رقم الجزء"""
        part_columns = ['part', 'جزء', 'volume']
        
        for col in part_columns:
            if col in row and pd.notna(row[col]):
                try:
                    return int(row[col])
                except:
                    pass
        
        return None
    
    def extract_title(self, row):
        """استخراج العنوان"""
        title_columns = ['title', 'tit', 'عنوان', 'اسم']
        
        for col in title_columns:
            if col in row and pd.notna(row[col]):
                return str(row[col]).strip()
        
        # أخذ أول نص غير رقمي
        for val in row.values:
            if pd.notna(val) and not str(val).isdigit() and len(str(val)) > 2:
                return str(val).strip()
        
        return ""
    
    def extract_level(self, row):
        """استخراج مستوى العنوان"""
        level_columns = ['level', 'lvl', 'مستوى']
        
        for col in level_columns:
            if col in row and pd.notna(row[col]):
                try:
                    return int(row[col])
                except:
                    pass
        
        return 1

def main():
    """الوظيفة الرئيسية"""
    print("📊 استخراج البيانات من ملفات CSV")
    print("=" * 50)
    
    extractor = CSVBokExtractor()
    
    # التحقق من وجود ملفات CSV
    csv_files = list(Path(extractor.csv_folder).glob("*.csv"))
    
    if not csv_files:
        print("❌ لا توجد ملفات CSV")
        extractor.guide_manual_export(None)
        return
    
    # معالجة الملفات
    book_name = "كتاب تجريبي"
    result = extractor.process_csv_files(book_name)
    
    if result:
        print("\n✅ تم استخراج البيانات بنجاح!")
        print(f"📄 المحتوى: {len(result['content_data'])} صفحة")
        print(f"📚 الفهرس: {len(result['index_data'])} عنصر")
        
        # عرض عينة
        if result['content_data']:
            sample = result['content_data'][0]
            print(f"📋 عينة محتوى: صفحة {sample.get('page', '؟')} - {sample.get('nass', '')[:50]}...")
    else:
        print("❌ فشل في استخراج البيانات")

if __name__ == "__main__":
    main()
    input("\nاضغط Enter للخروج...")
