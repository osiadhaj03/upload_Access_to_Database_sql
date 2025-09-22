#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
استخراج مباشر من ملف .bok المحول
"""

import pyodbc
import json
import os
from pathlib import Path

def extract_from_converted_bok():
    """استخراج البيانات من ملف .bok محول"""
    
    # مسار الملف المحول
    converted_file = r"d:\temp\shamela_ultimate_simple\بغية السائل_ultimate.accdb"
    
    if not os.path.exists(converted_file):
        print("❌ الملف المحول غير موجود")
        print("💡 شغّل التحويل أولاً باستخدام simple_bok_support")
        return False
    
    print(f"🔍 قراءة: {converted_file}")
    
    # تجربة connection strings مختلفة
    connection_strings = [
        f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={converted_file};",
        f"DRIVER={{Microsoft Access Driver (*.mdb)}};DBQ={converted_file};",
        f"DRIVER={{Microsoft Access Driver}};DBQ={converted_file};",
    ]
    
    for i, conn_str in enumerate(connection_strings, 1):
        try:
            print(f"🔗 تجربة اتصال {i}...")
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            
            # الحصول على الجداول
            cursor.execute("SELECT name FROM MSysObjects WHERE type=1 AND name NOT LIKE 'MSys*'")
            tables = cursor.fetchall()
            
            print(f"✅ اتصال نجح! وُجد {len(tables)} جدول:")
            
            for table in tables:
                table_name = table[0]
                print(f"  📋 {table_name}")
                
                # عد السجلات
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM [{table_name}]")
                    count = cursor.fetchone()[0]
                    print(f"    📊 {count} سجل")
                    
                    # عينة من البيانات
                    if count > 0:
                        cursor.execute(f"SELECT * FROM [{table_name}] LIMIT 3")
                        columns = [desc[0] for desc in cursor.description]
                        rows = cursor.fetchmany(3)
                        
                        print(f"    🗂️ الأعمدة: {', '.join(columns)}")
                        
                        for j, row in enumerate(rows, 1):
                            print(f"    📄 السجل {j}: {dict(zip(columns, row))}")
                    
                except Exception as table_error:
                    print(f"    ❌ خطأ في قراءة الجدول: {str(table_error)}")
            
            conn.close()
            return True
            
        except Exception as conn_error:
            print(f"  ❌ فشل الاتصال {i}: {str(conn_error)[:100]}...")
    
    print("❌ فشلت جميع محاولات الاتصال")
    return False

def find_converted_files():
    """البحث عن الملفات المحولة"""
    
    possible_locations = [
        r"d:\temp\shamela_ultimate_simple",
        r"C:\temp\shamela_ultimate_simple", 
        r"d:\test3\temp",
        r"d:\test3\data"
    ]
    
    print("🔍 البحث عن الملفات المحولة...")
    
    for location in possible_locations:
        if os.path.exists(location):
            files = list(Path(location).glob("*.accdb"))
            if files:
                print(f"📁 وُجد في {location}:")
                for file in files:
                    print(f"  📄 {file.name} ({file.stat().st_size:,} بايت)")
                return files
    
    print("❌ لم توجد ملفات محولة")
    return []

def main():
    print("🚀 استخراج البيانات من ملف .bok محول")
    print("=" * 50)
    
    # البحث عن الملفات المحولة
    converted_files = find_converted_files()
    
    if not converted_files:
        print("\n💡 للحصول على ملف محول:")
        print("1. شغّل: python src/simple_bok_support.py")
        print("2. أو استخدم PowerShell: extract_bok.ps1")
        print("3. أو التصدير اليدوي من Access")
        return
    
    # جرب استخراج البيانات
    success = extract_from_converted_bok()
    
    if not success:
        print("\n💡 بدائل:")
        print("1. شغّل PowerShell: extract_bok.ps1")
        print("2. التصدير اليدوي لـ CSV")

if __name__ == "__main__":
    main()
    input("\nاضغط Enter للخروج...")
