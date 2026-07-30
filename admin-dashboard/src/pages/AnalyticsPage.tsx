import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "../api/client";
import { useNavigate } from "react-router";

type TopCustomer = {
  customer_id: string;
  first_name: string;
  last_name?: string | null;
  total_visits: number;
  total_spending: number;
};

type VisitGranularity = "daily" | "weekly" | "monthly" | "yearly";

function formatPeriodLabel(period: string, granularity: VisitGranularity): string {
  if (granularity === "yearly") return period;
  if (granularity === "monthly") {
    const [y, m] = period.split("-");
    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    return `${months[Number(m) - 1] || m} ${y}`;
  }
  if (granularity === "weekly") {
    const d = new Date(`${period}T00:00:00`);
    if (Number.isNaN(d.getTime())) return period;
    return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
  }
  // daily
  const d = new Date(`${period}T00:00:00`);
  if (Number.isNaN(d.getTime())) return period;
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

const chartTooltipStyle = {
  background: "#ffffff",
  border: "1px solid rgba(201,168,76,0.35)",
  borderRadius: 8,
  color: "#1a1a1a",
};

export default function AnalyticsPage() {
  const [byService, setByService] = useState<
    { service_name: string; total_revenue: number; visit_count: number }[]
  >([]);
  const [topBySpending, setTopBySpending] = useState<TopCustomer[]>([]);
  const [topByVisits, setTopByVisits] = useState<TopCustomer[]>([]);
  const navigate = useNavigate();
  const [loyalty, setLoyalty] = useState<{
    redemption_rate: number;
  } | null>(null);
  const [metrics, setMetrics] = useState<{
    total_customers: number;
    total_visits: number;
  } | null>(null);
  const [visitGranularity, setVisitGranularity] = useState<VisitGranularity>("daily");
  const [visitTrend, setVisitTrend] = useState<{
    total_visits: number;
    points: { period: string; label: string; visit_count: number }[];
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      api.revenueByService(),
      api.topCustomers("spending"),
      api.topCustomers("visits"),
      api.loyaltyMetrics(),
      api.dashboard(),
    ])
      .then(([services, bySpending, byVisits, loyaltyMetrics, m]) => {
        setByService(services);
        setTopBySpending(bySpending);
        setTopByVisits(byVisits);
        setLoyalty(loyaltyMetrics);
        setMetrics(m);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load"));
  }, []);

  useEffect(() => {
    api
      .visitTrend(visitGranularity)
      .then((data) => {
        setVisitTrend({
          total_visits: data.total_visits,
          points: data.points.map((p) => ({
            period: p.period,
            label: formatPeriodLabel(p.period, visitGranularity),
            visit_count: p.visit_count,
          })),
        });
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load visit trend"));
  }, [visitGranularity]);

  if (error) return <p className="error-text">{error}</p>;

  const rangeLabel =
    visitGranularity === "daily"
      ? "Last 30 days"
      : visitGranularity === "weekly"
        ? "Last 12 weeks"
        : visitGranularity === "monthly"
          ? "Last 12 months"
          : "Last 5 years";

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <h1>Analytics</h1>
          <p className="muted">Revenue, visits, top customers, loyalty health</p>
        </div>
        <div className="row-actions">
          <button type="button" className="ghost-btn" onClick={() => api.downloadExport("xlsx")}>
            Excel
          </button>
          <button type="button" className="ghost-btn" onClick={() => api.downloadExport("pdf")}>
            PDF
          </button>
        </div>
      </header>

      {loyalty && metrics && (
        <div className="metric-grid">
          <article
            className="metric"
            style={{ cursor: "pointer" }}
            onClick={() => navigate("/visits")}
          >
            <span>Total Visits</span>
            <strong>{metrics.total_visits}</strong>
          </article>
          <article
            className="metric"
            style={{ cursor: "pointer" }}
            onClick={() => navigate("/customers")}
          >
            <span>Total Customer</span>
            <strong>{metrics.total_customers}</strong>
          </article>
          <article
            className="metric"
            style={{ cursor: "pointer" }}
            onClick={() => navigate("/rewards")}
          >
            <span>Reward Redemption Rate</span>
            <strong>{(loyalty.redemption_rate * 100).toFixed(1)}%</strong>
          </article>
        </div>
      )}

      <section className="panel">
        <div className="page-head" style={{ marginBottom: "0.75rem" }}>
          <div>
            <h2 style={{ margin: 0 }}>Visit analysis</h2>
            <p className="muted" style={{ margin: "0.25rem 0 0" }}>
              {rangeLabel}
              {visitTrend ? ` · ${visitTrend.total_visits} visits` : ""}
            </p>
          </div>
          <div className="tabs">
            {(
              [
                ["daily", "Daily"],
                ["weekly", "Weekly"],
                ["monthly", "Monthly"],
                ["yearly", "Yearly"],
              ] as const
            ).map(([value, label]) => (
              <button
                key={value}
                type="button"
                className={visitGranularity === value ? "active" : ""}
                onClick={() => setVisitGranularity(value)}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={visitTrend?.points || []}>
              <CartesianGrid stroke="rgba(201,168,76,0.18)" vertical={false} />
              <XAxis dataKey="label" stroke="#666666" fontSize={12} />
              <YAxis stroke="#666666" fontSize={12} allowDecimals={false} />
              <Tooltip contentStyle={chartTooltipStyle} />
              <Line
                type="monotone"
                dataKey="visit_count"
                name="Visits"
                stroke="#C9A84C"
                strokeWidth={2.5}
                dot={{ r: 3, fill: "#B8860B" }}
                activeDot={{ r: 5 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="panel">
        <h2>Revenue by service</h2>
        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={byService}>
              <CartesianGrid stroke="rgba(201,168,76,0.18)" vertical={false} />
              <XAxis dataKey="service_name" stroke="#666666" fontSize={12} />
              <YAxis stroke="#666666" fontSize={12} />
              <Tooltip contentStyle={chartTooltipStyle} />
              <Bar dataKey="total_revenue" fill="#C9A84C" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="panel">
        <h2>Top customers by spending</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Visits</th>
                <th>Spending</th>
              </tr>
            </thead>
            <tbody>
              {topBySpending.map((c) => (
                <tr key={c.customer_id}>
                  <td>
                    {c.first_name} {c.last_name || ""}
                  </td>
                  <td>{c.total_visits}</td>
                  <td>{Number(c.total_spending).toLocaleString()} ETB</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel">
        <h2>Top customers by visits</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Visits</th>
                <th>Spending</th>
              </tr>
            </thead>
            <tbody>
              {topByVisits.map((c) => (
                <tr key={c.customer_id}>
                  <td>
                    {c.first_name} {c.last_name || ""}
                  </td>
                  <td>{c.total_visits}</td>
                  <td>{Number(c.total_spending).toLocaleString()} ETB</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
