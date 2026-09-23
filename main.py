#!/usr/bin/env python3
"""
One-command local dev runner — no Docker required.

    python main.py              # start everything (SQLite mode, quick start)
    python main.py --full-ai    # also install the OCR/NLP/ML stack (torch,
                                #  transformers, sentence-transformers, opencv,
                                #  pymupdf — several GB, needed for real AI
                                #  evaluation of scanned scripts)
    python main.py --reset-db   # delete backend/local_dev.db and reseed before starting
    python main.py --backend-only / --frontend-only
    python main.py --help

What it does:
  1. Creates backend/venv with a suitable Python (3.10–3.12; uses `uv` when
     available, falls back to python3.12/3.11 on PATH, then sys.executable)
     — and transparently rebuilds a venv that can't run (e.g. one created on
     another OS, like a Windows venv used from Linux/WSL).
  2. Installs backend requirements (lite or full-AI set) — skipped when the
     key packages are already importable.
  3. Writes backend/.env pointing at a local SQLite file (no Postgres needed).
  4. Applies the additive schema migration and seeds the admin user
     (admin / ChangeMe@123) — both idempotent.
  5. Starts FastAPI (uvicorn) on :8000 and the Vite frontend on :5173,
     skipping either one if its port is already serving.

Stop both servers with Ctrl+C.

Note: Celery/Redis workers are NOT started by this script — they aren't
required for the core app (auth, CRUD, and synchronous AI evaluation via the
"Run AI Evaluation" button all work without them).
"""
import argparse
import os
import platform
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"
VENV_DIR = BACKEND_DIR / "venv"
IS_WINDOWS = platform.system() == "Windows"

# Packages whose importability means the backend deps are installed.
LITE_MARKER_PACKAGES = ["fastapi", "uvicorn", "sqlalchemy", "slowapi", "pypdf", "openpyxl"]
FULL_AI_MARKER_PACKAGES = ["torch", "transformers", "sentence_transformers", "fitz"]


def venv_python() -> Path:
    return VENV_DIR / ("Scripts/python.exe" if IS_WINDOWS else "bin/python")


def venv_pip() -> Path:
    return VENV_DIR / ("Scripts/pip.exe" if IS_WINDOWS else "bin/pip")


def run(cmd, cwd=None, check=True, env=None):
    print(f"$ {' '.join(str(c) for c in cmd)}")
    result = subprocess.run([str(c) for c in cmd], cwd=cwd, env=env)
    if check and result.returncode != 0:
        print(f"✖ Command failed with exit code {result.returncode}")
        sys.exit(result.returncode)
    return result


def probe_python(exe: str) -> tuple[str, tuple[int, int]] | None:
    """Returns (exe, (major, minor)) if exe runs and is Python 3, else None."""
    try:
        out = subprocess.run(
            [exe, "-c", "import sys;print('%d %d' % sys.version_info[:2])"],
            capture_output=True, text=True, timeout=30,
        )
        if out.returncode == 0 and out.stdout.strip():
            major, minor = out.stdout.strip().split()[:2]
            return (exe, (int(major), int(minor)))
    except (OSError, subprocess.TimeoutExpired, ValueError):
        pass
    return None


def existing_venv_works() -> bool:
    """True if backend/venv exists AND its interpreter actually runs here.

    Catches the classic trap of a venv copied/created on another OS (e.g.
    Windows `Scripts/python.exe` while running on Linux) — those binaries
    exist but cannot execute, and silently poison every later step.
    """
    py = venv_python()
    if not py.exists():
        return False
    return probe_python(str(py)) is not None


def pick_base_interpreter() -> str:
    """Choose a host interpreter for the new venv.

    The pinned deps (numpy 1.26.x, torch 2.4.x) support Python 3.10–3.12.
    Prefer 3.12 for compatibility; avoid 3.13+/free-threaded builds.
    """
    candidates = ["python3.12", "python3.11", "python3.10"]
    if not IS_WINDOWS:
        candidates = [c for c in candidates if shutil.which(c)] + []
    for cand in candidates:
        info = probe_python(cand)
        if info and (3, 10) <= info[1] <= (3, 12):
            return cand
    # Fall back to the interpreter running this launcher, with a warning.
    major, minor = sys.version_info[:2]
    if (major, minor) > (3, 12):
        print(
            f"⚠ Running Python {major}.{minor}; the pinned backend deps target "
            f"3.10–3.12. Install python3.12 (or `uv`) for a trouble-free setup — "
            f"continuing with {sys.executable} and hoping for the best."
        )
    return sys.executable


