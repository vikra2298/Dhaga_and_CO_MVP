import { useEffect, useState } from "react";
import { api, type Dashboard, type ReviewRow, type SkuDetail, type UploadResult } from "./api";

type Page = "metrics" | "dashboard" | "review" | "upload";

export function App() {
  const [page, setPage] = useState<Page>("metrics");
  const [data, setData] = useState<Dashboard | null>(null);
  const [sku, setSku] = useState("KURTI123");
  const [detail, setDetail] = useState<SkuDetail | null>(null);
  const [queue, setQueue] = useState<ReviewRow[]>([]);
  const [error, setError] = useState("");
  const [upload, setUpload] = useState<UploadResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [reviewSku, setReviewSku] = useState<string>("all");

  async function refresh() {
    const next = await api.dashboard();
    setData(next);
    const review = await api.review();
    setQueue(review.rows);
    const chosen = next.skus.includes(sku) ? sku : next.skus[0];
    if (chosen) {
      setSku(chosen);
      setDetail(await api.sku(chosen));
    } else {
      setDetail(null);
    }
  }

  useEffect(() => {
    refresh().catch((err: Error) => setError(err.message));
  }, []);

  async function chooseSku(value: string) {
    setSku(value);
    setDetail(await api.sku(value));
  }

  async function act(id: string, kind: "approve" | "dismiss" | "edit", label?: string) {
    setError("");
    try {
      if (kind === "edit") await api.edit(id, label || "");
      if (kind === "approve") await api.approve(id);
      if (kind === "dismiss") await api.dismiss(id);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "That action failed.");
    }
  }

  async function onFile(file: File) {
    setBusy(true);
    setError("");
    try {
      const result = await api.upload(file);
      setUpload(result);
      if (result.classified) await refresh();
      setPage(result.classified ? "metrics" : "upload");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setBusy(false);
    }
  }

  const titles: Record<Page, [string, string]> = {
    metrics: ["Return metrics", "The brief’s rates next to what this file made visible. Colour is the signal."],
    dashboard: ["Return Intelligence", "This file: what was loaded, which SKU to work on, and what still needs Neha."],
    review: ["Review queue", "Work by SKU. Approve, edit, or dismiss. Dismissed rows never enter the counts."],
    upload: ["Upload a returns file", "Other comments only. Live classification runs when both model keys are set."],
  };

  const nav: { id: Page; label: string }[] = [
    { id: "metrics", label: "Return metrics" },
    { id: "dashboard", label: "Command center" },
    { id: "review", label: "Review" },
    { id: "upload", label: "Upload" },
  ];

  const visibleQueue = reviewSku === "all" ? queue : queue.filter((row) => row.sku === reviewSku);

  return (
    <div className="app">
      <aside className="side">
        <div className="brand">
          <div className="mark">ध</div>
          <div>
            <h1>Dhaga</h1>
            <p>Return Intelligence</p>
          </div>
        </div>
        <nav>
          {nav.map((item) => (
            <button key={item.id} className={page === item.id ? "active" : ""} type="button" onClick={() => setPage(item.id)}>
              {item.label}
              {item.id === "review" ? <span className="badge">{queue.length}</span> : null}
            </button>
          ))}
        </nav>
        <p className="side-note">For Neha, Category. Auto-approve files a label. It does not change a size chart or a listing.</p>
      </aside>
      <main className="main">
        <p className="kicker">Internal · sample until a live file is classified</p>
        <h2>{titles[page][0]}</h2>
        <p className="lede">{titles[page][1]}</p>
        {data && page !== "metrics" ? <div className="banner">{data.sample_banner} Auto-approve threshold: {data.auto_approve_pct}%.</div> : null}
        {error ? <div className="error">{error}</div> : null}

        {page === "metrics" && data ? <ColourInsight data={data} /> : null}

        {page === "dashboard" && data ? (
          <CommandCenter
            data={data}
            sku={sku}
            detail={detail}
            onSku={chooseSku}
            onReview={() => setPage("review")}
          />
        ) : null}

        {page === "review" && data ? (
          <ReviewBoard
            data={data}
            queue={visibleQueue}
            reviewSku={reviewSku}
            onSku={setReviewSku}
            onAct={act}
          />
        ) : null}

        {page === "upload" ? (
          <section>
            <div className="drop">
              <div>
                <h3>CSV of Other returns</h3>
                <p className="lede">Columns: return_id, sku, category, vendor, size, return_reason, other_text. A sample lives at data/sample/returns_other.csv.</p>
              </div>
              <label className="file">
                <input type="file" accept=".csv,text/csv" disabled={busy} onChange={(event) => {
                  const file = event.target.files?.[0];
                  if (file) onFile(file);
                }} />
              </label>
            </div>
            {data && !data.models_configured ? (
              <div className="banner">MODEL_A and MODEL_B are not set. Uploading a file will not guess labels. The dashboard you see is the loaded sample.</div>
            ) : null}
            {upload?.agents ? (
              <section className="agents">
                <article className="card agent">
                  <p className="kicker">Agent 1 · done</p>
                  <h3>Intake</h3>
                  <p>Loaded {upload.agents.intake.loaded} comments in {upload.agents.intake.batches} batches of {upload.agents.intake.batch_size}.</p>
                </article>
                <article className="card agent">
                  <p className="kicker">Agent 2 · {upload.agents.review ? "done" : "waiting"}</p>
                  <h3>Review</h3>
                  <p>
                    {upload.agents.review
                      ? `Filed ${upload.agents.review.auto_approved} at ${upload.agents.review.threshold}% or above. Sent ${upload.agents.review.sent_to_neha} to Neha.`
                      : "Did not classify. The dashboard is unchanged."}
                  </p>
                </article>
              </section>
            ) : null}
            {upload ? (
              <article className="card" style={{ marginTop: 14 }}>
                <h3>{upload.message}</h3>
                <table>
                  <tbody>
                    <tr><th>Rows kept</th><td>{upload.kept}</td></tr>
                    {upload.dropped.map((item) => (
                      <tr key={item.reason}><th>{item.reason}</th><td>{item.count}</td></tr>
                    ))}
                  </tbody>
                </table>
                {upload.unclassified.length ? (
                  <ul className="raw">
                    {upload.unclassified.map((row) => (
                      <li key={row.return_id}><strong>{row.sku}</strong> — {row.text || "(empty)"}</li>
                    ))}
                  </ul>
                ) : null}
              </article>
            ) : null}
          </section>
        ) : null}
      </main>
    </div>
  );
}

