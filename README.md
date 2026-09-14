# FinMate AI

**Your Money. Smarter.**

An AI-powered personal finance platform built for students, employees,
households, and freelancers in Bangladesh — with natural-language transaction
entry (English + Bengali), real budget tracking, savings goals, and an AI
assistant grounded in your own data.

> **Scope note:** this repo is a genuine, tested, running MVP covering the
> core product (auth, transactions, budgets, goals, analytics, AI parsing,
> AI assistant, insights, financial health score, forecasting, demo data,
> tests). It intentionally does **not** implement every stretch feature from
> a full enterprise spec (SMS parsing, OCR, mobile apps, bank integrations,
> etc.) — those are listed under [Future Improvements](#future-improvements)
> and the architecture is designed so they can be added without a rewrite.

---

## Table of contents

- [Features](#features)
- [Architecture](#architecture)
- [Technology stack](#technology-stack)
- [Database schema](#database-schema)
- [API overview](#api-overview)
- [Installation](#installation)
- [Environment setup](#environment-setup)
- [Running locally](#running-locally)
- [Demo accounts](#demo-accounts)
- [AI configuration](#ai-configuration)
- [Testing](#testing)
- [Docker](#docker)
- [Deployment](#deployment)
- [Security & privacy notes](#security--privacy-notes)
- [Project limitations](#project-limitations)
- [Future improvements](#future-improvements)
- [Troubleshooting](#troubleshooting)

---

## Features

- **Auth**: register/login with hashed passwords (bcrypt) and JWT sessions
- **Onboarding**: user type, income, savings target, language preference
- **Transactions**: full CRUD, search, and filter by category/date/amount/payment method
- **Natural-language entry**: "I spent 250 taka on lunch" or "আজকে রিকশায় ১২০ টাকা খরচ হয়েছে" → parsed into a draft transaction you confirm before saving
- **Hybrid categorization**: keyword rules first, LLM fallback only when rules don't match, user always able to override
- **Budgets**: per-category monthly budgets with usage %, warning/overspent status
- **Savings goals**: target/current amount, progress %, required monthly saving, contributions
- **Analytics**: income/expense summary, category breakdown — all computed directly from your transactions, never invented
- **AI insights**: spending increases, budget warnings, positive trends, unusual-transaction flags — every insight cites the numbers behind it
- **Financial health score**: transparent 0–100 score broken into 4 explainable sub-scores
- **Forecasting**: honest end-of-month projection that explicitly says "not enough data" rather than guessing
- **AI assistant**: chat interface that only ever sees a small, structured snapshot of *your own* current data — never the raw database, never another user's data
- **Graceful AI fallback**: every AI feature has a deterministic/rule-based fallback, so the app works fully with zero AI configuration
- **Demo data**: three ready-made personas (student, employee, household) in BDT with 3 months of realistic transaction history

## Architecture

```
User → Frontend (React/TS) → Backend API (FastAPI) → SQLite/Postgres
                                      │
                                      ▼
                              AI Service Layer
                          (rules first, LLM second)
                                      │
                                      ▼
                         Optional LLM Provider (OpenAI-compatible)
```

Key design principle carried through the whole codebase: **AI is layered on
top of deterministic logic, never a replacement for it.**

- Totals, percentages, budget usage, goal progress → plain arithmetic (`app/analytics.py`)
- Categorization → keyword rules → LLM fallback (`app/ai/categorizer.py`)
- Natural-language transaction entry → LLM first (better at free text) → regex fallback (`app/ai/parser.py`)
- AI assistant → receives a small JSON snapshot built server-side, never raw DB access (`app/ai/assistant.py`)
- If the LLM call fails, times out, or no API key is set, every AI feature falls back to its non-AI version automatically. Nothing breaks.

## Technology stack

**Frontend:** React 18, TypeScript, Vite, Tailwind CSS, Recharts, React Router, Axios
**Backend:** Python, FastAPI, SQLAlchemy, Pydantic, python-jose (JWT), passlib (bcrypt)
**Database:** SQLite by default (zero setup); swappable to PostgreSQL via `DATABASE_URL`
**AI:** any OpenAI-compatible chat completions endpoint (OpenAI, Groq, OpenRouter, etc.), configured purely through environment variables — fully optional

## Database schema

Tables: `users`, `profiles`, `categories`, `transactions`, `budgets`,
`budget_categories`, `savings_goals`, `notifications`, `financial_insights`,
`chat_sessions`, `chat_messages`, `recurring_transactions`, `financial_scores`.

Full definitions with fields, types, and relationships: `backend/app/models.py`.

## API overview

All endpoints (except `/auth/register` and `/auth/login`) require a Bearer
JWT from the login response. Full interactive docs (Swagger UI) are
available at **`http://localhost:8000/docs`** once the backend is running.

| Method | Path | Purpose |
|---|---|---|
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Get access token |
| GET/PUT | `/auth/profile` | Onboarding profile |
| GET/POST | `/transactions` | List / create transactions |
| PUT/DELETE | `/transactions/{id}` | Edit / delete a transaction |
| POST | `/transactions/parse` | Natural-language → draft transaction |
| GET/POST | `/budgets` | List / set monthly budgets |
| GET/POST | `/goals` | List / create savings goals |
| POST | `/goals/{id}/contribute` | Add money toward a goal |
| GET | `/analytics/summary` | Income/expense/balance/savings rate |
| GET | `/analytics/insights` | AI/rule-based insights |
| GET | `/analytics/health-score` | Explainable financial health score |
| GET | `/analytics/forecast` | End-of-month projection |
| POST | `/ai/chat` | AI financial assistant |
| GET | `/notifications` | User notifications |

## Installation

Requirements: **Python 3.11+**, **Node.js 18+**, `git`.

```bash
git clone <your-repo-url> finmate-ai
cd finmate-ai
```

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env
```

### Frontend

```bash
cd ../frontend
npm install
```

## Environment setup

Copy `.env.example` to `.env` in `backend/` (already done above) and adjust
if needed. Defaults work out of the box with zero configuration:

```bash
DATABASE_URL=sqlite:///./finmate.db   # no setup required
SECRET_KEY=change-this-to-a-long-random-string
LLM_API_KEY=                          # leave blank to run AI-free
```

For the frontend, create `frontend/.env` with:

```bash
VITE_API_URL=http://localhost:8000
```

## Running locally

**Terminal 1 — backend:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```
Visit `http://localhost:8000/docs` to explore the API.

**Terminal 2 — seed demo data (optional but recommended):**
```bash
cd backend
source venv/bin/activate
python -m app.seed
```

**Terminal 3 — frontend:**
```bash
cd frontend
npm run dev
```
Visit `http://localhost:5173`.

## Demo accounts

After running `python -m app.seed`, log in with any of:

| Persona | Email | Password |
|---|---|---|
| Student (৳12,000/mo) | `student@demo.finmate.ai` | `demo1234` |
| Employee (৳45,000/mo) | `employee@demo.finmate.ai` | `demo1234` |
| Household (৳80,000/mo) | `household@demo.finmate.ai` | `demo1234` |

Each has 3 months of realistic transaction history, an active budget, a
savings goal, and a deliberately oversized transaction so you can see the
anomaly-detection insight fire immediately.

## AI configuration

FinMate AI works completely without any AI provider — categorization falls
back to keyword rules, transaction parsing falls back to regex extraction,
and the assistant falls back to template answers built from your real
numbers.

To enable full AI features, set in `backend/.env`:

```bash
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini
LLM_BASE_URL=https://api.openai.com/v1
```

Any OpenAI-compatible provider works by changing `LLM_BASE_URL` (e.g. Groq,
OpenRouter, Together AI). **Never commit a real API key** — `.env` is
git-ignored.

## Testing

```bash
cd backend
source venv/bin/activate
python -m pytest tests/ -v
```

Covers: registration/login, permission isolation (users can't see each
other's data), transaction CRUD, English + Bengali natural-language parsing,
budget usage math, savings goal math, analytics correctness, financial
health score, and the AI-disabled fallback path (18 tests, verified passing).

```bash
cd frontend
npx tsc -b --noEmit   # type-check
npm run build         # production build
```

## Docker

```bash
cp .env.example .env   # edit as needed
docker compose up --build
```

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5173`

To seed demo data inside Docker:
```bash
docker compose exec backend python -m app.seed
```

## Deployment

**Development:** SQLite, `--reload`, verbose logs — as configured above.

**Demo/staging:** Deploy the backend to a free-tier host (Render, Railway,
Fly.io) with `DATABASE_URL` pointed at a managed Postgres instance instead
of SQLite; deploy the frontend static build (`npm run build` → `dist/`) to
Vercel, Netlify, or Cloudflare Pages, with `VITE_API_URL` set to your
backend's public URL.

**Production changes required:**
- Switch `DATABASE_URL` to PostgreSQL and use a migration tool (Alembic) instead of `Base.metadata.create_all`
- Set a strong, unique `SECRET_KEY`
- Restrict CORS `allow_origins` to your real frontend domain
- Put the API behind HTTPS
- Add rate limiting in front of `/ai/*` endpoints to control LLM cost
- Rotate the `LLM_API_KEY` and store it in your host's secret manager, not in a committed `.env`

## Security & privacy notes

- Passwords are hashed with bcrypt, never stored in plain text
- All data-returning endpoints filter by the authenticated user's ID — verified by an automated test that two users cannot see each other's transactions
- The AI assistant receives only a small structured snapshot of the current user's data, built server-side — it never has raw database access and never sees other users' data
- No API keys are ever sent to the frontend
- **Prototype limitation:** this is a student/portfolio-grade prototype, not an audited financial system. It has not undergone a professional security review, has no rate limiting, and SQLite is not suitable for concurrent production traffic.

## Project limitations

- Single currency (BDT) end-to-end; multi-currency is not implemented
- No bank/mobile-financial-service API integrations (manual + natural-language entry only)
- Forecasting is a simple daily-average projection, not a trained model
- No automated recurring-transaction execution yet (the `RecurringTransaction` table exists but isn't scheduled)
- No PDF/CSV report export yet (the underlying data endpoints exist; export formatting is a natural next step)
- No mobile app (the frontend is responsive, but not a native app)

## Future improvements

Architecture already supports adding, without a rewrite:
- Bank/MFS API integration
- SMS transaction parsing
- Receipt OCR
- Voice-based expense entry
- WhatsApp/Telegram bot on top of the same `/ai/chat` and `/transactions/parse` endpoints
- Family shared wallets
- Investment tracking
- PDF/CSV report export
- A scheduled job to materialize `RecurringTransaction` rows into real transactions
- Push/email notifications (the `Notification` model and endpoints already exist)

## Troubleshooting

**`ModuleNotFoundError` when starting the backend** — make sure you activated
the virtual environment and ran `pip install -r requirements.txt` inside `backend/`.

**Frontend can't reach the API / CORS errors** — confirm the backend is
running on port 8000 and `frontend/.env` has `VITE_API_URL=http://localhost:8000`.

**"Incorrect email or password" on a fresh install** — you likely haven't
registered yet, or haven't run `python -m app.seed` if you're trying a demo account.

**AI features feel "dumb"** — that's expected with no `LLM_API_KEY` set; you're
seeing the deterministic fallback, by design. Set an API key to unlock the LLM-backed versions.

**Port already in use** — change `--port 8000` (backend) or `vite.config.ts`'s
`server.port` (frontend), and update `VITE_API_URL`/`FRONTEND_URL` to match.
