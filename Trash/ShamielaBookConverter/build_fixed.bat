@echo off
chcp 65001 > nul
echo ================================================
echo           محول كتب الشاملة - الإصدار 2.0
echo                   إصلاح مشكلة MySQL  
echo ================================================
echo.

echo [1/4] تثبيت المتطلبات...
pip install -r requirements.txt

echo.
echo [2/4] إصلاح مشكلة MySQL...
python fix_mysql.py

echo.
echo [3/4] بناء ملف EXE المحسن...
python build_exe_fixed.py

echo.
echo [4/4] انتهى!
echo.
echo ملف EXE موجود في مجلد dist
echo.
pause