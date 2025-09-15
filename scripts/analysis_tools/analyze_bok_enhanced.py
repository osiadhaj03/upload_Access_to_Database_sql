#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
محلل ملفات .bok للشاملة - الإصدار المحسن
يحلل ملفات .bok عن طريق نسخها إلى امتداد .accdb مؤقتاً
"""

import os
import pyodbc
import shutil
from pathlib import Path
import tempfile

def analyze_bok_file(bok_path):
    """تحليل ملف .bok واحد"""
    print(f"\n{'='*60}")
    print(f"تحليل ملف: {os.path.basename(bok_path)}")
    print(f"{'='*60}")
    
    # إنشاء ملف مؤقت بامتداد .accdb
    with tempfile.NamedTemporaryFile(suffix='.accdb', delete=False) as temp_file:
        temp_path = temp_file.name
    
    try:
        # نسخ الملف
        print(f"نسخ {os.path.basename(bok_path)} إلى ملف مؤقت...")
        shutil.copy(bok_path, temp_path)
        
        # محاولة الاتصال
        print("محاولة الاتصال بقاعدة البيانات...")
        connection_string = f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={temp_path};"
        
        with pyodbc.connect(connection_string) as conn:
            print("✅ نجح الاتصال!")
            
            cursor = conn.cursor()
            
            # الحصول على قائمة الجداول
            tables = [table.table_name for table in cursor.tables(tableType='TABLE') 
                     if not table.table_name.startswith('MSys')]
            
            print(f"عدد الجداول: {len(tables)}")
            print(f"أسماء الجداول: {tables}")
            
            analysis = {
                'file_name': os.path.basename(bok_path),
                'file_size': os.path.getsize(bok_path),
                'tables': [],
                'content_table': None,
                'index_table': None,
                'book_info': None
            }
            
            for table in tables:
                print(f"\n--- تحليل جدول: {table} ---")
                
                try:
                    # الحصول على أعمدة الجدول
                    cursor.execute(f"SELECT TOP 1 * FROM [{table}]")
                    columns = [column[0] for column in cursor.description] if cursor.description else []
                    
                    # عدد الصفوف
                    cursor.execute(f"SELECT COUNT(*) FROM [{table}]")
                    row_count = cursor.fetchone()[0]
                    
                    table_info = {
                        'name': table,
                        'columns': columns,
                        'row_count': row_count,
                        'sample_data': []
                    }
                    
                    print(f"الأعمدة: {columns}")
                    print(f"عدد الصفوف: {row_count}")
                    
                    # التحقق من نوع الجدول
                    if table.startswith('b') and len(table) > 1 and table[1:].isdigit():
                        analysis['content_table'] = table
                        print("🔍 هذا جدول المحتوى (b + رقم)")
                        
                        # استخراج معلومات الكتاب
                        try:
                            cursor.execute(f"SELECT TOP 1 * FROM [{table}] WHERE nass IS NOT NULL AND nass <> ''")
                            first_row = cursor.fetchone()
                            if first_row and len(first_row) > 0:
                                # البحث عن النص
                                for i, value in enumerate(first_row):
                                    if value and isinstance(value, str) and len(value) > 20:
                                        analysis['book_info'] = {
                                            'title_column': columns[i] if i < len(columns) else 'unknown',
                                            'sample_content': value[:200],
                                            'book_id': table[1:] if len(table) > 1 else 'unknown'
                                        }
                                        print(f"محتوى نموذجي: {value[:100]}...")
                                        break
                        except Exception as e:
                            print(f"⚠️ تحذير في استخراج محتوى الكتاب: {e}")
                            
                    elif table.startswith('t') and len(table) > 1 and table[1:].isdigit():
                        analysis['index_table'] = table
                        print("🔍 هذا جدول الفهرس (t + رقم)")
                    
                    # عرض نموذج من البيانات
                    if row_count > 0:
                        cursor.execute(f"SELECT TOP 3 * FROM [{table}]")
                        sample_rows = cursor.fetchall()
                        print("نموذج من البيانات:")
                        for i, row in enumerate(sample_rows):
                            # عرض البيانات بحذر لتجنب النصوص الطويلة
                            safe_row = []
                            for item in row:
                                if isinstance(item, str) and len(item) > 50:
                                    safe_row.append(item[:50] + "...")
                                else:
                                    safe_row.append(item)
                            print(f"  الصف {i+1}: {safe_row}")
                            table_info['sample_data'].append(safe_row)
                    
                    analysis['tables'].append(table_info)
                    
                except Exception as e:
                    print(f"❌ خطأ في تحليل جدول {table}: {e}")
            
            return analysis
            
    except Exception as e:
        print(f"❌ خطأ في تحليل الملف: {e}")
        return None
        
    finally:
        # حذف الملف المؤقت
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                print(f"تم حذف الملف المؤقت")
        except:
            pass

def create_detailed_report(all_results):
    """إنشاء تقرير markdown مفصل"""
    
    report = """# تقرير تحليل ملفات .bok للشاملة

