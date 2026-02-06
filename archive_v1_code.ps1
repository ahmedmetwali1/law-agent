# PowerShell Script لأرشفة أكواد V1

Write-Host "🗂️ بدء عملية الأرشفة..." -ForegroundColor Cyan
Write-Host "====================================`n" -ForegroundColor Cyan

# 1. إنشاء المجلدات
Write-Host "📁 إنشاء مجلدات الأرشيف..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "archive" | Out-Null
New-Item -ItemType Directory -Force -Path "archive\v1_nodes" | Out-Null
New-Item -ItemType Directory -Force -Path "archive\v1_tools" | Out-Null
Write-Host "✅ تم إنشاء المجلدات`n" -ForegroundColor Green

# 2. أرشفة الـ Nodes
Write-Host "📦 نقل الـ V1 Nodes..." -ForegroundColor Yellow

$nodes = @(
    "agents\graph\nodes\council.py",
    "agents\graph\nodes\drafter.py",
    "agents\graph\nodes\investigator.py",
    "agents\graph\nodes\research.py",
    "agents\graph\nodes\general.py",
    "agents\graph\nodes\reviewer.py",
    "agents\graph\nodes\router.py"
)

foreach ($node in $nodes) {
    if (Test-Path $node) {
        Move-Item -Path $node -Destination "archive\v1_nodes\" -Force
        Write-Host "  ✓ $node" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ ملف غير موجود: $node" -ForegroundColor Yellow
    }
}

Write-Host ""

# 3. أرشفة الأدوات
Write-Host "🔧 نقل الأدوات القديمة..." -ForegroundColor Yellow

$tools = @(
    "agents\tools\semantic_tools.py",
    "agents\tools\smart_finalizer.py"
)

foreach ($tool in $tools) {
    if (Test-Path $tool) {
        Move-Item -Path $tool -Destination "archive\v1_tools\" -Force
        Write-Host "  ✓ $tool" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ ملف غير موجود: $tool" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "⚠️  تم إلغاء أرشفة read_tool.py (وظيفة Navigation مهمة)" -ForegroundColor Yellow
Write-Host ""

# 4. التحقق
Write-Host "🔍 التحقق من النتائج..." -ForegroundColor Cyan

Write-Host "`n📊 محتويات الأرشيف:" -ForegroundColor Cyan
Get-ChildItem -Recurse "archive\" | Select-Object FullName

Write-Host "`n✅ اكتملت عملية الأرشفة!" -ForegroundColor Green
Write-Host "====================================`n" -ForegroundColor Cyan

Write-Host "📝 الخطوات التالية:" -ForegroundColor Yellow
Write-Host "  1. اختبار النظام للتأكد من عدم وجود أخطاء"
Write-Host "  2. دمج وظيفة Navigation من read_tool.py"
Write-Host "  3. بعد أسبوعين: حذف مجلد archive نهائياً"
