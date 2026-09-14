import { FormEvent, useEffect, useState } from "react";
import { api, apiErrorMessage } from "../lib/api";
import { formatBDT, currentMonthKey, currentMonthLabel } from "../lib/format";

interface BudgetCategory {
  category_name: string;
  allocated_amount: number;
  spent: number;
  percent_used: number;
  status: string;
}

const STATUS_STYLE: Record<string, string> = {
  ok: "bg-ok",
  warning: "bg-gold",
  high_warning: "bg-warn",
  overspent: "bg-danger",
};

export default function Budgets() {
  const [categories, setCategories] = useState<BudgetCategory[]>([]);
  const [availableCategories, setAvailableCategories] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [rows, setRows] = useState<{ category_name: string; allocated_amount: string }[]>([
    { category_name: "", allocated_amount: "" },
  ]);

  const month = currentMonthKey();

  async function load() {
    try {
      const res = await api.get(`/budgets/${month}`);
      setCategories(res.data.categories);
    } catch {
      setCategories([]);
    }
    const cats = await api.get("/transactions/categories/list");
    setAvailableCategories(cats.data.expense);
    setLoading(false);
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function updateRow(idx: number, field: "category_name" | "allocated_amount", value: string) {
    setRows((prev) => prev.map((r, i) => (i === idx ? { ...r, [field]: value } : r)));
  }

  function addRow() {
    setRows((prev) => [...prev, { category_name: "", allocated_amount: "" }]);
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    const valid = rows.filter((r) => r.category_name && r.allocated_amount);
    if (valid.length === 0) return;
    try {
      await api.post("/budgets", {
        month,
        period: "monthly",
        categories: valid.map((r) => ({ category_name: r.category_name, allocated_amount: Number(r.allocated_amount) })),
      });
      setRows([{ category_name: "", allocated_amount: "" }]);
      await load();
    } catch (err) {
      setError(apiErrorMessage(err));
    }
  }

  if (loading) return <div className="text-muted">Loading budget…</div>;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display font-semibold text-2xl text-ink">Budget</h1>
        <p className="text-muted text-sm mt-0.5">{currentMonthLabel()}</p>
      </div>

      {error && <div className="text-sm text-danger bg-danger/10 rounded px-3 py-2">{error}</div>}

      {categories.length > 0 && (
        <div className="bg-white border border-line rounded-lg p-5 space-y-4">
          <h2 className="font-display font-semibold text-sm text-ink">This month's usage</h2>
          {categories.map((c) => (
            <div key={c.category_name}>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-ink">{c.category_name}</span>
                <span className="money text-muted">
                  {formatBDT(c.spent)} / {formatBDT(c.allocated_amount)} ({c.percent_used}%)
                </span>
              </div>
              <div className="h-2 bg-line rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${STATUS_STYLE[c.status] || "bg-forest"}`}
                  style={{ width: `${Math.min(100, c.percent_used)}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="bg-white border border-line rounded-lg p-5">
        <h2 className="font-display font-semibold text-sm text-ink mb-3">
          {categories.length > 0 ? "Update this month's budget" : "Set a budget for this month"}
        </h2>
        <form onSubmit={handleSubmit} className="space-y-3">
          {rows.map((row, idx) => (
            <div key={idx} className="flex gap-3">
              <select
                value={row.category_name}
                onChange={(e) => updateRow(idx, "category_name", e.target.value)}
                className="flex-1 border border-line rounded px-3 py-2 text-sm"
              >
                <option value="">Category…</option>
                {availableCategories.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
              <input
                type="number" min={0}
                placeholder="Amount (৳)"
                value={row.allocated_amount}
                onChange={(e) => updateRow(idx, "allocated_amount", e.target.value)}
                className="w-40 border border-line rounded px-3 py-2 text-sm"
              />
            </div>
          ))}
          <div className="flex gap-3">
            <button type="button" onClick={addRow} className="text-sm text-forest hover:underline">
              + Add another category
            </button>
          </div>
          <button type="submit" className="bg-forest text-white text-sm rounded px-4 py-2 hover:bg-forest-light">
            Save budget
          </button>
        </form>
      </div>
    </div>
  );
}
