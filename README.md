

````markdown
# Intelligent Answer Script Evaluation & Automated Mark Assignment

> AI-powered platform for evaluating handwritten student answer scripts,
> comparing answers against faculty-provided references, assigning marks,
> and allowing teacher verification before finalization.

---

## 📌 Project Overview

**Answer_Eval_Platform** is an AI-powered examination evaluation platform
designed to automate the evaluation of handwritten student answer scripts.

The system accepts:

1. A **Question Paper**
2. A **Faculty Model Answer / Answer Key**
3. A **Student Handwritten Answer Script**

It then:

```text
Question Paper
      │
      ▼
Question Extraction
      │
      ▼
Model Answers / Rubrics
      │
      │
      │
Student Answer Script
      │
      ▼
PDF / Image Processing
      │
      ▼
Page Extraction
      │
      ▼
Handwriting Line Segmentation
      │
      ▼
Local TrOCR
      │
      ▼
OCR Text
      │
      ▼
Question Association
      │
      ▼
Answer Evaluation
      │
      ├── MCQ → Exact Option Matching
      │
      └── Descriptive → Semantic + Keyword/Rubric Matching
      │
      ▼
AI Marks
      │
      ▼
Confidence Evaluation
      │
      ├── High Confidence → Auto Approval
      │
      └── Low / Uncertain → Teacher Review
      │
      ▼
Teacher Verification / Override
      │
      ▼
Final Marks
      │
      ▼
Reports / Analytics
````

The goal is **not** to blindly replace teachers.

The system is designed as:

> **AI-assisted evaluation with teacher verification.**

---

# 🎯 Main Objectives

The platform is being developed to achieve the following:

- Automatically read handwritten answer scripts.
- Convert handwriting into machine-readable text.
- Identify which answer belongs to which question.
- Compare student answers with faculty-provided answers.
- Evaluate MCQ and descriptive questions differently.
- Assign AI-generated marks.
- Estimate evaluation confidence.
- Automatically flag uncertain evaluations.
- Allow teachers to review and override AI marks.
- Generate final examination reports.
- Learn from teacher corrections in future iterations.

---

# 🧠 Core Architecture

```text
                    ┌─────────────────────┐
                    │    Question Paper   │
                    │      PDF / DOCX     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Question Paper      │
                    │ Parser              │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Questions + Marks   │
                    │ + Question Type     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Faculty Model       │
                    │ Answers / Rubrics   │
                    └──────────┬──────────┘
                               │
                               │
                               │
┌───────────────────┐          │
│ Student Answer    │          │
│ Script PDF/Image  │          │
└─────────┬─────────┘          │
          │                    │
          ▼                    │
┌───────────────────┐          │
│ PDF Page          │          │
│ Extraction        │          │
└─────────┬─────────┘          │
          │                    │
          ▼                    │
┌───────────────────┐          │
│ Image             │          │
│ Preprocessing     │          │
└─────────┬─────────┘          │
          │                    │
          ▼                    │
┌───────────────────┐          │
│ Line Segmentation │          │
└─────────┬─────────┘          │
          │                    │
          ▼                    │
┌───────────────────┐
│ Local TrOCR       │
│ Handwriting OCR   │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ OCR Text +        │
│ Confidence        │
└─────────┬─────────┘
          │
          ▼
┌────────────────────────────┐
│ Question Marker Association│
└────────────┬───────────────┘
             │
             ▼
      ┌───────────────┐
      │ Evaluation    │
      │ Pipeline      │
      └───────┬───────┘
              │
       ┌──────┴────────┐
       ▼               ▼
     MCQ          Descriptive
       │               │
       ▼               ▼
 Exact Option      Semantic +
 Matching          Keyword/Rubric
       │               │
       └───────┬───────┘
               ▼
        ┌──────────────┐
        │ AI Marks     │
        └──────┬───────┘
               │
               ▼
        ┌──────────────┐
        │ Confidence   │
        └──────┬───────┘
               │
       ┌───────┴─────────┐
       ▼                 ▼
   Approved          Teacher Review
                         │
                         ▼
                  Teacher Override
                         │
                         ▼
                    Final Marks
