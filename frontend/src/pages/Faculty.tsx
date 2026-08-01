import { useEffect, useState } from "react";
import { Plus, Trash2, GraduationCap } from "lucide-react";
import api from "../services/api";
import NeoCard from "../components/ui/NeoCard";
import Button from "../components/ui/Button";
import Modal from "../components/ui/Modal";
import PageHeader from "../components/ui/PageHeader";
import type { Faculty as FacultyType } from "../types";

const emptyForm = { name: "", designation: "", department: "", email: "", phone: "" };

export default function Faculty() {
  const [faculty, setFaculty] = useState<FacultyType[]>([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState(emptyForm);

  function refresh() {
    api.get("/faculty").then((res) => setFaculty(res.data));
  }

  useEffect(refresh, []);

  async function handleSubmit() {
    await api.post("/faculty", form);
    setModalOpen(false);
    setForm(emptyForm);
    refresh();
  }

  async function handleDelete(id: number) {
    if (!confirm("Delete this faculty member?")) return;
    await api.delete(`/faculty/${id}`);
    refresh();
  }

  return (
    <div>
      <PageHeader
        title="Faculty"
        subtitle="Manage faculty in charge of subjects"
        action={<Button icon={<Plus size={16} />} onClick={() => setModalOpen(true)}>Add Faculty</Button>}
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {faculty.map((f) => (
          <NeoCard key={f.id} className="relative">
            <button onClick={() => handleDelete(f.id)} className="absolute right-4 top-4 text-red-500">
              <Trash2 size={15} />
            </button>
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 text-primary">
              <GraduationCap size={20} />
            </div>
            <h3 className="mt-4 font-bold">{f.name}</h3>
            <p className="text-xs text-ink/50">{f.designation || "Faculty"} • {f.department}</p>
            <p className="mt-2 text-xs text-ink/60">{f.email}</p>
          </NeoCard>
        ))}
        {faculty.length === 0 && (
          <p className="col-span-full py-10 text-center text-sm text-ink/40">No faculty added yet.</p>
        )}
      </div>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="Add Faculty">
        <div className="space-y-4">
          <input className="neo-input" placeholder="Full Name" value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <div className="grid grid-cols-2 gap-4">
            <input className="neo-input" placeholder="Designation" value={form.designation}
              onChange={(e) => setForm({ ...form, designation: e.target.value })} />
            <input className="neo-input" placeholder="Department" value={form.department}
              onChange={(e) => setForm({ ...form, department: e.target.value })} />
          </div>
          <input className="neo-input" placeholder="Email" value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })} />
          <input className="neo-input" placeholder="Phone (optional)" value={form.phone}
            onChange={(e) => setForm({ ...form, phone: e.target.value })} />
          <Button className="w-full" onClick={handleSubmit}>Add Faculty</Button>
        </div>
      </Modal>
    </div>
  );
}
