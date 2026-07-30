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
import { useAuth } from "../auth/AuthContext";
import { useNavigate } from "react-router-dom";




function getGreeting(firstName: string): string {
  const now = new Date();
  const hour = parseInt(
    new Intl.DateTimeFormat("en-GB", {
      hour: "numeric",
      hour12: false,
      timeZone: "Africa/Addis_Ababa",
    }).format(now),
    10,
  );

  let timeGreeting: string;
  let message: string;

  if (hour >= 5 && hour < 12) {
    timeGreeting = "Good morning";
    message = "Let's make today a great day!";
  } else if (hour >= 12 && hour < 17) {
    timeGreeting = "Good afternoon";
    message = "You're doing an amazing job!";
  } else if (hour >= 17 && hour < 21) {
    timeGreeting = "Good evening";
    message =  "The day's almost done. Great work today!";
  } else {
    timeGreeting = "Good night  "; 
    message = "Night shift hero rest well after!";
  }

  return `${timeGreeting}, ${firstName}! ${message}`;
}
export default function DashboardPage() {
  const [metrics, setMetrics] = useState<{
    total_customers: number;
    visits_today: number;
    appointment: number;
    active_rewards: number;
    revenue_today: number;
    revenue_this_month: number;
  } | null>(null);
  const [trend, setTrend] = useState<{ period: string; visit_count: number }[]>([]);
  const { staff } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.dashboard(), api.visitTrend("daily")])
      .then(([m, t]) => {
        setMetrics(m);
        setTrend(
          t.points.slice(-14).map((p) => ({
            period: p.period.slice(5),
            visit_count: p.visit_count,
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
          <p className="muted">{staff?.first_name ? getGreeting(staff.first_name):""}</p>
        </div>
        {/* <div className="row-actions">
          <button type="button" className="ghost-btn" onClick={() => api.downloadExport("xlsx")}>
            Export Excel
          </button>
          <button type="button" className="ghost-btn" onClick={() => api.downloadExport("pdf")}>
            Export PDF
          </button>
        </div> */}
      </header>

      <div className="metric-grid">
        {/* <article className="metric">
          <span>Customers</span>
          <strong>{metrics.total_customers}</strong>
        </article> */}


        <article
          className="metric"
          style={{ cursor: "pointer" }}
          onClick={() => {
            if (staff?.role === "admin") {
              navigate("/customers");
            } else {
              alert("You do not have this privilege");
            }
          }}
        >
          <span>Customers</span>
          <strong>{metrics.total_customers}</strong>
        </article>


        <article 
          className="metric"
          style={{ cursor: "pointer"}}
          onClick={() => {
            navigate("/visits");
          }}
             >
          <span>Visits today</span>
          <strong>{metrics.visits_today}</strong>
        </article>


        <article className="metric"
          style={{ cursor: "pointer"}}
          onClick={() => {
            navigate("/appointments");
          }}
        >
          <span>Total Appointments</span>
          <strong>{metrics.visits_today}</strong>
        </article>


        <article className="metric"
          style={{ cursor: "pointer"}}
          onClick={() => {
            navigate("/rewards");
          }}
             
        >
          <span>Active rewards</span>
          <strong>{metrics.active_rewards}</strong>
        </article>


        {staff?.role === "admin" && (
        <article className="metric"
        style={{ cursor: "pointer"}}
          onClick={() => {
            navigate("/analytics");
          }}
             
        >
          <span>Revenue today</span>
          <strong>{Number(metrics.revenue_today).toLocaleString()} ETB</strong>
        </article>
        )}



      {staff?.role === "admin" && (
        <article className="metric wide"
        style={{ cursor: "pointer"}}
          onClick={() => {
            navigate("/analytics");
          }}
             
        >
          <span>Revenue this month</span>
          <strong>{Number(metrics.revenue_this_month).toLocaleString()} ETB</strong>
        </article>
        )}

      </div>

      <section className="panel">
        <h2>Visits — last 14 days</h2>
        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={trend}>
              <CartesianGrid stroke="rgba(201,168,76,0.18)" vertical={false} />
              <XAxis dataKey="period" stroke="#666666" fontSize={12} />
              <YAxis allowDecimals={false} stroke="#666666" fontSize={12} />
              <Tooltip
                contentStyle={{
                  background: "#ffffff",
                  border: "1px solid rgba(201,168,76,0.35)",
                  borderRadius: 8,
                  color: "#1a1a1a",
                }}
              />
              <Bar dataKey="visit_count" fill="#C9A84C" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>
    </div>
  );
}
