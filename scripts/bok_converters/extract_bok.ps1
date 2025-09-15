# PowerShell BOK Extractor - مصحح
param(
    [string]$BokFile = "d:\test3\bok file\بغية السائل.bok"
)

Write-Host "🚀 PowerShell BOK Extractor" -ForegroundColor Green
Write-Host "File: $BokFile"

$OutputPath = "d:\test3\data\powershell_export"
if (!(Test-Path $OutputPath)) {
    New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null
}

try {
    Write-Host "🔍 Opening Access..." -ForegroundColor Yellow
    $accessApp = New-Object -ComObject Access.Application
    $accessApp.Visible = $false
    
    $accessApp.OpenCurrentDatabase($BokFile)
    Write-Host "✅ Database opened" -ForegroundColor Green
    
    $tables = $accessApp.CurrentDb().TableDefs | Where-Object { $_.Name -notlike "MSys*" }
    Write-Host "📋 Found $($tables.Count) tables:" -ForegroundColor Cyan
    
    foreach ($table in $tables) {
        try {
            $recordCount = $accessApp.CurrentDb().OpenRecordset("SELECT COUNT(*) FROM [$($table.Name)]").Fields(0).Value
            Write-Host "  - $($table.Name): $recordCount records" -ForegroundColor White
            
            if ($recordCount -gt 0) {
                $outputFile = Join-Path $OutputPath "$($table.Name).csv"
                $accessApp.DoCmd.TransferText(0, $null, $table.Name, $outputFile, $true)
                Write-Host "    ✅ Exported to: $outputFile" -ForegroundColor Green
            }
        }
        catch {
            Write-Host "    ⚠️ Skip $($table.Name): $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
    
    Write-Host "🎉 Export completed!" -ForegroundColor Green
    
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
} finally {
    if ($accessApp) {
        try {
            $accessApp.CloseCurrentDatabase()
            $accessApp.Quit()
        } catch { }
    }
}

Write-Host "📁 Output folder: $OutputPath" -ForegroundColor Cyan
