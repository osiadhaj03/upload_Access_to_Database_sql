#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
محلل ملفات .bok للشاملة
يحلل ملفات .bok لمعرفة بنيتها وإمكانية قراءتها
"""

import os
import pyodbc
from pathlib import Path
import struct

def analyze_file_header(file_path):
    """تحليل header الملف لمعرفة نوعه"""
    try:
        with open(file_path, 'rb') as f:
            # قراءة أول 32 بايت
            header = f.read(32)
            
            print(f"\n=== تحليل ملف: {os.path.basename(file_path)} ===")
            print(f"حجم الملف: {os.path.getsize(file_path):,} بايت")
            print(f"أول 32 بايت (hex): {header.hex()}")
            print(f"أول 32 بايت (ASCII): {header.decode('ascii', errors='ignore')}")
            
            # فحص إذا كان ملف Access
            if header.startswith(b'\x00\x01\x00\x00Standard Jet DB'):
                print("✅ ملف Access Database (Jet Format)")
                return "access_jet"
            elif header.startswith(b'\x00\x01\x00\x00Standard ACE DB'):
                print("✅ ملف Access Database (ACE Format)")
                return "access_ace"
            elif b'Microsoft' in header:
                print("⚠️ ملف Microsoft محتمل")
                return "microsoft"
            else:
                print("❓ نوع ملف غير معروف")
                return "unknown"
                
    except Exception as e:
        print(f"❌ خطأ في قراءة الملف: {e}")
        return "error"

def try_access_connection(file_path):
    """محاولة الاتصال بالملف كـ Access Database"""
    try:
        print(f"\n--- محاولة الاتصال بـ Access ---")
        
        # محاولة مع امتداد .bok مباشرة
        connection_string = f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={file_path};"
        
        try:
            conn = pyodbc.connect(connection_string)
            print("✅ نجح الاتصال مع امتداد .bok")
            return conn, "direct"
        except:
            pass
            
        # محاولة نسخ الملف بامتداد .accdb
        temp_file = file_path.replace('.bok', '_temp.accdb')
        try:
            import shutil
            shutil.copy(file_path, temp_file)
            
            connection_string = f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={temp_file};"
            conn = pyodbc.connect(connection_string)
            print("✅ نجح الاتصال بعد نسخ لـ .accdb")
            return conn, "copied", temp_file
        except:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            pass
            
        # محاولة مع .mdb
        temp_file = file_path.replace('.bok', '_temp.mdb')
        try:
            shutil.copy(file_path, temp_file)
            
            connection_string = f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={temp_file};"
            conn = pyodbc.connect(connection_string)
            print("✅ نجح الاتصال بعد نسخ لـ .mdb")
            return conn, "copied", temp_file
        except:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            pass
            
        print("❌ فشل في جميع محاولات الاتصال")
        return None, "failed"
        
    except Exception as e:
        print(f"❌ خطأ في محاولة الاتصال: {e}")
        return None, "error"

def analyze_database_structure(conn, file_name):
    """تحليل بنية قاعدة البيانات"""
    try:
        print(f"\n--- تحليل بنية قاعدة البيانات ---")
        
        cursor = conn.cursor()
        
        # الحصول على قائمة الجداول
        tables = [table.table_name for table in cursor.tables(tableType='TABLE') 
                 if not table.table_name.startswith('MSys')]
        
        print(f"عدد الجداول: {len(tables)}")
        print(f"أسماء الجداول: {tables}")
        
        analysis = {
            'file_name': file_name,
            'tables': [],
            'content_table': None,
            'index_table': None,
            'book_info': None
        }
        
        for table in tables:
            print(f"\n--- تحليل جدول: {table} ---")
            
            # الحصول على أعمدة الجدول
            try:
                cursor.execute(f"SELECT TOP 1 * FROM [{table}]")
                columns = [column[0] for column in cursor.description]
                
                # عدد الصفوف
                cursor.execute(f"SELECT COUNT(*) FROM [{table}]")
                row_count = cursor.fetchone()[0]
                
                table_info = {
                    'name': table,
                    'columns': columns,
                    'row_count': row_count
                }
                
                print(f"الأعمدة: {columns}")
                print(f"عدد الصفوف: {row_count}")
                
                # التحقق من نوع الجدول
                if table.startswith('b') and table[1:].isdigit():
                    analysis['content_table'] = table
                    print("🔍 هذا جدول المحتوى (b + رقم)")
                elif table.startswith('t') and table[1:].isdigit():
                    analysis['index_table'] = table
                    print("🔍 هذا جدول الفهرس (t + رقم)")
                
                # عرض نموذج من البيانات
                cursor.execute(f"SELECT TOP 3 * FROM [{table}]")
                sample_data = cursor.fetchall()
                print("نموذج من البيانات:")
                for i, row in enumerate(sample_data):
                    print(f"  الصف {i+1}: {row}")
                
                analysis['tables'].append(table_info)
                
            except Exception as e:
                print(f"❌ خطأ في تحليل جدول {table}: {e}")
        
        # محاولة استخراج معلومات الكتاب
        if analysis['content_table']:
            try:
                print(f"\n--- استخراج معلومات الكتاب ---")
                cursor.execute(f"SELECT TOP 1 * FROM [{analysis['content_table']}] WHERE nass IS NOT NULL")
                first_row = cursor.fetchone()
                if first_row:
                    # البحث عن عمود العنوان
                    for i, value in enumerate(first_row):
                        if value and isinstance(value, str) and len(value) > 10:
                            analysis['book_info'] = {
                                'title_column': columns[i],
                                'sample_title': value[:100]
                            }
                            print(f"عنوان محتمل: {value[:100]}")
                            break
            except Exception as e:
                print(f"⚠️ تحذير في استخراج معلومات الكتاب: {e}")
        
        return analysis
        
    except Exception as e:
        print(f"❌ خطأ في تحليل بنية قاعدة البيانات: {e}")
        return None

def main():
    """الدالة الرئيسية"""
    print("=== محلل ملفات .bok للشاملة ===")
    print("=" * 50)
    
    bok_folder = Path("d:/test3/bok file")
    bok_files = list(bok_folder.glob("*.bok"))
    
    if not bok_files:
        print("❌ لم يتم العثور على ملفات .bok")
        return
    
    print(f"تم العثور على {len(bok_files)} ملف .bok")
    
    analysis_results = []
    
    for bok_file in bok_files:
        print(f"\n{'='*60}")
        print(f"تحليل ملف: {bok_file.name}")
        print(f"{'='*60}")
        
        # تحليل header الملف
        file_type = analyze_file_header(str(bok_file))
        
        # محاولة الاتصال كـ Access
        connection_result = try_access_connection(str(bok_file))
        
        if len(connection_result) >= 2 and connection_result[0]:
            conn = connection_result[0]
            method = connection_result[1]
            temp_file = connection_result[2] if len(connection_result) > 2 else None
            
            # تحليل بنية قاعدة البيانات
            db_analysis = analyze_database_structure(conn, bok_file.name)
            
            if db_analysis:
                db_analysis['file_type'] = file_type
                db_analysis['connection_method'] = method
                analysis_results.append(db_analysis)
            
            conn.close()
            
            # حذف الملف المؤقت
            if temp_file and os.path.exists(temp_file):
                os.remove(temp_file)
        else:
            print(f"❌ لم يتم التمكن من تحليل {bok_file.name}")
    
    # إنشاء تقرير markdown
    create_analysis_report(analysis_results)
    
    print(f"\n{'='*60}")
    print("تم الانتهاء من التحليل")
    print(f"{'='*60}")

def create_analysis_report(results):
    """إنشاء تقرير markdown مفصل"""
    
    report = """# تقرير تحليل ملفات .bok للشاملة

