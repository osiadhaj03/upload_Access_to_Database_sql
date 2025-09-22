#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
حل نهائي لملفات .bok - استخدام أدوات مختلفة
"""

import os
import sys
import subprocess
import shutil
import tempfile
import time
from pathlib import Path

class FinalBokSolution:
    """حل نهائي لمعالجة ملفات .bok"""
    
    def __init__(self):
        self.temp_files = []
    
    def diagnose_system(self):
        """تشخيص النظام وتحديد أفضل طريقة"""
        diagnosis = {
            'python_version': sys.version,
            'platform': sys.platform,
            'access_runtime_available': False,
            'recommended_solution': None
        }
        
        # فحص وجود Access Runtime
        try:
            import pyodbc
            drivers = pyodbc.drivers()
            if 'Microsoft Access Driver (*.mdb, *.accdb)' in drivers:
                diagnosis['access_runtime_available'] = True
        except:
            pass
        
        # تحديد الحل المناسب
        if diagnosis['access_runtime_available']:
            diagnosis['recommended_solution'] = 'install_ace_engine'
        else:
            diagnosis['recommended_solution'] = 'install_access_runtime'
        
        return diagnosis
    
    def create_solution_guide(self):
        """إنشاء دليل الحلول للمستخدم"""
        
        guide = """
# دليل حل مشكلة ملفات .bok

## المشكلة المكتشفة
ملفات .bok هي قواعد بيانات Access قديمة تحتاج إعدادات خاصة للقراءة.

## الحلول المتاحة

### الحل الأول: تثبيت Microsoft Access Database Engine 2016 (مُوصى)

1. **تحميل المحرك:**
   - 64-bit: https://www.microsoft.com/en-us/download/details.aspx?id=54920
   - 32-bit: نفس الرابط، اختر النسخة المناسبة

2. **التثبيت:**
   - قم بإغلاق جميع تطبيقات Office
   - شغل ملف التثبيت كمدير
   - اتبع التعليمات

3. **إعادة التشغيل:**
   - أعد تشغيل الكمبيوتر
   - جرب التطبيق مرة أخرى

### الحل الثاني: تحويل ملفات .bok إلى .accdb يدوياً

1. **إذا كان لديك Microsoft Access:**
   - افتح Access
   - افتح ملف .bok (غير امتداد اسم الملف إلى .mdb مؤقتاً)
   - احفظه كـ .accdb جديد
   - استخدم الملف الجديد في التطبيق

2. **إذا لم يكن لديك Access:**
   - استخدم أداة تحويل مجانية مثل MDB Viewer Plus
   - أو استخدم LibreOffice Base (مجاني)

### الحل الثالث: محول تلقائي (متقدم)

نحن نطور محول خاص لا يحتاج Access، سيكون متاح قريباً.

## التحقق من الحل

بعد تطبيق أي حل، جرب:
1. فتح التطبيق
2. اختيار ملف .bok
3. إذا ظهرت رسالة "تم اكتشاف ملف .bok" بدون خطأ، فالحل نجح

## الدعم الفني

