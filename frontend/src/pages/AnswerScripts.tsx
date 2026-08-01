import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { Upload, ScanLine, PlayCircle } from "lucide-react";
import api from "../services/api";
import NeoCard from "../components/ui/NeoCard";
import Button from "../components/ui/Button";
import Modal from "../components/ui/Modal";
import PageHeader from "../components/ui/PageHeader";
import type { AnswerScript, Examination, Student } from "../types";

export default function AnswerScripts() {
  const location = useLocation();
  const presetExamId = (location.state as any)?.examinationId;

  const [scripts, setScripts] = useState<AnswerScript[]>([]);
  const [exams, setExams] = useState<Examination[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [examinationId, setExaminationId] = useState<string>(presetExamId ? String(presetExamId) : "");
  const [modalOpen, setModalOpen] = useState(false);
  const [studentId, setStudentId] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [runningId, setRunningId] = useState<number | null>(null);

  useEffect(() => {
    api.get("/examinations").then((res) => setExams(res.data));
    api.get("/students", { params: { page_size: 100 } }).then((res) => setStudents(res.data.items));
  }, []);

  useEffect(() => {
    if (!examinationId) {
      setScripts([]);
      return;
    }
    api.get("/answer-scripts", { params: { examination_id: examinationId } }).then((res) => setScripts(res.data));
  }, [examinationId]);

  async function handleUpload() {
    if (!file || !studentId || !examinationId) return;
    setUploading(true);
    const formData = new FormData();
    formData.append("examination_id", examinationId);
    formData.append("student_id", studentId);
    formData.append("file", file);
    try {
      await api.post("/answer-scripts/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setModalOpen(false);
      setFile(null);
      setStudentId("");
      const res = await api.get("/answer-scripts", { params: { examination_id: examinationId } });
      setScripts(res.data);
    } finally {
      setUploading(false);
    }
  }

  async function runEvaluation(scriptId: number) {
    setRunningId(scriptId);
    try {
      await api.post(`/evaluations/run/${scriptId}`);
    } finally {
      setRunningId(null);
    }
  }

  return (
    <div>
      <PageHeader
        title="Answer Scripts"
        subtitle="Upload scanned scripts and map them to students, then run AI evaluation"
        action={<Button icon={<Upload size={16} />} onClick={() => setModalOpen(true)} disabled={!examinationId}>Upload Script</Button>}
      />

      <div className="mb-6 max-w-sm">
        <select className="neo-input" value={examinationId} onChange={(e) => setExaminationId(e.target.value)}>
          <option value="">Select Examination</option>
          {exams.map((e) => <option key={e.id} value={e.id}>{e.name}</option>)}
        </select>
      </div>

      <NeoCard className="!p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-ink/5 dark:border-white/5 text-xs text-ink/50">
                <th className="px-6 py-4">Student</th>
                <th className="px-6 py-4">File Type</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4">Uploaded</th>
                <th className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {scripts.map((s) => {
                const student = students.find((st) => st.id === s.student_id);
                return (
                  <tr key={s.id} className="border-b border-ink/5 dark:border-white/5 last:border-0">
                    <td className="px-6 py-4 font-medium">{student ? `${student.usn} — ${student.name}` : `#${s.student_id}`}</td>
                    <td className="px-6 py-4 uppercase">{s.file_type}</td>
                    <td className="px-6 py-4 capitalize">{s.upload_status}</td>
                    <td className="px-6 py-4 text-ink/50">{new Date(s.created_at).toLocaleString()}</td>
                    <td className="px-6 py-4 text-right">
                      <Button variant="ghost" icon={<PlayCircle size={14} />} onClick={() => runEvaluation(s.id)} disabled={runningId === s.id}>
                        {runningId === s.id ? "Evaluating..." : "Run AI Evaluation"}
                      </Button>
                    </td>
                  </tr>
                );
              })}
              {examinationId && scripts.length === 0 && (
                <tr><td colSpan={5} className="px-6 py-10 text-center text-ink/40">
                  <ScanLine className="mx-auto mb-2" size={22} />No scripts uploaded for this examination yet.
                </td></tr>
              )}
              {!examinationId && (
                <tr><td colSpan={5} className="px-6 py-10 text-center text-ink/40">Select an examination to view scripts.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </NeoCard>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="Upload Answer Script">
        <div className="space-y-4">
          <select className="neo-input" value={studentId} onChange={(e) => setStudentId(e.target.value)}>
            <option value="">Select Student</option>
            {students.map((s) => <option key={s.id} value={s.id}>{s.usn} — {s.name}</option>)}
          </select>
          <label
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragOver(false);
              const dropped = e.dataTransfer.files?.[0];
              if (dropped) setFile(dropped);
            }}
            className={`neo-inset flex cursor-pointer flex-col items-center justify-center gap-2 rounded-2xl px-4 py-10 text-sm transition ${dragOver ? "ring-2 ring-accent" : ""}`}
          >
            <Upload size={22} className="text-primary" />
            {file ? file.name : "Drag & drop or click to select PDF/JPG/PNG"}
            <input type="file" accept=".pdf,.jpg,.jpeg,.png" className="hidden"
              onChange={(e) => setFile(e.target.files?.[0] || null)} />
          </label>
          <Button className="w-full" onClick={handleUpload} disabled={uploading || !file || !studentId}>
            {uploading ? "Uploading..." : "Upload Script"}
          </Button>
        </div>
      </Modal>
    </div>
  );
}