## ملخص التحليل

"""
    
    if not results:
        report += "❌ لم يتم التمكن من تحليل أي ملف بنجاح.\n\n"
    else:
        report += f"✅ تم تحليل **{len(results)}** ملف بنجاح.\n\n"
        
        # جدول ملخص
        report += "| اسم الملف | نوع الملف | طريقة الاتصال | عدد الجداول | جدول المحتوى | جدول الفهرس |\n"
        report += "|-----------|-----------|---------------|-------------|-------------|-------------|\n"
        
        for result in results:
            content_table = result.get('content_table', 'غير موجود')
            index_table = result.get('index_table', 'غير موجود')
            file_type = result.get('file_type', 'غير معروف')
            method = result.get('connection_method', 'غير معروف')
            
            report += f"| {result['file_name']} | {file_type} | {method} | {len(result['tables'])} | {content_table} | {index_table} |\n"
    
    report += "\n---\n\n"
    
    # تفاصيل كل ملف
    for result in results:
        report += f"## تفاصيل ملف: {result['file_name']}\n\n"
        
        report += f"- **نوع الملف:** {result.get('file_type', 'غير معروف')}\n"
        report += f"- **طريقة الاتصال:** {result.get('connection_method', 'غير معروف')}\n"
        report += f"- **عدد الجداول:** {len(result['tables'])}\n"
        report += f"- **جدول المحتوى:** {result.get('content_table', 'غير موجود')}\n"
        report += f"- **جدول الفهرس:** {result.get('index_table', 'غير موجود')}\n\n"
        
        if result.get('book_info'):
            book_info = result['book_info']
            report += f"- **معلومات الكتاب المحتملة:**\n"
            report += f"  - عمود العنوان: {book_info['title_column']}\n"
            report += f"  - نموذج عنوان: {book_info['sample_title']}\n\n"
        
        # تفاصيل الجداول
        report += "### الجداول:\n\n"
        
        for table in result['tables']:
            report += f"#### جدول: `{table['name']}`\n\n"
            report += f"- **عدد الصفوف:** {table['row_count']:,}\n"
            report += f"- **الأعمدة:** {', '.join([f'`{col}`' for col in table['columns']])}\n\n"
        
        report += "---\n\n"
    
    # خلاصة والتوصيات
    report += """## الخلاصة والتوصيات

