# Solution and approach — Dhaga Return Intelligence

**Status:** Locked for MVP build  
**Date:** 2026-10-02  
**Client brief:** [`brief/FDE_Academy_Tech_Track_Mini_Project_1_Dhaga_and_Co_Client_Engagement.pdf`](../brief/FDE_Academy_Tech_Track_Mini_Project_1_Dhaga_and_Co_Client_Engagement.pdf)  
**One-page discovery deliverable:** [`docs/discovery_note.md`](discovery_note.md) — fill and date it before the first feature commit  
**Build write-up (after the MVP exists):** [`docs/build_note.md`](build_note.md)

This document is the spec we build from. Numbers below are either quoted from the brief or marked as estimates. Anything the brief does not state is a question for the client, not a fact we invent.

---

## 1. What we are building

> An internal Return Intelligence tool that converts Dhaga’s unstructured “Other” return comments into a validated taxonomy, then shows which SKU, size, and vendor the complaints cluster on, with the customer’s own words and a confidence percentage. A row at 75% or above is filed automatically. Neha only reviews what is still under 75%, or a reply that failed validation. The tool never changes the catalogue by itself.

**Primary user:** Neha, Category Head.

**Her workflow today (brief, “What the people inside the company say”):**

```text
Customer returns a product
    → picks a reason, or "Other" plus free text
    → the text sits in the returns data
    → Neha reads some of it by hand
    → she can only get through a few hundred
    → no systematic view by SKU, size, or vendor
```

**One sentence, in her language:**

> Returns labelled Other hide the fit and product issues Neha cannot read at scale, so the category team cannot see which SKUs, sizes, and vendors to fix.

---

## 2. Why this problem (brief evidence)

The brief gives a client, not a problem statement. We chose this because a named person is losing something measurable today.

| Evidence | Source in the brief | How we use it |
|----------|---------------------|---------------|
| Returns are 31% overall | Neha, Category Head | The metric she already tracks |
| 44% of returns land in “Other” | Data table, Returns row | The unstructured bucket we classify |
| When she reads Other by hand, most of it looks like fit, but she can only read a few hundred at a time | Neha | The workflow gap |
| Size charts differ per vendor; colour ~90 ways; fabric is free text | Catalogue row | Why a fit cluster should point at a vendor size chart, not at a chatbot |
| Repeat purchase stuck at 22% for six quarters | Ritu, CEO | Downstream pain, not the MVP claim |
| CAC up 40% year on year | Sameer, Head of Growth | Same: hypothesis, not a demo result |
| 16 engineers, no ML engineer | Dev, CTO | Human review and a simple UI someone can run on Monday |
| ~48,000 orders a week | Scale | Volume for the cost line |
| Hinglish is normal | Constraints | Sample data and the failure case |
| Anything customer-facing is safe unread or has a designed human review step | Constraints | Labels are internal. Catalogue changes stay manual. Neha reviews only rows under 75% |
| Models do language and messy mapping; code does arithmetic, comparison, and lookup | Phase 2 | Classification is a model; counts are code |
| At least two of: prompt chaining, parallelization, routing, evaluator–optimizer | Phase 2 | Routing + evaluator–optimizer |
| At least two models; structured output; fail visibly; temperatures stated | Ground rules | See sections 6–8 |
| An MVP that does one thing convincingly beats four half-built features | Scope | Returns “Other” only |

**Case facts we will say out loud.** 31% returns. 44% Other. Neha can read only a few hundred. 22% repeat purchase. CAC +40% YoY. These are not the same claim as “our tool reduced returns.”

**Not in the brief (we ask, we do not invent):** row-level return fields (whether every return already has SKU, size, and vendor), the true mix inside “Other,” cost per product return, and token prices. Faizan’s ~₹120 is the cost of a COD return-to-origin, not the cost of a product return. The dashboard shows counts and shares. A rupee impact appears only after Dhaga gives a cost per return.

---

## 3. Ranked shortlist

