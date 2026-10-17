# Batchwise

> **“Every batch. Every cost. Every rupee.”**

Batchwise is a local-first, AI-assisted batch costing and profit intelligence tool engineered for small Indian home-based food businesses—including homemade snack sellers, home bakers, and tiffin providers.

Built for the **Hacktoberfest 2026 Week 2 “Side Hustle” Challenge**.

---

## 1. Why the Name Batchwise?

The name is intentional and defines our core mission:

- **Batch** refers to a real production batch: one preparation run of snacks, baked goods, sweets, or meals that consumes raw ingredients, labour, packaging, fuel, and other direct resources.
- **Wise** represents informed, mathematically sound, data-driven decisions about pricing, costs, and profitability—eliminating guesswork and accidental underpricing.
- **Batchwise** therefore means **making smarter business decisions, one production batch at a time.**

---

## 2. The Core Problem

Small-scale home food entrepreneurs across India face distinct financial calculation traps:
1. **The Wastage Double-Counting Pitfall:** Many bakers count scrap both by reducing sellable units *and* inflating ingredient expenses, distorting their true unit cost.
2. **Confusing Margin vs. Markup:** Selling a ₹20 item for ₹24 yields a **16.67% profit margin**, not the 20% margin the seller expected (20% was the markup on cost). Batchwise keeps these transparent so wholesale and retail prices are never miscalculated.
3. **Hidden Overheads:** Fuel/LPG, delivery fees, and specialized packaging boxes are frequently absorbed as invisible losses instead of factored into the unit cost.
4. **Messy Vendor Notes:** Purchase notes arrive as unstructured scribbles or voice transcripts (e.g. *"5 kg besan cost 600 rupees, oil 180, packaging 80, made 75 packets, sold each for 25"*).

Batchwise bridges this gap: **A local-first open-weight language model (Gemma 3 1B) extracts messy notes into candidate fields, while a deterministic pure Python Decimal calculation engine performs 100% of the financial math.**

---

## 3. Architecture & Core Guarantees

```
┌─────────────────────────────────────────────────────────────────┐
│                      Batchwise Frontend                         │
│           (React 18 + TypeScript + Tailwind CSS 3)              │
│       Mobile-First UI • Indian Rupee (₹) • Audit Viewer         │
└────────────────────────────────┬────────────────────────────────┘
                                 │ HTTP / JSON
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                       FastAPI Backend                           │
│        Endpoints: /calculate, /recipes, /batches, /parse-note   │
└──────────────┬──────────────────────────────────┬───────────────┘
               │                                  │
               ▼                                  ▼
┌──────────────────────────────┐   ┌──────────────────────────────┐
│  Deterministic Math Engine   │   │     AI Note Extraction       │
│   Python Decimal Arithmetic  │   │   • Google Gemini API (Cloud)│
│   • Exact paisa precision    │   │     (gemini-2.5-flash / free)│
│   • Margin vs Markup logic   │   │   • Local Ollama (On-Device) │
│   • Dimension-safe units     │   │     (gemma3:1b / private)    │
│   • Step-by-step audit trace │   │   • Untrusted draft review   │
│   • Zero LLM math allowed    │   │   • Zero arithmetic by AI    │
└──────────────┬───────────────┘   └──────────────────────────────┘
               │
               ▼
┌──────────────────────────────┐
│     SQLite Persistence       │
│  (SQLAlchemy 2.0 ORM Models) │
│  • Reusable Recipe Templates │
│  • Production Batch History  │
└──────────────────────────────┘
```

### Guarantees
- **Zero Binary Float Arithmetic:** All currency and quantity calculations use Python `decimal.Decimal` with standard `ROUND_HALF_UP`.
- **Zero AI Math:** The language model (whether hosted Gemini or local Gemma 3) *never* calculates totals, unit costs, profit, or margins. All arithmetic is executed deterministically by verified Python algorithms.
- **Strict Dimension Safety:** Mass (kg/g), Volume (L/ml), and Count (units/dozens) conversions are dimension-checked. Cross-dimensional conversions (e.g. kg to L) are rejected unless an explicit conversion is provided.
- **Human-in-the-Loop AI Staging:** AI extractions are presented in an editable review staging modal. Ambiguities are highlighted in amber alerts, and values are never committed without seller review and confirmation.
- **Flexible Deployment:** Supports private local-first workflows (via Ollama) and turnkey hosted cloud demos (via Google Gemini free tier), with automatic provider resolution.

---

## 4. Canonical Financial Verification Example

Batchwise is continuously verified against the standard Hacktoberfest benchmark:
- **Inputs:** 5 kg besan (₹600) + 1 L oil (₹180) + packaging (₹80)
- **Production Yield:** 75 packets produced
- **Planned Selling Price:** ₹25 per packet
- **Authoritative Verified Results:**
  - **Total Batch Cost:** ₹860.00
  - **Cost Per Sellable Unit:** ₹11.47 per packet
  - **Break-Even Selling Price:** ₹11.47 per packet
  - **Projected Revenue:** ₹1,875.00
  - **Net Projected Profit:** ₹1,015.00 (₹13.53 per packet)
  - **Profit Margin:** **54.13%** of revenue
  - **Markup on Cost:** **118.02%** over production cost
  - **Break-Even Volume:** 35 packets to cover all batch costs

---

