import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "../api/client";

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<{
    total_customers: number;
    visits_today: number;
    active_rewards: number;
    revenue_today: number;
    revenue_this_month: number;
  } | null>(null);
  const [trend, setTrend] = useState<{ period: string; visit_count: number }[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.dashboard(), api.visitTrend(14)])
      .then(([m, t]) => {
        setMetrics(m);
        setTrend(
          t.map((p) => ({
            ...p,
            period: p.period.slice(5),
          })),
        );
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load"));
  }, []);

  if (error) return <p className="error-text">{error}</p>;
  if (!metrics) return <p className="muted">Loading dashboard…</p>;

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <h1>Dashboard</h1>
          <p className="muted">Today’s pulse for the shop floor</p>
        </div>
        <div className="row-actions">
          <button type="button" className="ghost-btn" onClick={() => api.downloadExport("xlsx")}>
            Export Excel
          </button>
          <button type="button" className="ghost-btn" onClick={() => api.downloadExport("pdf")}>
            Export PDF
          </button>
        </div>
      </header>

      <div className="metric-grid">
        <article className="metric">
          <span>Customers</span>
          <strong>{metrics.total_customers}</strong>
        </article>
        <article className="metric">
          <span>Visits today</span>
          <strong>{metrics.visits_today}</strong>
        </article>
        <article className="metric">
          <span>Active rewards</span>
          <strong>{metrics.active_rewards}</strong>
        </article>
        <article className="metric">
          <span>Revenue today</span>
          <strong>{Number(metrics.revenue_today).toLocaleString()} ETB</strong>
        </article>
        <article className="metric wide">
          <span>Revenue this month</span>
          <strong>{Number(metrics.revenue_this_month).toLocaleString()} ETB</strong>
        </article>
      </div>

      <section className="panel">
        <h2>Visits — last 14 days</h2>
        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={trend}>
              <CartesianGrid stroke="rgba(232,201,138,0.12)" vertical={false} />
              <XAxis dataKey="period" stroke="#b9a894" fontSize={12} />
              <YAxis allowDecimals={false} stroke="#b9a894" fontSize={12} />
              <Tooltip
                contentStyle={{
                  background: "#2b1d14",
                  border: "1px solid rgba(232,201,138,0.25)",
                  borderRadius: 8,
                }}
              />
              <Bar dataKey="visit_count" fill="#c4a574" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>
    </div>
  );
}
