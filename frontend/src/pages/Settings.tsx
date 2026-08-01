import { useEffect, useState } from "react";
import { Save, KeyRound, Building2 } from "lucide-react";
import api from "../services/api";
import NeoCard from "../components/ui/NeoCard";
import Button from "../components/ui/Button";
import PageHeader from "../components/ui/PageHeader";
import { useAuth } from "../context/AuthContext";

export default function Settings() {
  const { user } = useAuth();
  const [instituteName, setInstituteName] = useState("");
  const [departments, setDepartments] = useState("");
  const [saving, setSaving] = useState(false);
  const [savedMsg, setSavedMsg] = useState("");

  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [pwMsg, setPwMsg] = useState("");

  useEffect(() => {
    api.get("/settings/institute").then((res) => {
      setInstituteName(res.data.institute_name || "");
      setDepartments((res.data.departments || []).join(", "));
    });
  }, []);

  async function saveInstitute() {
    setSaving(true);
    try {
      await api.put("/settings/institute", {
        institute_name: instituteName,
        departments: departments.split(",").map((d) => d.trim()).filter(Boolean),
        default_pass_percentage: 40,
      });
      setSavedMsg("Saved successfully");
      setTimeout(() => setSavedMsg(""), 2000);
    } finally {
      setSaving(false);
    }
  }

  async function changePassword() {
    setPwMsg("");
    try {
      await api.post("/auth/change-password", { old_password: oldPassword, new_password: newPassword });
      setPwMsg("Password updated");
      setOldPassword("");
      setNewPassword("");
    } catch (err: any) {
      setPwMsg(err?.response?.data?.detail || "Failed to update password");
    }
  }

  return (
    <div>
      <PageHeader title="Settings" subtitle="Institute configuration and account security" />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <NeoCard>
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 text-primary">
            <Building2 size={20} />
          </div>
          <h3 className="mt-4 font-bold">Institute Settings</h3>
          <div className="mt-4 space-y-4">
            <input className="neo-input" placeholder="Institute Name" value={instituteName}
              onChange={(e) => setInstituteName(e.target.value)} />
            <input className="neo-input" placeholder="Departments (comma separated)" value={departments}
              onChange={(e) => setDepartments(e.target.value)} />
            <Button icon={<Save size={15} />} onClick={saveInstitute} disabled={saving}>
              {saving ? "Saving..." : "Save Settings"}
            </Button>
            {savedMsg && <p className="text-xs text-emerald-600">{savedMsg}</p>}
          </div>
        </NeoCard>

        <NeoCard>
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 text-primary">
            <KeyRound size={20} />
          </div>
          <h3 className="mt-4 font-bold">Account Security</h3>
          <p className="mt-1 text-xs text-ink/50">Signed in as {user?.full_name} ({user?.username})</p>
          <div className="mt-4 space-y-4">
            <input className="neo-input" type="password" placeholder="Current Password" value={oldPassword}
              onChange={(e) => setOldPassword(e.target.value)} />
            <input className="neo-input" type="password" placeholder="New Password" value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)} />
            <Button icon={<KeyRound size={15} />} onClick={changePassword}>Update Password</Button>
            {pwMsg && <p className="text-xs text-ink/60">{pwMsg}</p>}
          </div>
        </NeoCard>
      </div>
    </div>
  );
}
