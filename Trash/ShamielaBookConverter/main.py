#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
محول كتب الشاملة - التطبيق الرئيسي
نقطة الدخول الرئيسية للتطبيق

المطور: GitHub Copilot AI Assistant
الإصدار: 2.0
التاريخ: 2025
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
import traceback

# إضافة مجلد src إلى مسار Python
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

def check_dependencies():
    """فحص المتطلبات المطلوبة"""
    missing_packages = []
    
    try:
        import pyodbc
    except ImportError:
        missing_packages.append("pyodbc")
    
    try:
        import mysql.connector
    except ImportError:
        missing_packages.append("mysql-connector-python")
    
    try:
        import tkinter
    except ImportError:
        missing_packages.append("tkinter")
    
    if missing_packages:
        error_msg = f"""
الحزم التالية مفقودة ويجب تثبيتها:
{', '.join(missing_packages)}

لتثبيت الحزم المفقودة، استخدم الأوامر التالية:
pip install {' '.join(missing_packages)}

أو استخدم الأمر الشامل:
pip install -r requirements.txt
        """
        
        if 'tkinter' not in missing_packages:
            messagebox.showerror("حزم مفقودة", error_msg)
        else:
            print("خطأ: " + error_msg)
        
        return False
    
    return True

def setup_application():
    """إعداد التطبيق"""
    
    # فحص نظام التشغيل
    if sys.platform.startswith('win'):
        # Windows - تحسين عرض الخطوط
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
    
    # تحديد مجلد العمل
    if hasattr(sys, '_MEIPASS'):
        # نحن في ملف exe
        app_dir = sys._MEIPASS
    else:
        # نحن في بيئة التطوير
        app_dir = current_dir
    
    # تحديد مسار الموارد
    resources_dir = os.path.join(app_dir, 'resources')
    
    return resources_dir

def create_app_icon(root, resources_dir):
    """إنشاء أيقونة التطبيق"""
    try:
        icon_path = os.path.join(resources_dir, 'icons', 'app_icon.ico')
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
        else:
            # استخدام أيقونة افتراضية
            pass
    except Exception as e:
        print(f"تعذر تحميل الأيقونة: {e}")

def handle_exception(exc_type, exc_value, exc_traceback):
    """معالج الأخطاء العام"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    
    try:
        # محاولة إظهار رسالة خطأ في واجهة المستخدم
        messagebox.showerror(
            "خطأ غير متوقع", 
            f"حدث خطأ غير متوقع في التطبيق:\n\n{str(exc_value)}\n\nيرجى إرسال تقرير الخطأ للمطور."
        )
    except:
        # إذا فشلت واجهة المستخدم، اطبع في وحدة التحكم
        print(f"خطأ غير متوقع: {error_msg}")

def main():
    """الدالة الرئيسية"""
    
    # تعيين معالج الأخطاء العام
    sys.excepthook = handle_exception
    
    print("=" * 60)
    print("        محول كتب الشاملة - الإصدار 2.0")
    print("     Shamela Books Converter - Version 2.0")
    print("=" * 60)
    print("المطور: GitHub Copilot AI Assistant")
    print("التاريخ: 2025")
    print("=" * 60)
    
    try:
        # فحص المتطلبات
        print("جاري فحص المتطلبات...")
        if not check_dependencies():
            print("❌ فشل في فحص المتطلبات")
            input("اضغط Enter للخروج...")
            return 1
        
        print("✅ تم فحص المتطلبات بنجاح")
        
        # إعداد التطبيق
        print("جاري إعداد التطبيق...")
        resources_dir = setup_application()
        print("✅ تم إعداد التطبيق")
        
        # إنشاء النافذة الرئيسية
        print("جاري تشغيل واجهة المستخدم...")
        root = tk.Tk()
        
        # إعداد النافذة
        root.title("محول كتب الشاملة v2.0")
        root.geometry("900x700")
        
        # إنشاء الأيقونة
        create_app_icon(root, resources_dir)
        
        # استيراد وتشغيل التطبيق
        from shamela_gui import ShamelaGUI
        app = ShamelaGUI(root)
        
        # تحديد موقع النافذة في وسط الشاشة
        root.update_idletasks()
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width // 2) - (900 // 2)
        y = (screen_height // 2) - (700 // 2)
        root.geometry(f"900x700+{x}+{y}")
        
        print("✅ تم تشغيل التطبيق بنجاح")
        print("=" * 60)
        
        # بدء حلقة التطبيق
        root.mainloop()
        
        print("تم إغلاق التطبيق")
        return 0
        
    except ImportError as e:
        error_msg = f"""
خطأ في الاستيراد: {str(e)}

تأكد من أن جميع الملفات موجودة في المجلد الصحيح:
- src/shamela_gui.py
- src/shamela_converter.py  
- src/simple_bok_support.py

أو تأكد من تثبيت المتطلبات:
pip install -r requirements.txt
        """
        
        try:
            messagebox.showerror("خطأ في الاستيراد", error_msg)
        except:
            print("خطأ: " + error_msg)
        
        input("اضغط Enter للخروج...")
        return 1
        
    except Exception as e:
        error_msg = f"خطأ عام في التطبيق: {str(e)}"
        print(f"❌ {error_msg}")
        
        try:
            messagebox.showerror("خطأ", error_msg)
        except:
            pass
        
        input("اضغط Enter للخروج...")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)