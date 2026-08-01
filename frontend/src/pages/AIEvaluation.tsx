import { useEffect, useState } from "react";
import { BrainCircuit } from "lucide-react";
import api from "../services/api";
import NeoCard from "../components/ui/NeoCard";
import PageHeader from "../components/ui/PageHeader";
import Badge from "../components/ui/Badge";
import type { Evaluation } from "../types";

export default function AIEvaluation() {
  const [evaluations, setEvaluations] = useState<Evaluation[]>([]);
  const [selected, setSelected] = useState<Evaluation | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/evaluations").then((res) => {
      setEvaluations(res.data);
      setSelected(res.data[0] || null);
      setLoading(false);
    });
  }, []);

  return (
    <div>
      <PageHeader title="AI Evaluation" subtitle="Live evaluation queue: OCR output, semantic scores, and final AI marks" />

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
                  <p className="text-xs text-ink/50">Script #{ev.answer_script_id}</p>
                </div>
                <Badge status={ev.status} />
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
                    <p className="text-xs text-ink/50">Current Student / Script</p>
                    <p className="text-lg font-bold">Answer Script #{selected.answer_script_id}</p>
                  </div>
                  <Badge status={selected.status} />
                </div>
                <div className="mt-5 grid grid-cols-3 gap-4 text-center">
                  <div className="neo-inset rounded-2xl py-4">
                    <p className="text-xl font-extrabold text-primary">{selected.total_ai_marks ?? "—"}</p>
                    <p className="text-xs text-ink/50">AI Marks / {selected.total_max_marks ?? "—"}</p>
                  </div>
                  <div className="neo-inset rounded-2xl py-4">
                    <p className="text-xl font-extrabold text-primary">
                      {selected.confidence_score != null ? `${Math.round(selected.confidence_score * 100)}%` : "—"}
                    </p>
                    <p className="text-xs text-ink/50">Confidence Score</p>
                  </div>
                  <div className="neo-inset rounded-2xl py-4">
                    <p className="text-xl font-extrabold text-primary">
                      {selected.confidence_score != null && selected.confidence_score < 0.85 ? "Review" : "Auto-approve"}
                    </p>
                    <p className="text-xs text-ink/50">Recommendation</p>
                  </div>
                </div>
              </NeoCard>

              {selected.ocr_raw_text && (
                <NeoCard>
                  <h3 className="mb-3 text-sm font-bold">OCR Output</h3>
                  <pre className="neo-inset max-h-48 overflow-y-auto whitespace-pre-wrap rounded-2xl p-4 text-xs text-ink/70">
                    {selected.ocr_raw_text}
                  </pre>
                </NeoCard>
              )}

              <NeoCard>
                <h3 className="mb-3 text-sm font-bold">Matched Questions & Scores</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr className="text-xs text-ink/50">
                        <th className="py-2">Q.No</th>
                        <th className="py-2">Semantic</th>
                        <th className="py-2">Keyword</th>
                        <th className="py-2">AI Marks</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(selected.extracted_answers || []).map((a) => (
                        <tr key={a.question_number} className="border-t border-ink/5 dark:border-white/5">
                          <td className="py-2 font-semibold">{a.question_number}</td>
                          <td className="py-2">{Math.round(a.semantic_score * 100)}%</td>
                          <td className="py-2">{Math.round(a.keyword_score * 100)}%</td>
                          <td className="py-2">{a.ai_marks} / {a.max_marks}</td>
                        </tr>
                      ))}
                      {(selected.extracted_answers || []).length === 0 && (
                        <tr><td colSpan={4} className="py-4 text-center text-ink/40">No per-question breakdown available.</td></tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </NeoCard>
            </>
          ) : (
            <NeoCard className="py-16 text-center text-ink/40">Select an evaluation to view details.</NeoCard>
          )}
        </div>
      </div>
    </div>
  );
}