```

---

# 🏗️ Repository Structure

```text
Answer_Eval_Platform/
│
├── backend/
│   │
│   ├── ai/
│   │   ├── ocr/
│   │   │   ├── ocr_service.py
│   │   │   ├── trocr_service.py
│   │   │   └── handwriting_segmentation.py
│   │   │
│   │   ├── nlp/
│   │   │   └── nlp_service.py
│   │   │
│   │   └── ml/
│   │       └── ml_service.py
│   │
│   ├── api/
│   │   ├── auth.py
│   │   ├── subjects.py
│   │   ├── students.py
│   │   ├── faculty.py
│   │   ├── question_papers.py
│   │   ├── model_answers.py
│   │   ├── examinations.py
│   │   ├── answer_scripts.py
│   │   ├── evaluations.py
│   │   ├── teacher_review.py
│   │   └── reports.py
│   │
│   ├── models/
│   │   ├── exam.py
│   │   └── ...
│   │
│   ├── services/
│   │   ├── evaluation_pipeline.py
│   │   ├── document_parser.py
│   │   ├── storage_service.py
│   │   └── celery_app.py
│   │
│   ├── scripts/
│   │   ├── seed_admin.py
│   │   └── migrate_add_trocr_columns.py
│   │
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_document_parser.py
│   │   ├── test_final_marks.py
│   │   ├── test_handwriting_segmentation.py
│   │   ├── test_mcq_scoring.py
│   │   └── test_trocr_model_loading.py
│   │
│   ├── requirements.txt
│   ├── requirements-lite.txt
│   └── main.py
│
├── frontend/
│   │
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── services/
│   │   └── ...
│   │
│   ├── package.json
│   └── vite.config.ts
│
├── models/
│   └── handwriting/
│       └── trocr-base-handwritten/
│
├── dataset/
│   ├── train.parquet
│   ├── test.parquet
│   └── validation.parquet
│
├── datasets/
│   └── handwriting/
│       └── benchmark_results/
│           └── trocr_test_results.csv
│
├── training/
│   └── handwriting/
│       └── test_trocr_dataset.py
│
├── scripts/
│   └── ...
│
├── .gitignore
├── main.py
└── README.md
```

---

# 🔬 AI Pipeline

## 1. Question Paper Processing

The faculty uploads a:

- PDF
- DOCX

The document parser extracts:

- Question number
- Question text
- Maximum marks
- MCQ options
- Question type

Question types are detected generically.

The system does **not** assume:

```text
Q1-Q20 = MCQ
Q21-Q35 = descriptive
```

Instead, question types are detected from the document.

This allows mixed question papers such as:

```text
Q1  → MCQ
Q2  → Descriptive
Q3  → MCQ
Q4  → Descriptive
Q5  → MCQ
```

---

# 📝 2. Faculty Model Answers

Each question can have a model answer.

## MCQ

Example:

```text
Question:
Which of the following is an assumption of Linear Regression?

A. High multicollinearity
B. Little or no autocorrelation
C. Heteroscedasticity
D. All of the mentioned

Correct Option:
B
```

The system uses normalized exact option matching.

No semantic model is required for MCQs.

---

## Descriptive Questions

Example:

```text
Question:
Define Supervised Learning.

Reference Answer:
A type of ML where the model is trained on
labeled data with known inputs and outputs.

Keywords:
labeled data
known inputs
known outputs
machine learning
```

The evaluator can use:

- Semantic similarity
- Keyword matching
- Rubric information

---

# ✍️ 3. Handwritten Answer Processing

Student answer scripts can be:

- PDF
- JPG
- PNG

The pipeline is:

```text
Student PDF
     ↓
PDF Page Extraction
     ↓
Image Preprocessing
     ↓
Horizontal Projection
     ↓
Line Detection
     ↓
Line Crops
     ↓
TrOCR
     ↓
Recognized Text
```

---

# 🤖 4. TrOCR Handwriting Recognition

The project uses:

```text
microsoft/trocr-base-handwritten
```

The model is executed locally.

The application uses:

```text
local_files_only=True
```

Therefore:

- No cloud OCR API is required.
- No handwriting data is sent to an external OCR provider.
- The model is not downloaded during evaluation.
- Missing model files produce an explicit error.

---

# ⚠️ Important TrOCR Limitation

TrOCR is designed for **text-line recognition**.

It should NOT receive an entire handwritten exam page.

Incorrect:

```text
Full Page
   ↓
TrOCR
```

Correct:

```text
Full Page
   ↓
