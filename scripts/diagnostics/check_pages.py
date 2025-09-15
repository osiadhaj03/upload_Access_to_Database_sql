import mysql.connector

# الاتصال بقاعدة البيانات
try:
    conn = mysql.connector.connect(
        host='srv1800.hstgr.io',
        user='u994369532_test',
        password='Test20205',
        database='u994369532_test',
        charset='utf8mb4'
    )
    
    cursor = conn.cursor()
    
    # البحث عن الكتاب الأخير
    cursor.execute("SELECT id, title FROM books WHERE title LIKE '%عمدة الرعاية%' ORDER BY id DESC LIMIT 1")
    book = cursor.fetchone()
    
    if book:
        book_id, title = book
        print(f"الكتاب: {title} (ID: {book_id})")
        
        # عدد الصفحات
        cursor.execute("SELECT COUNT(*) FROM pages WHERE book_id = %s", (book_id,))
        page_count = cursor.fetchone()[0]
        print(f"عدد الصفحات المرفوعة: {page_count}")
        
        # عدد الفصول
        cursor.execute("SELECT COUNT(*) FROM chapters WHERE book_id = %s", (book_id,))
        chapter_count = cursor.fetchone()[0]
        print(f"عدد الفصول المرفوعة: {chapter_count}")
        
        # أرقام الصفحات (عينة)
        cursor.execute("SELECT page_number FROM pages WHERE book_id = %s ORDER BY page_number LIMIT 10", (book_id,))
        sample_pages = cursor.fetchall()
        print(f"عينة من أرقام الصفحات: {[p[0] for p in sample_pages]}")
        
    else:
        print("لم يتم العثور على الكتاب")
        
except Exception as e:
    print(f"خطأ: {e}")
finally:
    if 'conn' in locals():
        conn.close()
