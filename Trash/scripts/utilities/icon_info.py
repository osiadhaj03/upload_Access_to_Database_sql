# إذا كنت تريد إضافة أيقونة للتطبيق، ضع ملف .ico هنا
# أو استخدم أدوات أونلاين لتحويل صورة إلى .ico

# مثال على تحديث setup.py مع الأيقونة:
# icon="app_icon.ico"

# مثال على تحديث PyInstaller مع الأيقونة:
# pyinstaller --onefile --windowed --icon=app_icon.ico --name "محول_كتب_الشاملة" shamela_gui.py

# رمز ASCII للكتاب (يمكن استخدامه في النصوص):
BOOK_ASCII = """
    📚 محول كتب الشاملة 📚
    
    ┌─────────────────────┐
    │  📖  الشـــاملة   │
    │                     │
    │  Access → MySQL     │
    │                     │
    │  🔄 محول الكتب    │
    └─────────────────────┘
"""

print(BOOK_ASCII)
