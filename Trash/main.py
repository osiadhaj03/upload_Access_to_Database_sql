#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
محول كتب الشاملة الرئيسي
Shamela Books Converter - Main Entry Point

هذا الملف الرئيسي لتشغيل محول كتب الشاملة
"""

import os
import sys

# إضافة مجلد src إلى المسار
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

# استيراد وتشغيل التطبيق
if __name__ == "__main__":
    try:
        from shamela_gui import main
        main()
    except ImportError as e:
        print(f"خطأ في استيراد الملفات: {e}")
        print("تأكد من وجود جميع الملفات المطلوبة في مجلد src")
        input("اضغط Enter للإغلاق...")
    except Exception as e:
        print(f"خطأ في تشغيل التطبيق: {e}")
        input("اضغط Enter للإغلاق...")
