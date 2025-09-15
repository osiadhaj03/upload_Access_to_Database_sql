# أدوات التحليل
# Analysis Tools

هذا المجلد يحتوي على أدوات تحليل ملفات BOK وقواعد البيانات

## الملفات الموجودة:

### محللات ملفات BOK:
- **`analyze_bok_files.py`** - تحليل أساسي لملفات BOK
  - يفحص هيكل ملفات .bok
  - يعرض معلومات الملف الأساسية
  - يتحقق من سلامة الملف

- **`analyze_bok_enhanced.py`** - تحليل محسن لملفات BOK
  - تحليل أعمق للبيانات الداخلية
  - عرض تفصيلي للجداول والحقول
  - إحصائيات شاملة عن المحتوى

- **`bok_comprehensive_analyzer.py`** - المحلل الشامل
  - تحليل كامل وتفصيلي
  - تقارير مفصلة بصيغة مختلفة
  - مقارنة بين عدة ملفات

## الاستخدام:

### تحليل ملف واحد:
```python
from analyze_bok_files import analyze_bok_file

result = analyze_bok_file("path/to/book.bok")
print(result)
```

### تحليل محسن:
```python
from analyze_bok_enhanced import enhanced_bok_analysis

analysis = enhanced_bok_analysis("path/to/book.bok")
```

### تحليل شامل:
```python
from bok_comprehensive_analyzer import comprehensive_analyze

report = comprehensive_analyze("path/to/book.bok")
```

## المخرجات:
- تقارير نصية مفصلة
- إحصائيات شاملة
- معلومات الهيكل الداخلي
- تحليل جودة البيانات

## الهدف:
هذه الأدوات مفيدة لـ:
- فهم هيكل ملفات BOK
- تشخيص مشاكل الملفات
- اختبار جودة البيانات
- التطوير والتحسين
