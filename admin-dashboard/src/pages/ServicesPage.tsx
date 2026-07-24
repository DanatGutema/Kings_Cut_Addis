import { FormEvent, useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";

type Service = {
  id: string;
  name: string;
  price: number;
  description?: string | null;
  duration_minutes?: number | null;
  is_active: boolean;
};

type ServiceForm = {
  name: string;
  price: string;
  description: string;
  duration_minutes: string;
};

const emptyForm: ServiceForm = {
  name: "",
  price: "200",
  description: "",
  duration_minutes: "",
};

export default function ServicesPage() {
  const { staff } = useAuth();
  const [rows, setRows] = useState<Service[]>([]);
  const [form, setForm] = useState<ServiceForm>(emptyForm);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function load() {
    const data = await api.services(false);
    setRows(data.items);
  }

  useEffect(() => {
    if (staff && staff.role !== "admin") return;
    load().catch((err) => setError(err instanceof Error ? err.message : "Load failed"));
  }, [staff]);

  if (staff && staff.role !== "admin") return <Navigate to="/" replace />;

  function startEdit(service: Service) {
    setEditingId(service.id);
    setForm({
      name: service.name,
      price: String(service.price),
      description: service.description || "",
      duration_minutes: service.duration_minutes != null ? String(service.duration_minutes) : "",
    });
    setError(null);
    setMessage(null);
  }

  function cancelEdit() {
    setEditingId(null);
    setForm(emptyForm);
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setMessage(null);

    const payload = {
      name: form.name.trim(),
      price: Number(form.price),
      description: form.description.trim() || undefined,
      duration_minutes: form.duration_minutes.trim()
        ? Number(form.duration_minutes)
        : undefined,
    };

    try {
      if (editingId) {
        await api.updateService(editingId, payload);
        setMessage("Service updated");
        cancelEdit();
      } else {
        await api.createService(payload);
        setMessage("Service created");
        setForm(emptyForm);
      }
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : editingId ? "Update failed" : "Create failed");
    }
  }

  async function onDeactivate(id: string) {
    if (!confirm("Deactivate this service? It will no longer appear for new visits.")) return;
    setError(null);
    setMessage(null);
    try {
      await api.deactivateService(id);
      setMessage("Service deactivated");
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
      await api.activateService(id);
      setMessage("Service activated");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Activate failed");
    }
  }

  async function onDelete(service: Service) {
    if (
      !confirm(
        `Permanently delete "${service.name}"? This only works if it was never used in visits or orders.`,
      )
    ) {
      return;
    }
    setError(null);
    setMessage(null);
    try {
      await api.deleteService(service.id);
      setMessage("Service deleted");
      if (editingId === service.id) cancelEdit();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    }
  }

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <h1>Services</h1>
          <p className="muted">Catalog prices for haircut, beard, spa, and more</p>
        </div>
      </header>

      <form className="panel form-grid compact" onSubmit={onSubmit}>
        <h2>{editingId ? "Edit service" : "Add service"}</h2>
        <div className="inline-fields">
          <input
            placeholder="Service name"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            required
          />
          <input
            placeholder="Price ETB"
            type="number"
            min={0}
            step="0.01"
            value={form.price}
            onChange={(e) => setForm({ ...form, price: e.target.value })}
            required
          />
          <input
            placeholder="Duration (min)"
            type="number"
            min={0}
            value={form.duration_minutes}
            onChange={(e) => setForm({ ...form, duration_minutes: e.target.value })}
          />
        </div>
        <input
          placeholder="Description (optional)"
          value={form.description}
          onChange={(e) => setForm({ ...form, description: e.target.value })}
        />
        <div className="toolbar">
          <button type="submit">{editingId ? "Save changes" : "Add"}</button>
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
              <th>Name</th>
              <th>Price</th>
              <th>Duration</th>
              <th>Status</th>
              <th>Description</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((s) => (
              <tr key={s.id}>
                <td>{s.name}</td>
                <td>{Number(s.price).toLocaleString()} ETB</td>
                <td>{s.duration_minutes ? `${s.duration_minutes} min` : "—"}</td>
                <td>
                  <span className={s.is_active ? "ok-text" : "error-text"}>
                    {s.is_active ? "Active" : "Inactive"}
                  </span>
                </td>
                <td>{s.description}</td>
                <td>
                  <div className="row-actions">
                    <button type="button" className="ghost-btn" onClick={() => startEdit(s)}>
                      Edit
                    </button>
                    {s.is_active ? (
                      <button
                        type="button"
                        className="ghost-btn btn-danger"
                        onClick={() => onDeactivate(s.id)}
                      >
                        Deactivate
                      </button>
                    ) : (
                      <>
                        <button
                          type="button"
                          className="ghost-btn btn-ok"
                          onClick={() => onActivate(s.id)}
                        >
                          Activate
                        </button>
                        <button
                          type="button"
                          className="ghost-btn btn-danger"
                          onClick={() => onDelete(s)}
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
