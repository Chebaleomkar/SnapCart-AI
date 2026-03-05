/**
 * API client for SnapCartAI backend
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Auth ──────────────────────────────────────────────────────────────

export async function getAuthStatus() {
  const res = await fetch(`${API_BASE}/api/auth/status`);
  return res.json();
}

export async function getAuthLoginUrl() {
  const res = await fetch(`${API_BASE}/api/auth/login`);
  return res.json();
}

export async function logout() {
  const res = await fetch(`${API_BASE}/api/auth/logout`);
  return res.json();
}

// ── Pipeline ──────────────────────────────────────────────────────────

export interface PipelineResult {
  url: string;
  steps: Record<string, unknown>;
  final_result: {
    dish_name: string;
    cuisine: string;
    servings: string;
    ingredients: Ingredient[];
    notes: string;
    cart_summary: CartSummary;
    cart_items: CartItem[];
  } | null;
  error: string | null;
  timing: Record<string, number>;
}

export interface Ingredient {
  name: string;
  quantity: string;
  category: string;
}

export interface CartSummary {
  total: number;
  added_to_cart: number;
  searched: number;
  fallback_urls: number;
  mcp_connected: boolean;
  combined_search_url: string;
}

export interface CartItem {
  ingredient: string;
  status: string;
  products: unknown[];
  search_url: string;
  cart_status?: string;
  error?: string;
}

export async function processUrl(url: string): Promise<PipelineResult> {
  const res = await fetch(`${API_BASE}/api/process-url`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail?.message || err.detail || "Pipeline failed");
  }

  return res.json();
}

// ── Health ─────────────────────────────────────────────────────────────

export async function checkHealth() {
  const res = await fetch(`${API_BASE}/api/health`);
  return res.json();
}
