import { useEffect, useState } from "react";
import { ShieldCheck, Check, X, RotateCcw } from "lucide-react";
import api from "../services/api";
import NeoCard from "../components/ui/NeoCard";
import Button from "../components/ui/Button";
import PageHeader from "../components/ui/PageHeader";
import Badge from "../components/ui/Badge";
import type { Evaluation } from "../types";

export default function TeacherReview() {
  const [evaluations, setEvaluations] = useState<Evaluation[]>([]);
  const [selected, setSelected] = useState<Evaluation | null>(null);
  const [adjustedMarks, setAdjustedMarks] = useState("");
  const [reason, setReason] = useState("");
  const [comments, setComments] = useState("");
  const [submitting, setSubmitting] = useState(false);

  function refresh() {
    api.get("/evaluations", { params: { status_filter: "under_review" } }).then((res) => {
      setEvaluations(res.data);
      setSelected((prev) => prev ?? res.data[0] ?? null);
    });
  }

  useEffect(refresh, []);

  useEffect(() => {
    if (selected) {
      setAdjustedMarks(String(selected.total_ai_marks ?? ""));
      setReason("");
      setComments("");
    }
  }, [selected]);

  async function submitReview(decision: "approve" | "reject" | "re_evaluate") {
    if (!selected) return;
    setSubmitting(true);
    try {
      await api.post(`/evaluations/${selected.id}/review`, {
        decision,
        adjusted_marks: adjustedMarks ? Number(adjustedMarks) : null,
        reason,
        comments,
      });
      setSelected(null);
      refresh();
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <PageHeader title="Teacher Review" subtitle="Verify low-confidence AI evaluations before marks are finalized" />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <NeoCard className="!p-0 overflow-hidden lg:col-span-1">
          <div className="max-h-[70vh] overflow-y-auto">
            {evaluations.map((ev) => (
              <button
                key={ev.id}
                onClick={() => setSelected(ev)}
                className={`flex w-full items-center justify-between border-b border-ink/5 dark:border-white/5 px-5 py-4 text-left transition ${
                  selected?.id === ev.id ? "bg-primary/10" : "hover:bg-black/5 dark:hover:bg-white/5"
                }`}
              >
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold">
                    {ev.student_usn ? `${ev.student_usn} — ${ev.student_name}` : `Evaluation #${ev.id}`}
                  </p>
                  <p className="truncate text-xs text-ink/50">
                    {ev.examination_name} · AI {ev.total_ai_marks ?? "—"}/{ev.total_max_marks ?? "—"}
                  </p>
                </div>
                <Badge status={ev.status} />
              </button>
            ))}
            {evaluations.length === 0 && (
              <p className="px-5 py-10 text-center text-sm text-ink/40">
                <ShieldCheck className="mx-auto mb-2" size={22} />
                Nothing pending review right now.
              </p>
            )}
          </div>
        </NeoCard>

        <div className="lg:col-span-2">
          {selected ? (
            <NeoCard>
              <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
                <div>
                  <h3 className="text-sm font-bold">
                    {selected.student_usn ? `${selected.student_usn} — ${selected.student_name}` : `Evaluation #${selected.id}`}
                  </h3>
                  <p className="text-xs text-ink/50">{selected.examination_name}</p>
                </div>
                <p className="text-sm font-bold text-primary">
                  AI total: {selected.total_ai_marks ?? "—"} / {selected.total_max_marks ?? "—"}
                </p>
              </div>
              <div className="space-y-3">
                {(selected.extracted_answers || []).map((a) => {
                  const ctx = selected.question_context?.[String(a.question_number)];
                  return (
                    <div key={a.question_number} className="neo-inset rounded-2xl p-4">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-bold">
                          Question {a.question_number}
                          <span className="ml-2 rounded-full bg-primary/10 px-2 py-0.5 text-[10px] font-semibold uppercase text-primary">
                            {a.question_type === "mcq" ? "MCQ" : "Short Answer"}
                          </span>
                        </p>
                        <p className="text-xs text-ink/50">AI: {a.ai_marks} / {a.max_marks}</p>
                      </div>
                      {ctx?.question_text && <p className="mt-1 text-xs text-ink/60">{ctx.question_text}</p>}
                      <div className="mt-2 grid grid-cols-1 gap-2 md:grid-cols-2">
                        <div className="rounded-xl bg-white p-3">
                          <p className="mb-1 text-[10px] font-bold uppercase tracking-wide text-ink/40">Student answer (OCR)</p>
                          <p className="text-xs text-ink/70 line-clamp-3">
                            {a.answer_text || <span className="italic text-ink/40">No answer detected</span>}
                          </p>
                        </div>
                        <div className="rounded-xl bg-white p-3">
                          <p className="mb-1 text-[10px] font-bold uppercase tracking-wide text-ink/40">Faculty reference</p>
                          <p className="text-xs text-ink/70 line-clamp-3">
                            {a.question_type === "mcq"
                              ? ctx?.correct_option
                                ? `Correct option: ${ctx.correct_option}`
                                : "Not configured"
                              : ctx?.reference_answer || <span className="italic text-ink/40">Not configured</span>}
                          </p>
                        </div>
                      </div>
                      <div className="mt-2 flex gap-3 text-[11px] text-ink/50">
                        {a.question_type === "mcq" ? (
                          <span>
                            Student: {a.mcq?.student_option ?? "not detected"}
                            {a.mcq?.is_correct ? " ✓ correct" : a.mcq?.option_detected ? " ✗ wrong" : ""}
                          </span>
                        ) : (
                          <>
                            <span>Semantic: {Math.round(a.semantic_score * 100)}%</span>
                            <span>Keyword: {Math.round(a.keyword_score * 100)}%</span>
                          </>
                        )}
                        {a.uncertain && <span className="font-semibold text-amber-600">⚠ uncertain match</span>}
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-1.5 block text-xs font-semibold text-ink/70">Teacher Marks</label>
                  <input className="neo-input" type="number" value={adjustedMarks}
                    onChange={(e) => setAdjustedMarks(e.target.value)} />
                </div>
                <div>
                  <label className="mb-1.5 block text-xs font-semibold text-ink/70">Reason</label>
                  <input className="neo-input" value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Optional" />
                </div>
              </div>
              <div className="mt-4">
                <label className="mb-1.5 block text-xs font-semibold text-ink/70">Comments</label>
                <textarea className="neo-input min-h-20" value={comments} onChange={(e) => setComments(e.target.value)} />
              </div>

              <div className="mt-6 flex flex-wrap gap-3">
                <Button icon={<Check size={15} />} onClick={() => submitReview("approve")} disabled={submitting}>Approve</Button>
                <Button variant="ghost" icon={<RotateCcw size={15} />} onClick={() => submitReview("re_evaluate")} disabled={submitting}>Re-evaluate</Button>
                <Button variant="danger" icon={<X size={15} />} onClick={() => submitReview("reject")} disabled={submitting}>Reject</Button>
              </div>
            </NeoCard>
          ) : (
            <NeoCard className="py-16 text-center text-ink/40">Select an evaluation to review.</NeoCard>
          )}
        </div>
      </div>
    </div>
  );
}
