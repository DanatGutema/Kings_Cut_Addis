import { useState, useEffect } from "react";
import { Navigate } from "react-router-dom";
import { api, Staff } from "../api/client";
import { useAuth } from "../auth/AuthContext";

export default function StaffPage() {
    const { staff: currentStaff } = useAuth();
    if (currentStaff && currentStaff.role !== "admin") return <Navigate to="/" replace />;
    const [staffList, setStaffList] = useState<Staff[]>([]);
    const [loading, setLoading] = useState(true);
    const [showCreateForm, setShowCreateForm] = useState(false);
    const [formData, setFormData] = useState({
        first_name: "",
        last_name: "",
        phone_number: "",
        email: "",
        role: "staff" as "admin" | "staff",
    });
    const [message, setMessage] = useState("");
    const [search, setSearch] = useState("");

    useEffect(() => {
        loadStaff();
    }, []);






    async function loadStaff() {
        try {
            const data = await api.listStaff();
            setStaffList(data);
        } catch (err) {
            console.error("Failed to load staff:", err);
        } finally {
            setLoading(false);
        }
    }

    async function handleCreate(e: React.FormEvent) {
        e.preventDefault();
        try {
            await api.createStaff(formData);
            setMessage("Staff member created! Invitation email sent.");
            setShowCreateForm(false);
            setFormData({
                first_name: "",
                last_name: "",
                phone_number: "",
                email: "",
                role: "staff",
            });
            loadStaff();
        } catch (err: any) {
            setMessage(err.message || "Failed to create staff");
        }
    }

    async function handleDeactivate(staffId: string) {
        if (!confirm("Are you sure you want to deactivate this staff member?")) return;
        try {
            await api.deactivateStaff(staffId);
            setMessage("Staff member deactivated");
            loadStaff();
        } catch (err: any) {
            setMessage(err.message || "Failed to deactivate staff");
        }
    }

    async function handleActivate(staffId: string) {
        try {
            await api.activateStaff(staffId);
            setMessage("Staff member activated");
            loadStaff();
        } catch (err: any) {
            setMessage(err.message || "Failed to activate staff");
        }
    }

    async function handleDelete(member: Staff) {
        if (
            !confirm(
                `Permanently delete ${member.first_name} ${member.last_name || ""}? ` +
                    "This only works if they have no visits, rewards, promotions, or audit history."
            )
        ) {
            return;
        }
        try {
            await api.deleteStaff(member.id);
            setMessage("Staff member deleted");
            loadStaff();
        } catch (err: any) {
            setMessage(err.message || "Failed to delete staff");
        }
    }

    if (loading) return <div>Loading...</div>;

    return (
        <div>
            <div className="page-head">
                <h1>STAFF MANAGEMENT</h1>
                <button onClick={() => setShowCreateForm(true)}>
                    + ADD STAFF
                </button>
            </div>

            <div className="toolbar">
                <input
                    placeholder="Search by name or phone"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                />
            </div>

            {message && (
                <div className="panel" style={{ marginBottom: "1rem" }}>
                    {message}
                </div>
            )}

            {showCreateForm && (
                <div className="panel" style={{ marginBottom: "1rem" }}>
                    <h2>Add New Staff Member</h2>
                    <form onSubmit={handleCreate} className="form-grid">
                        <div className="inline-fields">
                            <label>
                                First Name
                                <input
                                    type="text"
                                    value={formData.first_name}
                                    onChange={(e) =>
                                        setFormData({ ...formData, first_name: e.target.value })
                                    }
                                    required
                                />
                            </label>
                            <label>
                                Last Name
                                <input
                                    type="text"
                                    value={formData.last_name}
                                    onChange={(e) =>
                                        setFormData({ ...formData, last_name: e.target.value })
                                    }
                                    required
                                />
                            </label>
                        </div>
                        <div className="inline-fields">
                            <label>
                                Phone Number
                                <input
                                    type="tel"
                                    value={formData.phone_number}
                                    onChange={(e) =>
                                        setFormData({ ...formData, phone_number: e.target.value })
                                    }
                                    required
                                />
                            </label>
                            <label>
                                Email
                                <input
                                    type="email"
                                    value={formData.email}
                                    onChange={(e) =>
                                        setFormData({ ...formData, email: e.target.value })
                                    }
                                    required
                                />
                            </label>
                        </div>
                        <label>
                            Role
                            <select
                                value={formData.role}
                                onChange={(e) =>
                                    setFormData({
                                        ...formData,
                                        role: e.target.value as "admin" | "staff",
                                    })
                                }
                            >
                                <option value="staff">Staff</option>
                                <option value="admin">Admin</option>
                            </select>
                        </label>
                        <div className="toolbar">
                            <button type="submit">Create & Send Invitation</button>
                            <button
                                type="button"
                                className="ghost-btn"
                                onClick={() => setShowCreateForm(false)}
                            >
                                Cancel
                            </button>
                        </div>
                    </form>
                </div>
            )}

            <div className="panel">
                <div className="table-wrap">
                    <table>
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Email</th>
                                <th>Phone</th>
                                <th>Role</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {staffList.filter((member) => {
                                if (!search.trim()) return true;
                                const q = search.toLowerCase();
                                return (
                                    member.first_name.toLowerCase().includes(q) ||
                                    (member.last_name && member.last_name.toLowerCase().includes(q)) ||
                                    member.phone_number.includes(q)
                                );
                            }).map((member) => (
                                <tr key={member.id}>
                                    <td>
                                        {member.first_name} {member.last_name}
                                    </td>
                                    <td>{member.email}</td>
                                    <td>{member.phone_number}</td>
                                    <td>
                                        <span
                                            className={
                                                member.role === "admin" ? "error-text" : "ok-text"
                                            }
                                        >
                                            {member.role.toUpperCase()}
                                        </span>
                                    </td>
                                    <td>
                                        <span className={member.is_active ? "ok-text" : "error-text"}>
                                            {member.is_active ? "Active" : "Inactive"}
                                        </span>
                                    </td>
                                    <td>
                                        <div className="row-actions">
                                            {member.is_active ? (
                                                <button
                                                    className="ghost-btn btn-danger"
                                                    onClick={() => handleDeactivate(member.id)}
                                                >
                                                    Deactivate
                                                </button>
                                            ) : (
                                                <>
                                                    <button
                                                        className="ghost-btn btn-ok"
                                                        onClick={() => handleActivate(member.id)}
                                                    >
                                                        Activate
                                                    </button>
                                                    {member.id !== currentStaff?.id && (
                                                        <button
                                                            className="ghost-btn btn-danger"
                                                            onClick={() => handleDelete(member)}
                                                        >
                                                            Delete
                                                        </button>
                                                    )}
                                                </>
                                            )}
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}