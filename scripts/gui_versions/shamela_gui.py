import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
import json
import os
from datetime import datetime
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
        
        # متغير حالة التحويل
        self.conversion_running = False
        
        self.create_widgets()
        self.load_settings()
        self.check_message_queue()
    
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
        
        # قائمة الملفات المحددة
        self.files_listbox = tk.Listbox(files_frame, height=4, 
                                       font=("Arial", 9),
                                       bg='white', fg='#2c3e50')
        self.files_listbox.pack(fill="x", padx=10, pady=(0, 10))
        
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
        
        # إطار التحكم
        control_frame = tk.Frame(self.root, bg='#f0f0f0')
        control_frame.pack(fill="x", padx=20, pady=10)
        
        # شريط التقدم
        self.progress_var = tk.StringVar()
        self.progress_var.set("جاهز للبدء")
        progress_label = tk.Label(control_frame, textvariable=self.progress_var,
                                 font=("Arial", 10), bg='#f0f0f0', fg='#7f8c8d')
        progress_label.pack()
        
        self.progress_bar = ttk.Progressbar(control_frame, mode='indeterminate')
        self.progress_bar.pack(fill="x", pady=5)
        
        # زر البدء
        self.start_btn = tk.Button(control_frame, text="بدء التحويل", 
                                  command=self.start_conversion,
                                  font=("Arial", 12, "bold"),
                                  bg='#2ecc71', fg='white',
                                  relief='flat', padx=30, pady=10)
        self.start_btn.pack(pady=10)
        
        # منطقة سجل الأحداث
        log_frame = tk.LabelFrame(self.root, text="سجل الأحداث", 
                                 font=("Arial", 12, "bold"),
                                 bg='#f0f0f0', fg='#34495e')
        log_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, 
                                                 font=("Consolas", 9),
                                                 bg='#2c3e50', fg='#ecf0f1',
                                                 insertbackground='#ecf0f1')
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # شريط الحالة
        status_frame = tk.Frame(self.root, bg='#34495e', height=30)
        status_frame.pack(fill="x", side="bottom")
        
        self.status_var = tk.StringVar()
        self.status_var.set("جاهز")
        status_label = tk.Label(status_frame, textvariable=self.status_var,
                               font=("Arial", 9), bg='#34495e', fg='white')
        status_label.pack(side="left", padx=10, pady=5)
    
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
        if not self.selected_files:
            messagebox.showwarning("تحذير", "يرجى اختيار ملفات الكتب أولاً")
            return
        
        if self.conversion_running:
            messagebox.showinfo("معلومات", "عملية التحويل قيد التنفيذ بالفعل")
            return
        
        self.update_db_config()
        
        # التحقق من إعدادات قاعدة البيانات
        required_fields = ['host', 'database', 'user']
        if not all(self.db_config.get(field, '').strip() for field in required_fields):
            messagebox.showwarning("تحذير", "يرجى ملء الحقول المطلوبة: الخادم، قاعدة البيانات، اسم المستخدم")
            return
        
        # بدء التحويل في thread منفصل
        self.conversion_running = True
        self.start_btn.configure(text="جاري التحويل...", state="disabled")
        self.progress_bar.start()
        
        conversion_thread = threading.Thread(target=self.run_conversion)
        conversion_thread.daemon = True
        conversion_thread.start()
    
    def run_conversion(self):
        try:
            # استيراد الكلاس من السكريپت الأصلي
            from shamela_converter import ShamelaConverter
            
            self.message_queue.put(('progress', f"بدء عملية التحويل..."))
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
            
            if not self.selected_files:
                self.message_queue.put(('error', "❌ لا توجد ملفات قابلة للمعالجة"))
                return
            
            # إنشاء دالة callback لاستقبال رسائل المحول
            def message_callback(message, level):
                if level == "ERROR":
                    self.message_queue.put(('error', f"❌ {message}"))
                elif level == "WARNING":
                    self.message_queue.put(('info', f"⚠️ {message}"))
                else:
                    self.message_queue.put(('info', f"ℹ️ {message}"))
            
            converter = ShamelaConverter(self.db_config, message_callback)
            
            # اختبار الاتصال أولاً
            self.message_queue.put(('progress', f"اختبار الاتصال بقاعدة البيانات..."))
            if not converter.connect_mysql():
                self.message_queue.put(('error', "❌ فشل في الاتصال بقاعدة البيانات"))
                return
            
            self.message_queue.put(('success', "✅ تم الاتصال بقاعدة البيانات بنجاح"))
            
            total_files = len(self.selected_files)
            successful_conversions = 0
            
            for i, file_path in enumerate(self.selected_files, 1):
                self.message_queue.put(('progress', f"معالجة الملف {i}/{total_files}: {os.path.basename(file_path)}"))
                
                try:
                    # معالجة مع دعم ملفات .bok
                    def converter_callback(actual_file_path):
                        return converter.convert_file(actual_file_path)
                    
                    def progress_callback(message):
                        self.message_queue.put(('info', f"🔄 {message}"))
                    
                    # استخدام المعالج البسيط والقوي
                    result = process_bok_file_simple(
                        file_path=file_path,
                        converter_callback=converter_callback,
                        progress_callback=progress_callback
                    )
                    
                    if result:
                        successful_conversions += 1
                        file_type = "[BOK]" if file_path.lower().endswith('.bok') else "[ACCDB]"
                        self.message_queue.put(('success', f"✅ تم تحويل {os.path.basename(file_path)} {file_type} بنجاح"))
                    else:
                        self.message_queue.put(('error', f"❌ فشل تحويل {os.path.basename(file_path)}"))
                        
                except Exception as e:
                    self.message_queue.put(('error', f"❌ خطأ في تحويل {os.path.basename(file_path)}: {str(e)}"))
                    
                    # تنظيف الملفات المؤقتة في حالة الخطأ
                    try:
                        self.bok_converter.cleanup_temp_files()
                    except:
                        pass
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
            
            # رسالة الإنهاء
            self.message_queue.put(('finish', f"تم الانتهاء! نجح تحويل {successful_conversions}/{total_files} ملف"))
            
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
    
    def check_message_queue(self):
        try:
            while True:
                message_type, message = self.message_queue.get_nowait()
                
                if message_type == 'progress':
                    self.progress_var.set(message)
                    self.update_status(message)
                elif message_type == 'success':
                    self.log_message(message)
                elif message_type == 'info':
                    self.log_message(message)
                elif message_type == 'error':
                    self.log_message(message)
                elif message_type == 'finish':
                    self.log_message("\n" + "="*50)
                    self.log_message(message)
                    self.log_message("="*50)
                    self.update_status(message)
                elif message_type == 'done':
                    self.conversion_running = False
                    self.start_btn.configure(text="بدء التحويل", state="normal")
                    self.progress_bar.stop()
                    self.progress_var.set("تم الانتهاء من التحويل")
                    break
                    
        except queue.Empty:
            pass
        
        # جدولة التحقق التالي
        self.root.after(100, self.check_message_queue)
    
    def log_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, formatted_message)
        self.log_text.see(tk.END)
        self.log_text.update()
    
    def update_status(self, status):
        self.status_var.set(status)
        self.root.update_idletasks()

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
