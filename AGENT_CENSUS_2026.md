# AGENT CENSUS & CAPABILITY DOSSIER (2026)

**System Version:** Hybrid Architecture v2.0
**Context:** Full Audit of Intelligent Entities
**Date:** 2026-01-31

---

## 1. The Agent Census (Inventory)

**Total Count:** 9 Active Nodes

1.  **Grade A (Orchestrators):**
    *   `judge_node` (The Chief Justice) - *Router/Decision Maker*
    *   `gatekeeper_node` (The Clerk) - *First Line Defense*
2.  **Grade B (Specialists):**
    *   `council_node` (The Consultants) - *Multi-Persona Reasoning*
    *   `deep_research_node` (The Scout) - *Information Retrieval*
    *   `fast_track_node` (The Greeter) - *Simple Interactions*
3.  **Grade C (Admin Subgraph):**
    *   `action_node` (The Manager) - *Plan Execution Strategy*
    *   `execute_node` (The Worker) - *Tool Runner*
    *   `synthesize_node` (The Reporter) - *Output Formatter*
    *   `admin_ops_node` (The Interface) - *Entry/Exit Wrapper*

---

## 2. The Legal Branch (The Lawyers & Judges)

### A. The Chief Justice (`judge_node`)
*   **Mission:** To orchestrate the entire legal conversation. It acts as the "Brain", classifying intent (Analyst), planning strategy (Strategist), and synthesizing the final response (Speaker).
*   **Methodology:** 4-Layer Architecture (Analyst -> Strategist -> Executor -> Speaker). It is the only node with "Executive Power" to route to other agents.
*   **System Prompt:**
    > "You are the Chief Justice Node (4-Layer 🧠 Architecture). 1. Analyst: Classify Intent. 2. Strategist: Plan & Route. 3. Executor: Prepare State. 4. Speaker: Diplomatic Response."
*   **Tools:** None (Pure Reasoning). Routes to `deep_research` or `admin_ops` for tools.

### B. The Council (`council_node`)
*   **Mission:** To provide diverse legal perspectives. It simulates a "Blackboard" discussion between 4 personas (e.g., Devil's Advocate, Strategist).
*   **Methodology:** Parallel Reasoning. It specifically avoids tools in favor of pure deliberation based on facts provided by the Researcher.
*   **System Prompt:** Extracted from `CONSULTANT_PROMPTS` (Dynamic).
*   **Interaction:** Receives `research_results`. Outputs `council_opinions` (Dict of Monologue/Public Opinion).

### C. The Researcher (`deep_research_node`)
*   **Mission:** To find "ground truth" in the database. It converts user queries into semantic search vectors and SQL queries.
*   **Methodology:** Retrieval Augmented Generation (RAG). It expands context by reading "neighboring chunks" of documents.
*   **System Prompt:** 
    > "أنت خبير البحث القانوني الأول. مهمتك هي صياغة كلمات بحث دلالية قوية... استخراج القوانين والسوابق القضائية..."
*   **Tools:**
    *   `HybridSearchTool` (Vector + Keyword)
    *   `StatuteLinkingTool` (Legislation)
    *   `GetRelatedDocumentTool` (Context Expansion)

---

## 3. The Administrative Branch (The Office Managers)

### A. The Gatekeeper (`gatekeeper_node`)
*   **Mission:** Cost Control. Captures "Greeting" and "Trivial" inputs before they reach the expensive Judge.
*   **Methodology:** Deterministic Regex & Rules (System 0). Zero Token Cost.
*   **Logic:** `if input matches GREETING_PATTERNS -> Fast Track`.

### B. The Admin Manager (`action_node` inside `admin_ops`)
*   **Mission:** To manipulate the database safely. It handles `CRUD` operations for Clients, Cases, and Tasks.
*   **Methodology:** Fused "Extract -> Plan" Logic. It maps user requests directly to tool calls.
*   **System Prompt:**
    > "You are an expert Admin Agent... Select the best tool(s)... OUTPUT MUST BE A RAW JSON list... STRICT DATA ADHERENCE."
*   **Interaction Style:** Robotic/Efficiency-First.
*   **Tools (Dynamic Generator):**
    *   `query_*` (Read Only)
    *   `insert_*` (Create)
    *   `update_*` (Modify)
    *   `delete_*` (Destructive - Guarded)

### C. The Admin Reporter (`synthesize_node`)
*   **Mission:** To translate raw JSON tool outputs into a friendly Arabic response ("Saug Flavor").
*   **Methodology:** Hallucination Guardrails. It is forbidden from inventing data not present in the tool output.

---

## 4. The Interaction Flow

### Legal Flow (The Brain)
1.  **Judge (Analyst)** receives query.
2.  If information is missing -> Routes to **Researcher**.
3.  **Researcher** gathers facts -> Routes to **Council**.
4.  **Council** debates facts -> Returns opinions to **Judge**.
5.  **Judge (Verdict)** synthesizes opinions -> Delivers final answer.

### Admin Flow (The Hands)
1.  **Gatekeeper** -> **Judge (Analyst)** detects `ADMIN_ACTION`.
2.  Judge Routes to **Admin Ops**.
3.  **Admin Ops (Action)** plans tool calls.
4.  **Admin Ops (Execute)** runs SQL.
5.  **Admin Ops (Synthesize)** formats output.
6.  **Admin Ops** returns text to Judge.
7.  **Judge** relays text to User.

---

## 5. The Tool Separation (Security Matrix)

| ecosystem | Toolset | Access Policy |
| :--- | :--- | :--- |
| **LEGAL** | `HybridSearch`, `StatuteLink`, `GetDocument` | **Read Only**. Can see all Laws/Precedents. Cannot see Client Data. |
| **ADMIN** | `DatabaseToolGenerator` (`query`, `insert`, `update`, `delete`) | **Read/Write**. Can see Client Data. Cannot use Legal Search tools (Separation of Concerns). |
| **SHARED** | `ReadDocumentTool` (Maybe?) | **Risk:** None currently. Separation is strict. |

**Observation:** The separation is robust. The Legal Brain cannot accidentally delete a client, and the Admin Brain cannot hallucinate a law.

---
**Status:** COMPLETE inventory of active intelligence.
