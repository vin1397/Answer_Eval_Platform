import { useEffect, useState } from "react";
import { Plus, CalendarRange, FileText, ArrowRight, CheckCircle2, ScanLine, FileWarning } from "lucide-react";
import { Link } from "react-router-dom";
import api from "../services/api";
import NeoCard from "../components/ui/NeoCard";
import Button from "../components/ui/Button";
import Modal from "../components/ui/Modal";
import PageHeader from "../components/ui/PageHeader";
import type { ExaminationPipelineStatus, Subject, QuestionPaper } from "../types";

/** One workflow step of the exam pipeline. */
const STEPS = [
  { key: "setup", label: "Paper" },
  { key: "answers", label: "Answer Key" },
  { key: "scripts", label: "Scripts" },
  { key: "evaluate", label: "Evaluate" },
  { key: "review", label: "Review" },
] as const;

function pipelineStep(e: ExaminationPipelineStatus): number {
  if (!e.question_paper_title) return 0;
  if (e.next_action_route?.includes("model-answers")) return 1;
  if (e.scripts_uploaded === 0) return 2;
  if (e.awaiting_evaluation > 0) return 3;
  if (e.awaiting_review > 0) return 4;
  return 5; // fully done
}

export default function Examinations() {
  const [exams, setExams] = useState<ExaminationPipelineStatus[]>([]);
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
        subtitle="Track each exam as it moves through the evaluation pipeline — from question paper to final marks"
        action={<Button icon={<Plus size={16} />} onClick={() => setModalOpen(true)}>Create Examination</Button>}
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {exams.map((exam) => {
          const subject = subjects.find((s) => s.id === exam.subject_id);
          const step = pipelineStep(exam);
          const done = step >= 5;

          return (
            <NeoCard key={exam.id}>
              <div className="flex items-start justify-between">
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                  <CalendarRange size={20} />
                </div>
                {done && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-green-500/10 px-3 py-1 text-xs font-semibold text-green-600">
                    <CheckCircle2 size={13} /> Complete
                  </span>
                )}
              </div>

              <h3 className="mt-4 font-bold">{exam.name}</h3>
              <p className="text-xs text-ink/50">
                {subject ? `${subject.code} — ${subject.name}` : "—"} · {new Date(exam.exam_date).toLocaleDateString()}
              </p>

              {/* Pipeline progress steps */}
              <div className="mt-5 flex items-center gap-1">
                {STEPS.map((s, i) => {
                  const state = i < step ? "done" : i === step ? (done ? "done" : "active") : "todo";
                  return (
                    <div key={s.key} className="flex flex-1 flex-col items-center gap-1.5">
                      <div
                        className={`h-1.5 w-full rounded-full ${
                          state === "done" ? "bg-primary" : state === "active" ? "bg-accent" : "bg-ink/10"
                        }`}
                        title={s.label}
                      />
                      <span className={`text-[10px] font-semibold ${state === "todo" ? "text-ink/30" : "text-ink/60"}`}>{s.label}</span>
                    </div>
                  );
                })}
              </div>

              {/* Live counters */}
              <div className="mt-4 grid grid-cols-3 gap-2 text-center">
                <div className="neo-inset rounded-xl py-2">
                  <p className="text-base font-bold">{exam.scripts_uploaded}</p>
                  <p className="text-[10px] text-ink/50">Scripts</p>
                </div>
                <div className="neo-inset rounded-xl py-2">
                  <p className="text-base font-bold">{exam.evaluations_completed}</p>
                  <p className="text-[10px] text-ink/50">Evaluated</p>
                </div>
                <div className="neo-inset rounded-xl py-2">
                  <p className="text-base font-bold text-green-600">{exam.evaluations_approved}</p>
                  <p className="text-[10px] text-ink/50">Approved</p>
                </div>
              </div>

              {/* Next-step CTA */}
              {exam.next_action && (
                <Link to={exam.next_action_route ?? "/app/dashboard"} state={exam.next_action_route?.includes("answer-scripts") ? { examinationId: exam.id } : undefined}>
                  <Button variant={done ? "ghost" : "primary"} className="mt-4 w-full justify-between" icon={<ArrowRight size={15} />}>
                    {exam.next_action}
                  </Button>
                </Link>
              )}

              {exam.question_paper_title && (
                <p className="mt-3 flex items-center gap-1.5 text-[11px] text-ink/40">
                  <FileText size={12} /> {exam.question_paper_title}
                </p>
              )}

              <div className="mt-2 flex gap-2 text-[11px]">
                <Link to="/app/answer-scripts" state={{ examinationId: exam.id }} className="inline-flex items-center gap-1 text-ink/50 transition hover:text-primary">
                  <ScanLine size={12} /> Manage scripts
                </Link>
                {!exam.question_paper_title && (
                  <Link to="/app/question-papers" className="inline-flex items-center gap-1 text-ink/50 transition hover:text-primary">
                    <FileWarning size={12} /> Link paper
                  </Link>
                )}
              </div>
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