## 5. Local Development Quickstart

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- Ollama with `gemma3:1b` (optional, for local AI note parsing)

### 1. Backend Setup
```bash
cd backend

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run backend test suite (67 tests, 99% statement coverage)
pytest --cov=app

# Start development API server on http://127.0.0.1:8000
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Frontend Setup
```bash
cd frontend

# Install npm dependencies
npm install

# Run frontend test suite (16 tests, 0 warnings)
npm test

# Build production assets
npm run build

# Start Vite dev server on http://localhost:5173
npm run dev
```

### 3. Local Ollama Setup (For Local AI Note Parsing)
```bash
# In a separate terminal, pull and start Gemma 3 1B
ollama pull gemma3:1b
ollama run gemma3:1b
```

---

## 6. Production Deployment Guide

Batchwise is designed to be deployed cleanly on free cloud tiers with minimal configuration.

### Recommended Free Deployment Architecture

| Tier | Recommended Platform | Configuration |
|---|---|---|
| **Frontend** | **Vercel** or **Netlify** (Free Static Site) | Build: `npm run build`<br>Output: `dist`<br>Root: `frontend`<br>Env: `VITE_API_BASE_URL=https://<your-backend>.onrender.com/api/v1` |
| **Backend** | **Render** (Free Web Service) | Environment: `Python 3`<br>Build: `pip install -r requirements.txt`<br>Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`<br>Root: `backend` |

### Environment Variables

#### Backend (`backend/.env.example`)
| Variable | Default | Purpose |
|---|---|---|
| `PORT` | `8000` | Port assigned dynamically by cloud host |
| `HOST` | `0.0.0.0` | Bind address for container/server |
| `BATCHWISE_DATABASE_URL` | `sqlite:///./batchwise.db` | Database connection string (SQLite or PostgreSQL) |
| `BATCHWISE_CORS_ORIGINS` | `http://localhost:5173` | Comma-separated list of allowed frontend origins (e.g. `https://batchwise.vercel.app`) |
| `BATCHWISE_AI_PROVIDER` | `auto` | AI extraction provider: `auto`, `gemini`, or `ollama`. In `auto` mode, uses Gemini if `GEMINI_API_KEY` is present, else Ollama. |
| `GEMINI_API_KEY` | *(empty)* | Google Gemini API key (Free tier from [Google AI Studio](https://aistudio.google.com/)). Enables cloud AI parsing on hosted deploys like Render. |
| `BATCHWISE_GEMINI_MODEL`| `gemini-2.5-flash` | Gemini model tag (e.g., `gemini-2.5-flash`, `gemini-2.0-flash`) |
| `BATCHWISE_GEMINI_TIMEOUT`| `30.0` | Gemini API request timeout in seconds |
| `BATCHWISE_OLLAMA_URL` | `http://localhost:11434` | Ollama API endpoint (local-first on desktop/laptop) |
| `BATCHWISE_OLLAMA_MODEL` | `gemma3:1b` | Ollama model tag |
| `BATCHWISE_OLLAMA_TIMEOUT`| `30.0` | Ollama request timeout in seconds |

#### Frontend (`frontend/.env.example`)
| Variable | Default | Purpose |
|---|---|---|
| `VITE_API_BASE_URL` | `/api/v1` | Base URL of deployed backend API (e.g. `https://batchwise-api.onrender.com/api/v1`) |

---

## 7. AI Providers & Honest Hosting Disclosure

1. **Dual AI Provider Architecture (Cloud + Local):**
   - **Hosted Cloud AI (Google Gemini):** On hosted deployments like Render, configure `GEMINI_API_KEY` in Render environment variables. Batchwise calls Gemini's free tier via backend REST proxy with native JSON output mode. No personal notes are stored by the model, and LLM arithmetic is forbidden.
   - **Local & Private (Ollama Gemma 3 1B):** When self-hosting on a personal laptop or local server with Ollama running (`ollama run gemma3:1b`), Batchwise keeps all note processing 100% on-device and offline.
   - **Graceful Degradation:** If neither Gemini nor Ollama is configured or reachable, the application informs the user clearly: **Manual batch costing, recipe management, break-even simulation, and production batch history remain 100% operational.**
2. **SQLite Storage on Ephemeral Free Hosting:**
   - On free hosting tiers without persistent volume support (such as Render's Free Web Service), local SQLite files reset whenever the free container spins down after inactivity.
   - For a production deployment requiring permanent cloud storage, configure `BATCHWISE_DATABASE_URL` with a PostgreSQL connection string (such as Neon or Supabase free tiers).
   - For local self-hosting on a baker's laptop, the default SQLite storage is permanently persisted to disk.
   - For a production deployment requiring permanent cloud storage, configure `BATCHWISE_DATABASE_URL` with a PostgreSQL connection string (such as Neon or Supabase free tiers).
   - For local self-hosting on a baker's laptop, the default SQLite storage is permanently persisted to disk.

---

## 8. Verification & Test Suite

### Running the Full Test Suite
```bash
# 1. Backend tests
cd backend && pytest --cov=app

# 2. Frontend tests
cd ../frontend && npm test

# 3. Production build verification
npm run build
```

---

## 9. License & Project Information

- **License:** MIT License
- **Challenge:** Hacktoberfest 2026 Week 2 — “Side Hustle”
- **Philosophy:** Transparent math, zero hallucinated figures, local-first privacy.

