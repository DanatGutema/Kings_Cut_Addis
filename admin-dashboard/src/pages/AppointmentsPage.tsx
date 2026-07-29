import { FormEvent, useEffect, useState } from "react";
import { api } from "../api/client";

type Appointment = {
  id: string;
  customer_id: string;
  service_id: string;
  scheduled_at: string;
  notes?: string | null;
  status: "pending" | "accepted" | "rejected" | "completed";
  visit_id?: string | null;
  completed_at?: string | null;
  customer_name?: string | null;
  customer_phone?: string | null;
  service_name?: string | null;
  service_price?: number | null;
  preferred_barber_name?: string | null;
};

type CustomerOption = {
  id: string;
  first_name: string;
  last_name?: string | null;
  phone_number: string;
};

type ServiceOption = { id: string; name: string; price: number };
type BarberOption = {
  id: string;
  first_name: string;
  last_name?: string | null;
  specialty?: string | null;
  is_active: boolean;
};

function toDatetimeLocalValue(d = new Date()) {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

export default function AppointmentsPage() {
  const [rows, setRows] = useState<Appointment[]>([]);
  const [customers, setCustomers] = useState<CustomerOption[]>([]);
  const [services, setServices] = useState<ServiceOption[]>([]);
  const [barbers, setBarbers] = useState<BarberOption[]>([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const [customerId, setCustomerId] = useState("");
  const [serviceId, setServiceId] = useState("");
  const [barberId, setBarberId] = useState("");
  const [scheduledAt, setScheduledAt] = useState(toDatetimeLocalValue());
  const [notes, setNotes] = useState("");

  async function load(status = statusFilter) {
    setError(null);
    try {
      const [appointments, customerData, serviceData] = await Promise.all([
        api.appointments({
          status: status || undefined,
          limit: 100,
        }),
        api.customers({ limit: 200 }),
        api.services(true),
      ]);
      setRows(appointments.items);
      setCustomers(customerData.items);
      setServices(serviceData.items);
      if (!serviceId && serviceData.items[0]) setServiceId(serviceData.items[0].id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Load failed");
    }

    try {
      // All registered barbers; inactive ones shown disabled
      const barberData = await api.listBarbers(false);
      setBarbers(
        [...barberData].sort((a, b) =>
          `${a.first_name} ${a.last_name || ""}`.localeCompare(
            `${b.first_name} ${b.last_name || ""}`,
          ),
        ),
      );
    } catch (err) {
      setBarbers([]);
      setError(err instanceof Error ? err.message : "Failed to load barbers");
    }
  }

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Load failed"));
  }, []);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setMessage(null);
    setSaving(true);
    try {
      await api.createAppointment({
        customer_id: customerId,
        service_id: serviceId,
        scheduled_at: new Date(scheduledAt).toISOString(),
        preferred_barber_id: barberId || undefined,
        notes: notes.trim() || undefined,
      });
      setMessage("Appointment logged (accepted). Mark Completed when the service is done.");
      setNotes("");
      setBarberId("");
      setScheduledAt(toDatetimeLocalValue());
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not log appointment");
    } finally {
      setSaving(false);
    }
  }

  async function runAction(
    id: string,
    action: "accept" | "reject" | "complete",
  ) {
    setError(null);
    setMessage(null);
    setBusyId(id);
    try {
      if (action === "accept") {
        await api.acceptAppointment(id);
        setMessage("Appointment accepted — customer notified");
      } else if (action === "reject") {
        await api.rejectAppointment(id);
        setMessage("Appointment rejected — customer notified");
      } else {
        await api.completeAppointment(id);
        setMessage("Appointment completed — visit logged");
      }
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <h1>Appointments</h1>
          <p className="muted">
            Mini App bookings and phone / walk-in appointments and visits logged by staff
          </p>
        </div>
      </header>

      <form className="panel form-grid" onSubmit={onCreate}>
        <h2>Log appointment and visits</h2>
        <p className="muted">
          For customers who call or book in person. Saved as accepted.  Use Completed when the
          service is finished (creates a visit).
        </p>

        <label>
          Customer
          <select
            value={customerId}
            onChange={(e) => setCustomerId(e.target.value)}
            required
          >
            <option value="" disabled>
              Select customer…
            </option>
            {customers.map((c) => (
              <option key={c.id} value={c.id}>
                {c.first_name} {c.last_name || ""} · {c.phone_number}
              </option>
            ))}
          </select>
        </label>

        <label>
          Service
          <select
            value={serviceId}
            onChange={(e) => setServiceId(e.target.value)}
            required
          >
            {!services.length && (
              <option value="" disabled>
                No active services
              </option>
            )}
            {services.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name} — {Number(s.price).toLocaleString()} ETB
              </option>
            ))}
          </select>
        </label>

        <label>
          Date & time
          <input
            type="datetime-local"
            value={scheduledAt}
            onChange={(e) => setScheduledAt(e.target.value)}
            required
          />
        </label>

        <label>
          Barber
          <select value={barberId} onChange={(e) => setBarberId(e.target.value)}>
            <option value="">Any / not specified</option>
            {barbers.map((b) => (
              <option key={b.id} value={b.id} disabled={!b.is_active}>
                {[b.first_name, b.last_name].filter(Boolean).join(" ")}
                {b.specialty ? ` (${b.specialty})` : ""}
                {!b.is_active ? " — inactive" : ""}
              </option>
            ))}
          </select>
          {!barbers.length && (
            <span className="muted" style={{ display: "block", marginTop: "0.35rem" }}>
              No registered barbers yet. Add them under Staff → Add Barber.
            </span>
          )}
        </label>

        <label>
          Notes
          <input
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Phone booking, preferred style…"
          />
        </label>

        <button type="submit" disabled={saving || !customers.length || !services.length}>
          {saving ? "Saving…" : "Save appointment"}
        </button>
      </form>

      <div className="toolbar">
        <select
          value={statusFilter}
          onChange={(e) => {
            const value = e.target.value;
            setStatusFilter(value);
            load(value).catch((err) =>
              setError(err instanceof Error ? err.message : "Load failed"),
            );
          }}
        >
          <option value="">All statuses</option>
          <option value="pending">Pending</option>
          <option value="accepted">Accepted</option>
          <option value="rejected">Rejected</option>
          <option value="completed">Completed</option>
        </select>
        {/* <button type="button" className="ghost-btn" onClick={() => load()}>
          Refresh
        </button> */}
      </div>

      {error && <p className="error-text">{error}</p>}
      {message && <p className="ok-text">{message}</p>}

      <div className="table-wrap panel">
        <table>
          <thead>
            <tr>
              <th>Booked for</th>
              <th>Customer</th>
              <th>Phone</th>
              <th>Service</th>
              <th>Barber</th>
              <th>Notes</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((a) => (
              <tr key={a.id}>
                <td>{new Date(a.scheduled_at).toLocaleString()}</td>
                <td>{a.customer_name || a.customer_id.slice(0, 8) + "…"}</td>
                <td>{a.customer_phone || "—"}</td>
                <td>
                  {a.service_name || "—"}
                  {a.service_price != null
                    ? ` · ${Number(a.service_price).toLocaleString()} ETB`
                    : ""}
                </td>
                <td>{a.preferred_barber_name || "Any"}</td>
                <td>{a.notes || "—"}</td>
                <td>
                  <span
                    className={
                      a.status === "accepted" || a.status === "completed"
                        ? "ok-text"
                        : a.status === "rejected"
                          ? "error-text"
                          : undefined
                    }
                  >
                    {a.status}
                  </span>
                </td>
                <td>
                  <div className="row-actions">
                    {a.status === "pending" && (
                      <>
                        <button
                          type="button"
                          className="ghost-btn btn-ok"
                          disabled={busyId === a.id}
                          onClick={() => runAction(a.id, "accept")}
                        >
                          Accept
                        </button>
                        <button
                          type="button"
                          className="ghost-btn btn-danger"
                          disabled={busyId === a.id}
                          onClick={() => {
                            if (confirm("Reject this appointment?")) {
                              void runAction(a.id, "reject");
                            }
                          }}
                        >
                          Reject
                        </button>
                      </>
                    )}
                    {a.status === "accepted" && (
                      <button
                        type="button"
                        className="ghost-btn btn-ok"
                        disabled={busyId === a.id}
                        onClick={() => {
                          if (
                            confirm(
                              "Mark completed? This will add a visit with today's completion time.",
                            )
                          ) {
                            void runAction(a.id, "complete");
                          }
                        }}
                      >
                        Completed
                      </button>
                    )}
                    {(a.status === "rejected" || a.status === "completed") && (
                      <span className="muted">—</span>
                    )}
                  </div>
                </td>
              </tr>
            ))}
            {!rows.length && (
              <tr>
                <td colSpan={8} className="muted">
                  No appointments yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
