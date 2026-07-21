import { useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { api } from "../api/client";

export default function SetPasswordPage() {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const token = searchParams.get("token");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [message, setMessage] = useState("");
    const [loading, setLoading] = useState(false);

    if (!token) {
        return (
            <div className="login-page">
                <div className="login-card">
                    <h1>INVALID LINK</h1>
                    <p>This password reset link is invalid or missing.</p>
                </div>
            </div>
        );
    }

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        
        if (password !== confirmPassword) {
            setMessage("Passwords do not match");
            return;
        }
        
        if (password.length < 8) {
            setMessage("Password must be at least 8 characters");
            return;
        }
        
        setLoading(true);
        try {
            await api.setStaffPassword(token, password);
            setMessage("Password set successfully! Redirecting to login...");
            setTimeout(() => navigate("/login"), 2000);
        } catch (err: any) {
            setMessage(err.message || "Failed to set password");
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="login-page">
            <div className="login-card">
                <h1>SET YOUR PASSWORD</h1>
                <p>Welcome to Kings Cut Addis! Please create your password to access the admin dashboard.</p>
                
                {message && <div style={{ color: "var(--danger)" }}>{message}</div>}
                
                <form onSubmit={handleSubmit} className="form-grid">
                    <label>
                        New Password
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                            minLength={8}
                        />
                    </label>
                    <label>
                        Confirm Password
                        <input
                            type="password"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            required
                            minLength={8}
                        />
                    </label>
                    <button type="submit" disabled={loading}>
                        {loading ? "Setting Password..." : "Set Password"}
                    </button>
                </form>
            </div>
        </div>
    );
}