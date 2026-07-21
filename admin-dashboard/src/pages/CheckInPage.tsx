import { FormEvent, useState } from "react";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";

type CheckInResult = {
  customer_id: string;
  first_name: string;
  last_name?: string | null;
  phone_number: string;
  total_visits: number;
  total_spending: number;
  loyalty_status: string;
  is_new_customer: boolean;
};

export default function CheckInPage() {
  const { staff } = useAuth();
  const [mode, setMode] = useState<"qr" | "phone">("qr");
  const [qrToken, setQrToken] = useState("");
  const [phone, setPhone] = useState("");
  const [firstName, setFirstName] = useState("");
  const [result, setResult] = useState<CheckInResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!staff) return;
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const data =
        mode === "qr"
          ? await api.checkinQr(qrToken.trim(), staff.id)
          : await api.checkinPhone({
              phone_number: phone.trim(),
              staff_id: staff.id,
              first_name: firstName.trim() || undefined,
            });
      setResult(data as CheckInResult);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Check-in failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <h1>Check-in</h1>
          <p className="muted">Scan QR from Mini App or look up by phone</p>
        </div>
      </header>

      <div className="tabs">
        <button type="button" className={mode === "qr" ? "active" : ""} onClick={() => setMode("qr")}>
          QR token
        </button>
        <button
          type="button"
          className={mode === "phone" ? "active" : ""}
          onClick={() => setMode("phone")}
        >
          Phone
        </button>
      </div>

      <form className="panel form-grid" onSubmit={onSubmit}>
        {mode === "qr" ? (
          <label>
            QR token (UUID from customer Mini App)
            <input value={qrToken} onChange={(e) => setQrToken(e.target.value)} required />
          </label>
        ) : (
          <>
            <label>
              Phone number
              <input value={phone} onChange={(e) => setPhone(e.target.value)} required />
            </label>
            <label>
              First name (only if registering new)
              <input value={firstName} onChange={(e) => setFirstName(e.target.value)} />
            </label>
          </>
        )}
        {error && <p className="error-text">{error}</p>}
        <button type="submit" disabled={busy}>
          {busy ? "Looking up…" : "Check in"}
        </button>
      </form>

      {result && (
        <section className="panel result-card">
          <h2>
            {result.first_name} {result.last_name || ""}
          </h2>
          <p>
            {result.phone_number} · {result.loyalty_status}
          </p>
          <p>
            Visits: {result.total_visits} · Spend: {Number(result.total_spending).toLocaleString()}{" "}
            ETB
          </p>
          <p className="muted">
            Customer ID: {result.customer_id}
            {result.is_new_customer ? " · New customer created" : ""}
          </p>
          <p className="muted">Next: open Visits and log services for this customer.</p>
        </section>
      )}
    </div>
  );
}
