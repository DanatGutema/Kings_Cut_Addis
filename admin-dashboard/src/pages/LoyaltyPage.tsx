import { FormEvent, useEffect, useState } from "react";
import { api } from "../api/client";

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

export default function LoyaltyPage() {
  const [rules, setRules] = useState<Rule[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    rule_name: "",
    rule_type: "visit",
    visit_threshold: "10",
    spending_threshold: "5000",
    reward_type: "percentage",
    reward_percentage: "15",
    reward_amount: "500",
    expiry_days: "30",
    evaluation_period_days: "90",
  });

  async function load() {
    const data = await api.loyaltyRules();
    setRules(data.items);
  }

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Load failed"));
  }, []);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const body: Record<string, unknown> = {
        rule_name: form.rule_name.trim(),
        rule_type: form.rule_type,
        reward_type: form.reward_type,
        expiry_days: Number(form.expiry_days),
        evaluation_period_days: Number(form.evaluation_period_days) || null,
        is_active: true,
      };
      if (form.rule_type === "visit") body.visit_threshold = Number(form.visit_threshold);
      if (form.rule_type === "spending") body.spending_threshold = Number(form.spending_threshold);
      if (form.reward_type === "percentage" || form.reward_type === "both") {
        body.reward_percentage = Number(form.reward_percentage);
      }
      if (form.reward_type === "fixed" || form.reward_type === "both") {
        body.reward_amount = Number(form.reward_amount);
      }
      await api.createLoyaltyRule(body);
      setForm((f) => ({ ...f, rule_name: "" }));
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Create failed");
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

      <form className="panel form-grid" onSubmit={onCreate}>
        <h2>New rule</h2>
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
        <button type="submit">Create rule</button>
      </form>

      {error && <p className="error-text">{error}</p>}

      <div className="table-wrap panel">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Threshold</th>
              <th>Reward</th>
              <th>Active</th>
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
                <td>{r.is_active ? "Yes" : "No"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
