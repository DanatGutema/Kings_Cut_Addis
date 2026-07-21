import { FormEvent, useEffect, useState } from "react";
import { api } from "../api/client";

type Service = {
  id: string;
  name: string;
  price: number;
  description?: string | null;
  duration_minutes?: number | null;
  is_active: boolean;
};

export default function ServicesPage() {
  const [rows, setRows] = useState<Service[]>([]);
  const [name, setName] = useState("");
  const [price, setPrice] = useState("200");
  const [error, setError] = useState<string | null>(null);

  async function load() {
    const data = await api.services(false);
    setRows(data.items);
  }

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Load failed"));
  }, []);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.createService({ name: name.trim(), price: Number(price) });
      setName("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Create failed");
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

      <form className="panel form-grid compact" onSubmit={onCreate}>
        <div className="inline-fields">
          <input placeholder="Service name" value={name} onChange={(e) => setName(e.target.value)} required />
          <input
            placeholder="Price ETB"
            type="number"
            min={0}
            step="0.01"
            value={price}
            onChange={(e) => setPrice(e.target.value)}
            required
          />
          <button type="submit">Add</button>
        </div>
      </form>

      {error && <p className="error-text">{error}</p>}

      <div className="table-wrap panel">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Price</th>
              <th>Duration</th>
              <th>Status</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {rows.map((s) => (
              <tr key={s.id}>
                <td>{s.name}</td>
                <td>{Number(s.price).toLocaleString()} ETB</td>
                <td>{s.duration_minutes ? `${s.duration_minutes} min` : "—"}</td>
                <td>{s.is_active ? "Active" : "Inactive"}</td>
                <td>
                  {s.is_active && (
                    <button
                      type="button"
                      className="ghost-btn"
                      onClick={() =>
                        api.deactivateService(s.id).then(load).catch((err) => setError(String(err)))
                      }
                    >
                      Deactivate
                    </button>
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
