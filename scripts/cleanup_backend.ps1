# Backend Cleanup Script (PowerShell)
# Generated: 2026-01-23
# Purpose: Archive legacy files and delete dead code

Write-Host "🧹 Starting Backend Cleanup Operation..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Phase 1: Create Archive Directories
Write-Host ""
Write-Host "📁 Phase 1: Creating archive directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "agents\archive\orchestration" | Out-Null
New-Item -ItemType Directory -Force -Path "agents\archive\core" | Out-Null
New-Item -ItemType Directory -Force -Path "api\archive" | Out-Null
Write-Host "  ✅ Archive directories created" -ForegroundColor Green

# Phase 2: Archive Suspicious Files
Write-Host ""
Write-Host "📦 Phase 2: Archiving legacy files with valuable logic..." -ForegroundColor Yellow

# Archive orchestrator.py
if (Test-Path "agents\orchestration\orchestrator.py") {
    Write-Host "  ↪️  Moving orchestrator.py to archive..." -ForegroundColor White
    Move-Item -Path "agents\orchestration\orchestrator.py" -Destination "agents\archive\orchestration\" -Force
    Write-Host "    ✅ Archived (contains dependency resolution)" -ForegroundColor Green
}
else {
    Write-Host "  ⚠️  orchestrator.py not found (already archived?)" -ForegroundColor DarkYellow
}

# Archive enhanced_conduct_intake.py
if (Test-Path "agents\core\enhanced_conduct_intake.py") {
    Write-Host "  ↪️  Moving enhanced_conduct_intake.py to archive..." -ForegroundColor White
    Move-Item -Path "agents\core\enhanced_conduct_intake.py" -Destination "agents\archive\core\" -Force
    Write-Host "    ✅ Archived (contains context tracking)" -ForegroundColor Green
}
else {
    Write-Host "  ⚠️  enhanced_conduct_intake.py not found (already archived?)" -ForegroundColor DarkYellow
}

# Phase 3: Delete Dead Files
Write-Host ""
Write-Host "🗑️  Phase 3: Deleting confirmed dead files..." -ForegroundColor Yellow

# Delete chat_session.py
if (Test-Path "api\chat_session.py") {
    Write-Host "  🔴 Deleting chat_session.py (confirmed empty)..." -ForegroundColor Red
    Remove-Item -Path "api\chat_session.py" -Force
    Write-Host "    ✅ Deleted" -ForegroundColor Green
}
else {
    Write-Host "  ⚠️  chat_session.py not found (already deleted?)" -ForegroundColor DarkYellow
}

# Delete ai_helper.py (ONLY AFTER extracting logic)
$intentClassifierExists = Test-Path "api\utils\intent_classifier.py"
$aiHelperExists = Test-Path "api\ai_helper.py"

if ($intentClassifierExists -and $aiHelperExists) {
    Write-Host "  🔴 Deleting ai_helper.py (logic extracted to intent_classifier.py)..." -ForegroundColor Red
    Move-Item -Path "api\ai_helper.py" -Destination "api\archive\ai_helper.py.bak" -Force
    Write-Host "    ✅ Backed up to api\archive\ai_helper.py.bak" -ForegroundColor Green
}
elseif (-not $intentClassifierExists) {
    Write-Host "  ❌ ERROR: intent_classifier.py not found!" -ForegroundColor Red
    Write-Host "  ⏸️  Skipping ai_helper.py deletion for safety" -ForegroundColor Yellow
}
else {
    Write-Host "  ⚠️  ai_helper.py not found (already deleted?)" -ForegroundColor DarkYellow
}

# Phase 4: Create Archive README
Write-Host ""
Write-Host "📝 Phase 4: Creating archive documentation..." -ForegroundColor Yellow

$readmeContent = @'
# Archived Legacy Files

This directory contains legacy files that were archived during the 2026-01-23 cleanup operation.

## Why Archive Instead of Delete?

These files contain valuable logic patterns that might be useful for future reference,
even though they are not actively used in the current system.

## Archived Files

### orchestration/orchestrator.py
- **Archive Date:** 2026-01-23
- **Reason:** Replaced by core/multi_agent_orchestrator.py for legal workflows
- **Valuable Logic:** 
  - Dependency resolution (_resolve_dependencies())
  - Generic task execution framework
  - Progress tracking with ProgressStreamer
- **Future Use:** May be useful for non-legal multi-step tasks

### core/enhanced_conduct_intake.py
- **Archive Date:** 2026-01-23
- **Reason:** Experimental function for enhanced chat flow
- **Valuable Logic:**
  - Session caching for user profiles
  - Entity tracking (remember_client, remember_case)
  - Context injection for pronoun resolution
  - Multi-step request detection
- **Future Use:** Can be integrated into graph_agent.py for better UX

## How to Restore

If you need to reference or restore any of this logic:

1. Review the archived file
2. Extract specific functions/classes
3. Integrate into the current architecture
4. Do NOT simply copy-paste - adapt to current patterns
'@

Set-Content -Path "agents\archive\README.md" -Value $readmeContent -Encoding UTF8
Write-Host "  ✅ Created agents\archive\README.md" -ForegroundColor Green

# Phase 5: Verification
Write-Host ""
Write-Host "✅ Phase 5: Cleanup Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Archived Files:" -ForegroundColor White
if (Test-Path "agents\archive") {
    Get-ChildItem -Path "agents\archive" -Recurse -File | ForEach-Object { 
        Write-Host "  📦 $($_.FullName)" -ForegroundColor DarkGray 
    }
}

Write-Host ""
Write-Host "Deleted Files:" -ForegroundColor White
Write-Host "  ✓ api\chat_session.py (deprecated)" -ForegroundColor Gray
Write-Host "  ✓ api\ai_helper.py (logic extracted)" -ForegroundColor Gray

Write-Host ""
Write-Host "New Files Created:" -ForegroundColor White
Write-Host "  ✓ api\utils\intent_classifier.py" -ForegroundColor Green
Write-Host "  ✓ agents\archive\README.md" -ForegroundColor Green

Write-Host ""
Write-Host "Updated Files:" -ForegroundColor White
Write-Host "  ✓ agents\config\settings.py (added local storage config)" -ForegroundColor Green
Write-Host "  ✓ agents\storage\case_storage.py (uses configurable paths)" -ForegroundColor Green
Write-Host "  ✓ agents\storage\task_storage.py (uses configurable paths)" -ForegroundColor Green
Write-Host "  ✓ api\main.py (removed ai_helper router)" -ForegroundColor Green
Write-Host "  ✓ api\routers\chat.py (removed ai_helper import)" -ForegroundColor Green

Write-Host ""
Write-Host "🎉 Backend cleanup operation completed successfully!" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Test the application: python -m uvicorn api.main:app --reload" -ForegroundColor White
Write-Host "  2. Verify no import errors" -ForegroundColor White
Write-Host "  3. Check that intent_classifier is working correctly" -ForegroundColor White
Write-Host "  4. Commit changes to git" -ForegroundColor White
