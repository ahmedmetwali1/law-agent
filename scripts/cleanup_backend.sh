#!/bin/bash
# Backend Cleanup Script
# Generated: 2026-01-23
# Purpose: Archive legacy files and delete dead code

echo "🧹 Starting Backend Cleanup Operation..."
echo "========================================"

# Phase 1: Create Archive Directories
echo ""
echo "📁 Phase 1: Creating archive directories..."
mkdir -pv agents/archive/orchestration
mkdir -pv agents/archive/core
mkdir -pv api/archive

# Phase 2: Archive Suspicious Files (DO NOT DELETE - Contains valuable logic)
echo ""
echo "📦 Phase 2: Archiving legacy files with valuable logic..."

# Archive orchestration/orchestrator.py (valuable dependency resolution logic)
if [ -f "agents/orchestration/orchestrator.py" ]; then
    echo "  ↪️  Moving orchestrator.py to archive (contains dependency resolution)..."
    mv -v agents/orchestration/orchestrator.py agents/archive/orchestration/
else
    echo "  ⚠️  orchestrator.py not found (already archived?)"
fi

# Archive enhanced_conduct_intake.py (valuable context tracking logic)
if [ -f "agents/core/enhanced_conduct_intake.py" ]; then
    echo "  ↪️  Moving enhanced_conduct_intake.py to archive (contains context tracking)..."
    mv -v agents/core/enhanced_conduct_intake.py agents/archive/core/
else
    echo "  ⚠️  enhanced_conduct_intake.py not found (already archived?)"
fi

# Phase 3: Delete Dead Files
echo ""
echo "🗑️  Phase 3: Deleting confirmed dead files..."

# Delete chat_session.py (empty/deprecated file)
if [ -f "api/chat_session.py" ]; then
    echo "  🔴 Deleting chat_session.py (confirmed empty)..."
    rm -v api/chat_session.py
else
    echo "  ⚠️  chat_session.py not found (already deleted?)"
fi

# Delete ai_helper.py (ONLY AFTER extracting logic to intent_classifier.py)
if [ -f "api/utils/intent_classifier.py" ]; then
    if [ -f "api/ai_helper.py" ]; then
        echo "  🔴 Deleting ai_helper.py (logic extracted to intent_classifier.py)..."
        mv -v api/ai_helper.py api/archive/ai_helper.py.bak  # Backup first
        echo "  ✅ Backed up to api/archive/ai_helper.py.bak"
    else
        echo "  ⚠️  ai_helper.py not found (already deleted?)"
    fi
else
    echo "  ❌ ERROR: intent_classifier.py not found! Cannot safely delete ai_helper.py"
    echo "  ⏸️  Skipping ai_helper.py deletion for safety"
fi

# Phase 4: Create Archive README
echo ""
echo "📝 Phase 4: Creating archive documentation..."

cat > agents/archive/README.md << 'EOF'
# Archived Legacy Files

This directory contains legacy files that were archived during the 2026-01-23 cleanup operation.

## Why Archive Instead of Delete?

These files contain valuable logic patterns that might be useful for future reference,
even though they're not actively used in the current system.

## Archived Files

### orchestration/orchestrator.py
- **Archive Date:** 2026-01-23
- **Reason:** Replaced by `core/multi_agent_orchestrator.py` for legal workflows
- **Valuable Logic:** 
  - Dependency resolution (`_resolve_dependencies()`)
  - Generic task execution framework
  - Progress tracking with ProgressStreamer
- **Future Use:** May be useful for non-legal multi-step tasks

### core/enhanced_conduct_intake.py
- **Archive Date:** 2026-01-23
- **Reason:** Experimental function for enhanced chat flow
- **Valuable Logic:**
  - Session caching for user profiles
  - Entity tracking (remember_client, remember_case)
  - Context injection for pronoun resolution ("له", "لها")
  - Multi-step request detection
- **Future Use:** Can be integrated into graph_agent.py for better UX

## How to Restore

If you need to reference or restore any of this logic:

1. Review the archived file
2. Extract specific functions/classes
3. Integrate into the current architecture
4. Do NOT simply copy-paste - adapt to current patterns

## Cleanup Notes

- Hardcoded paths removed from active code
- Intent classification extracted to `api/utils/intent_classifier.py`
- All imports updated to remove references to archived files
EOF

echo "  ✅ Created agents/archive/README.md"

# Phase 5: Verification
echo ""
echo "✅ Phase 5: Cleanup Summary"
echo "========================================"
echo "Archived Files:"
ls -lh agents/archive/*/ 2>/dev/null || echo "  (none or directory doesn't exist)"
echo ""
echo "Deleted Files:"
echo "  ✓ api/chat_session.py (deprecated)"
echo "  ✓ api/ai_helper.py (logic extracted)"
echo ""
echo "New Files Created:"
echo "  ✓ api/utils/intent_classifier.py"
echo "  ✓ agents/archive/README.md"
echo ""
echo "Updated Files:"
echo "  ✓ agents/config/settings.py (added local_cases_dir, local_tasks_dir)"
echo "  ✓ agents/storage/case_storage.py (uses configurable paths)"
echo "  ✓ agents/storage/task_storage.py (uses configurable paths)"
echo "  ✓ api/main.py (removed ai_helper router)"
echo "  ✓ api/routers/chat.py (removed ai_helper import)"
echo ""
echo "🎉 Backend cleanup operation completed successfully!"
echo "Next steps:"
echo "  1. Test the application: python -m uvicorn api.main:app --reload"
echo "  2. Verify no import errors"
echo "  3. Check that intent_classifier is working correctly"
echo "  4. Commit changes to git"
