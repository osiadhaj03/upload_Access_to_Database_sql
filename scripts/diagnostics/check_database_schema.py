#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت فحص بنية قاعدة البيانات
يتحقق من:
1. بنية جدول pages
2. المفاتيح والفهارس
3. القيود الموجودة
4. البيانات الموجودة
"""

import mysql.connector
from mysql.connector import Error
import sys
import os

# إضافة مجلد src للمسار
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'src'))

def check_database_schema():
    """فحص بنية قاعدة البيانات"""
    
    # معلومات الاتصال
    config = {
        'host': 'srv1800.hstgr.io',
        'user': 'u994369532_test',
        'password': 'Test20205',
        'database': 'u994369532_test',
        'charset': 'utf8mb4',
        'use_unicode': True,
        'autocommit': False
    }
    
    try:
        print("🔍 بدء فحص بنية قاعدة البيانات...")
        print("=" * 60)
        
        # الاتصال بقاعدة البيانات
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        # 1. فحص بنية جدول pages
        print("\n📋 1. بنية جدول pages:")
        print("-" * 40)
        cursor.execute("DESCRIBE pages")
        columns = cursor.fetchall()
        
        for column in columns:
            field, type_info, null, key, default, extra = column
            print(f"  {field:20} | {type_info:15} | NULL: {null:3} | Key: {key:3} | Default: {str(default):8} | Extra: {extra}")
        
        # 2. فحص المفاتيح والفهارس
        print("\n🔑 2. المفاتيح والفهارس:")
        print("-" * 40)
        cursor.execute("SHOW INDEX FROM pages")
        indexes = cursor.fetchall()
        
        for index in indexes:
            # التعامل مع عدد مختلف من الأعمدة
            if len(index) >= 11:
                table, non_unique, key_name, seq_in_index, column_name = index[0], index[1], index[2], index[3], index[4]
                index_type = index[10] if len(index) > 10 else "UNKNOWN"
                print(f"  Index: {key_name:30} | Column: {column_name:15} | Unique: {not bool(non_unique):5} | Type: {index_type}")
            else:
                print(f"  فهرس: {index}")
        
        # 3. فحص القيود (Constraints)
        print("\n⚠️  3. القيود الموجودة:")
        print("-" * 40)
        cursor.execute("""
            SELECT 
                CONSTRAINT_NAME,
                CONSTRAINT_TYPE,
                TABLE_NAME,
                COLUMN_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
            WHERE TABLE_SCHEMA = 'u994369532_test' 
            AND TABLE_NAME = 'pages'
            ORDER BY CONSTRAINT_NAME
        """)
        constraints = cursor.fetchall()
        
        for constraint in constraints:
            constraint_name, constraint_type, table_name, column_name = constraint
            print(f"  {constraint_name:40} | Type: {constraint_type:10} | Column: {column_name}")
        
        # 4. فحص القيود الفريدة بالتفصيل
        print("\n🚫 4. القيود الفريدة (UNIQUE Constraints):")
        print("-" * 40)
        cursor.execute("""
            SELECT 
                tc.CONSTRAINT_NAME,
                GROUP_CONCAT(kcu.COLUMN_NAME ORDER BY kcu.ORDINAL_POSITION) as columns
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu 
                ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME 
                AND tc.TABLE_SCHEMA = kcu.TABLE_SCHEMA
            WHERE tc.TABLE_SCHEMA = 'u994369532_test' 
            AND tc.TABLE_NAME = 'pages'
            AND tc.CONSTRAINT_TYPE = 'UNIQUE'
            GROUP BY tc.CONSTRAINT_NAME
        """)
        unique_constraints = cursor.fetchall()
        
        for constraint in unique_constraints:
            constraint_name, columns = constraint
            print(f"  {constraint_name:40} | Columns: {columns}")
        
        # 5. إحصائيات البيانات
        print("\n📊 5. إحصائيات البيانات:")
        print("-" * 40)
        
        # عدد الصفحات الإجمالي
        cursor.execute("SELECT COUNT(*) FROM pages")
        total_pages = cursor.fetchone()[0]
        print(f"  إجمالي الصفحات: {total_pages}")
        
        # عدد الكتب
        cursor.execute("SELECT COUNT(DISTINCT book_id) FROM pages")
        total_books = cursor.fetchone()[0]
        print(f"  عدد الكتب: {total_books}")
        
        # فحص القيم المكررة في page_number
        cursor.execute("""
            SELECT book_id, page_number, COUNT(*) as count
            FROM pages 
            GROUP BY book_id, page_number 
            HAVING COUNT(*) > 1
            ORDER BY count DESC
            LIMIT 10
        """)
        duplicates = cursor.fetchall()
        
        if duplicates:
            print(f"\n  ⚠️ وجدت قيم مكررة في page_number:")
            for dup in duplicates:
                book_id, page_number, count = dup
                print(f"    الكتاب {book_id}, الصفحة {page_number}: {count} مرات")
        else:
            print("  ✅ لا توجد قيم مكررة في page_number")
        
        # فحص internal_index
        cursor.execute("SELECT MIN(internal_index), MAX(internal_index), COUNT(DISTINCT internal_index) FROM pages WHERE internal_index IS NOT NULL")
        result = cursor.fetchone()
        if result and result[0] is not None:
            min_internal, max_internal, distinct_count = result
            print(f"  internal_index: من {min_internal} إلى {max_internal} ({distinct_count} قيمة مختلفة)")
        else:
            print("  ⚠️ internal_index غير موجود أو فارغ")
        
        # 6. فحص بيانات الكتاب رقم 94 (المشكلة الحالية)
        print("\n🔍 6. فحص بيانات الكتاب رقم 94:")
        print("-" * 40)
        cursor.execute("SELECT COUNT(*) FROM pages WHERE book_id = 94")
        book_94_count = cursor.fetchone()[0]
        print(f"  عدد صفحات الكتاب 94: {book_94_count}")
        
        if book_94_count > 0:
            cursor.execute("""
                SELECT page_number, COUNT(*) as count
                FROM pages 
                WHERE book_id = 94
                GROUP BY page_number 
                HAVING COUNT(*) > 1
                ORDER BY count DESC
                LIMIT 5
            """)
            book_94_dups = cursor.fetchall()
            
            if book_94_dups:
                print("  ⚠️ صفحات مكررة في الكتاب 94:")
                for dup in book_94_dups:
                    page_num, count = dup
                    print(f"    الصفحة {page_num}: {count} مرات")
            
            # عرض بعض الصفحات
            cursor.execute("""
                SELECT id, internal_index, page_number 
                FROM pages 
                WHERE book_id = 94 
                ORDER BY id
                LIMIT 10
            """)
            sample_pages = cursor.fetchall()
            
            print("  عينة من الصفحات:")
            for page in sample_pages:
                page_id, internal_idx, page_num = page
                print(f"    ID: {page_id}, internal_index: {internal_idx}, page_number: {page_num}")
        
        print("\n" + "=" * 60)
        print("✅ انتهى فحص قاعدة البيانات")
        
    except Error as e:
        print(f"❌ خطأ في الاتصال بقاعدة البيانات: {e}")
        return False
    
    except Exception as e:
        print(f"❌ خطأ عام: {e}")
        return False
    
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
    
    return True

if __name__ == "__main__":
    print("🚀 سكريبت فحص بنية قاعدة البيانات")
    print("=" * 60)
    
    success = check_database_schema()
    
    if success:
        print("\n✅ تم الفحص بنجاح!")
    else:
        print("\n❌ فشل في الفحص!")
    
    input("\nاضغط Enter للخروج...")
