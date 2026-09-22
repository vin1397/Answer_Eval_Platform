import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { BrainCircuit, AlertTriangle, Eye, CheckCircle2, XCircle, HelpCircle } from "lucide-react";
import api from "../services/api";
import NeoCard from "../components/ui/NeoCard";
import PageHeader from "../components/ui/PageHeader";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import ScriptViewer from "../components/ScriptViewer";
import type { Evaluation, ExtractedAnswer } from "../types";

type QuestionContext = NonNullable<Evaluation["question_context"]>[string];

function QuestionRow({ answer, context }: { answer: ExtractedAnswer; context?: QuestionContext }) {
  const [expanded, setExpanded] = useState(false);
  const mcq = answer.mcq;

  return (
    <div className="neo-inset rounded-2xl p-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <p className="text-sm font-bold">
            Question {answer.question_number}
            <span className="ml-2 rounded-full bg-primary/10 px-2 py-0.5 text-[10px] font-semibold uppercase text-primary">
              {answer.question_type === "mcq" ? "MCQ" : "Short Answer"}
            </span>
          </p>
          {context?.question_text && (
            <p className="mt-1 text-xs text-ink/60">{context.question_text}</p>
          )}
        </div>
        <p className="text-sm font-extrabold text-primary">
          {answer.ai_marks} / {answer.max_marks}
        </p>
      </div>

      {/* MCQ: selection vs correct option */}
      {answer.question_type === "mcq" && mcq && (
        <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
          <span className="inline-flex items-center gap-1.5 rounded-xl bg-white px-3 py-1.5 font-semibold">
            {mcq.is_correct ? (
              <CheckCircle2 size={14} className="text-emerald-600" />
            ) : mcq.option_detected ? (
              <XCircle size={14} className="text-red-500" />
            ) : (
              <HelpCircle size={14} className="text-amber-500" />
            )}
            Student: {mcq.student_option ?? "not detected"}
          </span>
          {context?.correct_option && (
            <span className="rounded-xl bg-white px-3 py-1.5 text-ink/60">
              Correct: <b>{context.correct_option}</b>
            </span>
          )}
        </div>
      )}

      {/* Descriptive: student answer vs faculty reference */}
      {answer.question_type !== "mcq" && (
        <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-2">
          <div className="rounded-xl bg-white p-3">
            <p className="mb-1 text-[10px] font-bold uppercase tracking-wide text-ink/40">Student answer (OCR)</p>
            <p className={`text-xs text-ink/70 ${expanded ? "" : "line-clamp-4"}`}>
              {answer.answer_text || <span className="italic text-ink/40">No answer detected</span>}
            </p>
          </div>
          <div className="rounded-xl bg-white p-3">
            <p className="mb-1 text-[10px] font-bold uppercase tracking-wide text-ink/40">Faculty reference</p>
            <p className={`text-xs text-ink/70 ${expanded ? "" : "line-clamp-4"}`}>
              {context?.reference_answer || <span className="italic text-ink/40">Not configured</span>}
            </p>
          </div>
        </div>
      )}

      <div className="mt-3 flex flex-wrap items-center gap-3 text-[11px] text-ink/50">
        {answer.question_type === "mcq" ? (
          <span>Exact option matching — no semantic model involved</span>
        ) : (
          <>
            <span>Semantic: {Math.round(answer.semantic_score * 100)}%</span>
            <span>Keywords: {Math.round(answer.keyword_score * 100)}%</span>
            {context?.keywords && context.keywords.length > 0 && (
              <span className="truncate">
                Matched: {(answer.matched_keywords || []).join(", ") || "none"}
              </span>
            )}
          </>
        )}
        {(answer.answer_text?.length || 0) > 160 && (
          <button className="font-semibold text-primary" onClick={() => setExpanded(!expanded)}>
            {expanded ? "Show less" : "Show full text"}
          </button>
        )}
        {answer.uncertain && (
          <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 font-semibold text-amber-700">
            <AlertTriangle size={11} /> Uncertain match
          </span>
        )}
        {answer.note && <span className="italic">{answer.note}</span>}
      </div>
    </div>
  );
}

