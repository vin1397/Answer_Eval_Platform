import { useEffect, useState } from "react";
import { Plus, Trash2, CalendarRange } from "lucide-react";
import api from "../services/api";
import NeoCard from "../components/ui/NeoCard";
import Button from "../components/ui/Button";
import Modal from "../components/ui/Modal";
import PageHeader from "../components/ui/PageHeader";
import type { Semester, Scheme } from "../types";

export default function Semesters() {
  const [semesters, setSemesters] = useState<Semester[]>([]);
  const [schemes, setSchemes] = useState<Scheme[]>([]);
  const [semModal, setSemModal] = useState(false);
  const [schemeModal, setSchemeModal] = useState(false);
  const [semForm, setSemForm] = useState({ name: "", number: "" });
  const [schemeForm, setSchemeForm] = useState({ name: "", year: "" });

  function refresh() {
    api.get("/semesters").then((res) => setSemesters(res.data));
    api.get("/schemes").then((res) => setSchemes(res.data));
  }

  useEffect(refresh, []);

  async function createSemester() {
    await api.post("/semesters", { name: semForm.name, number: Number(semForm.number) });
    setSemModal(false);
    setSemForm({ name: "", number: "" });
    refresh();
  }

  async function createScheme() {
    await api.post("/schemes", { name: schemeForm.name, year: Number(schemeForm.year), is_active: true });
    setSchemeModal(false);
    setSchemeForm({ name: "", year: "" });
    refresh();
  }

  async function deleteSemester(id: number) {
    if (!confirm("Delete this semester?")) return;
    await api.delete(`/semesters/${id}`);
    refresh();
  }

  async function deleteScheme(id: number) {
    if (!confirm("Delete this scheme?")) return;
    await api.delete(`/schemes/${id}`);
    refresh();
  }

  return (
    <div>
      <PageHeader title="Semester & Scheme" subtitle="Configure the academic structure used across subjects" />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <NeoCard>
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-sm font-bold">Semesters</h3>
            <Button variant="ghost" icon={<Plus size={14} />} onClick={() => setSemModal(true)}>Add</Button>
          </div>
          <div className="space-y-2">
            {semesters.map((s) => (
              <div key={s.id} className="neo-inset flex items-center justify-between rounded-2xl px-4 py-3">
                <span className="text-sm font-medium">{s.name}</span>
                <button onClick={() => deleteSemester(s.id)} className="text-red-500"><Trash2 size={15} /></button>
              </div>
            ))}
            {semesters.length === 0 && (
              <p className="py-6 text-center text-sm text-ink/40"><CalendarRange className="mx-auto mb-2" size={22} />No semesters yet.</p>
            )}
          </div>
        </NeoCard>

        <NeoCard>
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-sm font-bold">Schemes</h3>
            <Button variant="ghost" icon={<Plus size={14} />} onClick={() => setSchemeModal(true)}>Add</Button>
          </div>
          <div className="space-y-2">
            {schemes.map((s) => (
              <div key={s.id} className="neo-inset flex items-center justify-between rounded-2xl px-4 py-3">
                <span className="text-sm font-medium">{s.name} ({s.year})</span>
                <button onClick={() => deleteScheme(s.id)} className="text-red-500"><Trash2 size={15} /></button>
              </div>
            ))}
            {schemes.length === 0 && (
              <p className="py-6 text-center text-sm text-ink/40"><CalendarRange className="mx-auto mb-2" size={22} />No schemes yet.</p>
            )}
          </div>
        </NeoCard>
      </div>

      <Modal open={semModal} onClose={() => setSemModal(false)} title="Add Semester">
        <div className="space-y-4">
          <input className="neo-input" placeholder="Name (e.g. Semester 5)" value={semForm.name}
            onChange={(e) => setSemForm({ ...semForm, name: e.target.value })} />
          <input className="neo-input" type="number" placeholder="Number (1-8)" value={semForm.number}
            onChange={(e) => setSemForm({ ...semForm, number: e.target.value })} />
          <Button className="w-full" onClick={createSemester}>Create Semester</Button>
        </div>
      </Modal>

      <Modal open={schemeModal} onClose={() => setSchemeModal(false)} title="Add Scheme">
        <div className="space-y-4">
          <input className="neo-input" placeholder="Name (e.g. 2022 Scheme)" value={schemeForm.name}
            onChange={(e) => setSchemeForm({ ...schemeForm, name: e.target.value })} />
          <input className="neo-input" type="number" placeholder="Year" value={schemeForm.year}
            onChange={(e) => setSchemeForm({ ...schemeForm, year: e.target.value })} />
          <Button className="w-full" onClick={createScheme}>Create Scheme</Button>
        </div>
      </Modal>
    </div>
  );
}
