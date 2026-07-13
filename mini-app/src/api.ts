const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

export type Customer = {
  id: string;
  first_name: string;
  last_name?: string | null;
  phone_number: string;
  total_visits: number;
  total_spending: number | string;
  loyalty_status: string;
  qr_token: string;
};

export type QrPayload = {
  qr_token: string;
  customer_name: string;
  phone_number: string;
};

export type RuleProgress = {
  rule_id: string;
  rule_name: string;
  rule_type: string;
  visit_threshold?: number | null;
  spending_threshold?: number | null;
  current_visits: number;
  current_spending: number | string;
  visits_remaining?: number | null;
  spending_remaining?: number | null;
  pending_rewards: number;
};

export type LoyaltyProgress = {
  customer_id: string;
  total_visits: number;
  total_spending: number | string;
  loyalty_status: string;
  rules: RuleProgress[];
};

export type Reward = {
  id: string;
  reward_type: string;
  reward_percentage?: number | null;
  reward_amount?: number | null;
  earned_date: string;
  expiry_date: string;
  status: string;
};

export type Promotion = {
  id: string;
  title: string;
  description?: string | null;
  discount_type: string;
  discount_value: number | string;
  start_date: string;
  end_date: string;
};

async function request<T>(path: string, options: RequestInit = {}, token?: string): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    let detail = "Request failed";
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* ignore */
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return res.json() as Promise<T>;
}

export function authWithTelegram(initData: string) {
  return request<{ access_token: string; customer: Customer }>("/api/v1/mini-app/auth", {
    method: "POST",
    body: JSON.stringify({ init_data: initData }),
  });
}

export function fetchMe(token: string) {
  return request<Customer>("/api/v1/mini-app/me", {}, token);
}

export function fetchQr(token: string) {
  return request<QrPayload>("/api/v1/mini-app/qr", {}, token);
}

export function fetchLoyalty(token: string) {
  return request<LoyaltyProgress>("/api/v1/mini-app/loyalty-progress", {}, token);
}

export function fetchRewards(token: string) {
  return request<Reward[]>("/api/v1/mini-app/rewards", {}, token);
}

export function fetchPromotions(token: string) {
  return request<Promotion[]>("/api/v1/mini-app/promotions", {}, token);
}