| Rank | Problem | Owner | Why it sits here |
|------|---------|-------|------------------|
| 1 | “Other” return text hides fit and product issues, so category cannot see SKU / size / vendor patterns | Neha | Named owner, 31% and 44% already on her desk, data they already collect, operable without an ML engineer |
| 2 | Repeat purchase stuck at 22% | Ritu | Real and expensive. It is the outcome of several problems. The MVP does not claim to move it |
| 3 | Catalogue attributes and vendor size charts are inconsistent | Vivek / listing | Real, and it is how a fit finding becomes a fix. Cleaning 14,000 SKUs is a later phase |
| 4 | 58% of tickets are “where is my order,” 9-hour first response | Arpita | Real pain. It does not explain why products come back |
| 5 | COD RTO at 26%, ~₹120 each | Faizan | Real money. Different cause (delivery), different owner |

Rejected for v1 on purpose: customer chatbot, return prediction, automatic refunds, automatic delist, review mining of all 410,000 reviews, search-journey analysis, full catalogue normalisation.

---

## 4. MVP boundary

### Build

- Ingest a CSV of return rows shaped like the client (Hinglish free text, not three perfect English lines).
- Classify only rows whose reason is “Other” (or whose free-text box is filled).
- Map each row to the fixed taxonomy, with a confidence percentage and a short quote from the text.
- Auto-approve at 75% or above when the schema is valid and the quote is inside the comment.
- Aggregate in code by SKU, size, and vendor. Auto-approved rows are included.
- Three screens: Upload, Dashboard, Review.
- Show a failure on purpose: a row under 75%, or a reply with no valid score, stays in review.
- Suggest one action from the final label. Nothing is written back to the catalogue.

### Do not build

- Customer-facing copy, chat, or refunds.
- Automatic size-chart or listing edits.
- A model that counts, ranks, or computes rates.
- Reviews, tickets, Mixpanel search, or catalogue-colour cleanup in v1.
- A production pipeline for all 14,000 live SKUs.

### Later (say this in “what we would build next”)

Add the 410,000 reviews as a second evidence source for the same SKU. Then, only if Neha asks, normalise colour and fabric, and connect occasion search (“office wear kurti”) to the return reason. Each of those needs a field check with Dhaga first.

---

## 5. Workflow

```text
CSV upload
    → Intake agent: require columns, drop empty text, trim to 1000 characters,
            dedupe, cap 500 rows per run, keep only "Other" / free text,
            then split the kept comments into batches of 8
    → Review agent, after those batches arrive:
            cheap model (temperature 0): one validated JSON per row
            show confidence as a percentage (0.88 is 88%)
            75% or above, schema valid, quote inside the text: auto-approve
            under 75%, or schema invalid: stronger model re-checks that row
            still under 75%, or still invalid: send the row to Neha
    → code: counts and shares by SKU, size, vendor, label
    → code: one suggested action from the final label
    → Neha: only the review queue — Approve / Edit / Dismiss
    → dashboard uses auto-approved labels and Neha’s final labels
```

**Auto-approve does not mean a catalogue edit.** It means the label is counted without a click. Clear dislike with no product reason is a high-confidence label, not a review item.

| Comment | Label | Confidence | Result |
|---------|-------|------------|--------|
| `product acha nahi laga` | `insufficient_evidence` | about 88% | Auto-approved. No size-chart or vendor action |
| `I didn’t like the product` | `insufficient_evidence` | about 90% | Auto-approved. No catalogue action |
| `macha nai lga` | `insufficient_evidence` | about 80% if the model recognizes it | Auto-approved. Same label as the clear sentence |
| `shrit but chota h` | `fit_too_small` | about 90% | Auto-approved and counted on that SKU |
| `shrit thoda alg h size` | unclear size direction | 58% | Review. Neha decides |
| `ok return` and the quote is not in the text | none | No score | Review. Never auto-approved |

