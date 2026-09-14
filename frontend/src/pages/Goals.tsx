import { FormEvent, useEffect, useState } from "react";
import { api, apiErrorMessage } from "../lib/api";
import { formatBDT, formatDate } from "../lib/format";

interface Goal {
  id: string;
  name: string;
  target_amount: number;
  current_amount: number;
  deadline: string | null;
  progress_percent: number;
  required_monthly_saving: number | null;
}

export default function Goals() {
  const [goals, setGoals] = useState<Goal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: "", target_amount: "", current_amount: "", deadline: "" });
  const [contribution, setContribution] = useState<Record<string, string>>({});

  async function load() {
    const res = await api.get("/goals");
    setGoals(res.data);
    setLoading(false);
  }

  useEffect(() => {
    load();
  }, []);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    if (!form.name || !form.target_amount) return;
    try {
      await api.post("/goals", {
        name: form.name,
        target_amount: Number(form.target_amount),
        current_amount: Number(form.current_amount) || 0,
        deadline: form.deadline ? new Date(form.deadline).toISOString() : null,
      });
      setForm({ name: "", target_amount: "", current_amount: "", deadline: "" });
      setShowForm(false);
      await load();
    } catch (err) {
      setError(apiErrorMessage(err));
    }
  }

  async function handleContribute(goalId: string) {
    const amount = Number(contribution[goalId]);
    if (!amount || amount <= 0) return;
    await api.post(`/goals/${goalId}/contribute`, { amount });
    setContribution((prev) => ({ ...prev, [goalId]: "" }));
    await load();
  }

  async function handleDelete(goalId: string) {
    await api.delete(`/goals/${goalId}`);
    await load();
  }

  if (loading) return <div className="text-muted">Loading goals…</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="font-display font-semibold text-2xl text-ink">Savings goals</h1>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="text-sm border border-forest text-forest rounded px-4 py-2 hover:bg-forest/5"
        >
          {showForm ? "Cancel" : "New goal"}
        </button>
      </div>

      {error && <div className="text-sm text-danger bg-danger/10 rounded px-3 py-2">{error}</div>}

      {showForm && (
        <form onSubmit={handleCreate} className="bg-white border border-line rounded-lg p-5 grid grid-cols-2 gap-4">
          <div className="col-span-2">
            <label className="block text-xs text-muted mb-1">Goal name</label>
            <input
              required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full border border-line rounded px-3 py-2 text-sm" placeholder="e.g. New laptop"
            />
          </div>
          <div>
            <label className="block text-xs text-muted mb-1">Target amount (৳)</label>
            <input
              type="number" min={0} required value={form.target_amount}
              onChange={(e) => setForm({ ...form, target_amount: e.target.value })}
              className="w-full border border-line rounded px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs text-muted mb-1">Already saved (৳)</label>
            <input
              type="number" min={0} value={form.current_amount}
              onChange={(e) => setForm({ ...form, current_amount: e.target.value })}
              className="w-full border border-line rounded px-3 py-2 text-sm"
            />
          </div>
          <div className="col-span-2">
            <label className="block text-xs text-muted mb-1">Deadline (optional)</label>
            <input
              type="date" value={form.deadline}
              onChange={(e) => setForm({ ...form, deadline: e.target.value })}
              className="w-full border border-line rounded px-3 py-2 text-sm"
            />
          </div>
          <div className="col-span-2">
            <button type="submit" className="bg-forest text-white text-sm rounded px-4 py-2 hover:bg-forest-light">
              Create goal
            </button>
          </div>
        </form>
      )}

      {goals.length === 0 && !showForm && (
        <div className="bg-white border border-line rounded-lg p-8 text-center text-muted text-sm">
          No savings goals yet. Create one to start tracking your progress.
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {goals.map((g) => (
          <div key={g.id} className="bg-white border border-line rounded-lg p-5">
            <div className="flex justify-between items-start mb-2">
              <h3 className="font-display font-semibold text-ink">{g.name}</h3>
              <button onClick={() => handleDelete(g.id)} className="text-xs text-muted hover:text-danger">
                Delete
              </button>
            </div>
            <div className="text-sm text-muted mb-2">
              <span className="money text-ink">{formatBDT(g.current_amount)}</span> of{" "}
              <span className="money">{formatBDT(g.target_amount)}</span>
            </div>
            <div className="h-2 bg-line rounded-full overflow-hidden mb-3">
              <div className="h-full bg-gold rounded-full" style={{ width: `${g.progress_percent}%` }} />
            </div>
            <div className="text-xs text-muted mb-3 space-y-0.5">
              <div>{g.progress_percent}% complete</div>
              {g.deadline && <div>Deadline: {formatDate(g.deadline)}</div>}
              {g.required_monthly_saving !== null && (
                <div>Save about {formatBDT(g.required_monthly_saving)}/month to hit your deadline</div>
              )}
            </div>
            <div className="flex gap-2">
              <input
                type="number" min={0} placeholder="Add amount"
                value={contribution[g.id] || ""}
                onChange={(e) => setContribution((prev) => ({ ...prev, [g.id]: e.target.value }))}
                className="flex-1 border border-line rounded px-3 py-1.5 text-sm"
              />
              <button
                onClick={() => handleContribute(g.id)}
                className="text-sm bg-forest text-white rounded px-3 py-1.5 hover:bg-forest-light"
              >
                Add
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
