import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { GraduationCap, TrendingUp, FileCheck2, ClipboardList } from "lucide-react";
import Modal from "./ui/Modal";
import NeoCard from "./ui/NeoCard";
import Button from "./ui/Button";
import Badge from "./ui/Badge";
import api from "../services/api";
import type { Student } from "../types";

interface StudentResult {
  examination_id: number | null;
  examination_name: string;
  exam_date: string | null;
  answer_script_id: number;
  evaluation_id: number | null;
  evaluation_status: string;
  ai_marks: number | null;
  max_marks: number | null;
  final_marks: number | null;
  confidence: number | null;
  evaluated_at: string | null;
}

/**
 * Opens when a student row is clicked anywhere in the app: shows the
 * student's per-examination results — AI marks, final (teacher-approved)
 * marks, confidence, and evaluation status — plus roll-up totals.
 */
export default function StudentResultsModal({
  open,
  onClose,
  student,
}: {
  open: boolean;
  onClose: () => void;
  student: Student | null;
}) {
  const [results, setResults] = useState<StudentResult[]>([]);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (!open || !student) return;
    setLoading(true);
    api
      .get(`/students/${student.id}/results`)
      .then((res) => setResults(res.data))
      .finally(() => setLoading(false));
  }, [open, student]);

  const evaluated = results.filter((r) => r.evaluation_id != null);
  const totals = evaluated.reduce(
    (acc, r) => {
      acc.final += r.final_marks ?? 0;
      acc.max += r.max_marks ?? 0;
      return acc;
    },
    { final: 0, max: 0 }
  );
  const overallPct = totals.max > 0 ? Math.round((totals.final / totals.max) * 100) : null;

  return (
    <Modal open={open} onClose={onClose} title={student ? `${student.name} — ${student.usn}` : "Student Results"}>
      {loading ? (
        <p className="py-10 text-center text-sm text-ink/40">Loading results…</p>
      ) : (
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-3 text-center">
            <div className="neo-inset rounded-2xl py-3">
              <p className="text-lg font-extrabold text-primary">{results.length}</p>
              <p className="text-[11px] text-ink/50">Scripts Uploaded</p>
            </div>
            <div className="neo-inset rounded-2xl py-3">
              <p className="text-lg font-extrabold text-primary">{evaluated.length}</p>
              <p className="text-[11px] text-ink/50">Evaluated</p>
            </div>
            <div className="neo-inset rounded-2xl py-3">
              <p className="text-lg font-extrabold text-primary">
                {overallPct != null ? `${overallPct}%` : "—"}
              </p>
              <p className="text-[11px] text-ink/50">Overall ({totals.final}/{totals.max})</p>
            </div>
          </div>

          {results.length === 0 && (
            <div className="py-10 text-center text-sm text-ink/40">
              <GraduationCap className="mx-auto mb-2" size={24} />
              No answer scripts uploaded for this student yet.
            </div>
          )}

          <div className="space-y-3">
            {results.map((r) => (
              <NeoCard key={r.answer_script_id} className="!p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <p className="text-sm font-bold">{r.examination_name}</p>
                    <p className="text-[11px] text-ink/50">
                      {r.exam_date ? new Date(r.exam_date).toLocaleDateString() : ""}
                      {r.evaluated_at ? ` · evaluated ${new Date(r.evaluated_at).toLocaleDateString()}` : ""}
                    </p>
                  </div>
                  <Badge status={r.evaluation_status} />
                </div>

                {r.evaluation_id != null ? (
                  <>
                    <div className="mt-3 grid grid-cols-3 gap-2 text-center text-xs">
                      <div className="neo-inset rounded-xl py-2">
                        <p className="text-sm font-bold">{r.ai_marks ?? "—"}/{r.max_marks ?? "—"}</p>
                        <p className="text-[10px] text-ink/50">AI Marks</p>
                      </div>
                      <div className="neo-inset rounded-xl py-2">
                        <p className="text-sm font-bold">{r.final_marks ?? "—"}/{r.max_marks ?? "—"}</p>
                        <p className="text-[10px] text-ink/50">Final Marks</p>
                      </div>
                      <div className="neo-inset rounded-xl py-2">
                        <p className="text-sm font-bold">
                          {r.confidence != null ? `${Math.round(r.confidence * 100)}%` : "—"}
                        </p>
                        <p className="text-[10px] text-ink/50">Confidence</p>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      className="mt-3 w-full"
                      icon={<ClipboardList size={14} />}
                      onClick={() => {
                        onClose();
                        navigate("/app/ai-evaluation", { state: { evaluationId: r.evaluation_id } });
                      }}
                    >
                      View full evaluation breakdown
                    </Button>
                  </>
                ) : (
                  <div className="mt-3 flex items-center gap-2 rounded-xl bg-amber-50 px-3 py-2 text-[11px] text-amber-700">
                    <FileCheck2 size={13} />
                    Script uploaded but not evaluated yet — run it from Answer Scripts.
                  </div>
                )}
              </NeoCard>
            ))}
          </div>

          {evaluated.length > 0 && (
            <p className="flex items-center gap-1.5 text-[11px] text-ink/40">
              <TrendingUp size={12} />
              Final marks always reflect teacher-approved overrides.
            </p>
          )}
        </div>
      )}
    </Modal>
  );
}