A vague comment is handled correctly when it becomes `insufficient_evidence` at 75% or above. It is not a validation failure. Validation failure is only a quote missing from the text, a label outside the eleven, or JSON that does not match the schema.

**Required CSV columns**

`return_id`, `sku`, `category`, `vendor`, `size`, `return_reason`, `other_text`

The brief does not publish this row schema. The MVP uses synthetic rows with these columns and says so. Before a real pilot we confirm with Dhaga that returns can be joined to SKU, size, and vendor.

**Caps:** 1000 characters per comment, 500 rows per run. Over the cap, the screen says what was dropped.

---

## 6. Taxonomy

Eleven labels. The model may return only these. Any other string fails validation and goes to review.

| Primary | Label | Typical evidence |
|---------|-------|------------------|
| Fit | `fit_too_small` | “M chota hai”, “expected se chota” |
| Fit | `fit_too_large` | “size bada hai” |
| Fit | `fit_too_tight` | “bahut tight”, “shoulder tight” |
| Fit | `fit_too_loose` | “loose hai”, “dheela” |
| Fit | `size_chart_mismatch` | “chart galat”, “not true to size” |
| Quality | `quality_fabric` | “kapda transparent”, “cloth patla” |
| Quality | `quality_stitching_or_damage` | stitch, tear, defect |
| Colour | `colour_image_mismatch` | “photo jaisa nahi” |
| Expectation | `description_or_look_mismatch` | style or description does not match, and it is not fit or colour |
| Unclear | `insufficient_evidence` | “acha nahi laga”, “did not like” |
| Not a product issue | `not_a_product_issue` | “delivery late hui”, wrong item, courier |

One JSON object can hold more than one issue when the sentence clearly has two (tight **and** colour). That is one model call with a list, not three agents.

**Suggested action (code, after the label is final):**

| Final label | Suggested action |
|-------------|------------------|
| Any fit label or `size_chart_mismatch` | Review this vendor’s size chart for this SKU |
| `colour_image_mismatch` | Compare listing images with the evidence quotes |
| `quality_fabric` or `quality_stitching_or_damage` | Raise with the vendor; do not edit the listing automatically |
| `description_or_look_mismatch` | Review product copy against the quotes |
| `insufficient_evidence` | No catalogue action |
| `not_a_product_issue` | No catalogue action. Delivery, courier, or wrong item |

---

## 7. Where the model stops and code starts

| Step | Code or model | Why | Temperature | Schema |
|------|---------------|-----|-------------|--------|
| Parse CSV, drop empties, trim, dedupe, cap rows | Code | Lookup and limits | — | Column contract |
| Classify “Other” text into the taxonomy and quote a span | Model A, cheap | Language, Hinglish, messy mapping | 0 | `Classification` |
| Re-check only rows under 75% or invalid rows | Model B, stronger | Judgment | 0 | `Evaluation` |
| Auto-approve at 75% or above | Code | Threshold, not a model judgment | — | `final_label` |
| Counts, shares, SKU / size / vendor grouping | Code | Arithmetic | — | Aggregates |
| Suggested action | Code | Lookup from final label | — | Action enum |
| Approve, edit, dismiss | Human, review queue only | Rows still under 75%, or no valid score | — | `final_label` |

Model output (both models), validated with Pydantic before anything is stored:

```text
issues[]: { label, confidence, evidence_span }
needs_review: bool
short_reason: str
```

`confidence` is stored as 0–1 and shown as a percentage. `evidence_span` must be a substring of the input. If it is not, the row has no score and goes to review.

Dashboard math uses auto-approved labels and Neha’s `final_label`. Rows still in review stay out of the counts.

---

## 8. Patterns (why the problem needs them)

### Routing

75% or above, with a valid schema and a real quote, is auto-approved. Under 75%, or a failed schema, goes to Model B. If Model B is still under 75%, the row goes to Neha.

Without routing, Neha is back to reading every comment, including clear lines such as “acha nahi laga”.

### Evaluator–optimizer

