export type Staff = {
  id: string;
  first_name: string;
  last_name?: string | null;
  email?: string | null;
  role: "admin" | "staff";
  phone_number: string;
  is_active: boolean;
  approval_status?: "pending" | "approved" | "rejected";
};

export type Paginated<T> = {
  items: T[];
  total: number;
  skip: number;
  limit: number;
};

/** Single in-flight refresh so parallel 401s don't race cookie rotation. */
let refreshInFlight: Promise<boolean> | null = null;

async function refreshSession(): Promise<boolean> {
  try {
    const res = await fetch("/api/v1/auth/refresh", {
      method: "POST",
      credentials: "include",
    });
    return res.ok;
  } catch {
    return false;
  }
}

function ensureRefreshed(): Promise<boolean> {
  if (!refreshInFlight) {
    refreshInFlight = refreshSession().finally(() => {
      refreshInFlight = null;
    });
  }
  return refreshInFlight;
}

async function parseError(res: Response): Promise<string> {
  let detail = "Request failed";
  try {
    const body = await res.json();
    detail = body.detail || detail;
  } catch {
    /* ignore */
  }
  return typeof detail === "string" ? detail : JSON.stringify(detail);
}

async function request<T>(path: string, options: RequestInit = {}, auth = true): Promise<T> {
  const isFormData = typeof FormData !== "undefined" && options.body instanceof FormData;
  const headers: Record<string, string> = {
    ...(isFormData ? {} : { "Content-Type": "application/json" }),
    ...(options.headers as Record<string, string> | undefined),
  };
  if (isFormData) {
    delete headers["Content-Type"];
  }

  let res = await fetch(path, {
    ...options,
    headers,
    credentials: "include",
  });

  if (res.status === 401 && auth) {
    const refreshed = await ensureRefreshed();
    if (refreshed) {
      res = await fetch(path, {
        ...options,
        headers,
        credentials: "include",
      });
    } else {
      const detail = await parseError(res);
      if (!window.location.pathname.startsWith("/login")) {
        window.location.assign("/login");
      }
      throw new Error(detail);
    }
  }

  if (res.status === 204) return undefined as T;
  if (!res.ok) {
    throw new Error(await parseError(res));
  }
  const type = res.headers.get("content-type") || "";
  if (type.includes("application/json")) return res.json() as Promise<T>;
  return res.blob() as Promise<T>;
}

