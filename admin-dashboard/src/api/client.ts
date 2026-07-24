const TOKEN_KEY = "kca_access_token";
const REFRESH_KEY = "kca_refresh_token";

export type Staff = {
  id: string;
  first_name: string;
  last_name?: string | null;
  email: string;
  role: "admin" | "staff";
  phone_number: string;
  is_active: boolean;
};

export type Paginated<T> = {
  items: T[];
  total: number;
  skip: number;
  limit: number;
};

export function getAccessToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setTokens(access: string, refresh: string) {
  localStorage.setItem(TOKEN_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
}

export function clearTokens() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

async function request<T>(path: string, options: RequestInit = {}, auth = true): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };
  if (auth) {
    const token = getAccessToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(path, { ...options, headers });
  if (res.status === 204) return undefined as T;
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
  const type = res.headers.get("content-type") || "";
  if (type.includes("application/json")) return res.json() as Promise<T>;
  return res.blob() as Promise<T>;
}

export const api = {
  login(email: string, password: string) {
    return request<{ access_token: string; refresh_token: string }>(
      "/api/v1/auth/login",
      { method: "POST", body: JSON.stringify({ email, password }) },
      false,
    );
  },
  me() {
    return request<Staff>("/api/v1/auth/me");
  },
  dashboard() {
    return request<{
      total_customers: number;
      visits_today: number;
      active_rewards: number;
      revenue_today: number;
      revenue_this_month: number;
    }>("/api/v1/analytics/dashboard");
  },
  visitTrend(days = 30) {
    return request<{ period: string; visit_count: number }[]>(
      `/api/v1/analytics/visits/trend?days=${days}`,
    );
  },
  revenueByService() {
    return request<{ service_name: string; total_revenue: number; visit_count: number }[]>(
      "/api/v1/analytics/revenue/by-service",
    );
  },
  topCustomers(sortBy: "spending" | "visits" = "spending") {
    return request<
      {
        customer_id: string;
        first_name: string;
        last_name?: string | null;
        total_visits: number;
        total_spending: number;
      }[]
    >(`/api/v1/analytics/customers/top?sort_by=${sortBy}`);
  },
  loyaltyMetrics() {
    return request<{
      rewards_earned: number;
      rewards_redeemed: number;
      rewards_expired: number;
      redemption_rate: number;
      expiry_rate: number;
    }>("/api/v1/analytics/loyalty");
  },
  customers(params: { search?: string; skip?: number; limit?: number } = {}) {
    const q = new URLSearchParams();
    if (params.search) q.set("search", params.search);
    q.set("skip", String(params.skip ?? 0));
    q.set("limit", String(params.limit ?? 50));
    return request<
      Paginated<{
        id: string;
        first_name: string;
        last_name?: string | null;
        phone_number: string;
        total_visits: number;
        total_spending: number;
        loyalty_status: string;
        last_visit_date?: string | null;
      }>
    >(`/api/v1/customers?${q}`);
  },
  createCustomer(body: {
    first_name: string;
    last_name?: string;
    phone_number: string;
    email?: string;
  }) {
    return request("/api/v1/customers", { method: "POST", body: JSON.stringify(body) });
  },
  deleteCustomer(customerId: string) {
    return request<void>(`/api/v1/customers/${customerId}`, { method: "DELETE" });
  },
  services(activeOnly = true) {
    return request<
      Paginated<{
        id: string;
        name: string;
        price: number;
        description?: string | null;
        duration_minutes?: number | null;
        is_active: boolean;
      }>
    >(`/api/v1/services?active_only=${activeOnly}&limit=200`);
  },
  createService(body: { name: string; price: number; description?: string; duration_minutes?: number }) {
    return request("/api/v1/services", { method: "POST", body: JSON.stringify(body) });
  },
  updateService(id: string, body: Record<string, unknown>) {
    return request(`/api/v1/services/${id}`, { method: "PATCH", body: JSON.stringify(body) });
  },
  deactivateService(id: string) {
    return request(`/api/v1/services/${id}/deactivate`, { method: "POST" });
  },
  activateService(id: string) {
    return request(`/api/v1/services/${id}/activate`, { method: "POST" });
  },
  deleteService(id: string) {
    return request<void>(`/api/v1/services/${id}`, { method: "DELETE" });
  },
  visits(params: { skip?: number; limit?: number; customer_id?: string } = {}) {
    const q = new URLSearchParams();
    q.set("skip", String(params.skip ?? 0));
    q.set("limit", String(params.limit ?? 50));
    if (params.customer_id) q.set("customer_id", params.customer_id);
    return request<
      Paginated<{
        id: string;
        customer_id: string;
        staff_id: string;
        visit_date: string;
        total_amount: number;
        notes?: string | null;
      }>
    >(`/api/v1/visits?${q}`);
  },
  createVisit(body: {
    customer_id: string;
    staff_id: string;
    notes?: string;
    services: { service_id: string; quantity: number }[];
  }) {
    return request("/api/v1/visits", { method: "POST", body: JSON.stringify(body) });
  },
  checkinQr(qr_token: string, staff_id: string) {
    return request<{
      customer_id: string;
      first_name: string;
      last_name?: string | null;
      phone_number: string;
      total_visits: number;
      total_spending: number;
      loyalty_status: string;
      is_new_customer: boolean;
    }>("/api/v1/checkin/qr", {
      method: "POST",
      body: JSON.stringify({ qr_token, staff_id }),
    });
  },
  checkinPhone(body: {
    phone_number: string;
    staff_id: string;
    first_name?: string;
    last_name?: string;
  }) {
    return request("/api/v1/checkin/phone", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },
  loyaltyRules() {
    return request<
      Paginated<{
        id: string;
        rule_name: string;
        rule_type: string;
        visit_threshold?: number | null;
        spending_threshold?: number | null;
        reward_type: string;
        reward_percentage?: number | null;
        reward_amount?: number | null;
        expiry_days: number;
        evaluation_period_days?: number | null;
        is_active: boolean;
      }>
    >("/api/v1/loyalty-rules?limit=100");
  },
  createLoyaltyRule(body: Record<string, unknown>) {
    return request("/api/v1/loyalty-rules", { method: "POST", body: JSON.stringify(body) });
  },
  updateLoyaltyRule(id: string, body: Record<string, unknown>) {
    return request(`/api/v1/loyalty-rules/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    });
  },
  deactivateLoyaltyRule(id: string) {
    return request(`/api/v1/loyalty-rules/${id}/deactivate`, { method: "POST" });
  },
  activateLoyaltyRule(id: string) {
    return request(`/api/v1/loyalty-rules/${id}/activate`, { method: "POST" });
  },
  deleteLoyaltyRule(id: string) {
    return request<void>(`/api/v1/loyalty-rules/${id}`, { method: "DELETE" });
  },
  rewards(params: { status?: string; customer_id?: string } = {}) {
    const q = new URLSearchParams({ limit: "100" });
    if (params.status) q.set("status", params.status);
    if (params.customer_id) q.set("customer_id", params.customer_id);
    return request<
      Paginated<{
        id: string;
        customer_id: string;
        reward_type: string;
        reward_percentage?: number | null;
        reward_amount?: number | null;
        earned_date: string;
        expiry_date: string;
        status: string;
      }>
    >(`/api/v1/rewards?${q}`);
  },
  redeemReward(id: string, remarks?: string) {
    return request(`/api/v1/rewards/${id}/redeem`, {
      method: "POST",
      body: JSON.stringify({ remarks }),
    });
  },
  voidReward(id: string, remarks?: string) {
    return request(`/api/v1/rewards/${id}/void`, {
      method: "POST",
      body: JSON.stringify({ remarks }),
    });
  },
  promotions() {
    return request<
      Paginated<{
        id: string;
        title: string;
        description?: string | null;
        discount_type: string;
        discount_value: number;
        start_date: string;
        end_date: string;
        is_active: boolean;
      }>
    >("/api/v1/promotions?limit=100");
  },
  createPromotion(body: Record<string, unknown>) {
    return request("/api/v1/promotions", { method: "POST", body: JSON.stringify(body) });
  },
  updatePromotion(id: string, body: Record<string, unknown>) {
    return request(`/api/v1/promotions/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    });
  },
  deactivatePromotion(id: string) {
    return request(`/api/v1/promotions/${id}/deactivate`, { method: "POST" });
  },
  activatePromotion(id: string) {
    return request(`/api/v1/promotions/${id}/activate`, { method: "POST" });
  },
  deletePromotion(id: string) {
    return request<void>(`/api/v1/promotions/${id}`, { method: "DELETE" });
  },
  broadcastPromotion(id: string, body: Record<string, unknown> = {}) {
    return request(`/api/v1/promotions/${id}/broadcast`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  },


  // Staff management
  async listStaff(): Promise<Staff[]> {
      return request<Staff[]>("/api/v1/staff/");
  },

  async createStaff(data: {
      first_name: string;
      last_name: string;
      phone_number: string;
      email: string;
      role: "admin" | "staff";
  }): Promise<Staff> {
      return request<Staff>("/api/v1/staff/", {
          method: "POST",
          body: JSON.stringify(data),
      });
  },

  async updateStaff(staffId: string, data: Partial<Staff>): Promise<Staff> {
      return request<Staff>(`/api/v1/staff/${staffId}`, {
          method: "PUT",
          body: JSON.stringify(data),
      });
  },

  async deactivateStaff(staffId: string): Promise<void> {
      return request<void>(`/api/v1/staff/${staffId}/deactivate`, {
          method: "POST",
      });
  },

  async activateStaff(staffId: string): Promise<void> {
      return request<void>(`/api/v1/staff/${staffId}/activate`, {
          method: "POST",
      });
  },

  async deleteStaff(staffId: string): Promise<void> {
      return request<void>(`/api/v1/staff/${staffId}`, {
          method: "DELETE",
      });
  },

  async setStaffPassword(token: string, password: string): Promise<void> {
      return request<void>("/api/v1/staff/set-password", {
          method: "POST",
          body: JSON.stringify({ token, password }),
      });
  },

  async downloadExport(kind: "xlsx" | "pdf") {
    const blob = await request<Blob>(`/api/v1/analytics/export/${kind}`);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = kind === "xlsx" ? "kings_cut_report.xlsx" : "kings_cut_summary.pdf";
    a.click();
    URL.revokeObjectURL(url);
  },
};