Model B sees the original text and Model A’s label. It confirms the label or replaces it with `insufficient_evidence` / `needs_review`.

Without it, a confident-looking wrong fit tag can send a vendor size-chart review that the words do not support. Example: “product acha nahi laga” must not become `quality_fabric`.

### Two agents

**Intake** loads the file and batches the comments that survive the column checks. It does not call a model. Batches are 8 comments. The dashboard shows how many comments arrived and how many batches Review received.

**Review** starts only after Intake has finished. It classifies each comment, files a row at 75% or above, and sends every row under 75% — or with no score — to Neha. Comments inside one batch are classified together. The next batch waits until that one is routed.

### Parallelization (inside a batch)

Comments in one batch are independent, so Review classifies them together. Each comment is still one classify call, then Model B only if that comment is under 75% or invalid. We do not run separate models for fit, colour, and quality.

---

## 9. Two models

| Model | Role | Why this split |
|-------|------|----------------|
| Model A — `openai/gpt-oss-20b` on Groq | Every eligible row | Free smaller model for bulk Hinglish classification |
| Model B — `openai/gpt-oss-120b` on Groq | Only rows under 75%, or rows whose JSON failed | Free stronger model for the unsure rows. Same Groq key |

Both run at temperature 0. Classification and evaluation are not customer-facing copy.

If a key is missing, the API errors, or JSON fails twice, the screen says the row was not classified and shows the raw text. No guessed label.

---

## 10. Screens

Internal tool for Neha on a laptop. Not the customer Android app. The screen is React. The API is FastAPI. Deploy both, and put both URLs in the README.

### Upload

File in. Show rows kept, rows dropped, and why (empty text, over the character cap, over 500 rows, missing columns). Missing API key is an error on this screen.

### Return metrics

Landing page. Colour-coded signals: brief return rate, brief Other share, share of this file now labeled, and how many rows were filed without a click. The reason mix sits beside the three unanswered items: rupees, exchanges, and trend. It does not show a rupee saving or a new return rate.

### Command center

The working page for this file:

- How many comments were loaded, how many are counted, and how many are still open.
- Which SKU, vendor, and size to work on, with the customer’s words.
- What Intake and Review did.
- What still needs Neha, with a link to Review.

The brief’s 31% and 44%, the reason colours, and the unanswered money, exchange, and trend lines live on Return metrics, not here.

Sample-data percentages on this screen are labelled **sample**. They are not the case-study mix. The brief does not give the breakdown inside “Other.”

### Review

Queue for Neha. Top of the page shows auto-approved and still-open totals, then one card per SKU with those same two counts. Selecting a SKU filters the open rows. Actions stay Approve, Edit, Dismiss. Dismissed rows never enter the counts.

---

## 11. What success means

### What the MVP proves

| Metric | Baseline from the brief | MVP proof |
|--------|-------------------------|-----------|
| Can “Other” be read as a standard label with a quote? | 44% sits in Other; Neha samples a few hundred by hand | Each row is auto-approved at 75% or above, or sent to review. No silent wrong label |
| Time to see a SKU / size / vendor cluster | Days of manual reading, and only a few hundred rows | Same session as the upload, for the rows in that file |
| Would Neha trust it? | She has no queue | She only opens rows under 75%. Approve, edit, or dismiss, and the dashboard follows that decision |

### What we do not claim in the demo

Return rate down, repeat purchase up, or CAC down. Those are the hypothesis **after** Dhaga acts on accepted insights and measures again with data they already have (returns, repeat purchase).

**Hypothesis, said as a hypothesis:** if accepted fit clusters lead the team to fix the vendor size chart or the listing, fit-related returns on those SKUs can fall, and that may help the 22% repeat rate. Dhaga would measure that. We will not.

### Assumption and falsifier

- **Assumption:** a meaningful share of “Other” is specific and repeated (fit, colour, quality), so a taxonomy can be extracted reliably.
- **Falsifier:** a human read of a few hundred to a thousand real “Other” comments is mostly vague, or agreement between the model and that human read is too low for Neha to act. Then this pick is the wrong v1, and we say so.

