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
// import { Navigate } from "react-router-dom";
import { useNavigate } from "react-router";


export default function AnalyticsPage() {
  const [byService, setByService] = useState<
    { service_name: string; total_revenue: number; visit_count: number }[]
  >([]);
  const [top, setTop] = useState<
    {
      customer_id: string;
      first_name: string;
      last_name?: string | null;
      total_visits: number;
      total_spending: number;
    }[]
  >([]);

  const navigate = useNavigate();
  const [loyalty, setLoyalty] = useState<{
    redemption_rate: number;
  } | null>(null);
  const [metrics, setMetrics] = useState<{
    total_customers: number;
    total_visits: number;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.revenueByService(), api.topCustomers("spending"), api.loyaltyMetrics(), api.dashboard()])
      .then(([services, customers, loyaltyMetrics, m]) => {
        setByService(services);
        setTop(customers);
        setLoyalty(loyaltyMetrics);
        setMetrics(m);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load"));
  }, []);

  if (error) return <p className="error-text">{error}</p>;

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <h1>Analytics</h1>
          <p className="muted">Revenue, top customers, loyalty health</p>
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
          <article className="metric"
          style={{ cursor: "pointer" }}
            onClick={() => {
              navigate("/visits");
            }}
          >
            <span>Total Visits</span>
            <strong>{metrics.total_visits}</strong>
          </article>
          <article 
            className="metric"
            style={{ cursor: "pointer" }}
            onClick={() => {
              navigate("/customers");
            }}
          >
            <span>Total Customer</span>
            <strong>{metrics.total_customers}</strong>
          </article>
          {/* <article className="metric">
            <span>Revenue By Service</span>
            <strong>{loyalty.rewards_expired}</strong>
          </article> */}
          <article className="metric"
            style={{ cursor: "pointer" }}
            onClick={() => {
              navigate("/rewards");
            }}  
          >
            <span>Reward Redemetion Rate</span>
            <strong>{(loyalty.redemption_rate * 100).toFixed(1)}%</strong>
          </article>
        </div>
      )}

      <section className="panel">
        <h2>Revenue by service</h2>
        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={byService}>
              <CartesianGrid stroke="rgba(232,201,138,0.12)" vertical={false} />
              <XAxis dataKey="service_name" stroke="#b9a894" fontSize={12} />
              <YAxis stroke="#b9a894" fontSize={12} />
              <Tooltip
                contentStyle={{
                  background: "#2b1d14",
                  border: "1px solid rgba(232,201,138,0.25)",
                  borderRadius: 8,
                }}
              />
              <Bar dataKey="total_revenue" fill="#e8c98a" radius={[6, 6, 0, 0]} />
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
              {top.map((c) => (
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
