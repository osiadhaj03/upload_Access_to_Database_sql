# أدوات التشخيص
# Diagnostics Tools

هذا المجلد يحتوي على أدوات تشخيص المشاكل والفحص الفني

## الملفات الموجودة:

### تشخيص Access:
- **`access_diagnostics.py`** - تشخيص مشاكل Microsoft Access
  - فحص تثبيت Access Database Engine
  - اختبار اتصال ODBC
  - تشخيص مشاكل التوافق
  - عرض معلومات النظام

### أدوات الفحص:
- **`check_access.py`** - فحص إمكانية الوصول لملفات Access
  - التحقق من صحة ملفات .accdb
  - اختبار فتح الملفات
  - فحص الأذونات
  - التحقق من سلامة البيانات

- **`check_pages.py`** - فحص صفحات وبيانات الكتب
  - التحقق من اكتمال الصفحات
  - فحص ترقيم الصفحات
  - التحقق من النصوص المفقودة
  - تحليل هيكل المحتوى

## الاستخدام:

### تشخيص Access:
```python
from access_diagnostics import run_diagnostics

diagnostics = run_diagnostics()
print(diagnostics)
```

### فحص ملف Access:
```python
from check_access import check_access_file

result = check_access_file("path/to/file.accdb")
```

### فحص الصفحات:
```python
from check_pages import check_book_pages

pages_info = check_book_pages("path/to/book.accdb")
```

## المخرجات:
- تقارير تشخيص مفصلة
- رسائل خطأ واضحة
- اقتراحات للحلول
- معلومات النظام

## متى تستخدم هذه الأدوات:
- عند مواجهة مشاكل في التحويل
- للتحقق من سلامة الملفات
- لتشخيص مشاكل البيئة
- قبل بدء عمليات التحويل الكبيرة

## ملاحظة:
هذه أدوات مساعدة للتطوير والصيانة الفنية.
