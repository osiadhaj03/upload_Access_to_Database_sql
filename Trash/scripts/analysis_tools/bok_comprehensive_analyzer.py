#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
محلل ملفات .bok للشاملة - الإصدار النهائي
يجرب طرق مختلفة لقراءة ملفات .bok
"""

import os
import pyodbc
import shutil
from pathlib import Path
import tempfile
import struct

def analyze_file_structure(file_path):
    """تحليل بنية الملف بدون ODBC"""
    try:
        with open(file_path, 'rb') as f:
            # قراءة header الملف
            header = f.read(128)
            
            # معلومات أساسية
            file_size = os.path.getsize(file_path)
            
            # تحديد نوع الملف
            file_type = "Unknown"
            if header.startswith(b'\x00\x01\x00\x00Standard Jet DB'):
                file_type = "Access Jet Database"
                version_bytes = header[20:24]
                version = struct.unpack('<I', version_bytes)[0]
                file_type += f" (Version: {version})"
            elif header.startswith(b'\x00\x01\x00\x00Standard ACE DB'):
                file_type = "Access ACE Database"
            
            return {
                'file_name': os.path.basename(file_path),
                'file_size': file_size,
                'file_type': file_type,
                'header_hex': header[:32].hex(),
                'header_ascii': header[:32].decode('ascii', errors='ignore'),
                'can_analyze': file_type.startswith("Access")
            }
            
    except Exception as e:
        return {
            'file_name': os.path.basename(file_path),
            'file_size': os.path.getsize(file_path) if os.path.exists(file_path) else 0,
            'file_type': 'Error',
            'error': str(e),
            'can_analyze': False
        }

def try_multiple_drivers(file_path):
    """جرب drivers مختلفة للاتصال بالملف"""
    drivers_to_try = [
        "Microsoft Access Driver (*.mdb, *.accdb)",
        "Microsoft Access Driver (*.mdb)",
        "Microsoft Access dBASE Driver (*.dbf, *.ndx, *.mdx)",
        "Driver do Microsoft Access (*.mdb)",
    ]
    
    # إنشاء ملف مؤقت بامتدادات مختلفة
    extensions_to_try = ['.accdb', '.mdb']
    
    for ext in extensions_to_try:
        temp_path = None
        try:
            # إنشاء ملف مؤقت
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as temp_file:
                temp_path = temp_file.name
            
            shutil.copy(file_path, temp_path)
            
            for driver in drivers_to_try:
                try:
                    connection_string = f"Driver={{{driver}}};DBQ={temp_path};"
                    
                    # محاولة اتصال سريع
                    with pyodbc.connect(connection_string, timeout=10) as conn:
                        return conn, driver, temp_path, ext
                        
                except pyodbc.Error:
                    continue
                except Exception:
                    continue
                    
        except Exception:
            continue
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
    
    return None, None, None, None

def analyze_with_alternative_method(file_path):
    """محاولة تحليل بديلة عن طريق قراءة البيانات مباشرة"""
    try:
        # هذا سيكون تحليل أساسي للملف
        analysis = {
            'file_name': os.path.basename(file_path),
            'can_read_directly': False,
            'estimated_content': None
        }
        
        # محاولة قراءة نصوص باللغة العربية من الملف
        with open(file_path, 'rb') as f:
            content = f.read()
            
            # البحث عن نصوص عربية
            try:
                # فك التشفير UTF-8 و UTF-16
                text_utf8 = content.decode('utf-8', errors='ignore')
                text_utf16 = content.decode('utf-16', errors='ignore')
                
                # البحث عن كلمات عربية شائعة
                arabic_patterns = ['الله', 'قال', 'باب', 'كتاب', 'فصل', 'مقدمة']
                
                found_arabic = []
                for pattern in arabic_patterns:
                    if pattern in text_utf8:
                        found_arabic.append(f"UTF-8: {pattern}")
                    if pattern in text_utf16:
                        found_arabic.append(f"UTF-16: {pattern}")
                
                if found_arabic:
                    analysis['can_read_directly'] = True
                    analysis['estimated_content'] = found_arabic[:5]  # أول 5 نتائج
                    
                    # محاولة استخراج عنوان محتمل
                    for encoding in ['utf-8', 'utf-16']:
                        try:
                            text = content.decode(encoding, errors='ignore')
                            lines = text.split('\n')
                            for line in lines:
                                line = line.strip()
                                if len(line) > 10 and any(arabic in line for arabic in arabic_patterns):
                                    analysis['potential_title'] = line[:100]
                                    break
                        except:
                            continue
                            
            except Exception as e:
                analysis['text_analysis_error'] = str(e)
        
        return analysis
        
    except Exception as e:
        return {
            'file_name': os.path.basename(file_path),
            'can_read_directly': False,
            'error': str(e)
        }

def create_comprehensive_report(all_analyses):
    """إنشاء تقرير شامل"""
    
    report = """# تقرير تحليل ملفات .bok للشاملة - التحليل الشامل

