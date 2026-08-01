import { Routes, Route } from "react-router-dom";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import NotFound from "./pages/NotFound";
import DashboardLayout from "./layouts/DashboardLayout";
import Dashboard from "./pages/Dashboard";
import Subjects from "./pages/Subjects";
import Semesters from "./pages/Semesters";
import Faculty from "./pages/Faculty";
import Students from "./pages/Students";
import QuestionPapers from "./pages/QuestionPapers";
import ModelAnswers from "./pages/ModelAnswers";
import Examinations from "./pages/Examinations";
import AnswerScripts from "./pages/AnswerScripts";
import AIEvaluation from "./pages/AIEvaluation";
import TeacherReview from "./pages/TeacherReview";
import Reports from "./pages/Reports";
import Analytics from "./pages/Analytics";
import Settings from "./pages/Settings";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />

      <Route path="/app" element={<DashboardLayout />}>
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="subjects" element={<Subjects />} />
        <Route path="semesters" element={<Semesters />} />
        <Route path="faculty" element={<Faculty />} />
        <Route path="students" element={<Students />} />
        <Route path="question-papers" element={<QuestionPapers />} />
        <Route path="model-answers" element={<ModelAnswers />} />
        <Route path="examinations" element={<Examinations />} />
        <Route path="answer-scripts" element={<AnswerScripts />} />
        <Route path="ai-evaluation" element={<AIEvaluation />} />
        <Route path="teacher-review" element={<TeacherReview />} />
        <Route path="reports" element={<Reports />} />
        <Route path="analytics" element={<Analytics />} />
        <Route path="settings" element={<Settings />} />
      </Route>

      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
