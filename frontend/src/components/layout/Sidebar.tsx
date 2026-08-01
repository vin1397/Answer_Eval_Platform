import { NavLink } from "react-router-dom";
import clsx from "clsx";
import {
  LayoutDashboard, BookOpen, CalendarRange, GraduationCap, Users, FileText,
  ClipboardCheck, ScanLine, BrainCircuit, ShieldCheck, BarChart3, PieChart,
  Settings, LogOut,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";

const NAV_ITEMS = [
  { to: "/app/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/app/subjects", label: "Subjects", icon: BookOpen },
  { to: "/app/semesters", label: "Semester & Scheme", icon: CalendarRange },
  { to: "/app/faculty", label: "Faculty", icon: GraduationCap },
  { to: "/app/students", label: "Students", icon: Users },
  { to: "/app/question-papers", label: "Question Papers", icon: FileText },
  { to: "/app/model-answers", label: "Model Answers", icon: ClipboardCheck },
  { to: "/app/examinations", label: "Examinations", icon: CalendarRange },
  { to: "/app/answer-scripts", label: "Answer Scripts", icon: ScanLine },
  { to: "/app/ai-evaluation", label: "AI Evaluation", icon: BrainCircuit },
  { to: "/app/teacher-review", label: "Teacher Review", icon: ShieldCheck },
  { to: "/app/reports", label: "Reports", icon: BarChart3 },
  { to: "/app/analytics", label: "Analytics", icon: PieChart },
  { to: "/app/settings", label: "Settings", icon: Settings },
];

export default function Sidebar() {
  const { logout, user } = useAuth();

  return (
    <aside className="fixed inset-y-0 left-0 z-30 hidden w-72 flex-col gap-1 overflow-y-auto bg-surface/70 dark:bg-dark-surface/80 p-5 backdrop-blur-xl lg:flex">
      <div className="mb-6 flex items-center gap-3 px-2">
        <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary text-white shadow-neo-flat">
          <BrainCircuit size={22} />
        </div>
        <div>
          <p className="text-sm font-bold leading-tight">AnswerEval AI</p>
          <p className="text-[11px] text-ink/50 dark:text-dark-ink/50">
            {user?.role === "admin" ? "Administrator" : "Faculty"}
          </p>
        </div>
      </div>

      <nav className="flex flex-1 flex-col gap-1">
        {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) => clsx("sidebar-link", isActive && "active")}
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>

      <button onClick={logout} className="sidebar-link mt-2 text-red-500 hover:bg-red-50">
        <LogOut size={18} />
        Logout
      </button>
    </aside>
  );
}
