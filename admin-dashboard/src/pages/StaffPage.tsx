import { useState, useEffect } from "react";
import { Navigate } from "react-router-dom";
import { api, Staff } from "../api/client";
import { useAuth } from "../auth/AuthContext";

type Barber = {
  id: string;
  first_name: string;
  last_name?: string | null;
  phone_number: string;
  email?: string | null;
  specialty?: string | null;
  notes?: string | null;
  is_active: boolean;
};

export default function StaffPage() {
  const { staff: currentStaff } = useAuth();
  if (currentStaff && currentStaff.role !== "admin") return <Navigate to="/" replace />;

  const [staffList, setStaffList] = useState<Staff[]>([]);
  const [barbers, setBarbers] = useState<Barber[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showBarberForm, setShowBarberForm] = useState(false);
  const [formData, setFormData] = useState({
    first_name: "",
    last_name: "",
    phone_number: "",
    email: "",
    role: "staff" as "admin" | "staff",
  });
  const [barberForm, setBarberForm] = useState({
    first_name: "",
    last_name: "",
    phone_number: "",
    email: "",
    specialty: "",
    notes: "",
  });
  const [message, setMessage] = useState("");
  const [search, setSearch] = useState("");
  const [approveRoles, setApproveRoles] = useState<Record<string, "admin" | "staff">>({});

  useEffect(() => {
    void loadAll();
  }, []);

  async function loadAll() {
    try {
      const [staffData, barberData] = await Promise.all([
        api.listStaff(),
        api.listBarbers(),
      ]);
      setStaffList(staffData);
      setBarbers(barberData);
    } catch (err) {
      console.error("Failed to load staff/barbers:", err);
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
      await loadAll();
    } catch (err: any) {
      setMessage(err.message || "Failed to create staff");
    }
  }

  async function handleCreateBarber(e: React.FormEvent) {
    e.preventDefault();
    try {
      await api.createBarber({
        first_name: barberForm.first_name.trim(),
        last_name: barberForm.last_name.trim() || undefined,
        phone_number: barberForm.phone_number.trim(),
        email: barberForm.email.trim() || undefined,
        specialty: barberForm.specialty.trim() || undefined,
        notes: barberForm.notes.trim() || undefined,
      });
      setMessage("Barber registered (no login / no email invite).");
      setShowBarberForm(false);
      setBarberForm({
        first_name: "",
        last_name: "",
        phone_number: "",
        email: "",
        specialty: "",
        notes: "",
      });
      await loadAll();
    } catch (err: any) {
      setMessage(err.message || "Failed to create barber");
    }
  }

  async function handleDeactivate(staffId: string) {
    if (!confirm("Are you sure you want to deactivate this staff member?")) return;
    try {
      await api.deactivateStaff(staffId);
      setMessage("Staff member deactivated");
      await loadAll();
    } catch (err: any) {
      setMessage(err.message || "Failed to deactivate staff");
    }
  }

  async function handleActivate(staffId: string) {
    try {
      await api.activateStaff(staffId);
      setMessage("Staff member activated");
      await loadAll();
    } catch (err: any) {
      setMessage(err.message || "Failed to activate staff");
    }
  }

  async function handleDelete(member: Staff) {
    if (
      !confirm(
        `Permanently delete ${member.first_name} ${member.last_name || ""}? ` +
          "This only works if they have no visits, rewards, promotions, or audit history.",
      )
    ) {
      return;
    }
    try {
      await api.deleteStaff(member.id);
      setMessage("Staff member deleted");
      await loadAll();
    } catch (err: any) {
      setMessage(err.message || "Failed to delete staff");
    }
  }

  async function handleDeactivateBarber(id: string) {
    if (!confirm("Deactivate this barber? They will no longer appear in booking lists.")) return;
    try {
      await api.deactivateBarber(id);
      setMessage("Barber deactivated");
      await loadAll();
    } catch (err: any) {
      setMessage(err.message || "Failed to deactivate barber");
    }
  }

  async function handleActivateBarber(id: string) {
    try {
      await api.activateBarber(id);
      setMessage("Barber activated");
      await loadAll();
    } catch (err: any) {
      setMessage(err.message || "Failed to activate barber");
    }
  }

  async function handleDeleteBarber(barber: Barber) {
    if (
      !confirm(
        `Permanently delete ${barber.first_name} ${barber.last_name || ""}? ` +
          "Only works if they have no linked appointments.",
      )
    ) {
      return;
    }
    try {
      await api.deleteBarber(barber.id);
      setMessage("Barber deleted");
      await loadAll();
    } catch (err: any) {
      setMessage(err.message || "Failed to delete barber");
    }
  }

  async function handleApprove(member: Staff) {
    const role = approveRoles[member.id] || "staff";
    try {
      await api.approveStaff(member.id, role);
      setMessage(`Approved ${member.first_name} as ${role}`);
      await loadAll();
    } catch (err: any) {
      setMessage(err.message || "Failed to approve");
    }
  }

  async function handleReject(member: Staff) {
    if (!confirm(`Reject registration for ${member.first_name}? They will not be able to sign in.`)) {
      return;
    }
    try {
      await api.rejectStaff(member.id);
      setMessage(`Rejected ${member.first_name}`);
      await loadAll();
    } catch (err: any) {
      setMessage(err.message || "Failed to reject");
    }
  }

  if (loading) return <div>Loading...</div>;

  const q = search.trim().toLowerCase();
  const filteredStaff = staffList.filter((member) => {
    if (!q) return true;
    return (
      member.first_name.toLowerCase().includes(q) ||
      (member.last_name && member.last_name.toLowerCase().includes(q)) ||
      member.phone_number.includes(q) ||
      (member.email && member.email.toLowerCase().includes(q))
    );
  });
  const pendingStaff = filteredStaff.filter((m) => m.approval_status === "pending");
  const otherStaff = filteredStaff.filter((m) => m.approval_status !== "pending");
  const filteredBarbers = barbers.filter((b) => {
    if (!q) return true;
    return (
      b.first_name.toLowerCase().includes(q) ||
      (b.last_name && b.last_name.toLowerCase().includes(q)) ||
      b.phone_number.includes(q) ||
      (b.specialty && b.specialty.toLowerCase().includes(q))
    );
  });

  return (
    <div>
      <div className="page-head">
        <div>
          <h1>STAFF MANAGEMENT</h1>
          <p className="muted">
            System users (login) and shop barbers (registry only — no access)
          </p>
        </div>
        <div className="row-actions">

          <button
            type="button"
            className="ghost-btn"
            onClick={() => {
              setShowBarberForm(true);
              setShowCreateForm(false);
            }}
          >
            + ADD BARBER
          </button>
          <button
            type="button"
            onClick={() => {
              setShowCreateForm(true);
              setShowBarberForm(false);
            }}
          >
            + ADD STAFF
          </button>

        </div>
      </div>

      <div className="toolbar">
        <input
          placeholder="Search by name, phone, or specialty"
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
          <p className="muted">Creates a dashboard login and sends an invitation email.</p>
          <form onSubmit={handleCreate} className="form-grid">
            <div className="inline-fields">
              <label>
                First Name
                <input
                  type="text"
                  value={formData.first_name}
                  onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                  required
                />
              </label>
              <label>
                Last Name
                <input
                  type="text"
                  value={formData.last_name}
                  onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
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
                  onChange={(e) => setFormData({ ...formData, phone_number: e.target.value })}
                  required
                />
              </label>
              <label>
                Email
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
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

      {showBarberForm && (
        <div className="panel" style={{ marginBottom: "1rem" }}>
          <h2>Add Barber</h2>
          <p className="muted">
            Registry only — no password, no dashboard access. Used for booking lists and headcount.
          </p>
          <form onSubmit={handleCreateBarber} className="form-grid">
            <div className="inline-fields">
              <label>
                First Name
                <input
                  type="text"
                  value={barberForm.first_name}
                  onChange={(e) => setBarberForm({ ...barberForm, first_name: e.target.value })}
                  required
                />
              </label>
              <label>
                Last Name
                <input
                  type="text"
                  value={barberForm.last_name}
                  onChange={(e) => setBarberForm({ ...barberForm, last_name: e.target.value })}
                />
              </label>
            </div>
            <div className="inline-fields">
              <label>
                Phone Number
                <input
                  type="tel"
                  value={barberForm.phone_number}
                  onChange={(e) => setBarberForm({ ...barberForm, phone_number: e.target.value })}
                  required
                />
              </label>
              <label>
                Email (optional)
                <input
                  type="email"
                  value={barberForm.email}
                  onChange={(e) => setBarberForm({ ...barberForm, email: e.target.value })}
                />
              </label>
            </div>
            <label>
              Specialty (optional)
              <input
                type="text"
                value={barberForm.specialty}
                onChange={(e) => setBarberForm({ ...barberForm, specialty: e.target.value })}
                placeholder="e.g. Fade specialist"
              />
            </label>
            <label>
              Notes (optional)
              <input
                type="text"
                value={barberForm.notes}
                onChange={(e) => setBarberForm({ ...barberForm, notes: e.target.value })}
              />
            </label>
            <div className="toolbar">
              <button type="submit">Register Barber</button>
              <button
                type="button"
                className="ghost-btn"
                onClick={() => setShowBarberForm(false)}
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {pendingStaff.length > 0 && (
        <div className="panel" style={{ marginBottom: "1rem" }}>
          <h2>Pending approvals ({pendingStaff.length})</h2>
          <p className="muted">
            Self-registered accounts waiting for your decision. Choose their role, then approve.
          </p>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Phone</th>
                  <th>Email</th>
                  <th>Assign role</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {pendingStaff.map((member) => (
                  <tr key={member.id}>
                    <td>
                      {member.first_name} {member.last_name || ""}
                    </td>
                    <td>{member.phone_number}</td>
                    <td>{member.email || "—"}</td>
                    <td>
                      <select
                        value={approveRoles[member.id] || "staff"}
                        onChange={(e) =>
                          setApproveRoles({
                            ...approveRoles,
                            [member.id]: e.target.value as "admin" | "staff",
                          })
                        }
                      >
                        <option value="staff">Staff</option>
                        <option value="admin">Admin</option>
                      </select>
                    </td>
                    <td>
                      <div className="row-actions">
                        <button
                          type="button"
                          className="ghost-btn btn-ok"
                          onClick={() => handleApprove(member)}
                        >
                          Approve
                        </button>
                        <button
                          type="button"
                          className="ghost-btn btn-danger"
                          onClick={() => handleReject(member)}
                        >
                          Reject
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="panel">
        <h2>System users ({otherStaff.length})</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Phone</th>
                <th>Role</th>
                <th>Approval</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {otherStaff.map((member) => (
                <tr key={member.id}>
                  <td>
                    {member.first_name} {member.last_name}
                  </td>
                  <td>{member.email || "—"}</td>
                  <td>{member.phone_number}</td>
                  <td>
                    <span className={member.role === "admin" ? "error-text" : "ok-text"}>
                      {member.role.toUpperCase()}
                    </span>
                  </td>
                  <td>
                    <span
                      className={
                        member.approval_status === "approved"
                          ? "ok-text"
                          : member.approval_status === "rejected"
                            ? "error-text"
                            : "muted"
                      }
                    >
                      {(member.approval_status || "approved").toUpperCase()}
                    </span>
                  </td>
                  <td>
                    <span className={member.is_active ? "ok-text" : "error-text"}>
                      {member.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td>
                    <div className="row-actions">
                      {member.approval_status === "rejected" && (
                        <button
                          type="button"
                          className="ghost-btn btn-ok"
                          onClick={() => handleApprove(member)}
                        >
                          Approve
                        </button>
                      )}
                      {member.is_active ? (
                        <button
                          className="ghost-btn btn-danger"
                          onClick={() => handleDeactivate(member.id)}
                        >
                          Deactivate
                        </button>
                      ) : (
                        <>
                          {member.approval_status === "approved" && (
                            <button
                              className="ghost-btn btn-ok"
                              onClick={() => handleActivate(member.id)}
                            >
                              Activate
                            </button>
                          )}
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

      <div className="panel" style={{ marginTop: "1rem" }}>
        <h2>Barbers ({filteredBarbers.length})</h2>
        <p className="muted">No system login — listed in Mini App booking and appointment details.</p>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Phone</th>
                <th>Email</th>
                <th>Specialty</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredBarbers.map((b) => (
                <tr key={b.id}>
                  <td>
                    {b.first_name} {b.last_name || ""}
                  </td>
                  <td>{b.phone_number}</td>
                  <td>{b.email || "—"}</td>
                  <td>{b.specialty || "—"}</td>
                  <td>
                    <span className={b.is_active ? "ok-text" : "error-text"}>
                      {b.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td>
                    <div className="row-actions">
                      {b.is_active ? (
                        <button
                          className="ghost-btn btn-danger"
                          onClick={() => handleDeactivateBarber(b.id)}
                        >
                          Deactivate
                        </button>
                      ) : (
                        <>
                          <button
                            className="ghost-btn btn-ok"
                            onClick={() => handleActivateBarber(b.id)}
                          >
                            Activate
                          </button>
                          <button
                            className="ghost-btn btn-danger"
                            onClick={() => handleDeleteBarber(b)}
                          >
                            Delete
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
              {!filteredBarbers.length && (
                <tr>
                  <td colSpan={6} className="muted">
                    No barbers registered yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
