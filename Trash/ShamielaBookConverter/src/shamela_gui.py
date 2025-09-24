from tkinter import ttk, filedialog, messagebox, scrolledtext
import tkinter as tk
import queue
import threading
import json
import os
from datetime import datetime, timedelta
import re
import time
from pathlib import Path
from Trash.simple_bok_support import SimpleBokConverter, process_bok_file_simple

class ShamelaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("محول كتب الشاملة - Shamela Books Converter v2.0")
        self.root.geometry("900x700")
        self.root.configure(bg='#f0f0f0')
        
        # قائمة الملفات المحددة
        self.selected_files = []
        
        # معالج ملفات .bok
        self.bok_converter = SimpleBokConverter()
        
        # إعدادات قاعدة البيانات الافتراضية
        self.db_config = {
            'host': '145.223.98.97',
            'port': 3306,
            'database': 'bms',
            'user': 'bms',
            'password': 'bms2025'
        }
        
        # قائمة انتظار الرسائل
        self.message_queue = queue.Queue()
        
        # متغيرات حالة التحويل
        self.conversion_running = False
        self.cancel_conversion_flag = False
        self.cancel_requested = False
        
        # متغيرات الوقت والتقدم المتقدمة
        self.start_time = None
        self.all_log_messages = []
        
        # إحصائيات التحويل المتقدمة
        self.total_files = 0
        self.current_file_index = 0
        self.books_stats = []  # قائمة إحصائيات كل كتاب
        self.current_book_stats = None
        
        self.create_widgets()
        self.load_settings()
        # لا نبدأ check_message_queue هنا، سيبدأ عند بدء التحويل
    
    def create_widgets(self):
        # العنوان الرئيسي
        title_label = tk.Label(self.root, text="محول كتب الشاملة v2.0", 
                              font=("Arial", 18, "bold"), 
                              bg='#f0f0f0', fg='#2c3e50')
        title_label.pack(pady=10)
        
        # إطار اختيار الملفات
        files_frame = tk.LabelFrame(self.root, text="اختيار ملفات الكتب (.accdb / .bok)", 
                                   font=("Arial", 12, "bold"), 
                                   bg='#f0f0f0', fg='#34495e')
        files_frame.pack(fill="x", padx=20, pady=10)
        
        # زر اختيار الملفات
        select_files_btn = tk.Button(files_frame, text="اختيار ملفات الكتب", 
                                    command=self.select_files,
                                    font=("Arial", 10, "bold"),
                                    bg='#3498db', fg='white',
                                    relief='flat', padx=20, pady=8)
        select_files_btn.pack(side="left", padx=10, pady=10)
        
        # زر مسح الملفات
        clear_files_btn = tk.Button(files_frame, text="مسح القائمة", 
                                   command=self.clear_files,
                                   font=("Arial", 10),
                                   bg='#e74c3c', fg='white',
                                   relief='flat', padx=20, pady=8)
        clear_files_btn.pack(side="left", padx=5, pady=10)
        
        # إطار قائمة الملفات مع أزرار إضافية
        files_list_frame = tk.Frame(files_frame, bg='#f0f0f0')
        files_list_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # قائمة الملفات المحددة
        self.files_listbox = tk.Listbox(files_list_frame, height=4, 
                                       font=("Arial", 9),
                                       bg='white', fg='#2c3e50',
                                       selectmode=tk.SINGLE)
        self.files_listbox.pack(side="left", fill="both", expand=True)
        
        # إطار أزرار إدارة الملفات
        files_buttons_frame = tk.Frame(files_list_frame, bg='#f0f0f0')
        files_buttons_frame.pack(side="right", fill="y", padx=(5, 0))
        
        # زر حذف ملف محدد
        delete_file_btn = tk.Button(files_buttons_frame, text="حذف المحدد", 
                                   command=self.delete_selected_file,
                                   font=("Arial", 8),
                                   bg='#e67e22', fg='white',
                                   relief='flat', padx=10, pady=3)
        delete_file_btn.pack(pady=(0, 2))
        
        # زر معاينة الملف
        preview_file_btn = tk.Button(files_buttons_frame, text="معاينة", 
                                    command=self.preview_selected_file,
                                    font=("Arial", 8),
                                    bg='#9b59b6', fg='white',
                                    relief='flat', padx=10, pady=3)
        preview_file_btn.pack(pady=2)
        
        # إطار إعدادات قاعدة البيانات
        db_frame = tk.LabelFrame(self.root, text="إعدادات قاعدة البيانات", 
                                font=("Arial", 12, "bold"),
                                bg='#f0f0f0', fg='#34495e')
        db_frame.pack(fill="x", padx=20, pady=10)
        
        # Grid لتنظيم الحقول
        db_inner_frame = tk.Frame(db_frame, bg='#f0f0f0')
        db_inner_frame.pack(fill="x", padx=10, pady=10)
        
        # حقول قاعدة البيانات
        tk.Label(db_inner_frame, text="الخادم:", font=("Arial", 10), 
                bg='#f0f0f0').grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.host_entry = tk.Entry(db_inner_frame, font=("Arial", 10), width=25)
        self.host_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(db_inner_frame, text="المنفذ:", font=("Arial", 10), 
                bg='#f0f0f0').grid(row=0, column=2, sticky="e", padx=5, pady=5)
        self.port_entry = tk.Entry(db_inner_frame, font=("Arial", 10), width=8)
        self.port_entry.grid(row=0, column=3, padx=5, pady=5)
        
        tk.Label(db_inner_frame, text="قاعدة البيانات:", font=("Arial", 10), 
                bg='#f0f0f0').grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.database_entry = tk.Entry(db_inner_frame, font=("Arial", 10), width=25)
        self.database_entry.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(db_inner_frame, text="اسم المستخدم:", font=("Arial", 10), 
                bg='#f0f0f0').grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.user_entry = tk.Entry(db_inner_frame, font=("Arial", 10), width=25)
        self.user_entry.grid(row=2, column=1, padx=5, pady=5)
        
        tk.Label(db_inner_frame, text="كلمة المرور:", font=("Arial", 10), 
                bg='#f0f0f0').grid(row=2, column=2, sticky="e", padx=5, pady=5)
        self.password_entry = tk.Entry(db_inner_frame, font=("Arial", 10), width=25, show="*")
        self.password_entry.grid(row=2, column=3, padx=5, pady=5)
        
        # ملاحظة عن كلمة المرور
        note_label = tk.Label(db_inner_frame, text="(اتركها فارغة إذا لم تكن مطلوبة)", 
                             font=("Arial", 8), bg='#f0f0f0', fg='#7f8c8d')
        note_label.grid(row=3, column=2, columnspan=2, sticky="w", padx=5)
        
        # أزرار الإعدادات
        db_buttons_frame = tk.Frame(db_frame, bg='#f0f0f0')
        db_buttons_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        test_db_btn = tk.Button(db_buttons_frame, text="اختبار الاتصال", 
                               command=self.test_connection,
                               font=("Arial", 10),
                               bg='#f39c12', fg='white',
                               relief='flat', padx=15, pady=5)
        test_db_btn.pack(side="left", padx=5)
        
        save_settings_btn = tk.Button(db_buttons_frame, text="حفظ الإعدادات", 
                                     command=self.save_settings,
                                     font=("Arial", 10),
                                     bg='#27ae60', fg='white',
                                     relief='flat', padx=15, pady=5)
        save_settings_btn.pack(side="left", padx=5)
        
        # إطار التحكم المتقدم
        control_frame = tk.Frame(self.root, bg='#f0f0f0')
        control_frame.pack(fill="x", padx=20, pady=10)
        
        # معلومات التقدم
        progress_info_frame = tk.Frame(control_frame, bg='#f0f0f0')
        progress_info_frame.pack(fill="x")
        
        # النص العلوي للحالة
        self.progress_var = tk.StringVar()
        self.progress_var.set("جاهز للبدء")
        progress_label = tk.Label(progress_info_frame, textvariable=self.progress_var,
                                 font=("Arial", 10), bg='#f0f0f0', fg='#7f8c8d')
        progress_label.pack(side="left")
        
        # معلومات التقدم (ملف حالي/إجمالي)
        self.progress_details_var = tk.StringVar()
        self.progress_details_var.set("")
        progress_details_label = tk.Label(progress_info_frame, textvariable=self.progress_details_var,
                                         font=("Arial", 9), bg='#f0f0f0', fg='#95a5a6')
        progress_details_label.pack(side="right")
        
        # شريط التقدم المحدد
        progress_frame = tk.Frame(control_frame, bg='#f0f0f0')
        progress_frame.pack(fill="x", pady=(5, 10))
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', maximum=100)
        self.progress_bar.pack(fill="x")
        
        # متغيرات التقدم
        self.total_files = 0
        self.current_file_index = 0
        
        # إطار أزرار التحكم
        control_buttons_frame = tk.Frame(control_frame, bg='#f0f0f0')
        control_buttons_frame.pack(pady=10)
        
        # زر البدء
        self.start_btn = tk.Button(control_buttons_frame, text="بدء التحويل", 
                                  command=self.start_conversion,
                                  font=("Arial", 12, "bold"),
                                  bg='#2ecc71', fg='white',
                                  relief='flat', padx=30, pady=10)
        self.start_btn.pack(side="left", padx=(0, 10))
        
        # زر الإلغاء/الإيقاف
        self.cancel_btn = tk.Button(control_buttons_frame, text="إيقاف", 
                                   command=self.cancel_conversion,
                                   font=("Arial", 11),
                                   bg='#e74c3c', fg='white',
                                   relief='flat', padx=20, pady=10,
                                   state="disabled")
        self.cancel_btn.pack(side="left", padx=5)
        
        # زر حفظ السجل
        self.save_log_btn = tk.Button(control_buttons_frame, text="حفظ السجل", 
                                     command=self.save_log,
                                     font=("Arial", 10),
                                     bg='#3498db', fg='white',
                                     relief='flat', padx=15, pady=10)
        self.save_log_btn.pack(side="left", padx=5)
        
        # زر تقرير الجلسة
        self.session_report_btn = tk.Button(control_buttons_frame, text="تقرير الجلسة", 
                                           command=self.show_session_report,
                                           font=("Arial", 10),
                                           bg='#9b59b6', fg='white',
                                           relief='flat', padx=15, pady=10)
        self.session_report_btn.pack(side="left", padx=5)
        
        # منطقة السجل
        log_frame = tk.LabelFrame(self.root, text="سجل العمليات", 
                                 font=("Arial", 12, "bold"),
                                 bg='#f0f0f0', fg='#34495e')
        log_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # شريط أدوات السجل
        log_toolbar = tk.Frame(log_frame, bg='#f0f0f0')
        log_toolbar.pack(fill="x", padx=5, pady=5)
        
        # فلتر السجل
        tk.Label(log_toolbar, text="فلتر:", font=("Arial", 9), bg='#f0f0f0').pack(side="left", padx=5)
        self.log_filter_var = tk.StringVar()
        log_filter_combo = ttk.Combobox(log_toolbar, textvariable=self.log_filter_var,
                                       values=["الكل", "معلومات", "تحذيرات", "أخطاء"],
                                       width=10, state="readonly")
        log_filter_combo.pack(side="left", padx=5)
        log_filter_combo.set("الكل")
        log_filter_combo.bind("<<ComboboxSelected>>", self.filter_log_messages)
        
        # زر مسح السجل
        clear_log_btn = tk.Button(log_toolbar, text="مسح السجل", 
                                 command=self.clear_log,
                                 font=("Arial", 9),
                                 bg='#95a5a6', fg='white',
                                 relief='flat', padx=10, pady=3)
        clear_log_btn.pack(side="right", padx=5)
        
        # منطقة نص السجل
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12,
                                                 font=("Consolas", 9),
                                                 bg='#2c3e50', fg='#ecf0f1',
                                                 wrap=tk.WORD, state=tk.DISABLED)
        self.log_text.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        
        # تكوين ألوان السجل
        self.log_text.tag_config("INFO", foreground="#3498db")
        self.log_text.tag_config("WARNING", foreground="#f39c12")
        self.log_text.tag_config("ERROR", foreground="#e74c3c")
        self.log_text.tag_config("SUCCESS", foreground="#2ecc71")
        self.log_text.tag_config("TIMESTAMP", foreground="#95a5a6")
        
        # تحديث الإعدادات في الحقول
        self.update_db_fields()
    
    def select_files(self):
        """اختيار ملفات الكتب"""
        files = filedialog.askopenfilenames(
            title="اختيار ملفات كتب الشاملة",
            filetypes=[
                ("جميع الملفات المدعومة", "*.accdb;*.mdb;*.bok"),
                ("ملفات Access", "*.accdb;*.mdb"),
                ("ملفات BOK", "*.bok"),
                ("جميع الملفات", "*.*")
            ]
        )
        
        if files:
            # إضافة الملفات الجديدة إلى القائمة مع تجنب التكرار
            for file_path in files:
                if file_path not in self.selected_files:
                    self.selected_files.append(file_path)
                    self.files_listbox.insert(tk.END, os.path.basename(file_path))
            
            self.log_message(f"تم اختيار {len(files)} ملف. إجمالي الملفات: {len(self.selected_files)}")
    
    def delete_selected_file(self):
        """حذف الملف المحدد من القائمة"""
        selection = self.files_listbox.curselection()
        if selection:
            index = selection[0]
            file_name = self.files_listbox.get(index)
            self.files_listbox.delete(index)
            
            # حذف من القائمة الأصلية
            if index < len(self.selected_files):
                removed_file = self.selected_files.pop(index)
                self.log_message(f"تم حذف الملف: {os.path.basename(removed_file)}")
        else:
            messagebox.showwarning("تحذير", "يرجى اختيار ملف للحذف")
    
    def preview_selected_file(self):
        """معاينة الملف المحدد"""
        selection = self.files_listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self.selected_files):
                file_path = self.selected_files[index]
                file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                file_modified = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%Y-%m-%d %H:%M:%S") if os.path.exists(file_path) else "غير معروف"
                
                preview_info = f"""
معلومات الملف:
الاسم: {os.path.basename(file_path)}
المسار: {file_path}
الحجم: {file_size:,} بايت ({file_size/1024/1024:.2f} ميغابايت)
تاريخ التعديل: {file_modified}
النوع: {os.path.splitext(file_path)[1].upper()}
                """
                messagebox.showinfo("معاينة الملف", preview_info.strip())
        else:
            messagebox.showwarning("تحذير", "يرجى اختيار ملف للمعاينة")
    
    def cancel_conversion(self):
        """إلغاء عملية التحويل"""
        self.cancel_requested = True
        self.cancel_conversion_flag = True
        self.log_message("تم طلب إيقاف عملية التحويل...", "WARNING")
        self.cancel_btn.config(state="disabled", text="جاري الإيقاف...")
    
    def save_log(self):
        """حفظ السجل في ملف"""
        if not self.all_log_messages:
            messagebox.showwarning("تحذير", "لا يوجد سجل للحفظ")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="حفظ سجل العمليات",
            defaultextension=".txt",
            filetypes=[
                ("ملفات نصية", "*.txt"),
                ("جميع الملفات", "*.*")
            ],
            initialname=f"shamela_conversion_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    # كتابة رأس التقرير
                    f.write("=== سجل عمليات محول كتب الشاملة ===\n")
                    f.write(f"تاريخ الإنشاء: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"عدد الملفات المعالجة: {len(self.selected_files)}\n")
                    f.write("="*50 + "\n\n")
                    
                    # كتابة الرسائل
                    for msg_data in self.all_log_messages:
                        f.write(f"[{msg_data['timestamp']}] {msg_data['level']}: {msg_data['message']}\n")
                    
                    # كتابة إحصائيات الجلسة إذا كانت متوفرة
                    if hasattr(self, 'books_stats') and self.books_stats:
                        f.write("\n" + "="*50 + "\n")
                        f.write("=== إحصائيات الجلسة ===\n")
                        for book_stat in self.books_stats:
                            f.write(f"الكتاب: {book_stat['book_name']}\n")
                            f.write(f"الصفحات: {book_stat['pages_count']}\n")
                            f.write(f"الوقت: {book_stat['duration']}\n")
                            f.write("-" * 30 + "\n")
                
                messagebox.showinfo("نجح", f"تم حفظ السجل في:\n{file_path}")
                self.log_message(f"تم حفظ السجل: {os.path.basename(file_path)}")
                
            except Exception as e:
                messagebox.showerror("خطأ", f"فشل في حفظ السجل:\n{str(e)}")
    
    def filter_log_messages(self, event=None):
        """فلترة رسائل السجل"""
        filter_value = self.log_filter_var.get()
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        
        for msg_data in self.all_log_messages:
            if filter_value == "الكل" or self.map_message_type(msg_data['level']) == filter_value:
                self.display_log_message(msg_data)
        
        self.log_text.config(state=tk.DISABLED)
        self.log_text.see(tk.END)
    
    def show_session_report(self):
        """إظهار تقرير الجلسة المفصل"""
        if not hasattr(self, 'books_stats') or not self.books_stats:
            messagebox.showinfo("معلومات", "لا توجد إحصائيات متاحة. يرجى تشغيل عملية تحويل أولاً.")
            return
        
        # إنشاء نافذة التقرير
        report_window = tk.Toplevel(self.root)
        report_window.title("تقرير الجلسة المفصل")
        report_window.geometry("800x600")
        report_window.configure(bg='#f0f0f0')
        
        # إطار التقرير
        report_frame = tk.Frame(report_window, bg='#f0f0f0')
        report_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # العنوان
        title_label = tk.Label(report_frame, text="تقرير جلسة التحويل", 
                              font=("Arial", 16, "bold"), 
                              bg='#f0f0f0', fg='#2c3e50')
        title_label.pack(pady=(0, 20))
        
        # منطقة النص
        report_text = scrolledtext.ScrolledText(report_frame, height=25,
                                               font=("Arial", 10),
                                               bg='white', fg='#2c3e50',
                                               wrap=tk.WORD)
        report_text.pack(fill="both", expand=True)
        
        # إنشاء محتوى التقرير
        report_content = self.generate_session_report()
        report_text.insert(1.0, report_content)
        report_text.config(state=tk.DISABLED)
        
        # أزرار التقرير
        buttons_frame = tk.Frame(report_frame, bg='#f0f0f0')
        buttons_frame.pack(fill="x", pady=(10, 0))
        
        # زر حفظ التقرير
        save_report_btn = tk.Button(buttons_frame, text="حفظ التقرير", 
                                   command=lambda: self.save_session_report(report_content),
                                   font=("Arial", 10),
                                   bg='#3498db', fg='white',
                                   relief='flat', padx=15, pady=5)
        save_report_btn.pack(side="left", padx=5)
        
        # زر إغلاق
        close_btn = tk.Button(buttons_frame, text="إغلاق", 
                             command=report_window.destroy,
                             font=("Arial", 10),
                             bg='#95a5a6', fg='white',
                             relief='flat', padx=15, pady=5)
        close_btn.pack(side="right", padx=5)
    
    def generate_session_report(self):
        """إنشاء تقرير مفصل للجلسة"""
        if not hasattr(self, 'books_stats') or not self.books_stats:
            return "لا توجد إحصائيات متاحة."
        
        report = []
        report.append("=" * 60)
        report.append("تقرير جلسة تحويل كتب الشاملة")
        report.append("=" * 60)
        report.append(f"تاريخ الجلسة: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # إحصائيات عامة
        total_books = len(self.books_stats)
        successful_books = len([b for b in self.books_stats if b.get('success', False)])
        failed_books = total_books - successful_books
        total_pages = sum(b.get('pages_count', 0) for b in self.books_stats)
        
        if hasattr(self, 'start_time') and self.start_time:
            total_duration = datetime.now() - self.start_time
            total_duration_str = str(total_duration).split('.')[0]  # إزالة الميكروثانية
        else:
            total_duration_str = "غير محدد"
        
        report.append("الإحصائيات العامة:")
        report.append("-" * 20)
        report.append(f"إجمالي الكتب: {total_books}")
        report.append(f"الكتب المحولة بنجاح: {successful_books}")
        report.append(f"الكتب الفاشلة: {failed_books}")
        report.append(f"إجمالي الصفحات: {total_pages:,}")
        report.append(f"المدة الإجمالية: {total_duration_str}")
        report.append("")
        
        # تفاصيل كل كتاب
        report.append("تفاصيل الكتب:")
        report.append("-" * 20)
        
        for i, book_stat in enumerate(self.books_stats, 1):
            status = "✅ نجح" if book_stat.get('success', False) else "❌ فشل"
            report.append(f"{i}. {book_stat.get('book_name', 'غير معروف')}")
            report.append(f"   الحالة: {status}")
            report.append(f"   الصفحات: {book_stat.get('pages_count', 0):,}")
            report.append(f"   المدة: {book_stat.get('duration', 'غير محدد')}")
            if book_stat.get('error_message'):
                report.append(f"   الخطأ: {book_stat['error_message']}")
            report.append("")
        
        return "\n".join(report)
    
    def save_session_report(self, report_content=None):
        """حفظ تقرير الجلسة"""
        if not report_content:
            report_content = self.generate_session_report()
        
        file_path = filedialog.asksaveasfilename(
            title="حفظ تقرير الجلسة",
            defaultextension=".txt",
            filetypes=[
                ("ملفات نصية", "*.txt"),
                ("ملفات HTML", "*.html"),
                ("جميع الملفات", "*.*")
            ],
            initialname=f"shamela_session_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        
        if file_path:
            try:
                if file_path.lower().endswith('.html'):
                    # تحويل التقرير إلى HTML
                    html_content = self.convert_report_to_html(report_content)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                else:
                    # حفظ كملف نصي
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(report_content)
                
                messagebox.showinfo("نجح", f"تم حفظ التقرير في:\n{file_path}")
                self.log_message(f"تم حفظ تقرير الجلسة: {os.path.basename(file_path)}")
                
            except Exception as e:
                messagebox.showerror("خطأ", f"فشل في حفظ التقرير:\n{str(e)}")
    
    def convert_report_to_html(self, report_content):
        """تحويل التقرير إلى تنسيق HTML"""
        html_content = f"""
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تقرير جلسة تحويل كتب الشاملة</title>
    <style>
        body {{
            font-family: 'Arial', sans-serif;
            line-height: 1.6;
            margin: 40px;
            background-color: #f4f4f4;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        .stats {{
            background: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .book-item {{
            margin: 10px 0;
            padding: 10px;
            border-right: 4px solid #3498db;
            background: #f8f9fa;
        }}
        .success {{ border-right-color: #2ecc71; }}
        .failed {{ border-right-color: #e74c3c; }}
        .timestamp {{
            color: #7f8c8d;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <pre>{report_content}</pre>
    </div>
</body>
</html>
        """
        return html_content

    def clear_log(self):
        """مسح سجل العمليات"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.all_log_messages.clear()
    
    def clear_files(self):
        """مسح قائمة الملفات"""
        self.selected_files.clear()
        self.files_listbox.delete(0, tk.END)
    
    def test_connection(self):
        """اختبار الاتصال بقاعدة البيانات"""
        self.update_db_config()
        
        try:
            from shamela_converter import ShamelaConverter
            
            converter = ShamelaConverter(self.db_config)
            
            if converter.connect_mysql():
                messagebox.showinfo("نجح", "تم الاتصال بقاعدة البيانات بنجاح!")
                self.log_message("تم اختبار الاتصال بنجاح", "SUCCESS")
                converter.mysql_conn.close()
            else:
                messagebox.showerror("فشل", "فشل في الاتصال بقاعدة البيانات")
                self.log_message("فشل اختبار الاتصال", "ERROR")
                
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في اختبار الاتصال:\n{str(e)}")
            self.log_message(f"خطأ في اختبار الاتصال: {str(e)}", "ERROR")
    
    def save_settings(self):
        """حفظ إعدادات قاعدة البيانات"""
        self.update_db_config()
        
        try:
            # إضافة timestamp للإعدادات
            settings_to_save = self.db_config.copy()
            settings_to_save['saved_at'] = datetime.now().isoformat()
            settings_to_save['version'] = '2.0'
            
            with open('db_settings.json', 'w', encoding='utf-8') as f:
                json.dump(settings_to_save, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo("نجح", "تم حفظ الإعدادات بنجاح")
            self.log_message("تم حفظ إعدادات قاعدة البيانات")
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في حفظ الإعدادات:\n{str(e)}")
    
    def load_settings(self):
        """تحميل إعدادات قاعدة البيانات"""
        try:
            if os.path.exists('db_settings.json'):
                with open('db_settings.json', 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                # تحديث الإعدادات
                self.db_config.update({
                    'host': settings.get('host', '145.223.98.97'),
                    'port': settings.get('port', 3306),
                    'database': settings.get('database', 'bms'),
                    'user': settings.get('user', 'bms'),
                    'password': settings.get('password', 'bms2025')
                })
                
                self.update_db_fields()
                self.log_message("تم تحميل إعدادات قاعدة البيانات")
        except Exception as e:
            self.log_message(f"تعذر تحميل الإعدادات: {str(e)}", "WARNING")
    
    def update_db_config(self):
        """تحديث إعدادات قاعدة البيانات من الحقول"""
        self.db_config = {
            'host': self.host_entry.get() or '145.223.98.97',
            'port': int(self.port_entry.get() or 3306),
            'database': self.database_entry.get() or 'bms',
            'user': self.user_entry.get() or 'bms',
            'password': self.password_entry.get() or 'bms2025',
            'charset': 'utf8mb4',
            'use_unicode': True
        }
        
        # إزالة كلمة المرور إذا كانت فارغة
        if not self.db_config['password']:
            self.db_config.pop('password', None)
    
    def update_db_fields(self):
        """تحديث حقول قاعدة البيانات من الإعدادات"""
        self.host_entry.delete(0, tk.END)
        self.host_entry.insert(0, self.db_config.get('host', ''))
        
        self.port_entry.delete(0, tk.END)
        self.port_entry.insert(0, str(self.db_config.get('port', '')))
        
        self.database_entry.delete(0, tk.END)
        self.database_entry.insert(0, self.db_config.get('database', ''))
        
        self.user_entry.delete(0, tk.END)
        self.user_entry.insert(0, self.db_config.get('user', ''))
        
        self.password_entry.delete(0, tk.END)
        self.password_entry.insert(0, self.db_config.get('password', ''))
    
    def start_conversion(self):
        """بدء عملية التحويل"""
        if not self.selected_files:
            messagebox.showwarning("تحذير", "يرجى اختيار ملفات للتحويل أولاً")
            return
        
        if self.conversion_running:
            messagebox.showwarning("تحذير", "عملية التحويل جارية بالفعل")
            return
        
        # تحديث إعدادات قاعدة البيانات
        self.update_db_config()
        
        # إعداد متغيرات الحالة
        self.conversion_running = True
        self.cancel_requested = False
        self.cancel_conversion_flag = False
        self.start_time = datetime.now()
        self.books_stats = []  # إعادة تعيين الإحصائيات
        
        # تحديث واجهة المستخدم
        self.start_btn.config(state="disabled", text="جاري التحويل...")
        self.cancel_btn.config(state="normal", text="إيقاف")
        self.progress_bar['value'] = 0
        self.total_files = len(self.selected_files)
        self.current_file_index = 0
        
        self.log_message(f"بدء تحويل {self.total_files} ملف...")
        self.log_message(f"إعدادات قاعدة البيانات: {self.db_config['user']}@{self.db_config['host']}")
        
        # بدء check_message_queue
        self.check_message_queue()
        
        # بدء المعالجة في thread منفصل
        conversion_thread = threading.Thread(target=self.run_conversion, daemon=True)
        conversion_thread.start()
    
    def run_conversion(self):
        """تشغيل عملية التحويل في thread منفصل"""
        successful_conversions = 0
        
        try:
            from shamela_converter import ShamelaConverter
            
            def progress_callback(message, level="INFO"):
                """callback لاستقبال رسائل التقدم"""
                self.message_queue.put({
                    'type': 'log',
                    'message': message,
                    'level': level,
                    'timestamp': datetime.now().strftime("%H:%M:%S")
                })
            
            # إنشاء المحول
            converter = ShamelaConverter(self.db_config, progress_callback)
            
            for i, file_path in enumerate(self.selected_files):
                if self.cancel_requested:
                    self.message_queue.put({
                        'type': 'log',
                        'message': "تم إلغاء عملية التحويل بواسطة المستخدم",
                        'level': 'WARNING',
                        'timestamp': datetime.now().strftime("%H:%M:%S")
                    })
                    break
                
                self.current_file_index = i + 1
                file_name = os.path.basename(file_path)
                
                # تحديث التقدم
                progress_percent = (i / self.total_files) * 100
                self.message_queue.put({
                    'type': 'progress',
                    'current': i + 1,
                    'total': self.total_files,
                    'percent': progress_percent,
                    'message': f"معالجة: {file_name}"
                })
                
                # بدء إحصائيات الكتاب الحالي
                book_start_time = datetime.now()
                self.current_book_stats = {
                    'book_name': file_name,
                    'start_time': book_start_time,
                    'pages_count': 0,
                    'success': False,
                    'error_message': None
                }
                
                self.message_queue.put({
                    'type': 'log',
                    'message': f"[{i+1}/{self.total_files}] بدء معالجة: {file_name}",
                    'level': 'INFO',
                    'timestamp': datetime.now().strftime("%H:%M:%S")
                })
                
                try:
                    # معالجة ملف .bok إذا لزم الأمر
                    if file_path.lower().endswith('.bok'):
                        def conversion_callback(converted_path):
                            return converter.convert_file(converted_path)
                        
                        success = process_bok_file_simple(file_path, conversion_callback, progress_callback)
                    else:
                        success = converter.convert_file(file_path)
                    
                    # تحديث إحصائيات الكتاب
                    book_end_time = datetime.now()
                    duration = book_end_time - book_start_time
                    duration_str = str(duration).split('.')[0]  # إزالة الميكروثانية
                    
                    self.current_book_stats.update({
                        'success': success,
                        'duration': duration_str,
                        'end_time': book_end_time
                    })
                    
                    if success:
                        successful_conversions += 1
                        self.message_queue.put({
                            'type': 'log',
                            'message': f"✅ تم تحويل: {file_name} ({duration_str})",
                            'level': 'SUCCESS',
                            'timestamp': datetime.now().strftime("%H:%M:%S")
                        })
                    else:
                        self.current_book_stats['error_message'] = "فشل التحويل"
                        self.message_queue.put({
                            'type': 'log',
                            'message': f"❌ فشل تحويل: {file_name}",
                            'level': 'ERROR',
                            'timestamp': datetime.now().strftime("%H:%M:%S")
                        })
                    
                    # إضافة إحصائيات الكتاب إلى القائمة
                    self.books_stats.append(self.current_book_stats.copy())
                    
                    # تحديث التقدم المتقدم
                    if hasattr(converter, 'conversion_log'):
                        # تحليل السجل لاستخراج معلومات إضافية
                        pages_info = self.parse_conversion_message('\n'.join(converter.conversion_log))
                        if pages_info:
                            self.current_book_stats['pages_count'] = pages_info.get('pages', 0)
                    
                except Exception as e:
                    error_message = str(e)
                    self.current_book_stats.update({
                        'success': False,
                        'error_message': error_message,
                        'duration': str(datetime.now() - book_start_time).split('.')[0]
                    })
                    self.books_stats.append(self.current_book_stats.copy())
                    
                    self.message_queue.put({
                        'type': 'log',
                        'message': f"❌ خطأ في معالجة {file_name}: {error_message}",
                        'level': 'ERROR',
                        'timestamp': datetime.now().strftime("%H:%M:%S")
                    })
            
            # تحديث التقدم النهائي
            self.message_queue.put({
                'type': 'progress',
                'current': self.total_files,
                'total': self.total_files,
                'percent': 100,
                'message': "اكتملت المعالجة"
            })
            
            # إضافة ملخص الجلسة
            self.add_session_summary(successful_conversions)
            
        except Exception as e:
            self.message_queue.put({
                'type': 'log',
                'message': f"خطأ عام في عملية التحويل: {str(e)}",
                'level': 'ERROR',
                'timestamp': datetime.now().strftime("%H:%M:%S")
            })
        finally:
            # إنهاء عملية التحويل
            self.message_queue.put({
                'type': 'conversion_complete',
                'successful': successful_conversions,
                'total': self.total_files
            })
    
    def parse_conversion_message(self, message):
        """تحليل رسائل التحويل لاستخراج معلومات مفيدة"""
        info = {}
        
        # البحث عن عدد الصفحات
        pages_match = re.search(r'تم استخراج (\d+) سجل', message)
        if pages_match:
            info['pages'] = int(pages_match.group(1))
        
        # البحث عن اسم الكتاب
        book_match = re.search(r'تم استخراج معلومات الكتاب: (.+)', message)
        if book_match:
            info['book_name'] = book_match.group(1)
        
        # البحث عن معلومات أخرى
        author_match = re.search(r'تم إدراج مؤلف جديد: (.+)', message)
        if author_match:
            info['author'] = author_match.group(1)
        
        return info
    
    def add_book_summary(self):
        """إضافة ملخص الكتاب الحالي"""
        if self.current_book_stats and self.current_book_stats.get('success'):
            pages = self.current_book_stats.get('pages_count', 0)
            duration = self.current_book_stats.get('duration', '0:00:00')
            
            self.message_queue.put({
                'type': 'log',
                'message': f"📊 ملخص: {pages:,} صفحة في {duration}",
                'level': 'INFO',
                'timestamp': datetime.now().strftime("%H:%M:%S")
            })
    
    def add_session_summary(self, successful_conversions):
        """إضافة ملخص الجلسة"""
        if self.start_time:
            total_duration = datetime.now() - self.start_time
            total_duration_str = str(total_duration).split('.')[0]
            
            total_pages = sum(book.get('pages_count', 0) for book in self.books_stats)
            failed_conversions = self.total_files - successful_conversions
            
            summary_lines = [
                "🎉 انتهت عملية التحويل!",
                f"📈 الإحصائيات النهائية:",
                f"   • الملفات المعالجة: {self.total_files}",
                f"   • نجح: {successful_conversions} | فشل: {failed_conversions}",
                f"   • إجمالي الصفحات: {total_pages:,}",
                f"   • المدة الإجمالية: {total_duration_str}",
                f"   • متوسط الوقت لكل ملف: {total_duration.total_seconds()/self.total_files:.1f} ثانية"
            ]
            
            for line in summary_lines:
                self.message_queue.put({
                    'type': 'log',
                    'message': line,
                    'level': 'SUCCESS' if line.startswith('🎉') else 'INFO',
                    'timestamp': datetime.now().strftime("%H:%M:%S")
                })

    def check_message_queue(self):
        """فحص قائمة انتظار الرسائل"""
        try:
            while True:
                try:
                    message = self.message_queue.get_nowait()
                    
                    if message['type'] == 'log':
                        self.log_message(message['message'], message['level'])
                    elif message['type'] == 'progress':
                        self.update_progress(message['current'], message['total'], message['message'])
                        self.progress_bar['value'] = message['percent']
                    elif message['type'] == 'conversion_complete':
                        self.conversion_complete(message['successful'], message['total'])
                        return  # توقف عن فحص الرسائل
                        
                except queue.Empty:
                    break
            
            # إعادة جدولة فحص الرسائل إذا كان التحويل مازال يعمل
            if self.conversion_running:
                self.root.after(100, self.check_message_queue)
                
        except Exception as e:
            self.log_message(f"خطأ في معالجة الرسائل: {str(e)}", "ERROR")
    
    def conversion_complete(self, successful, total):
        """انتهاء عملية التحويل"""
        self.conversion_running = False
        self.cancel_requested = False
        
        # تحديث واجهة المستخدم
        self.start_btn.config(state="normal", text="بدء التحويل")
        self.cancel_btn.config(state="disabled", text="إيقاف")
        self.progress_var.set(f"اكتمل - نجح {successful} من {total}")
        
        # إظهار رسالة النتيجة
        if successful == total:
            messagebox.showinfo("مبروك!", f"تم تحويل جميع الملفات بنجاح!\n{successful} ملف")
        elif successful > 0:
            messagebox.showwarning("انتهى جزئياً", f"تم تحويل {successful} من {total} ملف")
        else:
            messagebox.showerror("فشل", "فشل في تحويل جميع الملفات")
    
    def log_message(self, message, msg_type="INFO"):
        """إضافة رسالة إلى السجل"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # حفظ الرسالة في القائمة الشاملة
        msg_data = {
            'message': message,
            'level': msg_type,
            'timestamp': timestamp
        }
        self.all_log_messages.append(msg_data)
        
        # فلترة وعرض الرسالة
        filter_value = self.log_filter_var.get()
        mapped_type = self.map_message_type(msg_type)
        
        if filter_value == "الكل" or mapped_type == filter_value:
            self.display_log_message(msg_data)
    
    def map_message_type(self, msg_type):
        """تحويل نوع الرسالة للعربية"""
        mapping = {
            "INFO": "معلومات",
            "WARNING": "تحذيرات", 
            "ERROR": "أخطاء",
            "SUCCESS": "معلومات"
        }
        return mapping.get(msg_type, "معلومات")
    
    def update_status(self, message):
        """تحديث حالة التطبيق"""
        self.progress_var.set(message)
        
        # تحديث معلومات التقدم التفصيلية
        if hasattr(self, 'current_file_index') and hasattr(self, 'total_files'):
            if self.total_files > 0:
                details = f"الملف {self.current_file_index} من {self.total_files}"
                self.progress_details_var.set(details)
            
            # تحديث شريط التقدم
            if self.total_files > 0:
                progress_percent = (self.current_file_index / self.total_files) * 100
                self.progress_bar['value'] = progress_percent

    def display_log_message(self, msg_data):
        """عرض رسالة في منطقة السجل"""
        self.log_text.config(state=tk.NORMAL)
        
        # إضافة الرسالة مع التنسيق
        timestamp_tag = "TIMESTAMP"
        level_tag = msg_data['level']
        
        self.log_text.insert(tk.END, f"[{msg_data['timestamp']}] ", timestamp_tag)
        self.log_text.insert(tk.END, f"{msg_data['message']}\n", level_tag)
        
        self.log_text.config(state=tk.DISABLED)
        self.log_text.see(tk.END)
    
    def update_progress(self, current, total, message=""):
        """تحديث شريط التقدم"""
        if total > 0:
            progress_percent = (current / total) * 100
            self.progress_bar['value'] = progress_percent
            
            # تحديث النص
            if message:
                self.progress_var.set(message)
            
            # تحديث التفاصيل
            self.progress_details_var.set(f"الملف {current} من {total}")
        
        # تحديث الواجهة
        self.root.update_idletasks()
    
    def update_status(self, message):
        """تحديث حالة التطبيق"""
        self.progress_var.set(message)
        
        # تحديث معلومات التقدم التفصيلية
        if hasattr(self, 'current_file_index') and hasattr(self, 'total_files'):
            if self.total_files > 0:
                details = f"الملف {self.current_file_index} من {self.total_files}"
                self.progress_details_var.set(details)
        
        # تحديث الواجهة فوراً
        self.root.update_idletasks()
    
    def test_database_connection(self):
        """اختبار اتصال قاعدة البيانات"""
        self.update_db_config()
        
        try:
            from shamela_converter import ShamelaConverter
            converter = ShamelaConverter(self.db_config)
            
            if converter.connect_mysql():
                return True
            else:
                return False
        except Exception as e:
            self.log_message(f"خطأ في اختبار الاتصال: {str(e)}", "ERROR")
            return False


def main():
    root = tk.Tk()
    
    # تطبيق الستايل
    style = ttk.Style()
    style.theme_use('clam')
    
    app = ShamelaGUI(root)
    
    # جعل النافذة في المنتصف
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (900 // 2)
    y = (root.winfo_screenheight() // 2) - (700 // 2)
    root.geometry(f"900x700+{x}+{y}")
    
    root.mainloop()

if __name__ == "__main__":
    main()