@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM =====================================================
REM     محول كتب الشاملة - ملف التشغيل التلقائي
REM =====================================================

echo.
echo ========================================================
echo           محول كتب الشاملة - Shamela Converter
echo ========================================================
echo.
echo جاري تشغيل البرنامج...
echo.

REM التحقق من وجود الملف التنفيذي
if not exist "dist\shamela_converter_src.exe" (
    echo ❌ خطأ: لم يتم العثور على الملف التنفيذي!
    echo المسار المطلوب: dist\shamela_converter_src.exe
    echo.
    echo الحلول المقترحة:
    echo 1. تأكد من وجود مجلد dist
    echo 2. تأكد من وجود الملف shamela_converter_src.exe
    echo 3. قم ببناء المشروع باستخدام PyInstaller
    echo.
    pause
    exit /b 1
)

REM التحقق من وجود ملف إعدادات قاعدة البيانات
if not exist "db_settings.json" (
    echo ⚠️  تحذير: لم يتم العثور على ملف إعدادات قاعدة البيانات
    echo سيتم استخدام الإعدادات الافتراضية
    echo.
)

REM إنشاء مجلد السجلات إذا لم يكن موجوداً
if not exist "logs" mkdir logs

REM تسجيل وقت التشغيل
echo [%date% %time%] بدء تشغيل محول كتب الشاملة >> logs\run_log.txt

REM تشغيل البرنامج مع معالجة الأخطاء
echo 🚀 تشغيل محول كتب الشاملة...
echo.

cd /d "%~dp0"
start "محول كتب الشاملة" /wait "dist\shamela_converter_src.exe"

REM التحقق من رمز الخروج
if !errorlevel! equ 0 (
    echo.
    echo ✅ تم إغلاق البرنامج بنجاح
    echo [%date% %time%] تم إغلاق البرنامج بنجاح >> logs\run_log.txt
) else (
    echo.
    echo ❌ حدث خطأ أثناء تشغيل البرنامج
    echo رمز الخطأ: !errorlevel!
    echo [%date% %time%] خطأ في التشغيل - رمز الخطأ: !errorlevel! >> logs\run_log.txt
    echo.
    echo الحلول المقترحة:
    echo 1. تشغيل البرنامج كمسؤول (Run as Administrator)
    echo 2. التأكد من وجود جميع المكتبات المطلوبة
    echo 3. فحص ملف السجل: logs\run_log.txt
    echo 4. إعادة تشغيل الكمبيوتر
    echo 5. تعطيل برنامج مكافحة الفيروسات مؤقتاً
    echo.
)

echo.
echo اضغط أي مفتاح للخروج...
pause >nul
exit /b !errorlevel!