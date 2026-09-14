import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { apiErrorMessage } from "../lib/api";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
      navigate("/dashboard");
    } catch (err) {
      setError(apiErrorMessage(err, "Incorrect email or password."));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-forest flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="font-display font-semibold text-2xl text-paper">FinMate AI</div>
          <div className="text-gold-light text-sm mt-1">Your Money. Smarter.</div>
        </div>

        <form onSubmit={handleSubmit} className="bg-white rounded-lg p-7 space-y-4">
          <h1 className="font-display font-semibold text-xl text-ink">Log in</h1>

          {error && <div className="text-sm text-danger bg-danger/10 rounded px-3 py-2">{error}</div>}

          <div>
            <label className="block text-sm text-muted mb-1">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full border border-line rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-forest/30"
              placeholder="you@example.com"
            />
          </div>
          <div>
            <label className="block text-sm text-muted mb-1">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full border border-line rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-forest/30"
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-forest text-white rounded py-2.5 text-sm font-medium hover:bg-forest-light transition-colors disabled:opacity-60"
          >
            {submitting ? "Logging in…" : "Log in"}
          </button>

          <p className="text-sm text-muted text-center">
            New here?{" "}
            <Link to="/register" className="text-forest font-medium hover:underline">
              Create an account
            </Link>
          </p>
        </form>

        <div className="mt-5 text-center text-xs text-paper/70">
          Demo accounts: student@demo.finmate.ai / employee@demo.finmate.ai / household@demo.finmate.ai
          <br />
          password: demo1234
        </div>
      </div>
    </div>
  );
}
