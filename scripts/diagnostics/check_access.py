import pyodbc
import os

# فتح ملف Access وفحص البيانات
access_file = "shamela_book.accdb"
access_path = os.path.abspath(access_file)

try:
    # تركيب سلسلة الاتصال
    driver = r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=' + access_path + ';'
    conn = pyodbc.connect(driver)
    cursor = conn.cursor()
    
    # البحث عن جدول المحتوى
    tables = [table.table_name for table in cursor.tables(tableType='TABLE') 
             if not table.table_name.startswith('MSys')]
    
    content_table = None
    for table in tables:
        if table.startswith('b') and table[1:].isdigit():
            content_table = table
            break
    
    if content_table:
        print(f"جدول المحتوى: {content_table}")
        
        # فحص إجمالي الصفحات
        cursor.execute(f"SELECT COUNT(*) FROM {content_table}")
        total_rows = cursor.fetchone()[0]
        print(f"إجمالي الصفوف: {total_rows}")
        
        # فحص الصفحات الفريدة
        cursor.execute(f"SELECT COUNT(DISTINCT page) FROM {content_table}")
        unique_pages = cursor.fetchone()[0]
        print(f"الصفحات الفريدة: {unique_pages}")
        
        # فحص أجزاء part
        cursor.execute(f"SELECT DISTINCT part FROM {content_table} ORDER BY part")
        parts = cursor.fetchall()
        print(f"الأجزاء المتاحة: {[p[0] for p in parts if p[0] is not None]}")
        
        # فحص توزيع الصفحات حسب part
        cursor.execute(f"SELECT part, COUNT(*) FROM {content_table} GROUP BY part ORDER BY part")
        part_counts = cursor.fetchall()
        print("توزيع الصفحات حسب الجزء:")
        for part, count in part_counts:
            print(f"  الجزء {part}: {count} صفحة")
            
        # عينة من البيانات المكررة
        cursor.execute(f"SELECT page, COUNT(*) as cnt FROM {content_table} GROUP BY page HAVING COUNT(*) > 1 ORDER BY cnt DESC LIMIT 5")
        duplicates = cursor.fetchall()
        if duplicates:
            print("عينة من الصفحات المكررة:")
            for page, count in duplicates:
                print(f"  الصفحة {page}: مكررة {count} مرة")
        
    conn.close()
    
except Exception as e:
    print(f"خطأ: {e}")
