import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { ClipboardCheck, Save, CheckCircle2 } from "lucide-react";
import api from "../services/api";
import NeoCard from "../components/ui/NeoCard";
import Button from "../components/ui/Button";
import PageHeader from "../components/ui/PageHeader";
import type { QuestionPaper, ModelAnswerState } from "../types";

interface FormState {
  answer_text: string;
  keywords: string;
  expected_concepts: string;
  correct_option: string;
}

const emptyFormState: FormState = { answer_text: "", keywords: "", expected_concepts: "", correct_option: "" };

function toFormState(saved: ModelAnswerState | undefined): FormState {
  if (!saved) return emptyFormState;
  return {
    answer_text: saved.answer_text ?? "",
    keywords: (saved.keywords ?? []).join(", "),
    expected_concepts: (saved.expected_concepts ?? []).join(", "),
    correct_option: saved.correct_option ?? "",
  };
}

export default function ModelAnswers() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [papers, setPapers] = useState<QuestionPaper[]>([]);
  const [selectedPaper, setSelectedPaper] = useState<number | "">("");
  const [forms, setForms] = useState<Record<number, FormState>>({});
  const [savedQuestions, setSavedQuestions] = useState<Set<number>>(new Set());
  const [savingId, setSavingId] = useState<number | null>(null);
  const [justSavedId, setJustSavedId] = useState<number | null>(null);

  useEffect(() => {
    api.get("/question-papers").then((res) => {
      setPapers(res.data);
      // Deep link: /app/model-answers?paper=3 (e.g. from an exam card's CTA)
      const requested = Number(searchParams.get("paper"));
      if (requested && res.data.some((p: QuestionPaper) => p.id === requested)) {
        setSelectedPaper(requested);
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Load previously saved model answers whenever the selected paper changes.
  useEffect(() => {
    if (selectedPaper === "") return;
    const paper = papers.find((p) => p.id === selectedPaper);
    if (!paper || paper.questions.length === 0) return;

    api
      .get("/model-answers", { params: { question_ids: paper.questions.map((q) => q.id).join(",") } })
      .then((res) => {
        const saved: ModelAnswerState[] = res.data;
        setSavedQuestions(new Set(saved.map((s) => s.question_id)));
        setForms((prev) => {
          const next = { ...prev };
          for (const q of paper.questions) {
            const existing = next[q.id] ?? emptyFormState;
            const prefill = toFormState(saved.find((s) => s.question_id === q.id));
            // Prefill from saved values; keep any local edits the user already made.
            next[q.id] = {
              answer_text: existing.answer_text || prefill.answer_text,
              keywords: existing.keywords || prefill.keywords,
              expected_concepts: existing.expected_concepts || prefill.expected_concepts,
              correct_option: existing.correct_option || prefill.correct_option,
            };
          }
          return next;
        });
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedPaper, papers]);

  const activePaper = papers.find((p) => p.id === selectedPaper);

  function updateForm(questionId: number, field: keyof FormState, value: string) {
    setForms((prev) => ({
      ...prev,
      [questionId]: { ...emptyFormState, ...prev[questionId], [field]: value },
    }));
  }

  async function saveModelAnswer(question: { id: number; question_type: string }, isMcq: boolean) {
    const form = forms[question.id] || emptyFormState;
    if (isMcq && !form.correct_option) return;
    if (!isMcq && !form.answer_text) return;

    setSavingId(question.id);
    try {
      const payload = {
        question_id: question.id,
        answer_text: isMcq ? null : form.answer_text,
        correct_option: isMcq ? form.correct_option : null,
        keywords: form.keywords ? form.keywords.split(",").map((k) => k.trim()).filter(Boolean) : [],
        expected_concepts: form.expected_concepts
          ? form.expected_concepts.split(",").map((k) => k.trim()).filter(Boolean)
          : [],
        rubric: [],
      };
      // POST creates the answer key the first time; PUT updates it afterwards.
      if (savedQuestions.has(question.id)) {
        const existing = await api.get("/model-answers", {
          params: { question_ids: String(question.id) },
        });
        const row = existing.data.find((r: ModelAnswerState) => r.question_id === question.id);
        if (row) {
          await api.put(`/model-answers/${row.id}`, payload);
        } else {
          await api.post("/model-answers", payload);
        }
      } else {
        await api.post("/model-answers", payload);
      }
      setSavedQuestions((prev) => new Set(prev).add(question.id));
      setJustSavedId(question.id);
      setTimeout(() => setJustSavedId((id) => (id === question.id ? null : id)), 2000);
    } finally {
      setSavingId(null);
    }
  }

  return (
    <div>
      <PageHeader
        title="Model Answers"
        subtitle="Author the faculty answer key the AI grades against — MCQ correct options or reference answers per question"
      />

      <div className="mb-6 max-w-sm">
        <select
          className="neo-input"
          value={selectedPaper}
          onChange={(e) => {
            setSelectedPaper(Number(e.target.value) || "");
            setSearchParams(e.target.value ? { paper: e.target.value } : {});
          }}
        >
          <option value="">Select a question paper</option>
          {papers.map((p) => (
            <option key={p.id} value={p.id}>{p.title}</option>
          ))}
        </select>
      </div>

      {activePaper ? (
        <div className="space-y-5">
          {activePaper.questions.map((q) => {
            const isMcq = q.question_type === "mcq";
            const isSaved = savedQuestions.has(q.id);
            return (
              <NeoCard key={q.id}>
                <div className="mb-3 flex items-center justify-between gap-3">
                  <p className="font-bold">Q{q.question_number}. {q.question_text}</p>
                  <div className="flex shrink-0 gap-2">
                    {isSaved && (
                      <span className="inline-flex items-center gap-1 rounded-full bg-green-500/10 px-3 py-1 text-xs font-semibold text-green-600">
                        <CheckCircle2 size={12} /> Answer key saved
                      </span>
                    )}
                    <span className="rounded-full bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">{q.max_marks} marks</span>
                    <span className={`rounded-full px-3 py-1 text-xs font-semibold ${isMcq ? "bg-accent/10 text-accent" : "bg-ink/10 text-ink/60"}`}>
                      {isMcq ? "MCQ" : "Short Answer"}
                    </span>
                  </div>
                </div>

                {isMcq ? (
                  <div>
                    <p className="mb-2 text-xs font-semibold text-ink/60">Select the correct option</p>
                    <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                      {(q.options || []).map((opt, idx) => {
                        const letter = String.fromCharCode(65 + idx); // A, B, C, D...
                        const selected = forms[q.id]?.correct_option === letter;
                        return (
                          <button
                            key={letter}
                            onClick={() => updateForm(q.id, "correct_option", letter)}
                            className={`neo-inset rounded-2xl px-3 py-2 text-left text-xs transition ${
                              selected ? "ring-2 ring-primary bg-primary/10" : ""
                            }`}
                          >
                            <span className="font-bold">{letter}.</span> {opt}
                          </button>
                        );
                      })}
                    </div>
                    {(!q.options || q.options.length === 0) && (
                      <p className="text-xs text-ink/40">No options were extracted for this question — re-upload the question paper, or edit it to add options.</p>
                    )}
                  </div>
                ) : (
                  <>
                    <textarea
                      className="neo-input min-h-24 resize-y"
                      placeholder="Model answer text..."
                      value={forms[q.id]?.answer_text || ""}
                      onChange={(e) => updateForm(q.id, "answer_text", e.target.value)}
                    />
                    <div className="mt-3 grid grid-cols-2 gap-3">
                      <input className="neo-input" placeholder="Keywords (comma separated)"
                        value={forms[q.id]?.keywords || ""} onChange={(e) => updateForm(q.id, "keywords", e.target.value)} />
                      <input className="neo-input" placeholder="Expected concepts (comma separated)"
                        value={forms[q.id]?.expected_concepts || ""} onChange={(e) => updateForm(q.id, "expected_concepts", e.target.value)} />
                    </div>
                  </>
                )}

                <Button
                  className="mt-4"
                  icon={justSavedId === q.id ? <CheckCircle2 size={15} /> : <Save size={15} />}
                  onClick={() => saveModelAnswer(q, isMcq)}
                  disabled={savingId === q.id}
                >
                  {savingId === q.id ? "Saving..." : justSavedId === q.id ? "Saved" : isSaved ? "Update Model Answer" : "Save Model Answer"}
                </Button>
              </NeoCard>
            );
          })}
        </div>
      ) : (
        <NeoCard className="py-12 text-center text-ink/40">
          <ClipboardCheck className="mx-auto mb-2" size={26} />
          Select a question paper to author model answers.
        </NeoCard>
      )}
    </div>
  );
}
