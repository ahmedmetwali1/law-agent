"""
Test Multi-Country Support in semantic_tools.py
Tests generic pattern extraction for Egyptian and Saudi legal text
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.tools.semantic_tools import LegalEntityExtractorTool

# Initialize tool
extractor = LegalEntityExtractorTool()

print("=" * 60)
print("🌍 Multi-Country Entity Extraction Test")
print("=" * 60)
print()

# ========================================
# Test 1: Egyptian Text 🇪🇬
# ========================================
print("📋 Test 1: Egyptian Legal Text")
print("-" * 60)

egyptian_text = """
قضت محكمة النقض المصرية في الدعوى رقم 123 لسنة 2024
بإلغاء الحكم الصادر من محكمة استئناف القاهرة.
استنادًا إلى المادة 368 من القانون المدني المصري.
الموكل ضد المدعى عليه في قضية التعويض.
"""

result = extractor.run(egyptian_text)

if result.success:
    print("✅ Extraction successful!")
    print(f"\nCourts found: {len(result.data['courts'])}")
    for court in result.data['courts']:
        print(f"  - {court['text']} (type: {court['type']})")
    
    print(f"\nLaws/Articles found: {len(result.data['laws'])}")
    for law in result.data['laws'][:3]:
        if 'number' in law:
            print(f"  - Article {law.get('number', 'N/A')}")
        else:
            print(f"  - {law.get('name', 'N/A')}")
    
    print(f"\nPersons found: {len(result.data['persons'])}")
    for person in result.data['persons']:
        print(f"  - {person.get('name', 'N/A')} ({person['role']})")
else:
    print(f"❌ Extraction failed: {result.error}")

print()

# ========================================
# Test 2: Saudi Text 🇸🇦
# ========================================
print("📋 Test 2: Saudi Legal Text")
print("-" * 60)

saudi_text = """
حكمت المحكمة العليا في القضية رقم 456 لسنة 1445هـ
بتأييد حكم محكمة الاستئناف بجدة.
وفقًا لأحكام المادة 77 من نظام المعاملات المدنية.
المدعي ضد المدعى عليه في النزاع التجاري.
"""

result = extractor.run(saudi_text)

if result.success:
    print("✅ Extraction successful!")
    print(f"\nCourts found: {len(result.data['courts'])}")
    for court in result.data['courts']:
        print(f"  - {court['text']} (type: {court['type']})")
    
    print(f"\nLaws/Articles found: {len(result.data['laws'])}")
    for law in result.data['laws'][:3]:
        if 'number' in law:
            print(f"  - Article {law.get('number', 'N/A')}")
        else:
            print(f"  - {law.get('name', 'N/A')}")
    
    print(f"\nPersons found: {len(result.data['persons'])}")
    for person in result.data['persons']:
        print(f"  - {person.get('name', 'N/A')} ({person['role']})")
else:
    print(f"❌ Extraction failed: {result.error}")

print()
print("=" * 60)
print("✅ Multi-Country Test Complete!")
print("=" * 60)
