# محول كتب الشاملة - Shamela Books Converter

تطبيق لتحويل كتب مكتبة الشاملة من قاعدة بيانات Microsoft Access إلى قاعدة بيانات MySQL مع واجهة رسومية سهلة الاستخدام.

## المطورون - Developers

- **Osaid Salah** - مطور رئيسي
- **Aziz Hashlamoun** - مطور مشارك

## نظرة عامة - Overview

يوفر هذا التطبيق حلاً شاملاً لتحويل كتب مكتبة الشاملة من تنسيق Microsoft Access إلى MySQL، مع الحفاظ على بنية البيانات والعلاقات بين الجداول.

## المميزات الرئيسية - Key Features

### 🔄 تحويل شامل للبيانات
- تحويل كامل لكتب الشاملة من Access إلى MySQL
- الحفاظ على بنية البيانات والعلاقات
- دعم الترقيم التلقائي والفهارس

### 🖥️ واجهة رسومية متقدمة
- واجهة مستخدم بسيطة وسهلة الاستخدام
- شريط تقدم مفصل لمتابعة عملية التحويل
- عرض إحصائيات مفصلة للتحويل
- نظام رسائل متطور لمتابعة العمليات

### 📊 إدارة البيانات الذكية
- اكتشاف تلقائي لجداول قاعدة البيانات
- تحويل أنواع البيانات بشكل ذكي
- معالجة النصوص العربية بشكل صحيح
- دعم الترميز UTF-8

### ⚡ أداء محسن
- معالجة متوازية للبيانات
- نظام ذاكرة تخزين مؤقت ذكي
- تحسينات خاصة للملفات الكبيرة

## متطلبات النظام - System Requirements

### البرمجيات المطلوبة
- Windows 10/11
- Python 3.8+ (للتشغيل من المصدر)
- Microsoft Access Database Engine
- MySQL Server 5.7+

### مكتبات Python المطلوبة
```
tkinter
pymysql
pyodbc
pathlib
threading
queue
json
datetime
uuid
re
typing
```

## التثبيت والتشغيل - Installation & Usage

### الطريقة الأولى: استخدام الملف التنفيذي
1. قم بتحميل الملف `shamela_gui.exe` من مجلد `dist`
2. شغل الملف مباشرة - لا يحتاج تثبيت Python

### الطريقة الثانية: تشغيل من المصدر
1. استنسخ المشروع:
```bash
git clone https://github.com/osiadhaj03/upload_Access_to_Database_sql.git
cd upload_Access_to_Database_sql
```

2. ثبت المكتبات المطلوبة:
```bash
pip install pymysql pyodbc
```

3. شغل التطبيق:
```bash
python shamela_gui.py
```

## كيفية الاستخدام - How to Use

### 1. إعداد الاتصال بقاعدة البيانات
- أدخل معلومات خادم MySQL (العنوان، المنفذ، اسم المستخدم، كلمة المرور)
- اختبر الاتصال للتأكد من صحة البيانات

### 2. اختيار ملف قاعدة البيانات
- اضغط على "اختيار ملف قاعدة البيانات"
- اختر ملف `.mdb` الخاص بكتاب الشاملة

### 3. إعداد التحويل
- اختر اسم قاعدة البيانات الجديدة في MySQL
- حدد الخيارات المطلوبة للتحويل

### 4. بدء التحويل
- اضغط على "بدء التحويل"
- تابع التقدم من خلال شريط التقدم والرسائل

## بنية المشروع - Project Structure

```
├── shamela_gui.py          # الملف الرئيسي للتطبيق
├── shamela_gui.spec        # ملف إعدادات PyInstaller
├── db_settings.json        # ملف إعدادات قاعدة البيانات
├── dist/                   # مجلد الملفات التنفيذية
│   └── shamela_gui.exe     # الملف التنفيذي الرئيسي
├── build/                  # ملفات البناء المؤقتة
└── README.md              # هذا الملف
```

## الميزات التقنية - Technical Features

### إدارة قواعد البيانات
- **Access Connection**: اتصال محسن بقواعد بيانات Microsoft Access
- **MySQL Integration**: تكامل كامل مع MySQL باستخدام PyMySQL
- **Automatic Schema Creation**: إنشاء تلقائي لمخطط قاعدة البيانات

### معالجة البيانات
- **Unicode Support**: دعم كامل للنصوص العربية والأحرف الخاصة
- **Data Type Mapping**: تحويل ذكي لأنواع البيانات
- **Error Handling**: معالجة شاملة للأخطاء والاستثناءات

### واجهة المستخدم
- **Modern GUI**: واجهة عصرية باستخدام Tkinter
- **Real-time Progress**: متابعة مباشرة لتقدم العمليات
- **Multi-threading**: معالجة متوازية لضمان عدم تجمد الواجهة

## استكشاف الأخطاء - Troubleshooting

### مشاكل شائعة وحلولها

#### خطأ في الاتصال بـ MySQL
```
الحل: تأكد من تشغيل خادم MySQL وصحة بيانات الاتصال
```

#### خطأ في قراءة ملف Access
```
الحل: تأكد من تثبيت Microsoft Access Database Engine
```

#### خطأ في الترميز
```
الحل: تأكد من أن ملف Access يدعم الترميز UTF-8
```

## المساهمة في المشروع - Contributing

نرحب بالمساهمات! إذا كنت تريد المساهمة:

1. Fork المشروع
2. أنشئ branch جديد (`git checkout -b feature/AmazingFeature`)
3. اعمل commit للتغييرات (`git commit -m 'Add some AmazingFeature'`)
4. ادفع إلى Branch (`git push origin feature/AmazingFeature`)
5. افتح Pull Request

## الترخيص - License

هذا المشروع مرخص تحت رخصة MIT - انظر ملف [LICENSE](LICENSE) للتفاصيل.

## الإصدارات - Versions

### الإصدار 2.0.0 - الحالي
- واجهة رسومية محدثة
- دعم PyMySQL بدلاً من mysql-connector-python
- تحسينات في الأداء والاستقرار
- إصلاح مشاكل PyInstaller

### الإصدار 1.0.0
- الإصدار الأول من التطبيق
- الوظائف الأساسية للتحويل

## التواصل - Contact

للاستفسارات والدعم الفني:
- **GitHub Issues**: [رابط المشروع](https://github.com/osiadhaj03/upload_Access_to_Database_sql/issues)
- **المطور الرئيسي**: Osaid Salah
- **المطور المشارك**: Aziz Hashlamoun

## شكر وتقدير - Acknowledgments

- شكر خاص لمجتمع مكتبة الشاملة
- شكر لمطوري مكتبات Python المستخدمة
- شكر لكل من ساهم في تطوير هذا المشروع

---

**ملاحظة**: هذا المشروع تم تطويره لخدمة مجتمع الباحثين والدارسين في العلوم الشرعية والتراث الإسلامي.

## Screenshots - لقطات شاشة

### الواجهة الرئيسية
![الواجهة الرئيسية](docs/screenshots/main_interface.png)

### عملية التحويل
![عملية التحويل](docs/screenshots/conversion_process.png)

---

**Made with ❤️ by Osaid Salah & Aziz Hashlamoun**