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
  uncertain?: boolean;
  question_type?: "mcq" | "short_answer";
  matched_keywords?: string[];
  missing_keywords?: string[];
  mcq?: {
    student_option: string | null;
    correct_option: string | null;
    is_correct: boolean;
    option_detected: boolean;
  };
  note?: string;
}

export interface Evaluation {
  id: number;
  answer_script_id: number;
  status: EvaluationStatus;
  status_detail?: string | null;
  ocr_raw_text?: string | null;
  extracted_answers?: ExtractedAnswer[] | null;
  has_uncertain_segments?: boolean;
  total_ai_marks?: number | null;
  total_max_marks?: number | null;
  total_teacher_marks?: number | null;
  final_marks?: number | null;
  confidence_score?: number | null;
  ai_model_version?: string | null;
  created_at: string;
  student_name?: string | null;
  student_usn?: string | null;
  examination_name?: string | null;
  answer_script_file_type?: string | null;
  question_context?: Record<
    string,
    {
      question_text: string;
      max_marks: number;
      question_type: string;
      reference_answer?: string | null;
      correct_option?: string | null;
      keywords?: string[];
    }
  > | null;
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
  question_type: "mcq" | "short_answer";
  options?: string[] | null;
}

export interface ExaminationPipelineStatus extends Examination {
  question_paper_title: string | null;
  scripts_uploaded: number;
  evaluations_completed: number;
  evaluations_approved: number;
  awaiting_evaluation: number;
  awaiting_review: number;
  next_action: string | null;
  next_action_route: string | null;
}

export interface ModelAnswerState {
  id: number;
  question_id: number;
  answer_text: string | null;
  correct_option: string | null;
  keywords: string[];
  expected_concepts: string[];
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
  // Enrichment from the list endpoint:
  student_name?: string | null;
  student_usn?: string | null;
  examination_name?: string | null;
  evaluation_status?: string;
  final_marks?: number | null;
  total_max_marks?: number | null;
  evaluation_id?: number | null;
}

export interface DashboardSummary {
  total_subjects: number;
  total_exams: number;
  students_evaluated: number;
  pending_evaluations: number;
  average_marks: number;
  todays_evaluations: number;
}
