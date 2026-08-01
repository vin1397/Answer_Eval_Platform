import { useEffect, useState } from "react";
import { Outlet, Navigate } from "react-router-dom";
import Sidebar from "../components/layout/Sidebar";
import Navbar from "../components/layout/Navbar";
import { useAuth } from "../context/AuthContext";

export default function DashboardLayout() {
  const { isAuthenticated, isLoading } = useAuth();
  const [darkMode, setDarkMode] = useState(false);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", darkMode);
  }, [darkMode]);

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-surface dark:bg-dark-surface">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="min-h-screen bg-surface dark:bg-dark-surface">
      <Sidebar />
      <div className="lg:pl-72">
        <Navbar darkMode={darkMode} onToggleDark={() => setDarkMode((d) => !d)} />
        <main className="p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
