export type UserRole = "admin" | "teacher";

export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: UserRole;
  department?: string | null;
  is_active: boolean;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface Semester {
  id: number;
  name: string;
  number: number;
}

export interface Scheme {
  id: number;
  name: string;
  year: number;
  is_active: boolean;
}

export interface Faculty {
  id: number;
  name: string;
  designation?: string | null;
  department: string;
  email: string;
  phone?: string | null;
}

export interface Subject {
  id: number;
  code: string;
  name: string;
  credits: number;
  department: string;
  semester_id: number;
  scheme_id: number;
  faculty_id?: number | null;
  created_at: string;
}

export interface Student {
  id: number;
  usn: string;
  name: string;
  section: string;
  department: string;
  semester_id: number;
  email?: string | null;
  phone?: string | null;
  created_at: string;
}

export interface Paginated<T> {
  total: number;
  page: number;
  page_size: number;
  items: T[];
}

export type EvaluationStatus =
  | "pending"
  | "ocr_in_progress"
  | "nlp_in_progress"
  | "ai_evaluated"
  | "under_review"
  | "approved"
  | "rejected"
  | "re_evaluation_requested"
  | "failed";

export interface ExtractedAnswer {
  question_number: string;
  answer_text: string;
  semantic_score: number;
  keyword_score: number;
  ai_marks: number;
  max_marks: number;
  confidence?: number;
  matched_keywords?: string[];
  missing_keywords?: string[];
  note?: string;
}

export interface Evaluation {
  id: number;
  answer_script_id: number;
  status: EvaluationStatus;
  ocr_raw_text?: string | null;
  extracted_answers?: ExtractedAnswer[] | null;
  total_ai_marks?: number | null;
  total_max_marks?: number | null;
  total_teacher_marks?: number | null;
  confidence_score?: number | null;
  ai_model_version?: string | null;
  created_at: string;
}

export interface QuestionPaper {
  id: number;
  title: string;
  file_path: string;
  file_type: string;
  total_marks: number;
  subject_id: number;
  created_at: string;
  questions: Question[];
}

export interface Question {
  id: number;
  question_paper_id: number;
  question_number: string;
  question_text: string;
  max_marks: number;
  difficulty: "easy" | "medium" | "hard";
  bloom_level: string;
}

export interface Examination {
  id: number;
  name: string;
  exam_date: string;
  subject_id: number;
  question_paper_id?: number | null;
  created_at: string;
}

export interface AnswerScript {
  id: number;
  file_path: string;
  file_type: string;
  page_count: number;
  upload_status: string;
  examination_id: number;
  student_id: number;
  created_at: string;
}

export interface DashboardSummary {
  total_subjects: number;
  total_exams: number;
  students_evaluated: number;
  pending_evaluations: number;
  average_marks: number;
  todays_evaluations: number;
}
