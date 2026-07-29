import { FormEvent, useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";

type Service = { id: string; name: string; price: number };
type Visit = {
  id: string;
  customer_id: string;
  staff_id: string;
  visit_date: string;
  total_amount: number;
  notes?: string | null;
};

type CustomerName = {
  id: string;
  first_name: string;
  last_name?: string | null;
  phone_number: string;
};

export default function VisitsPage() {
  const { staff } = useAuth();
  const [searchParams] = useSearchParams();
  const [visits, setVisits] = useState<Visit[]>([]);
  const [services, setServices] = useState<Service[]>([]);
  const [customerId, setCustomerId] = useState("");
  const [serviceId, setServiceId] = useState("");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [customers, setCustomers] = useState<CustomerName[]>([]);
  const [pendingRewardCount, setPendingRewardCount] = useState<Record<string, number>>({});

  const customerMap = Object.fromEntries(
    customers.map((c) => [c.id, `${c.first_name} ${c.last_name || ""}`.trim()]),
  );

  async function load() {
    const [v, s, c, pending] = await Promise.all([
      api.visits({ limit: 50 }),
      api.services(true),
      api.customers({ limit: 200 }),
      api.rewards({ status: "pending" }),
    ]);
    let list = c.items as CustomerName[];

    const prefillId = searchParams.get("customer_id");
    const prefillName = searchParams.get("customer_name") || "Checked-in customer";
    const prefillPhone = searchParams.get("phone") || "";
    if (prefillId && !list.some((x) => x.id === prefillId)) {
      const parts = prefillName.trim().split(/\s+/);
      list = [
        {
          id: prefillId,
          first_name: parts[0] || prefillName,
          last_name: parts.slice(1).join(" ") || null,
          phone_number: prefillPhone,
        },
        ...list,
      ];
    }

    const counts: Record<string, number> = {};
    for (const reward of pending.items) {
      counts[reward.customer_id] = (counts[reward.customer_id] || 0) + 1;
    }

    setVisits(v.items);
    setServices(s.items);
    setCustomers(list);
    setPendingRewardCount(counts);
    if (!serviceId && s.items[0]) setServiceId(s.items[0].id);
    if (prefillId) setCustomerId(prefillId);
  }

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Load failed"));
  }, [searchParams]);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    if (!staff) return;
    setError(null);
    try {
      await api.createVisit({
        customer_id: customerId.trim(),
        staff_id: staff.id,
        notes: notes.trim() || undefined,
        services: [{ service_id: serviceId, quantity: 1 }],
      });
      setCustomerId("");
      setNotes("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not log visit");
    }
  }

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <h1>Visits</h1>
          <p className="muted">All the completed services are available here. 
            click the rewards to redeem them and apply discount.
          </p>
        </div>
      </header>
{/* 
      <form className="panel form-grid" onSubmit={onCreate}>
        <h2>Log visit</h2>
        <label>
          Customer
          <select value={customerId} onChange={(e) => setCustomerId(e.target.value)} required>
            <option value="" disabled>
              Select customer…
            </option>
            {customers.map((c) => (
              <option key={c.id} value={c.id}>
                {c.first_name} {c.last_name || ""}
                {c.phone_number ? ` · ${c.phone_number}` : ""}
              </option>
            ))}
          </select>
        </label>
        <label>
          Service
          <select value={serviceId} onChange={(e) => setServiceId(e.target.value)} required>
            {services.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name} — {Number(s.price).toLocaleString()} ETB
              </option>
            ))}
          </select>
        </label>
        <label>
          Notes
          <input value={notes} onChange={(e) => setNotes(e.target.value)} />
        </label>
        <button type="submit">Save visit</button>
      </form> */}

      {error && <p className="error-text">{error}</p>}

      <div className="table-wrap panel">
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Customer Name</th>
              <th>Amount</th>
              <th>Notes</th>
              <th>Rewards</th>
            </tr>
          </thead>
          <tbody>
            {visits.map((v) => {
              const count = pendingRewardCount[v.customer_id] || 0;
              return (
                <tr key={v.id}>
                  <td>{new Date(v.visit_date).toLocaleString()}</td>
                  <td>{customerMap[v.customer_id] || v.customer_id.slice(0, 8) + "…"}</td>
                  <td>{Number(v.total_amount).toLocaleString()} ETB</td>
                  <td>{v.notes || "—"}</td>
                  <td>
                    {count > 0 ? (
                      <Link
                        to={`/rewards?customer_id=${encodeURIComponent(v.customer_id)}`}
                        className="ghost-btn"
                        style={{ display: "inline-block", textDecoration: "none" }}
                      >
                        Rewards ({count})
                      </Link>
                    ) : (
                      <span className="muted">—</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
