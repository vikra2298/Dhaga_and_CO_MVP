# Discovery note — Dhaga & Co.

**Group:** Vikrant Kumar  
**Date:** 2026-10-01 — agreed before first feature commit (`a96c695`)  
**Status:** Agreed — build Return Intelligence for Neha (Category)

**Brief:** [`brief/FDE_Academy_Tech_Track_Mini_Project_1_Dhaga_and_Co_Client_Engagement.pdf`](../brief/FDE_Academy_Tech_Track_Mini_Project_1_Dhaga_and_Co_Client_Engagement.pdf)

---

## 1. The problem (one sentence, client language)

Returns labelled Other hide the fit and product issues Neha cannot read at scale, so the category team cannot see which SKUs, sizes, and vendors to fix.

---

## 2. Who owns it today, and what they do instead

| Role | Person | What they do today |
|------|--------|--------------------|
| Owner | Neha, Category Head | Reads “Other” return free text by hand; gets through only a few hundred rows; no systematic view by SKU, size, or vendor |
| Downstream fix | Vivek, Listing | Updates size charts, copy, or images only when someone escalates a specific SKU |
| Downstream pain | Ritu, CEO | Sees repeat purchase stuck at 22%; cannot point at which product issues to fix |
| Constraint | Dev, CTO | Sixteen engineers, no ML engineer — whatever ships must be runnable on Monday without a specialist hire |

---

## 3. Evidence from the case study (cite specifically)

- **Returns are 31% overall** → Neha, Category Head (“What the people inside the company say”)
- **44% of returns land in “Other”** → Data table, Returns row
- **When she reads Other by hand, most of it looks like fit, but she can only read a few hundred at a time** → Neha, Category Head
- **Size charts differ per vendor; colour typed ~90 ways; fabric is free text** → Catalogue / listing pain (why a fit cluster must point at a vendor size chart, not a chatbot)
- **Repeat purchase stuck at 22% for six quarters; CAC up 40% YoY** → Ritu (CEO) / Sameer (Growth) — downstream pressure, not the MVP claim
- **~48,000 orders a week; Hinglish is normal; no ML engineer** → Scale, Constraints, Dev (CTO)

---

## 4. What it costs them

Express in **money, time, or a metric they already track and argue about**.

| Metric | Value from brief | What it implies |
|--------|------------------|-----------------|
| Overall return rate | 31% | Category already tracks this; unstructured “Other” blocks diagnosis of why |
| Share of returns in “Other” | 44% | Nearly half of return signal is free text Neha cannot operationalise |
| Manual read capacity | A few hundred comments at a time | At ~48k orders/week, she cannot cover the “Other” volume by hand |
| Repeat purchase | 22%, stuck six quarters | Blindness on product issues feeds low trust / low repeat (hypothesis, not MVP proof) |
| CAC | Up 40% YoY | Sameer cannot outspend a retention/product-fit problem he cannot see |

Faizan’s ~₹120 is COD RTO cost, **not** product-return cost. We do not invent ₹ impact until Dhaga gives a cost per product return.

---

## 5. What success looks like (measurable with data they already hold)

- **Primary metric:** Share of “Other” rows that become a validated taxonomy label with a customer quote (auto-approved at ≥75%, or decided in Neha’s review queue)
- **Baseline today:** 44% of returns sit in unstructured “Other”; Neha samples a few hundred by hand; no SKU / size / vendor cluster view
- **Target for MVP proof:** One upload session produces labeled rows, SKU-level clusters with evidence, and a review queue only for rows under 75% or failed validation — no silent wrong labels
- **Data source they already have:** Returns export with reason dropdown + “Other” free text (MVP uses a synthetic CSV with `return_id`, `sku`, `category`, `vendor`, `size`, `return_reason`, `other_text`; confirm real join fields with Dhaga before a pilot)

**Out of MVP scope to claim:** return rate down, repeat purchase up, or CAC down. Those are hypotheses after Dhaga acts on accepted insights and remeasures.

---

## 6. Ranked shortlist (at least four problems)

| Rank | Problem | Owner inside Dhaga & Co. | Why this rank |
|------|---------|--------------------------|---------------|
| 1 | “Other” return text hides fit and product issues — no SKU / size / vendor pattern | Neha (Category) | Named owner, 31% and 44% already on her desk, data they already collect, operable without an ML engineer |
| 2 | Repeat purchase stuck at 22% | Ritu (CEO) | Real and expensive, but an outcome of several problems; MVP does not claim to move it |
| 3 | Catalogue attributes and vendor size charts inconsistent | Vivek (Listing) | How a fit finding becomes a fix; cleaning ~14k SKUs is later phase |
| 4 | WISMO tickets 58%, 9h first response | Arpita (CX) | Real CX pain; does not explain why products come back |
| 5 | COD RTO at 26%, ~₹120 each | Faizan (Supply) | Real money; different cause (delivery) and owner |

**Rejected for v1 on purpose:** customer chatbot, return prediction, automatic refunds/delist, mining all 410k reviews, search-journey analysis, full catalogue normalisation.

---

## 7. Biggest assumption, and what would prove it wrong

- **Assumption:** A meaningful share of “Other” is specific and repeated (fit, colour, quality), so a fixed taxonomy can be extracted reliably enough for Neha to act.
- **Falsifier:** A human read of a few hundred to a thousand real “Other” comments is mostly vague, **or** agreement between the model and that human read is too low for Neha to trust. Then this pick is the wrong v1, and we say so.

**Cheapest test:** Classify a sample file and have a person score label agreement before any catalogue workflow.

---

### Constraint reminder (Dev, CTO)

Sixteen engineers, **no ML engineer**. Whatever we build, somebody here has to run it on the Monday after we leave. Labels are internal; catalogue changes stay manual; Neha reviews only rows under 75% or that fail validation.
