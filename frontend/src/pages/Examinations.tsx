import { useEffect, useState } from "react";
import { Plus, CalendarRange } from "lucide-react";
import { Link } from "react-router-dom";
import api from "../services/api";
import NeoCard from "../components/ui/NeoCard";
import Button from "../components/ui/Button";
import Modal from "../components/ui/Modal";
import PageHeader from "../components/ui/PageHeader";
import type { Examination, Subject, QuestionPaper } from "../types";

export default function Examinations() {
  const [exams, setExams] = useState<Examination[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [papers, setPapers] = useState<QuestionPaper[]>([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState({ name: "", exam_date: "", subject_id: "", question_paper_id: "" });

  function refresh() {
    api.get("/examinations").then((res) => setExams(res.data));
  }

  useEffect(() => {
    refresh();
    api.get("/subjects", { params: { page_size: 100 } }).then((res) => setSubjects(res.data.items));
    api.get("/question-papers").then((res) => setPapers(res.data));
  }, []);

  async function handleSubmit() {
    await api.post("/examinations", {
      name: form.name,
      exam_date: new Date(form.exam_date).toISOString(),
      subject_id: Number(form.subject_id),
      question_paper_id: form.question_paper_id ? Number(form.question_paper_id) : null,
    });
    setModalOpen(false);
    setForm({ name: "", exam_date: "", subject_id: "", question_paper_id: "" });
    refresh();
  }

  return (
    <div>
      <PageHeader
        title="Examinations"
        subtitle="Create examinations and link them to a question paper for evaluation"
        action={<Button icon={<Plus size={16} />} onClick={() => setModalOpen(true)}>Create Examination</Button>}
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {exams.map((exam) => {
          const subject = subjects.find((s) => s.id === exam.subject_id);
          return (
            <NeoCard key={exam.id}>
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                <CalendarRange size={20} />
              </div>
              <h3 className="mt-4 font-bold">{exam.name}</h3>
              <p className="text-xs text-ink/50">{subject ? `${subject.code} — ${subject.name}` : "—"}</p>
              <p className="mt-1 text-xs text-ink/50">{new Date(exam.exam_date).toLocaleDateString()}</p>
              <Link to="/app/answer-scripts" state={{ examinationId: exam.id }}>
                <Button variant="ghost" className="mt-4 w-full">Manage Scripts</Button>
              </Link>
            </NeoCard>
          );
        })}
        {exams.length === 0 && (
          <NeoCard className="col-span-full py-12 text-center text-ink/40">
            <CalendarRange className="mx-auto mb-2" size={26} />
            No examinations created yet.
          </NeoCard>
        )}
      </div>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="Create Examination">
        <div className="space-y-4">
          <input className="neo-input" placeholder="Examination Name (e.g. CIE-1)" value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <input className="neo-input" type="date" value={form.exam_date}
            onChange={(e) => setForm({ ...form, exam_date: e.target.value })} />
          <select className="neo-input" value={form.subject_id}
            onChange={(e) => setForm({ ...form, subject_id: e.target.value })}>
            <option value="">Select Subject</option>
            {subjects.map((s) => <option key={s.id} value={s.id}>{s.code} — {s.name}</option>)}
          </select>
          <select className="neo-input" value={form.question_paper_id}
            onChange={(e) => setForm({ ...form, question_paper_id: e.target.value })}>
            <option value="">Link Question Paper (optional)</option>
            {papers.map((p) => <option key={p.id} value={p.id}>{p.title}</option>)}
          </select>
          <Button className="w-full" onClick={handleSubmit}>Create Examination</Button>
        </div>
      </Modal>
    </div>
  );
}