Cheapest test of the assumption: classify a sample file and have a person score agreement, before any catalogue workflow.

---

## 12. Cost line (fill when models are chosen)

Show this arithmetic in the build note. Do not invent a rupee figure.

```text
Other rows per week (estimate, label it as one)
    = 48,000 orders/week × 31% returns × 44% Other
    = 48,000 × 0.31 × 0.44
    ≈ 6,550 rows/week

This multiplication assumes the 31% return rate applies to weekly orders.
The brief states each number separately. It does not state weekly return counts.

Model A cost per 1,000 rows = (tokens per row / 1000) × A price
Model B cost per 1,000 reviewed rows = (tokens per row / 1000) × B price
Share sent to Model B = measured on the sample (design target: well under all rows)

Weekly cost ≈ (6,550 / 1000) × Model A cost per 1,000
            + (6,550 / 1000) × (share to Model B) × Model B cost per 1,000
```

Also report cost of one demo run (the uploaded file), not only the weekly estimate.

---

## 13. What we show live

**Auto-approved, no click from Neha**

```text
"product acha nahi laga"
"I didn't like the product"
"macha nai lga"   (when the model recognizes it)
```

Screen: `insufficient_evidence`, about 80–90%, already on the dashboard. No fit label. No vendor action.

**Review, because the score is under 75%**

```text
"shrit thoda alg h size"
```

Screen: confidence such as 58%. Neha approves, edits, or dismisses.

**Review, because there is no score**

A quote that is not in the customer’s text, a label outside the eleven, or JSON that does not match the schema. The UI says validation failed and shows no percentage. That row is never auto-approved.

---

## 14. Where the code will live

```text
frontend/                        React dashboard (Upload, Dashboard, Review)
backend/api.py                   FastAPI
backend/agents/intake.py         Intake agent: load comments, batch by 8
backend/agents/route.py          Review agent: classify, auto-approve, send the rest to Neha
backend/workflows/ingest.py      CSV contract, caps, dedupe
backend/workflows/classify.py    Model A, then Model B under 75%
backend/store.py                 SQLite counts and review decisions
backend/schemas/                 Pydantic taxonomy and model output
data/sample/returns_other.csv    Hinglish “Other” rows, messy on purpose
```

SQLite is enough for the demo. Secrets stay in the host’s secret store, never in git.

---

## 15. Demo story (do not open with architecture)

**Problem (about 3 min).** Neha’s returns are 31%. 44% are “Other.” She already thinks much of that is fit, and she can only read a few hundred.

**Why it matters (about 3 min).** While that text stays unstructured, category cannot point at a SKU, a size, and a vendor. Repeat purchase at 22% and CAC up 40% are why Ritu and Sameer care. We do not claim this MVP has moved those numbers.

**Live demo (about 6 min).** Upload the sample. Show a SKU cluster with quotes. Show “acha nahi laga” already filed at 88% as not enough evidence, with no catalogue action. Then open Review and show one row under 75%, plus one row with no score. Edit the low-percentage row and show the dashboard follow that label.

**Next (about 2 min).** Reviews as a second source. Confirm the real return schema and a cost per return with Dhaga. No auto-edits to size charts.

**Questions we expect.** Cost (section 12). Who runs it (Neha uses it; an engineer keeps the Space and the keys; no ML hire). What happens when it is wrong (review queue, dismiss, no catalogue write).

---

## 16. Build order

| Day | Work |
|-----|------|
| Before feature code | Agree and date `docs/discovery_note.md` from sections 1–3 and 11 of this file |
| Day 1 | Taxonomy enum, sample CSV, ingest, schemas, three screens with the failure state already visible |
| Day 2 | Model A, routing, review actions |
| Day 3 | Aggregates, deploy the URL, cost arithmetic, one live failure |

Deploy a trivial running URL early. Do not leave hosting to the morning of the presentation.
