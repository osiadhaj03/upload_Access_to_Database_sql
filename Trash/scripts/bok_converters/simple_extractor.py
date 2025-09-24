#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
طريقة بسيطة لاستخراج البيانات من ملفات .bok بدون مكتبات خارجية
"""

import sqlite3
import shutil
import os
import csv
from pathlib import Path
import tempfile
import subprocess

class SimpleBokExtractor:
    """استخراج البيانات من ملفات .bok بطرق بسيطة"""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = Path("d:/test3/data/simple_extract")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def extract_all_methods(self, bok_file):
        """جرب جميع الطرق المتاحة"""
        print("🔍 جاري تجربة طرق الاستخراج...")
        
        methods = [
            ("Simple BOK Support", self.try_simple_bok),
            ("SQLite Copy", self.try_sqlite_copy),
            ("Raw File Analysis", self.try_raw_analysis),
            ("PowerShell COM", self.try_powershell_com),
            ("Manual Guide", self.show_manual_guide)
        ]
        
        for method_name, method_func in methods:
            print(f"\n📋 تجربة: {method_name}")
            print("-" * 40)
            
            try:
                result = method_func(bok_file)
                if result:
                    print(f"✅ {method_name}: نجح!")
                    return result
                else:
                    print(f"❌ {method_name}: لم ينجح")
            except Exception as e:
                print(f"❌ {method_name}: خطأ - {str(e)}")
        
        print("\n⚠️ فشلت جميع الطرق التلقائية")
        return None
    
    def try_simple_bok(self, bok_file):
        """تجربة Simple BOK Support"""
        try:
            import sys
            sys.path.append("../../../src")
            from Trash.simple_bok_support import SimpleBokProcessor
            
            processor = SimpleBokProcessor()
            result = processor.extract_from_bok(bok_file)
            
            if result and result.get('content_data'):
                print(f"  📄 {len(result['content_data'])} صفحة محتوى")
                print(f"  📚 {len(result.get('index_data', []))} عنصر فهرس")
                return result
            
            return None
            
        except Exception as e:
            print(f"  خطأ: {str(e)}")
            return None
    
    def try_sqlite_copy(self, bok_file):
        """تجربة نسخ كـ SQLite"""
        try:
            # نسخ الملف كـ .db
            sqlite_file = self.temp_dir + "/test.db"
            shutil.copy2(bok_file, sqlite_file)
            
            # محاولة فتحه كـ SQLite
            conn = sqlite3.connect(sqlite_file)
            cursor = conn.cursor()
            
            # الحصول على قائمة الجداول
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            if not tables:
                conn.close()
                return None
            
            print(f"  📋 وُجد {len(tables)} جدول")
            
            # البحث عن جداول المحتوى
            content_data = []
            index_data = []
            
            for table_name, in tables:
                try:
                    cursor.execute(f"SELECT * FROM `{table_name}` LIMIT 5")
                    sample = cursor.fetchall()
                    
                    if sample:
                        print(f"    - {table_name}: {len(sample)} عينة")
                        
                        # تحديد نوع الجدول بناءً على البيانات
                        if self.looks_like_content_table(sample, table_name):
                            content_data.extend(self.extract_content_from_table(cursor, table_name))
                        elif self.looks_like_index_table(sample, table_name):
                            index_data.extend(self.extract_index_from_table(cursor, table_name))
                            
                except Exception as table_error:
                    print(f"    ⚠️ تخطي {table_name}: {str(table_error)}")
            
            conn.close()
            
            if content_data:
                return {
                    'content_data': content_data,
                    'index_data': index_data,
                    'book_info': {'title': Path(bok_file).stem}
                }
            
            return None
            
        except Exception as e:
            print(f"  خطأ SQLite: {str(e)}")
            return None
    
    def looks_like_content_table(self, sample, table_name):
        """تحديد إذا كان الجدول يحتوي على محتوى"""
        name_indicators = ['main', 'content', 'nass', 'text']
        
        # فحص اسم الجدول
        if any(indicator in table_name.lower() for indicator in name_indicators):
            return True
        
        # فحص البيانات
        for row in sample:
            for cell in row:
                if isinstance(cell, str) and len(cell) > 50:
                    return True
        
        return False
    
    def looks_like_index_table(self, sample, table_name):
        """تحديد إذا كان الجدول يحتوي على فهرس"""
        name_indicators = ['title', 'index', 'fihris', 'tbtitle']
        
        return any(indicator in table_name.lower() for indicator in name_indicators)
    
    def extract_content_from_table(self, cursor, table_name):
        """استخراج المحتوى من جدول"""
        try:
            cursor.execute(f"SELECT * FROM `{table_name}`")
            rows = cursor.fetchall()
            
            # الحصول على أسماء الأعمدة
            column_names = [description[0] for description in cursor.description]
            
            content_data = []
            for i, row in enumerate(rows):
                row_dict = dict(zip(column_names, row))
                
                # البحث عن المحتوى ورقم الصفحة
                content = self.find_content_in_row(row_dict)
                page_num = self.find_page_number_in_row(row_dict, i)
                part = self.find_part_in_row(row_dict)
                
                if content:
                    content_data.append({
                        'page': page_num,
                        'id': page_num,
                        'nass': content,
                        'part': part
                    })
            
            return content_data
            
        except Exception as e:
            print(f"    خطأ في استخراج المحتوى: {str(e)}")
            return []
    
    def extract_index_from_table(self, cursor, table_name):
        """استخراج الفهرس من جدول"""
        try:
            cursor.execute(f"SELECT * FROM `{table_name}`")
            rows = cursor.fetchall()
            
            column_names = [description[0] for description in cursor.description]
            
            index_data = []
            for i, row in enumerate(rows):
                row_dict = dict(zip(column_names, row))
                
                title = self.find_title_in_row(row_dict)
                page_num = self.find_page_number_in_row(row_dict, i)
                level = self.find_level_in_row(row_dict)
                
                if title:
                    index_data.append({
                        'id': page_num,
                        'tit': title,
                        'lvl': level or 1
                    })
            
            return index_data
            
        except Exception as e:
            print(f"    خطأ في استخراج الفهرس: {str(e)}")
            return []
    
    def find_content_in_row(self, row_dict):
        """البحث عن المحتوى في السطر"""
        content_keys = ['nass', 'content', 'text', 'body', 'matn']
        
        for key in content_keys:
            for row_key, value in row_dict.items():
                if key in row_key.lower() and isinstance(value, str) and len(value) > 10:
                    return value.strip()
        
        # البحث عن أطول نص
        longest_text = ""
        for value in row_dict.values():
            if isinstance(value, str) and len(value) > len(longest_text):
                longest_text = value
        
        return longest_text.strip() if len(longest_text) > 10 else None
    
    def find_page_number_in_row(self, row_dict, default_index):
        """البحث عن رقم الصفحة"""
        page_keys = ['page', 'pagenum', 'id', 'num']
        
        for key in page_keys:
            for row_key, value in row_dict.items():
                if key in row_key.lower():
                    try:
                        return int(value)
                    except:
                        pass
        
        return default_index + 1
    
    def find_part_in_row(self, row_dict):
        """البحث عن رقم الجزء"""
        part_keys = ['part', 'volume', 'juz']
        
        for key in part_keys:
            for row_key, value in row_dict.items():
                if key in row_key.lower():
                    try:
                        return int(value)
                    except:
                        pass
        
        return None
    
    def find_title_in_row(self, row_dict):
        """البحث عن العنوان"""
        title_keys = ['title', 'tit', 'name', 'heading']
        
        for key in title_keys:
            for row_key, value in row_dict.items():
                if key in row_key.lower() and isinstance(value, str):
                    return value.strip()
        
        return None
    
    def find_level_in_row(self, row_dict):
        """البحث عن مستوى العنوان"""
        level_keys = ['level', 'lvl', 'depth']
        
        for key in level_keys:
            for row_key, value in row_dict.items():
                if key in row_key.lower():
                    try:
                        return int(value)
                    except:
                        pass
        
        return 1
    
    def try_raw_analysis(self, bok_file):
        """تحليل الملف كنص خام"""
        print("  📄 تحليل الملف كنص خام...")
        
        try:
            with open(bok_file, 'rb') as f:
                data = f.read(10000)  # أول 10KB
            
            # البحث عن نصوص عربية
            text_data = data.decode('utf-8', errors='ignore')
            arabic_chars = sum(1 for c in text_data if '\u0600' <= c <= '\u06FF')
            
            print(f"  📊 وُجد {arabic_chars} حرف عربي في أول 10KB")
            
            if arabic_chars > 100:
                print("  ✅ الملف يحتوي على نصوص عربية")
                return {'analysis': 'contains_arabic', 'arabic_chars': arabic_chars}
            
            return None
            
        except Exception as e:
            print(f"  خطأ في التحليل: {str(e)}")
            return None
    
    def try_powershell_com(self, bok_file):
        """تجربة PowerShell مع COM"""
        print("  🔧 تجربة PowerShell COM...")
        
        try:
            ps_script = Path(__file__).parent / "powershell_extractor.ps1"
            
            if not ps_script.exists():
                print("  ⚠️ سكريبت PowerShell غير موجود")
                return None
            
            # تشغيل PowerShell
            cmd = f'powershell -ExecutionPolicy Bypass -File "{ps_script}" -BokFilePath "{bok_file}"'
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print("  ✅ PowerShell نجح")
                return {'method': 'powershell', 'output': result.stdout}
            else:
                print(f"  ❌ PowerShell فشل: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"  خطأ PowerShell: {str(e)}")
            return None
    
    def show_manual_guide(self, bok_file):
        """عرض دليل التصدير اليدوي"""
        print("  📋 دليل التصدير اليدوي:")
        print("  " + "="*40)
        print("  1. افتح الملف في Microsoft Access")
        print("  2. File > Export > Text File")
        print("  3. صدّر الجداول:")
        print("     - Main/TBMain (المحتوى)")
        print("     - TBTitles (الفهرس)")
        print(f"  4. احفظ في: {self.output_dir}")
        print("  5. استخدم csv_extractor.py")
        print("  " + "="*40)
        
        return {'method': 'manual', 'guide': True}

def main():
    """الوظيفة الرئيسية"""
    import sys
    
    if len(sys.argv) != 2:
        print("الاستخدام: python simple_extractor.py <bok_file>")
        return
    
    bok_file = sys.argv[1]
    
    if not os.path.exists(bok_file):
        print(f"❌ الملف غير موجود: {bok_file}")
        return
    
    print(f"🚀 استخراج البيانات من: {Path(bok_file).name}")
    print("=" * 60)
    
    extractor = SimpleBokExtractor()
    result = extractor.extract_all_methods(bok_file)
    
    if result and result.get('content_data'):
        print(f"\n🎉 نجح الاستخراج!")
        print(f"📄 المحتوى: {len(result['content_data'])} صفحة")
        print(f"📚 الفهرس: {len(result.get('index_data', []))} عنصر")
    else:
        print(f"\n⚠️ الاستخراج التلقائي لم ينجح")
        print("💡 جرب التصدير اليدوي من Access")

if __name__ == "__main__":
    main()
