import { FormEvent, useEffect, useState } from "react";
import { api } from "../api/client";

type CustomerRow = {
  id: string;
  first_name: string;
  last_name?: string | null;
  phone_number: string;
  total_visits: number;
  total_spending: number;
  loyalty_status: string;
  last_visit_date?: string | null;
  is_active: boolean;
};

export default function CustomersPage() {
  const [rows, setRows] = useState<CustomerRow[]>([]);
  const [search, setSearch] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [phone, setPhone] = useState("");

  async function load(q = search) {
    try {
      const data = await api.customers({ search: q || undefined, limit: 100 });
      setRows(data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load");
    }
  }

  useEffect(() => {
    void load();
  }, []);

  useEffect(() => {
    const t = setTimeout(() => void load(search), 300);
    return () => clearTimeout(t);
  }, [search]);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setMessage(null);
    try {
      await api.createCustomer({
        first_name: firstName.trim(),
        last_name: lastName.trim() || undefined,
        phone_number: phone.trim(),
      });
      setFirstName("");
      setLastName("");
      setPhone("");
      setMessage("Customer created");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Create failed");
    }
  }

  async function onDeactivate(customer: CustomerRow) {
    if (
      !confirm(
        `Deactivate ${customer.first_name} ${customer.last_name || ""}? They will not be usable for check-in until reactivated.`,
      )
    ) {
      return;
    }
    setError(null);
    setMessage(null);
    try {
      await api.deactivateCustomer(customer.id);
      setMessage("Customer deactivated");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Deactivate failed");
    }
  }

  async function onActivate(customer: CustomerRow) {
    setError(null);
    setMessage(null);
    try {
      await api.activateCustomer(customer.id);
      setMessage("Customer activated");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Activate failed");
    }
  }

  async function onDelete(customer: CustomerRow) {
    if (
      !confirm(
        `Permanently delete ${customer.first_name} ${customer.last_name || ""}? ` +
          "This only works if they have no visits, rewards, orders, or message history.",
      )
    ) {
      return;
    }
    setError(null);
    setMessage(null);
    try {
      await api.deleteCustomer(customer.id);
      setMessage("Customer deleted");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    }
  }

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <h1>Customers</h1>
          <p className="muted">Search directory and register walk-ins</p>
        </div>
      </header>

      <div className="toolbar">
        <input
          placeholder="Search name or phone"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <form className="panel form-grid compact" onSubmit={onCreate}>
        <h2>Add customer</h2>
        <div className="inline-fields">
          <input placeholder="First name" value={firstName} onChange={(e) => setFirstName(e.target.value)} required />
          <input placeholder="Last name" value={lastName} onChange={(e) => setLastName(e.target.value)} />
          <input placeholder="Phone" value={phone} onChange={(e) => setPhone(e.target.value)} required />
          <button type="submit">Save</button>
        </div>
      </form>

      {error && <p className="error-text">{error}</p>}
      {message && <p className="ok-text">{message}</p>}

      <div className="table-wrap panel">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Phone</th>
              <th>Visits</th>
              <th>Spending</th>
              <th>Tier</th>
              <th>Last visit</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((c) => (
              <tr key={c.id}>
                <td>
                  {c.first_name} {c.last_name || ""}
                </td>
                <td>{c.phone_number}</td>
                <td>{c.total_visits}</td>
                <td>{Number(c.total_spending).toLocaleString()}</td>
                <td>{c.loyalty_status}</td>
                <td>{c.last_visit_date || "—"}</td>
                <td>
                  <span className={c.is_active ? "ok-text" : "error-text"}>
                    {c.is_active ? "Active" : "Inactive"}
                  </span>
                </td>
                <td>
                  <div className="row-actions">
                    {c.is_active ? (
                      <button
                        type="button"
                        className="ghost-btn btn-danger"
                        onClick={() => onDeactivate(c)}
                      >
                        Deactivate
                      </button>
                    ) : (
                      <>
                        <button
                          type="button"
                          className="ghost-btn btn-ok"
                          onClick={() => onActivate(c)}
                        >
                          Activate
                        </button>
                        <button
                          type="button"
                          className="ghost-btn btn-danger"
                          onClick={() => onDelete(c)}
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
