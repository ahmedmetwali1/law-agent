# PowerShell Script - Archive V1 Nodes Only
# Safe archival of legacy agent files

Write-Host ""
Write-Host "Archive V1 Nodes" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host ""

# Check path
if (-not (Test-Path "agents\graph\nodes")) {
    Write-Host "ERROR: agents\graph\nodes directory not found!" -ForegroundColor Red
    Write-Host "Run this script from project root (e:\law)" -ForegroundColor Yellow
    exit 1
}

# 1. Create archive directory
Write-Host "Creating archive directory..." -ForegroundColor Yellow

if (-not (Test-Path "archive")) {
    New-Item -ItemType Directory -Path "archive" | Out-Null
    Write-Host "  Created: archive\" -ForegroundColor Green
}

if (-not (Test-Path "archive\v1_nodes")) {
    New-Item -ItemType Directory -Path "archive\v1_nodes" | Out-Null
    Write-Host "  Created: archive\v1_nodes\" -ForegroundColor Green
}

Write-Host ""

# 2. List of V1 nodes to archive
$v1_nodes = @(
    "council.py",
    "drafter.py",
    "investigator.py",
    "research.py",
    "general.py",
    "reviewer.py",
    "router.py"
)

Write-Host "Moving V1 nodes to archive..." -ForegroundColor Yellow
Write-Host ""

$moved_count = 0
$not_found_count = 0

foreach ($node in $v1_nodes) {
    $source_path = "agents\graph\nodes\$node"
    $dest_path = "archive\v1_nodes\$node"
    
    if (Test-Path $source_path) {
        try {
            Move-Item -Path $source_path -Destination $dest_path -Force
            Write-Host "  OK: $node" -ForegroundColor Green
            $moved_count++
        }
        catch {
            Write-Host "  FAIL: $node - $_" -ForegroundColor Red
        }
    }
    else {
        Write-Host "  SKIP: $node (not found)" -ForegroundColor DarkGray
        $not_found_count++
    }
}

Write-Host ""
Write-Host ("-" * 60) -ForegroundColor DarkGray
Write-Host ""

# 3. Summary
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  Moved: $moved_count files" -ForegroundColor Green
if ($not_found_count -gt 0) {
    Write-Host "  Not found: $not_found_count files" -ForegroundColor Yellow
}

Write-Host ""

# 4. Show archive contents
Write-Host "Archive contents:" -ForegroundColor Cyan
Get-ChildItem -Path "archive\v1_nodes" -Filter "*.py" | ForEach-Object {
    $size_kb = [math]::Round($_.Length / 1KB, 1)
    Write-Host "  $($_.Name) ($size_kb KB)" -ForegroundColor White
}

Write-Host ""
Write-Host ("-" * 60) -ForegroundColor DarkGray
Write-Host ""

# 5. Create README
$readme = "# V1 Nodes Archive`n`n"
$readme += "Archived on: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n`n"
$readme += "## Archived Files`n"
foreach ($node in $v1_nodes) {
    $readme += "- $node`n"
}
$readme += "`n## Reason`n"
$readme += "Replaced with V2 versions`n`n"
$readme += "## Restore Command`n"
$readme += "Copy-Item archive\v1_nodes\council.py agents\graph\nodes\`n"

$readme | Out-File -FilePath "archive\v1_nodes\README.md" -Encoding UTF8
Write-Host "Created README.md in archive" -ForegroundColor Green

Write-Host ""
Write-Host ("-" * 60) -ForegroundColor DarkGray
Write-Host ""

# 6. Verify V2 nodes exist
Write-Host "Verifying V2 nodes..." -ForegroundColor Yellow
Write-Host ""

$v2_nodes = @(
    "council_v2.py",
    "drafter_v2.py",
    "deep_research.py",
    "judge.py",
    "gatekeeper.py"
)

$all_v2_exist = $true
foreach ($node in $v2_nodes) {
    $path = "agents\graph\nodes\$node"
    if (Test-Path $path) {
        Write-Host "  OK: $node exists" -ForegroundColor Green
    }
    else {
        Write-Host "  MISSING: $node" -ForegroundColor Red
        $all_v2_exist = $false
    }
}

Write-Host ""

if ($all_v2_exist) {
    Write-Host "SUCCESS: All V2 nodes present!" -ForegroundColor Green
}
else {
    Write-Host "WARNING: Some V2 nodes are missing!" -ForegroundColor Red
}

Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "Archive completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Test the system" -ForegroundColor White
Write-Host "2. Monitor for 2 weeks" -ForegroundColor White
Write-Host "3. Delete archive if no issues" -ForegroundColor White
Write-Host ""
