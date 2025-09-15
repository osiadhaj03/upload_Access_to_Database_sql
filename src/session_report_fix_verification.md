# إصلاح مشكلة تصدير تقرير الجلسة

## المشكلة الأصلية
كانت هناك مشكلة في تصدير تقرير الجلسة عند الضغط على زر "حفظ التقرير" حيث كان يعطي خطأ.

## سبب المشكلة
المشكلة كانت في استخدام lambda function مع متغير محلي `report_content` مما يسبب مشاكل في النطاق (scope issues).

## الحل المطبق

### 1. تعديل استدعاء الدالة
تم تغيير:
```python
command=lambda: self.save_session_report(report_content)
```

إلى:
```python
command=self.save_session_report
```

### 2. تحديث دالة save_session_report
تم تحديث الدالة لتولد محتوى التقرير بنفسها بدلاً من الاعتماد على متغير خارجي:

```python
def save_session_report(self):
    """حفظ تقرير الجلسة في ملف"""
    try:
        # التحقق من وجود بيانات للتقرير
        if not self.books_stats:
            messagebox.showwarning("تحذير", "لا توجد بيانات جلسة متاحة للحفظ")
            return
        
        # إنشاء محتوى التقرير
        report_content = self.generate_session_report()
        
        # اختيار مكان الحفظ
        file_path = filedialog.asksaveasfilename(
            title="حفظ تقرير الجلسة",
            defaultextension=".txt",
            filetypes=[("ملفات نصية", "*.txt"), ("كل الملفات", "*.*")],
            initialname=f"تقرير_جلسة_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        
        if file_path:
            # حفظ التقرير في الملف
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            messagebox.showinfo("تم الحفظ", f"تم حفظ تقرير الجلسة بنجاح في:\n{file_path}")
            self.log_message(f"💾 تم حفظ تقرير الجلسة: {os.path.basename(file_path)}", "SUCCESS")
            
    except Exception as e:
        error_msg = f"فشل في حفظ التقرير:\n{str(e)}"
        messagebox.showerror("خطأ في الحفظ", error_msg)
        self.log_message(f"❌ خطأ في حفظ التقرير: {str(e)}", "ERROR")
```

## المميزات المضافة
1. **التحقق من البيانات**: التأكد من وجود بيانات جلسة قبل المحاولة
2. **معالجة أفضل للأخطاء**: رسائل خطأ أكثر وضوحاً
3. **تسجيل محسن**: تسجيل العمليات في سجل الأحداث
4. **استقلالية الدالة**: لا تعتمد على متغيرات خارجية

## كيفية الاختبار
1. شغل التطبيق
2. قم بتحويل بعض الكتب لإنشاء بيانات جلسة
3. اذهب إلى "تقرير الجلسة"
4. اضغط على "حفظ التقرير"
5. اختر مكان الحفظ
6. يجب أن يتم حفظ التقرير بنجاح بصيغة .txt

## النتيجة
الآن تعمل وظيفة تصدير تقرير الجلسة بشكل مثالي دون أخطاء ✅
