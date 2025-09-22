#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار للتأكد من عدم حذف الرموز الخاصة مثل === و « »
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.shamela_converter import ShamelaConverter

def test_symbols_preservation():
    """اختبار الحفاظ على الرموز الخاصة"""
    
    # إعدادات MySQL وهمية للاختبار
    mysql_config = {
        'host': 'localhost',
        'user': 'test',
        'password': 'test',
        'database': 'test'
    }
    
    # إنشاء كائن المحول
    converter = ShamelaConverter(mysql_config)
    
    # نصوص اختبار تحتوي على الرموز المطلوبة
    test_texts = [
        "هذا نص يحتوي على === رموز خاصة",
        "نص آخر مع أقواس « مزدوجة » في الوسط",
        "=== بداية الفصل === وسط النص === نهاية الفصل ===",
        "قال المؤلف « هذا مثال » وأضاف « مثال آخر »",
        "نص مختلط === مع « أقواس » و === رموز متعددة ==="
    ]
    
    print("اختبار الحفاظ على الرموز الخاصة:")
    print("=" * 50)
    
    for i, text in enumerate(test_texts, 1):
        print(f"\nالنص الأصلي {i}:")
        print(f"'{text}'")
        
        # اختبار دالة preserve_arabic_diacritics
        preserved = converter.preserve_arabic_diacritics(text)
        print(f"بعد preserve_arabic_diacritics:")
        print(f"'{preserved}'")
        
        # اختبار دالة extract_arabic_text_enhanced
        enhanced = converter.extract_arabic_text_enhanced(text)
        print(f"بعد extract_arabic_text_enhanced:")
        print(f"'{enhanced}'")
        
        # اختبار دالة clean_text
        cleaned = converter.clean_text(text)
        print(f"بعد clean_text:")
        print(f"'{cleaned}'")
        
        # التحقق من وجود الرموز
        has_equals = '===' in enhanced
        has_quotes = '«' in enhanced or '»' in enhanced
        
        print(f"هل تم الحفاظ على ===؟ {'نعم' if has_equals else 'لا'}")
        print(f"هل تم الحفاظ على « »؟ {'نعم' if has_quotes else 'لا'}")
        
        print("-" * 30)

if __name__ == "__main__":
    test_symbols_preservation()