export default function AIEvaluation() {
  const location = useLocation();
  const presetEvaluationId = (location.state as any)?.evaluationId;

  const [evaluations, setEvaluations] = useState<Evaluation[]>([]);
  const [selected, setSelected] = useState<Evaluation | null>(null);
  const [loading, setLoading] = useState(true);
  const [viewingSheet, setViewingSheet] = useState(false);

  useEffect(() => {
    api.get("/evaluations").then((res) => {
      setEvaluations(res.data);
      const preset = presetEvaluationId
        ? res.data.find((e: Evaluation) => e.id === presetEvaluationId)
        : null;
      setSelected(preset || res.data[0] || null);
      setLoading(false);
    });
  }, []);

  return (
    <div>
      <PageHeader title="AI Evaluation" subtitle="What the AI read, how it scored each question, and what the faculty reference says" />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <NeoCard className="!p-0 overflow-hidden lg:col-span-1">
          <div className="max-h-[70vh] overflow-y-auto">
            {evaluations.map((ev) => (
              <button
                key={ev.id}
                onClick={() => setSelected(ev)}
                className={`flex w-full items-center justify-between border-b border-ink/5 px-5 py-4 text-left transition ${
                  selected?.id === ev.id ? "bg-primary/10" : "hover:bg-black/5"
                }`}
              >
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold">
                    {ev.student_usn ? `${ev.student_usn} — ${ev.student_name}` : `Evaluation #${ev.id}`}
                  </p>
                  <p className="truncate text-xs text-ink/50">{ev.examination_name || `Script #${ev.answer_script_id}`}</p>
                  <p className="mt-0.5 text-xs font-semibold text-primary">
                    {ev.final_marks ?? ev.total_ai_marks ?? "—"}/{ev.total_max_marks ?? "—"} marks
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  {ev.has_uncertain_segments && <AlertTriangle size={14} className="text-amber-500" />}
                  <Badge status={ev.status} />
                </div>
              </button>
            ))}
            {!loading && evaluations.length === 0 && (
              <p className="px-5 py-10 text-center text-sm text-ink/40">
                <BrainCircuit className="mx-auto mb-2" size={22} />
                No evaluations in the queue yet. Upload and run one from Answer Scripts.
              </p>
            )}
          </div>
        </NeoCard>

        <div className="lg:col-span-2 space-y-6">
          {selected ? (
            <>
              <NeoCard>
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="text-xs text-ink/50">Student / Examination</p>
                    <p className="text-lg font-bold">
                      {selected.student_usn
                        ? `${selected.student_usn} — ${selected.student_name}`
                        : `Answer Script #${selected.answer_script_id}`}
                    </p>
                    <p className="text-xs text-ink/50">{selected.examination_name}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button variant="ghost" icon={<Eye size={14} />} onClick={() => setViewingSheet(true)}>
                      View sheet
                    </Button>
                    <Badge status={selected.status} />
                  </div>
                </div>

                {selected.has_uncertain_segments && (
                  <div className="mt-4 flex items-start gap-2 rounded-2xl bg-amber-50 px-4 py-3 text-xs text-amber-700">
                    <AlertTriangle size={15} className="mt-0.5 shrink-0" />
                    <span>
                      Some answer segments couldn't be confidently matched to a question number
                      and were not auto-graded — this evaluation needs teacher review before marks are final.
                    </span>
                  </div>
                )}

                <div className="mt-5 grid grid-cols-3 gap-4 text-center">
                  <div className="neo-inset rounded-2xl py-4">
                    <p className="text-xl font-extrabold text-primary">{selected.final_marks ?? selected.total_ai_marks ?? "—"}</p>
                    <p className="text-xs text-ink/50">
                      {selected.total_teacher_marks != null ? "Final (Teacher) Marks" : "AI Marks"} / {selected.total_max_marks ?? "—"}
                    </p>
                  </div>
                  <div className="neo-inset rounded-2xl py-4">
                    <p className="text-xl font-extrabold text-primary">
                      {selected.confidence_score != null ? `${Math.round(selected.confidence_score * 100)}%` : "—"}
                    </p>
                    <p className="text-xs text-ink/50">Confidence Score</p>
                  </div>
                  <div className="neo-inset rounded-2xl py-4">
                    <p className="text-xl font-extrabold text-primary">
                      {selected.has_uncertain_segments || (selected.confidence_score != null && selected.confidence_score < 0.85)
                        ? "Review"
                        : "Auto-approve"}
                    </p>
                    <p className="text-xs text-ink/50">Recommendation</p>
                  </div>
                </div>
              </NeoCard>

              <div className="space-y-4">
                <h3 className="text-sm font-bold">Per-Question Breakdown</h3>
                {(selected.extracted_answers || []).map((a) => (
                  <QuestionRow
                    key={a.question_number}
                    answer={a}
                    context={selected.question_context?.[String(a.question_number)]}
                  />
                ))}
                {(selected.extracted_answers || []).length === 0 && (
                  <NeoCard className="py-8 text-center text-sm text-ink/40">
                    No per-question breakdown available.
                  </NeoCard>
                )}
              </div>

              {selected.ocr_raw_text && (
                <NeoCard>
                  <h3 className="mb-3 text-sm font-bold">Raw Handwriting OCR Output</h3>
                  <pre className="neo-inset max-h-48 overflow-y-auto whitespace-pre-wrap rounded-2xl p-4 text-xs text-ink/70">
                    {selected.ocr_raw_text}
                  </pre>
                </NeoCard>
              )}
            </>
          ) : (
            <NeoCard className="py-16 text-center text-ink/40">Select an evaluation to view details.</NeoCard>
          )}
        </div>
      </div>

      <ScriptViewer
        open={viewingSheet}
        onClose={() => setViewingSheet(false)}
        fileId={selected?.answer_script_id ?? null}
        fileType={selected?.answer_script_file_type ?? "pdf"}
        title={selected?.student_usn ? `Answer Sheet — ${selected.student_usn}` : `Answer Sheet #${selected?.answer_script_id ?? ""}`}
        subtitle={selected?.examination_name ?? undefined}
      />
    </div>
  );
}
