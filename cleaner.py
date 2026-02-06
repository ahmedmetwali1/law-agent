import os
import ast
import shutil
import sys
from pathlib import Path

# ================= إعدادات السكربت =================
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__)) # مسار المشروع الحالي
ENTRY_POINT = "main.py"  # اسم الملف الرئيسي الذي يبدأ منه المشروع
ARCHIVE_DIR = "archive_unused" # اسم مجلد الأرشيف
DRY_RUN = True  # اجعلها False عندما تكون مستعداً للنقل الفعلي (للتجربة أولاً)
# ===================================================

def get_imports(file_path):
    """
    يقرأ ملف بايثون ويستخرج جميع المكتبات المستوردة باستخدام AST
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=file_path)
    except SyntaxError:
        print(f"⚠️ خطأ في قراءة الملف (Syntax Error): {file_path}")
        return []
    except Exception as e:
        print(f"⚠️ تعذر قراءة الملف {file_path}: {e}")
        return []

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
                # معالجة الاستيراد النسبي مثل from .utils import x
            elif node.level > 0:
                # هذا يعني استيراد نسبي بدون اسم موديول صريح
                imports.append("." * node.level)
    return imports

def resolve_file(base_path, import_name):
    """
    يحاول إيجاد مسار الملف المحلي بناءً على اسم الاستيراد
    """
    # تحويل النقاط إلى مسارات (مثال: utils.helpers -> utils/helpers)
    parts = import_name.split('.')
    base_dir = os.path.dirname(base_path)
    
    candidates = [
        os.path.join(PROJECT_ROOT, *parts) + ".py",           # project/module.py
        os.path.join(PROJECT_ROOT, *parts, "__init__.py"),    # project/module/__init__.py
        os.path.join(base_dir, *parts) + ".py",               # relative/module.py
    ]

    for candidate in candidates:
        if os.path.exists(candidate) and os.path.isfile(candidate):
            return os.path.normpath(candidate)
    
    return None

def main():
    start_file = os.path.join(PROJECT_ROOT, ENTRY_POINT)
    
    if not os.path.exists(start_file):
        print(f"❌ الملف الرئيسي غير موجود: {start_file}")
        return

    print(f"🔍 جاري تحليل المشروع بدءاً من: {ENTRY_POINT}...")

    # 1. تتبع الملفات المستخدمة
    used_files = set()
    queue = [start_file]
    used_files.add(start_file)

    while queue:
        current_file = queue.pop(0)
        imports = get_imports(current_file)

        for imp in imports:
            resolved_path = resolve_file(current_file, imp)
            if resolved_path and resolved_path not in used_files:
                # تأكد أن الملف داخل مجلد المشروع وليس مكتبة خارجية
                if PROJECT_ROOT in resolved_path:
                    used_files.add(resolved_path)
                    queue.append(resolved_path)

    print(f"✅ تم اكتشاف {len(used_files)} ملف مرتبط بالمشروع.")

    # 2. حصر جميع ملفات البايثون في المشروع
    all_python_files = set()
    for root, dirs, files in os.walk(PROJECT_ROOT):
        # تجاهل مجلد الأرشيف والبيئات الافتراضية والمجلدات المخفية
        if ARCHIVE_DIR in root or "venv" in root or ".git" in root or "__pycache__" in root:
            continue
            
        for file in files:
            if file.endswith(".py") and file != os.path.basename(__file__): # تجاهل هذا السكربت نفسه
                full_path = os.path.join(root, file)
                all_python_files.add(full_path)

    # 3. تحديد الملفات غير المستخدمة
    unused_files = all_python_files - used_files

    print(f"⚠️ تم العثور على {len(unused_files)} ملف غير مستخدم.")

    if not unused_files:
        print("🎉 مشروعك نظيف! لا توجد ملفات غير مرتبطة.")
        return

    # 4. نقل الملفات
    archive_path = os.path.join(PROJECT_ROOT, ARCHIVE_DIR)
    if not os.path.exists(archive_path) and not DRY_RUN:
        os.makedirs(archive_path)

    print("\n📦 تفاصيل العملية:")
    for file_path in unused_files:
        relative_path = os.path.relpath(file_path, PROJECT_ROOT)
        dest_path = os.path.join(archive_path, relative_path)
        
        print(f" -> نقل: {relative_path}")
        
        if not DRY_RUN:
            # إنشاء المجلدات الفرعية داخل الأرشيف للحفاظ على الهيكلية
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            shutil.move(file_path, dest_path)

    if DRY_RUN:
        print("\n🛑 وضع التجربة (DRY RUN): لم يتم نقل أي ملف.")
        print("💡 لتنفيذ النقل فعلياً، قم بتغيير المتغير 'DRY_RUN' إلى False في بداية السكربت.")
    else:
        print(f"\n✅ تم نقل الملفات بنجاح إلى مجلد: {ARCHIVE_DIR}")

if __name__ == "__main__":
    main()