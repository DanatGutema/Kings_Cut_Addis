import { FormEvent, useEffect, useMemo, useState } from "react";
import { QRCodeSVG } from "qrcode.react";
import {
  authWithTelegram,
  createAppointment,
  fetchAppointments,
  fetchLoyalty,
  fetchPromotions,
  fetchQr,
  fetchRewards,
  fetchServices,
  type Appointment,
  type Customer,
  type LoyaltyProgress,
  type Promotion,
  type QrPayload,
  type Reward,
  type Service,
} from "./api";
import { bootstrapTelegram } from "./telegram";
import "./styles.css";

type Tab = "checkin" | "book" | "loyalty" | "rewards" | "promos";

function progressPct(current: number, target?: number | null) {
  if (!target || target <= 0) return 0;
  return Math.min(100, Math.round((current / target) * 100));
}

function toIsoLocal(value: string) {
  // datetime-local → ISO without timezone (backend expects naive/local-ish UTC parse)
  if (!value) return value;
  return new Date(value).toISOString();
}

export default function App() {
  const [tab, setTab] = useState<Tab>("checkin");
  const [token, setToken] = useState<string | null>(null);
  const [customer, setCustomer] = useState<Customer | null>(null);
  const [qr, setQr] = useState<QrPayload | null>(null);
  const [loyalty, setLoyalty] = useState<LoyaltyProgress | null>(null);
  const [rewards, setRewards] = useState<Reward[]>([]);
  const [promos, setPromos] = useState<Promotion[]>([]);
  const [services, setServices] = useState<Service[]>([]);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [serviceId, setServiceId] = useState("");
  const [scheduledAt, setScheduledAt] = useState("");
  const [notes, setNotes] = useState("");
  const [bookMessage, setBookMessage] = useState<string | null>(null);
  const [bookError, setBookError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const tg = bootstrapTelegram();
    const initData = tg?.initData || "";

    async function boot() {
      try {
        if (!initData) {
          setError(
            "Open this Mini App from the Kings Cut Telegram bot. Direct browser open has no Telegram auth.",
          );
          setLoading(false);
          return;
        }
        const auth = await authWithTelegram(initData);
        setToken(auth.access_token);
        setCustomer(auth.customer);
        const [qrData, loyaltyData, rewardsData, promosData, servicesData, apptData] =
          await Promise.all([
            fetchQr(auth.access_token),
            fetchLoyalty(auth.access_token),
            fetchRewards(auth.access_token),
            fetchPromotions(auth.access_token),
            fetchServices(auth.access_token),
            fetchAppointments(auth.access_token),
          ]);
        setQr(qrData);
        setLoyalty(loyaltyData);
        setRewards(rewardsData);
        setPromos(promosData);
        setServices(servicesData);
        setAppointments(apptData);
        if (servicesData[0]) setServiceId(servicesData[0].id);
        tg?.HapticFeedback?.impactOccurred("light");
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not load Mini App");
      } finally {
        setLoading(false);
      }
    }

    void boot();
  }, []);

  const spending = useMemo(
    () => Number(customer?.total_spending ?? 0).toLocaleString(),
    [customer],
  );

  async function onBook(e: FormEvent) {
    e.preventDefault();
    if (!token) return;
    setBookError(null);
    setBookMessage(null);
    try {
      await createAppointment(token, {
        service_id: serviceId,
        scheduled_at: toIsoLocal(scheduledAt),
        notes: notes.trim() || undefined,
      });
      setNotes("");
      setBookMessage("Appointment requested. We'll notify you when staff responds.");
      const apptData = await fetchAppointments(token);
      setAppointments(apptData);
      bootstrapTelegram()?.HapticFeedback?.notificationOccurred("success");
    } catch (err) {
      setBookError(err instanceof Error ? err.message : "Booking failed");
    }
  }

  if (loading) {
    return (
      <div className="state">
        <h1>Kings Cut</h1>
        <p>Opening your loyalty pass…</p>
      </div>
    );
  }

  if (error || !customer || !token) {
    return (
      <div className="state error">
        <h1>Kings Cut</h1>
        <p>{error || "Not signed in"}</p>
        <p style={{ marginTop: "1rem", color: "var(--muted)" }}>
          In Telegram: open the bot → share your phone → use Open Kings Cut App.
        </p>
      </div>
    );
  }

  return (
    <div className="app-shell">
      {tab === "checkin" && (
        <section className="hero">
          <h1 className="brand">
            Kings Cut
            <br />
            Addis
          </h1>
          <p className="tagline">Show this code at the chair. Your visits and rewards stay with you.</p>
          <div className="qr-stage">
            {qr && (
              <QRCodeSVG
                value={qr.qr_token}
                size={220}
                level="M"
                bgColor="transparent"
                fgColor="#1a120b"
                includeMargin={false}
              />
            )}
          </div>
          <p className="qr-meta">
            {qr?.customer_name}
            <br />
            {qr?.phone_number}
          </p>
        </section>
      )}

      {tab === "book" && (
        <section className="section">
          <h2>Book</h2>
          <form className="panel" onSubmit={onBook}>
            <label className="field">
              Service
              <select value={serviceId} onChange={(e) => setServiceId(e.target.value)} required>
                {services.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name} — {Number(s.price).toLocaleString()} ETB
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              Date & time
              <input
                type="datetime-local"
                value={scheduledAt}
                onChange={(e) => setScheduledAt(e.target.value)}
                required
              />
            </label>
            <label className="field">
              Notes (optional)
              <input value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Any request?" />
            </label>
            <button type="submit" className="primary-btn">
              Request appointment
            </button>
            {bookMessage && <p className="ok-text">{bookMessage}</p>}
            {bookError && <p className="error-text">{bookError}</p>}
            {!services.length && <p className="qr-meta">No services available to book yet.</p>}
          </form>

          <div className="list" style={{ marginTop: "1rem" }}>
            <h3 style={{ margin: "0 0 0.5rem" }}>Your appointments</h3>
            {appointments.map((a) => (
              <article className="card-item" key={a.id}>
                <h3>{a.service_name || "Service"}</h3>
                <p>{new Date(a.scheduled_at).toLocaleString()}</p>
                <span className={`badge ${a.status}`}>{a.status}</span>
              </article>
            ))}
            {!appointments.length && <p className="qr-meta">No bookings yet.</p>}
          </div>
        </section>
      )}

      {tab === "loyalty" && (
        <section className="section">
          <h2>Loyalty</h2>
          <div className="panel">
            <div className="stats">
              <div className="stat">
                <strong>{customer.total_visits}</strong>
                <span>Visits</span>
              </div>
              <div className="stat">
                <strong>{spending}</strong>
                <span>ETB</span>
              </div>
              <div className="stat">
                <strong>{customer.loyalty_status}</strong>
                <span>Tier</span>
              </div>
            </div>
            {(loyalty?.rules || []).map((rule) => {
              const isVisit = rule.rule_type === "visit";
              const current = isVisit ? rule.current_visits : Number(rule.current_spending);
              const target = isVisit
                ? rule.visit_threshold
                : Number(rule.spending_threshold || 0);
              const pct = progressPct(current, target || null);
              return (
                <div className="progress-row" key={rule.rule_id}>
                  <header>
                    <span>{rule.rule_name}</span>
                    <span>
                      {isVisit
                        ? `${rule.current_visits}/${rule.visit_threshold ?? "—"}`
                        : `${Number(rule.current_spending).toLocaleString()}/${Number(rule.spending_threshold || 0).toLocaleString()}`}
                    </span>
                  </header>
                  <div className="bar">
                    <i style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
            {!loyalty?.rules?.length && <p className="qr-meta">No active loyalty rules yet.</p>}
          </div>
        </section>
      )}

      {tab === "rewards" && (
        <section className="section">
          <h2>Rewards</h2>
          <div className="list">
            {rewards.map((reward) => (
              <article className="card-item" key={reward.id}>
                <h3>
                  {reward.reward_type === "percentage" && `${reward.reward_percentage}% off`}
                  {reward.reward_type === "fixed" && `${reward.reward_amount} ETB off`}
                  {reward.reward_type === "both" &&
                    `${reward.reward_percentage}% + ${reward.reward_amount} ETB`}
                </h3>
                <p>
                  Earned {reward.earned_date} · Expires {reward.expiry_date}
                </p>
                <span className={`badge ${reward.status}`}>{reward.status}</span>
              </article>
            ))}
            {!rewards.length && <p className="qr-meta">No rewards yet — keep visiting.</p>}
          </div>
        </section>
      )}

      {tab === "promos" && (
        <section className="section">
          <h2>Promos</h2>
          <div className="list">
            {promos.map((promo) => (
              <article className="card-item" key={promo.id}>
                <h3>{promo.title}</h3>
                <p>{promo.description || "Limited-time shop offer"}</p>
                <p style={{ marginTop: "0.4rem" }}>
                  {promo.discount_type === "percentage"
                    ? `${promo.discount_value}% off`
                    : `${promo.discount_value} ETB off`}{" "}
                  · {promo.start_date} → {promo.end_date}
                </p>
              </article>
            ))}
            {!promos.length && <p className="qr-meta">No active promotions right now.</p>}
          </div>
        </section>
      )}

      <nav className="nav">
        {(
          [
            ["checkin", "Check-in"],
            ["book", "Book"],
            ["loyalty", "Loyalty"],
            ["rewards", "Rewards"],
            ["promos", "Promos"],
          ] as const
        ).map(([id, label]) => (
          <button
            key={id}
            type="button"
            className={tab === id ? "active" : ""}
            onClick={() => {
              setTab(id);
              bootstrapTelegram()?.HapticFeedback?.impactOccurred("light");
            }}
          >
            {label}
          </button>
        ))}
      </nav>
    </div>
  );
}
