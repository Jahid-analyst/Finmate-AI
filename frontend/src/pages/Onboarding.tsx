import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, apiErrorMessage } from "../lib/api";

const USER_TYPES = [
  { value: "student", label: "Student" },
  { value: "employee", label: "Employee" },
  { value: "household", label: "Household" },
  { value: "freelancer", label: "Freelancer" },
  { value: "business_owner", label: "Small business owner" },
];

export default function Onboarding() {
  const navigate = useNavigate();
  const [userType, setUserType] = useState("student");
  const [monthlyIncome, setMonthlyIncome] = useState("");
  const [savingsTarget, setSavingsTarget] = useState("");
  const [goalText, setGoalText] = useState("");
  const [language, setLanguage] = useState("en");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await api.put("/auth/profile", {
        user_type: userType,
        monthly_income: Number(monthlyIncome) || 0,
        income_frequency: "monthly",
        preferred_language: language,
        preferred_currency: "BDT",
        savings_target: Number(savingsTarget) || 0,
        financial_goal_text: goalText,
      });
      navigate("/dashboard");
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-paper flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-lg bg-white border border-line rounded-lg p-8">
        <h1 className="font-display font-semibold text-2xl text-ink mb-1">Let's set up FinMate AI</h1>
        <p className="text-sm text-muted mb-6">A few quick questions so your dashboard and AI insights are personalized.</p>

        {error && <div className="text-sm text-danger bg-danger/10 rounded px-3 py-2 mb-4">{error}</div>}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm text-muted mb-2">I am a…</label>
            <div className="grid grid-cols-2 gap-2">
              {USER_TYPES.map((t) => (
                <button
                  type="button"
                  key={t.value}
                  onClick={() => setUserType(t.value)}
                  className={`text-sm text-left px-3 py-2 rounded border transition-colors ${
                    userType === t.value ? "border-forest bg-forest/5 text-forest font-medium" : "border-line text-ink hover:border-forest/40"
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-muted mb-1">Monthly income (৳)</label>
              <input
                type="number" min={0} value={monthlyIncome}
                onChange={(e) => setMonthlyIncome(e.target.value)}
                className="w-full border border-line rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-forest/30"
                placeholder="30000"
              />
            </div>
            <div>
              <label className="block text-sm text-muted mb-1">Savings target (৳)</label>
              <input
                type="number" min={0} value={savingsTarget}
                onChange={(e) => setSavingsTarget(e.target.value)}
                className="w-full border border-line rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-forest/30"
                placeholder="50000"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm text-muted mb-1">Main financial goal (optional)</label>
            <input
              value={goalText}
              onChange={(e) => setGoalText(e.target.value)}
              className="w-full border border-line rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-forest/30"
              placeholder="e.g. Save for a laptop"
            />
          </div>

          <div>
            <label className="block text-sm text-muted mb-2">Preferred language</label>
            <div className="flex gap-2">
              {[{ v: "en", l: "English" }, { v: "bn", l: "বাংলা" }].map((opt) => (
                <button
                  type="button"
                  key={opt.v}
                  onClick={() => setLanguage(opt.v)}
                  className={`px-4 py-1.5 rounded text-sm border transition-colors ${
                    language === opt.v ? "border-forest bg-forest/5 text-forest font-medium" : "border-line text-ink"
                  }`}
                >
                  {opt.l}
                </button>
              ))}
            </div>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-forest text-white rounded py-2.5 text-sm font-medium hover:bg-forest-light transition-colors disabled:opacity-60"
          >
            {submitting ? "Saving…" : "Go to my dashboard"}
          </button>
        </form>
      </div>
    </div>
  );
}