Line Segmentation
   ↓
Individual Line
   ↓
TrOCR
```

This distinction is extremely important for this project.

Testing confirmed that line-level recognition is significantly more useful than directly passing an entire answer page.

---

# 📦 Local TrOCR Model Setup

Expected location:

```text
models/
└── handwriting/
    └── trocr-base-handwritten/
        ├── config.json
        ├── generation_config.json
        ├── merges.txt
        ├── preprocessor_config.json
        ├── special_tokens_map.json
        ├── tokenizer_config.json
        ├── vocab.json
        └── model.safetensors
```

The actual model weights are intentionally not part of normal Git source management.

The model can be configured through:

```env
TROCR_MODEL_DIR=../models/handwriting/trocr-base-handwritten
```

---

# ⚙️ Environment Configuration

Backend `.env` example:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/answer_eval

OCR_ENGINE=trocr

TROCR_MODEL_DIR=../models/handwriting/trocr-base-handwritten

TROCR_DEVICE=auto

SCAN_DPI=300

LOW_CONFIDENCE_LINE_THRESHOLD=0.35

AUTO_APPROVE_CONFIDENCE_THRESHOLD=0.85
```

---

# 📊 OCR Dataset

The project currently uses a handwriting dataset stored as:

```text
dataset/
├── train.parquet
├── test.parquet
└── validation.parquet
```

The dataset contains:

```text
text
image
```

The `text` field provides the ground-truth transcription.

This is important because it allows objective OCR evaluation.

---

# 🧪 OCR Benchmark

Before attempting fine-tuning, the existing TrOCR model was tested against the ground-truth handwriting dataset.

The benchmark script is:

```text
training/handwriting/test_trocr_dataset.py
```

Run:

```powershell
.\backend\venv\Scripts\python.exe training\handwriting\test_trocr_dataset.py
```

The benchmark evaluates:

- Successful OCR runs
- Exact matches
- Character Error Rate (CER)
- Word Error Rate (WER)

---

# 📈 Current OCR Benchmark

The current 100-sample benchmark produced:

```text
Samples tested : 100
Successful     : 100
Exact matches  : 18 / 100

Average CER    : 7.14%
Average WER    : 28.92%
```

Results:

```text
datasets/
└── handwriting/
    └── benchmark_results/
        └── trocr_test_results.csv
```

---

# 📌 How to Interpret the Benchmark

## CER

Character Error Rate measures character-level mistakes.

Current:

```text
CER = 7.14%
```

This indicates that the model is recognizing most individual characters correctly.

---

## WER

Word Error Rate measures word-level mistakes.

Current:

```text
WER = 28.92%
```

This is considerably higher than CER.

This means the model can recognize characters reasonably well while still producing incorrect word boundaries or complete words.

---

## Exact Match

Current:

```text
18 / 100
```

Only 18 samples matched the reference transcription exactly.

Therefore, the current OCR should **not yet be considered perfect**.

The next step is to inspect the failed predictions rather than immediately fine-tuning.

---

# 🔍 Inspect OCR Failures

Use:

```powershell
.\backend\venv\Scripts\python.exe -c "import pandas as pd; f=r'.\datasets\handwriting\benchmark_results\trocr_test_results.csv'; df=pd.read_csv(f); print(df.sort_values('wer',ascending=False)[['sample','reference','prediction','cer','wer']].head(10).to_string(index=False))"
```

This displays the worst predictions.

The purpose is to determine whether errors come from:

- Poor handwriting
- Incorrect line segmentation
- Image quality
- Cropping
- Skew
- Noise
- Text normalization
- TrOCR recognition
- Dataset characteristics

---

# 🧠 OCR Improvement Strategy

Do **not** immediately fine-tune the model.

Use this order:

```text
Existing TrOCR
      ↓
Benchmark
      ↓
Inspect Errors
      ↓
Improve Image Preprocessing
      ↓
Improve Line Segmentation
      ↓
Benchmark Again
      ↓
Test Real Exam Pages
      ↓
Benchmark Again
      ↓
Only Then Consider Fine-Tuning
```

Fine-tuning should be performed only if the existing model plus preprocessing cannot provide sufficient accuracy.

---

# 📄 Real Student Exam Dataset

The project also contains a real examination dataset.

The intended structure is:

