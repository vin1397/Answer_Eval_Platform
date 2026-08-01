import { useEffect, useState } from "react";
import { ClipboardCheck, Save } from "lucide-react";
import api from "../services/api";
import NeoCard from "../components/ui/NeoCard";
import Button from "../components/ui/Button";
import PageHeader from "../components/ui/PageHeader";
import type { QuestionPaper } from "../types";

export default function ModelAnswers() {
  const [papers, setPapers] = useState<QuestionPaper[]>([]);
  const [selectedPaper, setSelectedPaper] = useState<number | "">("");
  const [forms, setForms] = useState<Record<number, { answer_text: string; keywords: string; expected_concepts: string }>>({});
  const [savingId, setSavingId] = useState<number | null>(null);

  useEffect(() => {
    api.get("/question-papers").then((res) => setPapers(res.data));
  }, []);

  const activePaper = papers.find((p) => p.id === selectedPaper);

  function updateForm(questionId: number, field: string, value: string) {
    setForms((prev) => ({
      ...prev,
      [questionId]: { ...prev[questionId], [field]: value } as any,
    }));
  }

  async function saveModelAnswer(questionId: number) {
    const form = forms[questionId];
    if (!form?.answer_text) return;
    setSavingId(questionId);
    try {
      await api.post("/model-answers", {
        question_id: questionId,
        answer_text: form.answer_text,
        keywords: form.keywords ? form.keywords.split(",").map((k) => k.trim()).filter(Boolean) : [],
        expected_concepts: form.expected_concepts
          ? form.expected_concepts.split(",").map((k) => k.trim()).filter(Boolean)
          : [],
        rubric: [],
      });
    } finally {
      setSavingId(null);
    }
  }

  return (
    <div>
      <PageHeader title="Model Answers" subtitle="Author faculty reference answers, keywords, and expected concepts per question" />

      <div className="mb-6 max-w-sm">
        <select className="neo-input" value={selectedPaper} onChange={(e) => setSelectedPaper(Number(e.target.value) || "")}>
          <option value="">Select a question paper</option>
          {papers.map((p) => <option key={p.id} value={p.id}>{p.title}</option>)}
        </select>
      </div>

      {activePaper ? (
        <div className="space-y-5">
          {activePaper.questions.map((q) => (
            <NeoCard key={q.id}>
              <div className="mb-3 flex items-center justify-between">
                <p className="font-bold">Q{q.question_number}. {q.question_text}</p>
                <span className="rounded-full bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">{q.max_marks} marks</span>
              </div>
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
              <Button className="mt-4" icon={<Save size={15} />} onClick={() => saveModelAnswer(q.id)} disabled={savingId === q.id}>
                {savingId === q.id ? "Saving..." : "Save Model Answer"}
              </Button>
            </NeoCard>
          ))}
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
