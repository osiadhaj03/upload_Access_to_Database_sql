#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مثال سريع لاستخدام محول كتب الشاملة
=====================================

هذا المثال يوضح كيفية استخدام السكريبتات بطريقة بسيطة

الاستخدام:
python quick_example.py
"""

from working_shamela_converter import WorkingShamelaConverter
import os

def quick_conversion_example():
    """مثال سريع للتحويل"""
    
    print("=" * 50)
    print("    مثال سريع - محول كتب الشاملة")
    print("=" * 50)
    
    # إعدادات قاعدة البيانات (عدّلها حسب نظامك)
    mysql_config = {
        'host': 'localhost',           # عنوان خادم MySQL
        'port': 3306,                  # منفذ MySQL (افتراضي: 3306)
        'user': 'shamela_user',        # اسم المستخدم
        'password': 'password123',     # كلمة المرور
        'database': 'shamela_books',   # اسم قاعدة البيانات
        'charset': 'utf8mb4',
        'autocommit': False
    }
    
    # ملفات للتحويل (عدّل هذه المسارات)
    access_files = [
        "data/shamela_book.accdb",
        # أضف المزيد من المسارات هنا
        # "path/to/another_book.accdb",
        # "path/to/book.bok",
    ]
    
    # التحقق من وجود الملفات
    existing_files = []
    for file_path in access_files:
        if os.path.exists(file_path):
            existing_files.append(file_path)
            print(f"✅ ملف موجود: {file_path}")
        else:
            print(f"❌ ملف غير موجود: {file_path}")
    
    if not existing_files:
        print("\n❌ لم يتم العثور على أي ملفات للتحويل!")
        print("💡 الرجاء تحديث مسارات الملفات في السكريپت")
        return
    
    # إنشاء المحول
    print(f"\n🔧 إنشاء المحول...")
    converter = WorkingShamelaConverter(mysql_config)
    
    try:
        # الاتصال بقاعدة البيانات
        print("🔌 محاولة الاتصال بقاعدة البيانات...")
        if not converter.connect_mysql():
            print("❌ فشل الاتصال بقاعدة البيانات!")
            print("💡 تأكد من:")
            print("   - تشغيل خدمة MySQL")
            print("   - صحة بيانات الاتصال")
            print("   - وجود قاعدة البيانات")
            return
        
        print("✅ تم الاتصال بقاعدة البيانات بنجاح!")
        
        # تحويل الملفات
        print(f"\n🔄 بدء تحويل {len(existing_files)} ملف...")
        results = converter.convert_multiple_files(existing_files)
        
        # عرض النتائج
        print(f"\n" + "=" * 30)
        print("📊 النتائج النهائية:")
        print("=" * 30)
        print(f"📁 العدد الكلي: {results['total']}")
        print(f"✅ نجح: {len(results['successful'])}")
        print(f"❌ فشل: {len(results['failed'])}")
        
        if results['successful']:
            print(f"\n✅ الملفات التي نجحت:")
            for file in results['successful']:
                print(f"   - {os.path.basename(file)}")
        
        if results['failed']:
            print(f"\n❌ الملفات التي فشلت:")
            for file in results['failed']:
                print(f"   - {os.path.basename(file)}")
        
        print(f"\n🎉 انتهت العملية!")
        
    except Exception as e:
        print(f"❌ خطأ عام: {str(e)}")
    
    finally:
        # إغلاق الاتصالات
        converter.close_connections()
        print("🔌 تم إغلاق الاتصالات")

def setup_mysql_guide():
    """دليل إعداد MySQL"""
    print("\n" + "=" * 50)
    print("📋 دليل إعداد MySQL")
    print("=" * 50)
    print("""
1️⃣ تثبيت MySQL Server (إذا لم يكن مثبتاً):
   - حمّل من: https://dev.mysql.com/downloads/mysql/
   - ثبّت واتبع التعليمات

2️⃣ إنشاء قاعدة البيانات والمستخدم:
   افتح MySQL Command Line أو MySQL Workbench وشغّل:

   CREATE DATABASE shamela_books CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'shamela_user'@'localhost' IDENTIFIED BY 'password123';
   GRANT ALL PRIVILEGES ON shamela_books.* TO 'shamela_user'@'localhost';
   FLUSH PRIVILEGES;

3️⃣ تحديث إعدادات الاتصال في السكريپت:
   عدّل المتغير mysql_config حسب إعداداتك

4️⃣ تشغيل السكريپت:
   python quick_example.py
    """)

if __name__ == "__main__":
    # عرض دليل الإعداد أولاً
    setup_mysql_guide()
    
    # سؤال المستخدم
    response = input("\n❓ هل تريد المتابعة مع التحويل؟ (y/n): ").strip().lower()
    
    if response in ['y', 'yes', 'نعم', 'ن']:
        quick_conversion_example()
    else:
        print("👋 إلى اللقاء!")
