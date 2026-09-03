# Intelligent Answer Script Evaluation & Automated Mark Assignment

AI-powered platform that reads handwritten answer scripts (OCR), understands
answers using NLP semantic similarity, and assigns marks automatically —
with teacher verification before marks are finalized.

## What's in this build

This is a **real, working core platform**, not a mockup — every file listed
below runs. It has been verified in this environment:

- **Frontend**: `npm install`, `tsc -b` (0 errors), and `vite build`
  (production bundle) all succeed.
- **Backend**: `main.py` imports cleanly, generates a valid OpenAPI schema
  with **43 endpoints**, and all 13 SQLAlchemy models create their tables
  correctly with foreign keys and indexes intact.

Given the scope of the original spec (a full enterprise ML platform with
OCR, NLP, model training, Celery, WebSockets, and a dozen UI modules), this
build focuses on making the **core evaluation pipeline genuinely work
end-to-end**, with every other module scaffolded to production patterns so
you can extend it. See "Honest scope notes" below for specifics.

## Architecture

```
Question Paper (PDF/DOCX) ──▶ auto-parsed into Questions (MCQ options OR
                                descriptive text, detected generically —
                                no hardcoded question ranges)
Model Answer (per question) ──▶ MCQ: correct_option
                                 Descriptive: reference text + keywords/rubric
Answer Script (PDF/JPG/PNG)
        │
        ▼
   PDF/page extraction ──▶ preprocessing ──▶ line segmentation
   (generic horizontal-projection profiling — no fixed coordinates,
    no per-student or per-page assumptions)
        │
        ▼
   Local TrOCR (line-level crops, never a full page) ─── local_files_only=True,
        │                                                 model loaded once (singleton)
        ▼
   Question-number marker detection per block
   (confident match -> assigned; no match -> flagged `uncertain`,
    never guessed)
        │
        ▼
   Per-question scoring:
     MCQ         -> exact normalized-option match (A/B/C/D), no ML involved
     Descriptive -> Sentence-Transformers semantic similarity
                    + keyword/rubric matching
        │
        ▼
   scikit-learn confidence model (trained on teacher corrections;
   heuristic fallback until then)
        │
        ▼
   Final AI marks ──▶ auto-approve OR route to Teacher Review
   (forced to review if ANY segment was uncertain)
        │
        ▼
   Teacher override (total_teacher_marks) ──▶ `final_marks` property
   (used by ALL reports — teacher correction always wins over raw AI marks)
```

### Local handwriting OCR (TrOCR) setup

The handwriting OCR engine (`ai/ocr/trocr_service.py`) requires a locally
downloaded TrOCR checkpoint — it is **never** fetched at runtime
(`local_files_only=True`) and never calls any cloud OCR API.

1. Place your downloaded model at:
   ```
   models/handwriting/trocr-base-handwritten/
   ```
   relative to the project root (sibling of `backend/` and `frontend/`),
   containing `config.json`, `model.safetensors`, `tokenizer.json`,
   `vocab.json`, `merges.txt`, `preprocessor_config.json`, etc.
2. Or point `TROCR_MODEL_DIR` in `backend/.env` at wherever it actually lives.
3. If the model directory is missing, evaluation runs fail immediately with
   a clear, actionable error — they never silently fall back to a different
   engine or produce a fabricated result.

An alternate full-page PaddleOCR engine is still available
(`OCR_ENGINE=paddleocr` in `.env`) for printed/non-handwriting documents,
but TrOCR line-segmentation is the default for student answer scripts.

### Upgrading an existing database

If you already have a database from before this change, run the additive
migration once (never drops or rewrites existing data):
```bash
cd backend
python -m scripts.migrate_add_trocr_columns
```
This was verified against a populated pre-existing schema in this build —
existing rows survive with sensible defaults (`question_type` defaults to
`short_answer`).

