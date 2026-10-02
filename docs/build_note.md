# Build note — Dhaga & Co. MVP

**Max length:** two pages  
**Fill after the MVP exists.** Discovery note must be dated before feature work.

---

## Problem we built for

_[One sentence from discovery note]_

## Code vs model table

Every step is either deterministic code or a model call. Know which, and why.

| Step | Code or model? | Why | Model / temp (if any) | Schema |
|------|----------------|-----|------------------------|--------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

## Patterns used (at least two)

| Pattern | Where in the workflow | What breaks without it |
|---------|----------------------|------------------------|
| Prompt chaining | | |
| Parallelization | | |
| Routing | | |
| Evaluator–optimizer | | |

## Two-model split

| Model | Role | Cost / latency / quality justification |
|-------|------|----------------------------------------|
| Cheap / bulk | | |
| Stronger / judgment | | |

## Temperatures

| Task type | Temperature | Why |
|-----------|-------------|-----|
| Extraction / classification / evaluation | | |
| Customer-facing copy (if any) | | |

## Cost line

Show the arithmetic. Dev (CTO) will ask.

| Item | Value |
|------|-------|
| Cost per single run | ₹ / $ |
| Volume at Dhaga & Co. for this use case | _[from brief]_ |
| Estimated weekly / monthly cost at that volume | |
| Assumptions | |

## Structured output & failure

- Schema validation: _[library / approach]_
- When validation fails: _[visible UI behaviour]_
- When the system cannot answer: _[exact screen copy / state]_

## Real-shaped input

What sample data proves this is not a curated demo path (Hinglish, free text, messy catalogue fields, etc.):

- `data/sample/...`

## Code layout reminder

- UI: `frontend/`
- Workflows / patterns / schemas / model clients: `backend/`


## The thing that broke that we did not expect

_[Honest write-up]_

## What we would build next

_[Honest scope we did not ship; what we would need from the client]_
