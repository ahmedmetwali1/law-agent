# Marid: Professional Legal AI Multi-Agent System ⚖️🤖

**Marid** is a state-of-the-art, high-performance legal office management and AI advisory platform. Designed for modern law firms, it orchestrates a complex network of specialized AI agents to handle everything from administrative tasks to deep legal research and document drafting.

---

## 🛠️ Core Technology Stack

### **Frontend (The Interface of Intelligence)**
- **Framework:** React 18 (Vite-powered)
- **Language:** TypeScript (Strict Type Safety)
- **UI Architecture:** 
  - **Tailwind CSS** for modern, responsive aesthetics.
  - **Radix UI Primitives** for accessible, premium components.
  - **Lucide React** for consistent iconography.
- **State & Data:**
  - **Zustand** for lightweight, high-performance global state.
  - **TanStack Query (React Query)** for robust server-state management and caching.
- **Communication:** Axios & Supabase JS Client.

### **Backend (The Cognitive Engine)**
- **Framework:** FastAPI (Python 3.10+)
- **Agent Orchestration:** **LangGraph** (Stateful Multi-Agent Workflows).
- **Core AI Integration:** LangChain, OpenAI, Anthropic, and Google Gemini.
- **Data Validation:** Pydantic v2.
- **Caching:** Redis-ready for high-scale performance.
- **Real-time:** WebSockets for agent perception and live updates.

### **Infrastructure & Database**
- **Persistence:** PostgreSQL (via Supabase).
- **Security:** Supabase Auth (JWT) + custom RBAC (Role-Based Access Control).
- **Storage:** S3-compatible cloud storage and local encrypted backups.
- **Search:** Hybrid Search (Vector + Full-Text) for precision legal retrieval.

---

## 🏗️ Architectural Overview: The Agent Graph

Marid utilizes a non-linear, graph-based architecture using **LangGraph**. Unlike simple chatbots, Marid transitions through cognitive states based on the complexity of the legal query.

### **The Cognitive Workflow**
1.  **Gatekeeper Node:** Analyzes user intent and classifies the query (Administrative vs. Legal).
2.  **Stateless Router:** Dispatches tasks to specialized agent clusters.
3.  **Specialized Agent Nodes:**
    - **ResearchNode:** Performs deep-dive legal lookups in the knowledge base.
    - **CouncilNode:** Aggregates legal opinions and performs multi-step reasoning.
    - **DraftNode:** Generates professional legal documents from templates or research.
    - **AdminOpsNode:** Interacts with the office database (Clients, Cases, Hearings).
4.  **Reflector / Reviewer:** Self-corrects and verifies the output for legal accuracy before finalization.

---

## 📁 System Blueprint

```text
e:\law
├── agents/             # The "Brain" of the system
│   ├── graph/          # LangGraph definitions (nodes, state, subgraphs)
│   ├── persistence/    # Postgres & Supabase persistence layers
│   ├── tools/          # Custom-built tools (Hybrid Search, Legal Blackboard)
│   └── prompts/        # Centralized system prompts & templates
├── api/                # The "Central Nervous System"
│   ├── main.py         # Entry point & router registration
│   ├── services/       # Business logic (Chat, Admin, Deliberation)
│   └── routers/        # Modular API endpoints
├── frontend/           # The "Sense" (UI/UX)
│   ├── src/api/        # BFF (Backend-for-Frontend) integration
│   ├── src/components/ # Modular, reusable shadcn-inspired components
│   └── src/stores/     # Zustand stores for real-time UI state
└── migrations/         # Database evolution & SQL schemas
```

---

## 🚀 Professional Setup & Deployment

### **Prerequisites**
- **Node.js** v18+ & **pnpm** (Recommended)
- **Python** 3.10+
- **Supabase Account** with PostgreSQL & Vector Extension.
- **Environment Variables:** Configure `.env` based on the internal security protocol.

### **Backend Initialization**
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Run migrations
python migrations/run_migrations.py

# Launch API
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### **Frontend Initialization**
```bash
cd frontend
npm install
npm run dev
```

---

## ⚖️ Security & Data Governance

- **Zero Trust:** All Backend requests are validated via JWT tokens.
- **RLS (Row Level Security):** Data is isolated at the database level using Supabase RLS policies.
- **Audit Logging:** Every administrative action is logged in a secure, non-erasable audit trail.
- **Sanitization:** All agent outputs are sanitized to prevent injection or leaking of PII (Personally Identifiable Information).

---

## 📖 API Documentation

Detailed OpenAPI documentation is available at:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

### **Primary Endpoints**
- `POST /api/chat/message`: The entry point for the Multi-Agent engine.
- `GET /api/dashboard/stats`: Global office analytics.
- `PATCH /api/cases/{case_id}`: Secure case state transitions.

---

> [!IMPORTANT]
> This project is a **private, proprietary system**. Unauthorized access or distribution of the code or data is strictly prohibited.

**© 2026 Marid AI Systems. All rights reserved.**