const AREA_TONE: Record<string, string> = {
  "Fit and size": "rose",
  Quality: "amber",
  Colour: "violet",
  "Copy and look": "blue",
  "Not enough to act": "slate",
  "Not a product issue": "green",
};

function ColourInsight({ data }: { data: Dashboard }) {
  const report = data.insights;
  const cards = [
    { tone: "rose", label: "Return rate · brief", value: "31%", note: "Already on Neha’s desk. This file does not remeasure it." },
    { tone: "amber", label: "Other · brief", value: "44%", note: "The unread bucket. The split below is this file only." },
    { tone: "violet", label: "Labeled on this file", value: `${report.counted_pct}%`, note: `${report.counted} of ${data.total} comments now have a counted label.` },
    { tone: "green", label: "Filed without a click", value: String(data.agents.review.auto_approved), note: `${report.still_with_neha} still with Neha. A filed label does not change a listing.` },
  ];
  return (
    <section className="ink">
      <div className="tones">
        {cards.map((card) => (
          <article className={`tone ${card.tone}`} key={card.label}>
            <span>{card.label}</span>
            <strong>{card.value}</strong>
            <p>{card.note}</p>
          </article>
        ))}
      </div>
      <div className="ink-split">
        <div className="ink-list">
          {report.areas.filter((area) => area.count > 0).map((area) => (
            <div className="ink-row" key={area.title}>
              <span className={`swatch ${AREA_TONE[area.title] || "slate"}`} />
              <div>
                <div className="area-top">
                  <span>{area.title}</span>
                  <strong>{area.count} · {area.share_pct}%</strong>
                </div>
                <div className="track dark"><div className={`fill ${AREA_TONE[area.title] || "slate"}`} style={{ width: `${area.share_pct}%` }} /></div>
                <p className="ink-quiet">{area.actionable ? area.note : "No catalogue action."}</p>
              </div>
            </div>
          ))}
        </div>
        <div className="ink-notes">
          <article className="ink-note">
            <span>Financial impact</span>
            <h3>Not calculated</h3>
            <p>Rupees need a cost per product return from Dhaga. About ₹120 is a COD return-to-origin cost, a different problem.</p>
          </article>
          <article className="ink-note">
            <span>Exchanges and resales</span>
            <h3>Not in this file</h3>
            <p>There is no exchange or resale field, so recovered value is not shown.</p>
          </article>
          <article className="ink-note">
            <span>Trend</span>
            <h3>One snapshot</h3>
            <p>There is no earlier file, so this screen cannot say returns are improving or worsening. {report.leave_pct}% of counted rows need no catalogue change.</p>
          </article>
        </div>
      </div>
    </section>
  );
}

