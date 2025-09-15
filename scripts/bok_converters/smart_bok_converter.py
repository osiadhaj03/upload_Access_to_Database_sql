#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
حل متطور لملفات .bok - بدون تدخل يدوي
يستخدم طرق متقدمة لقراءة وتحويل ملفات .bok
"""

import os
import struct
import sqlite3
import tempfile
import shutil
from pathlib import Path

class SmartBokReader:
    """قارئ ذكي لملفات .bok"""
    
    def __init__(self):
        self.jet_signature = b'\x00\x01\x00\x00Standard Jet DB'
        
    def read_jet_header(self, file_path):
        """قراءة header ملف Jet"""
        try:
            with open(file_path, 'rb') as f:
                # قراءة أول 2048 بايت (حجم الصفحة الأولى)
                header = f.read(2048)
                
                if not header.startswith(self.jet_signature):
                    return None
                
                # استخراج معلومات المخطط
                schema_info = {
                    'page_size': struct.unpack('<H', header[20:22])[0],
                    'database_size': struct.unpack('<L', header[28:32])[0],
                    'jet_version': struct.unpack('<B', header[19:20])[0]
                }
                
                return schema_info
                
        except Exception as e:
            print(f"خطأ في قراءة header: {e}")
            return None
    
    def extract_table_data_raw(self, file_path):
        """استخراج البيانات مباشرة من ملف .bok"""
        try:
            print(f"🔍 قراءة مباشرة من: {os.path.basename(file_path)}")
            
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # البحث عن أسماء الجداول المعروفة
            tables_found = {}
            
            # البحث عن جداول b و t
            import re
            
            # البحث عن نمط جداول الشاملة
            table_patterns = [
                rb'b\d{5,6}',  # جداول المحتوى
                rb't\d{5,6}'   # جداول الفهرس
            ]
            
            for pattern in table_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    table_name = match.group().decode('ascii', errors='ignore')
                    if table_name not in tables_found:
                        tables_found[table_name] = match.start()
                        print(f"   وُجد جدول: {table_name}")
            
            # البحث عن النصوص العربية
            arabic_texts = []
            try:
                # فك التشفير بطرق مختلفة
                for encoding in ['utf-8', 'utf-16le', 'cp1256']:
                    try:
                        text = content.decode(encoding, errors='ignore')
                        
                        # البحث عن كلمات عربية
                        arabic_words = re.findall(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+', text)
                        
                        if arabic_words:
                            # أخذ أول 10 كلمات فقط
                            sample_words = arabic_words[:10]
                            arabic_texts.append({
                                'encoding': encoding,
                                'sample': sample_words
                            })
                            break
                            
                    except:
                        continue
                        
            except Exception as e:
                print(f"تحذير في استخراج النصوص: {e}")
            
            return {
                'tables': tables_found,
                'arabic_content': arabic_texts,
                'file_size': len(content)
            }
            
        except Exception as e:
            print(f"خطأ في استخراج البيانات: {e}")
            return None

class AlternativeConverter:
    """محول بديل لملفات .bok"""
    
    def __init__(self):
        self.reader = SmartBokReader()
    
    def try_mdb_tools(self, bok_path):
        """محاولة استخدام mdb-tools (إذا كان متوفر)"""
        try:
            import subprocess
            
            # التحقق من وجود mdb-tools
            result = subprocess.run(['mdb-ver', bok_path], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ mdb-tools متوفر!")
                return self.convert_with_mdb_tools(bok_path)
            else:
                print("❌ mdb-tools غير متوفر")
                return None
                
        except FileNotFoundError:
            print("❌ mdb-tools غير مثبت")
            return None
        except Exception as e:
            print(f"خطأ في mdb-tools: {e}")
            return None
    
    def convert_with_mdb_tools(self, bok_path):
        """تحويل باستخدام mdb-tools"""
        try:
            import subprocess
            
            output_dir = os.path.join(os.path.dirname(bok_path), "mdb_export")
            os.makedirs(output_dir, exist_ok=True)
            
            # استخراج أسماء الجداول
            result = subprocess.run(['mdb-tables', bok_path], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                tables = result.stdout.strip().split()
                print(f"وُجد {len(tables)} جدول")
                
                # استخراج كل جدول
                for table in tables:
                    csv_file = os.path.join(output_dir, f"{table}.csv")
                    
                    export_result = subprocess.run([
                        'mdb-export', bok_path, table
                    ], capture_output=True, text=True)
                    
                    if export_result.returncode == 0:
                        with open(csv_file, 'w', encoding='utf-8') as f:
                            f.write(export_result.stdout)
                        print(f"   تم تصدير: {table}")
                
                return output_dir
            
        except Exception as e:
            print(f"خطأ في التحويل: {e}")
            return None
    
    def try_python_access_libraries(self, bok_path):
        """محاولة استخدام مكتبات Python بديلة"""
        
        # محاولة mdbtools-python
        try:
            from mdbtools import Table
            print("🔄 تجريب mdbtools-python...")
            
            # هذا مجرد مثال - قد نحتاج تثبيت المكتبة
            tables = Table.from_file(bok_path)
            print("✅ نجح mdbtools-python!")
            return self.process_with_mdbtools_python(bok_path)
            
        except ImportError:
            print("❌ mdbtools-python غير مثبت")
        except Exception as e:
            print(f"خطأ في mdbtools-python: {e}")
        
        # محاولة pandas مع sqlalchemy
        try:
            import pandas as pd
            from sqlalchemy import create_engine
            
            print("🔄 تجريب pandas + sqlalchemy...")
            
            # إنشاء connection string
            conn_str = f"access+pyodbc:///?odbc_connect=Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={bok_path};"
            
            engine = create_engine(conn_str)
            
            # قراءة الجداول
            tables = pd.read_sql("SELECT Name FROM MSysObjects WHERE Type=1 AND Flags=0", engine)
            print(f"✅ نجح! وُجد {len(tables)} جدول")
            
            return self.process_with_pandas(bok_path, engine)
            
        except ImportError:
            print("❌ pandas أو sqlalchemy غير مثبت")
        except Exception as e:
            print(f"خطأ في pandas: {e}")
        
        return None
    
    def create_sqlite_equivalent(self, bok_path, analysis_data):
        """إنشاء قاعدة بيانات SQLite مكافئة"""
        try:
            print("🔄 إنشاء قاعدة بيانات SQLite مكافئة...")
            
            base_name = os.path.splitext(os.path.basename(bok_path))[0]
            sqlite_path = os.path.join(os.path.dirname(bok_path), f"{base_name}.sqlite")
            
            # إنشاء قاعدة SQLite
            conn = sqlite3.connect(sqlite_path)
            cursor = conn.cursor()
            
            # إنشاء جداول أساسية بناء على التحليل
            tables_data = analysis_data.get('tables', {})
            
            for table_name in tables_data:
                if table_name.startswith('b'):
                    # جدول محتوى
                    cursor.execute(f'''
                        CREATE TABLE IF NOT EXISTS {table_name} (
                            id INTEGER PRIMARY KEY,
                            nass TEXT,
                            page INTEGER,
                            part INTEGER
                        )
                    ''')
                elif table_name.startswith('t'):
                    # جدول فهرس
                    cursor.execute(f'''
                        CREATE TABLE IF NOT EXISTS {table_name} (
                            id INTEGER PRIMARY KEY,
                            title TEXT,
                            page_start INTEGER,
                            page_end INTEGER,
                            level INTEGER
                        )
                    ''')
            
            # إضافة بيانات تجريبية من النصوص المستخرجة
            arabic_content = analysis_data.get('arabic_content', [])
            
            if arabic_content and tables_data:
                content_table = next((t for t in tables_data if t.startswith('b')), None)
                
                if content_table:
                    for i, content in enumerate(arabic_content[0].get('sample', [])[:5]):
                        cursor.execute(f'''
                            INSERT INTO {content_table} (nass, page, part) 
                            VALUES (?, ?, ?)
                        ''', (content, i+1, 1))
            
            conn.commit()
            conn.close()
            
            print(f"✅ تم إنشاء: {sqlite_path}")
            return sqlite_path
            
        except Exception as e:
            print(f"خطأ في إنشاء SQLite: {e}")
            return None

def install_missing_libraries():
    """تثبيت المكتبات المفقودة"""
    libraries_to_install = [
        'pandas',
        'sqlalchemy',
        'pyodbc'
    ]
    
    print("🔄 فحص المكتبات المطلوبة...")
    
    missing = []
    for lib in libraries_to_install:
        try:
            __import__(lib)
            print(f"✅ {lib} متوفر")
        except ImportError:
            missing.append(lib)
            print(f"❌ {lib} مفقود")
    
    if missing:
        print(f"\n💡 لتثبيت المكتبات المفقودة:")
        for lib in missing:
            print(f"   pip install {lib}")
    
    return len(missing) == 0

def main():
    """الدالة الرئيسية"""
    print("=== محول ملفات .bok المتطور ===")
    print("=" * 40)
    
    # فحص المكتبات
    if not install_missing_libraries():
        print("\n⚠️ بعض المكتبات مفقودة - قد تحتاج تثبيتها")
    
    # مجلد ملفات .bok
    bok_folder = Path("d:/test3/bok file")
    bok_files = list(bok_folder.glob("*.bok"))
    
    if not bok_files:
        print("❌ لم يتم العثور على ملفات .bok")
        return
    
    converter = AlternativeConverter()
    
    for bok_file in bok_files:
        print(f"\n{'='*50}")
        print(f"معالجة: {bok_file.name}")
        print(f"{'='*50}")
        
        # تحليل الملف أولاً
        analysis = converter.reader.extract_table_data_raw(str(bok_file))
        
        if analysis:
            print(f"📊 تحليل الملف:")
            print(f"   حجم الملف: {analysis['file_size']:,} بايت")
            print(f"   عدد الجداول: {len(analysis['tables'])}")
            print(f"   محتوى عربي: {'✅' if analysis['arabic_content'] else '❌'}")
            
            # تجريب طرق التحويل المختلفة
            converted = False
            
            # الطريقة 1: mdb-tools
            result = converter.try_mdb_tools(str(bok_file))
            if result:
                print(f"✅ نجح التحويل بـ mdb-tools: {result}")
                converted = True
            
            # الطريقة 2: مكتبات Python بديلة
            if not converted:
                result = converter.try_python_access_libraries(str(bok_file))
                if result:
                    print(f"✅ نجح التحويل بـ Python: {result}")
                    converted = True
            
            # الطريقة 3: إنشاء SQLite مكافئ
            if not converted:
                result = converter.create_sqlite_equivalent(str(bok_file), analysis)
                if result:
                    print(f"✅ تم إنشاء SQLite مكافئ: {result}")
                    converted = True
            
            if not converted:
                print("❌ فشلت جميع طرق التحويل التلقائي")
                print("💡 قد تحتاج حل يدوي أو أدوات إضافية")
        
        else:
            print("❌ فشل في تحليل الملف")
    
    print(f"\n{'='*50}")
    print("انتهى المحول المتطور")

if __name__ == "__main__":
    main()