إذا استمرت المشكلة، يرجى إرسال:
- نوع نظام التشغيل (Windows 10/11)
- نوع المعالج (32-bit/64-bit)
- رسالة الخطأ كاملة
"""
        
        return guide
    
    def create_temporary_workaround(self, bok_path, callback=None):
        """حل مؤقت: إرشاد المستخدم لتحويل يدوي"""
        
        if callback:
            callback(f"🔧 ملف .bok مُكتشف: {os.path.basename(bok_path)}")
            callback("⚠️ هذا الملف يحتاج تحويل خاص")
            callback("📋 يرجى اتباع التعليمات في دليل الحلول")
        
        # إنشاء دليل الحلول
        guide_content = self.create_solution_guide()
        
        try:
            # حفظ الدليل في نفس مجلد التطبيق
            guide_path = os.path.join(os.getcwd(), "BOK_Files_Solution_Guide.md")
            with open(guide_path, "w", encoding="utf-8") as f:
                f.write(guide_content)
            
            if callback:
                callback(f"📄 تم إنشاء دليل الحلول: {guide_path}")
                callback("🔗 يرجى فتح الدليل واتباع التعليمات")
        except Exception as e:
            if callback:
                callback(f"خطأ في إنشاء الدليل: {e}")
        
        return False, "يحتاج تحويل يدوي - راجع دليل الحلول"
    
    def suggest_alternative_workflow(self, bok_files, callback=None):
        """اقتراح سير عمل بديل للمستخدم"""
        
        if callback:
            callback(f"🎯 سير عمل مقترح لمعالجة {len(bok_files)} ملف .bok:")
            callback("")
            callback("📋 الخطوات المطلوبة:")
            callback("1. تثبيت Microsoft Access Database Engine 2016")
            callback("2. إعادة تشغيل الكمبيوتر")
            callback("3. إعادة تشغيل هذا التطبيق")
            callback("4. إعادة تجريب تحويل ملفات .bok")
            callback("")
            callback("📁 الملفات المُكتشفة:")
            
            for i, bok_file in enumerate(bok_files, 1):
                file_size = os.path.getsize(bok_file) / (1024*1024)
                callback(f"   {i}. {os.path.basename(bok_file)} ({file_size:.1f} MB)")
            
            callback("")
            callback("⚡ حل سريع: تغيير امتداد .bok إلى .mdb وتجريب التحويل")
            callback("📞 للمساعدة: راجع ملف BOK_Files_Solution_Guide.md")

def integrate_bok_solution_in_gui():
    """دمج الحل في واجهة التطبيق"""
    
    integration_code = '''
# في shamela_gui.py - إضافة في بداية الملف
from final_bok_solution import FinalBokSolution

# في دالة التحويل
def handle_bok_files_in_conversion(self, selected_files):
    """معالجة ملفات .bok في عملية التحويل"""
    
    bok_files = [f for f in selected_files if f.lower().endswith('.bok')]
    regular_files = [f for f in selected_files if not f.lower().endswith('.bok')]
    
    if bok_files:
        bok_solution = FinalBokSolution()
        
        self.log_message(f"🔍 تم اكتشاف {len(bok_files)} ملف .bok")
        
        # عرض حل مؤقت
        bok_solution.suggest_alternative_workflow(bok_files, self.log_message)
        
        # تشخيص النظام
        diagnosis = bok_solution.diagnose_system()
        
        if diagnosis['recommended_solution'] == 'install_ace_engine':
            self.log_message("💡 حل: تثبيت Microsoft Access Database Engine 2016")
            self.log_message("🔗 رابط التحميل: https://www.microsoft.com/en-us/download/details.aspx?id=54920")
        
        # إنشاء دليل الحلول
        bok_solution.create_temporary_workaround(bok_files[0], self.log_message)
        
        # معالجة الملفات العادية فقط في الوقت الحالي
        return regular_files
    
    return selected_files
'''
    
    return integration_code

def main():
    """اختبار الحل النهائي"""
    print("=== الحل النهائي لملفات .bok ===")
    print()
    
    solution = FinalBokSolution()
    
    # تشخيص النظام
    print("🔍 تشخيص النظام...")
    diagnosis = solution.diagnose_system()
    
    print(f"Python: {diagnosis['python_version'][:20]}...")
    print(f"Platform: {diagnosis['platform']}")
    print(f"Access Runtime: {'✅ متوفر' if diagnosis['access_runtime_available'] else '❌ غير متوفر'}")
    print(f"الحل الموصى: {diagnosis['recommended_solution']}")
    print()
    
    # اختبار على ملفات موجودة
    bok_folder = Path("d:/test3/bok file")
    if bok_folder.exists():
        bok_files = list(bok_folder.glob("*.bok"))
        
        if bok_files:
            print(f"📁 تم العثور على {len(bok_files)} ملف .bok")
            
            # اقتراح سير عمل
            solution.suggest_alternative_workflow(bok_files, print)
            
            print()
            print("📄 إنشاء دليل الحلول...")
            solution.create_temporary_workaround(str(bok_files[0]), print)
            
        else:
            print("لم يتم العثور على ملفات .bok")
    else:
        print("مجلد ملفات .bok غير موجود")
    
    print()
    print("=== انتهى التشخيص ===")

if __name__ == "__main__":
    main()