### النتائج:
"""
    
    if results:
        report += f"- ✅ ملفات .bok هي ملفات Access Database عادية\n"
        report += f"- ✅ يمكن قراءتها باستخدام نفس محرك Access\n"
        report += f"- ✅ تحتوي على نفس بنية الجداول (b+ رقم للمحتوى، t+ رقم للفهرس)\n"
        report += f"- ✅ يمكن دمجها في السكريپت الحالي\n\n"
        
        report += "### التوصيات:\n"
        report += "1. **إضافة دعم امتداد .bok** في واجهة اختيار الملفات\n"
        report += "2. **إنشاء نسخة مؤقتة** بامتداد .accdb عند الحاجة\n"
        report += "3. **استخدام نفس منطق التحويل** المستخدم مع ملفات .accdb\n"
        report += "4. **إضافة تنظيف للملفات المؤقتة** بعد التحويل\n\n"
    else:
        report += "- ❌ لم يتم التمكن من قراءة ملفات .bok\n"
        report += "- ⚠️ قد تحتاج مكتبات إضافية أو طريقة مختلفة\n\n"
    
    report += """### كود التكامل المقترح:

```python
# إضافة دعم .bok في واجهة اختيار الملفات
filetypes=[
    ("Access Database", "*.accdb;*.bok"), 
    ("كل الملفات", "*.*")
]

# تحويل .bok إلى .accdb مؤقتاً
def handle_bok_file(bok_path):
    if bok_path.endswith('.bok'):
        temp_path = bok_path.replace('.bok', '_temp.accdb')
        shutil.copy(bok_path, temp_path)
        return temp_path
    return bok_path
```

---
*تم إنشاء هذا التقرير تلقائياً بواسطة محلل ملفات .bok*
"""
    
    # حفظ التقرير
    with open("bok_analysis_report.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n📄 تم إنشاء تقرير التحليل: bok_analysis_report.md")

if __name__ == "__main__":
    main()