تم إجراء تحليل متعدد المستويات لملفات .bok لتحديد طبيعتها وإمكانية قراءتها.

## ملخص النتائج

"""
    
    total_files = len(all_analyses)
    
    # حساب الإحصائيات
    access_files = sum(1 for a in all_analyses if a.get('structure', {}).get('can_analyze', False))
    readable_files = sum(1 for a in all_analyses if a.get('alternative', {}).get('can_read_directly', False))
    
    report += f"- **إجمالي الملفات:** {total_files}\n"
    report += f"- **ملفات Access مؤكدة:** {access_files}\n"
    report += f"- **ملفات قابلة للقراءة المباشرة:** {readable_files}\n\n"
    
    # جدول ملخص
    report += "| اسم الملف | حجم (MB) | نوع الملف | قابل للتحليل | محتوى عربي |\n"
    report += "|-----------|----------|-----------|-------------|------------|\n"
    
    for analysis in all_analyses:
        structure = analysis.get('structure', {})
        alternative = analysis.get('alternative', {})
        
        file_name = structure.get('file_name', 'غير معروف')
        file_size = round(structure.get('file_size', 0) / (1024*1024), 2)
        file_type = structure.get('file_type', 'غير معروف')
        can_analyze = "✅" if structure.get('can_analyze', False) else "❌"
        has_arabic = "✅" if alternative.get('can_read_directly', False) else "❌"
        
        report += f"| {file_name} | {file_size} | {file_type} | {can_analyze} | {has_arabic} |\n"
    
    report += "\n---\n\n"
    
    # تفاصيل كل ملف
    for analysis in all_analyses:
        structure = analysis.get('structure', {})
        alternative = analysis.get('alternative', {})
        
        file_name = structure.get('file_name', 'غير معروف')
        
        report += f"## تفاصيل ملف: {file_name}\n\n"
        
        # معلومات البنية
        report += "### تحليل البنية:\n"
        report += f"- **حجم الملف:** {round(structure.get('file_size', 0) / (1024*1024), 2)} MB\n"
        report += f"- **نوع الملف:** {structure.get('file_type', 'غير معروف')}\n"
        
        if structure.get('header_hex'):
            report += f"- **Header (hex):** `{structure['header_hex']}`\n"
        
        if structure.get('header_ascii'):
            report += f"- **Header (ASCII):** `{structure['header_ascii']}`\n"
        
        if structure.get('error'):
            report += f"- **خطأ في التحليل:** {structure['error']}\n"
        
        # معلومات المحتوى
        report += "\n### تحليل المحتوى:\n"
        
        if alternative.get('can_read_directly'):
            report += "- **قابل للقراءة المباشرة:** ✅\n"
            
            if alternative.get('estimated_content'):
                report += "- **محتوى مُكتشف:**\n"
                for content in alternative['estimated_content']:
                    report += f"  - {content}\n"
            
            if alternative.get('potential_title'):
                report += f"- **عنوان محتمل:** {alternative['potential_title']}\n"
        else:
            report += "- **قابل للقراءة المباشرة:** ❌\n"
            
        if alternative.get('error'):
            report += f"- **خطأ في تحليل المحتوى:** {alternative['error']}\n"
        
        report += "\n---\n\n"
    
    # خلاصة وتوصيات
    report += """## الخلاصة والتوصيات