function CommandCenter({
  data,
  sku,
  detail,
  onSku,
  onReview,
}: {
  data: Dashboard;
  sku: string;
  detail: SkuDetail | null;
  onSku: (sku: string) => void;
  onReview: () => void;
}) {
  const report = data.insights;
  const focus = report.focus;
  return (
    <div className="command">
      <section className="rail" aria-label="This file">
        <div>
          <span>Returns in this file</span>
          <strong>{data.total}</strong>
          <p>Other comments loaded for this run.</p>
        </div>
        <div>
          <span>Counted</span>
          <strong>{data.accepted}</strong>
          <p>Auto-approved, or accepted by Neha.</p>
        </div>
        <div>
          <span>Still open</span>
          <strong>{data.in_review}</strong>
          <p>Under 75%, or no score. Open Review to decide.</p>
        </div>
      </section>

      <section className="split">
        <article className="card">
          <p className="kicker">Which products</p>
          <h3>SKUs with the most counted returns</h3>
          {report.products.length === 0 ? <p className="empty">No counted SKU yet.</p> : null}
          {report.products.map((item) => (
            <button key={item.sku} type="button" className={item.sku === sku ? "sku-row on" : "sku-row"} onClick={() => onSku(item.sku)}>
              <span>
                <strong>{item.sku}</strong>
                <em>{item.vendor} · {item.top_title}</em>
              </span>
              <b>{item.count} · {item.share_pct}%</b>
            </button>
          ))}
          {detail?.top_title ? (
            <div className="sku-detail">
              <div className="action"><strong>Suggested action. </strong>{detail.action}</div>
              {detail.quotes.slice(0, 2).map((quote) => (
                <blockquote key={quote.text}>
                  “{quote.text}”
                  <div className="meta">{quote.label} · {quote.confidence_pct == null ? "No score" : `${quote.confidence_pct}%`}</div>
                </blockquote>
              ))}
            </div>
          ) : null}
        </article>
        <article className="card">
          <p className="kicker">Needs attention</p>
          <h3>{focus ? focus.title : "No cluster yet"}</h3>
          {focus ? (
            <p className="report-line">
              {focus.cluster} comments on {focus.sku}, size {focus.size}, {focus.vendor}, labeled {focus.label}. {focus.action}
            </p>
          ) : <p className="empty">Nothing counted yet.</p>}
          {report.attention.map((item) => (
            <div className="attn" key={`${item.sku}-${item.text}`}>
              <p>“{item.text}”</p>
              <div className="meta">{item.sku} · size {item.size} · {item.why}</div>
            </div>
          ))}
          <button className="primary" type="button" onClick={onReview}>Open review</button>
        </article>
      </section>

      <section className="agents">
        <article className="card agent">
          <p className="kicker">Agent · Intake</p>
          <h3>Loaded the comments</h3>
          <p>{data.agents.intake.detail}</p>
        </article>
        <article className="card agent">
          <p className="kicker">Agent · Review</p>
          <h3>Filed or sent to Neha</h3>
          <p>{data.agents.review.detail} Filing a label does not change a listing.</p>
        </article>
      </section>
    </div>
  );
}

