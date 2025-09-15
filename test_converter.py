#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ملف اختبار لتجربة دوال استخراج النص والتشكيل
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.shamela_converter import ShamelaConverter

def test_text_processing():
    """اختبار دوال معالجة النص والتشكيل"""
    try:
        print("بدء اختبار دوال معالجة النص...")
        
        # إعدادات وهمية لقاعدة البيانات (لن نستخدمها)
        mysql_config = {
            'host': 'localhost',
            'user': 'test',
            'password': '',
            'database': 'test'
        }
        
        # إنشاء محول جديد
        converter = ShamelaConverter(mysql_config)
        
        # نص تجريبي مع تشكيل
        test_text = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ. الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ. الرَّحْمَٰنِ الرَّحِيمِ. مَالِكِ يَوْمِ الدِّينِ."
        
        print(f"النص الأصلي: {test_text}")
        
        # اختبار دالة الحفاظ على التشكيل
        preserved_text = converter.preserve_arabic_diacritics(test_text)
        print(f"النص مع الحفاظ على التشكيل: {preserved_text}")
        
        # اختبار دالة استخراج النص المحسن
        enhanced_text = converter.extract_arabic_text_enhanced(test_text)
        print(f"النص المحسن: {enhanced_text}")
        
        # اختبار دالة تحويل إلى HTML
        html_text = converter.format_text_to_html(enhanced_text)
        print(f"النص بصيغة HTML: {html_text}")
        
        # اختبار مع نص متعدد الفقرات
        multi_paragraph_text = """بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ
        
الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ

الرَّحْمَٰنِ الرَّحِيمِ

مَالِكِ يَوْمِ الدِّينِ"""
        
        print("\n--- اختبار النص متعدد الفقرات ---")
        print(f"النص الأصلي:\n{multi_paragraph_text}")
        
        enhanced_multi = converter.extract_arabic_text_enhanced(multi_paragraph_text)
        html_multi = converter.format_text_to_html(enhanced_multi)
        print(f"\nالنص بصيغة HTML:\n{html_multi}")
        
        print("\nتم إكمال اختبار دوال معالجة النص بنجاح!")
        
    except Exception as e:
        print(f"خطأ في الاختبار: {str(e)}")
        import traceback
        traceback.print_exc()

def test_access_connection():
    """اختبار الاتصال بملف Access"""
    try:
        print("\n--- اختبار الاتصال بملف Access ---")
        
        mysql_config = {
            'host': 'localhost',
            'user': 'test',
            'password': '',
            'database': 'test'
        }
        
        converter = ShamelaConverter(mysql_config)
        
        # مسار ملف Access
        access_file = 'access file/إبراز الغي في شفاء العي 1304.accdb'
        
        if os.path.exists(access_file):
            print(f"ملف Access موجود: {access_file}")
            
            # محاولة الاتصال بملف Access
            if converter.connect_access(access_file):
                print("تم الاتصال بملف Access بنجاح")
                
                # استخراج معلومات الكتاب
                book_info = converter.extract_book_info()
                if book_info:
                    print(f"معلومات الكتاب: {book_info}")
                
                # إغلاق الاتصال
                converter.access_conn.close()
            else:
                print("فشل في الاتصال بملف Access")
        else:
            print(f"ملف Access غير موجود: {access_file}")
            
    except Exception as e:
        print(f"خطأ في اختبار Access: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_text_processing()
    test_access_connection()