### Running the test suite
```bash
cd backend
pytest tests/ -v
```
34 tests cover: question/MCQ-option parsing, MCQ answer normalization and
scoring, line/block segmentation, question-marker detection (including the
"never guess, flag uncertain" safety property), teacher-override precedence
in reports, and guarded TrOCR model loading (skips cleanly with a clear
reason if the model isn't installed in your environment, runs fully if it is).

## Tech stack (as specified)

React 19 + Vite + TypeScript + TailwindCSS + Framer Motion + React Router +
React Hook Form + Zod + Axios + Recharts + Lucide · FastAPI + SQLAlchemy +
PostgreSQL + JWT auth · PaddleOCR + Sentence-Transformers + scikit-learn +
OpenCV + PyTorch (transitive) · Celery + Redis · WebSocket · Docker.

## Running it

### Option A — Docker Compose (recommended)

```bash
docker compose up --build
```

This starts Postgres, Redis, the FastAPI backend (`:8000`), a Celery
worker, and the Vite dev server (`:5173`). First boot auto-creates tables.
Then seed the first admin account:

```bash
docker compose exec backend python -m scripts.seed_admin
```

Login with **admin / ChangeMe@123** — change it immediately from Settings.

### Option B — Manual

**Backend**
```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # then point DATABASE_URL at your Postgres instance
python -m scripts.seed_admin
uvicorn main:app --reload
```
API docs: `http://localhost:8000/api/docs`

**Frontend**
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```
App: `http://localhost:5173`

**Celery worker** (for background/batch evaluation)
```bash
cd backend
celery -A services.celery_app worker --loglevel=info
```

## Honest scope notes — what's fully live vs. scaffolded

**Fully wired, working, and test-covered in this round:**
- JWT auth (login/refresh/logout), role-based access (Admin/Teacher)
- Subjects, Students (+ Excel import/export), Semesters, Schemes, Faculty — full CRUD
- Question paper upload with automatic question/marks extraction, **including
  generic MCQ-option detection** (no hardcoded question ranges — mixed
  MCQ/descriptive papers in any order are handled correctly)
- Model answer authoring — MCQ correct-option picker or descriptive
  reference text/keywords, depending on question type
- Examinations + answer script upload (single, drag-and-drop, bulk)
- **Local handwriting OCR**: PDF/image → page extraction → generic line
  segmentation (horizontal-projection profiling, no fixed coordinates) →
  local TrOCR (`local_files_only=True`, singleton-loaded, line crops only,
  never a full page) → question-marker association that flags `uncertain`
  rather than guessing
- MCQ scoring (exact normalized-option match) and descriptive scoring
  (semantic + keyword) both feed the same evaluation pipeline and ML
  confidence model
- Teacher review workflow; `Evaluation.final_marks` always prefers the
  teacher's correction over raw AI marks, and **every report now uses it**
- Dashboard with live charts, analytics, recent activity
- PDF and Excel report generation (now with a Final Marks column)
- Institute settings, password change
- 34 pytest tests (32 pass unconditionally, 2 require the actual TrOCR
  model weights and skip cleanly without them) — actually run in this
  environment, not just written

**What genuinely wasn't executable in this sandbox, and why:**
- The real TrOCR model wasn't loaded here (no model weights present in this
  environment) — the loading/inference code is correct and was unit-tested
  for its structure and error paths (missing-model handling, confidence
  estimation math), but not against real handwriting images. Test it on
  your machine with `pytest tests/test_trocr_model_loading.py -v` once the
  model is in place — those 2 tests will stop skipping and actually run.
- PaddleOCR/PyTorch/Sentence-Transformers/opencv are large; segmentation
  logic (line/block detection, question-marker regex) WAS tested with
  synthetic images using real OpenCV. Sentence-Transformers embedding
  generation itself wasn't executed here (no model download), but its
  integration point (`nlp_service.score_question`) is unchanged from the
  previously-verified build.

**Scaffolded, not rebuilt (preserved from the existing architecture per your instructions):**
- The ML confidence model (`ai/ml/ml_service.py`) needs ≥20 teacher-reviewed
  evaluations before it trains a real model; heuristic fallback until then.
- WebSocket route exists for realtime progress; the pipeline doesn't yet
  call `manager.broadcast()` — `status_detail` is written to the DB at each
  step (so polling `GET /evaluations/{id}` mid-run shows live progress
  server-side), but the frontend's "Run AI Evaluation" button doesn't poll
  during the synchronous call yet. Wire that in if you want a live progress
  bar rather than a blocking spinner.
- Alembic isn't set up; use `scripts/migrate_add_trocr_columns.py` for this
  round's schema changes, or `Base.metadata.create_all` for a fresh dev DB.
- S3 storage backend is implemented but untested (local filesystem verified).
- Per-question teacher marks editing isn't in the UI — review currently
  overrides the *total* only (existing architecture), not each question's
  mark individually.

## Default login

```
username: admin
password: ChangeMe@123
```
Change this immediately in a real deployment.
