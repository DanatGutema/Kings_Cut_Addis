import { useEffect, useState } from "react";
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
  phone_number: string 
};

export default function RewardsPage() {
  const [rows, setRows] = useState<Reward[]>([]);
  const [status, setStatus] = useState("pending");
  const [error, setError] = useState<string | null>(null);
  const [customers, setCustomers] = useState<Customer[]>([]);

  // async function load(nextStatus = status) {
  //   const data = await api.rewards({ status: nextStatus || undefined });
  //   setRows(data.items);
  // }


  const customerMap = Object.fromEntries(
    customers.map((c) => [c.id, `${c.first_name} ${c.last_name || ""}`])
  );


  async function load(nextStatus = status) {
    const [r, c] = await Promise.all([
        api.rewards({ status: nextStatus || undefined }),
        api.customers({ limit: 200 }),
    ]);
    setRows(r.items);
    setCustomers(c.items);
  }

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Load failed"));
  }, []);

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
            setStatus(e.target.value);
            load(e.target.value).catch((err) => setError(String(err)));
          }}
        >
          <option value="pending">Pending</option>
          <option value="redeemed">Redeemed</option>
          <option value="expired">Expired</option>
          <option value="void">Void</option>
          <option value="">All</option>
        </select>
      </header>

      {error && <p className="error-text">{error}</p>}

      <div className="table-wrap panel">
        <table>
          <thead>
            <tr>
              <th>Customer</th>
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
                {/* <td className="mono">{r.customer_id.slice(0, 8)}…</td> */}
                <td>{customerMap[r.customer_id] || r.customer_id.slice(0, 8) + "…"}</td>
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
                            .then(() => load())
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
                            .then(() => load())
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
