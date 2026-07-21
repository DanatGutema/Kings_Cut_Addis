import { FormEvent, useEffect, useState } from "react";
import { api } from "../api/client";

type Promo = {
  id: string;
  title: string;
  description?: string | null;
  discount_type: string;
  discount_value: number;
  start_date: string;
  end_date: string;
  is_active: boolean;
};

export default function PromotionsPage() {
  const [rows, setRows] = useState<Promo[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [form, setForm] = useState({
    title: "",
    description: "",
    discount_type: "percentage",
    discount_value: "10",
    start_date: new Date().toISOString().slice(0, 10),
    end_date: new Date(Date.now() + 7 * 86400000).toISOString().slice(0, 10),
  });

  async function load() {
    const data = await api.promotions();
    setRows(data.items);
  }

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Load failed"));
  }, []);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.createPromotion({
        ...form,
        discount_value: Number(form.discount_value),
        is_active: true,
      });
      setForm((f) => ({ ...f, title: "", description: "" }));
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Create failed");
    }
  }

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <h1>Promotions</h1>
          <p className="muted">Create offers and broadcast via Telegram</p>
        </div>
      </header>

      <form className="panel form-grid" onSubmit={onCreate}>
        <h2>New promotion</h2>
        <label>
          Title
          <input
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
            required
          />
        </label>
        <label>
          Description
          <input
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
          />
        </label>
        <div className="inline-fields">
          <label>
            Discount type
            <select
              value={form.discount_type}
              onChange={(e) => setForm({ ...form, discount_type: e.target.value })}
            >
              <option value="percentage">Percentage</option>
              <option value="fixed">Fixed ETB</option>
            </select>
          </label>
          <label>
            Value
            <input
              type="number"
              value={form.discount_value}
              onChange={(e) => setForm({ ...form, discount_value: e.target.value })}
              required
            />
          </label>
          <label>
            Start
            <input
              type="date"
              value={form.start_date}
              onChange={(e) => setForm({ ...form, start_date: e.target.value })}
              required
            />
          </label>
          <label>
            End
            <input
              type="date"
              value={form.end_date}
              onChange={(e) => setForm({ ...form, end_date: e.target.value })}
              required
            />
          </label>
        </div>
        <button type="submit">Create</button>
      </form>

      {error && <p className="error-text">{error}</p>}
      {message && <p className="ok-text">{message}</p>}

      <div className="table-wrap panel">
        <table>
          <thead>
            <tr>
              <th>Title</th>
              <th>Discount</th>
              <th>Dates</th>
              <th>Active</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {rows.map((p) => (
              <tr key={p.id}>
                <td>{p.title}</td>
                <td>
                  {p.discount_type === "percentage"
                    ? `${p.discount_value}%`
                    : `${p.discount_value} ETB`}
                </td>
                <td>
                  {p.start_date} → {p.end_date}
                </td>
                <td>{p.is_active ? "Yes" : "No"}</td>
                <td>
                  <button
                    type="button"
                    onClick={() =>
                      api
                        .broadcastPromotion(p.id, {})
                        .then((res) => {
                          const r = res as {
                            telegram_sent: number;
                            telegram_failed: number;
                            recipients_total: number;
                          };
                          setMessage(
                            `Broadcast done: ${r.telegram_sent} sent / ${r.telegram_failed} failed of ${r.recipients_total}`,
                          );
                        })
                        .catch((err) => setError(String(err)))
                    }
                  >
                    Broadcast
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
