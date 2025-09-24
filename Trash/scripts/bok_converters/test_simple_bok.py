#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار Simple BOK Support
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

def test_simple_bok():
    try:
        from Trash.simple_bok_support import SimpleBokConverter
        
        bok_file = r"d:\test3\bok file\بغية السائل.bok"
        print(f"🔍 اختبار ملف: {bok_file}")
        
        converter = SimpleBokConverter()
        
        # تحويل .bok إلى .accdb أولاً
        print("🔄 تحويل .bok إلى .accdb...")
        accdb_file = converter.convert_bok_to_accdb(bok_file)
        
        if accdb_file and os.path.exists(accdb_file):
            print(f"✅ تم التحويل: {accdb_file}")
            
            # الآن نحاول قراءة البيانات
            print("📖 قراءة البيانات...")
            
            # استخدام شاميلا كونفيرتر لقراءة البيانات
            from shamela_converter import ShamelaConverter
            shamela_converter = ShamelaConverter()
            
            # محاولة الاتصال بـ accdb
            import pyodbc
            conn_str = f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={accdb_file};"
            
            try:
                conn = pyodbc.connect(conn_str)
                cursor = conn.cursor()
                
                # الحصول على قائمة الجداول
                cursor.execute("SELECT name FROM MSysObjects WHERE type=1 AND name NOT LIKE 'MSys*'")
                tables = cursor.fetchall()
                
                print(f"📋 وُجد {len(tables)} جدول:")
                for table in tables:
                    print(f"  - {table[0]}")
                
                conn.close()
                return True
                
            except Exception as pyodbc_error:
                print(f"❌ خطأ pyodbc: {str(pyodbc_error)}")
                return False
        else:
            print("❌ فشل التحويل")
            return False
            
    except Exception as e:
        print(f"❌ خطأ: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 اختبار Simple BOK Support")
    print("=" * 50)
    
    success = test_simple_bok()
    
    if not success:
        print("\n💡 بدائل متاحة:")
        print("1. التصدير اليدوي من Access")
        print("2. PowerShell COM (بعد إصلاح السكريبت)")
        print("3. استخدام mdb-tools في WSL")
    
    input("\nاضغط Enter للخروج...")
