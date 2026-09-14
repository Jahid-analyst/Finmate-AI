import { useEffect, useState } from "react";
import {
  Cell, Pie, PieChart, ResponsiveContainer, Tooltip,
} from "recharts";
import { api } from "../lib/api";
import { formatBDT, currentMonthLabel } from "../lib/format";
import StatCard from "../components/StatCard";
import { useAuth } from "../lib/auth";

interface Summary {
  total_income: number;
  total_expense: number;
  balance: number;
  savings_rate: number;
  top_categories: { category: string; amount: number }[];
}

interface Insight {
  type: string;
  severity: string;
  message: string;
}

interface HealthScore {
  total_score: number;
  savings_score: number;
  budget_score: number;
  cashflow_score: number;
  goals_score: number;
}

interface Forecast {
  reliable: boolean;
  message: string;
  projected_expense?: number;
  projected_balance?: number;
}

const PIE_COLORS = ["#0E3B36", "#C89B4A", "#3E7A52", "#9E7A34", "#155048", "#B65C2B"];

const SEVERITY_STYLE: Record<string, string> = {
  warning: "border-l-warn bg-warn/5",
  critical: "border-l-danger bg-danger/5",
  positive: "border-l-ok bg-ok/5",
  info: "border-l-forest bg-forest/5",
};

export default function Dashboard() {
  const { user } = useAuth();
  const [summary, setSummary] = useState<Summary | null>(null);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [health, setHealth] = useState<HealthScore | null>(null);
  const [forecast, setForecast] = useState<Forecast | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      const [s, i, h, f] = await Promise.all([
        api.get("/analytics/summary"),
        api.get("/analytics/insights"),
        api.get("/analytics/health-score"),
        api.get("/analytics/forecast"),
      ]);
      setSummary(s.data);
      setInsights(i.data);
      setHealth(h.data);
      setForecast(f.data);
      setLoading(false);
    }
    load();
  }, []);

  if (loading || !summary) {
    return <div className="text-muted">Loading your dashboard…</div>;
  }

  const pieData = summary.top_categories.map((c) => ({ name: c.category, value: c.amount }));

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display font-semibold text-2xl text-ink">
          Welcome back{user ? `, ${user.full_name.split(" ")[0]}` : ""}
        </h1>
        <p className="text-muted text-sm mt-0.5">{currentMonthLabel()} overview</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Income" value={formatBDT(summary.total_income)} />
        <StatCard label="Expenses" value={formatBDT(summary.total_expense)} />
        <StatCard
          label="Balance"
          value={formatBDT(summary.balance)}
          tone={summary.balance >= 0 ? "positive" : "negative"}
        />
        <StatCard label="Savings rate" value={`${summary.savings_rate}%`} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 bg-white border border-line rounded-lg p-5">
          <h2 className="font-display font-semibold text-sm text-ink mb-3">Spending by category</h2>
          {pieData.length === 0 ? (
            <p className="text-sm text-muted py-10 text-center">No expenses recorded yet this month.</p>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" innerRadius={50} outerRadius={80} paddingAngle={2}>
                  {pieData.map((_, idx) => (
                    <Cell key={idx} fill={PIE_COLORS[idx % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(v: number) => formatBDT(v)} />
              </PieChart>
            </ResponsiveContainer>
          )}
          <div className="mt-3 space-y-1.5">
            {summary.top_categories.map((c, idx) => (
              <div key={c.category} className="flex items-center justify-between text-sm">
                <span className="flex items-center gap-2 text-ink">
                  <span className="w-2 h-2 rounded-full" style={{ background: PIE_COLORS[idx % PIE_COLORS.length] }} />
                  {c.category}
                </span>
                <span className="money text-muted">{formatBDT(c.amount)}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="lg:col-span-2 space-y-4">
          <div className="bg-white border border-line rounded-lg p-5">
            <div className="flex items-center justify-between mb-3">
              <h2 className="font-display font-semibold text-sm text-ink">Financial health score</h2>
              {health && <span className="money text-2xl text-forest">{health.total_score}/100</span>}
            </div>
            {health && (
              <div className="grid grid-cols-4 gap-3 text-xs text-muted">
                <div>Savings <div className="money text-ink text-sm">{health.savings_score}/25</div></div>
                <div>Budget <div className="money text-ink text-sm">{health.budget_score}/25</div></div>
                <div>Cash flow <div className="money text-ink text-sm">{health.cashflow_score}/25</div></div>
                <div>Goals <div className="money text-ink text-sm">{health.goals_score}/25</div></div>
              </div>
            )}
          </div>

          <div className="bg-white border border-line rounded-lg p-5">
            <h2 className="font-display font-semibold text-sm text-ink mb-2">End-of-month forecast</h2>
            {forecast && (
              <>
                <p className="text-sm text-ink">{forecast.message}</p>
                {forecast.reliable && (
                  <p className="text-xs text-muted mt-2">
                    This is a projection based on your spending pattern this month, not a guarantee.
                  </p>
                )}
              </>
            )}
          </div>
        </div>
      </div>

      <div>
        <h2 className="font-display font-semibold text-sm text-ink mb-3">AI insights</h2>
        {insights.length === 0 ? (
          <p className="text-sm text-muted bg-white border border-line rounded-lg p-5">
            No notable insights yet — as you add more transactions, FinMate AI will surface patterns here.
          </p>
        ) : (
          <div className="space-y-2">
            {insights.map((ins, idx) => (
              <div
                key={idx}
                className={`border-l-2 rounded px-4 py-3 text-sm text-ink ${SEVERITY_STYLE[ins.severity] || SEVERITY_STYLE.info}`}
              >
                {ins.message}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