function ReviewBoard({
  data,
  queue,
  reviewSku,
  onSku,
  onAct,
}: {
  data: Dashboard;
  queue: ReviewRow[];
  reviewSku: string;
  onSku: (sku: string) => void;
  onAct: (id: string, kind: "approve" | "dismiss" | "edit", label?: string) => Promise<void>;
}) {
  const board = data.insights.sku_board;
  const auto = data.agents.review.auto_approved;
  const open = data.in_review;
  return (
    <div className="review-board">
      <section className="rail" aria-label="Review status">
        <div>
          <span>Auto-approved</span>
          <strong>{auto}</strong>
          <p>Filed at {data.auto_approve_pct}% or above. Already on the counts.</p>
        </div>
        <div>
          <span>Still open</span>
          <strong>{open}</strong>
          <p>{data.insights.low_confidence} under 75%, {data.insights.no_score} with no score.</p>
        </div>
        <div>
          <span>Showing now</span>
          <strong>{queue.length}</strong>
          <p>{reviewSku === "all" ? "All open rows." : `Only ${reviewSku}.`}</p>
        </div>
      </section>

      <section className="sku-board">
        <button type="button" className={reviewSku === "all" ? "sku-card on" : "sku-card"} onClick={() => onSku("all")}>
          <span className="kicker">All SKUs</span>
          <h3>Whole queue</h3>
          <div className="sku-stats">
            <div><b>{auto}</b><em>auto-approved</em></div>
            <div><b>{open}</b><em>still open</em></div>
          </div>
        </button>
        {board.map((item) => (
          <button
            key={item.sku}
            type="button"
            className={reviewSku === item.sku ? "sku-card on" : "sku-card"}
            onClick={() => onSku(item.sku)}
          >
            <span className="kicker">{item.vendor}</span>
            <h3>{item.sku}</h3>
            <div className="sku-stats">
              <div><b>{item.auto_approved}</b><em>auto-approved</em></div>
              <div><b>{item.open}</b><em>still open</em></div>
            </div>
            {item.open > 0 ? <p className="quiet">Needs Neha on this SKU.</p> : <p className="quiet">Clear for this SKU.</p>}
          </button>
        ))}
      </section>

      <section className="stack">
        {queue.length === 0 ? <p className="empty">Review is clear for this filter. Every remaining label is already counted.</p> : null}
        {queue.map((row) => (
          <ReviewCard key={row.id} row={row} options={data.label_options} onAct={onAct} />
        ))}
      </section>
    </div>
  );
}

function ReviewCard({
  row,
  options,
  onAct,
}: {
  row: ReviewRow;
  options: { label: string; title: string }[];
  onAct: (id: string, kind: "approve" | "dismiss" | "edit", label?: string) => Promise<void>;
}) {
  const [label, setLabel] = useState(row.label || "insufficient_evidence");
  const needsLabel = row.label == null;
  return (
    <article className="card review">
      <header>
        <div>
          <p className="quote">“{row.other_text}”</p>
          <div className="pills">
            <span className="pill">{row.sku}</span>
            <span className="pill">Size {row.size}</span>
            <span className="pill">{row.vendor}</span>
          </div>
        </div>
        <div>{row.confidence_pct == null ? "No score" : `Confidence ${row.confidence_pct}%`}</div>
      </header>
      <p className="warn">{row.short_reason}</p>
      <div className="actions">
        <button className="primary" type="button" disabled={needsLabel} onClick={() => onAct(row.id, "approve")}>Approve</button>
        <select aria-label="Edit label" value={label} onChange={(event) => setLabel(event.target.value)}>
          {options.map((option) => <option key={option.label} value={option.label}>{option.title}</option>)}
        </select>
        <button type="button" onClick={() => onAct(row.id, "edit", label)}>Save edit</button>
        <button className="danger" type="button" onClick={() => onAct(row.id, "dismiss")}>Dismiss</button>
      </div>
    </article>
  );
}
