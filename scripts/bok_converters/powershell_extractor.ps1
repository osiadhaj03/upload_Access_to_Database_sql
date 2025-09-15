# PowerShell script لاستخراج البيانات من ملفات .bok
param(
    [Parameter(Mandatory=$true)]
    [string]$BokFilePath,
    
    [Parameter(Mandatory=$false)]
    [string]$OutputPath = "d:\test3\data\powershell_export"
)

Write-Host "🚀 PowerShell BOK Extractor" -ForegroundColor Green
Write-Host "=" * 50

# إنشاء مجلد الإخراج
if (!(Test-Path $OutputPath)) {
    New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null
}

try {
    Write-Host "🔍 محاولة فتح ملف .bok..." -ForegroundColor Yellow
    
    # إنشاء كائن Access
    $accessApp = New-Object -ComObject Access.Application
    $accessApp.Visible = $false
    
    # فتح قاعدة البيانات
    $accessApp.OpenCurrentDatabase($BokFilePath)
    Write-Host "✅ تم فتح الملف بنجاح" -ForegroundColor Green
    
    # الحصول على قائمة الجداول
    $tables = $accessApp.CurrentDb().TableDefs | Where-Object { $_.Name -notlike "MSys*" }
    Write-Host "📋 الجداول الموجودة:" -ForegroundColor Cyan
    
    foreach ($table in $tables) {
        $recordCount = $accessApp.CurrentDb().OpenRecordset("SELECT COUNT(*) FROM [$($table.Name)]").Fields(0).Value
        Write-Host "  - $($table.Name): $recordCount سجل" -ForegroundColor White
    }
    
    # استخراج البيانات من الجداول المهمة
    $importantTables = @("Main", "TBMain", "TBTitles", "Books", "BookInfo")
    
    foreach ($tableName in $importantTables) {
        $table = $tables | Where-Object { $_.Name -eq $tableName }
        if ($table) {
            Write-Host "📤 تصدير جدول: $tableName" -ForegroundColor Yellow
            
            $outputFile = Join-Path $OutputPath "$tableName.csv"
            
            # تصدير كـ CSV
            $accessApp.DoCmd.TransferText(
                [Microsoft.Office.Interop.Access.AcTextTransferType]::acExportDelim,
                $null,
                $tableName,
                $outputFile,
                $true  # HasFieldNames
            )
            
            Write-Host "  ✅ تم حفظ: $outputFile" -ForegroundColor Green
        }
    }
    
    Write-Host "🎉 تم التصدير بنجاح!" -ForegroundColor Green
    
} catch {
    Write-Host "❌ خطأ: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "💡 تأكد من:" -ForegroundColor Yellow
    Write-Host "  1. تثبيت Microsoft Access" -ForegroundColor White
    Write-Host "  2. صلاحيات الوصول للملف" -ForegroundColor White
    Write-Host "  3. إغلاق الملف في برامج أخرى" -ForegroundColor White
    
} finally {
    # إغلاق Access
    if ($accessApp) {
        try {
            $accessApp.CloseCurrentDatabase()
            $accessApp.Quit()
            [System.Runtime.Interopservices.Marshal]::ReleaseComObject($accessApp) | Out-Null
        } catch {
            # تجاهل أخطاء الإغلاق
        }
    }
}

Write-Host "`n📁 مجلد الإخراج: $OutputPath" -ForegroundColor Cyan
Write-Host "🔄 يمكنك الآن استخدام csv_extractor.py لمعالجة الملفات" -ForegroundColor Yellow