def create_venv() -> None:
    if existing_venv_works():
        print("✔ Backend venv already exists and runs — skipping creation.")
        return
    if VENV_DIR.exists():
        print("✖ backend/venv exists but its interpreter can't run here "
              "(created on another OS?) — recreating it.")
        shutil.rmtree(VENV_DIR, ignore_errors=True)

    # `uv` is much faster and can fetch a managed CPython itself.
    if shutil.which("uv"):
        print("→ Creating backend virtual environment with uv (Python 3.12)...")
        if run(["uv", "venv", str(VENV_DIR), "--python", "3.12"], check=False).returncode == 0:
            return
        print("  uv venv failed — falling back to plain venv.")

    base = pick_base_interpreter()
    print(f"→ Creating backend virtual environment with {base}...")
    run([base, "-m", "venv", str(VENV_DIR)])


def marker_packages() -> list[str]:
    return FULL_AI_MARKER_PACKAGES if ARGS.full_ai else LITE_MARKER_PACKAGES


def deps_installed() -> bool:
    py = str(venv_python())
    probe = (
        "import importlib.util as u, sys\n"
        "mods = " + repr(marker_packages()) + "\n"
        "missing = [m for m in mods if u.find_spec(m) is None]\n"
        "print('MISSING:' + ','.join(missing)) if missing else print('OK')\n"
    )
    try:
        out = subprocess.run([py, "-c", probe], capture_output=True, text=True, timeout=120)
        ok = "OK" in out.stdout
        if not ok:
            print(f"  missing packages: {out.stdout.strip().replace('MISSING:', '')}")
        return ok
    except (OSError, subprocess.TimeoutExpired):
        return False


def install_backend_deps() -> None:
    if deps_installed():
        print("✔ Backend dependencies already installed — skipping pip.")
        return

    if shutil.which("uv"):
        req = "requirements.txt" if ARGS.full_ai else "requirements-lite.txt"
        print(f"→ Installing backend requirements with uv ({req})...")
        if run(
            ["uv", "pip", "install", "--python", str(venv_python()), "-r", str(BACKEND_DIR / req)],
            cwd=BACKEND_DIR, check=False,
        ).returncode == 0:
            return
        print("  uv install failed — falling back to pip.")

    print("→ Upgrading pip...")
    run([str(venv_pip()), "install", "--upgrade", "pip"])

    if ARGS.full_ai:
        req_file = BACKEND_DIR / "requirements.txt"
        print("→ Installing FULL requirements (torch/transformers — several GB, be patient)...")
    else:
        req_file = BACKEND_DIR / "requirements-lite.txt"
        print("→ Installing LITE requirements (no OCR/NLP heavy libs — core app only).")
        print("  Re-run later with --full-ai to enable real AI evaluation.")

    run([str(venv_pip()), "install", "-r", str(req_file)])

    # Known passlib/bcrypt incompatibility fix — pin bcrypt explicitly.
    print("→ Applying bcrypt compatibility pin (fixes 'module bcrypt has no attribute __about__')...")
    run([str(venv_pip()), "install", "bcrypt==4.0.1"])


def ensure_env_file() -> None:
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
        "OCR_ENGINE=trocr\n"
        "TROCR_MODEL_DIR=../models/handwriting/trocr-base-handwritten\n"
        "TROCR_DEVICE=auto\n"
        "SCAN_DPI=300\n"
        "SENTENCE_TRANSFORMER_MODEL=all-MiniLM-L6-v2\n"
        "ML_MODEL_DIR=./ml_models\n"
    )


def seed_admin() -> None:
    print("→ Seeding admin user (idempotent — safe to re-run)...")
    result = subprocess.run(
        [str(venv_python()), "-m", "scripts.seed_admin"],
        cwd=BACKEND_DIR,
        env=os.environ.copy(),
    )
    if result.returncode != 0:
        print("⚠ Seeding failed — see traceback above. Continuing anyway; re-run to retry.")


def run_migration() -> None:
    print("→ Applying any pending schema additions (safe no-op if up to date)...")
    result = subprocess.run(
        [str(venv_python()), "-m", "scripts.migrate_add_trocr_columns"],
        cwd=BACKEND_DIR,
        env=os.environ.copy(),
    )
    if result.returncode != 0:
        print("⚠ Migration step failed — see traceback above. Continuing anyway.")


