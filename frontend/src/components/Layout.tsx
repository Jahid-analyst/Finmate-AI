import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../lib/auth";
import Sidebar from "./Sidebar";

export default function Layout() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center text-muted font-body">
        Loading FinMate AI…
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="flex min-h-screen bg-paper">
      <Sidebar />
      <main className="flex-1 px-8 py-8 max-w-6xl">
        <Outlet />
      </main>
    </div>
  );
}
