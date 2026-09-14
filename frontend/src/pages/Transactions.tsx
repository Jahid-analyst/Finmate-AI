import { FormEvent, useEffect, useState } from "react";
import { api, apiErrorMessage } from "../lib/api";
import { formatBDT, formatDate } from "../lib/format";

interface Transaction {
  id: string;
  amount: number;
  txn_type: string;
  category_name: string;
  description: string;
  payment_method: string;
  occurred_on: string;
  source: string;
  ai_flagged_anomaly: boolean;
}

interface ParsedDraft {
  amount: number | null;
  txn_type: string;
  category_name: string | null;
  description: string | null;
  payment_method: string | null;
  used_ai: boolean;
  confidence: string;
}

const PAYMENT_METHODS = ["cash", "bank", "card", "mfs", "other"];

export default function Transactions() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [categories, setCategories] = useState<{ expense: string[]; income: string[] }>({ expense: [], income: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [nlText, setNlText] = useState("");
  const [draft, setDraft] = useState<ParsedDraft | null>(null);
  const [parsing, setParsing] = useState(false);

  const [showManual, setShowManual] = useState(false);
  const [manual, setManual] = useState({
    amount: "", txn_type: "expense", category_name: "", description: "", payment_method: "cash",
  });

  const [search, setSearch] = useState("");
  const [filterType, setFilterType] = useState("");

  async function loadTransactions() {
    const params: Record<string, string> = {};
    if (search) params.q = search;
    if (filterType) params.txn_type = filterType;
    const res = await api.get("/transactions", { params });
    setTransactions(res.data);
  }

  useEffect(() => {
    async function init() {
      const cats = await api.get("/transactions/categories/list");
      setCategories(cats.data);
      await loadTransactions();
      setLoading(false);
    }
    init();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!loading) loadTransactions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search, filterType]);

  async function handleParse(e: FormEvent) {
    e.preventDefault();
    if (!nlText.trim()) return;
    setParsing(true);
    setError(null);
    try {
      const res = await api.post("/transactions/parse", { text: nlText });
      setDraft(res.data);
    } catch (err) {
      setError(apiErrorMessage(err, "Could not understand that transaction. Try adding it manually."));
    } finally {
      setParsing(false);
    }
  }

  async function confirmDraft() {
    if (!draft || !draft.amount) return;
    try {
      await api.post("/transactions", {
        amount: draft.amount,
        txn_type: draft.txn_type,
        category_name: draft.category_name || "Other",
        description: draft.description || nlText,
        payment_method: draft.payment_method || "cash",
      });
      setDraft(null);
      setNlText("");
      await loadTransactions();
    } catch (err) {
      setError(apiErrorMessage(err));
    }
  }

  async function submitManual(e: FormEvent) {
    e.preventDefault();
    if (!manual.amount || !manual.category_name) return;
    try {
      await api.post("/transactions", {
        amount: Number(manual.amount),
        txn_type: manual.txn_type,
        category_name: manual.category_name,
        description: manual.description,
        payment_method: manual.payment_method,
      });
      setManual({ amount: "", txn_type: "expense", category_name: "", description: "", payment_method: "cash" });
      setShowManual(false);
      await loadTransactions();
    } catch (err) {
      setError(apiErrorMessage(err));
    }
  }

  async function handleDelete(id: string) {
    await api.delete(`/transactions/${id}`);
    await loadTransactions();
  }

  const availableCategories = manual.txn_type === "income" ? categories.income : categories.expense;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="font-display font-semibold text-2xl text-ink">Transactions</h1>
        <button
          onClick={() => setShowManual((v) => !v)}
          className="text-sm border border-forest text-forest rounded px-4 py-2 hover:bg-forest/5 transition-colors"
        >
          {showManual ? "Cancel" : "Add manually"}
        </button>
      </div>

      {error && <div className="text-sm text-danger bg-danger/10 rounded px-3 py-2">{error}</div>}

      {/* Natural-language entry */}
      <div className="bg-white border border-line rounded-lg p-5">
        <h2 className="font-display font-semibold text-sm text-ink mb-1">Quick add — just describe it</h2>
        <p className="text-xs text-muted mb-3">
          e.g. "I spent 250 taka on lunch today" or "আজকে রিকশায় ১২০ টাকা খরচ হয়েছে"
        </p>
        <form onSubmit={handleParse} className="flex gap-2">
          <input
            value={nlText}
            onChange={(e) => setNlText(e.target.value)}
            className="flex-1 border border-line rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-forest/30"
            placeholder="Type a transaction in plain English or Bengali…"
          />
          <button
            type="submit"
            disabled={parsing}
            className="bg-forest text-white rounded px-4 py-2 text-sm font-medium hover:bg-forest-light transition-colors disabled:opacity-60"
          >
            {parsing ? "Reading…" : "Parse"}
          </button>
        </form>

        {draft && (
          <div className="mt-4 border border-gold/60 bg-gold/5 rounded p-4">
            <div className="text-xs text-muted mb-2">
              {draft.used_ai ? "AI-parsed draft" : "Rule-based draft (AI unavailable)"} — please confirm before saving:
            </div>
            <div className="grid grid-cols-2 gap-3 text-sm mb-3">
              <div><span className="text-muted">Amount:</span> <span className="money">{draft.amount ? formatBDT(draft.amount) : "—"}</span></div>
              <div><span className="text-muted">Type:</span> {draft.txn_type}</div>
              <div><span className="text-muted">Category:</span> {draft.category_name}</div>
              <div><span className="text-muted">Payment:</span> {draft.payment_method || "unknown"}</div>
            </div>
            <div className="flex gap-2">
              <button onClick={confirmDraft} className="bg-forest text-white text-sm rounded px-4 py-1.5 hover:bg-forest-light">
                Confirm &amp; save
              </button>
              <button onClick={() => setDraft(null)} className="text-sm text-muted px-4 py-1.5 hover:text-ink">
                Discard
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Manual entry form */}
      {showManual && (
        <form onSubmit={submitManual} className="bg-white border border-line rounded-lg p-5 grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-muted mb-1">Type</label>
            <select
              value={manual.txn_type}
              onChange={(e) => setManual({ ...manual, txn_type: e.target.value, category_name: "" })}
              className="w-full border border-line rounded px-3 py-2 text-sm"
            >
              <option value="expense">Expense</option>
              <option value="income">Income</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-muted mb-1">Amount (৳)</label>
            <input
              type="number" min={0} required value={manual.amount}
              onChange={(e) => setManual({ ...manual, amount: e.target.value })}
              className="w-full border border-line rounded px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs text-muted mb-1">Category</label>
            <select
              required value={manual.category_name}
              onChange={(e) => setManual({ ...manual, category_name: e.target.value })}
              className="w-full border border-line rounded px-3 py-2 text-sm"
            >
              <option value="">Select…</option>
              {availableCategories.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-muted mb-1">Payment method</label>
            <select
              value={manual.payment_method}
              onChange={(e) => setManual({ ...manual, payment_method: e.target.value })}
              className="w-full border border-line rounded px-3 py-2 text-sm"
            >
              {PAYMENT_METHODS.map((m) => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>
          <div className="col-span-2">
            <label className="block text-xs text-muted mb-1">Description</label>
            <input
              value={manual.description}
              onChange={(e) => setManual({ ...manual, description: e.target.value })}
              className="w-full border border-line rounded px-3 py-2 text-sm"
            />
          </div>
          <div className="col-span-2">
            <button type="submit" className="bg-forest text-white text-sm rounded px-4 py-2 hover:bg-forest-light">
              Save transaction
            </button>
          </div>
        </form>
      )}

      {/* Filters */}
      <div className="flex gap-3">
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search description or category…"
          className="border border-line rounded px-3 py-2 text-sm flex-1"
        />
        <select value={filterType} onChange={(e) => setFilterType(e.target.value)} className="border border-line rounded px-3 py-2 text-sm">
          <option value="">All types</option>
          <option value="income">Income</option>
          <option value="expense">Expense</option>
        </select>
      </div>

      {/* Table */}
      <div className="bg-white border border-line rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-line text-left text-xs uppercase tracking-wide text-muted">
              <th className="px-4 py-3">Date</th>
              <th className="px-4 py-3">Category</th>
              <th className="px-4 py-3">Description</th>
              <th className="px-4 py-3">Payment</th>
              <th className="px-4 py-3 text-right">Amount</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {transactions.length === 0 && (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-muted">No transactions yet.</td></tr>
            )}
            {transactions.map((t) => (
              <tr key={t.id} className="border-b border-line last:border-0 hover:bg-paper/60">
                <td className="px-4 py-3 text-muted">{formatDate(t.occurred_on)}</td>
                <td className="px-4 py-3">{t.category_name}</td>
                <td className="px-4 py-3 text-muted">{t.description || "—"}</td>
                <td className="px-4 py-3 text-muted capitalize">{t.payment_method}</td>
                <td className={`px-4 py-3 text-right money ${t.txn_type === "income" ? "text-ok" : "text-ink"}`}>
                  {t.txn_type === "income" ? "+" : "-"}{formatBDT(t.amount)}
                </td>
                <td className="px-4 py-3 text-right">
                  <button onClick={() => handleDelete(t.id)} className="text-xs text-muted hover:text-danger">
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
