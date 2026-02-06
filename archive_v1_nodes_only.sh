#!/bin/bash
# Bash Script لأرشفة الوكلاء V1 فقط (لأنظمة Linux/Mac)

echo ""
echo "🗂️  أرشفة الوكلاء V1"
echo "============================================================"
echo ""

# التحقق من المسار
if [ ! -d "agents/graph/nodes" ]; then
    echo "❌ خطأ: المجلد agents/graph/nodes غير موجود!"
    echo "   تأكد من تشغيل السكريبت من مجلد المشروع الرئيسي"
    exit 1
fi

# 1. إنشاء مجلد الأرشيف
echo "📁 إنشاء مجلد الأرشيف..."

mkdir -p archive/v1_nodes
echo "   ✓ تم إنشاء archive/v1_nodes/"
echo ""

# 2. قائمة الوكلاء القدامى
declare -a v1_nodes=(
    "council.py"
    "drafter.py"
    "investigator.py"
    "research.py"
    "general.py"
    "reviewer.py"
    "router.py"
)

echo "📦 نقل الوكلاء V1 إلى الأرشيف..."
echo ""

moved_count=0
not_found_count=0

for node in "${v1_nodes[@]}"; do
    source_path="agents/graph/nodes/$node"
    dest_path="archive/v1_nodes/$node"
    
    if [ -f "$source_path" ]; then
        mv "$source_path" "$dest_path"
        echo "   ✓ $node"
        ((moved_count++))
    else
        echo "   ⚠ $node (غير موجود)"
        ((not_found_count++))
    fi
done

echo ""
echo "────────────────────────────────────────────────────────────"
echo ""

# 3. ملخص النتائج
echo "📊 ملخص العملية:"
echo "   • تم نقل: $moved_count ملفات"
if [ $not_found_count -gt 0 ]; then
    echo "   • غير موجود: $not_found_count ملفات"
fi

echo ""

# 4. عرض محتويات الأرشيف
echo "📂 محتويات الأرشيف:"
ls -lh archive/v1_nodes/ | tail -n +2 | awk '{print "   • " $9 " (" $5 ")"}'

echo ""
echo "────────────────────────────────────────────────────────────"
echo ""

# 5. إنشاء README
cat > archive/v1_nodes/README.md << 'EOF'
# V1 Nodes Archive

## تاريخ الأرشفة
$(date '+%Y-%m-%d %H:%M:%S')

## الملفات المُؤرشفة
- council.py
- drafter.py
- investigator.py
- research.py
- general.py
- reviewer.py
- router.py

## السبب
تم استبدال هذه الوكلاء بنسخة V2 محسّنة

## الاسترجاع
```bash
cp archive/v1_nodes/council.py agents/graph/nodes/
```

## الحذف النهائي (بعد أسبوعين)
```bash
rm -rf archive/v1_nodes
```
EOF

echo "📝 تم إنشاء README.md في الأرشيف"
echo ""

# 6. التحقق من النظام
echo "🔍 التحقق من سلامة النظام..."
echo ""

declare -a v2_nodes=(
    "council_v2.py"
    "drafter_v2.py"
    "deep_research.py"
    "judge.py"
    "gatekeeper.py"
)

all_v2_exist=true
for node in "${v2_nodes[@]}"; do
    if [ -f "agents/graph/nodes/$node" ]; then
        echo "   ✓ $node موجود"
    else
        echo "   ✗ $node مفقود!"
        all_v2_exist=false
    fi
done

echo ""

if [ "$all_v2_exist" = true ]; then
    echo "✅ جميع الوكلاء النشطة (V2) موجودة وسليمة!"
else
    echo "⚠️  تحذير: بعض الوكلاء V2 مفقودة!"
fi

echo ""
echo "============================================================"
echo "✅ اكتملت عملية الأرشفة بنجاح!"
echo ""