## ملخص النتائج

"""
    
    successful_analyses = [r for r in all_results if r is not None]
    
    if not successful_analyses:
        report += "❌ لم يتم التمكن من تحليل أي ملف بنجاح.\n\n"
        report += "### الأسباب المحتملة:\n"
        report += "- عدم وجود Microsoft Access Driver\n"
        report += "- ملفات .bok تحتاج إعدادات خاصة\n"
        report += "- مشكلة في الصلاحيات\n\n"
    else:
        report += f"✅ تم تحليل **{len(successful_analyses)}** ملف من أصل **{len(all_results)}** بنجاح.\n\n"
        
        # جدول ملخص
        report += "| اسم الملف | حجم الملف (MB) | عدد الجداول | جدول المحتوى | جدول الفهرس | معرف الكتاب |\n"
        report += "|-----------|----------------|-------------|-------------|-------------|-------------|\n"
        
        for result in successful_analyses:
            content_table = result.get('content_table', 'غير موجود')
            index_table = result.get('index_table', 'غير موجود')
            file_size_mb = round(result.get('file_size', 0) / (1024*1024), 2)
            book_id = result.get('book_info', {}).get('book_id', 'غير معروف') if result.get('book_info') else 'غير معروف'
            
            report += f"| {result['file_name']} | {file_size_mb} | {len(result['tables'])} | {content_table} | {index_table} | {book_id} |\n"
    
    report += "\n---\n\n"
    
    # تفاصيل كل ملف
    for result in successful_analyses:
        report += f"## تفاصيل ملف: {result['file_name']}\n\n"
        
        report += f"- **حجم الملف:** {round(result['file_size'] / (1024*1024), 2)} MB\n"
        report += f"- **عدد الجداول:** {len(result['tables'])}\n"
        report += f"- **جدول المحتوى:** {result.get('content_table', 'غير موجود')}\n"
        report += f"- **جدول الفهرس:** {result.get('index_table', 'غير موجود')}\n\n"
        
        if result.get('book_info'):
            book_info = result['book_info']
            report += f"### معلومات الكتاب:\n"
            report += f"- **معرف الكتاب:** {book_info.get('book_id', 'غير معروف')}\n"
            report += f"- **عمود المحتوى:** {book_info.get('title_column', 'غير معروف')}\n"
            report += f"- **نموذج المحتوى:**\n```\n{book_info.get('sample_content', 'غير متوفر')}\n```\n\n"
        
        # تفاصيل الجداول
        report += "### الجداول:\n\n"
        
        for table in result['tables']:
            report += f"#### جدول: `{table['name']}`\n\n"
            report += f"- **عدد الصفوف:** {table['row_count']:,}\n"
            report += f"- **الأعمدة:** {', '.join([f'`{col}`' for col in table['columns']])}\n"
            
            if table.get('sample_data'):
                report += f"- **نموذج البيانات:**\n"
                for i, row in enumerate(table['sample_data'][:2]):  # عرض أول صفين فقط
                    report += f"  - الصف {i+1}: {row}\n"
            
            report += "\n"
        
        report += "---\n\n"
    
    # التوصيات النهائية
    if successful_analyses:
        report += """## التوصيات والخطوات التالية

