import { NavLink } from "react-router-dom";
import clsx from "clsx";
import {
  LayoutDashboard, BookOpen, CalendarRange, GraduationCap, Users, FileText,
  ClipboardCheck, ScanLine, BrainCircuit, ShieldCheck, BarChart3, PieChart,
  Settings, LogOut, Library,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";

/**
 * Navigation mirrors the real evaluation lifecycle so the product reads as a
 * pipeline rather than a list of unrelated screens:
 *   1. Setup        — academic structure + question banks + model answers
 *   2. Examine      — create exams, upload student scripts
 *   3. AI Evaluate  — OCR + scoring, then teacher verification
 *   4. Insights     — reports, analytics, settings
 */
const NAV_GROUPS: { label: string; items: { to: string; label: string; icon: any }[] }[] = [
  {
    label: "Overview",
    items: [{ to: "/app/dashboard", label: "Dashboard", icon: LayoutDashboard }],
  },
  {
    label: "Setup",
    items: [
      { to: "/app/subjects", label: "Subjects", icon: BookOpen },
      { to: "/app/semesters", label: "Semester & Scheme", icon: CalendarRange },
      { to: "/app/faculty", label: "Faculty", icon: GraduationCap },
      { to: "/app/students", label: "Students", icon: Users },
      { to: "/app/question-papers", label: "Question Papers", icon: FileText },
      { to: "/app/model-answers", label: "Model Answers", icon: ClipboardCheck },
    ],
  },
  {
    label: "Examine",
    items: [
      { to: "/app/examinations", label: "Examinations", icon: CalendarRange },
      { to: "/app/answer-scripts", label: "Answer Scripts", icon: ScanLine },
    ],
  },
  {
    label: "Evaluate",
    items: [
      { to: "/app/ai-evaluation", label: "AI Evaluation", icon: BrainCircuit },
      { to: "/app/teacher-review", label: "Teacher Review", icon: ShieldCheck },
    ],
  },
  {
    label: "Insights",
    items: [
      { to: "/app/reports", label: "Reports", icon: BarChart3 },
      { to: "/app/analytics", label: "Analytics", icon: PieChart },
      { to: "/app/settings", label: "Settings", icon: Settings },
    ],
  },
];

export default function Sidebar() {
  const { logout, user } = useAuth();

  return (
    <aside className="fixed inset-y-0 left-0 z-30 hidden w-72 flex-col gap-1 overflow-y-auto bg-surface/70 p-5 backdrop-blur-xl lg:flex">
      <div className="mb-6 flex items-center gap-3 px-2">
        <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary text-white shadow-neo-flat">
          <BrainCircuit size={22} />
        </div>
        <div>
          <p className="text-sm font-bold leading-tight">AnswerEval AI</p>
          <p className="text-[11px] text-ink/50">
            {user?.role === "admin" ? "Administrator" : "Faculty"}
          </p>
        </div>
      </div>

      <nav className="flex flex-1 flex-col gap-4">
        {NAV_GROUPS.map((group) => (
          <div key={group.label}>
            <p className="mb-1 flex items-center gap-1.5 px-3 text-[10px] font-bold uppercase tracking-widest text-ink/35">
              {group.label === "Setup" && <Library size={10} />}
              {group.label}
            </p>
            <div className="flex flex-col gap-0.5">
              {group.items.map(({ to, label, icon: Icon }) => (
                <NavLink
                  key={to}
                  to={to}
                  className={({ isActive }) => clsx("sidebar-link", isActive && "active")}
                >
                  <Icon size={18} />
                  {label}
                </NavLink>
              ))}
            </div>
          </div>
        ))}
      </nav>

      <button onClick={logout} className="sidebar-link mt-2 text-red-500 hover:bg-red-50">
        <LogOut size={18} />
        Logout
      </button>
    </aside>
  );
}
