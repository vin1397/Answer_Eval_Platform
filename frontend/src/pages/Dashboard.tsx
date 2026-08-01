import { useEffect, useState } from "react";
import {
  BookOpen, CalendarRange, Users, Clock, TrendingUp, CheckCircle2, Upload, FileText, BarChart3,
} from "lucide-react";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, PieChart, Pie, Cell,
  LineChart, Line, CartesianGrid,
} from "recharts";
import api from "../services/api";
import NeoCard from "../components/ui/NeoCard";
import StatCard from "../components/ui/StatCard";
import Badge from "../components/ui/Badge";
import type { DashboardSummary } from "../types";
import { Link } from "react-router-dom";

const PIE_COLORS = ["#9C8CD4", "#7C6AC8", "#C9BFF0", "#5B4E96"];

export default function Dashboard() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [charts, setCharts] = useState<any>(null);
  const [activity, setActivity] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get("/dashboard/summary"),
      api.get("/dashboard/charts"),
      api.get("/dashboard/recent-activity"),
    ])
      .then(([s, c, a]) => {
        setSummary(s.data);
        setCharts(c.data);
        setActivity(a.data);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const cards = summary
    ? [
        { label: "Total Subjects", value: summary.total_subjects, icon: <BookOpen size={20} /> },
        { label: "Total Exams", value: summary.total_exams, icon: <CalendarRange size={20} /> },
        { label: "Students Evaluated", value: summary.students_evaluated, icon: <Users size={20} /> },
        { label: "Pending Evaluations", value: summary.pending_evaluations, icon: <Clock size={20} /> },
        { label: "Average Marks", value: summary.average_marks, icon: <TrendingUp size={20} /> },
        { label: "Today's Evaluations", value: summary.todays_evaluations, icon: <CheckCircle2 size={20} /> },
      ]
    : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold">Dashboard</h1>
        <p className="text-sm text-ink/60 dark:text-dark-ink/60">
          Overview of evaluation activity across your institute.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        {loading
          ? [...Array(6)].map((_, i) => (
              <div key={i} className="neo-card h-24 animate-pulse !bg-surface/60" />
            ))
          : cards.map((c, i) => <StatCard key={c.label} {...c} delay={i * 0.05} />)}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <NeoCard className="lg:col-span-2">
          <h3 className="mb-4 text-sm font-bold">Evaluations by Status</h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={charts?.bar_chart || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#d3cfe9" />
              <XAxis dataKey="status" tick={{ fontSize: 10 }} interval={0} angle={-20} textAnchor="end" height={60} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="count" fill="#9C8CD4" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </NeoCard>

        <NeoCard>
          <h3 className="mb-4 text-sm font-bold">Scripts by File Type</h3>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie
                data={charts?.pie_chart || []}
                dataKey="count"
                nameKey="type"
                innerRadius={55}
                outerRadius={90}
                paddingAngle={4}
              >
                {(charts?.pie_chart || []).map((_: any, i: number) => (
                  <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </NeoCard>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <NeoCard className="lg:col-span-2">
          <h3 className="mb-4 text-sm font-bold">Evaluations Completed (Last 14 Days)</h3>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={charts?.line_chart || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#d3cfe9" />
              <XAxis dataKey="date" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Line type="monotone" dataKey="count" stroke="#7C6AC8" strokeWidth={3} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </NeoCard>

        <NeoCard>
          <h3 className="mb-4 text-sm font-bold">Quick Actions</h3>
          <div className="grid grid-cols-2 gap-3">
            <Link to="/app/examinations" className="neo-card flex flex-col items-center gap-2 !p-4 text-xs font-semibold hover:-translate-y-0.5">
              <CalendarRange size={18} className="text-primary" /> Create Evaluation
            </Link>
            <Link to="/app/question-papers" className="neo-card flex flex-col items-center gap-2 !p-4 text-xs font-semibold hover:-translate-y-0.5">
              <Upload size={18} className="text-primary" /> Upload Question Paper
            </Link>
            <Link to="/app/answer-scripts" className="neo-card flex flex-col items-center gap-2 !p-4 text-xs font-semibold hover:-translate-y-0.5">
              <FileText size={18} className="text-primary" /> Upload Answer Sheets
            </Link>
            <Link to="/app/reports" className="neo-card flex flex-col items-center gap-2 !p-4 text-xs font-semibold hover:-translate-y-0.5">
              <BarChart3 size={18} className="text-primary" /> Generate Reports
            </Link>
          </div>
        </NeoCard>
      </div>

      <NeoCard>
        <h3 className="mb-4 text-sm font-bold">Recent Activity</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="text-xs text-ink/50 dark:text-dark-ink/50">
                <th className="pb-3">Evaluation</th>
                <th className="pb-3">AI Marks</th>
                <th className="pb-3">Confidence</th>
                <th className="pb-3">Status</th>
                <th className="pb-3">Updated</th>
              </tr>
            </thead>
            <tbody>
              {activity.map((a) => (
                <tr key={a.evaluation_id} className="border-t border-ink/5 dark:border-white/5">
                  <td className="py-3 font-medium">#{a.evaluation_id}</td>
                  <td className="py-3">{a.total_ai_marks ?? "—"}</td>
                  <td className="py-3">
                    {a.confidence_score != null ? `${Math.round(a.confidence_score * 100)}%` : "—"}
                  </td>
                  <td className="py-3">
                    <Badge status={a.status} />
                  </td>
                  <td className="py-3 text-ink/50 dark:text-dark-ink/50">
                    {new Date(a.updated_at).toLocaleString()}
                  </td>
                </tr>
              ))}
              {activity.length === 0 && !loading && (
                <tr>
                  <td colSpan={5} className="py-6 text-center text-ink/40">
                    No activity yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </NeoCard>
    </div>
  );
}
