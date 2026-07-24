import { FormEvent, useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";

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

type PromoForm = {
  title: string;
  description: string;
  discount_type: string;
  discount_value: string;
  start_date: string;
  end_date: string;
};

function defaultDates(): Pick<PromoForm, "start_date" | "end_date"> {
  return {
    start_date: new Date().toISOString().slice(0, 10),
    end_date: new Date(Date.now() + 7 * 86400000).toISOString().slice(0, 10),
  };
}

const emptyForm = (): PromoForm => ({
  title: "",
  description: "",
  discount_type: "percentage",
  discount_value: "10",
  ...defaultDates(),
});

export default function PromotionsPage() {
  const { staff } = useAuth();
  const [rows, setRows] = useState<Promo[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<PromoForm>(emptyForm);

  async function load() {
    const data = await api.promotions();
    setRows(data.items);
  }

  useEffect(() => {
    if (staff && staff.role !== "admin") return;
    load().catch((err) => setError(err instanceof Error ? err.message : "Load failed"));
  }, [staff]);

  if (staff && staff.role !== "admin") return <Navigate to="/" replace />;

  function startEdit(promo: Promo) {
    setEditingId(promo.id);
    setForm({
      title: promo.title,
      description: promo.description || "",
      discount_type: promo.discount_type,
      discount_value: String(promo.discount_value),
      start_date: promo.start_date.slice(0, 10),
      end_date: promo.end_date.slice(0, 10),
    });
    setError(null);
    setMessage(null);
  }

  function cancelEdit() {
    setEditingId(null);
    setForm(emptyForm());
  }

  function buildPayload(isActive = true): Record<string, unknown> {
    return {
      title: form.title.trim(),
      description: form.description.trim() || undefined,
      discount_type: form.discount_type,
      discount_value: Number(form.discount_value),
      start_date: form.start_date,
      end_date: form.end_date,
      is_active: isActive,
    };
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setMessage(null);
    try {
      if (editingId) {
        const existing = rows.find((p) => p.id === editingId);
        await api.updatePromotion(editingId, buildPayload(existing?.is_active ?? true));
        setMessage("Promotion updated");
        cancelEdit();
      } else {
        await api.createPromotion(buildPayload(true));
        setMessage("Promotion created");
        setForm(emptyForm());
      }
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : editingId ? "Update failed" : "Create failed");
    }
  }

  async function onDeactivate(id: string) {
    if (!confirm("Deactivate this promotion?")) return;
    setError(null);
    setMessage(null);
    try {
      await api.deactivatePromotion(id);
      setMessage("Promotion deactivated");
      if (editingId === id) cancelEdit();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Deactivate failed");
    }
  }

  async function onActivate(id: string) {
    setError(null);
    setMessage(null);
    try {
      await api.activatePromotion(id);
      setMessage("Promotion activated");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Activate failed");
    }
  }

  async function onDelete(promo: Promo) {
    if (
      !confirm(
        `Permanently delete "${promo.title}"? This only works if it was never broadcast to recipients.`,
      )
    ) {
      return;
    }
    setError(null);
    setMessage(null);
    try {
      await api.deletePromotion(promo.id);
      setMessage("Promotion deleted");
      if (editingId === promo.id) cancelEdit();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    }
  }

  async function onBroadcast(id: string) {
    setError(null);
    setMessage(null);
    try {
      const res = (await api.broadcastPromotion(id, {})) as {
        telegram_sent: number;
        telegram_failed: number;
        recipients_total: number;
      };
      setMessage(
        `Broadcast done: ${res.telegram_sent} sent / ${res.telegram_failed} failed of ${res.recipients_total}`,
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Broadcast failed");
    }
  }

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <h1>Promotions</h1>
          <p className="muted">Create offers and broadcast via Telegram (admin)</p>
        </div>
      </header>

      <form className="panel form-grid" onSubmit={onSubmit}>
        <h2>{editingId ? "Edit promotion" : "New promotion"}</h2>
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
        <div className="toolbar">
          <button type="submit">{editingId ? "Save changes" : "Create"}</button>
          {editingId && (
            <button type="button" className="ghost-btn" onClick={cancelEdit}>
              Cancel
            </button>
          )}
        </div>
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
              <th>Status</th>
              <th>Actions</th>
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
                <td>
                  <span className={p.is_active ? "ok-text" : "error-text"}>
                    {p.is_active ? "Active" : "Inactive"}
                  </span>
                </td>
                <td>
                  <div className="row-actions">
                    <button type="button" className="ghost-btn" onClick={() => startEdit(p)}>
                      Edit
                    </button>
                    {p.is_active && (
                      <button type="button" className="ghost-btn" onClick={() => onBroadcast(p.id)}>
                        Broadcast
                      </button>
                    )}
                    {p.is_active ? (
                      <button
                        type="button"
                        className="ghost-btn btn-danger"
                        onClick={() => onDeactivate(p.id)}
                      >
                        Deactivate
                      </button>
                    ) : (
                      <>
                        <button
                          type="button"
                          className="ghost-btn btn-ok"
                          onClick={() => onActivate(p.id)}
                        >
                          Activate
                        </button>
                        <button
                          type="button"
                          className="ghost-btn btn-danger"
                          onClick={() => onDelete(p)}
                        >
                          Delete
                        </button>
                      </>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
