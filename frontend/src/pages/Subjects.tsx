import { useEffect, useState } from "react";
import { Plus, Pencil, Trash2, BookOpen } from "lucide-react";
import api from "../services/api";
import NeoCard from "../components/ui/NeoCard";
import Button from "../components/ui/Button";
import Modal from "../components/ui/Modal";
import PageHeader from "../components/ui/PageHeader";
import SearchInput from "../components/ui/SearchInput";
import type { Subject, Semester, Scheme, Faculty, Paginated } from "../types";

const emptyForm = {
  code: "", name: "", credits: 4, department: "", semester_id: "", scheme_id: "", faculty_id: "",
};

export default function Subjects() {
  const [data, setData] = useState<Paginated<Subject> | null>(null);
  const [semesters, setSemesters] = useState<Semester[]>([]);
  const [schemes, setSchemes] = useState<Scheme[]>([]);
  const [faculty, setFaculty] = useState<Faculty[]>([]);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [loading, setLoading] = useState(true);

  function fetchSubjects() {
    setLoading(true);
    api
      .get("/subjects", { params: { search: search || undefined, page, page_size: 10 } })
      .then((res) => setData(res.data))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    Promise.all([api.get("/semesters"), api.get("/schemes"), api.get("/faculty")]).then(
      ([s, sc, f]) => {
        setSemesters(s.data);
        setSchemes(sc.data);
        setFaculty(f.data);
      }
    );
  }, []);

  useEffect(() => {
    const t = setTimeout(fetchSubjects, 300);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search, page]);

  function openCreate() {
    setEditingId(null);
    setForm(emptyForm);
    setModalOpen(true);
  }

  function openEdit(subject: Subject) {
    setEditingId(subject.id);
    setForm({
      code: subject.code,
      name: subject.name,
      credits: subject.credits,
      department: subject.department,
      semester_id: String(subject.semester_id),
      scheme_id: String(subject.scheme_id),
      faculty_id: subject.faculty_id ? String(subject.faculty_id) : "",
    });
    setModalOpen(true);
  }

  async function handleSubmit() {
    const payload = {
      ...form,
      credits: Number(form.credits),
      semester_id: Number(form.semester_id),
      scheme_id: Number(form.scheme_id),
      faculty_id: form.faculty_id ? Number(form.faculty_id) : null,
    };
    if (editingId) {
      await api.put(`/subjects/${editingId}`, payload);
    } else {
      await api.post("/subjects", payload);
    }
    setModalOpen(false);
    fetchSubjects();
  }

  async function handleDelete(id: number) {
    if (!confirm("Delete this subject?")) return;
    await api.delete(`/subjects/${id}`);
    fetchSubjects();
  }

  return (
    <div>
      <PageHeader
        title="Subjects"
        subtitle="Manage subjects across semesters and schemes"
        action={
          <Button icon={<Plus size={16} />} onClick={openCreate}>
            Add Subject
          </Button>
        }
      />

      <div className="mb-4 max-w-sm">
        <SearchInput value={search} onChange={setSearch} placeholder="Search by name or code..." />
      </div>

      <NeoCard className="!p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-ink/5 dark:border-white/5 text-xs text-ink/50 dark:text-dark-ink/50">
                <th className="px-6 py-4">Code</th>
                <th className="px-6 py-4">Name</th>
                <th className="px-6 py-4">Credits</th>
                <th className="px-6 py-4">Department</th>
                <th className="px-6 py-4">Semester</th>
                <th className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {(data?.items || []).map((s) => (
                <tr key={s.id} className="border-b border-ink/5 dark:border-white/5 last:border-0">
                  <td className="px-6 py-4 font-semibold text-primary">{s.code}</td>
                  <td className="px-6 py-4">{s.name}</td>
                  <td className="px-6 py-4">{s.credits}</td>
                  <td className="px-6 py-4">{s.department}</td>
                  <td className="px-6 py-4">
                    {semesters.find((sem) => sem.id === s.semester_id)?.name || "—"}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex justify-end gap-2">
                      <button onClick={() => openEdit(s)} className="rounded-xl p-2 hover:bg-primary/10">
                        <Pencil size={15} />
                      </button>
                      <button onClick={() => handleDelete(s.id)} className="rounded-xl p-2 text-red-500 hover:bg-red-50">
                        <Trash2 size={15} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {!loading && (data?.items?.length ?? 0) === 0 && (
                <tr>
                  <td colSpan={6} className="px-6 py-10 text-center text-ink/40">
                    <BookOpen className="mx-auto mb-2" size={24} />
                    No subjects found.
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
              <Button variant="ghost" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                Prev
              </Button>
              <Button
                variant="ghost"
                disabled={page >= Math.ceil(data.total / data.page_size)}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </Button>
            </div>
          </div>
        )}
      </NeoCard>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title={editingId ? "Edit Subject" : "Add Subject"}>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <input className="neo-input" placeholder="Subject Code" value={form.code}
              onChange={(e) => setForm({ ...form, code: e.target.value })} />
            <input className="neo-input" type="number" placeholder="Credits" value={form.credits}
              onChange={(e) => setForm({ ...form, credits: Number(e.target.value) })} />
          </div>
          <input className="neo-input" placeholder="Subject Name" value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <input className="neo-input" placeholder="Department" value={form.department}
            onChange={(e) => setForm({ ...form, department: e.target.value })} />
          <div className="grid grid-cols-2 gap-4">
            <select className="neo-input" value={form.semester_id}
              onChange={(e) => setForm({ ...form, semester_id: e.target.value })}>
              <option value="">Semester</option>
              {semesters.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
            <select className="neo-input" value={form.scheme_id}
              onChange={(e) => setForm({ ...form, scheme_id: e.target.value })}>
              <option value="">Scheme</option>
              {schemes.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </div>
          <select className="neo-input" value={form.faculty_id}
            onChange={(e) => setForm({ ...form, faculty_id: e.target.value })}>
            <option value="">Faculty In-Charge (optional)</option>
            {faculty.map((f) => <option key={f.id} value={f.id}>{f.name}</option>)}
          </select>
          <Button className="w-full" onClick={handleSubmit}>
            {editingId ? "Save Changes" : "Create Subject"}
          </Button>
        </div>
      </Modal>
    </div>
  );
}
