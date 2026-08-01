import { useEffect, useState } from "react";
import { FileDown, BarChart3 } from "lucide-react";
import api from "../services/api";
import NeoCard from "../components/ui/NeoCard";
import Button from "../components/ui/Button";
import PageHeader from "../components/ui/PageHeader";
import type { Examination, Student } from "../types";

async function downloadFile(url: string, filename: string) {
  const res = await api.get(url, { responseType: "blob" });
  const blobUrl = window.URL.createObjectURL(new Blob([res.data]));
  const link = document.createElement("a");
  link.href = blobUrl;
  link.setAttribute("download", filename);
  document.body.appendChild(link);
  link.click();
  link.remove();
}

export default function Reports() {
  const [exams, setExams] = useState<Examination[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [examId, setExamId] = useState("");
  const [studentId, setStudentId] = useState("");

  useEffect(() => {
    api.get("/examinations").then((res) => setExams(res.data));
    api.get("/students", { params: { page_size: 100 } }).then((res) => setStudents(res.data.items));
  }, []);

  return (
    <div>
      <PageHeader title="Reports" subtitle="Generate exam-wise and student-wise evaluation reports" />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <NeoCard>
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 text-primary">
            <BarChart3 size={20} />
          </div>
          <h3 className="mt-4 font-bold">Examination Report</h3>
          <p className="mt-1 text-sm text-ink/60">Marks, status, and confidence for every student in an exam.</p>
          <select className="neo-input mt-4" value={examId} onChange={(e) => setExamId(e.target.value)}>
            <option value="">Select Examination</option>
            {exams.map((e) => <option key={e.id} value={e.id}>{e.name}</option>)}
          </select>
          <div className="mt-4 flex gap-3">
            <Button icon={<FileDown size={15} />} disabled={!examId}
              onClick={() => downloadFile(`/reports/exam/${examId}/pdf`, `exam_${examId}_report.pdf`)}>
              Generate PDF
            </Button>
            <Button variant="ghost" icon={<FileDown size={15} />} disabled={!examId}
              onClick={() => downloadFile(`/reports/exam/${examId}/excel`, `exam_${examId}_report.xlsx`)}>
              Export Excel
            </Button>
          </div>
        </NeoCard>

        <NeoCard>
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 text-primary">
            <FileDown size={20} />
          </div>
          <h3 className="mt-4 font-bold">Student Report</h3>
          <p className="mt-1 text-sm text-ink/60">A single student's performance across all examinations.</p>
          <select className="neo-input mt-4" value={studentId} onChange={(e) => setStudentId(e.target.value)}>
            <option value="">Select Student</option>
            {students.map((s) => <option key={s.id} value={s.id}>{s.usn} — {s.name}</option>)}
          </select>
          <div className="mt-4">
            <Button icon={<FileDown size={15} />} disabled={!studentId}
              onClick={() => downloadFile(`/reports/student/${studentId}/pdf`, `student_${studentId}_report.pdf`)}>
              Generate PDF
            </Button>
          </div>
        </NeoCard>
      </div>
    </div>
  );
}
