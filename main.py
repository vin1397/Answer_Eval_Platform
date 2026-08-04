#!/usr/bin/env python3
"""
One-command local dev runner — no Docker required.

What it does:
  1. Creates a Python venv inside backend/venv (if missing)
  2. Installs backend requirements (with the bcrypt pin fix applied)
  3. Writes backend/.env pointing at a local SQLite file (no Postgres needed)
  4. Seeds the admin user (admin / ChangeMe@123)
  5. Starts the FastAPI backend (uvicorn) on :8000
  6. Runs `npm install` (first time only) and starts the Vite frontend on :5173

Usage:
    python run_local.py            # SQLite mode, quick start
    python run_local.py --full-ai  # also installs PaddleOCR/torch/sentence-transformers
                                    # (large download, needed for real OCR/NLP evaluation)

Stop both servers with Ctrl+C.

Note: Celery/Redis/WebSocket-broadcast features are NOT started by this
script — they aren't required for the core app (auth, CRUD, sync AI
evaluation via the "Run AI Evaluation" button all work without them).
"""
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"
VENV_DIR = BACKEND_DIR / "venv"
IS_WINDOWS = platform.system() == "Windows"

VENV_PYTHON = VENV_DIR / ("Scripts/python.exe" if IS_WINDOWS else "bin/python")
VENV_PIP = VENV_DIR / ("Scripts/pip.exe" if IS_WINDOWS else "bin/pip")

FULL_AI = "--full-ai" in sys.argv


def run(cmd, cwd=None, check=True):
    print(f"\n$ {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(cmd, cwd=cwd)
    if check and result.returncode != 0:
        print(f"Command failed with exit code {result.returncode}")
        sys.exit(result.returncode)
    return result


def ensure_venv():
    if VENV_PYTHON.exists():
        print("✔ Backend venv already exists — skipping creation.")
        return
    print("→ Creating backend virtual environment...")
    run([sys.executable, "-m", "venv", str(VENV_DIR)])


def install_backend_deps():
    print("→ Upgrading pip...")
    run([str(VENV_PIP), "install", "--upgrade", "pip"])

    if FULL_AI:
        req_file = BACKEND_DIR / "requirements.txt"
        print("→ Installing FULL requirements (this includes PaddleOCR/torch — several GB, can take a while)...")
    else:
        req_file = BACKEND_DIR / "requirements-lite.txt"
        print("→ Installing LITE requirements (no OCR/NLP/ML heavy libs — core app only).")
        print("  Run with --full-ai later to enable real AI evaluation.")

    run([str(VENV_PIP), "install", "-r", str(req_file)])

    # Known passlib/bcrypt incompatibility fix — pin bcrypt explicitly.
    print("→ Applying bcrypt compatibility pin (fixes 'module bcrypt has no attribute __about__')...")
    run([str(VENV_PIP), "install", "bcrypt==4.0.1"])


def ensure_env_file():
    env_path = BACKEND_DIR / ".env"
    if env_path.exists():
        print("✔ backend/.env already exists — leaving it as-is.")
        return

    print("→ Writing backend/.env (SQLite mode, no Postgres required)...")
    env_path.write_text(
        "APP_ENV=development\n"
        "DEBUG=true\n"
        "SECRET_KEY=dev-only-secret-change-in-production\n"
        "DATABASE_URL=sqlite:///./local_dev.db\n"
        'CORS_ORIGINS=["http://localhost:5173"]\n'
        "STORAGE_BACKEND=local\n"
        "LOCAL_STORAGE_PATH=./storage\n"
        "SENTENCE_TRANSFORMER_MODEL=all-MiniLM-L6-v2\n"
        "ML_MODEL_DIR=./ml_models\n"
    )


def seed_admin():
    print("→ Seeding admin user (idempotent — safe to re-run)...")
    env = os.environ.copy()
    result = subprocess.run(
        [str(VENV_PYTHON), "-m", "scripts.seed_admin"],
        cwd=BACKEND_DIR,
        env=env,
    )
    if result.returncode != 0:
        print("Seeding failed — see traceback above. Continuing anyway; you can re-run this script.")


def start_backend():
    print("\n→ Starting backend on http://localhost:8000  (docs: /api/docs)")
    return subprocess.Popen(
        [str(VENV_PYTHON), "-m", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
        cwd=BACKEND_DIR,
    )


def ensure_frontend_deps():
    if (FRONTEND_DIR / "node_modules").exists():
        print("✔ Frontend node_modules already installed — skipping.")
        return
    npm = "npm.cmd" if IS_WINDOWS else "npm"
    if shutil.which(npm) is None:
        print("✖ npm not found on PATH. Install Node.js 20+ from https://nodejs.org, then re-run this script.")
        sys.exit(1)
    print("→ Installing frontend dependencies (npm install)...")
    run([npm, "install"], cwd=FRONTEND_DIR)

    env_path = FRONTEND_DIR / ".env"
    if not env_path.exists():
        env_path.write_text("VITE_API_BASE_URL=http://localhost:8000/api/v1\n")


def start_frontend():
    npm = "npm.cmd" if IS_WINDOWS else "npm"
    print("→ Starting frontend on http://localhost:5173")
    return subprocess.Popen([npm, "run", "dev"], cwd=FRONTEND_DIR)


def main():
    print("=" * 60)
    print("Answer Eval Platform — local setup (no Docker)")
    print("=" * 60)

    ensure_venv()
    install_backend_deps()
    ensure_env_file()
    seed_admin()
    ensure_frontend_deps()

    backend_proc = start_backend()
    time.sleep(2)  # give uvicorn a head start before the frontend hits it
    frontend_proc = start_frontend()

    print("\n" + "=" * 60)
    print("Backend:  http://localhost:8000/api/docs")
    print("Frontend: http://localhost:5173")
    print("Login:    admin / ChangeMe@123")
    print("Press Ctrl+C to stop both servers.")
    print("=" * 60 + "\n")

    try:
        backend_proc.wait()
        frontend_proc.wait()
    except KeyboardInterrupt:
        print("\nStopping servers...")
        backend_proc.terminate()
        frontend_proc.terminate()


if __name__ == "__main__":
    main()
