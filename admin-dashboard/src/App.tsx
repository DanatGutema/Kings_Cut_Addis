import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import AppLayout from "./layout/AppLayout";
import AnalyticsPage from "./pages/AnalyticsPage";
import AppointmentsPage from "./pages/AppointmentsPage";
import CheckInPage from "./pages/CheckInPage";
import CustomersPage from "./pages/CustomersPage";
import DashboardPage from "./pages/DashboardPage";
import LoginPage from "./pages/LoginPage";
import LoyaltyPage from "./pages/LoyaltyPage";
import PromotionsPage from "./pages/PromotionsPage";
import RegisterPage from "./pages/RegisterPage";
import RewardsPage from "./pages/RewardsPage";
import ServicesPage from "./pages/ServicesPage";
import VisitsPage from "./pages/VisitsPage";
import StaffPage from "./pages/StaffPage";
import SetPasswordPage from "./pages/SetPasswordPage";


function Protected({ children }: { children: React.ReactNode }) {
  const { staff, loading } = useAuth();
  if (loading) return <div className="login-page muted">Loading…</div>;
  if (!staff) return <Navigate to="/login" replace />;
  return children;
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/set-password" element={<SetPasswordPage />} />
        <Route
          path="/"
          element={
            <Protected>
              <AppLayout />
            </Protected>
          }
        >
          <Route index element={<DashboardPage />} />
          <Route path="checkin" element={<CheckInPage />} />
          <Route path="customers" element={<CustomersPage />} />
          <Route path="appointments" element={<AppointmentsPage />} />
          <Route path="visits" element={<VisitsPage />} />
          <Route path="services" element={<ServicesPage />} />
          <Route path="loyalty" element={<LoyaltyPage />} />
          <Route path="rewards" element={<RewardsPage />} />
          <Route path="promotions" element={<PromotionsPage />} />
          <Route path="analytics" element={<AnalyticsPage />} />
          <Route path="staff" element={<StaffPage />} />
        </Route>
      </Routes>
    </AuthProvider>
  );
}
