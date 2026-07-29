import { FormEvent, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";

export default function RegisterPage() {
  const { staff, loading } = useAuth();
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    phone_number: "",
    email: "",
    password: "",
    confirm: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (!loading && staff) return <Navigate to="/" replace />;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setDone(null);

    if (form.password !== form.confirm) {
      setError("Passwords do not match");
      return;
    }
    if (form.password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }

    setBusy(true);
    try {
      const res = await api.registerStaff({
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim() || undefined,
        phone_number: form.phone_number.trim(),
        email: form.email.trim() || undefined,
        password: form.password,
      });
      setDone(res.message);
      setForm({
        first_name: "",
        last_name: "",
        phone_number: "",
        email: "",
        password: "",
        confirm: "",
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-stage">
      <div className="auth-stage__glow" aria-hidden />
      <form className="auth-card" onSubmit={onSubmit}>
        <p className="auth-card__brand">Kings Cut Addis</p>
        <h1>Join the team</h1>
        <p className="auth-card__lead">
         An Admin must approve you before you can
          sign in.
        </p>

        {done ? (
          <div className="auth-success">
            <strong>Request sent</strong>
            <p>{done}</p>
            <Link to="/login" className="auth-link">
              Back to sign in
            </Link>
          </div>
        ) : (
          <>
            <div className="auth-grid">
              <label>
                First name
                <input
                  value={form.first_name}
                  onChange={(e) => setForm({ ...form, first_name: e.target.value })}
                  required
                  autoComplete="given-name"
                />
              </label>
              <label>
                Last name
                <input
                  value={form.last_name}
                  onChange={(e) => setForm({ ...form, last_name: e.target.value })}
                  autoComplete="family-name"
                />
              </label>
            </div>

            <label>
              Phone number
              <input
                type="tel"
                value={form.phone_number}
                onChange={(e) => setForm({ ...form, phone_number: e.target.value })}
                required
                placeholder="09xxxxxxxx"
                autoComplete="tel"
              />
            </label>

            <label>
              Email <span className="auth-optional">(optional)</span>
              <input
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                placeholder="If you have one"
                autoComplete="email"
              />
            </label>

            <div className="auth-grid">
              <label>
                Password
                <input
                  type="password"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  required
                  minLength={8}
                  autoComplete="new-password"
                />
              </label>
              <label>
                Confirm
                <input
                  type="password"
                  value={form.confirm}
                  onChange={(e) => setForm({ ...form, confirm: e.target.value })}
                  required
                  minLength={8}
                  autoComplete="new-password"
                />
              </label>
            </div>

            {error && <p className="error-text">{error}</p>}

            <button type="submit" disabled={busy}>
              {busy ? "Submitting…" : "Request access"}
            </button>

            <p className="auth-footer">
              Already registered? <Link to="/login">Sign in</Link>
            </p>
          </>
        )}
      </form>
    </div>
  );
}
