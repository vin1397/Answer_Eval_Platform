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
                <div>
                  <p className="text-sm font-semibold">Evaluation #{ev.id}</p>
                  <p className="text-xs text-ink/50">
                    Confidence: {ev.confidence_score != null ? `${Math.round(ev.confidence_score * 100)}%` : "—"}
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
              <h3 className="mb-4 text-sm font-bold">Answer Comparison — Evaluation #{selected.id}</h3>
              <div className="space-y-3">
                {(selected.extracted_answers || []).map((a) => (
                  <div key={a.question_number} className="neo-inset rounded-2xl p-4">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-bold">Question {a.question_number}</p>
                      <p className="text-xs text-ink/50">AI: {a.ai_marks} / {a.max_marks}</p>
                    </div>
                    <p className="mt-2 text-xs text-ink/60 line-clamp-3">{a.answer_text}</p>
                    <div className="mt-2 flex gap-3 text-[11px] text-ink/50">
                      <span>Semantic: {Math.round(a.semantic_score * 100)}%</span>
                      <span>Keyword: {Math.round(a.keyword_score * 100)}%</span>
                    </div>
                  </div>
                ))}
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
