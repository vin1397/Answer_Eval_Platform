import { useEffect, useState } from "react";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
import { PieChart as PieIcon } from "lucide-react";
import api from "../services/api";
import NeoCard from "../components/ui/NeoCard";
import PageHeader from "../components/ui/PageHeader";
import StatCard from "../components/ui/StatCard";
import type { Examination } from "../types";
import { Percent, TrendingUp, TrendingDown, Users } from "lucide-react";

export default function Analytics() {
  const [exams, setExams] = useState<Examination[]>([]);
  const [examId, setExamId] = useState("");
  const [questionWise, setQuestionWise] = useState<any[]>([]);
  const [classPerf, setClassPerf] = useState<any | null>(null);

  useEffect(() => {
    api.get("/examinations").then((res) => setExams(res.data));
  }, []);

  useEffect(() => {
    if (!examId) return;
    api.get(`/analytics/question-wise/${examId}`).then((res) => setQuestionWise(res.data));
    api.get(`/analytics/class-performance/${examId}`).then((res) => setClassPerf(res.data));
  }, [examId]);

  return (
    <div>
      <PageHeader title="Analytics" subtitle="Question-wise performance, class averages, and pass rates" />

      <div className="mb-6 max-w-sm">
        <select className="neo-input" value={examId} onChange={(e) => setExamId(e.target.value)}>
          <option value="">Select Examination</option>
          {exams.map((e) => <option key={e.id} value={e.id}>{e.name}</option>)}
        </select>
      </div>

      {examId && classPerf ? (
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <StatCard label="Class Average" value={classPerf.class_average} icon={<Percent size={18} />} />
            <StatCard label="Highest" value={classPerf.highest} icon={<TrendingUp size={18} />} />
            <StatCard label="Lowest" value={classPerf.lowest} icon={<TrendingDown size={18} />} />
            <StatCard label="Pass %" value={`${classPerf.pass_percentage}%`} icon={<Users size={18} />} />
          </div>

          <NeoCard>
            <h3 className="mb-4 text-sm font-bold">Question-wise Average Marks</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={questionWise}>
                <CartesianGrid strokeDasharray="3 3" stroke="#d3cfe9" />
                <XAxis dataKey="question_number" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="average_marks" fill="#7C6AC8" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </NeoCard>
        </div>
      ) : (
        <NeoCard className="py-16 text-center text-ink/40">
          <PieIcon className="mx-auto mb-2" size={26} />
          Select an examination to view analytics.
        </NeoCard>
      )}
    </div>
  );
}
