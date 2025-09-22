#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار نهائي للتأكد من الحفاظ على الرموز وتحويل === إلى <br>
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.shamela_converter import ShamelaConverter

def test_final_symbols():
    """اختبار نهائي للرموز والتحويل إلى HTML"""
    try:
        print("=== اختبار نهائي للرموز والتحويل إلى HTML ===")
        
        # إعدادات وهمية
        mysql_config = {
            'host': 'localhost',
            'user': 'test',
            'password': '',
            'database': 'test'
        }
        
        converter = ShamelaConverter(mysql_config)
        
        # نصوص اختبار متنوعة
        test_texts = [
            "نص عادي مع === فاصل === ونهاية",
            "قال المؤلف « هذا مثال » وأضاف « مثال آخر »",
            "نص مختلط === مع « أقواس » و === رموز متعددة ===",
            "بداية النص\n=== فاصل ===\nوسط النص\n=== نهاية ===",
            "« قول أول » === فاصل === « قول ثاني »"
        ]
        
        for i, text in enumerate(test_texts, 1):
            print(f"\n--- اختبار النص {i} ---")
            print(f"النص الأصلي: '{text}'")
            
            # تطبيق الدوال بالتسلسل
            preserved = converter.preserve_arabic_diacritics(text)
            enhanced = converter.extract_arabic_text_enhanced(preserved)
            html_result = converter.format_text_to_html(enhanced)
            
            print(f"النتيجة النهائية HTML: '{html_result}'")
            
            # فحص النتائج
            has_quotes = '«' in html_result and '»' in html_result
            has_br_conversion = '===' not in html_result and '<br>' in html_result
            
            print(f"هل تم الحفاظ على « »؟ {'نعم' if has_quotes else 'لا'}")
            print(f"هل تم تحويل === إلى <br>؟ {'نعم' if has_br_conversion else 'لا'}")
            
            # تحقق خاص للنصوص التي تحتوي على ===
            if '===' in text:
                if '===' in html_result:
                    print("⚠️ تحذير: لم يتم تحويل === إلى <br>")
                else:
                    print("✅ تم تحويل === إلى <br> بنجاح")
            
            # تحقق خاص للنصوص التي تحتوي على « »
            if '«' in text and '»' in text:
                if '«' in html_result and '»' in html_result:
                    print("✅ تم الحفاظ على علامات الاقتباس العربية « »")
                else:
                    print("⚠️ تحذير: لم يتم الحفاظ على علامات الاقتباس العربية « »")
            
            print("-" * 50)
        
        print("\n=== انتهى الاختبار النهائي ===")
        
    except Exception as e:
        print(f"خطأ في الاختبار: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_final_symbols()