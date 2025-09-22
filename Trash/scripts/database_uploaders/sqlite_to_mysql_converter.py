#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
محول قواعد بيانات SQLite المستخرجة إلى MySQL
يأخذ قواعد البيانات المحولة ويرفعها للنظام الرئيسي
"""

import sqlite3
import mysql.connector
import os
from pathlib import Path

class SQLiteToMySQLConverter:
    """محول من SQLite إلى MySQL"""
    
    def __init__(self, mysql_config):
        self.mysql_config = mysql_config
        self.mysql_conn = None
    
    def connect_mysql(self):
        """الاتصال بـ MySQL"""
        try:
            self.mysql_conn = mysql.connector.connect(**self.mysql_config)
            print("✅ تم الاتصال بـ MySQL بنجاح")
            return True
        except Exception as e:
            print(f"❌ خطأ في الاتصال بـ MySQL: {e}")
            return False
    
    def read_sqlite_data(self, sqlite_path):
        """قراءة البيانات من ملف SQLite"""
        try:
            conn = sqlite3.connect(sqlite_path)
            cursor = conn.cursor()
            
            # قراءة معلومات الكتاب
            cursor.execute("SELECT * FROM book_info LIMIT 1")
            book_info = cursor.fetchone()
            
            if not book_info:
                print("❌ لا توجد معلومات كتاب")
                return None
            
            # استخراج أسماء الجداول
            content_table = book_info[4]  # content_table
            index_table = book_info[5]    # index_table
            
            # قراءة المحتوى
            cursor.execute(f"SELECT * FROM {content_table}")
            content_data = cursor.fetchall()
            
            # قراءة الفهرس
            cursor.execute(f"SELECT * FROM {index_table}")
            index_data = cursor.fetchall()
            
            conn.close()
            
            return {
                'book_info': {
                    'title': book_info[1],
                    'author': book_info[2],
                    'total_pages': book_info[3]
                },
                'content': content_data,
                'index': index_data,
                'tables': {
                    'content': content_table,
                    'index': index_table
                }
            }
            
        except Exception as e:
            print(f"❌ خطأ في قراءة SQLite: {e}")
            return None
    
    def insert_book_to_mysql(self, book_data, callback=None):
        """إدراج الكتاب في MySQL"""
        try:
            if not self.mysql_conn:
                print("❌ لا يوجد اتصال MySQL")
                return False
            
            cursor = self.mysql_conn.cursor()
            
            # إدراج معلومات الكتاب
            book_info = book_data['book_info']
            
            if callback:
                callback(f"إدراج كتاب: {book_info['title']}")
            
            cursor.execute("""
                INSERT INTO books (title, author, year, description, page_count, part_count)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                book_info['title'],
                book_info['author'],
                2024,  # سنة افتراضية
                f"كتاب محول من ملف .bok",
                book_info['total_pages'],
                1  # جزء واحد افتراضي
            ))
            
            book_id = cursor.lastrowid
            
            if callback:
                callback(f"تم إنشاء كتاب برقم: {book_id}")
            
            # إنشاء مجلد افتراضي
            cursor.execute("""
                INSERT INTO folders (name, parent_id, description)
                VALUES (%s, %s, %s)
            """, (f"مجلد {book_info['title']}", None, "مجلد تلقائي"))
            
            folder_id = cursor.lastrowid
            
            # إدراج الفصول
            chapters_inserted = 0
            for chapter_data in book_data['index']:
                try:
                    cursor.execute("""
                        INSERT INTO chapters (book_id, folder_id, title, page_start, page_end, chapter_order)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        book_id,
                        folder_id,
                        chapter_data[1],  # title
                        chapter_data[2],  # page_start
                        chapter_data[3],  # page_end
                        chapter_data[0]   # id as order
                    ))
                    chapters_inserted += 1
                except Exception as e:
                    if callback:
                        callback(f"تحذير: فشل إدراج فصل {chapter_data[1]}: {str(e)}")
            
            if callback:
                callback(f"تم إدراج {chapters_inserted} فصل")
            
            # إدراج الصفحات
            pages_inserted = 0
            failed_pages = 0
            
            for page_data in book_data['content']:
                try:
                    cursor.execute("""
                        INSERT INTO pages (book_id, page_number, content, part_number)
                        VALUES (%s, %s, %s, %s)
                    """, (
                        book_id,
                        page_data[2],  # page
                        page_data[1],  # nass (content)
                        page_data[3] if len(page_data) > 3 else 1  # part
                    ))
                    pages_inserted += 1
                    
                    # تحديث التقدم كل 100 صفحة
                    if pages_inserted % 100 == 0 and callback:
                        callback(f"تم إدراج {pages_inserted} صفحة...")
                        
                except mysql.connector.Error as e:
                    if "Duplicate entry" in str(e):
                        failed_pages += 1
                        continue
                    else:
                        raise e
            
            if callback:
                callback(f"تم إدراج {pages_inserted} صفحة")
                if failed_pages > 0:
                    callback(f"تحذير: فشل {failed_pages} صفحة (صفحات مكررة)")
            
            # تحديث إحصائيات الكتاب
            cursor.execute("""
                UPDATE books SET page_count = %s WHERE id = %s
            """, (pages_inserted, book_id))
            
            self.mysql_conn.commit()
            
            if callback:
                callback(f"✅ تم تحويل الكتاب بنجاح!")
                callback(f"   معرف الكتاب: {book_id}")
                callback(f"   الصفحات: {pages_inserted}")
                callback(f"   الفصول: {chapters_inserted}")
            
            return True
            
        except Exception as e:
            if callback:
                callback(f"❌ خطأ في إدراج الكتاب: {str(e)}")
            
            if self.mysql_conn:
                self.mysql_conn.rollback()
            
            return False
    
    def convert_sqlite_file(self, sqlite_path, callback=None):
        """تحويل ملف SQLite واحد"""
        if callback:
            callback(f"🔄 بدء تحويل: {os.path.basename(sqlite_path)}")
        
        # قراءة البيانات
        book_data = self.read_sqlite_data(sqlite_path)
        
        if not book_data:
            if callback:
                callback("❌ فشل في قراءة البيانات")
            return False
        
        if callback:
            callback(f"✅ تم قراءة البيانات:")
            callback(f"   العنوان: {book_data['book_info']['title'][:50]}...")
            callback(f"   المحتوى: {len(book_data['content'])} صفحة")
            callback(f"   الفهرس: {len(book_data['index'])} فصل")
        
        # إدراج في MySQL
        return self.insert_book_to_mysql(book_data, callback)
    
    def batch_convert_sqlite_files(self, sqlite_folder, callback=None):
        """تحويل جميع ملفات SQLite في مجلد"""
        sqlite_files = list(Path(sqlite_folder).glob("*.db"))
        
        if not sqlite_files:
            if callback:
                callback("❌ لم يتم العثور على ملفات SQLite")
            return []
        
        if callback:
            callback(f"🔍 تم العثور على {len(sqlite_files)} ملف SQLite")
        
        successful_conversions = []
        
        for i, sqlite_file in enumerate(sqlite_files, 1):
            if callback:
                callback(f"\n{'='*50}")
                callback(f"[{i}/{len(sqlite_files)}] معالجة: {sqlite_file.name}")
                callback(f"{'='*50}")
            
            success = self.convert_sqlite_file(str(sqlite_file), callback)
            
            if success:
                successful_conversions.append(str(sqlite_file))
                if callback:
                    callback(f"✅ نجح تحويل {sqlite_file.name}")
            else:
                if callback:
                    callback(f"❌ فشل تحويل {sqlite_file.name}")
        
        if callback:
            callback(f"\n🎉 النتائج النهائية:")
            callback(f"   نجح: {len(successful_conversions)}/{len(sqlite_files)}")
        
        return successful_conversions

def main():
    """الدالة الرئيسية"""
    print("=== محول SQLite إلى MySQL ===")
    print("=" * 35)
    
    # إعدادات MySQL
    mysql_config = {
        'host': 'srv1800.hstgr.io',
        'port': 3306,
        'database': 'u994369532_test',
        'user': 'u994369532_shamela',
        'password': 'mT8$pR3@vK9#'
    }
    
    # إنشاء المحول
    converter = SQLiteToMySQLConverter(mysql_config)
    
    # الاتصال بـ MySQL
    if not converter.connect_mysql():
        print("❌ فشل في الاتصال بـ MySQL")
        return
    
    # مجلد ملفات SQLite
    sqlite_folder = "d:/test3/ultimate_converted"
    
    # تحويل جميع الملفات
    successful = converter.batch_convert_sqlite_files(sqlite_folder, print)
    
    if successful:
        print(f"\n🎉 تم تحويل {len(successful)} كتاب بنجاح!")
        print("💡 يمكنك الآن استخدام الكتب في التطبيق الرئيسي")
    else:
        print("\n❌ لم ينجح أي تحويل")
    
    # إغلاق الاتصال
    if converter.mysql_conn:
        converter.mysql_conn.close()
        print("\n🔌 تم إغلاق اتصال MySQL")

if __name__ == "__main__":
    main()
