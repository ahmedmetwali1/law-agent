-- =========================================================
-- 🧪 TEST: Pure Text Search for "Article 368" (No Digit Fallback)
-- =========================================================
-- Goal: Verify that searching for "Three Hundred AND Sixty Eight" (Text)
-- finds the correct article definition, relying entirely on:
-- 1. Exact Phrase Match (+3.0) -> Because match is in the HEADER (first 200 chars).
-- 2. Semantic Match (+0.8) -> Because 'semantic_query' contains text parts.
-- 3. NOT relying on "Digit Match" (since input is text and DB content is text).
-- =========================================================

-- 1. Run the Query
SELECT 
  id, 
  source_title, 
  -- ✅ SMART PREVIEW: Show the text AROUND the match, not just the beginning of the file.
  -- This proves we found "Article 368" even if the file starts with "Article 359".
  substring(
    content 
    from position(normalize_arabic('المادة الثامنة والستون بعد الثلاثمائة') in normalize_arabic(content)) 
    for 150
  ) as smart_snippet,
  similarity_score,
  debug_info
FROM check_text_existence(
  -- 1. The User's Query (EXACT HEADER provided by User)
  query_text => 'المادة الثامنة والستون بعد الثلاثمائة', 
  
  -- 2. Threshold (Standard)
  match_threshold => 0.4, 
  
  -- 3. Country
  filter_country_id => '61a2dd4b-cf18-4d88-b210-4d3687701b01'::uuid, 
  
  -- 4. Semantic Query (Keywords from the Body text provided by User)
  -- "إذا كان الموهوب عقارًا... منقولًا... توثيق"
  semantic_query => 'هبة | عقار | منقول | توثيق | النصوص | النظامية', 
  
  -- 5. Quality Gate
  min_return_score => 0.75 
);
