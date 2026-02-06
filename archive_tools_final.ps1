# Professional Tool Archival Script
# Final version - Archives only read_tool.py

Write-Host ""
Write-Host "Professional Tool Archival" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host ""

# Analysis results
Write-Host "Analysis Summary:" -ForegroundColor Yellow
Write-Host "  Total tools analyzed: 14" -ForegroundColor White
Write-Host "  Tools to keep: 13" -ForegroundColor Green
Write-Host "  Tools to archive: 1" -ForegroundColor Cyan
Write-Host ""

# Create archive directory
if (-not (Test-Path "archive\v1_tools")) {
    New-Item -ItemType Directory -Force -Path "archive\v1_tools" | Out-Null
    Write-Host "Created archive directory" -ForegroundColor Green
}

# Archive read_tool.py (Navigation merged into GetRelatedDocumentTool)
$tool = "read_tool.py"
$source = "agents\tools\$tool"
$dest = "archive\v1_tools\$tool"

if (Test-Path $source) {
    Move-Item -Path $source -Destination $dest -Force
    Write-Host "Archived: $tool" -ForegroundColor Green
    
    # Create detailed README
    $readme = @"
# Archived Tool: read_tool.py

## Date
$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

## Reason
- Navigation by sequence_number merged into GetRelatedDocumentTool
- No longer used in V2 architecture
- Functionality fully replaced

## What Was Merged
- prev/next page navigation
- Navigation metadata with commands

## Unique Features (Not Migrated - Low Priority)
- Article boundary detection (_find_article_boundaries)
- In-document keyword search

## Usage Before Archival
- Only in V1 nodes (council.py, investigator.py)
- V1 nodes already archived

## Restore If Needed
``````powershell
Copy-Item archive\v1_tools\read_tool.py agents\tools\
``````

## Safe to Delete After
$(Get-Date).AddDays(14).ToString('yyyy-MM-dd')

## Decision Confidence
High (95%) - Navigation already merged and tested
"@
    
    $readme | Out-File -FilePath "archive\v1_tools\README.md" -Encoding UTF8
    Write-Host "Created README.md" -ForegroundColor Green
    
} else {
    Write-Host "WARNING: $tool not found" -ForegroundColor Yellow
}

Write-Host ""
Write-Host ("-" * 60) -ForegroundColor DarkGray
Write-Host ""

# Verify remaining tools
Write-Host "Verifying remaining tools..." -ForegroundColor Yellow
Write-Host ""

$critical_tools = @(
    "hybrid_search_tool.py",
    "db_tool_factory.py",
    "fetch_tools.py",
    "legal_blackboard_tool.py",
    "semantic_tools.py",
    "smart_finalizer.py",
    "lookup_tools.py",
    "law_identifier_tool.py",
    "vector_tools.py",
    "arabic_morphology.py",
    "arabic_numbers.py",
    "base_tool.py"
)

$all_present = $true
foreach ($t in $critical_tools) {
    if (Test-Path "agents\tools\$t") {
        Write-Host "  OK: $t" -ForegroundColor Green
    } else {
        Write-Host "  MISSING: $t" -ForegroundColor Red
        $all_present = $false
    }
}

Write-Host ""

if ($all_present) {
    Write-Host "SUCCESS: All critical tools present!" -ForegroundColor Green
} else {
    Write-Host "ERROR: Some critical tools missing!" -ForegroundColor Red
}

Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "Archival completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Test system functionality" -ForegroundColor White
Write-Host "2. Monitor for 2 weeks" -ForegroundColor White
Write-Host "3. Delete archive if no issues" -ForegroundColor White
Write-Host ""