### النتائج المؤكدة:
- ✅ ملفات .bok هي ملفات Access Database عادية بتنسيق Jet
- ✅ يمكن قراءتها عن طريق نسخها إلى امتداد .accdb
- ✅ تحتوي على نفس بنية الشاملة (جداول b و t)
- ✅ يمكن دمجها في النظام الحالي

### خطة التطبيق:

1. **تعديل واجهة اختيار الملفات:**
```python
filetypes=[
    ("ملفات الشاملة", "*.accdb;*.bok"), 
    ("Access Database", "*.accdb"), 
    ("ملفات BOK", "*.bok"),
    ("كل الملفات", "*.*")
]
```

2. **إضافة دالة معالجة ملفات .bok:**
```python
def handle_bok_file(file_path):
    if file_path.lower().endswith('.bok'):
        # إنشاء ملف مؤقت
        temp_dir = tempfile.gettempdir()
        temp_name = f"shamela_temp_{int(time.time())}.accdb"
        temp_path = os.path.join(temp_dir, temp_name)
        
        shutil.copy(file_path, temp_path)
        return temp_path, True  # True يعني ملف مؤقت
    return file_path, False
```

3. **تنظيف الملفات المؤقتة:**
```python
def cleanup_temp_file(temp_path, is_temp):
    if is_temp and os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except:
            pass
```

### كود التكامل الكامل:
ملف `shamela_bok_support.py` سيحتوي على الدوال المساعدة لدعم ملفات .bok
"""
    else:
        report += """## تشخيص المشكلة

### الأسباب المحتملة لفشل القراءة:
1. **عدم وجود Microsoft Access Driver:**
   - تحتاج تثبيت Microsoft Access Database Engine
   - رابط التحميل: https://www.microsoft.com/en-us/download/details.aspx?id=54920

2. **مشكلة في إعدادات النظام:**
   - قد تحتاج تشغيل Python كمدير
   - تحقق من إعدادات الحماية

3. **مشكلة في ملفات .bok:**
   - قد تكون محمية أو مشفرة
   - قد تحتاج أدوات خاصة للقراءة

### خطوات الحل المقترحة:
1. تثبيت Microsoft Access Database Engine
2. إعادة تشغيل النظام
3. تجريب السكريپت مرة أخرى
"""
    
    report += """

---
*تم إنشاء هذا التقرير تلقائياً بواسطة محلل ملفات .bok المحسن*
"""
    
    # حفظ التقرير
    report_path = "bok_analysis_detailed_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n📄 تم إنشاء تقرير التحليل المفصل: {report_path}")
    return report_path

def main():
    """الدالة الرئيسية"""
    print("=== محلل ملفات .bok للشاملة - الإصدار المحسن ===")
    print("=" * 60)
    
    bok_folder = Path("d:/test3/bok file")
    
    if not bok_folder.exists():
        print("❌ مجلد ملفات .bok غير موجود")
        return
    
    bok_files = list(bok_folder.glob("*.bok"))
    
    if not bok_files:
        print("❌ لم يتم العثور على ملفات .bok")
        return
    
    print(f"تم العثور على {len(bok_files)} ملف .bok")
    
    all_results = []
    
    for bok_file in bok_files:
        analysis = analyze_bok_file(str(bok_file))
        all_results.append(analysis)
    
    # إنشاء تقرير مفصل
    report_path = create_detailed_report(all_results)
    
    print(f"\n{'='*60}")
    print("تم الانتهاء من التحليل المحسن")
    print(f"تقرير التحليل: {report_path}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
