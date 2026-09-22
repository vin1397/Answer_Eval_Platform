import { useEffect, useState } from "react";
import { Upload, FileText, ChevronDown, ChevronUp, Eye } from "lucide-react";
import api from "../services/api";
import NeoCard from "../components/ui/NeoCard";
import Button from "../components/ui/Button";
import Modal from "../components/ui/Modal";
import PageHeader from "../components/ui/PageHeader";
import ScriptViewer from "../components/ScriptViewer";
import type { QuestionPaper, Subject } from "../types";

export default function QuestionPapers() {
  const [papers, setPapers] = useState<QuestionPaper[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [expanded, setExpanded] = useState<number | null>(null);
  const [title, setTitle] = useState("");
  const [subjectId, setSubjectId] = useState("");
  const [totalMarks, setTotalMarks] = useState(100);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [viewingPaper, setViewingPaper] = useState<QuestionPaper | null>(null);

  function refresh() {
    api.get("/question-papers").then((res) => setPapers(res.data));
  }

  useEffect(() => {
    refresh();
    api.get("/subjects", { params: { page_size: 100 } }).then((res) => setSubjects(res.data.items));
  }, []);

  async function handleUpload() {
    if (!file || !subjectId || !title) return;
    setUploading(true);
    const formData = new FormData();
    formData.append("title", title);
    formData.append("subject_id", subjectId);
    formData.append("total_marks", String(totalMarks));
    formData.append("auto_extract", "true");
    formData.append("file", file);
    try {
      await api.post("/question-papers/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setModalOpen(false);
      setTitle("");
      setSubjectId("");
      setFile(null);
      refresh();
    } finally {
      setUploading(false);
    }
  }

  return (
    <div>
      <PageHeader
        title="Question Papers"
        subtitle="Upload PDF/DOCX question papers — questions are auto-extracted"
        action={<Button icon={<Upload size={16} />} onClick={() => setModalOpen(true)}>Upload Paper</Button>}
      />

      <div className="space-y-4">
        {papers.map((paper) => (
          <NeoCard key={paper.id} className="!p-0 overflow-hidden">
            <button
              onClick={() => setExpanded(expanded === paper.id ? null : paper.id)}
              className="flex w-full items-center justify-between px-6 py-5"
            >
              <div className="flex items-center gap-4">
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                  <FileText size={20} />
                </div>
                <div className="text-left">
                  <p className="font-bold">{paper.title}</p>
                  <p className="text-xs text-ink/50">
                    {paper.questions.length} questions • {paper.total_marks} marks • {paper.file_type.toUpperCase()}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={(e) => { e.stopPropagation(); setViewingPaper(paper); }}
                  className="inline-flex items-center gap-1.5 rounded-full bg-primary/10 px-3 py-1.5 text-xs font-semibold text-primary transition hover:bg-primary/20"
                  title="View the original document"
                >
                  <Eye size={13} /> View paper
                </button>
                {expanded === paper.id ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
              </div>
            </button>
            {expanded === paper.id && (
              <div className="border-t border-ink/5 dark:border-white/5 px-6 py-4">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="text-xs text-ink/50">
                      <th className="py-2">Q.No</th>
                      <th className="py-2">Question</th>
                      <th className="py-2">Marks</th>
                      <th className="py-2">Difficulty</th>
                    </tr>
                  </thead>
                  <tbody>
                    {paper.questions.map((q) => (
                      <tr key={q.id} className="border-t border-ink/5 dark:border-white/5">
                        <td className="py-2 font-semibold">{q.question_number}</td>
                        <td className="py-2 max-w-lg">{q.question_text}</td>
                        <td className="py-2">{q.max_marks}</td>
                        <td className="py-2 capitalize">{q.difficulty}</td>
                      </tr>
                    ))}
                    {paper.questions.length === 0 && (
                      <tr><td colSpan={4} className="py-4 text-center text-ink/40">No questions extracted — add manually via API.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </NeoCard>
        ))}
        {papers.length === 0 && (
          <NeoCard className="py-12 text-center text-ink/40">
            <FileText className="mx-auto mb-2" size={26} />
            No question papers uploaded yet.
          </NeoCard>
        )}
      </div>

      <ScriptViewer
        open={viewingPaper != null}
        onClose={() => setViewingPaper(null)}
        fileId={viewingPaper?.id ?? null}
        fileType={viewingPaper?.file_type ?? null}
        fileUrl={viewingPaper ? `/question-papers/${viewingPaper.id}/file` : undefined}
        title={viewingPaper?.title ?? "Question Paper"}
        subtitle={viewingPaper ? `${viewingPaper.questions.length} questions • ${viewingPaper.total_marks} marks` : undefined}
      />

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="Upload Question Paper">
        <div className="space-y-4">
          <input className="neo-input" placeholder="Paper Title" value={title} onChange={(e) => setTitle(e.target.value)} />
          <select className="neo-input" value={subjectId} onChange={(e) => setSubjectId(e.target.value)}>
            <option value="">Select Subject</option>
            {subjects.map((s) => <option key={s.id} value={s.id}>{s.code} — {s.name}</option>)}
          </select>
          <input className="neo-input" type="number" placeholder="Total Marks" value={totalMarks}
            onChange={(e) => setTotalMarks(Number(e.target.value))} />
          <label className="neo-inset flex cursor-pointer flex-col items-center justify-center gap-2 rounded-2xl px-4 py-8 text-sm">
            <Upload size={20} className="text-primary" />
            {file ? file.name : "Click to select PDF or DOCX"}
            <input type="file" accept=".pdf,.docx" className="hidden" onChange={(e) => setFile(e.target.files?.[0] || null)} />
          </label>
          <Button className="w-full" onClick={handleUpload} disabled={uploading || !file || !subjectId || !title}>
            {uploading ? "Uploading & Extracting..." : "Upload & Extract Questions"}
          </Button>
        </div>
      </Modal>
    </div>
  );
}
