#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
حل مشكلة Access Driver مع الملفات المحولة
يحاول طرق مختلفة للاتصال بالملفات
"""

import pyodbc
import os
import tempfile
import shutil

def test_access_drivers():
    """اختبار drivers المختلفة المتوفرة"""
    print("🔍 فحص Access Drivers المتوفرة...")
    
    drivers = [d for d in pyodbc.drivers() if 'access' in d.lower() or 'microsoft' in d.lower()]
    
    print(f"📋 العثور على {len(drivers)} driver:")
    for i, driver in enumerate(drivers, 1):
        print(f"   {i}. {driver}")
    
    return drivers

def try_different_connection_methods(file_path):
    """جرب طرق اتصال مختلفة"""
    print(f"\n🔄 اختبار طرق اتصال مختلفة للملف: {os.path.basename(file_path)}")
    
    # قائمة drivers للتجريب
    drivers_to_try = [
        "Microsoft Access Driver (*.mdb, *.accdb)",
        "Microsoft Access Driver (*.mdb)",
        "Driver do Microsoft Access (*.mdb)",
    ]
    
    # طرق connection string مختلفة
    connection_methods = []
    
    for driver in drivers_to_try:
        # الطريقة العادية
        connection_methods.append(f"Driver={{{driver}}};DBQ={file_path};")
        
        # مع extended properties
        connection_methods.append(f"Driver={{{driver}}};DBQ={file_path};ExtendedAnsiSQL=1;")
        
        # مع read only
        connection_methods.append(f"Driver={{{driver}}};DBQ={file_path};ReadOnly=1;")
        
        # مع user admin
        connection_methods.append(f"Driver={{{driver}}};DBQ={file_path};UID=Admin;PWD=;")
    
    successful_methods = []
    
    for i, conn_str in enumerate(connection_methods, 1):
        try:
            print(f"   [{i}/{len(connection_methods)}] جاري الاختبار...")
            
            with pyodbc.connect(conn_str, timeout=5) as conn:
                cursor = conn.cursor()
                
                # اختبار قراءة الجداول
                tables = [table.table_name for table in cursor.tables(tableType='TABLE')]
                tables = [t for t in tables if not t.startswith('MSys')]
                
                print(f"   ✅ نجح! العثور على {len(tables)} جدول")
                successful_methods.append({
                    'connection_string': conn_str,
                    'tables_count': len(tables),
                    'tables': tables[:3]  # أول 3 جداول فقط
                })
                
                return conn_str, tables  # إرجاع أول طريقة ناجحة
                
        except pyodbc.Error as e:
            continue
        except Exception as e:
            continue
    
    print("   ❌ فشلت جميع طرق الاتصال")
    return None, None

def fix_access_file(file_path):
    """محاولة إصلاح ملف Access"""
    print(f"\n🔧 محاولة إصلاح الملف: {os.path.basename(file_path)}")
    
    try:
        # إنشاء نسخة مؤقتة
        temp_dir = tempfile.gettempdir()
        temp_name = f"fixed_{os.path.basename(file_path)}"
        temp_path = os.path.join(temp_dir, temp_name)
        
        # نسخ الملف
        shutil.copy2(file_path, temp_path)
        print(f"📁 تم إنشاء نسخة مؤقتة: {temp_path}")
        
        # محاولة فتح النسخة المؤقتة
        connection_string, tables = try_different_connection_methods(temp_path)
        
        if connection_string:
            print("✅ تم إصلاح الملف!")
            return temp_path, connection_string, tables
        else:
            # حذف النسخة المؤقتة إذا فشلت
            os.remove(temp_path)
            print("❌ فشل في إصلاح الملف")
            return None, None, None
            
    except Exception as e:
        print(f"❌ خطأ في إصلاح الملف: {e}")
        return None, None, None

def create_compatible_access_file(source_file, output_file):
    """إنشاء ملف Access متوافق جديد"""
    print(f"\n🔄 إنشاء ملف متوافق جديد...")
    
    try:
        # محاولة قراءة البيانات من الملف الأصلي
        connection_string, tables = try_different_connection_methods(source_file)
        
        if not connection_string:
            print("❌ لا يمكن قراءة الملف الأصلي")
            return False
        
        print(f"✅ تم قراءة {len(tables)} جدول من الملف الأصلي")
        
        # هنا يمكن إضافة منطق إنشاء ملف جديد
        # لكن هذا يحتاج Access مثبت أو مكتبة أخرى
        
        print("ℹ️ هذه الوظيفة تحتاج تطوير إضافي")
        return False
        
    except Exception as e:
        print(f"❌ خطأ في إنشاء ملف متوافق: {e}")
        return False

def diagnose_access_problems():
    """تشخيص مشاكل Access"""
    print("🔍 تشخيص مشاكل Access...")
    
    # فحص Drivers
    drivers = test_access_drivers()
    
    if not drivers:
        print("❌ لا توجد Access drivers مثبتة!")
        print("💡 الحل: تثبيت Microsoft Access Database Engine")
        return False
    
    # فحص إصدار Python
    import sys
    python_arch = "64-bit" if sys.maxsize > 2**32 else "32-bit"
    print(f"🐍 Python: {python_arch}")
    
    # فحص إصدار Windows  
    import platform
    print(f"🖥️ Windows: {platform.platform()}")
    
    print("\n💡 توصيات الحل:")
    print("1. تثبيت Microsoft Access Database Engine 2016 (نفس معمارية Python)")
    print("2. تجريب تشغيل Python كمدير")
    print("3. استخدام طريقة Access اليدوية للملفات المهمة")
    
    return True

def test_converted_files():
    """اختبار الملفات المحولة"""
    converted_folder = r"d:\test3\converted_books"
    
    if not os.path.exists(converted_folder):
        print("❌ مجلد الملفات المحولة غير موجود")
        return
    
    files = [f for f in os.listdir(converted_folder) if f.endswith('.accdb')]
    
    print(f"\n🔍 اختبار {len(files)} ملف محول...")
    
    successful_files = []
    failed_files = []
    
    for file in files:
        file_path = os.path.join(converted_folder, file)
        print(f"\n--- اختبار: {file} ---")
        
        connection_string, tables = try_different_connection_methods(file_path)
        
        if connection_string:
            successful_files.append({
                'file': file,
                'connection': connection_string,
                'tables': len(tables)
            })
        else:
            failed_files.append(file)
    
    print(f"\n📊 نتائج الاختبار:")
    print(f"✅ نجح: {len(successful_files)}/{len(files)}")
    print(f"❌ فشل: {len(failed_files)}/{len(files)}")
    
    if successful_files:
        print(f"\n✅ الملفات التي تعمل:")
        for item in successful_files:
            print(f"   📁 {item['file']} ({item['tables']} جدول)")
    
    if failed_files:
        print(f"\n❌ الملفات التي تحتاج إصلاح:")
        for file in failed_files:
            print(f"   📁 {file}")
            
        print(f"\n🔧 اقتراحات للملفات الفاشلة:")
        print("1. حاول فتحها في Access وحفظها مرة أخرى")
        print("2. استخدم الملفات الأصلية .bok")
        print("3. جرب تحويل مختلف")

def main():
    """الدالة الرئيسية"""
    print("=== تشخيص وحل مشاكل Access ===")
    print("=" * 40)
    
    # تشخيص عام
    diagnose_access_problems()
    
    # اختبار الملفات المحولة
    test_converted_files()
    
    print(f"\n{'='*40}")
    print("انتهى التشخيص")

if __name__ == "__main__":
    main()
