import { Link } from "react-router-dom";

const FEATURES = [
  { title: "Natural-language entry", body: "Type \"lunch 250 taka\" or say it in Bengali — FinMate AI extracts the amount, category, and date for you to confirm." },
  { title: "Real budgets, real numbers", body: "Every chart, percentage, and alert is calculated from your actual transactions — never fabricated." },
  { title: "AI insights you can trust", body: "Spending increases, overspending warnings, and unusual transactions, each traceable back to the data behind it." },
  { title: "Works without AI, too", body: "If the AI is unavailable, tracking, budgeting, and analytics keep working — AI only adds on top." },
];

const USER_TYPES = ["Students", "Employees", "Households", "Freelancers", "Small business owners"];

export default function Landing() {
  return (
    <div className="bg-paper text-ink">
      <header className="max-w-5xl mx-auto px-6 py-6 flex items-center justify-between">
        <div className="font-display font-semibold text-lg">FinMate AI</div>
        <div className="flex gap-3">
          <Link to="/login" className="text-sm px-4 py-2 rounded hover:bg-forest/5">Log in</Link>
          <Link to="/register" className="text-sm px-4 py-2 rounded bg-forest text-white hover:bg-forest-light">Get started</Link>
        </div>
      </header>

      <section className="max-w-5xl mx-auto px-6 pt-16 pb-20">
        <p className="text-gold-dark text-sm font-medium mb-4">Personal finance for Bangladesh, built with AI</p>
        <h1 className="font-display font-semibold text-5xl leading-tight max-w-2xl">
          Your money.<br />Smarter.
        </h1>
        <p className="text-muted text-lg mt-6 max-w-xl">
          FinMate AI helps you track, understand, and improve your personal finances —
          in Taka, in Bengali or English, with AI insights grounded in your real numbers.
        </p>
        <div className="mt-8 flex gap-4">
          <Link to="/register" className="bg-forest text-white rounded px-6 py-3 text-sm font-medium hover:bg-forest-light">
            Create your free account
          </Link>
        </div>
      </section>

      <section className="border-t border-line bg-white">
        <div className="max-w-5xl mx-auto px-6 py-16">
          <h2 className="font-display font-semibold text-2xl mb-2">The problem</h2>
          <p className="text-muted max-w-xl">
            Most students, employees, and households in Bangladesh don't have a simple way to track
            daily cash and mobile-payment expenses, understand where money actually goes, or get
            personalized guidance in their own language.
          </p>
        </div>
      </section>

      <section className="max-w-5xl mx-auto px-6 py-16">
        <h2 className="font-display font-semibold text-2xl mb-8">What FinMate AI does</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {FEATURES.map((f) => (
            <div key={f.title} className="border-l-2 border-gold pl-4">
              <h3 className="font-display font-semibold text-ink mb-1">{f.title}</h3>
              <p className="text-sm text-muted">{f.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="border-t border-line bg-forest text-paper">
        <div className="max-w-5xl mx-auto px-6 py-16">
          <h2 className="font-display font-semibold text-2xl mb-6">Built for how you actually earn and spend</h2>
          <div className="flex flex-wrap gap-3">
            {USER_TYPES.map((t) => (
              <span key={t} className="border border-white/25 rounded-full px-4 py-1.5 text-sm">{t}</span>
            ))}
          </div>
        </div>
      </section>

      <section className="max-w-5xl mx-auto px-6 py-16 text-center">
        <h2 className="font-display font-semibold text-2xl mb-4">Ready to see where your money goes?</h2>
        <Link to="/register" className="inline-block bg-forest text-white rounded px-6 py-3 text-sm font-medium hover:bg-forest-light">
          Start tracking for free
        </Link>
      </section>

      <footer className="border-t border-line py-6 text-center text-xs text-muted">
        FinMate AI is a student/portfolio prototype. Not a licensed financial advisory service.
      </footer>
    </div>
  );
}
