import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

const links = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/appointments", label: "Appointments" },
  { to: "/checkin", label: "Check-in" },
  { to: "/visits", label: "Visits" },
  { to: "/rewards", label: "Rewards" },
  { to: "/promotions", label: "Promotions" },
  { to: "/analytics", label: "Analytics" },
  { to: "/customers", label: "Customers" },
  { to: "/services", label: "Services" },
  { to: "/loyalty", label: "Loyalty" },
  { to: "/staff", label: "Staff" },
];

export default function AppLayout() {
  const { staff, logout } = useAuth();

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand-block">
          <p className="brand">Kings Cut</p>
          <p className="brand-sub">Barber Shop</p>
        </div>
        <nav>
          {links
            .filter(
              (link) =>
                (link.to !== "/staff" &&
                  link.to !== "/services" &&
                  link.to !== "/loyalty" &&
                  // link.to !== "/customers" &&
                  link.to !== "/analytics" &&
                  link.to !== "/promotions") ||
                staff?.role === "admin",
            )
            .map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.end}
                className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}
              >
                {link.label}
              </NavLink>
            ))}
        </nav>
        <div className="sidebar-foot">
          <p>
            {staff?.first_name} · {staff?.role}
          </p>
          <button type="button" className="ghost-btn" onClick={logout}>
            Sign out
          </button>
        </div>
      </aside>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
