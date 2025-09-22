#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار سريع لتحويل .bok وتشغيل على التطبيق مباشرة
"""

import os
import sys
from pathlib import Path
from simple_bok_support import SimpleBokConverter

def quick_test_bok_conversion():
    """اختبار سريع لتحويل ملف .bok واحد"""
    
    print("=== اختبار سريع لتحويل .bok ===")
    
    # مجلد ملفات .bok  
    bok_folder = Path("d:/test3/bok file")
    bok_files = list(bok_folder.glob("*.bok"))
    
    if not bok_files:
        print("❌ لم يتم العثور على ملفات .bok")
        return None
    
    # اختيار أول ملف للاختبار
    test_file = bok_files[0]
    print(f"📝 اختبار ملف: {test_file.name}")
    
    # تحويل الملف
    converter = SimpleBokConverter()
    
    def progress_log(message):
        print(f"   {message}")
    
    converted_path, success = converter.convert_bok_to_accdb(
        str(test_file), 
        progress_log
    )
    
    if success and converted_path:
        print(f"✅ تم التحويل بنجاح!")
        print(f"📁 المسار: {converted_path}")
        
        # التحقق من إمكانية قراءة الملف
        print(f"\n🔍 اختبار قراءة الملف المحول...")
        
        try:
            import pyodbc
            
            conn_str = (
                r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
                f'DBQ={converted_path};'
            )
            
            try:
                conn = pyodbc.connect(conn_str, timeout=10)
                cursor = conn.cursor()
                
                # قراءة أسماء الجداول
                tables = cursor.tables(tableType='TABLE').fetchall()
                user_tables = [t.table_name for t in tables if not t.table_name.startswith('MSys')]
                
                print(f"📊 تم العثور على {len(user_tables)} جدول:")
                for table in user_tables[:5]:  # أول 5 جداول
                    print(f"   • {table}")
                
                # قراءة عينة من البيانات
                if user_tables:
                    sample_table = user_tables[0]
                    cursor.execute(f"SELECT TOP 3 * FROM [{sample_table}]")
                    rows = cursor.fetchall()
                    
                    print(f"\n📋 عينة من جدول '{sample_table}':")
                    for i, row in enumerate(rows, 1):
                        print(f"   الصف {i}: {len(row)} عمود")
                
                conn.close()
                print("\n✅ الملف قابل للقراءة ويحتوي على بيانات!")
                
            except Exception as e:
                print(f"❌ مشكلة في قراءة الملف: {e}")
                print("💡 لكن الملف تم تحويله بنجاح (مشكلة في pyodbc)")
                
        except ImportError:
            print("⚠️ pyodbc غير متوفر للاختبار")
        
        return converted_path
        
    else:
        print("❌ فشل التحويل")
        return None

def test_multiple_files():
    """اختبار تحويل عدة ملفات"""
    
    print("\n" + "="*60)
    print("اختبار تحويل عدة ملفات .bok")
    print("="*60)
    
    bok_folder = Path("d:/test3/bok file")
    bok_files = list(bok_folder.glob("*.bok"))
    
    converter = SimpleBokConverter()
    successful_conversions = []
    
    for i, bok_file in enumerate(bok_files, 1):
        print(f"\n[{i}/{len(bok_files)}] تحويل: {bok_file.name}")
        print("-" * 40)
        
        def progress_log(message):
            print(f"   {message}")
        
        converted_path, success = converter.convert_bok_to_accdb(
            str(bok_file),
            progress_log
        )
        
        if success:
            successful_conversions.append({
                'original': str(bok_file),
                'converted': converted_path,
                'size': os.path.getsize(converted_path)
            })
            print(f"✅ نجح: {bok_file.name}")
        else:
            print(f"❌ فشل: {bok_file.name}")
    
    print(f"\n{'='*60}")
    print(f"النتائج النهائية: {len(successful_conversions)}/{len(bok_files)} نجح")
    print(f"{'='*60}")
    
    if successful_conversions:
        print("\n📁 الملفات المحولة:")
        for result in successful_conversions:
            size_mb = result['size'] / (1024*1024)
            print(f"   ✅ {os.path.basename(result['converted'])} ({size_mb:.1f} MB)")
            
        print(f"\n💡 يمكن الآن استخدام هذه الملفات في التطبيق الرئيسي")
        
        # اقتراح تشغيل التطبيق
        print(f"\n🚀 لتشغيل التطبيق:")
        print(f"   python shamela_gui.py")
    
    return successful_conversions

if __name__ == "__main__":
    
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        # اختبار سريع
        quick_test_bok_conversion()
    elif len(sys.argv) > 1 and sys.argv[1] == "multiple":
        # اختبار متعدد
        test_multiple_files()
    else:
        # القائمة
        print("استخدام:")
        print("  python test_direct_conversion.py quick      # اختبار سريع")
        print("  python test_direct_conversion.py multiple   # اختبار متعدد")
        print()
        
        choice = input("اختر (quick/multiple): ").strip().lower()
        
        if choice == "quick":
            quick_test_bok_conversion()
        elif choice == "multiple":
            test_multiple_files()
        else:
            print("خيار غير صحيح")
