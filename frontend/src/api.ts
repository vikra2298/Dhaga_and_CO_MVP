export type LabelCount = { label: string; title: string; count: number };
export type LabelOption = { label: string; title: string };

export type Agents = {
  intake: {
    name: string;
    loaded: number;
    batches: number | null;
    batch_size: number;
    detail: string;
  };
  review: {
    name: string;
    auto_approved: number;
    sent_to_neha: number;
    threshold: number;
    detail: string;
  };
  source: string;
};

export type Focus = {
  title: string;
  count: number;
  share_pct: number;
  sku: string;
  vendor: string;
  size: string;
  label: string;
  cluster: number;
  action: string;
};

export type InsightArea = {
  title: string;
  count: number;
  share_pct: number;
  actionable: boolean;
  note: string;
};

export type ProductRank = {
  sku: string;
  vendor: string;
  count: number;
  share_pct: number;
  top_title: string;
};

export type AttentionItem = {
  sku: string;
  size: string;
  vendor: string;
  text: string;
  why: string;
};

export type SkuBoardItem = {
  sku: string;
  vendor: string;
  auto_approved: number;
  open: number;
  counted: number;
};

export type Insights = {
  headline: string;
  counted: number;
  counted_pct: number;
  still_with_neha: number;
  still_pct: number;
  low_confidence: number;
  no_score: number;
  leave_alone: number;
  leave_pct: number;
  areas: InsightArea[];
  products: ProductRank[];
  sku_board: SkuBoardItem[];
  attention: AttentionItem[];
  focus: Focus | null;
  limit: string;
};

export type Dashboard = {
  total: number;
  accepted: number;
  in_review: number;
  dismissed: number;
  labels: LabelCount[];
  skus: string[];
  sample_banner: string;
  models_configured: boolean;
  auto_approve_pct: number;
  label_options: LabelOption[];
  agents: Agents;
  insights: Insights;
};

export type Quote = {
  text: string;
  label: string;
  confidence_pct: number | null;
  auto_approved: boolean;
};

export type SkuDetail = {
  sku: string;
  vendor: string | null;
  top_label: string | null;
  top_title: string | null;
  action: string | null;
  sizes: { size: string; count: number }[];
  quotes: Quote[];
};

export type ReviewRow = {
  id: string;
  sku: string;
  vendor: string;
  size: string;
  other_text: string;
  label: string | null;
  display_label: string | null;
  confidence_pct: number | null;
  short_reason: string;
};

export type UploadResult = {
  classified: boolean;
  message: string;
  kept: number;
  dropped: { reason: string; count: number }[];
  unclassified: { return_id: string; sku: string; text: string }[];
  accepted?: number;
  in_review?: number;
  agents?: {
    intake: { name: string; loaded: number; batches: number; batch_size: number };
    review: { name: string; auto_approved: number; sent_to_neha: number; threshold: number } | null;
  };
};

async function read<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = typeof body.detail === "string" ? body.detail : "The request failed.";
    throw new Error(detail);
  }
  return body as T;
}

export const api = {
  dashboard: () => read<Dashboard>("/api/dashboard"),
  sku: (sku: string) => read<SkuDetail>(`/api/sku/${encodeURIComponent(sku)}`),
  review: () => read<{ rows: ReviewRow[] }>("/api/review"),
  approve: (id: string) => read(`/api/review/${id}/approve`, { method: "POST" }),
  dismiss: (id: string) => read(`/api/review/${id}/dismiss`, { method: "POST" }),
  edit: (id: string, label: string) =>
    read(`/api/review/${id}/edit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ label }),
    }),
  upload: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return read<UploadResult>("/api/upload", { method: "POST", body: form });
  },
};
