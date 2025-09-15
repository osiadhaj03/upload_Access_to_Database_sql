#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from shamela_converter import ShamelaConverter

def test_special_separator():
    """اختبار معالجة الرمز ¬__________"""
    
    # إعداد فارغ للاختبار
    mysql_config = {}
    converter = ShamelaConverter(mysql_config)
    
    # نص تجريبي يحتوي على الرمز ¬__________
    test_text = """هذا نص تجريبي قبل الخط الفاصل.
¬__________
هذا نص تجريبي بعد الخط الفاصل.
نص آخر مع ¬_____________ خط فاصل طويل.
وهذا نص عادي بدون خطوط فاصلة."""
    
    print("النص الأصلي:")
    print(repr(test_text))
    print("\n" + "="*50 + "\n")
    
    # تطبيق معالجة النص
    processed_text = converter.format_text_to_html(test_text)
    
    print("النص بعد المعالجة:")
    print(repr(processed_text))
    print("\n" + "="*50 + "\n")
    
    print("النص المعالج (للعرض):")
    print(processed_text)
    print("\n" + "="*50 + "\n")
    
    # التحقق من النتائج
    checks = [
        ("¬__________" in processed_text, "تم الاحتفاظ بالرمز ¬ مع الخط الفاصل"),
        ("<p style=\"text-align: center; margin: 10px 0;\">¬__________</p>" in processed_text, "الخط الفاصل ¬__________ في سطر منفصل مع التنسيق الصحيح"),
        (processed_text.count("¬__________") >= 2, "تم معالجة جميع الخطوط الفاصلة مع الرمز ¬"),
        ("¬" in processed_text, "تم الاحتفاظ بالرمز ¬ في النص")
    ]
    
    print("نتائج الفحص:")
    for check, description in checks:
        status = "✓" if check else "✗"
        print(f"{status} {description}")
    
    return all(check for check, _ in checks)

if __name__ == "__main__":
    success = test_special_separator()
    print(f"\nنتيجة الاختبار: {'نجح' if success else 'فشل'}")