```text
datasets/
└── exam_dataset/
    ├── Student_Pdf/
    ├── Corrected_Pdf/
    ├── AnswerKey/
    └── Question/
```

The dataset contains handwritten student answer scripts together with corrected papers and faculty evaluation information.

This dataset is especially useful for evaluating the **complete grading pipeline**.

Unlike the handwriting OCR dataset, it does not necessarily provide exact handwriting transcriptions for every answer.

Therefore:

```text
Handwriting Dataset
        ↓
OCR accuracy evaluation

Student Examination Dataset
        ↓
End-to-end evaluation / grading accuracy
```

These are two different evaluation problems.

---

# 🧩 Question Association

OCR text alone is not enough.

The system must determine:

```text
Which question does this answer belong to?
```

For example:

```text
Q21
Define Supervised Learning.

Student:
"Supervised learning is a machine learning algorithm..."
```

The pipeline should associate the recognized block with:

```text
Question 21
```

---

# 🚨 Never Guess Question Numbers

Question-marker detection follows a safety rule:

```text
Confident question marker
        ↓
Assign question
```

If the system cannot confidently identify the question:

```text
Unknown / ambiguous marker
        ↓
uncertain
        ↓
Teacher Review
```

The system must **never silently guess** the question number.

This prevents an OCR mistake from causing an answer to be evaluated against the wrong question.

---

# 🧮 Evaluation Logic

## MCQ

Example:

```text
Reference:
B

Student:
D
```

Result:

```text
0 marks
```

If:

```text
Reference:
B

Student:
b
```

Normalization allows:

```text
B == b
```

and the answer is considered correct.

---

# 📚 Descriptive Evaluation

Descriptive answers use:

```text
Student Answer
      +
Reference Answer
      +
Keywords / Rubric
      ↓
Semantic Similarity
      +
Keyword Matching
      ↓
AI Score
```

The purpose is to evaluate meaning rather than exact wording.

For example:

Reference:

```text
A type of ML where the model is trained
on labeled data with known inputs and outputs.
```

Student:

```text
Supervised learning trains a model using
data where the correct output is already known.
```

These answers use different words but communicate similar meaning.

---

# 🤝 Teacher Verification

AI evaluation is not always trusted automatically.

The system has a teacher-review stage.

```text
AI Evaluation
      │
      ▼
Confidence Check
      │
 ┌────┴─────┐
 │          │
High      Low
 │          │
 ▼          ▼
Approve   Review
            │
            ▼
       Teacher Decision
```

If a question marker is uncertain, the evaluation is forced into review.

---

# 🏆 Final Marks Rule

Teacher marks always take priority.

Conceptually:

```text
if teacher_marks exists:
    final_marks = teacher_marks
else:
    final_marks = ai_marks
```

Therefore reports should never accidentally display the old AI score after a teacher correction.

The `Evaluation.final_marks` property is used for this purpose.

---

# 📊 Reports

The platform supports report generation including:

- Student information
- Examination
- Question
- AI marks
- Final marks
- Maximum marks
- Evaluation status

Final marks are used after teacher corrections.

---

# 🖥️ Frontend

The frontend is built using:

- React 19
- Vite
- TypeScript
- TailwindCSS
- Framer Motion
- React Router
- React Hook Form
- Zod
- Axios
- Recharts
- Lucide

Major areas include:

```text
Dashboard
Subjects
Students
Faculty
Question Papers
Model Answers
Examinations
Answer Scripts
AI Evaluation
Teacher Review
Reports
Settings
```

---

# ⚡ Backend

Backend technologies:

- FastAPI
- SQLAlchemy
- PostgreSQL
- JWT authentication
- Celery
- Redis
- OpenCV
- PyTorch
- Transformers
- TrOCR
- PaddleOCR
- Sentence-Transformers
- scikit-learn

---

# 🔐 Authentication

The platform uses JWT authentication.

Roles currently include:

```text
Admin
Teacher
```

Default development account:

```text
username: admin
password: ChangeMe@123
```

Change this immediately for any real deployment.

---

# 🚀 Installation

## Requirements

Recommended:

```text
Python 3.11 / 3.12
Node.js
npm
PostgreSQL
Redis
Git
```

For local handwriting OCR:

```text
PyTorch
Transformers
Pillow
SentencePiece
TrOCR model weights
```

---

