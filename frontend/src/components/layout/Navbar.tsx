import { useState } from "react";
import { Bell, Moon, Sun, Search } from "lucide-react";
import { useAuth } from "../../context/AuthContext";

export default function Navbar({
  darkMode,
  onToggleDark,
}: {
  darkMode: boolean;
  onToggleDark: () => void;
}) {
  const { user } = useAuth();
  const [query, setQuery] = useState("");

  return (
    <header className="sticky top-0 z-20 flex items-center justify-between gap-4 bg-surface/70 dark:bg-dark-surface/80 px-6 py-4 backdrop-blur-xl">
      <div className="neo-inset flex w-full max-w-sm items-center gap-2 rounded-2xl px-4 py-2.5">
        <Search size={16} className="text-ink/40 dark:text-dark-ink/40" />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search students, subjects, exams..."
          className="w-full bg-transparent text-sm outline-none placeholder:text-ink/40 dark:placeholder:text-dark-ink/40"
        />
      </div>

      <div className="flex items-center gap-3">
        <button
          onClick={onToggleDark}
          className="neo-card flex h-10 w-10 items-center justify-center !rounded-2xl !p-0"
        >
          {darkMode ? <Sun size={18} /> : <Moon size={18} />}
        </button>
        <button className="neo-card relative flex h-10 w-10 items-center justify-center !rounded-2xl !p-0">
          <Bell size={18} />
          <span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-accent" />
        </button>
        <div className="flex items-center gap-3 pl-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-primary font-semibold text-white shadow-neo-flat">
            {user?.full_name?.charAt(0) ?? "U"}
          </div>
          <div className="hidden sm:block">
            <p className="text-sm font-semibold leading-tight">{user?.full_name}</p>
            <p className="text-[11px] capitalize text-ink/50 dark:text-dark-ink/50">{user?.role}</p>
          </div>
        </div>
      </div>
    </header>
  );
}
