import { FormEvent, useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";

type Rule = {
  id: string;
  rule_name: string;
  rule_type: string;
  visit_threshold?: number | null;
  spending_threshold?: number | null;
  reward_type: string;
  reward_percentage?: number | null;
  reward_amount?: number | null;
  expiry_days: number;
  evaluation_period_days?: number | null;
  is_active: boolean;
};

type RuleForm = {
  rule_name: string;
  rule_type: string;
  visit_threshold: string;
  spending_threshold: string;
  reward_type: string;
  reward_percentage: string;
  reward_amount: string;
  expiry_days: string;
  evaluation_period_days: string;
};

const emptyForm: RuleForm = {
  rule_name: "",
  rule_type: "visit",
  visit_threshold: "10",
  spending_threshold: "5000",
  reward_type: "percentage",
  reward_percentage: "15",
  reward_amount: "500",
  expiry_days: "30",
  evaluation_period_days: "90",
};

function buildRulePayload(form: RuleForm, isActive = true): Record<string, unknown> {
  const body: Record<string, unknown> = {
    rule_name: form.rule_name.trim(),
    rule_type: form.rule_type,
    reward_type: form.reward_type,
    expiry_days: Number(form.expiry_days),
    evaluation_period_days: Number(form.evaluation_period_days) || null,
    is_active: isActive,
    visit_threshold: form.rule_type === "visit" ? Number(form.visit_threshold) : null,
    spending_threshold:
      form.rule_type === "spending" ? Number(form.spending_threshold) : null,
    reward_percentage:
      form.reward_type === "percentage" || form.reward_type === "both"
        ? Number(form.reward_percentage)
        : null,
    reward_amount:
      form.reward_type === "fixed" || form.reward_type === "both"
        ? Number(form.reward_amount)
        : null,
  };
  return body;
}

export default function LoyaltyPage() {
  const { staff } = useAuth();
  const [rules, setRules] = useState<Rule[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<RuleForm>(emptyForm);

  async function load() {
    const data = await api.loyaltyRules();
    setRules(data.items);
  }

  useEffect(() => {
    if (staff && staff.role !== "admin") return;
    load().catch((err) => setError(err instanceof Error ? err.message : "Load failed"));
  }, [staff]);

  if (staff && staff.role !== "admin") return <Navigate to="/" replace />;

  function startEdit(rule: Rule) {
    setEditingId(rule.id);
    setForm({
      rule_name: rule.rule_name,
      rule_type: rule.rule_type,
      visit_threshold: rule.visit_threshold != null ? String(rule.visit_threshold) : "10",
      spending_threshold:
        rule.spending_threshold != null ? String(rule.spending_threshold) : "5000",
      reward_type: rule.reward_type,
      reward_percentage:
        rule.reward_percentage != null ? String(rule.reward_percentage) : "15",
      reward_amount: rule.reward_amount != null ? String(rule.reward_amount) : "500",
      expiry_days: String(rule.expiry_days),
      evaluation_period_days:
        rule.evaluation_period_days != null ? String(rule.evaluation_period_days) : "90",
    });
    setError(null);
    setMessage(null);
  }

  function cancelEdit() {
    setEditingId(null);
    setForm(emptyForm);
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setMessage(null);
    try {
      if (editingId) {
        const existing = rules.find((r) => r.id === editingId);
        await api.updateLoyaltyRule(
          editingId,
          buildRulePayload(form, existing?.is_active ?? true),
        );
        setMessage("Loyalty rule updated");
        cancelEdit();
      } else {
        await api.createLoyaltyRule(buildRulePayload(form, true));
        setMessage("Loyalty rule created");
        setForm(emptyForm);
      }
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : editingId ? "Update failed" : "Create failed");
    }
  }

  async function onDeactivate(id: string) {
    if (!confirm("Deactivate this loyalty rule? It will stop issuing new rewards.")) return;
    setError(null);
    setMessage(null);
    try {
      await api.deactivateLoyaltyRule(id);
      setMessage("Loyalty rule deactivated");
      if (editingId === id) cancelEdit();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Deactivate failed");
    }
  }

  async function onActivate(id: string) {
    setError(null);
    setMessage(null);
    try {
      await api.activateLoyaltyRule(id);
      setMessage("Loyalty rule activated");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Activate failed");
    }
  }

  async function onDelete(rule: Rule) {
    if (
      !confirm(
        `Permanently delete "${rule.rule_name}"? This only works if no rewards were issued from it.`,
      )
    ) {
      return;
    }
    setError(null);
    setMessage(null);
    try {
      await api.deleteLoyaltyRule(rule.id);
      setMessage("Loyalty rule deleted");
      if (editingId === rule.id) cancelEdit();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    }
  }

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <h1>Loyalty rules</h1>
          <p className="muted">Visit / spend thresholds and reward configuration (admin)</p>
        </div>
      </header>

      <form className="panel form-grid" onSubmit={onSubmit}>
        <h2>{editingId ? "Edit rule" : "New rule"}</h2>
        <label>
          Name
          <input
            value={form.rule_name}
            onChange={(e) => setForm({ ...form, rule_name: e.target.value })}
            required
          />
        </label>
        <div className="inline-fields">
          <label>
            Rule type
            <select
              value={form.rule_type}
              onChange={(e) => setForm({ ...form, rule_type: e.target.value })}
            >
              <option value="visit">Visit</option>
              <option value="spending">Spending</option>
            </select>
          </label>
          <label>
            Reward type
            <select
              value={form.reward_type}
              onChange={(e) => setForm({ ...form, reward_type: e.target.value })}
            >
              <option value="percentage">Percentage</option>
              <option value="fixed">Fixed</option>
              <option value="both">Both</option>
            </select>
          </label>
        </div>
        <div className="inline-fields">
          {form.rule_type === "visit" ? (
            <label>
              Visit threshold
              <input
                type="number"
                value={form.visit_threshold}
                onChange={(e) => setForm({ ...form, visit_threshold: e.target.value })}
              />
            </label>
          ) : (
            <label>
              Spend threshold (ETB)
              <input
                type="number"
                value={form.spending_threshold}
                onChange={(e) => setForm({ ...form, spending_threshold: e.target.value })}
              />
            </label>
          )}
          <label>
            Expiry days
            <input
              type="number"
              value={form.expiry_days}
              onChange={(e) => setForm({ ...form, expiry_days: e.target.value })}
            />
          </label>
          <label>
            Period days
            <input
              type="number"
              value={form.evaluation_period_days}
              onChange={(e) => setForm({ ...form, evaluation_period_days: e.target.value })}
            />
          </label>
        </div>
        <div className="inline-fields">
          {(form.reward_type === "percentage" || form.reward_type === "both") && (
            <label>
              Reward %
              <input
                type="number"
                value={form.reward_percentage}
                onChange={(e) => setForm({ ...form, reward_percentage: e.target.value })}
              />
            </label>
          )}
          {(form.reward_type === "fixed" || form.reward_type === "both") && (
            <label>
              Reward amount
              <input
                type="number"
                value={form.reward_amount}
                onChange={(e) => setForm({ ...form, reward_amount: e.target.value })}
              />
            </label>
          )}
        </div>
        <div className="toolbar">
          <button type="submit">{editingId ? "Save changes" : "Create rule"}</button>
          {editingId && (
            <button type="button" className="ghost-btn" onClick={cancelEdit}>
              Cancel
            </button>
          )}
        </div>
      </form>

      {error && <p className="error-text">{error}</p>}
      {message && <p className="ok-text">{message}</p>}

      <div className="table-wrap panel">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Threshold</th>
              <th>Reward</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {rules.map((r) => (
              <tr key={r.id}>
                <td>{r.rule_name}</td>
                <td>{r.rule_type}</td>
                <td>
                  {r.rule_type === "visit"
                    ? `${r.visit_threshold} visits`
                    : `${r.spending_threshold} ETB`}
                </td>
                <td>
                  {r.reward_type}
                  {r.reward_percentage != null ? ` ${r.reward_percentage}%` : ""}
                  {r.reward_amount != null ? ` ${r.reward_amount} ETB` : ""}
                </td>
                <td>
                  <span className={r.is_active ? "ok-text" : "error-text"}>
                    {r.is_active ? "Active" : "Inactive"}
                  </span>
                </td>
                <td>
                  <div className="row-actions">
                    <button type="button" className="ghost-btn" onClick={() => startEdit(r)}>
                      Edit
                    </button>
                    {r.is_active ? (
                      <button
                        type="button"
                        className="ghost-btn btn-danger"
                        onClick={() => onDeactivate(r.id)}
                      >
                        Deactivate
                      </button>
                    ) : (
                      <>
                        <button
                          type="button"
                          className="ghost-btn btn-ok"
                          onClick={() => onActivate(r.id)}
                        >
                          Activate
                        </button>
                        <button
                          type="button"
                          className="ghost-btn btn-danger"
                          onClick={() => onDelete(r)}
                        >
                          Delete
                        </button>
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
  );
}
