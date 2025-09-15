#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار وظيفة حفظ تقرير الجلسة
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime

def test_save_session_report():
    """اختبار حفظ تقرير الجلسة"""
    
    # محاكاة بيانات الجلسة
    books_stats = [
        {
            'name': 'كتاب تجريبي 1',
            'volumes': 2,
            'chapters': 15,
            'pages': 250,
            'success': True,
            'status': 'مكتمل بنجاح',
            'start_time': datetime.now(),
            'end_time': datetime.now()
        },
        {
            'name': 'كتاب تجريبي 2',
            'volumes': 1,
            'chapters': 8,
            'pages': 120,
            'success': True,
            'status': 'مكتمل بنجاح',
            'start_time': datetime.now(),
            'end_time': datetime.now()
        }
    ]
    
    def generate_session_report():
        """إنشاء محتوى تقرير الجلسة"""
        report_lines = []
        
        # عنوان التقرير
        report_lines.append("="*60)
        report_lines.append("📊 تقرير جلسة التحويل المفصل")
        report_lines.append("="*60)
        report_lines.append(f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # الإحصائيات العامة
        successful_books = sum(1 for book in books_stats if book.get('success', False))
        failed_books = len(books_stats) - successful_books
        total_volumes = sum(book.get('volumes', 0) for book in books_stats)
        total_chapters = sum(book.get('chapters', 0) for book in books_stats)
        total_pages = sum(book.get('pages', 0) for book in books_stats)
        
        report_lines.append("📋 الإحصائيات العامة:")
        report_lines.append(f"   📚 إجمالي الكتب: {len(books_stats)}")
        report_lines.append(f"   ✅ نجح التحويل: {successful_books}")
        report_lines.append(f"   ❌ فشل التحويل: {failed_books}")
        report_lines.append(f"   📁 إجمالي المجلدات: {total_volumes}")
        report_lines.append(f"   📑 إجمالي الفصول: {total_chapters}")
        report_lines.append(f"   📄 إجمالي الصفحات: {total_pages}")
        report_lines.append("")
        
        # تفاصيل كل كتاب
        report_lines.append("📋 تفاصيل الكتب:")
        report_lines.append("-" * 60)
        
        for i, book in enumerate(books_stats, 1):
            status_icon = "✅" if book.get('success', False) else "❌"
            report_lines.append(f"{i}. {status_icon} {book['name']}")
            report_lines.append(f"   📊 الحالة: {book.get('status', 'غير محدد')}")
            report_lines.append(f"   📁 المجلدات: {book.get('volumes', 0)}")
            report_lines.append(f"   📑 الفصول: {book.get('chapters', 0)}")
            report_lines.append(f"   📄 الصفحات: {book.get('pages', 0)}")
            report_lines.append("")
        
        report_lines.append("="*60)
        report_lines.append("تم إنشاء التقرير بواسطة محول كتب الشاملة")
        report_lines.append("="*60)
        
        return '\n'.join(report_lines)
    
    def save_session_report():
        """حفظ تقرير الجلسة في ملف"""
        try:
            print("🔄 بدء عملية حفظ التقرير...")
            
            # التحقق من وجود بيانات للتقرير
            if not books_stats:
                print("❌ لا توجد بيانات جلسة متاحة للحفظ")
                return False
            
            print("✅ تم العثور على بيانات الجلسة")
            
            # إنشاء محتوى التقرير
            print("🔄 إنشاء محتوى التقرير...")
            report_content = generate_session_report()
            print(f"✅ تم إنشاء التقرير بحجم {len(report_content)} حرف")
            
            # إنشاء نافذة Tkinter مخفية
            root = tk.Tk()
            root.withdraw()  # إخفاء النافذة الرئيسية
            
            print("🔄 فتح مربع حوار الحفظ...")
            
            # اختيار مكان الحفظ
            file_path = filedialog.asksaveasfilename(
                title="حفظ تقرير الجلسة",
                defaultextension=".txt",
                filetypes=[("ملفات نصية", "*.txt"), ("كل الملفات", "*.*")],
                initialname=f"تقرير_جلسة_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
            
            if file_path:
                print(f"🔄 حفظ التقرير في: {file_path}")
                
                # حفظ التقرير في الملف
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                
                print(f"✅ تم حفظ تقرير الجلسة بنجاح في: {file_path}")
                
                # إظهار رسالة نجاح
                messagebox.showinfo("تم الحفظ", f"تم حفظ تقرير الجلسة بنجاح في:\n{file_path}")
                
                return True
            else:
                print("❌ تم إلغاء العملية من قبل المستخدم")
                return False
                
        except Exception as e:
            error_msg = f"فشل في حفظ التقرير: {str(e)}"
            print(f"❌ خطأ: {error_msg}")
            
            # إظهار رسالة خطأ
            try:
                messagebox.showerror("خطأ في الحفظ", error_msg)
            except:
                pass
            
            return False
        
        finally:
            try:
                root.destroy()
            except:
                pass
    
    # تنفيذ الاختبار
    print("="*60)
    print("🧪 اختبار وظيفة حفظ تقرير الجلسة")
    print("="*60)
    
    success = save_session_report()
    
    if success:
        print("\n✅ نجح الاختبار! وظيفة حفظ التقرير تعمل بشكل صحيح")
    else:
        print("\n❌ فشل الاختبار! هناك مشكلة في وظيفة حفظ التقرير")
    
    print("="*60)

if __name__ == "__main__":
    test_save_session_report()
