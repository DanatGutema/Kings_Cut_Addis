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
  media_type?: "photo" | "video" | null;
  media_url?: string | null;
  recipients_total: number;
  telegram_sent: number;
  telegram_failed: number;
};

type Recipient = {
  id: string;
  customer_id: string;
  telegram_sent: boolean;
  delivered: boolean;
  delivered_at?: string | null;
  customer_name?: string | null;
  customer_phone?: string | null;
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
  const [mediaFile, setMediaFile] = useState<File | null>(null);
  const [selectedPromo, setSelectedPromo] = useState<Promo | null>(null);
  const [recipients, setRecipients] = useState<Recipient[]>([]);
  const [recipientsLoading, setRecipientsLoading] = useState(false);
  const [retryingId, setRetryingId] = useState<string | null>(null);

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
    setMediaFile(null);
    setError(null);
    setMessage(null);
  }

  function cancelEdit() {
    setEditingId(null);
    setForm(emptyForm());
    setMediaFile(null);
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
      let promoId = editingId;
      if (editingId) {
        const existing = rows.find((p) => p.id === editingId);
        await api.updatePromotion(editingId, buildPayload(existing?.is_active ?? true));
      } else {
        const created = await api.createPromotion(buildPayload(true));
        promoId = created.id;
      }
      if (mediaFile && promoId) {
        await api.uploadPromotionMedia(promoId, mediaFile);
      }
      setMessage(editingId ? "Promotion updated" : "Promotion created");
      cancelEdit();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : editingId ? "Update failed" : "Create failed");
    }
  }

  async function onRemoveMedia(id: string) {
    setError(null);
    setMessage(null);
    try {
      await api.deletePromotionMedia(id);
      setMessage("Media removed");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Remove media failed");
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
      if (selectedPromo?.id === promo.id) {
        setSelectedPromo(null);
        setRecipients([]);
      }
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    }
  }

  async function onBroadcast(id: string) {
    setError(null);
    setMessage(null);
    try {
      const res = await api.broadcastPromotion(id, {});
      setMessage(
        `Broadcast done: ${res.telegram_sent} sent / ${res.telegram_failed} failed of ${res.recipients_total}`,
      );
      const data = await api.promotions();
      setRows(data.items);
      if (selectedPromo?.id === id) {
        const updated = data.items.find((p) => p.id === id);
        if (updated) await openDelivery(updated);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Broadcast failed");
    }
  }

  async function openDelivery(promo: Promo) {
    setSelectedPromo(promo);
    setRecipientsLoading(true);
    setError(null);
    try {
      const data = await api.promotionRecipients(promo.id);
      setRecipients(data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load recipients");
      setRecipients([]);
    } finally {
      setRecipientsLoading(false);
    }
  }

  async function onRetryRecipient(recipient: Recipient) {
    if (!selectedPromo) return;
    setError(null);
    setMessage(null);
    setRetryingId(recipient.id);
    try {
      await api.retryPromotionRecipient(selectedPromo.id, recipient.id);
      setMessage(`Retry sent to ${recipient.customer_name || "customer"}`);
      const data = await api.promotions();
      setRows(data.items);
      const updated = data.items.find((p) => p.id === selectedPromo.id);
      if (updated) await openDelivery(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Retry failed");
      // Refresh so status stays accurate if Telegram failed again
      try {
        const data = await api.promotions();
        setRows(data.items);
        const updated = data.items.find((p) => p.id === selectedPromo.id);
        if (updated) await openDelivery(updated);
      } catch {
        /* ignore refresh errors */
      }
    } finally {
      setRetryingId(null);
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
        <label>
          Photo or video (optional)
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp,video/mp4"
            onChange={(e) => setMediaFile(e.target.files?.[0] || null)}
          />
        </label>
        {mediaFile && (
          <p className="muted">Selected: {mediaFile.name}</p>
        )}
        {editingId && rows.find((p) => p.id === editingId)?.media_url && (
          <div className="toolbar">
            <p className="muted" style={{ margin: 0 }}>
              Current media: {rows.find((p) => p.id === editingId)?.media_type}
            </p>
            <button type="button" className="ghost-btn" onClick={() => onRemoveMedia(editingId)}>
              Remove media
            </button>
          </div>
        )}
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
              <th>Media</th>
              <th>Title</th>
              <th>Discount</th>
              <th>Dates</th>
              <th>Delivery</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((p) => (
              <tr key={p.id}>
                <td>
                  {p.media_url ? (
                    p.media_type === "video" ? (
                      <video
                        src={p.media_url}
                        style={{ width: 64, height: 48, objectFit: "cover", borderRadius: 6 }}
                        muted
                      />
                    ) : (
                      <img
                        src={p.media_url}
                        alt=""
                        style={{ width: 64, height: 48, objectFit: "cover", borderRadius: 6 }}
                      />
                    )
                  ) : (
                    <span className="muted">—</span>
                  )}
                </td>
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
                  {p.recipients_total > 0 ? (
                    <button
                      type="button"
                      className="ghost-btn"
                      onClick={() => openDelivery(p)}
                      title="View recipient delivery details"
                    >
                      <span className="ok-text">{p.telegram_sent} sent</span>
                      {" / "}
                      <span className="error-text">{p.telegram_failed} failed</span>
                    </button>
                  ) : (
                    <span className="muted">Not broadcast</span>
                  )}
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

      {selectedPromo && (
        <div className="panel" style={{ marginTop: "1rem" }}>
          <div className="page-head" style={{ marginBottom: "0.75rem" }}>
            <div>
              <h2>Delivery — {selectedPromo.title}</h2>
              <p className="muted">
                {selectedPromo.telegram_sent} sent · {selectedPromo.telegram_failed} failed ·{" "}
                {selectedPromo.recipients_total} total
              </p>
            </div>
            <button
              type="button"
              className="ghost-btn"
              onClick={() => {
                setSelectedPromo(null);
                setRecipients([]);
              }}
            >
              Close
            </button>
          </div>

          {recipientsLoading ? (
            <p className="muted">Loading recipients…</p>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Customer</th>
                    <th>Phone</th>
                    <th>Delivery</th>
                    <th>Delivered at</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {recipients.map((r) => {
                    const ok = r.telegram_sent || r.delivered;
                    return (
                      <tr key={r.id}>
                        <td>{r.customer_name || r.customer_id.slice(0, 8) + "…"}</td>
                        <td>{r.customer_phone || "—"}</td>
                        <td>
                          {ok ? (
                            <span className="ok-text">Delivered</span>
                          ) : (
                            <span className="error-text">Failed</span>
                          )}
                        </td>
                        <td>
                          {r.delivered_at
                            ? new Date(r.delivered_at).toLocaleString()
                            : "—"}
                        </td>
                        <td>
                          {!ok && (
                            <button
                              type="button"
                              className="ghost-btn"
                              disabled={retryingId === r.id}
                              onClick={() => void onRetryRecipient(r)}
                            >
                              {retryingId === r.id ? "Retrying…" : "Retry"}
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                  {!recipients.length && (
                    <tr>
                      <td colSpan={5} className="muted">
                        No recipients for this promotion.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
