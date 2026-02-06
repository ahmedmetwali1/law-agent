# Knowledge Base Architecture: The Sequential Layer Model

## 1. Core Structure
The system does not strictly separate "Articles" into individual rows. Instead, it simulates a **Book** structure.

### **Level 1: The Source (The Book)**
*   **Table:** `legal_sources`
*   **Schema:** `id, country_id, title, doc_type, full_content_md, total_word_count, drive_link, is_enriched, metadata, created_at, updated_at, drive_file_id`
*   **Purpose:** The single source of truth containing the full text.

### **Level 2: The Chunks (The Pages)**
*   **Table:** `document_chunks`
*   **Relation:** Many-to-One with `legal_sources` (`source_id`).
*   **Schema:** `id, source_id, content, embedding, sequence_number, hierarchy_path, chunk_word_count, status, ai_summary, legal_logic, legal_strength, keywords, fts_tokens, created_at, retry_count, locked_at, last_error, processed_at, extracted_principles, legal_domain, country_id`
*   **Key Concept:** `sequence_number` determines the page order.
*   **Logic:**
    *   If "Article 7" is in **Chunk 5**...
    *   **Chunk 4** contains the preceding context (definitions/preamble).
    *   **Chunk 6** contains the following context (exceptions/penalties).

### **Level 3: The Templates (The Universal Constants)**
*   **Table:** `thought_templates`
*   **Schema:** `id, template_text, template_embedding, occurrence_count, confidence_score, domain_tag, source_doc_ids, created_at, updated_at, source_chunk_ids, principle_type, is_absolute, exceptions, related_templates, keywords`
*   **Purpose:** Universal legal principles (e.g., "Pacta Sunt Servanda") applicable across jurisdictions.

## 2. Retrieval Strategy (The "Reader" Logic)

### **The Problem:**
Searching for "Article 7" gives a single chunk. Legal understanding requires the *context* (exceptions often come in the next article).

### **The Solution (Agents MUST use this):**
1.  **Hit:** Agent finds **Chunk X** containing the keyword.
2.  **Expand:** Agent calls `GetRelatedDocumentTool(chunk_id=X, include_siblings=True)`.
3.  **Read:** System returns **[Chunk X-1, Chunk X, Chunk X+1]**.
4.  **Understand:** Agent reads the full sequence to capture definitions and exceptions.

## 3. Implications for Tools
*   **StatuteLinkingTool:** Instead of looking for a row "Article 7", it searches for the text "Article 7" in chunks, then *must* fetch the context to ensure it didn't miss a sub-clause split across chunks.