def reset_db() -> None:
    db = BACKEND_DIR / "local_dev.db"
    if db.exists():
        print(f"→ Deleting {db} ...")
        db.unlink()
    seed_admin()


def port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def start_backend():
    print("\n→ Starting backend on http://localhost:8000  (docs: /api/docs)")
    return subprocess.Popen(
        [str(venv_python()), "-m", "uvicorn", "main:app", "--reload",
         "--host", "0.0.0.0", "--port", "8000"],
        cwd=BACKEND_DIR,
    )


def ensure_frontend_deps() -> None:
    env_path = FRONTEND_DIR / ".env"
    if not env_path.exists():
        env_path.write_text("VITE_API_BASE_URL=http://localhost:8000/api/v1\n")

    if (FRONTEND_DIR / "node_modules").exists():
        print("✔ Frontend node_modules already installed — skipping npm install.")
        return
    npm = "npm.cmd" if IS_WINDOWS else "npm"
    if shutil.which(npm) is None:
        print("✖ npm not found on PATH. Install Node.js 20+ from https://nodejs.org, then re-run.")
        sys.exit(1)
    print("→ Installing frontend dependencies (npm install)...")
    run([npm, "install"], cwd=FRONTEND_DIR)


def start_frontend():
    npm = "npm.cmd" if IS_WINDOWS else "npm"
    print("→ Starting frontend on http://localhost:5173")
    return subprocess.Popen([npm, "run", "dev"], cwd=FRONTEND_DIR)


def wait_until_healthy(url: str, timeout: float = 30.0) -> bool:
    import urllib.request
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    return True
        except OSError:
            time.sleep(0.5)
    return False


ARGS = argparse.Namespace()  # populated in main()


def main() -> None:
    global ARGS
    parser = argparse.ArgumentParser(description="Answer Eval Platform — local launcher")
    parser.add_argument("--full-ai", action="store_true",
                        help="install the full OCR/NLP/ML stack (torch, transformers, ...)")
    parser.add_argument("--reset-db", action="store_true",
                        help="delete backend/local_dev.db and reseed before starting")
    parser.add_argument("--backend-only", action="store_true", help="don't start the frontend")
    parser.add_argument("--frontend-only", action="store_true", help="don't start the backend")
    ARGS = parser.parse_args()

    print("=" * 60)
    print("Answer Eval Platform — local setup (no Docker)")
    print("=" * 60)

    if not ARGS.frontend_only:
        create_venv()
        install_backend_deps()
        ensure_env_file()
        if ARGS.reset_db:
            reset_db()
        else:
            seed_admin()
        run_migration()
        ensure_frontend_deps()

    procs = []
    backend_started = frontend_started = False
    try:
        if not ARGS.frontend_only:
            if port_in_use(8000):
                print("✔ Port 8000 already serving — assuming backend is already running.")
            else:
                procs.append(start_backend())
                backend_started = True
                if wait_until_healthy("http://127.0.0.1:8000/api/health"):
                    print("✔ Backend healthy.")
                else:
                    print("⚠ Backend did not answer /api/health within 30s — check the logs above.")

        if not ARGS.backend_only:
            if port_in_use(5173):
                print("✔ Port 5173 already serving — assuming frontend is already running.")
            else:
                procs.append(start_frontend())
                frontend_started = True

        print("\n" + "=" * 60)
        print("Backend:  http://localhost:8000/api/docs")
        print("Frontend: http://localhost:5173")
        print("Login:    admin / ChangeMe@123")
        print("Press Ctrl+C to stop." +
              ("" if (backend_started or frontend_started) else " (nothing to stop — servers were already running)"))
        print("=" * 60 + "\n")

        if procs:
            while any(p.poll() is None for p in procs):
                time.sleep(1)
                for p in procs:
                    if p.poll() is not None:
                        print(f"⚠ A child process exited with code {p.returncode}.")
        else:
            print("All services were already running — exiting.")
    except KeyboardInterrupt:
        print("\nStopping servers...")
    finally:
        for p in procs:
            if p.poll() is None:
                p.terminate()
        for p in procs:
            try:
                p.wait(timeout=10)
            except subprocess.TimeoutExpired:
                p.kill()
        print("Done.")


if __name__ == "__main__":
    main()