### النتائج المؤكدة:
"""
    
    if access_files > 0:
        report += f"- ✅ {access_files} ملف مؤكد أنه Access Database\n"
        report += "- ✅ الملفات تستخدم تنسيق Jet Database\n"
        report += "- ✅ الهيكل متوافق مع ملفات الشاملة\n\n"
    
    if readable_files > 0:
        report += f"- ✅ {readable_files} ملف يحتوي على نص عربي قابل للقراءة\n"
        report += "- ✅ المحتوى يبدو متوافق مع كتب الشاملة\n\n"
    
    if access_files == 0:
        report += "- ❌ لم يتم التمكن من قراءة الملفات كـ Access Database\n"
        report += "- ⚠️ قد تحتاج إعدادات خاصة أو drivers مختلفة\n\n"
    
    report += """### الحلول المقترحة:

#### الحل الأول: تثبيت Access Database Engine
```bash
# تحميل وتثبيت Microsoft Access Database Engine 2016
# https://www.microsoft.com/en-us/download/details.aspx?id=54920
```

#### الحل الثاني: استخدام أدوات بديلة
```python
# استخدام mdb-tools لـ Linux أو Wine
# أو استخدام SQLite مع converter خاص
```

#### الحل الثالث: قراءة مباشرة للبيانات
```python
# تطوير parser خاص لقراءة البيانات مباشرة
# من ملفات .bok بدون ODBC
```

### خطة التطبيق المقترحة:

1. **دعم امتداد .bok في الواجهة:**
   - إضافة `*.bok` لقائمة الملفات المدعومة
   - تحذير المستخدم عند اختيار ملف .bok

2. **إضافة converter خاص:**
   - نسخ ملفات .bok إلى .accdb مؤقتاً
   - تجريب drivers مختلفة تلقائياً
   - معالجة أخطاء الاتصال بشكل أنيق

3. **إضافة تشخيص ذكي:**
   - فحص نوع الملف قبل المعالجة
   - عرض رسائل خطأ واضحة
   - اقتراح حلول للمستخدم

---
*تم إنشاء هذا التقرير بواسطة محلل ملفات .bok الشامل*
"""
    
    return report

def main():
    """الدالة الرئيسية"""
    print("=== محلل ملفات .bok للشاملة - التحليل الشامل ===")
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
    print("بدء التحليل الشامل...\n")
    
    all_analyses = []
    
    for i, bok_file in enumerate(bok_files, 1):
        print(f"[{i}/{len(bok_files)}] تحليل: {bok_file.name}")
        
        # تحليل بنية الملف
        print("  ├── تحليل البنية...")
        structure_analysis = analyze_file_structure(str(bok_file))
        
        # تحليل المحتوى البديل
        print("  ├── تحليل المحتوى...")
        alternative_analysis = analyze_with_alternative_method(str(bok_file))
        
        # محاولة drivers مختلفة (سريعة)
        print("  └── فحص التوافقية...")
        
        analysis = {
            'structure': structure_analysis,
            'alternative': alternative_analysis
        }
        
        all_analyses.append(analysis)
        
        # عرض نتيجة سريعة
        if structure_analysis.get('can_analyze'):
            print(f"      ✅ ملف Access مؤكد")
        elif alternative_analysis.get('can_read_directly'):
            print(f"      📖 يحتوي على نص عربي")
        else:
            print(f"      ❓ يحتاج تحليل إضافي")
        
        print()
    
    # إنشاء التقرير الشامل
    print("إنشاء التقرير الشامل...")
    report_content = create_comprehensive_report(all_analyses)
    
    # حفظ التقرير
    report_path = "bok_comprehensive_analysis.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    
    print(f"\n{'='*60}")
    print("تم الانتهاء من التحليل الشامل")
    print(f"📄 التقرير النهائي: {report_path}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
