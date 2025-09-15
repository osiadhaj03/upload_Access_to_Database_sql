#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت اختبار اتصال قاعدة البيانات
Test Database Connection Script
"""

import mysql.connector
import json
import os
from pathlib import Path

def test_database_connection():
    """
    اختبار اتصال قاعدة البيانات باستخدام الإعدادات المحفوظة
    """
    print("🔍 بدء اختبار اتصال قاعدة البيانات...")
    print("=" * 50)
    
    # قراءة إعدادات قاعدة البيانات
    db_settings_file = "db_settings.json"
    
    if os.path.exists(db_settings_file):
        try:
            with open(db_settings_file, 'r', encoding='utf-8') as f:
                db_config = json.load(f)
            print(f"✅ تم تحميل إعدادات قاعدة البيانات من {db_settings_file}")
        except Exception as e:
            print(f"❌ خطأ في قراءة ملف الإعدادات: {e}")
            return False
    else:
        # استخدام الإعدادات الافتراضية
        db_config = {
            'host': 'srv1800.hstgr.io',
            'port': 3306,
            'database': 'u994369532_test',
            'user': 'u994369532_test',
            'password': 'Test20205'
        }
        print("⚠️ لم يتم العثور على ملف الإعدادات، استخدام الإعدادات الافتراضية")
    
    # عرض معلومات الاتصال (بدون كلمة المرور)
    print("\n📋 معلومات الاتصال:")
    print(f"   الخادم: {db_config['host']}")
    print(f"   المنفذ: {db_config['port']}")
    print(f"   قاعدة البيانات: {db_config['database']}")
    print(f"   المستخدم: {db_config['user']}")
    print(f"   كلمة المرور: {'*' * len(str(db_config.get('password', '')))}")
    
    # محاولة الاتصال
    print("\n🔗 محاولة الاتصال...")
    
    try:
        # إنشاء الاتصال
        connection = mysql.connector.connect(
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password'],
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci',
            autocommit=True,
            connect_timeout=10
        )
        
        if connection.is_connected():
            print("✅ تم الاتصال بقاعدة البيانات بنجاح!")
            
            # الحصول على معلومات الخادم
            cursor = connection.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
            print(f"📊 إصدار MySQL: {version}")
            
            # اختبار الجداول الموجودة
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print(f"📋 عدد الجداول الموجودة: {len(tables)}")
            
            if tables:
                print("   الجداول الموجودة:")
                for table in tables[:10]:  # عرض أول 10 جداول فقط
                    print(f"   - {table[0]}")
                if len(tables) > 10:
                    print(f"   ... و {len(tables) - 10} جدول آخر")
            
            # اختبار إنشاء جدول تجريبي
            test_table_name = "test_connection_table"
            try:
                cursor.execute(f"""
                    CREATE TABLE IF NOT EXISTS {test_table_name} (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        test_message VARCHAR(255),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                print(f"✅ تم إنشاء الجدول التجريبي: {test_table_name}")
                
                # إدراج بيانات تجريبية
                cursor.execute(f"""
                    INSERT INTO {test_table_name} (test_message) 
                    VALUES ('اختبار الاتصال - تم بنجاح')
                """)
                print("✅ تم إدراج البيانات التجريبية")
                
                # قراءة البيانات
                cursor.execute(f"SELECT * FROM {test_table_name} ORDER BY id DESC LIMIT 1")
                result = cursor.fetchone()
                if result:
                    print(f"✅ تم قراءة البيانات: {result}")
                
                # حذف الجدول التجريبي
                cursor.execute(f"DROP TABLE {test_table_name}")
                print(f"🗑️ تم حذف الجدول التجريبي: {test_table_name}")
                
            except Exception as e:
                print(f"⚠️ تحذير في اختبار العمليات: {e}")
            
            cursor.close()
            connection.close()
            print("\n🎉 اختبار الاتصال مكتمل بنجاح!")
            return True
            
    except mysql.connector.Error as e:
        print(f"❌ خطأ في الاتصال بقاعدة البيانات:")
        print(f"   رمز الخطأ: {e.errno}")
        print(f"   رسالة الخطأ: {e.msg}")
        
        # تحليل أنواع الأخطاء الشائعة
        if e.errno == 1045:
            print("\n💡 حلول مقترحة لخطأ المصادقة (1045):")
            print("   1. تحقق من اسم المستخدم وكلمة المرور")
            print("   2. تأكد من أن المستخدم له صلاحيات الوصول")
            print("   3. تحقق من عنوان IP المسموح له بالاتصال")
        elif e.errno == 2003:
            print("\n💡 حلول مقترحة لخطأ الاتصال (2003):")
            print("   1. تحقق من عنوان الخادم والمنفذ")
            print("   2. تأكد من أن الخادم يعمل")
            print("   3. تحقق من إعدادات الجدار الناري")
        elif e.errno == 1049:
            print("\n💡 حلول مقترحة لخطأ قاعدة البيانات (1049):")
            print("   1. تحقق من اسم قاعدة البيانات")
            print("   2. تأكد من وجود قاعدة البيانات على الخادم")
        
        return False
        
    except Exception as e:
        print(f"❌ خطأ عام: {e}")
        return False
    
    print("=" * 50)

if __name__ == "__main__":
    success = test_database_connection()
    if success:
        print("\n🎯 النتيجة: الاتصال يعمل بشكل مثالي!")
    else:
        print("\n⚠️ النتيجة: يوجد مشكلة في الاتصال تحتاج إلى حل.")
    
    input("\nاضغط Enter للخروج...")