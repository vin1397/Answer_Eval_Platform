import { useEffect, useRef, useState } from "react";
import { Plus, Pencil, Trash2, Users, Upload, Download, Eye } from "lucide-react";
import api from "../services/api";
import NeoCard from "../components/ui/NeoCard";
import Button from "../components/ui/Button";
import Modal from "../components/ui/Modal";
import PageHeader from "../components/ui/PageHeader";
import SearchInput from "../components/ui/SearchInput";
import StudentResultsModal from "../components/StudentResultsModal";
import type { Student, Semester, Paginated } from "../types";

const emptyForm = { usn: "", name: "", section: "", department: "", semester_id: "", email: "", phone: "" };

export default function Students() {
  const [data, setData] = useState<Paginated<Student> | null>(null);
  const [semesters, setSemesters] = useState<Semester[]>([]);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [loading, setLoading] = useState(true);
  const [resultsStudent, setResultsStudent] = useState<Student | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  function fetchStudents() {
    setLoading(true);
    api
      .get("/students", { params: { search: search || undefined, page, page_size: 10 } })
      .then((res) => setData(res.data))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    api.get("/semesters").then((res) => setSemesters(res.data));
  }, []);

  useEffect(() => {
    const t = setTimeout(fetchStudents, 300);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search, page]);

  function openCreate() {
    setEditingId(null);
    setForm(emptyForm);
    setModalOpen(true);
  }

  function openEdit(student: Student) {
    setEditingId(student.id);
    setForm({
      usn: student.usn, name: student.name, section: student.section, department: student.department,
      semester_id: String(student.semester_id), email: student.email || "", phone: student.phone || "",
    });
    setModalOpen(true);
  }

  async function handleSubmit() {
    const payload = { ...form, semester_id: Number(form.semester_id) };
    if (editingId) {
      const { usn, ...updatePayload } = payload;
      await api.put(`/students/${editingId}`, updatePayload);
    } else {
      await api.post("/students", payload);
    }
    setModalOpen(false);
    fetchStudents();
  }

  async function handleDelete(id: number) {
    if (!confirm("Delete this student?")) return;
    await api.delete(`/students/${id}`);
    fetchStudents();
  }

  async function handleImport(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    await api.post("/students/import-excel", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    fetchStudents();
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  async function handleExport() {
    const res = await api.get("/students/export-excel", { responseType: "blob" });
    const url = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", "students_export.xlsx");
    document.body.appendChild(link);
    link.click();
    link.remove();
  }

  return (
    <div>
      <PageHeader
        title="Students"
        subtitle="Manage the student roster used for evaluation mapping"
        action={
          <div className="flex gap-2">
            <input ref={fileInputRef} type="file" accept=".xlsx,.xls" className="hidden" onChange={handleImport} />
            <Button variant="ghost" icon={<Upload size={16} />} onClick={() => fileInputRef.current?.click()}>
              Import Excel
            </Button>
            <Button variant="ghost" icon={<Download size={16} />} onClick={handleExport}>
              Export Excel
            </Button>
            <Button icon={<Plus size={16} />} onClick={openCreate}>
              Add Student
            </Button>
          </div>
        }
      />

      <div className="mb-4 max-w-sm">
        <SearchInput value={search} onChange={setSearch} placeholder="Search by name or USN..." />
      </div>

      <NeoCard className="!p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-ink/5 dark:border-white/5 text-xs text-ink/50 dark:text-dark-ink/50">
                <th className="px-6 py-4">USN</th>
                <th className="px-6 py-4">Name</th>
                <th className="px-6 py-4">Semester</th>
                <th className="px-6 py-4">Section</th>
                <th className="px-6 py-4">Department</th>
                <th className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {(data?.items || []).map((s) => (
                <tr
                  key={s.id}
                  onClick={() => setResultsStudent(s)}
                  className="cursor-pointer border-b border-ink/5 transition hover:bg-primary/5 dark:border-white/5 last:border-0"
                  title="View student results"
                >
                  <td className="px-6 py-4 font-semibold text-primary">{s.usn}</td>
                  <td className="px-6 py-4">{s.name}</td>
                  <td className="px-6 py-4">
                    {semesters.find((sem) => sem.id === s.semester_id)?.name || "—"}
                  </td>
                  <td className="px-6 py-4">{s.section}</td>
                  <td className="px-6 py-4">{s.department}</td>
                  <td className="px-6 py-4">
                    <div className="flex justify-end gap-2">
                      <button
                        onClick={(e) => { e.stopPropagation(); setResultsStudent(s); }}
                        className="rounded-xl p-2 hover:bg-primary/10"
                        title="View results & marks"
                      >
                        <Eye size={15} />
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); openEdit(s); }}
                        className="rounded-xl p-2 hover:bg-primary/10"
                      >
                        <Pencil size={15} />
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); handleDelete(s.id); }}
                        className="rounded-xl p-2 text-red-500 hover:bg-red-50"
                      >
                        <Trash2 size={15} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {!loading && (data?.items?.length ?? 0) === 0 && (
                <tr>
                  <td colSpan={6} className="px-6 py-10 text-center text-ink/40">
                    <Users className="mx-auto mb-2" size={24} />
                    No students found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {data && data.total > 10 && (
          <div className="flex items-center justify-between px-6 py-4 text-xs">
            <span className="text-ink/50">
              Page {data.page} of {Math.ceil(data.total / data.page_size)}
            </span>
            <div className="flex gap-2">
              <Button variant="ghost" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>Prev</Button>
              <Button variant="ghost" disabled={page >= Math.ceil(data.total / data.page_size)} onClick={() => setPage((p) => p + 1)}>Next</Button>
            </div>
          </div>
        )}
      </NeoCard>

      <StudentResultsModal
        open={resultsStudent != null}
        onClose={() => setResultsStudent(null)}
        student={resultsStudent}
      />

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title={editingId ? "Edit Student" : "Add Student"}>
        <div className="space-y-4">
          <input className="neo-input" placeholder="USN" disabled={!!editingId} value={form.usn}
            onChange={(e) => setForm({ ...form, usn: e.target.value })} />
          <input className="neo-input" placeholder="Full Name" value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <div className="grid grid-cols-2 gap-4">
            <input className="neo-input" placeholder="Section" value={form.section}
              onChange={(e) => setForm({ ...form, section: e.target.value })} />
            <select className="neo-input" value={form.semester_id}
              onChange={(e) => setForm({ ...form, semester_id: e.target.value })}>
              <option value="">Semester</option>
              {semesters.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </div>
          <input className="neo-input" placeholder="Department" value={form.department}
            onChange={(e) => setForm({ ...form, department: e.target.value })} />
          <div className="grid grid-cols-2 gap-4">
            <input className="neo-input" placeholder="Email (optional)" value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })} />
            <input className="neo-input" placeholder="Phone (optional)" value={form.phone}
              onChange={(e) => setForm({ ...form, phone: e.target.value })} />
          </div>
          <Button className="w-full" onClick={handleSubmit}>
            {editingId ? "Save Changes" : "Create Student"}
          </Button>
        </div>
      </Modal>
    </div>
  );
}
