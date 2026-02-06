# Marid V2.0: Legal Intelligence System

Marid is a **LangGraph-driven Multi-Agent System** engineered for the legal domain. It combines Retrieval-Augmented Generation (RAG) with a rigorous "Honor Constraint Framework" (HCF) to ensure high-fidelity legal reasoning, citation accuracy, and transparent deliberation.

---

## 🏗️ Architecture: The "Legal Blackboard"

Marid operates on a stateful, graph-based architecture where specialized agents collaborate around a shared memory structure called the **Legal Blackboard**.

### **Core Components**
*   **Legal Blackboard (Postgres):** The definitive "Source of Truth". A versioned state machine that stores:
    *   `facts_snapshot`: Verified case facts extracted by the Investigator.
    *   `research_data`: Raw legal texts and citations found by the Researcher.
    *   `council_monologues`: Real-time strategic debates between internal agents.
    *   `hcf_decisions`: Verification status of every legal claim (Source vs. Analogy).
*   **LangGraph Orchestrator:** Manages the non-linear flow between agents (Investigator -> Researcher -> Council -> Draft).
*   **Context Enrichment Layer:** A middleware that resolves ambiguous queries (e.g., "in the second article") by injecting entity-rich context from conversation history before search execution.

---

## 🛡️ The Honor Constraint Framework (HCF)

Marid distinguishes itself through **HCF**, a protocol that enforces "Digital Honor" in legal citations.

### **Mechanism**
1.  **Phase 1: Divergent Search:** The Researcher agent casts a wide net using `HybridSearchV3` (Vector + Keyword + Trigram).
2.  **Phase 2: Strict Verification:**
    *   **Direct Match:** If an exact article text is found, it is flagged as `VERIFIED_SOURCE`.
    *   **Analogical Reasoning:** If no text exists, the agent must explictly declare it as `VERIFIED_ANALOGY` (Qi'yas) or `STRATEGIC_ESTIMATION`.
    *   **Hallucination Block:** Any claim not supported by the retrieved context is rejected.
3.  **Phase 3: The Deliberation Room:** A UI-visible layer where the "Council" agents (Legislator, Strategist, Devils' Advocate) debate the findings in real-time.

---

## ⚙️ Tech Stack & Protocols

| Component | Technology | Rationale |
| :--- | :--- | :--- |
| **Backend** | Python 3.10+, FastAPI | Native support for LangChain & async processing. |
| **Orchestration** | LangGraph | Stateful, cyclic agent workflows (unlike linear Chains). |
| **Persistence** | PostgreSQL + Supabase | Row-Level Security (RLS) & JSONB for flexible state. |
| **Streaming** | Server-Sent Events (SSE) | Real-time token streaming + custom "Council" events. |
| **Search** | Hybrid (pgvector + BM25) | High-recall legal retrieval (Semantic + Term-based). |
| **Frontend** | React 18, Zustand, Tailwind | High-performance, identifying "Active Thinking" states. |

---

## 🚀 Setup & Local Deployment

### **1. Environment Configuration**
Ensure `.env` contains the following critical keys:
```bash
SUPABASE_URL=...
SUPABASE_KEY=...
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=... # For Council Agents (OPUS/SONNET)
LOG_LEVEL=INFO
```

### **2. Database Migrations**
Initialize the `legal_blackboard` and `hcf_logs` tables:
```bash
python migrations/run_migrations.py
```

### **3. Backend Service**
Launch the API server with auto-reload:
```bash
cd e:\law
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### **4. Frontend Interface**
Start the Vite development server:
```bash
cd frontend
npm install
npm run dev
```

---

## 📡 API Streaming Protocol (The "Viva" Protocol)

The frontend consumes a unified SSE stream that multiplexes multiple event types:
- `token`: Standard LLM text chunks.
- `step_update`: Agent state transitions (e.g., "Investigating -> Deliberating").
- `reasoning_chunk`: Raw thought process from the Judge or Council (Private/Public).
- `hcf_decision`: Structured JSON payload containing verification metadata.

---

**© 2026 Marid AI Systems. Proprietary & Confidential.**
