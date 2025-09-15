#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أداة تحويل ملفات .bok بواجهة رسومية
تحاكي عملية Access بشكل مبسط
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import shutil
import threading
from pathlib import Path

class BokConverterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("محول ملفات .bok إلى .accdb")
        self.root.geometry("600x500")
        self.root.configure(bg='#f0f0f0')
        
        self.bok_files = []
        self.output_folder = tk.StringVar()
        self.conversion_running = False
        
        self.create_widgets()
    
    def create_widgets(self):
        # العنوان
        title_label = tk.Label(self.root, text="محول ملفات .bok إلى .accdb", 
                              font=("Arial", 16, "bold"), 
                              bg='#f0f0f0', fg='#2c3e50')
        title_label.pack(pady=10)
        
        # شرح
        info_label = tk.Label(self.root, 
                             text="هذه الأداة تحول ملفات .bok إلى .accdb حتى يمكن استخدامها في التطبيق الرئيسي",
                             font=("Arial", 10), bg='#f0f0f0', fg='#7f8c8d')
        info_label.pack(pady=5)
        
        # إطار اختيار الملفات
        files_frame = tk.LabelFrame(self.root, text="اختيار ملفات .bok", 
                                   font=("Arial", 12, "bold"), 
                                   bg='#f0f0f0', fg='#2c3e50')
        files_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        # أزرار اختيار الملفات
        buttons_frame = tk.Frame(files_frame, bg='#f0f0f0')
        buttons_frame.pack(pady=10)
        
        select_files_btn = tk.Button(buttons_frame, text="اختيار ملفات .bok", 
                                    command=self.select_bok_files,
                                    font=("Arial", 10, "bold"), 
                                    bg='#3498db', fg='white', 
                                    padx=20, pady=5)
        select_files_btn.pack(side="left", padx=5)
        
        select_folder_btn = tk.Button(buttons_frame, text="اختيار مجلد", 
                                     command=self.select_bok_folder,
                                     font=("Arial", 10, "bold"), 
                                     bg='#9b59b6', fg='white', 
                                     padx=20, pady=5)
        select_folder_btn.pack(side="left", padx=5)
        
        clear_btn = tk.Button(buttons_frame, text="مسح القائمة", 
                             command=self.clear_files,
                             font=("Arial", 10, "bold"), 
                             bg='#e74c3c', fg='white', 
                             padx=20, pady=5)
        clear_btn.pack(side="left", padx=5)
        
        # قائمة الملفات
        self.files_listbox = tk.Listbox(files_frame, height=8, 
                                       font=("Arial", 9))
        self.files_listbox.pack(pady=10, padx=10, fill="both", expand=True)
        
        # إطار مجلد الحفظ
        output_frame = tk.LabelFrame(self.root, text="مجلد الحفظ", 
                                    font=("Arial", 12, "bold"), 
                                    bg='#f0f0f0', fg='#2c3e50')
        output_frame.pack(pady=10, padx=20, fill="x")
        
        output_buttons_frame = tk.Frame(output_frame, bg='#f0f0f0')
        output_buttons_frame.pack(pady=10)
        
        tk.Button(output_buttons_frame, text="اختيار مجلد الحفظ", 
                 command=self.select_output_folder,
                 font=("Arial", 10, "bold"), 
                 bg='#27ae60', fg='white', 
                 padx=20, pady=5).pack(side="left", padx=5)
        
        self.output_label = tk.Label(output_frame, textvariable=self.output_folder,
                                    font=("Arial", 9), bg='#f0f0f0', fg='#2c3e50')
        self.output_label.pack(pady=5)
        
        # زر التحويل
        self.convert_btn = tk.Button(self.root, text="🔄 بدء التحويل", 
                                    command=self.start_conversion,
                                    font=("Arial", 12, "bold"), 
                                    bg='#f39c12', fg='white', 
                                    padx=30, pady=10)
        self.convert_btn.pack(pady=20)
        
        # شريط التقدم
        self.progress = ttk.Progressbar(self.root, mode='determinate')
        self.progress.pack(pady=10, padx=20, fill="x")
        
        # منطقة الحالة
        self.status_text = tk.Text(self.root, height=6, font=("Arial", 9))
        self.status_text.pack(pady=10, padx=20, fill="x")
        
        # تعيين مجلد افتراضي
        default_output = os.path.join(os.path.dirname(__file__), "converted_books")
        self.output_folder.set(default_output)
    
    def select_bok_files(self):
        """اختيار ملفات .bok منفردة"""
        files = filedialog.askopenfilenames(
            title="اختيار ملفات .bok",
            filetypes=[("ملفات BOK", "*.bok"), ("كل الملفات", "*.*")]
        )
        
        for file in files:
            if file not in self.bok_files:
                self.bok_files.append(file)
                self.files_listbox.insert(tk.END, os.path.basename(file))
        
        self.log_status(f"تم إضافة {len(files)} ملف جديد")
    
    def select_bok_folder(self):
        """اختيار مجلد يحتوي على ملفات .bok"""
        folder = filedialog.askdirectory(title="اختيار مجلد ملفات .bok")
        
        if folder:
            bok_files_in_folder = list(Path(folder).glob("*.bok"))
            added_count = 0
            
            for bok_file in bok_files_in_folder:
                file_str = str(bok_file)
                if file_str not in self.bok_files:
                    self.bok_files.append(file_str)
                    self.files_listbox.insert(tk.END, bok_file.name)
                    added_count += 1
            
            self.log_status(f"تم إضافة {added_count} ملف من المجلد: {os.path.basename(folder)}")
    
    def clear_files(self):
        """مسح قائمة الملفات"""
        self.bok_files.clear()
        self.files_listbox.delete(0, tk.END)
        self.log_status("تم مسح قائمة الملفات")
    
    def select_output_folder(self):
        """اختيار مجلد الحفظ"""
        folder = filedialog.askdirectory(title="اختيار مجلد الحفظ")
        if folder:
            self.output_folder.set(folder)
            self.log_status(f"تم تحديد مجلد الحفظ: {os.path.basename(folder)}")
    
    def log_status(self, message):
        """إضافة رسالة للحالة"""
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.see(tk.END)
        self.root.update()
    
    def start_conversion(self):
        """بدء عملية التحويل"""
        if not self.bok_files:
            messagebox.showwarning("تحذير", "يرجى اختيار ملفات .bok أولاً")
            return
        
        if not self.output_folder.get():
            messagebox.showwarning("تحذير", "يرجى تحديد مجلد الحفظ")
            return
        
        if self.conversion_running:
            messagebox.showinfo("معلومات", "التحويل جاري بالفعل...")
            return
        
        # تشغيل التحويل في thread منفصل
        thread = threading.Thread(target=self.run_conversion)
        thread.daemon = True
        thread.start()
    
    def run_conversion(self):
        """تشغيل عملية التحويل"""
        self.conversion_running = True
        self.convert_btn.configure(state='disabled', text="جاري التحويل...")
        
        try:
            # إنشاء مجلد الحفظ
            output_dir = self.output_folder.get()
            os.makedirs(output_dir, exist_ok=True)
            
            total_files = len(self.bok_files)
            successful_conversions = 0
            
            self.progress['maximum'] = total_files
            self.log_status(f"🔄 بدء تحويل {total_files} ملف...")
            
            for i, bok_file in enumerate(self.bok_files):
                self.log_status(f"معالجة [{i+1}/{total_files}]: {os.path.basename(bok_file)}")
                
                try:
                    # تحديد اسم الملف الجديد
                    base_name = os.path.splitext(os.path.basename(bok_file))[0]
                    accdb_path = os.path.join(output_dir, f"{base_name}.accdb")
                    
                    # نسخ الملف مع تغيير الامتداد
                    shutil.copy2(bok_file, accdb_path)
                    
                    self.log_status(f"✅ تم: {os.path.basename(accdb_path)}")
                    successful_conversions += 1
                    
                except Exception as e:
                    self.log_status(f"❌ فشل: {os.path.basename(bok_file)} - {str(e)}")
                
                # تحديث شريط التقدم
                self.progress['value'] = i + 1
                self.root.update()
            
            # النتائج النهائية
            self.log_status(f"\n🎉 انتهى التحويل!")
            self.log_status(f"✅ نجح: {successful_conversions}/{total_files}")
            self.log_status(f"📁 المجلد: {output_dir}")
            
            if successful_conversions > 0:
                messagebox.showinfo("تم!", 
                                   f"تم تحويل {successful_conversions} ملف بنجاح!\n"
                                   f"الملفات محفوظة في:\n{output_dir}")
            
        except Exception as e:
            self.log_status(f"❌ خطأ عام: {str(e)}")
            messagebox.showerror("خطأ", f"حدث خطأ أثناء التحويل:\n{str(e)}")
        
        finally:
            self.conversion_running = False
            self.convert_btn.configure(state='normal', text="🔄 بدء التحويل")
            self.progress['value'] = 0

def main():
    root = tk.Tk()
    app = BokConverterGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
