import { useEffect, useState } from "react";
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
};

export default function AppointmentsPage() {
  const [rows, setRows] = useState<Appointment[]>([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  async function load(status = statusFilter) {
    const data = await api.appointments({
      status: status || undefined,
      limit: 100,
    });
    setRows(data.items);
  }

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Load failed"));
  }, []);

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
            Bookings from the Telegram Mini App — completed stay in the list (use the status filter)
          </p>
        </div>
      </header>

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
        <button type="button" className="ghost-btn" onClick={() => load()}>
          Refresh
        </button>
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
                <td colSpan={7} className="muted">
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
