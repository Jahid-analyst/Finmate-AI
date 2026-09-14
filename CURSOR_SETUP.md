# Working on FinMate AI in Cursor / VS Code

This project is split into two independent apps so Cursor can index and edit
each one cleanly:

```
finmate-ai/
├── backend/   ← open this folder for backend work (Python/FastAPI)
└── frontend/  ← open this folder for frontend work (React/TypeScript)
```

## Recommended workflow

1. Open the **repo root** (`finmate-ai/`) as your Cursor/VS Code workspace —
   this lets Cursor see both apps and the shared `.env.example` at once.
2. Open two terminals: one in `backend/`, one in `frontend/`.
3. Run the backend and frontend dev servers side by side (see the main
   `README.md` for exact commands).

## Where things live

| If you want to change...              | Edit this                                      |
|-----------------------------------------|-------------------------------------------------|
| Database tables / relationships         | `backend/app/models.py`                          |
| API request/response shapes             | `backend/app/schemas.py`                         |
| An API endpoint                         | `backend/app/routers/*.py`                       |
| Deterministic finance calculations      | `backend/app/analytics.py`                       |
| AI parsing / categorization / chat      | `backend/app/ai/*.py`                            |
| Demo data                               | `backend/app/seed.py`                            |
| A page's UI                             | `frontend/src/pages/*.tsx`                       |
| Navigation / layout                     | `frontend/src/components/Sidebar.tsx`, `Layout.tsx` |
| API calls from the frontend             | `frontend/src/lib/api.ts`                        |
| Colors, fonts, design tokens            | `frontend/tailwind.config.js`                    |

## Useful prompts to give Cursor/Claude while extending this project

- "Add a new expense category called X to the categorizer and the frontend category dropdowns."
- "Add a `/reports/monthly` PDF export endpoint using the pdf skill / a Python PDF library."
- "Add a Notifications page that lists `GET /notifications` and lets me mark them read."
- "Add a recurring-transactions scheduler that creates transactions from `RecurringTransaction` rows automatically."

## Before committing

- Backend: `cd backend && python -m pytest tests/ -v`
- Frontend: `cd frontend && npx tsc -b --noEmit && npm run build`

Both should pass with zero errors — this repo was verified to pass both at
the time it was generated.
