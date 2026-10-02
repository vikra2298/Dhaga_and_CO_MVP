# Dhaga & Co. MVP

FDE Academy Tech Track — Mini Project 1: **The Dhaga & Co. Engagement**.

Client engagement MVP for Dhaga & Co., a D2C fashion brand (Bengaluru). Discover the problem worth solving, build a deployed frontend MVP, present it back to the client.

## Status

| Phase | Status |
|-------|--------|
| 1. Discovery | In progress — fill `docs/discovery_note.md` before coding |
| 2. Build | Not started |
| 3. Present | Not started |

## Quick start (local)

> Cold start target: a stranger should run this in **five minutes**.

```bash
# Prerequisites: Python 3.11+, pip
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Add your API keys to .env

streamlit run frontend/main.py
```

Open the local URL Streamlit prints (usually `http://localhost:8501`).

## Project layout

```
Dhaga_&_CO_MVP/
├── README.md
├── requirements.txt
├── .env.example
├── brief/                          # Original client engagement PDF
├── docs/
│   ├── discovery_note.md           # Phase 1 (before first code commit)
│   └── build_note.md               # Phase 2 technical write-up
├── frontend/                       # UI only (Streamlit)
│   └── main.py
├── backend/                        # Logic, models, schemas
│   ├── workflows/                  # End-to-end orchestration
│   ├── patterns/                   # Agentic patterns (chain, route, etc.)
│   └── schemas/                    # Structured / validated outputs
└── data/
    └── sample/                     # Real-shaped sample inputs (Hinglish, free text)
```

**Separation rule:** `frontend/` renders screens and collects input. `backend/` owns workflows, patterns, schemas, and model calls. Keep product logic out of the UI.

## Deliverables checklist

- [ ] Discovery note (one page, seven required items) — dated before first feature commit
- [ ] Deployed MVP with a visible frontend and live URL
- [ ] Repository with this README (run, expect, fail visibly)
- [ ] Build note (code vs model table, patterns, cost line, unexpected break)
- [ ] Live presentation (20 min incl. questions; every member speaks)

## Build constraints (from brief)

- Mobile-first, low-end Android, unreliable connections
- Hinglish / vernacular input is normal
- COD-heavy economics
- No ML engineer on the client side — operable by a small busy team
- At least **two** agentic patterns: prompt chaining, parallelization, routing, evaluator-optimizer
- At least **two** models, with cost/latency/quality justification
- Structured (schema-validated) model outputs; fail visibly when unsure
- Report cost per run and at Dhaga & Co. volume

## Client brief

See [`brief/FDE_Academy_Tech_Track_Mini_Project_1_Dhaga_and_Co_Client_Engagement.pdf`](brief/FDE_Academy_Tech_Track_Mini_Project_1_Dhaga_and_Co_Client_Engagement.pdf).

## What fails looks like

The UI must show an explicit failure / “cannot answer” state. Silent wrong answers are not acceptable.

## License

Private group project for FDE Academy submission.
