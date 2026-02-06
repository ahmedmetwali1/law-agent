"""
🔍 فحص: هل هناك نتائج مفقودة؟
"""
import sys
sys.path.append('e:/law')

import asyncio
from agents.config.database import db


async def check_all_results():
    """فحص كل النتائج الموجودة"""
    
    print("=" * 100)
    print("🔍 فحص النتائج الكاملة عن 'الهبة'")
    print("=" * 100)
    
    variants = ['الهبة', 'الهبه', 'هبة', 'هبه']
    
    try:
        or_conditions = ','.join([f"content.ilike.%{v}%" for v in variants])
        
        result = db.client.table('document_chunks') \
            .select('id, content, source_id, sequence_number, hierarchy_path') \
            .or_(or_conditions) \
            .limit(100) \
            .execute()
        
        print(f"\n✅ إجمالي النتائج: {len(result.data)}")
        
        # جلب معلومات المصادر
        source_ids = list(set([d.get('source_id') for d in result.data]))
        
        sources = db.client.table('legal_sources') \
            .select('id, title') \
            .in_('id', source_ids) \
            .execute()
        
        sources_map = {s['id']: s['title'] for s in sources.data}
        
        # تجميع حسب المصدر
        by_source = {}
        for doc in result.data:
            sid = doc.get('source_id')
            title = sources_map.get(sid, 'غير معروف')
            if title not in by_source:
                by_source[title] = []
            by_source[title].append(doc)
        
        # عرض
        print(f"\n📚 توزيع النتائج حسب المصدر:")
        for title, docs in sorted(by_source.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"\n  [{len(docs)}] {title}")
            for i, doc in enumerate(docs[:3], 1):
                print(f"     {i}. {doc['content'][:100]}...")
        
        # التركيز على نظام المعاملات المدنية
        civil_docs = [docs for title, docs in by_source.items() if 'المعاملات المدنية' in title]
        if civil_docs:
            print(f"\n\n🎯 نظام المعاملات المدنية: {len(civil_docs[0])} مواد")
            for i, doc in enumerate(civil_docs[0], 1):
                print(f"\n  [{i}] Seq: {doc.get('sequence_number')}")
                print(f"      {doc['content'][:150]}...")
        
    except Exception as e:
        print(f"❌ خطأ: {e}")


if __name__ == "__main__":
    asyncio.run(check_all_results())
