#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار مبسط لحفظ تقرير الجلسة مع بيانات وهمية
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
from datetime import datetime

class TestSessionReport:
    def __init__(self):
        # بيانات وهمية للاختبار
        self.books_stats = [
            {
                'name': 'كتاب البخاري',
                'volumes': 3,
                'chapters': 97,
                'pages': 1250,
                'success': True,
                'status': 'مكتمل بنجاح',
                'start_time': datetime.now(),
                'end_time': datetime.now()
            },
            {
                'name': 'كتاب مسلم',
                'volumes': 2,
                'chapters': 54,
                'pages': 980,
                'success': True,
                'status': 'مكتمل بنجاح',
                'start_time': datetime.now(),
                'end_time': datetime.now()
            }
        ]
        
        self.start_time = datetime.now()
    
    def generate_session_report(self):
        """إنشاء محتوى تقرير الجلسة"""
        report_lines = []
        
        # عنوان التقرير
        report_lines.append("="*60)
        report_lines.append("📊 تقرير جلسة التحويل المفصل")
        report_lines.append("="*60)
        report_lines.append(f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # الإحصائيات العامة
        successful_books = sum(1 for book in self.books_stats if book.get('success', False))
        failed_books = len(self.books_stats) - successful_books
        total_volumes = sum(book.get('volumes', 0) for book in self.books_stats)
        total_chapters = sum(book.get('chapters', 0) for book in self.books_stats)
        total_pages = sum(book.get('pages', 0) for book in self.books_stats)
        
        report_lines.append("📋 الإحصائيات العامة:")
        report_lines.append(f"   📚 إجمالي الكتب: {len(self.books_stats)}")
        report_lines.append(f"   ✅ نجح التحويل: {successful_books}")
        report_lines.append(f"   ❌ فشل التحويل: {failed_books}")
        report_lines.append(f"   📁 إجمالي المجلدات: {total_volumes}")
        report_lines.append(f"   📑 إجمالي الفصول: {total_chapters}")
        report_lines.append(f"   📄 إجمالي الصفحات: {total_pages}")
        
        if self.start_time:
            total_time = datetime.now() - self.start_time
            report_lines.append(f"   ⏱️ إجمالي الوقت: {str(total_time).split('.')[0]}")
        
        report_lines.append("")
        
        # تفاصيل كل كتاب
        report_lines.append("📋 تفاصيل الكتب:")
        report_lines.append("-" * 60)
        
        for i, book in enumerate(self.books_stats, 1):
            status_icon = "✅" if book.get('success', False) else "❌"
            report_lines.append(f"{i}. {status_icon} {book['name']}")
            report_lines.append(f"   📊 الحالة: {book.get('status', 'غير محدد')}")
            report_lines.append(f"   📁 المجلدات: {book.get('volumes', 0)}")
            report_lines.append(f"   📑 الفصول: {book.get('chapters', 0)}")
            report_lines.append(f"   📄 الصفحات: {book.get('pages', 0)}")
            
            if 'start_time' in book and 'end_time' in book:
                duration = book['end_time'] - book['start_time']
                report_lines.append(f"   ⏱️ المدة: {str(duration).split('.')[0]}")
            
            report_lines.append("")
        
        report_lines.append("="*60)
        report_lines.append("تم إنشاء التقرير بواسطة محول كتب الشاملة")
        report_lines.append("="*60)
        
        return '\n'.join(report_lines)
    
    def save_session_report(self):
        """حفظ تقرير الجلسة في ملف"""
        try:
            print("🔄 بدء عملية الحفظ...")
            
            # التحقق من وجود بيانات للتقرير
            if not hasattr(self, 'books_stats') or not self.books_stats:
                messagebox.showwarning("تحذير", "لا توجد بيانات جلسة متاحة للحفظ")
                return
            
            print("✅ وجدت بيانات الجلسة")
            
            # إنشاء محتوى التقرير
            try:
                report_content = self.generate_session_report()
                if not report_content or len(report_content.strip()) == 0:
                    messagebox.showerror("خطأ", "فشل في إنشاء محتوى التقرير")
                    return
                print(f"✅ تم إنشاء التقرير بحجم {len(report_content)} حرف")
            except Exception as e:
                print(f"❌ خطأ في إنشاء التقرير: {e}")
                messagebox.showerror("خطأ", f"خطأ في إنشاء التقرير:\n{str(e)}")
                return
            
            # تحديد اسم الملف الافتراضي
            try:
                default_filename = f"تقرير_جلسة_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            except:
                default_filename = "تقرير_جلسة.txt"
            
            print(f"🔄 اسم الملف الافتراضي: {default_filename}")
            
            # اختيار مكان الحفظ
            try:
                file_path = filedialog.asksaveasfilename(
                    title="حفظ تقرير الجلسة",
                    defaultextension=".txt",
                    filetypes=[
                        ("ملفات نصية", "*.txt"), 
                        ("جميع الملفات", "*.*")
                    ],
                    initialfile=default_filename
                )
                print(f"📁 المسار المختار: {file_path}")
            except Exception as e:
                print(f"❌ خطأ في مربع الحوار: {e}")
                messagebox.showerror("خطأ", f"خطأ في فتح مربع الحوار:\n{str(e)}")
                return
            
            if not file_path:
                print("⚠️ المستخدم ألغى العملية")
                return
            
            # التأكد من أن الملف ينتهي بـ .txt
            if not file_path.lower().endswith('.txt'):
                file_path += '.txt'
                print(f"📁 المسار بعد إضافة .txt: {file_path}")
            
            # حفظ التقرير في الملف
            try:
                print("🔄 بدء الكتابة في الملف...")
                with open(file_path, 'w', encoding='utf-8', newline='') as f:
                    f.write(report_content)
                
                print("✅ تم الكتابة في الملف")
                
                # التحقق من أن الملف تم إنشاؤه بنجاح
                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    file_size = os.path.getsize(file_path)
                    success_msg = f"تم حفظ تقرير الجلسة بنجاح في:\n{file_path}\n\nحجم الملف: {file_size} بايت"
                    print(f"✅ نجح الحفظ! حجم الملف: {file_size} بايت")
                    messagebox.showinfo("تم الحفظ بنجاح", success_msg)
                else:
                    print("❌ الملف غير موجود أو فارغ")
                    messagebox.showerror("خطأ", "فشل في إنشاء الملف أو الملف فارغ")
                    
            except PermissionError:
                error_msg = f"ليس لديك صلاحية للكتابة في هذا المكان:\n{file_path}\n\nحاول اختيار مكان آخر أو تشغيل البرنامج كمسؤول"
                print(f"❌ خطأ صلاحيات: {error_msg}")
                messagebox.showerror("خطأ في الصلاحيات", error_msg)
            except Exception as e:
                error_msg = f"فشل في حفظ الملف:\n{str(e)}"
                print(f"❌ خطأ في الحفظ: {error_msg}")
                messagebox.showerror("خطأ في الحفظ", error_msg)
                
        except Exception as e:
            # خطأ عام غير متوقع
            error_msg = f"خطأ غير متوقع في حفظ التقرير:\n{str(e)}"
            print(f"❌ خطأ عام: {error_msg}")
            messagebox.showerror("خطأ عام", error_msg)

def create_test_gui():
    """إنشاء واجهة اختبار بسيطة"""
    root = tk.Tk()
    root.title("اختبار حفظ تقرير الجلسة")
    root.geometry("400x300")
    
    # إنشاء مثيل من كلاس الاختبار
    test_report = TestSessionReport()
    
    # عنوان
    title_label = tk.Label(root, text="اختبار حفظ تقرير الجلسة", 
                          font=("Arial", 16, "bold"))
    title_label.pack(pady=20)
    
    # معلومات البيانات الوهمية
    info_label = tk.Label(root, text=f"البيانات الوهمية: {len(test_report.books_stats)} كتاب", 
                         font=("Arial", 12))
    info_label.pack(pady=10)
    
    # زر اختبار الحفظ
    test_btn = tk.Button(root, text="اختبار حفظ التقرير", 
                        command=test_report.save_session_report,
                        font=("Arial", 12, "bold"),
                        bg='#27ae60', fg='white',
                        padx=30, pady=10)
    test_btn.pack(pady=20)
    
    # زر إغلاق
    close_btn = tk.Button(root, text="إغلاق", 
                         command=root.quit,
                         font=("Arial", 10),
                         bg='#95a5a6', fg='white',
                         padx=20, pady=8)
    close_btn.pack(pady=10)
    
    return root

if __name__ == "__main__":
    print("="*60)
    print("🧪 اختبار حفظ تقرير الجلسة")
    print("="*60)
    
    # إنشاء واجهة الاختبار
    root = create_test_gui()
    
    # تشغيل التطبيق
    root.mainloop()
    
    print("="*60)
    print("انتهى الاختبار")
    print("="*60)
