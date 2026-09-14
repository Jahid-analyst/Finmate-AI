import { NavLink } from "react-router-dom";
import { useAuth } from "../lib/auth";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/transactions", label: "Transactions" },
  { to: "/budgets", label: "Budget" },
  { to: "/goals", label: "Savings Goals" },
  { to: "/assistant", label: "AI Assistant" },
];

export default function Sidebar() {
  const { user, logout } = useAuth();

  return (
    <aside className="w-60 shrink-0 bg-forest text-paper flex flex-col h-screen sticky top-0">
      <div className="px-6 py-6 border-b border-white/10">
        <div className="font-display font-semibold text-lg tracking-tight">FinMate AI</div>
        <div className="text-xs text-gold-light mt-0.5">Your Money. Smarter.</div>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `block px-3 py-2 rounded text-sm transition-colors ${
                isActive ? "bg-white/10 text-white font-medium" : "text-paper/70 hover:bg-white/5 hover:text-paper"
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="px-3 py-4 border-t border-white/10 text-sm">
        <div className="px-3 py-1.5 text-paper/70 truncate">{user?.full_name}</div>
        <button
          onClick={logout}
          className="w-full text-left px-3 py-2 rounded text-paper/70 hover:bg-white/5 hover:text-paper transition-colors"
        >
          Log out
        </button>
      </div>
    </aside>
  );
}
