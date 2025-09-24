@echo off
chcp 65001 > nul
echo.
echo ================================================
echo 🧪 اختبار سريع لمحول كتب الشاملة
echo ================================================
echo.

echo 🔍 فحص متطلبات التشغيل...
echo.

REM فحص وجود الملف التنفيذي
if not exist "ShamielaConverter.exe" (
    echo ❌ ملف ShamielaConverter.exe غير موجود!
    goto :error
)
echo ✅ ملف البرنامج موجود

REM فحص اتصال MySQL (محاولة بسيطة)
echo 🔄 فحص اتصال MySQL...
mysql --version > nul 2>&1
if %errorlevel% == 0 (
    echo ✅ MySQL متوفر في النظام
) else (
    echo ⚠️  لم يتم العثور على MySQL في PATH
    echo    💡 تأكد من تشغيل MySQL Server
)

echo.
echo 🚀 بدء تشغيل البرنامج...
echo.

REM تشغيل البرنامج
start "" "ShamielaConverter.exe"

echo ✅ تم تشغيل البرنامج بنجاح!
echo.
echo 💡 نصائح للاختبار:
echo    1. جرب الاتصال بقاعدة بيانات فارغة أولاً
echo    2. اختر ملف كتاب واحد للاختبار
echo    3. راقب رسائل السجل في البرنامج
echo.
pause
goto :end

:error
echo.
echo ❌ فشل في الاختبار!
echo 💡 تحقق من وجود جميع الملفات المطلوبة
echo.
pause

:end