export const api = {
  login(identifier: string, password: string) {
    const trimmed = identifier.trim();
    const body = trimmed.includes("@")
      ? { email: trimmed, password }
      : { phone_number: trimmed, password };
    return request<Staff>(
      "/api/v1/auth/login",
      { method: "POST", body: JSON.stringify(body) },
      false,
    );
  },
  registerStaff(body: {
    first_name: string;
    last_name?: string;
    phone_number: string;
    email?: string;
    password: string;
  }) {
    return request<{ message: string; approval_status: string }>(
      "/api/v1/staff/register",
      { method: "POST", body: JSON.stringify(body) },
      false,
    );
  },
  approveStaff(id: string, role: "admin" | "staff" = "staff") {
    return request<Staff>(`/api/v1/staff/${id}/approve`, {
      method: "POST",
      body: JSON.stringify({ role }),
    });
  },
  rejectStaff(id: string) {
    return request<Staff>(`/api/v1/staff/${id}/reject`, { method: "POST" });
  },
  async logout() {
    try {
      await fetch("/api/v1/auth/logout", {
        method: "POST",
        credentials: "include",
      });
    } catch {
      /* ignore network errors on logout */
    }
  },
  me() {
    return request<Staff>("/api/v1/auth/me");
  },
  dashboard() {
    return request<{
      total_customers: number;
      visits_today: number;
      appointment: number;
      active_rewards: number;
      revenue_today: number;
      total_visits: number
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
        last_visit_date?: string | null;
        is_active: boolean;
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
  deactivateCustomer(customerId: string) {
    return request(`/api/v1/customers/${customerId}/deactivate`, { method: "POST" });
  },
  activateCustomer(customerId: string) {
    return request(`/api/v1/customers/${customerId}/activate`, { method: "POST" });
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
  appointments(params: { status?: string; skip?: number; limit?: number } = {}) {
    const q = new URLSearchParams();
    q.set("skip", String(params.skip ?? 0));
    q.set("limit", String(params.limit ?? 100));
    if (params.status) q.set("status", params.status);
    return request<
      Paginated<{
        id: string;
        customer_id: string;
        service_id: string;
        scheduled_at: string;
        notes?: string | null;
        status: "pending" | "accepted" | "rejected" | "completed";
        preferred_barber_id?: string | null;
        preferred_barber_name?: string | null;
        visit_id?: string | null;
        completed_at?: string | null;
        customer_name?: string | null;
        customer_phone?: string | null;
        service_name?: string | null;
        service_price?: number | null;
      }>
    >(`/api/v1/appointments?${q}`);
  },
  createAppointment(body: {
    customer_id: string;
    service_id: string;
    scheduled_at: string;
    preferred_barber_id?: string;
    notes?: string;
  }) {
    return request("/api/v1/appointments", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },
  acceptAppointment(id: string) {
    return request(`/api/v1/appointments/${id}/accept`, { method: "POST" });
  },
  rejectAppointment(id: string) {
    return request(`/api/v1/appointments/${id}/reject`, { method: "POST" });
  },
  completeAppointment(id: string) {
    return request(`/api/v1/appointments/${id}/complete`, { method: "POST" });
  },
  checkinQr(qr_token: string, staff_id: string) {
    return request<{
      customer_id: string;
      first_name: string;
      last_name?: string | null;
      phone_number: string;
      total_visits: number;
      total_spending: number;
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
        media_type?: "photo" | "video" | null;
        media_url?: string | null;
        recipients_total: number;
        telegram_sent: number;
        telegram_failed: number;
      }>
    >("/api/v1/promotions?limit=100");
  },
  createPromotion(body: Record<string, unknown>) {
    return request<{ id: string }>("/api/v1/promotions", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },
  updatePromotion(id: string, body: Record<string, unknown>) {
    return request(`/api/v1/promotions/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    });
  },
  uploadPromotionMedia(id: string, file: File) {
    const form = new FormData();
    form.append("file", file);
    return request(`/api/v1/promotions/${id}/media`, {
      method: "POST",
      body: form,
    });
  },
  deletePromotionMedia(id: string) {
    return request(`/api/v1/promotions/${id}/media`, { method: "DELETE" });
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
    return request<{
      promotion_id: string;
      recipients_total: number;
      telegram_sent: number;
      telegram_failed: number;
      sms_queued: number;
    }>(`/api/v1/promotions/${id}/broadcast`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  },
  promotionRecipients(id: string) {
    return request<
      Paginated<{
        id: string;
        promotion_id: string;
        customer_id: string;
        telegram_sent: boolean;
        sms_sent: boolean;
        delivered: boolean;
        delivered_at?: string | null;
        customer_name?: string | null;
        customer_phone?: string | null;
      }>
    >(`/api/v1/promotions/${id}/recipients?limit=200`);
  },
  retryPromotionRecipient(promotionId: string, recipientId: string) {
    return request<{
      id: string;
      promotion_id: string;
      customer_id: string;
      telegram_sent: boolean;
      sms_sent: boolean;
      delivered: boolean;
      delivered_at?: string | null;
      customer_name?: string | null;
      customer_phone?: string | null;
    }>(`/api/v1/promotions/${promotionId}/recipients/${recipientId}/retry`, {
      method: "POST",
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

  listBarbers(activeOnly = false) {
    const q = activeOnly ? "?active_only=true" : "";
    return request<
      {
        id: string;
        first_name: string;
        last_name?: string | null;
        phone_number: string;
        email?: string | null;
        specialty?: string | null;
        notes?: string | null;
        is_active: boolean;
      }[]
    >(`/api/v1/barbers${q}`);
  },
  createBarber(data: {
    first_name: string;
    last_name?: string;
    phone_number: string;
    email?: string;
    specialty?: string;
    notes?: string;
  }) {
    return request(`/api/v1/barbers`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },
  deactivateBarber(id: string) {
    return request(`/api/v1/barbers/${id}/deactivate`, { method: "POST" });
  },
  activateBarber(id: string) {
    return request(`/api/v1/barbers/${id}/activate`, { method: "POST" });
  },
  deleteBarber(id: string) {
    return request<void>(`/api/v1/barbers/${id}`, { method: "DELETE" });
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
