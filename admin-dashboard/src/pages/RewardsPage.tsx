import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../api/client";

type Reward = {
  id: string;
  customer_id: string;
  reward_type: string;
  reward_percentage?: number | null;
  reward_amount?: number | null;
  earned_date: string;
  expiry_date: string;
  status: string;
};

type Customer = {
  id: string;
  first_name: string;
  last_name?: string | null;
  phone_number: string;
};

export default function RewardsPage() {
  const [searchParams] = useSearchParams();
  const [rows, setRows] = useState<Reward[]>([]);
  const [status, setStatus] = useState("pending");
  const [error, setError] = useState<string | null>(null);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [searchPhone, setSearchPhone] = useState("");
  const [selectedCustomerId, setSelectedCustomerId] = useState<string | null>(null);
  const [loyalty, setLoyalty] = useState<{
    rewards_earned: number;
    rewards_redeemed: number;
    rewards_expired: number;
    redemption_rate: number;
    expiry_rate: number;
  } | null>(null);

  const customerMap = Object.fromEntries(
    customers.map((c) => [c.id, `${c.first_name} ${c.last_name || ""}`]),
  );

  const phoneMap = Object.fromEntries(customers.map((c) => [c.id, c.phone_number]));

  async function load(nextStatus = status, customerId?: string | null) {
    const params: { status?: string; customer_id?: string } = {};
    if (nextStatus) params.status = nextStatus;
    if (customerId) params.customer_id = customerId;

    const [r, c, l] = await Promise.all([
      api.rewards(params),
      api.customers({ limit: 200 }),
      api.loyaltyMetrics(),
    ]);
    setRows(r.items);
    setCustomers(c.items);
    setLoyalty(l);
  }

  async function handleSearch() {
    if (!searchPhone.trim()) return;
    setError(null);
    try {
      const result = await api.customers({ search: searchPhone.trim(), limit: 1 });
      if (result.items.length === 0) {
        setError("No customer found with that phone number");
        setSelectedCustomerId(null);
        return;
      }
      setSelectedCustomerId(result.items[0].id);
      await load(status, result.items[0].id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    }
  }

  function handleClear() {
    setSearchPhone("");
    setSelectedCustomerId(null);
    load(status, null).catch((err) => setError(String(err)));
  }

  useEffect(() => {
    const fromVisit = searchParams.get("customer_id");
    if (fromVisit) {
      setSelectedCustomerId(fromVisit);
      setStatus("pending");
      load("pending", fromVisit).catch((err) =>
        setError(err instanceof Error ? err.message : "Load failed"),
      );
      return;
    }
    load().catch((err) => setError(err instanceof Error ? err.message : "Load failed"));
  }, [searchParams]);

  useEffect(() => {
    if (!selectedCustomerId || customers.length === 0) return;
    const phone = phoneMap[selectedCustomerId];
    if (phone && !searchPhone) setSearchPhone(phone);
  }, [selectedCustomerId, customers]);

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <h1>Rewards</h1>
          <p className="muted">Redeem or void pending rewards at the chair</p>
        </div>
        <select
          value={status}
          onChange={(e) => {
            const next = e.target.value;
            setStatus(next);
            load(next, selectedCustomerId).catch((err) => setError(String(err)));
          }}
        >
          <option value="pending">Pending</option>
          <option value="redeemed">Redeemed</option>
          <option value="expired">Expired</option>
          <option value="void">Void</option>
          <option value="">All</option>
        </select>
      </header>

      <div className="panel" style={{ marginBottom: "1rem" }}>
        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
          <input
            value={searchPhone}
            onChange={(e) => setSearchPhone(e.target.value)}
            placeholder="Search by phone number…"
            style={{ flex: 1 }}
          />
          <button type="button" onClick={handleSearch}>
            Search
          </button>
          {selectedCustomerId && (
            <button type="button" className="ghost-btn" onClick={handleClear}>
              Clear
            </button>
          )}
        </div>
        {selectedCustomerId && (
          <p className="muted" style={{ marginTop: "0.25rem" }}>
            Showing rewards for{" "}
            <strong>{customerMap[selectedCustomerId] || "this customer"}</strong> only
          </p>
        )}
      </div>

      {loyalty && (
        <div className="metric-grid">
          <article className="metric">
            <span>Rewards earned</span>
            <strong>{loyalty.rewards_earned}</strong>
          </article>
          <article className="metric">
            <span>Redeemed</span>
            <strong>{loyalty.rewards_redeemed}</strong>
          </article>
          <article className="metric">
            <span>Expired</span>
            <strong>{loyalty.rewards_expired}</strong>
          </article>
          <article className="metric">
            <span>Redemption rate</span>
            <strong>{(loyalty.redemption_rate * 100).toFixed(1)}%</strong>
          </article>
        </div>
      )}
      {error && <p className="error-text">{error}</p>}
      {selectedCustomerId && rows.length === 0 && !error && (
        <p className="muted">This customer has no {status || "pending"} rewards.</p>
      )}

      <div className="table-wrap panel">
        <table>
          <thead>
            <tr>
              <th>Customer</th>
              <th>Phone</th>
              <th>Reward</th>
              <th>Earned</th>
              <th>Expires</th>
              <th>Status</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id}>
                <td>{customerMap[r.customer_id] || r.customer_id.slice(0, 8) + "…"}</td>
                <td className="mono">{phoneMap[r.customer_id] || "\u2014"}</td>
                <td>
                  {r.reward_type}
                  {r.reward_percentage != null ? ` ${r.reward_percentage}%` : ""}
                  {r.reward_amount != null ? ` ${r.reward_amount} ETB` : ""}
                </td>
                <td>{r.earned_date}</td>
                <td>{r.expiry_date}</td>
                <td>{r.status}</td>
                <td className="row-actions">
                  {r.status === "pending" && (
                    <>
                      <button
                        type="button"
                        onClick={() =>
                          api
                            .redeemReward(r.id, "Redeemed at shop")
                            .then(() => load(status, selectedCustomerId))
                            .catch((err) => setError(String(err)))
                        }
                      >
                        Redeem
                      </button>
                      <button
                        type="button"
                        className="ghost-btn"
                        onClick={() =>
                          api
                            .voidReward(r.id, "Voided by staff")
                            .then(() => load(status, selectedCustomerId))
                            .catch((err) => setError(String(err)))
                        }
                      >
                        Void
                      </button>
                    </>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