# 🐍 Backend Setup — Linux (Arch, uv)

Faster alternative using [uv](https://docs.astral.sh/uv/) (works on any Linux distro):

```bash
cd backend
uv venv venv --python 3.12          # pinned deps target Python 3.12
uv pip install --python venv/bin/python -r requirements-lite.txt pytest httpx

# AI stack (torch CPU + transformers + sentence-transformers + opencv + pymupdf):
uv pip install --python venv/bin/python torch --index-url https://download.pytorch.org/whl/cpu
uv pip install --python venv/bin/python "transformers==4.44.2" "sentence-transformers==3.1.1" "opencv-python-headless==4.10.0.84" "pymupdf==1.24.10"
```

SQLite needs no server — `backend/.env` uses `DATABASE_URL=sqlite:///./local_dev.db`.
Seed and run:

```bash
venv/bin/python -m scripts.seed_admin
venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Full end-to-end verification (48 checks incl. the real OCR pipeline) against a
running backend:

```bash
venv/bin/python scripts/smoke_test_api.py
```

Note: the checked-in `backend/venv` from a Windows machine cannot run on Linux
(the `python.exe` binaries are PE executables). Recreate the venv with the
steps above when switching OS.

---

# 🐍 Backend Setup — Windows

From the project root:

```powershell
cd backend
```

Create the virtual environment:

```powershell
python -m venv venv
```

Activate it:

```powershell
.\venv\Scripts\Activate.ps1
```

Upgrade pip:

```powershell
python -m pip install --upgrade pip
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

---

# 🧠 Important Python Environment Rule

This project may have multiple Python environments.

Always verify which Python is being used:

```powershell
python --version
```

or:

```powershell
.\backend\venv\Scripts\python.exe --version
```

For project commands, the safest approach is:

```powershell
.\backend\venv\Scripts\python.exe
```

Do not accidentally run the project using:

```text
C:\Python313\python.exe
```

if the required dependencies are installed in the project virtual environment.

---

# 🗄️ Database Setup

Configure:

```text
backend/.env
```

Example:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/answer_eval
```

Then seed the administrator:

```powershell
cd backend
python -m scripts.seed_admin
```

---

# 🔄 Existing Database Migration

If the database already existed before the TrOCR changes:

```powershell
cd backend
python -m scripts.migrate_add_trocr_columns
```

The migration is additive.

It does not intentionally delete existing examination data.

---

# ▶️ Start Backend

```powershell
cd backend
.\venv\Scripts\Activate.ps1
uvicorn main:app --reload
```

Backend:

```text
http://localhost:8000
```

API documentation:

```text
http://localhost:8000/api/docs
```

---

# 🌐 Start Frontend

Open another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:5173
```

---

# 🧰 Project Launcher

The repository contains a root-level launcher that boots the whole stack with one command — no Docker, no Postgres, no manual steps:

```powershell
python main.py              # quick start: SQLite + lite backend deps
python main.py --full-ai    # also install the OCR/NLP/ML stack (torch, transformers, ...)
python main.py --reset-db   # wipe backend/local_dev.db and reseed (refused while the backend is running)
python main.py --backend-only
python main.py --frontend-only
python main.py --help
```

What it does, in order:

1. Creates `backend/venv` with a suitable Python (3.10–3.12). It prefers `uv` (which can fetch a managed Python 3.12), falls back to `python3.12`/`python3.11`/`python3.10` on PATH, then to the interpreter running the launcher. A venv that exists but cannot run (e.g. one created on Windows and reused from Linux/WSL) is detected and rebuilt automatically.
2. Installs backend requirements — `requirements-lite.txt` by default, `requirements.txt` with `--full-ai` — but **skips pip entirely** when the key packages are already importable, so re-runs are instant.
3. Writes `backend/.env` in SQLite mode if missing, and creates `frontend/.env` pointing at the API.
4. Seeds the admin user (`admin / ChangeMe@123`, idempotent) and applies the additive schema migration (safe no-op when up to date).
5. Starts FastAPI on `:8000` and the Vite frontend on `:5173` — skipping either one if its port is already serving — and shuts both down cleanly on Ctrl+C.

Stop everything and reset to a clean slate:

```powershell
# stop the launcher with Ctrl+C, then:
python main.py --reset-db
```

> **Note:** the full-AI evaluation pipeline needs the model weights under
> `models/handwriting/trocr-base-handwritten/` — with `--full-ai` installed and
> the weights present, uploaded scanned scripts are graded by the real local
> TrOCR + semantic scoring pipeline. Without them, the core app (auth, CRUD,
> uploads, dashboards) still works and evaluation requests fail gracefully.
> Celery/Redis workers are not required and are not started by the launcher.

---

# 🐳 Docker

Docker support may be added/maintained as deployment work progresses.

The intended architecture is:

```text
Frontend
    │
    ▼
FastAPI Backend
    │
 ┌──┴─────────────┐
 ▼                ▼
PostgreSQL       Redis
                    │
                    ▼
                 Celery
                    │
                    ▼
              AI Evaluation
```

---

# 🧪 Running Tests

From the backend:

```powershell
cd backend
pytest tests/ -v
```

Tests cover areas including:

```text
Question parsing
MCQ parsing
MCQ scoring
Answer normalization
Line segmentation
Question marker detection
Uncertain question handling
Teacher mark precedence
TrOCR model loading
```

TrOCR model tests may skip when the local model weights are unavailable.

Once the model is installed, run:

```powershell
pytest tests/test_trocr_model_loading.py -v
```

---

# 🧪 Recommended Testing Workflow

Use this sequence:

## Stage 1 — Unit Tests

```powershell
cd backend
pytest tests/ -v
```

---

## Stage 2 — OCR Dataset Benchmark

```powershell
cd ..
.\backend\venv\Scripts\python.exe training\handwriting\test_trocr_dataset.py
```

---

## Stage 3 — Inspect OCR Errors

```powershell
.\backend\venv\Scripts\python.exe -c "import pandas as pd; f=r'.\datasets\handwriting\benchmark_results\trocr_test_results.csv'; df=pd.read_csv(f); print(df.sort_values('wer',ascending=False)[['sample','reference','prediction','cer','wer']].head(10).to_string(index=False))"
```

---

## Stage 4 — Real Exam Script

Run the actual evaluation pipeline against a student answer script.

Check:

```text
PDF extraction
↓
Line segmentation
↓
OCR
↓
Question association
↓
Answer extraction
↓
Scoring
↓
Confidence
↓
Teacher review
```

---

## Stage 5 — Compare Against Teacher Marks

For every question:

```text
AI Marks
Teacher Marks
Difference
```

Calculate:

```text
Average absolute error
Exact agreement
Within ±0.5 marks
Within ±1 mark
```

This is more important for the final system than OCR accuracy alone.

---

# 📈 Evaluation Metrics

The project should eventually track two separate groups of metrics.

## OCR Metrics

```text
CER
WER
Exact Match
Line Detection Accuracy
Question Marker Accuracy
```

---

## Grading Metrics

```text
Mean Absolute Error
Mean Absolute Percentage Error
Exact Mark Agreement
Within ±0.5 Marks
Within ±1 Mark
Correlation with Teacher Marks
Question-level Accuracy
Total-paper Accuracy
```

---

# 🤖 ML Confidence Model

The project contains an ML confidence component.

Initially:

```text
Teacher-reviewed evaluations < 20
        ↓
Heuristic confidence
```

After enough teacher-reviewed examples:

```text
Teacher-reviewed evaluations
        ↓
Feature extraction
        ↓
scikit-learn model
        ↓
Confidence prediction
```

The confidence model should improve as the platform accumulates verified evaluations.

---

# 🔄 Future Learning Loop

The long-term system is intended to work like:

```text
Student Answer
      ↓
AI Evaluation
      ↓
Teacher Review
      ↓
Corrected Mark
      ↓
Training Data
      ↓
Improved Confidence / Evaluation Models
      ↓
Better Future Evaluations
```

Teacher corrections are therefore valuable training data.

---

# 🗂️ Git & Large Files

Large datasets and model weights should not normally be stored directly in the Git repository.

Examples:

```text
dataset/*.parquet
*.safetensors
*.pt
*.pth
*.ckpt
```

The local model may contain:

```text
model.safetensors
```

which is approximately gigabyte-scale and should be handled separately.

The dataset files are also large:

```text
train.parquet
test.parquet
validation.parquet
```

Keep these available locally for experimentation while keeping repository history manageable.

---

# 🔒 Data Privacy

Student examination papers can contain sensitive academic information.

Production deployments should consider:

- Access control
- Secure storage
- Encryption
- Database security
- File permissions
- Audit logging
- Data retention policies
- Student anonymization
- Secure backups

The local TrOCR pipeline is designed so handwriting OCR itself does not require a cloud OCR provider.

---

# ⚠️ Current Limitations

The project is a working core platform, but several areas still require development.

## 1. OCR Accuracy

Current benchmark:

```text
CER: 7.14%
WER: 28.92%
Exact: 18%
```

Further improvement is required for highly reliable handwritten examination evaluation.

---

## 2. Line Segmentation

Current segmentation uses generic image analysis and horizontal projection.

Different handwriting styles, page layouts, ink colors, shadows, and scan quality can affect detection.

---

## 3. Question Association

Question markers that cannot be identified confidently are flagged for review.

This is intentional.

The system should prioritize correctness over guessing.

---

## 4. Descriptive Grading

Semantic similarity and keyword matching are useful but do not perfectly reproduce human marking.

Rubric-aware scoring should be improved over time.

---

## 5. Teacher Review

The current review workflow primarily supports total-mark override.

Per-question teacher mark editing can be expanded further.

---

## 6. Real-Time Progress

The backend stores evaluation status and progress information.

A more complete implementation can add:

```text
WebSocket / polling
       ↓
Live frontend progress
```

for:

```text
Uploading
Extracting pages
Segmenting lines
Running OCR
Evaluating
Generating results
```

---

# 🛣️ Development Roadmap

The recommended development order is:

```text
PHASE 1
Existing Platform
       ↓
PHASE 2
OCR Benchmark
       ↓
PHASE 3
OCR Error Analysis
       ↓
PHASE 4
Image Preprocessing Improvements
       ↓
PHASE 5
Line Segmentation Improvements
       ↓
PHASE 6
Real Student Answer Testing
       ↓
PHASE 7
Question Association Validation
       ↓
PHASE 8
End-to-End Grading Validation
       ↓
PHASE 9
Teacher Review Improvements
       ↓
PHASE 10
Evaluation Model Improvements
       ↓
PHASE 11
TrOCR Fine-Tuning if necessary
       ↓
PHASE 12
Confidence Model Training
       ↓
PHASE 13
Production Hardening
```

---

# 🎯 Immediate Next Tasks

The current priority should **not** be adding random features.

The immediate workflow is:

### 1. Analyze the current OCR benchmark

Inspect the worst 10–20 predictions.

---

### 2. Determine the source of errors

Classify errors into:

```text
Segmentation
Preprocessing
OCR
Normalization
Dataset
```

---

### 3. Improve the OCR pipeline

If segmentation is responsible for errors:

```text
Improve segmentation
```

If image quality is responsible:

```text
Improve preprocessing
```

If TrOCR itself is responsible:

```text
Consider fine-tuning
```

---

### 4. Test on actual examination pages

Use real student answer scripts.

Do not rely only on the handwriting benchmark.

---

### 5. Validate question association

Ensure:

```text
Q21 → Q21 answer
Q22 → Q22 answer
Q23 → Q23 answer
```

and never:

```text
Q21 → Q22
```

---

### 6. Validate grading

Compare:

```text
AI marks
vs.
Teacher marks
```

for the real examination dataset.

---

# 🧪 Current Project Validation Status

The current implementation has already established the following baseline:

```text
Frontend
    ✓ npm install
    ✓ TypeScript compilation
    ✓ Vite production build

Backend
    ✓ Application imports
    ✓ FastAPI application
    ✓ OpenAPI generation
    ✓ SQLAlchemy models
    ✓ Database table creation

AI
    ✓ TrOCR integration
    ✓ Local model loading
    ✓ Line segmentation
    ✓ Question marker detection
    ✓ MCQ scoring
    ✓ Descriptive scoring integration
    ✓ Confidence pipeline

OCR Benchmark
    ✓ 100 samples processed
    ✓ CER measured
    ✓ WER measured
    ✓ Exact matches measured

Testing
    ✓ Unit/integration tests
```

---

# 🧭 Development Philosophy

The project follows several important principles.

## 1. Do not hardcode examination layouts

Bad:

```text
Q1-Q20 are always MCQs
Q21-Q35 are always descriptive
```

Good:

```text
Detect question structure from the uploaded paper.
```

---

## 2. Do not assume page coordinates

Bad:

```text
Question 21 is always at x=100, y=5000
```

Good:

```text
Detect text regions dynamically.
```

---

## 3. Do not run TrOCR on entire pages

Bad:

```text
Page → TrOCR
```

Good:

```text
Page
 ↓
Line segmentation
 ↓
Line crop
 ↓
TrOCR
```

---

## 4. Do not guess uncertain questions

Bad:

```text
Probably Q21
```

Good:

```text
uncertain → teacher review
```

---

## 5. Teacher corrections always win

Bad:

```text
Report → AI marks
```

Good:

```text
Report → final_marks
```

---

## 6. Benchmark before training

Bad:

```text
Model has errors
 ↓
Immediately fine-tune
```

Good:

```text
Measure
 ↓
Analyze
 ↓
Improve preprocessing
 ↓
Measure again
 ↓
Fine-tune only if necessary
```

---

# 📚 Project Learning Path

A developer continuing this project should understand these areas in roughly this order:

```text
1. Python
2. FastAPI
3. SQLAlchemy
4. PostgreSQL
5. React + TypeScript
6. OpenCV
7. OCR
8. Transformers
9. TrOCR
10. NLP semantic similarity
11. Machine learning
12. Evaluation metrics
13. Celery + Redis
14. Production deployment
```

For the AI portion:

```text
Image
 ↓
Computer Vision
 ↓
OCR
 ↓
NLP
 ↓
Semantic Evaluation
 ↓
Scoring
 ↓
Confidence
 ↓
Human Verification
```

---

# 📌 Important Files

### OCR

```text
backend/ai/ocr/trocr_service.py
backend/ai/ocr/handwriting_segmentation.py
backend/ai/ocr/ocr_service.py
```

### Evaluation

```text
backend/services/evaluation_pipeline.py
```

### Question Parsing

```text
backend/services/document_parser.py
```

### ML Confidence

```text
backend/ai/ml/ml_service.py
```

### Database Models

```text
backend/models/exam.py
```

### OCR Benchmark

```text
training/handwriting/test_trocr_dataset.py
```

### TrOCR Model

```text
models/handwriting/trocr-base-handwritten/
```

---

# 🔗 Repository

GitHub:

```text
https://github.com/vin1397/Answer_Eval_Platform
```

---

# 📌 Current Baseline

The project should be considered to be at this point:

```text
                  CURRENT STATE
                       │
                       ▼
             Core platform working
                       │
                       ▼
              Local TrOCR integrated
                       │
                       ▼
              OCR benchmark completed
                       │
                       ▼
              7.14% average CER
              28.92% average WER
              18% exact matches
                       │
                       ▼
              Error analysis NEXT
                       │
                       ▼
             Real exam validation
                       │
                       ▼
          End-to-end grading validation
                       │
                       ▼
             Model improvement
```

---

# 🚀 Final Goal

The final system should allow a teacher to do this:

```text
1. Create Examination
        ↓
2. Upload Question Paper
        ↓
3. Questions automatically extracted
        ↓
4. Add / verify Model Answers
        ↓
5. Upload Student Answer Scripts
        ↓
6. AI scans handwritten answers
        ↓
7. AI identifies questions
        ↓
8. AI evaluates answers
        ↓
9. AI assigns marks
        ↓
10. AI calculates confidence
        ↓
11. Uncertain answers go to Teacher Review
        ↓
12. Teacher approves / corrects marks
        ↓
13. Final marks are stored
        ↓
14. Reports are generated
```

The ultimate objective is:

> **A reliable AI-assisted examination evaluation platform where handwriting recognition, question understanding, answer evaluation, automated marking, confidence estimation, and teacher verification work together as one complete system.**

---

## 🔥 Development Rule

**Do not restart the project when adding new AI capabilities.**

Continue from the existing architecture.

Improve individual stages:

```text
OCR
 ↓
Segmentation
 ↓
Question Association
 ↓
Answer Extraction
 ↓
Evaluation
 ↓
Confidence
 ↓
Teacher Review
```

Every improvement should be benchmarked against the previous version so that progress can be measured objectively.

````

### One important correction from your old README

Your pasted README still says **Docker Compose is recommended**, but your recent Git history shows:

```text
delete mode 100644 docker-compose.yml
````

