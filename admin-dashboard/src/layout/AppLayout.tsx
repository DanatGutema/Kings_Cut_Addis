import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
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
  const location = useLocation();
  const [navOpen, setNavOpen] = useState(false);

  const visibleLinks = links.filter(
    (link) =>
      (link.to !== "/staff" &&
        link.to !== "/services" &&
        link.to !== "/loyalty" &&
        link.to !== "/analytics" &&
        link.to !== "/promotions") ||
      staff?.role === "admin",
  );

  useEffect(() => {
    setNavOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (!navOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setNavOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [navOpen]);

  useEffect(() => {
    document.body.classList.toggle("nav-lock", navOpen);
    return () => document.body.classList.remove("nav-lock");
  }, [navOpen]);

  return (
    <div className={`shell${navOpen ? " nav-open" : ""}`}>
      <header className="topbar">
        <button
          type="button"
          className="menu-toggle"
          aria-label={navOpen ? "Close menu" : "Open menu"}
          aria-expanded={navOpen}
          onClick={() => setNavOpen((open) => !open)}
        >
          <span />
          <span />
          <span />
        </button>
        <div className="topbar-brand">
          <p className="brand">Kings Cut</p>
          <p className="brand-sub">Admin</p>
        </div>
        <p className="topbar-user">
          {staff?.first_name} · {staff?.role}
        </p>
      </header>

      <div
        className="nav-backdrop"
        aria-hidden={!navOpen}
        onClick={() => setNavOpen(false)}
      />

      <aside className="sidebar" aria-label="Main navigation">
        <div className="brand-block sidebar-brand">
          <p className="brand">Kings Cut</p>
          <p className="brand-sub">Barber Shop</p>
        </div>
        <nav>
          {visibleLinks.map((link) => (
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
