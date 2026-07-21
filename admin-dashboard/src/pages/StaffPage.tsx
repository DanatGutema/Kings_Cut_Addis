import { useState, useEffect } from "react";
import { api, Staff } from "../api/client";

export default function StaffPage() {
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

    if (loading) return <div>Loading...</div>;

    return (
        <div>
            <div className="page-head">
                <h1>STAFF MANAGEMENT</h1>
                <button onClick={() => setShowCreateForm(true)}>
                    + ADD STAFF
                </button>
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
                            {staffList.map((staff) => (
                                <tr key={staff.id}>
                                    <td>
                                        {staff.first_name} {staff.last_name}
                                    </td>
                                    <td>{staff.email}</td>
                                    <td>{staff.phone_number}</td>
                                    <td>
                                        <span
                                            className={
                                                staff.role === "admin" ? "error-text" : "ok-text"
                                            }
                                        >
                                            {staff.role.toUpperCase()}
                                        </span>
                                    </td>
                                    <td>
                                        <span className={staff.is_active ? "ok-text" : "error-text"}>
                                            {staff.is_active ? "Active" : "Inactive"}
                                        </span>
                                    </td>
                                    <td>
                                        <div className="row-actions">
                                            {staff.is_active && (
                                                <button
                                                    className="ghost-btn"
                                                    onClick={() => handleDeactivate(staff.id)}
                                                >
                                                    Deactivate
                                                </button>
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