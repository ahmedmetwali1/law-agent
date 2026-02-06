"""
🔍 تشخيص نهائي: لماذا Score = 0؟
"""
import sys
sys.path.append('e:/law')

import asyncio
from agents.config.database import db


async def diagnose():
    """فحص مباشر"""
    
    print("=" * 100)
    print("🔍 التشخيص النهائي")
    print("=" * 100)
    
    # Test 1: SQL ILIKE مباشر
    print("\n[1] اختبار SQL ILIKE:")
    
    variants = ['الهبة', 'الهبه', 'هبة', 'هبه']
    
    try:
        or_conditions = ','.join([f"content.ilike.%{v}%" for v in variants])
        
        result = db.client.table('document_chunks') \
            .select('id, content, source_id, sequence_number') \
            .or_(or_conditions) \
            .limit(10) \
            .execute()
        
        print(f"  ✅ وجدنا {len(result.data)} نتيجة")
        
        for i, doc in enumerate(result.data[:3], 1):
            content = doc.get('content', '')
            print(f"\n  [{i}] {content[:200]}...")
            
            # Count occurrences
            count = sum(content.lower().count(v.lower()) for v in variants)
            print(f"      التكرار: {count}")
        
        return result.data
        
    except Exception as e:
        print(f"  ❌ خطأ: {e}")
        return []


if __name__ == "__main__":
    asyncio.run(diagnose())
