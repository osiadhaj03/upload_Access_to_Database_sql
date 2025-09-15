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

class ModernShamelaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("📚 Shamela Books Converter Pro")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # متغيرات الألوان والثيم
        self.setup_theme()
        
        # قائمة الملفات المحددة
        self.selected_files = []
        
        # معالج ملفات .bok
        self.bok_converter = SimpleBokConverter()
        
        # إعدادات قاعدة البيانات الافتراضية
        self.db_config = {
            'host': 'srv1800.hstgr.io',
            'port': 3306,
            'database': 'u994369532_test',
            'user': 'u994369532_test',
            'password': 'Test20205'
        }
        
        # قائمة انتظار الرسائل
        self.message_queue = queue.Queue()
        
        # متغيرات حالة التحويل
        self.conversion_running = False
        self.cancel_conversion_flag = False
        self.cancel_requested = False
        
        # متغيرات الوقت والتقدم
        self.start_time = None
        self.all_log_messages = []
        
        # إحصائيات التحويل
        self.total_files = 0
        self.current_file_index = 0
        self.books_stats = []
        self.current_book_stats = None
        
        # إنشاء الواجهة
        self.create_modern_ui()
        self.load_settings()
        
    def setup_theme(self):
        """إعداد الثيم والألوان"""
        # الوضع الداكن - ألوان عصرية
        self.colors = {
            'bg_primary': '#0f1419',      # خلفية رئيسية داكنة
            'bg_secondary': '#1a1f29',    # خلفية ثانوية
            'bg_card': '#242933',         # خلفية البطاقات
            'bg_hover': '#2d3340',        # خلفية عند التمرير
            'accent': '#00d4ff',          # اللون الرئيسي (أزرق سماوي)
            'accent_hover': '#00a8cc',    # اللون الرئيسي عند التمرير
            'success': '#00ff88',         # أخضر نيون
            'error': '#ff3366',           # أحمر وردي
            'warning': '#ffaa00',         # برتقالي ذهبي
            'text_primary': '#ffffff',    # نص أبيض
            'text_secondary': '#9ca3af',  # نص رمادي
            'text_muted': '#6b7280',      # نص باهت
            'border': '#374151',          # حدود
            'gradient_start': '#667eea',  # بداية التدرج
            'gradient_end': '#764ba2'     # نهاية التدرج
        }
        
        # إعداد نافذة رئيسية
        self.root.configure(bg=self.colors['bg_primary'])
        
        # إعداد الخط الأساسي
        self.fonts = {
            'title': ('Segoe UI', 24, 'bold'),
            'heading': ('Segoe UI', 14, 'bold'),
            'subheading': ('Segoe UI', 12, 'bold'),
            'body': ('Segoe UI', 11),
            'small': ('Segoe UI', 10),
            'mono': ('Cascadia Code', 10)
        }
        
    def create_modern_ui(self):
        """إنشاء واجهة عصرية متطورة"""
        
        # الحاوية الرئيسية
        main_container = tk.Frame(self.root, bg=self.colors['bg_primary'])
        main_container.pack(fill="both", expand=True)
        
        # شريط العنوان المخصص
        self.create_custom_titlebar(main_container)
        
        # المحتوى الرئيسي مع شريط جانبي
        content_frame = tk.Frame(main_container, bg=self.colors['bg_primary'])
        content_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # الشريط الجانبي
        self.create_sidebar(content_frame)
        
        # منطقة المحتوى الرئيسية
        main_content = tk.Frame(content_frame, bg=self.colors['bg_primary'])
        main_content.pack(side="right", fill="both", expand=True, padx=(20, 0))
        
        # حاوية التمرير
        canvas = tk.Canvas(main_content, bg=self.colors['bg_primary'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_content, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['bg_primary'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # بطاقات المحتوى
        self.create_file_selection_card(scrollable_frame)
        self.create_database_card(scrollable_frame)
        self.create_progress_card(scrollable_frame)
        self.create_log_card(scrollable_frame)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # شريط الحالة السفلي
        self.create_status_bar(main_container)
        
    def create_custom_titlebar(self, parent):
        """إنشاء شريط عنوان مخصص"""
        titlebar = tk.Frame(parent, bg=self.colors['bg_secondary'], height=60)
        titlebar.pack(fill="x", padx=0, pady=0)
        titlebar.pack_propagate(False)
        
        # حاوية المحتوى
        title_content = tk.Frame(titlebar, bg=self.colors['bg_secondary'])
        title_content.pack(fill="both", expand=True, padx=30, pady=10)
        
        # الأيقونة والعنوان
        title_left = tk.Frame(title_content, bg=self.colors['bg_secondary'])
        title_left.pack(side="left", fill="y")
        
        # العنوان الرئيسي مع تأثير التدرج
        title_label = tk.Label(title_left, text="📚 محول كتب الشاملة", 
                              font=self.fonts['title'],
                              bg=self.colors['bg_secondary'], 
                              fg=self.colors['accent'])
        title_label.pack(side="left")
        
        # العنوان الفرعي
        subtitle = tk.Label(title_left, text="  |  النسخة الاحترافية 2.0", 
                           font=self.fonts['small'],
                           bg=self.colors['bg_secondary'], 
                           fg=self.colors['text_secondary'])
        subtitle.pack(side="left", padx=(10, 0))
        
        # أزرار التحكم بالنافذة (يمين)
        controls_frame = tk.Frame(title_content, bg=self.colors['bg_secondary'])
        controls_frame.pack(side="right")
        
        # زر تبديل الثيم
        theme_btn = self.create_modern_button(controls_frame, "🌙", 
                                             command=self.toggle_theme,
                                             width=3, height=1,
                                             bg=self.colors['bg_card'])
        theme_btn.pack(side="left", padx=5)
        
        # زر تصغير
        min_btn = self.create_modern_button(controls_frame, "─", 
                                           command=self.minimize_window,
                                           width=3, height=1,
                                           bg=self.colors['bg_card'])
        min_btn.pack(side="left", padx=2)
        
        # زر تكبير
        max_btn = self.create_modern_button(controls_frame, "□", 
                                           command=self.toggle_maximize,
                                           width=3, height=1,
                                           bg=self.colors['bg_card'])
        max_btn.pack(side="left", padx=2)
        
        # زر إغلاق
        close_btn = self.create_modern_button(controls_frame, "✕", 
                                             command=self.root.quit,
                                             width=3, height=1,
                                             bg=self.colors['error'])
        close_btn.pack(side="left", padx=(2, 0))
        
    def create_sidebar(self, parent):
        """إنشاء شريط جانبي للتنقل السريع"""
        sidebar = tk.Frame(parent, bg=self.colors['bg_secondary'], width=80)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        
        # قائمة الأيقونات
        icons = [
            ("📁", "الملفات", self.scroll_to_files),
            ("🗄️", "قاعدة البيانات", self.scroll_to_database),
            ("📊", "التقدم", self.scroll_to_progress),
            ("📋", "السجل", self.scroll_to_log),
            ("📈", "الإحصائيات", self.show_statistics),
            ("⚙️", "الإعدادات", self.show_settings),
            ("❓", "المساعدة", self.show_help)
        ]
        
        for icon, tooltip, command in icons:
            btn_frame = tk.Frame(sidebar, bg=self.colors['bg_secondary'], height=70)
            btn_frame.pack(fill="x", pady=5)
            btn_frame.pack_propagate(False)
            
            btn = tk.Label(btn_frame, text=icon, font=('Segoe UI', 20),
                          bg=self.colors['bg_secondary'], fg=self.colors['text_secondary'],
                          cursor="hand2")
            btn.pack(expand=True)
            
            # تأثيرات التمرير
            def on_enter(e, label=btn):
                label.configure(fg=self.colors['accent'])
                
            def on_leave(e, label=btn):
                label.configure(fg=self.colors['text_secondary'])
                
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)
            btn.bind("<Button-1>", lambda e, cmd=command: cmd())
            
            # Tooltip
            self.create_tooltip(btn, tooltip)
            
    def create_file_selection_card(self, parent):
        """بطاقة اختيار الملفات"""
        card = self.create_card(parent, "📁 اختيار ملفات الكتب")
        
        # منطقة السحب والإفلات
        drop_zone = tk.Frame(card, bg=self.colors['bg_hover'], height=120)
        drop_zone.pack(fill="x", pady=10)
        drop_zone.pack_propagate(False)
        
        # تصميم منطقة السحب
        drop_content = tk.Frame(drop_zone, bg=self.colors['bg_hover'])
        drop_content.place(relx=0.5, rely=0.5, anchor="center")
        
        drop_icon = tk.Label(drop_content, text="📥", font=('Segoe UI', 32),
                            bg=self.colors['bg_hover'], fg=self.colors['accent'])
        drop_icon.pack()
        
        drop_text = tk.Label(drop_content, text="اسحب الملفات هنا أو انقر للاختيار",
                            font=self.fonts['body'],
                            bg=self.colors['bg_hover'], fg=self.colors['text_secondary'])
        drop_text.pack()
        
        drop_hint = tk.Label(drop_content, text="يدعم: .accdb, .bok",
                           font=self.fonts['small'],
                           bg=self.colors['bg_hover'], fg=self.colors['text_muted'])
        drop_hint.pack()
        
        # جعل المنطقة قابلة للنقر
        for widget in [drop_zone, drop_icon, drop_text, drop_hint]:
            widget.bind("<Button-1>", lambda e: self.select_files())
            widget.configure(cursor="hand2")
        
        # أزرار التحكم
        btn_frame = tk.Frame(card, bg=self.colors['bg_card'])
        btn_frame.pack(fill="x", pady=10)
        
        select_btn = self.create_gradient_button(btn_frame, "➕ إضافة ملفات", 
                                                self.select_files, width=15)
        select_btn.pack(side="left", padx=5)
        
        clear_btn = self.create_modern_button(btn_frame, "🗑️ مسح الكل", 
                                             self.clear_files, width=12,
                                             bg=self.colors['bg_hover'])
        clear_btn.pack(side="left", padx=5)
        
        # قائمة الملفات المحددة
        files_frame = tk.Frame(card, bg=self.colors['bg_card'])
        files_frame.pack(fill="both", expand=True, pady=10)
        
        # إطار القائمة مع Scrollbar
        list_container = tk.Frame(files_frame, bg=self.colors['bg_hover'])
        list_container.pack(fill="both", expand=True)
        
        self.files_listbox = tk.Listbox(list_container, height=5,
                                       font=self.fonts['body'],
                                       bg=self.colors['bg_hover'],
                                       fg=self.colors['text_primary'],
                                       selectbackground=self.colors['accent'],
                                       selectforeground=self.colors['bg_primary'],
                                       borderwidth=0,
                                       highlightthickness=0)
        self.files_listbox.pack(side="left", fill="both", expand=True)
        
        files_scrollbar = ttk.Scrollbar(list_container, orient="vertical",
                                       command=self.files_listbox.yview)
        files_scrollbar.pack(side="right", fill="y")
        self.files_listbox.configure(yscrollcommand=files_scrollbar.set)
        
        # أزرار إدارة الملفات
        manage_frame = tk.Frame(card, bg=self.colors['bg_card'])
        manage_frame.pack(fill="x", pady=5)
        
        delete_btn = self.create_small_button(manage_frame, "❌ حذف", 
                                             self.delete_selected_file)
        delete_btn.pack(side="left", padx=5)
        
        preview_btn = self.create_small_button(manage_frame, "👁️ معاينة", 
                                              self.preview_selected_file)
        preview_btn.pack(side="left", padx=5)
        
        self.files_card = card
        
    def create_database_card(self, parent):
        """بطاقة إعدادات قاعدة البيانات"""
        card = self.create_card(parent, "🗄️ إعدادات قاعدة البيانات")
        
        # شبكة الإدخالات
        grid_frame = tk.Frame(card, bg=self.colors['bg_card'])
        grid_frame.pack(fill="x", pady=10)
        
        # الصف الأول
        row1 = tk.Frame(grid_frame, bg=self.colors['bg_card'])
        row1.pack(fill="x", pady=5)
        
        self.create_input_group(row1, "الخادم:", "host_entry", 
                               default="srv1800.hstgr.io", width=30).pack(side="left", padx=10)
        self.create_input_group(row1, "المنفذ:", "port_entry", 
                               default="3306", width=10).pack(side="left", padx=10)
        
        # الصف الثاني
        row2 = tk.Frame(grid_frame, bg=self.colors['bg_card'])
        row2.pack(fill="x", pady=5)
        
        self.create_input_group(row2, "قاعدة البيانات:", "database_entry",
                               default="u994369532_test", width=30).pack(side="left", padx=10)
        
        # الصف الثالث
        row3 = tk.Frame(grid_frame, bg=self.colors['bg_card'])
        row3.pack(fill="x", pady=5)
        
        self.create_input_group(row3, "المستخدم:", "user_entry",
                               default="u994369532_shamela", width=30).pack(side="left", padx=10)
        self.create_input_group(row3, "كلمة المرور:", "password_entry",
                               default="", width=30, show="*").pack(side="left", padx=10)
        
        # أزرار الإجراءات
        actions_frame = tk.Frame(card, bg=self.colors['bg_card'])
        actions_frame.pack(fill="x", pady=10)
        
        test_btn = self.create_gradient_button(actions_frame, "🔍 اختبار الاتصال",
                                              self.test_connection, width=15)
        test_btn.pack(side="left", padx=5)
        
        save_btn = self.create_modern_button(actions_frame, "💾 حفظ الإعدادات",
                                            self.save_settings, width=15,
                                            bg=self.colors['success'])
        save_btn.pack(side="left", padx=5)
        
        self.db_card = card
        
    def create_progress_card(self, parent):
        """بطاقة التقدم والتحكم"""
        card = self.create_card(parent, "📊 التحكم والتقدم")
        
        # معلومات التقدم
        info_frame = tk.Frame(card, bg=self.colors['bg_card'])
        info_frame.pack(fill="x", pady=10)
        
        # الحالة الحالية
        self.progress_var = tk.StringVar(value="🟢 جاهز للبدء")
        progress_label = tk.Label(info_frame, textvariable=self.progress_var,
                                font=self.fonts['subheading'],
                                bg=self.colors['bg_card'],
                                fg=self.colors['accent'])
        progress_label.pack(side="left")
        
        # التفاصيل
        self.progress_details_var = tk.StringVar()
        details_label = tk.Label(info_frame, textvariable=self.progress_details_var,
                                font=self.fonts['small'],
                                bg=self.colors['bg_card'],
                                fg=self.colors['text_secondary'])
        details_label.pack(side="right")
        
        # شريط التقدم المتحرك
        progress_container = tk.Frame(card, bg=self.colors['bg_card'])
        progress_container.pack(fill="x", pady=10)
        
        # خلفية شريط التقدم
        progress_bg = tk.Frame(progress_container, bg=self.colors['bg_hover'], height=30)
        progress_bg.pack(fill="x")
        progress_bg.pack_propagate(False)
        
        # شريط التقدم نفسه
        self.progress_bar = tk.Frame(progress_bg, bg=self.colors['accent'], height=30)
        self.progress_bar.place(x=0, y=0, relheight=1, width=0)
        
        # نص التقدم
        self.progress_text = tk.Label(progress_bg, text="0%",
                                     font=self.fonts['small'],
                                     bg=self.colors['bg_hover'],
                                     fg=self.colors['text_primary'])
        self.progress_text.place(relx=0.5, rely=0.5, anchor="center")
        
        # أزرار التحكم الرئيسية
        controls_frame = tk.Frame(card, bg=self.colors['bg_card'])
        controls_frame.pack(pady=15)
        
        self.start_btn = self.create_large_gradient_button(
            controls_frame, "🚀 بدء التحويل", self.start_conversion)
        self.start_btn.pack(side="left", padx=10)
        
        self.cancel_btn = self.create_modern_button(
            controls_frame, "⏹️ إيقاف", self.cancel_conversion,
            width=15, height=2, bg=self.colors['error'])
        self.cancel_btn.pack(side="left", padx=10)
        self.cancel_btn.configure(state="disabled")
        
        # أزرار إضافية
        extra_frame = tk.Frame(card, bg=self.colors['bg_card'])
        extra_frame.pack(fill="x", pady=5)
        
        save_log_btn = self.create_small_button(extra_frame, "📝 حفظ السجل", 
                                               self.save_log)
        save_log_btn.pack(side="left", padx=5)
        
        report_btn = self.create_small_button(extra_frame, "📊 تقرير الجلسة", 
                                             self.show_session_report)
        report_btn.pack(side="left", padx=5)
        
        stats_btn = self.create_small_button(extra_frame, "📈 الإحصائيات", 
                                            self.show_statistics)
        stats_btn.pack(side="left", padx=5)
        
        # معلومات الوقت
        time_frame = tk.Frame(card, bg=self.colors['bg_card'])
        time_frame.pack(fill="x", pady=10)
        
        self.time_var = tk.StringVar()
        time_label = tk.Label(time_frame, textvariable=self.time_var,
                             font=self.fonts['small'],
                             bg=self.colors['bg_card'],
                             fg=self.colors['text_muted'])
        time_label.pack()
        
        self.progress_card = card
        
    def create_log_card(self, parent):
        """بطاقة سجل الأحداث"""
        card = self.create_card(parent, "📋 سجل الأحداث", height=300)
        
        # أدوات السجل
        tools_frame = tk.Frame(card, bg=self.colors['bg_card'])
        tools_frame.pack(fill="x", pady=5)
        
        # فلتر الرسائل
        filter_label = tk.Label(tools_frame, text="🔍 تصفية:",
                              font=self.fonts['small'],
                              bg=self.colors['bg_card'],
                              fg=self.colors['text_secondary'])
        filter_label.pack(side="left", padx=5)
        
        self.filter_var = tk.StringVar(value="الكل")
        filter_options = ["الكل", "معلومات", "نجاح", "خطأ", "تحذير"]
        
        filter_menu = tk.OptionMenu(tools_frame, self.filter_var, *filter_options,
                                   command=self.filter_log_messages)
        filter_menu.configure(font=self.fonts['small'],
                             bg=self.colors['bg_hover'],
                             fg=self.colors['text_primary'],
                             activebackground=self.colors['accent'],
                             activeforeground=self.colors['bg_primary'],
                             borderwidth=0,
                             highlightthickness=0)
        filter_menu.pack(side="left", padx=5)
        
        # زر مسح السجل
        clear_log_btn = self.create_small_button(tools_frame, "🗑️ مسح", 
                                                self.clear_log)
        clear_log_btn.pack(side="right", padx=5)
        
        # منطقة السجل
        log_container = tk.Frame(card, bg=self.colors['bg_hover'])
        log_container.pack(fill="both", expand=True, pady=5)
        
        self.log_text = tk.Text(log_container, height=12,
                               font=self.fonts['mono'],
                               bg=self.colors['bg_primary'],
                               fg=self.colors['text_primary'],
                               insertbackground=self.colors['accent'],
                               borderwidth=0,
                               highlightthickness=0,
                               wrap=tk.WORD)
        
        # إعداد ألوان الرسائل
        self.log_text.tag_configure("INFO", foreground=self.colors['accent'])
        self.log_text.tag_configure("SUCCESS", foreground=self.colors['success'])
        self.log_text.tag_configure("ERROR", foreground=self.colors['error'])
        self.log_text.tag_configure("WARNING", foreground=self.colors['warning'])
        self.log_text.tag_configure("PROGRESS", foreground=self.colors['gradient_start'])
        self.log_text.tag_configure("timestamp", foreground=self.colors['text_muted'])
        
        log_scrollbar = ttk.Scrollbar(log_container, orient="vertical",
                                     command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scrollbar.pack(side="right", fill="y")
        
        self.log_card = card
        
    def create_status_bar(self, parent):
        """شريط الحالة السفلي"""
        status_bar = tk.Frame(parent, bg=self.colors['bg_secondary'], height=40)
        status_bar.pack(fill="x", side="bottom")
        status_bar.pack_propagate(False)
        
        status_content = tk.Frame(status_bar, bg=self.colors['bg_secondary'])
        status_content.pack(fill="both", expand=True, padx=20, pady=5)
        
        # الحالة
        self.status_var = tk.StringVar(value="🟢 جاهز")
        status_label = tk.Label(status_content, textvariable=self.status_var,
                              font=self.fonts['small'],
                              bg=self.colors['bg_secondary'],
                              fg=self.colors['text_secondary'])
        status_label.pack(side="left")
        
        # معلومات إضافية
        self.status_details_var = tk.StringVar()
        details_label = tk.Label(status_content, textvariable=self.status_details_var,
                                font=self.fonts['small'],
                                bg=self.colors['bg_secondary'],
                                fg=self.colors['text_muted'])
        details_label.pack(side="left", padx=(20, 0))
        
        # معلومات النظام
        system_info = tk.Label(status_content, text="v2.0 Pro | Python 3.x",
                              font=self.fonts['small'],
                              bg=self.colors['bg_secondary'],
                              fg=self.colors['text_muted'])
        system_info.pack(side="right")
        
    # دوال مساعدة لإنشاء العناصر
    def create_card(self, parent, title, height=None):
        """إنشاء بطاقة بتصميم عصري"""
        card = tk.Frame(parent, bg=self.colors['bg_card'])
        card.pack(fill="x", pady=10)
        
        if height:
            card.configure(height=height)
            card.pack_propagate(False)
        
        # شريط العنوان
        title_bar = tk.Frame(card, bg=self.colors['bg_card'], height=40)
        title_bar.pack(fill="x")
        title