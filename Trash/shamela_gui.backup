import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
import json
import os
from datetime import datetime, timedelta
import pyodbc
import mysql.connector
from pathlib import Path
from simple_bok_support import SimpleBokConverter, process_bok_file_simple

class ShamelaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("محول كتب الشاملة - Shamela Books Converter")
        self.root.geometry("900x700")
        self.root.configure(bg='#f0f0f0')
        
        # قائمة الملفات المحددة
        self.selected_files = []
        
        # معالج ملفات .bok
        self.bok_converter = SimpleBokConverter()
        
        # إعدادات قاعدة البيانات الافتراضية
        self.db_config = {
            'host': 'srv1800.hstgr.io',
            'port': 3306,
            'database': 'u994369532_test',
            'user': 'u994369532_shamela',
            'password': 'mT8$pR3@vK9#'
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
        title_label = tk.Label(self.root, text="محول كتب الشاملة", 
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
        
        # منطقة سجل الأحداث المتقدمة
        log_frame = tk.LabelFrame(self.root, text="سجل الأحداث", 
                                 font=("Arial", 12, "bold"),
                                 bg='#f0f0f0', fg='#34495e')
        log_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # إطار أدوات السجل
        log_tools_frame = tk.Frame(log_frame, bg='#f0f0f0')
        log_tools_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        # أزرار تصفية الرسائل
        tk.Label(log_tools_frame, text="تصفية:", font=("Arial", 9), 
                bg='#f0f0f0').pack(side="left", padx=(0, 5))
        
        self.filter_var = tk.StringVar(value="الكل")
        filter_options = ["الكل", "معلومات", "نجاح", "خطأ", "تحذير"]
        self.filter_combo = ttk.Combobox(log_tools_frame, textvariable=self.filter_var,
                                        values=filter_options, state="readonly", width=10)
        self.filter_combo.pack(side="left", padx=5)
        self.filter_combo.bind("<<ComboboxSelected>>", self.filter_log_messages)
        
        # زر مسح السجل
        clear_log_btn = tk.Button(log_tools_frame, text="مسح السجل", 
                                 command=self.clear_log,
                                 font=("Arial", 8),
                                 bg='#95a5a6', fg='white',
                                 relief='flat', padx=10, pady=3)
        clear_log_btn.pack(side="right", padx=5)
        
        # إطار السجل مع scroll
        log_display_frame = tk.Frame(log_frame, bg='#f0f0f0')
        log_display_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.log_text = tk.Text(log_display_frame, height=15, 
                               font=("Consolas", 9),
                               bg='#2c3e50', fg='#ecf0f1',
                               insertbackground='#ecf0f1',
                               wrap=tk.WORD)
        
        # إعداد الألوان للرسائل المختلفة
        self.log_text.tag_configure("INFO", foreground="#74b9ff")      # أزرق فاتح
        self.log_text.tag_configure("SUCCESS", foreground="#00b894")   # أخضر
        self.log_text.tag_configure("ERROR", foreground="#e17055")     # أحمر
        self.log_text.tag_configure("WARNING", foreground="#fdcb6e")   # أصفر
        self.log_text.tag_configure("PROGRESS", foreground="#a29bfe")  # بنفسجي
        self.log_text.tag_configure("timestamp", foreground="#636e72") # رمادي
        
        # إضافة scrollbar للسجل
        log_scrollbar = ttk.Scrollbar(log_display_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scrollbar.pack(side="right", fill="y")
        
        # شريط الحالة المتقدم
        status_frame = tk.Frame(self.root, bg='#34495e', height=35)
        status_frame.pack(fill="x", side="bottom")
        status_frame.pack_propagate(False)
        
        # الحالة الرئيسية
        self.status_var = tk.StringVar()
        self.status_var.set("جاهز")
        status_label = tk.Label(status_frame, textvariable=self.status_var,
                               font=("Arial", 9), bg='#34495e', fg='white')
        status_label.pack(side="left", padx=10, pady=8)
        
        # معلومات إضافية
        self.status_details_var = tk.StringVar()
        self.status_details_var.set("")
        status_details_label = tk.Label(status_frame, textvariable=self.status_details_var,
                                       font=("Arial", 8), bg='#34495e', fg='#bdc3c7')
        status_details_label.pack(side="left", padx=(20, 10))
        
        # وقت العملية
        self.time_var = tk.StringVar()
        self.time_var.set("")
        time_label = tk.Label(status_frame, textvariable=self.time_var,
                             font=("Arial", 8), bg='#34495e', fg='#95a5a6')
        time_label.pack(side="right", padx=10, pady=8)
    
    def select_files(self):
        files = filedialog.askopenfilenames(
            title="اختيار ملفات الكتب",
            filetypes=[
                ("ملفات الشاملة", "*.accdb;*.bok"), 
                ("Access Database", "*.accdb"), 
                ("ملفات BOK", "*.bok"),
                ("كل الملفات", "*.*")
            ]
        )
        
        for file in files:
            if file not in self.selected_files:
                self.selected_files.append(file)
                
                # إضافة رمز نوع الملف
                file_display = os.path.basename(file)
                if file.lower().endswith('.bok'):
                    file_display += " [BOK]"
                elif file.lower().endswith('.accdb'):
                    file_display += " [ACCDB]"
                
                self.files_listbox.insert(tk.END, file_display)
        
        self.log_message(f"تم اختيار {len(files)} ملف جديد")
        self.update_status(f"تم تحديد {len(self.selected_files)} ملف")
    
    def delete_selected_file(self):
        """حذف الملف المحدد من القائمة"""
        try:
            selection = self.files_listbox.curselection()
            if not selection:
                messagebox.showwarning("تحذير", "يرجى تحديد ملف للحذف")
                return
            
            index = selection[0]
            file_name = self.files_listbox.get(index)
            
            if messagebox.askyesno("تأكيد الحذف", f"هل تريد حذف الملف:\n{file_name}"):
                # حذف من القائمة المرئية والقائمة الداخلية
                self.files_listbox.delete(index)
                del self.selected_files[index]
                
                self.log_message(f"تم حذف الملف: {file_name}", "INFO")
                self.update_status(f"تم تحديد {len(self.selected_files)} ملف")
                
        except Exception as e:
            self.log_message(f"خطأ في حذف الملف: {str(e)}", "ERROR")
    
    def preview_selected_file(self):
        """معاينة معلومات الملف المحدد"""
        try:
            selection = self.files_listbox.curselection()
            if not selection:
                messagebox.showwarning("تحذير", "يرجى تحديد ملف للمعاينة")
                return
            
            index = selection[0]
            file_path = self.selected_files[index]
            
            # جمع معلومات الملف
            file_info = []
            file_info.append(f"اسم الملف: {os.path.basename(file_path)}")
            file_info.append(f"المسار: {file_path}")
            
            if os.path.exists(file_path):
                stat_info = os.stat(file_path)
                file_size = stat_info.st_size
                
                # تحويل الحجم لوحدة مناسبة
                if file_size < 1024:
                    size_str = f"{file_size} بايت"
                elif file_size < 1024*1024:
                    size_str = f"{file_size/1024:.1f} كيلو بايت"
                else:
                    size_str = f"{file_size/(1024*1024):.1f} ميجا بايت"
                
                file_info.append(f"الحجم: {size_str}")
                
                # تاريخ التعديل
                import time
                mod_time = time.ctime(stat_info.st_mtime)
                file_info.append(f"تاريخ التعديل: {mod_time}")
                
                # نوع الملف
                if file_path.lower().endswith('.bok'):
                    file_info.append("النوع: ملف BOK (مضغوط)")
                elif file_path.lower().endswith('.accdb'):
                    file_info.append("النوع: قاعدة بيانات Access")
            else:
                file_info.append("⚠️ تحذير: الملف غير موجود!")
            
            messagebox.showinfo("معلومات الملف", "\n".join(file_info))
            
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في معاينة الملف:\n{str(e)}")
    
    def cancel_conversion(self):
        """إلغاء عملية التحويل"""
        if not self.conversion_running:
            return
        
        if messagebox.askyesno("تأكيد الإلغاء", "هل تريد إيقاف عملية التحويل؟"):
            self.cancel_requested = True
            self.log_message("تم طلب إيقاف العملية...", "WARNING")
            self.update_status("جاري الإيقاف...")
    
    def save_log(self):
        """حفظ سجل الأحداث في ملف"""
        try:
            if not hasattr(self, 'all_log_messages') or not self.all_log_messages:
                messagebox.showwarning("تحذير", "لا يوجد محتوى في السجل للحفظ")
                return
            
            # تحديد اسم الملف الافتراضي
            try:
                default_filename = f"سجل_الأحداث_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            except:
                default_filename = "سجل_الأحداث.txt"
            
            # اختيار مكان الحفظ
            try:
                file_path = filedialog.asksaveasfilename(
                    title="حفظ سجل الأحداث",
                    defaultextension=".txt",
                    filetypes=[("ملفات نصية", "*.txt"), ("جميع الملفات", "*.*")],
                    initialfile=default_filename
                )
            except Exception as e:
                messagebox.showerror("خطأ", f"خطأ في فتح مربع الحوار:\n{str(e)}")
                return
            
            if not file_path:
                return  # المستخدم ألغى العملية
            
            # التأكد من أن الملف ينتهي بـ .txt
            if not file_path.lower().endswith('.txt'):
                file_path += '.txt'
            
            # حفظ السجل في الملف
            try:
                with open(file_path, 'w', encoding='utf-8', newline='') as f:
                    f.write("=== سجل أحداث محول كتب الشاملة ===\n")
                    f.write(f"تاريخ الإنشاء: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("="*50 + "\n\n")
                    
                    for msg_data in self.all_log_messages:
                        f.write(f"{msg_data['full_message']}\n")
                
                # التحقق من نجاح الحفظ
                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    file_size = os.path.getsize(file_path)
                    success_msg = f"تم حفظ السجل بنجاح في:\n{file_path}\n\nحجم الملف: {file_size} بايت"
                    messagebox.showinfo("تم الحفظ بنجاح", success_msg)
                    self.log_message(f"💾 تم حفظ السجل: {os.path.basename(file_path)}", "SUCCESS")
                else:
                    messagebox.showerror("خطأ", "فشل في إنشاء الملف أو الملف فارغ")
                
            except PermissionError:
                messagebox.showerror("خطأ في الصلاحيات", 
                    f"ليس لديك صلاحية للكتابة في هذا المكان:\n{file_path}\n\nحاول اختيار مكان آخر أو تشغيل البرنامج كمسؤول")
            except Exception as e:
                messagebox.showerror("خطأ في الحفظ", f"فشل في حفظ السجل:\n{str(e)}")
                
        except Exception as e:
            messagebox.showerror("خطأ عام", f"خطأ غير متوقع في حفظ السجل:\n{str(e)}")
    
    def filter_log_messages(self, event=None):
        """تصفية رسائل السجل حسب النوع"""
        try:
            filter_type = self.filter_var.get()
            
            # مسح السجل الحالي
            self.log_text.delete(1.0, tk.END)
            
            # إعادة عرض الرسائل المفلترة
            for msg_data in self.all_log_messages:
                if filter_type == "الكل" or msg_data['type'] == filter_type:
                    self.display_log_message(msg_data)
            
            # التمرير للأسفل
            self.log_text.see(tk.END)
            
        except Exception as e:
            print(f"خطأ في التصفية: {e}")
    
    def show_session_report(self):
        """عرض تقرير مفصل لجلسة التحويل"""
        if not self.books_stats:
            messagebox.showinfo("تقرير الجلسة", "لا توجد بيانات جلسة متاحة")
            return
        
        # إنشاء نافذة التقرير
        report_window = tk.Toplevel(self.root)
        report_window.title("تقرير جلسة التحويل")
        report_window.geometry("800x600")
        report_window.configure(bg='#f0f0f0')
        
        # عنوان التقرير
        title_label = tk.Label(report_window, text="📊 تقرير جلسة التحويل", 
                              font=("Arial", 16, "bold"), 
                              bg='#f0f0f0', fg='#2c3e50')
        title_label.pack(pady=10)
        
        # إطار التقرير مع scroll
        report_frame = tk.Frame(report_window, bg='#f0f0f0')
        report_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        report_text = scrolledtext.ScrolledText(report_frame, 
                                               font=("Consolas", 10),
                                               bg='white', fg='#2c3e50',
                                               wrap=tk.WORD)
        report_text.pack(fill="both", expand=True)
        
        # إعداد الألوان
        report_text.tag_configure("header", foreground="#2c3e50", font=("Arial", 12, "bold"))
        report_text.tag_configure("success", foreground="#27ae60")
        report_text.tag_configure("error", foreground="#e74c3c") 
        report_text.tag_configure("info", foreground="#3498db")
        
        # بناء محتوى التقرير
        report_content = self.generate_session_report()
        
        # إدراج المحتوى مع التنسيق
        lines = report_content.split('\n')
        for line in lines:
            if line.startswith('=') or 'ملخص' in line or 'تقرير' in line:
                report_text.insert(tk.END, line + '\n', "header")
            elif '✅' in line or 'نجح' in line:
                report_text.insert(tk.END, line + '\n', "success")
            elif '❌' in line or 'فشل' in line:
                report_text.insert(tk.END, line + '\n', "error")
            else:
                report_text.insert(tk.END, line + '\n', "info")
        
        report_text.configure(state="disabled")
        
        # أزرار التحكم
        buttons_frame = tk.Frame(report_window, bg='#f0f0f0')
        buttons_frame.pack(pady=10)
        
        # زر حفظ التقرير
        save_report_btn = tk.Button(buttons_frame, text="حفظ التقرير", 
                                   command=self.save_session_report,
                                   font=("Arial", 10),
                                   bg='#27ae60', fg='white',
                                   relief='flat', padx=20, pady=8)
        save_report_btn.pack(side="left", padx=10)
        
        # زر إغلاق
        close_btn = tk.Button(buttons_frame, text="إغلاق", 
                             command=report_window.destroy,
                             font=("Arial", 10),
                             bg='#95a5a6', fg='white',
                             relief='flat', padx=20, pady=8)
        close_btn.pack(side="left", padx=10)
    
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
        
        # معدل الأداء
        if successful_books > 0 and self.start_time:
            total_seconds = (datetime.now() - self.start_time).total_seconds()
            if total_seconds > 0:
                books_per_minute = (successful_books / total_seconds) * 60
                pages_per_minute = (total_pages / total_seconds) * 60
                report_lines.append("📊 معدل الأداء:")
                report_lines.append(f"   📚 {books_per_minute:.1f} كتاب/دقيقة")
                report_lines.append(f"   📄 {pages_per_minute:.1f} صفحة/دقيقة")
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
            # التحقق من وجود بيانات للتقرير
            if not hasattr(self, 'books_stats') or not self.books_stats:
                messagebox.showwarning("تحذير", "لا توجد بيانات جلسة متاحة للحفظ")
                return
            
            # إنشاء محتوى التقرير
            try:
                report_content = self.generate_session_report()
                if not report_content or len(report_content.strip()) == 0:
                    messagebox.showerror("خطأ", "فشل في إنشاء محتوى التقرير")
                    return
            except Exception as e:
                messagebox.showerror("خطأ", f"خطأ في إنشاء التقرير:\n{str(e)}")
                return
            
            # تحديد اسم الملف الافتراضي
            try:
                default_filename = f"تقرير_جلسة_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            except:
                default_filename = "تقرير_جلسة.txt"
            
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
            except Exception as e:
                messagebox.showerror("خطأ", f"خطأ في فتح مربع الحوار:\n{str(e)}")
                return
            
            if not file_path:
                # المستخدم ألغى العملية
                return
            
            # التأكد من أن الملف ينتهي بـ .txt
            if not file_path.lower().endswith('.txt'):
                file_path += '.txt'
            
            # حفظ التقرير في الملف
            try:
                with open(file_path, 'w', encoding='utf-8', newline='') as f:
                    f.write(report_content)
                
                # التحقق من أن الملف تم إنشاؤه بنجاح
                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    success_msg = f"تم حفظ تقرير الجلسة بنجاح في:\n{file_path}"
                    messagebox.showinfo("تم الحفظ بنجاح", success_msg)
                    
                    # تسجيل النجاح في السجل
                    if hasattr(self, 'log_message'):
                        self.log_message(f"💾 تم حفظ تقرير الجلسة: {os.path.basename(file_path)}", "SUCCESS")
                else:
                    messagebox.showerror("خطأ", "فشل في إنشاء الملف أو الملف فارغ")
                    
            except PermissionError:
                messagebox.showerror("خطأ في الصلاحيات", 
                    f"ليس لديك صلاحية للكتابة في هذا المكان:\n{file_path}\n\nحاول اختيار مكان آخر أو تشغيل البرنامج كمسؤول")
            except Exception as e:
                messagebox.showerror("خطأ في الحفظ", f"فشل في حفظ الملف:\n{str(e)}")
                
        except Exception as e:
            # خطأ عام غير متوقع
            error_msg = f"خطأ غير متوقع في حفظ التقرير:\n{str(e)}"
            messagebox.showerror("خطأ عام", error_msg)
            
            # تسجيل الخطأ في السجل إذا أمكن
            try:
                if hasattr(self, 'log_message'):
                    self.log_message(f"❌ خطأ في حفظ التقرير: {str(e)}", "ERROR")
            except:
                pass

    def clear_log(self):
        """مسح سجل الأحداث"""
        if messagebox.askyesno("تأكيد المسح", "هل تريد مسح سجل الأحداث؟"):
            self.log_text.delete(1.0, tk.END)
            self.all_log_messages.clear()
            self.log_message("تم مسح سجل الأحداث", "INFO")
    
    def clear_files(self):
        self.selected_files.clear()
        self.files_listbox.delete(0, tk.END)
        self.log_message("تم مسح قائمة الملفات")
        self.update_status("جاهز")
    
    def test_connection(self):
        self.update_db_config()
        
        try:
            # إعداد معاملات الاتصال
            connection_params = self.db_config.copy()
            
            # إزالة كلمة المرور إذا كانت فارغة
            if not connection_params.get('password'):
                connection_params.pop('password', None)
            
            connection = mysql.connector.connect(**connection_params)
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            connection.close()
            
            messagebox.showinfo("نجح الاتصال", "تم الاتصال بقاعدة البيانات بنجاح!")
            self.log_message("✅ تم اختبار الاتصال بقاعدة البيانات بنجاح")
            
        except Exception as e:
            messagebox.showerror("فشل الاتصال", f"فشل في الاتصال بقاعدة البيانات:\n{str(e)}")
            self.log_message(f"❌ فشل اختبار الاتصال: {str(e)}")
    
    def save_settings(self):
        self.update_db_config()
        
        try:
            with open("db_settings.json", "w", encoding="utf-8") as f:
                json.dump(self.db_config, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo("تم الحفظ", "تم حفظ إعدادات قاعدة البيانات بنجاح!")
            self.log_message("💾 تم حفظ إعدادات قاعدة البيانات")
            
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في حفظ الإعدادات:\n{str(e)}")
            self.log_message(f"❌ فشل حفظ الإعدادات: {str(e)}")
    
    def load_settings(self):
        try:
            if os.path.exists("db_settings.json"):
                with open("db_settings.json", "r", encoding="utf-8") as f:
                    self.db_config = json.load(f)
                self.log_message("📂 تم تحميل إعدادات قاعدة البيانات")
        except Exception as e:
            self.log_message(f"⚠️ فشل تحميل الإعدادات: {str(e)}")
        
        # تحديث الحقول
        self.host_entry.delete(0, tk.END)
        self.host_entry.insert(0, self.db_config.get('host', ''))
        
        self.port_entry.delete(0, tk.END)
        self.port_entry.insert(0, str(self.db_config.get('port', 3306)))
        
        self.database_entry.delete(0, tk.END)
        self.database_entry.insert(0, self.db_config.get('database', ''))
        
        self.user_entry.delete(0, tk.END)
        self.user_entry.insert(0, self.db_config.get('user', ''))
        
        self.password_entry.delete(0, tk.END)
        self.password_entry.insert(0, self.db_config.get('password', ''))
    
    def update_db_config(self):
        # التحقق من المنفذ وتعيين القيمة الافتراضية
        port_text = self.port_entry.get().strip()
        try:
            port = int(port_text) if port_text else 3306
        except ValueError:
            port = 3306
            
        self.db_config = {
            'host': self.host_entry.get().strip(),
            'port': port,
            'database': self.database_entry.get().strip(),
            'user': self.user_entry.get().strip(),
            'password': self.password_entry.get()  # السماح بكلمة مرور فارغة
        }
    
    def start_conversion(self):
        """بدء عملية التحويل مع إدارة متطورة للحالة"""
        # فحص الملفات المحددة
        if not self.selected_files:
            messagebox.showwarning("تحذير", "يرجى اختيار ملفات الكتب أولاً")
            return
        
        # فحص ما إذا كان التحويل قيد التشغيل
        if self.conversion_running:
            messagebox.showinfo("معلومات", "عملية التحويل قيد التنفيذ بالفعل")
            return
        
        # تحديث وفحص إعدادات قاعدة البيانات
        self.update_db_config()
        required_fields = ['host', 'database', 'user']
        if not all(self.db_config.get(field, '').strip() for field in required_fields):
            messagebox.showwarning("تحذير", "يرجى ملء الحقول المطلوبة: الخادم، قاعدة البيانات، اسم المستخدم")
            return
        
        # اختبار اتصال قاعدة البيانات
        if not self.test_database_connection():
            response = messagebox.askyesno(
                "تحذير", 
                "فشل الاتصال بقاعدة البيانات. هل تريد المتابعة؟"
            )
            if not response:
                return
        
        # إعداد حالة التحويل
        self.conversion_running = True
        self.cancel_conversion_flag = False
        self.start_time = datetime.now()
        
        # تحديث واجهة المستخدم
        self.start_btn.configure(text="جاري التحويل...", state="disabled")
        self.cancel_btn.configure(state="normal")
        self.progress_bar.stop()  # إيقاف الحركة اللامحدودة
        self.progress_bar.configure(mode='determinate')
        self.progress_bar['value'] = 0
        
        # تفريغ السجل وإعداد التقدم
        self.clear_log()
        self.status_var.set("🔄 بدء عملية التحويل...")
        self.progress_var.set("جاري الإعداد...")
        self.progress_details_var.set("0/0 (0%)")
        
        # بدء خيط التحويل
        conversion_thread = threading.Thread(target=self.run_conversion)
        conversion_thread.daemon = True
        conversion_thread.start()
        
        # بدء مراقبة الرسائل
        self.check_message_queue()
        
        self.log_message("🔄 بدء عملية تحويل الملفات المحددة", "PROGRESS")
    
    def run_conversion(self):
        try:
            # استيراد الكلاس من السكريپت الأصلي
            from shamela_converter import ShamelaConverter
            
            # إعداد الإحصائيات
            self.total_files = len(self.selected_files)
            self.current_file_index = 0
            self.books_stats = []
            
            self.message_queue.put(('progress', f"إعداد التحويل للـ {self.total_files} ملف..."))
            self.message_queue.put(('update_progress', (0, self.total_files, "بدء التحويل...")))
            self.message_queue.put(('info', f"📊 إعدادات قاعدة البيانات: {self.db_config['host']}:{self.db_config['port']}"))
            
            # فصل ملفات .bok عن الملفات العادية
            bok_files = [f for f in self.selected_files if f.lower().endswith('.bok')]
            regular_files = [f for f in self.selected_files if not f.lower().endswith('.bok')]
            
            # معالجة ملفات .bok بشكل خاص
            if bok_files:
                self.message_queue.put(('info', f"🔍 تم اكتشاف {len(bok_files)} ملف .bok"))
                self.message_queue.put(('info', f"🚀 بدء التحويل التلقائي المباشر..."))
                
                # تحويل ملفات .bok تلقائياً
                for bok_file in bok_files:
                    self.message_queue.put(('info', f"📝 تحويل: {os.path.basename(bok_file)}"))
                    
                    try:
                        converted_path, success = self.bok_converter.convert_bok_to_accdb(
                            bok_file, 
                            lambda msg: self.message_queue.put(('info', f"   {msg}"))
                        )
                        
                        if success and converted_path:
                            self.message_queue.put(('info', f"✅ تم تحويل: {os.path.basename(bok_file)}"))
                            regular_files.append(converted_path)
                        else:
                            self.message_queue.put(('error', f"❌ فشل تحويل: {os.path.basename(bok_file)}"))
                            
                    except Exception as e:
                        self.message_queue.put(('error', f"❌ خطأ في تحويل {os.path.basename(bok_file)}: {str(e)[:50]}"))
                
                # تحديث قائمة الملفات للمعالجة
                self.selected_files = regular_files
                self.total_files = len(self.selected_files)
            
            if not self.selected_files:
                self.message_queue.put(('error', "❌ لا توجد ملفات قابلة للمعالجة"))
                return
            
            # إنشاء دالة callback لاستقبال رسائل المحول مع تتبع التقدم
            def message_callback(message, level):
                if level == "ERROR":
                    self.message_queue.put(('error', f"❌ {message}"))
                elif level == "WARNING":
                    self.message_queue.put(('info', f"⚠️ {message}"))
                else:
                    # تحليل الرسائل لاستخراج الإحصائيات
                    self.parse_conversion_message(message)
                    self.message_queue.put(('info', f"ℹ️ {message}"))
            
            converter = ShamelaConverter(self.db_config, message_callback)
            
            # اختبار الاتصال أولاً
            self.message_queue.put(('progress', f"اختبار الاتصال بقاعدة البيانات..."))
            if not converter.connect_mysql():
                self.message_queue.put(('error', "❌ فشل في الاتصال بقاعدة البيانات"))
                return
            
            self.message_queue.put(('success', "✅ تم الاتصال بقاعدة البيانات بنجاح"))
            
            successful_conversions = 0
            
            for i, file_path in enumerate(self.selected_files, 1):
                self.current_file_index = i
                book_name = os.path.basename(file_path)
                
                # إعداد إحصائيات الكتاب الحالي
                self.current_book_stats = {
                    'name': book_name,
                    'file_path': file_path,
                    'start_time': datetime.now(),
                    'volumes': 0,
                    'chapters': 0,
                    'pages': 0,
                    'status': 'جاري المعالجة',
                    'success': False
                }
                
                # تحديث التقدم
                progress_msg = f"📚 الكتاب {i}/{self.total_files}: {book_name}"
                self.message_queue.put(('progress', progress_msg))
                self.message_queue.put(('update_progress', (i-1, self.total_files, progress_msg)))
                self.message_queue.put(('info', f"🔄 بدء معالجة: {book_name}"))
                
                try:
                    # معالجة مع دعم ملفات .bok
                    def converter_callback(actual_file_path):
                        return converter.convert_file(actual_file_path)
                    
                    def progress_callback(message):
                        self.message_queue.put(('info', f"   🔄 {message}"))
                    
                    # استخدام المعالج البسيط والقوي
                    result = process_bok_file_simple(
                        file_path=file_path,
                        converter_callback=converter_callback,
                        progress_callback=progress_callback
                    )
                    
                    if result:
                        successful_conversions += 1
                        self.current_book_stats['success'] = True
                        self.current_book_stats['status'] = 'مكتمل بنجاح'
                        self.current_book_stats['end_time'] = datetime.now()
                        
                        file_type = "[BOK]" if file_path.lower().endswith('.bok') else "[ACCDB]"
                        
                        # تحديث التقدم لإظهار الكتاب مكتمل
                        progress_msg = f"✅ اكتمل {i}/{self.total_files}: {book_name}"
                        self.message_queue.put(('update_progress', (i, self.total_files, progress_msg)))
                        self.message_queue.put(('success', f"✅ تم تحويل {book_name} {file_type} بنجاح"))
                        
                        # إضافة ملخص الكتاب
                        self.add_book_summary()
                        
                    else:
                        self.current_book_stats['success'] = False
                        self.current_book_stats['status'] = 'فشل'
                        self.current_book_stats['end_time'] = datetime.now()
                        self.message_queue.put(('error', f"❌ فشل تحويل {book_name}"))
                        
                except Exception as e:
                    self.current_book_stats['success'] = False
                    self.current_book_stats['status'] = f'خطأ: {str(e)[:30]}'
                    self.current_book_stats['end_time'] = datetime.now()
                    self.message_queue.put(('error', f"❌ خطأ في تحويل {book_name}: {str(e)}"))
                    
                    # تنظيف الملفات المؤقتة في حالة الخطأ
                    try:
                        self.bok_converter.cleanup_temp_files()
                    except:
                        pass
                
                # حفظ إحصائيات الكتاب
                self.books_stats.append(self.current_book_stats.copy())
            # التحقق من النتائج النهائية
            self.message_queue.put(('progress', f"التحقق من النتائج في قاعدة البيانات..."))
            
            try:
                # فحص عدد الكتب المضافة
                if converter.mysql_conn:
                    cursor = converter.mysql_conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM books")
                    book_count = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM pages")
                    page_count = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM chapters")
                    chapter_count = cursor.fetchone()[0]
                    
                    self.message_queue.put(('info', f"📊 النتائج النهائية:"))
                    self.message_queue.put(('info', f"   📚 عدد الكتب: {book_count}"))
                    self.message_queue.put(('info', f"   📄 عدد الصفحات: {page_count}"))
                    self.message_queue.put(('info', f"   📑 عدد الفصول: {chapter_count}"))
                    
                    if book_count == 0:
                        self.message_queue.put(('error', "⚠️ تحذير: لم يتم إضافة أي كتب إلى قاعدة البيانات!"))
                    
            except Exception as e:
                self.message_queue.put(('error', f"❌ خطأ في التحقق من النتائج: {str(e)}"))
            
            # رسالة الإنهاء مع الملخص الشامل
            self.message_queue.put(('finish', f"تم الانتهاء! نجح تحويل {successful_conversions}/{self.total_files} كتاب"))
            self.message_queue.put(('update_progress', (self.total_files, self.total_files, "اكتمل التحويل")))
            
            # إضافة ملخص شامل للجلسة
            self.add_session_summary(successful_conversions)
            
            # تنظيف الملفات المؤقتة
            try:
                cleaned_count = self.bok_converter.cleanup_temp_files(
                    lambda msg: self.message_queue.put(('info', f"🧹 {msg}"))
                )
                if cleaned_count > 0:
                    self.message_queue.put(('info', f"🧹 تم تنظيف {cleaned_count} ملف مؤقت"))
            except Exception as e:
                self.message_queue.put(('error', f"⚠️ تحذير: مشكلة في تنظيف الملفات المؤقتة: {str(e)}"))
            
        except Exception as e:
            self.message_queue.put(('error', f"خطأ عام في عملية التحويل: {str(e)}"))
        
        finally:
            # تنظيف نهائي للملفات المؤقتة
            try:
                self.bok_converter.cleanup_temp_files()
            except:
                pass
            self.message_queue.put(('done', None))
    
    def parse_conversion_message(self, message):
        """تحليل رسائل التحويل لاستخراج الإحصائيات"""
        if not self.current_book_stats:
            return
            
        try:
            # استخراج إحصائيات المجلدات
            if "تم إنشاء المجلد" in message:
                self.current_book_stats['volumes'] += 1
            elif "تم إدراج" in message and "فصل" in message:
                # استخراج عدد الفصول
                import re
                match = re.search(r'تم إدراج (\d+) فصل', message)
                if match:
                    self.current_book_stats['chapters'] = int(match.group(1))
            elif "تم إدراج" in message and "صفحة" in message and "فصل" in message:
                # استخراج عدد الصفحات والفصول معاً
                import re
                # البحث عن النمط: "تم إدراج X صفحة و Y فصل"
                match = re.search(r'تم إدراج (\d+) صفحة و (\d+) فصل', message)
                if match:
                    self.current_book_stats['pages'] = int(match.group(1))
                    self.current_book_stats['chapters'] = int(match.group(2))
            elif "إجمالي الصفحات:" in message:
                # استخراج من رسائل الإحصائيات
                import re
                match = re.search(r'إجمالي الصفحات: (\d+)', message)
                if match:
                    self.current_book_stats['pages'] = int(match.group(1))
            elif "إجمالي الفصول:" in message:
                # استخراج من رسائل الإحصائيات
                import re
                match = re.search(r'إجمالي الفصول: (\d+)', message)
                if match:
                    self.current_book_stats['chapters'] = int(match.group(1))
            elif "تم تحديث معلومات الكتاب:" in message:
                # استخراج عدد الصفحات النهائي
                import re
                match = re.search(r'تم تحديث معلومات الكتاب: (\d+) صفحة', message)
                if match:
                    self.current_book_stats['pages'] = int(match.group(1))
        except Exception as e:
            print(f"خطأ في تحليل الرسالة: {e}")
            pass
    
    def add_book_summary(self):
        """إضافة ملخص للكتاب المكتمل"""
        if not self.current_book_stats:
            return
            
        stats = self.current_book_stats
        duration = ""
        if 'end_time' in stats and 'start_time' in stats:
            duration_delta = stats['end_time'] - stats['start_time']
            duration = str(duration_delta).split('.')[0]
        
        summary_lines = [
            f"📋 ملخص الكتاب: {stats['name']}",
            f"   📁 المجلدات: {stats['volumes']}",
            f"   📑 الفصول: {stats['chapters']}",
            f"   📄 الصفحات: {stats['pages']}",
            f"   ⏱️ المدة: {duration}",
            f"   ✅ الحالة: {stats['status']}"
        ]
        
        for line in summary_lines:
            self.message_queue.put(('success', line))
    
    def add_session_summary(self, successful_conversions):
        """إضافة ملخص شامل للجلسة"""
        self.message_queue.put(('info', "\n" + "="*60))
        self.message_queue.put(('info', "📊 ملخص جلسة التحويل الشامل"))
        self.message_queue.put(('info', "="*60))
        
        # إحصائيات عامة
        total_volumes = sum(book.get('volumes', 0) for book in self.books_stats)
        total_chapters = sum(book.get('chapters', 0) for book in self.books_stats)
        total_pages = sum(book.get('pages', 0) for book in self.books_stats)
        failed_books = self.total_files - successful_conversions
        
        self.message_queue.put(('info', f"📚 إجمالي الكتب المعالجة: {self.total_files}"))
        self.message_queue.put(('success', f"✅ نجح التحويل: {successful_conversions}"))
        if failed_books > 0:
            self.message_queue.put(('error', f"❌ فشل التحويل: {failed_books}"))
        
        self.message_queue.put(('info', f"📁 إجمالي المجلدات المنشأة: {total_volumes}"))
        self.message_queue.put(('info', f"📑 إجمالي الفصول المدرجة: {total_chapters}"))
        self.message_queue.put(('info', f"📄 إجمالي الصفحات المدرجة: {total_pages}"))
        
        # وقت الجلسة الإجمالي
        if self.start_time:
            total_session_time = datetime.now() - self.start_time
            total_session_str = str(total_session_time).split('.')[0]
            self.message_queue.put(('info', f"⏱️ إجمالي وقت الجلسة: {total_session_str}"))
        
        # تفاصيل كل كتاب
        self.message_queue.put(('info', "\n📋 تفاصيل الكتب:"))
        for i, book in enumerate(self.books_stats, 1):
            status_icon = "✅" if book.get('success', False) else "❌"
            self.message_queue.put(('info', f"{i}. {status_icon} {book['name']}"))
            self.message_queue.put(('info', f"   📁 {book.get('volumes', 0)} مجلد | 📑 {book.get('chapters', 0)} فصل | 📄 {book.get('pages', 0)} صفحة"))
            self.message_queue.put(('info', f"   📊 الحالة: {book.get('status', 'غير محدد')}"))
        
        self.message_queue.put(('info', "="*60))

    def check_message_queue(self):
        """فحص ومعالجة رسائل التحويل مع دعم التقدم المحدد المتقدم"""
        try:
            messages_processed = 0
            while messages_processed < 10:  # معالجة حتى 10 رسائل في المرة الواحدة
                message_type, message = self.message_queue.get_nowait()
                messages_processed += 1
                
                if message_type == 'progress':
                    self.progress_var.set(message)
                    self.update_status(message)
                    self.log_message(message, "PROGRESS")
                elif message_type == 'update_progress':
                    # رسالة تحديث التقدم: (current, total, message)
                    current, total, msg = message
                    self.update_progress(current, total, msg)
                elif message_type == 'success':
                    self.log_message(message, "SUCCESS")
                elif message_type == 'info':
                    self.log_message(message, "INFO")
                elif message_type == 'error':
                    self.log_message(message, "ERROR")
                elif message_type == 'warning':
                    self.log_message(message, "WARNING")
                elif message_type == 'finish':
                    self.log_message("\n" + "="*50)
                    self.log_message(message, "SUCCESS")
                    self.log_message("="*50)
                    self.update_status(message)
                    # تحديث التقدم إلى 100%
                    self.progress_bar['value'] = 100
                    self.progress_details_var.set("مكتمل (100%)")
                elif message_type == 'done':
                    self.conversion_running = False
                    self.start_btn.configure(text="بدء التحويل", state="normal")
                    self.cancel_btn.configure(state="disabled")
                    self.progress_bar.stop()
                    self.progress_var.set("تم الانتهاء من التحويل")
                    
                    # حساب الوقت الإجمالي
                    if self.start_time:
                        total_time = datetime.now() - self.start_time
                        total_time_str = str(total_time).split('.')[0]
                        self.time_var.set(f"مكتمل في: {total_time_str}")
                        self.log_message(f"⏱️ إجمالي وقت التحويل: {total_time_str}", "INFO")
                    
                    return  # إنهاء المراقبة
                    
        except queue.Empty:
            pass
        
        # جدولة التحقق التالي
        if self.conversion_running:
            self.root.after(100, self.check_message_queue)
    
    def log_message(self, message, msg_type="INFO"):
        """تسجيل رسالة في السجل مع دعم الألوان والتصفية"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # تحديد نوع الرسالة بناءً على المحتوى إذا لم يحدد
        if msg_type == "INFO":
            if "✅" in message or "تم" in message and "بنجاح" in message:
                msg_type = "SUCCESS"
            elif "❌" in message or "خطأ" in message or "فشل" in message:
                msg_type = "ERROR"
            elif "⚠️" in message or "تحذير" in message:
                msg_type = "WARNING"
            elif "🔄" in message or "جاري" in message or "بدء" in message:
                msg_type = "PROGRESS"
        
        full_message = f"[{timestamp}] {message}"
        
        # حفظ الرسالة للتصفية
        msg_data = {
            'timestamp': timestamp,
            'message': message,
            'type': self.map_message_type(msg_type),
            'full_message': full_message,
            'tag': msg_type
        }
        self.all_log_messages.append(msg_data)
        
        # عرض الرسالة إذا كانت تطابق الفلتر الحالي
        current_filter = self.filter_var.get()
        if current_filter == "الكل" or msg_data['type'] == current_filter:
            self.display_log_message(msg_data)
        
        # التمرير للأسفل
        self.log_text.see(tk.END)
        self.log_text.update()
    
    def map_message_type(self, msg_type):
        """تحويل نوع الرسالة للعربية للتصفية"""
        type_map = {
            "INFO": "معلومات",
            "SUCCESS": "نجاح", 
            "ERROR": "خطأ",
            "WARNING": "تحذير",
            "PROGRESS": "معلومات"
        }
        return type_map.get(msg_type, "معلومات")
    
    def update_status(self, message):
        """تحديث شريط الحالة مع الرموز والألوان"""
        # اقتطاع الرسالة إذا كانت طويلة
        if len(message) > 80:
            message = message[:77] + "..."
        
        # إضافة رمز حسب نوع الرسالة
        if "✅" in message or "تم" in message and "بنجاح" in message:
            status_msg = f"✅ {message}"
        elif "❌" in message or "خطأ" in message or "فشل" in message:
            status_msg = f"❌ {message}"
        elif "⚠️" in message or "تحذير" in message:
            status_msg = f"⚠️ {message}"
        elif "🔄" in message or "جاري" in message or "بدء" in message:
            status_msg = f"🔄 {message}"
        else:
            status_msg = message
        
        self.status_var.set(status_msg)

    def display_log_message(self, msg_data):
        """عرض رسالة واحدة في السجل مع التنسيق"""
        # إدراج timestamp مع لون خاص
        self.log_text.insert(tk.END, f"[{msg_data['timestamp']}] ", "timestamp")
        
        # إدراج الرسالة مع اللون المناسب
        self.log_text.insert(tk.END, f"{msg_data['message']}\n", msg_data['tag'])
    
    def update_progress(self, current, total, message=""):
        """تحديث شريط التقدم والمعلومات"""
        try:
            if total > 0:
                percentage = (current / total) * 100
                self.progress_bar['value'] = percentage
                
                # تحديث النص التفصيلي
                self.progress_details_var.set(f"{current}/{total} ({percentage:.1f}%)")
            
            if message:
                self.progress_var.set(message)
            
            # حساب الوقت المنقضي والمتبقي
            if self.start_time:
                elapsed = datetime.now() - self.start_time
                elapsed_str = str(elapsed).split('.')[0]  # إزالة الميكروثانية
                
                if total > 0 and current > 0:
                    # تقدير الوقت المتبقي
                    rate = current / elapsed.total_seconds()
                    remaining_items = total - current
                    if rate > 0:
                        remaining_seconds = remaining_items / rate
                        remaining_time = str(timedelta(seconds=int(remaining_seconds)))
                        self.time_var.set(f"منقضي: {elapsed_str} | متبقي: {remaining_time}")
                    else:
                        self.time_var.set(f"منقضي: {elapsed_str}")
                else:
                    self.time_var.set(f"منقضي: {elapsed_str}")
            
            self.root.update_idletasks()
            
        except Exception as e:
            print(f"خطأ في تحديث التقدم: {e}")
    
    def update_status(self, message):
        """تحديث شريط الحالة مع الرموز والألوان"""
        # اقتطاع الرسالة إذا كانت طويلة
        if len(message) > 80:
            message = message[:77] + "..."
        
        # إضافة رمز حسب نوع الرسالة
        if "✅" in message or "تم" in message and "بنجاح" in message:
            status_msg = f"✅ {message}"
        elif "❌" in message or "خطأ" in message or "فشل" in message:
            status_msg = f"❌ {message}"
        elif "⚠️" in message or "تحذير" in message:
            status_msg = f"⚠️ {message}"
        elif "🔄" in message or "جاري" in message or "بدء" in message:
            status_msg = f"🔄 {message}"
        else:
            status_msg = message
        
        self.status_var.set(status_msg)
        self.root.update_idletasks()
    
    def test_database_connection(self):
        """اختبار الاتصال بقاعدة البيانات"""
        try:
            import mysql.connector
            
            # تحديث الإعدادات أولاً
            self.update_db_config()
            
            # محاولة الاتصال
            connection = mysql.connector.connect(
                host=self.db_config.get('host', 'localhost'),
                port=int(self.db_config.get('port', 3306)),
                user=self.db_config.get('user', ''),
                password=self.db_config.get('password', ''),
                database=self.db_config.get('database', ''),
                charset='utf8mb4'
            )
            
            if connection.is_connected():
                connection.close()
                return True
            
        except Exception as e:
            print(f"خطأ في اختبار الاتصال: {e}")
            return False
        
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
