import argparse
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path


def load_env(env_path: Path) -> None:
    """
    Load environment variables from a file if it exists.

    We prefer `python-dotenv` because it matches how your Django settings load `.env`,
    but fall back to a minimal parser if the dependency isn't available at build time.
    """
    if not env_path.exists():
        return

    try:
        from dotenv import load_dotenv  # type: ignore

        load_dotenv(dotenv_path=str(env_path), override=True)
        return
    except Exception:
        pass

    # Minimal fallback: KEY=VALUE lines, ignores comments/blank lines.
    for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ[key] = value


def _log(message: str) -> None:
    print(message, flush=True)


def _relay_output(prefix: str, proc: subprocess.Popen) -> None:
    if not proc.stdout:
        return
    try:
        for line in proc.stdout:
            _log(f"[{prefix}] {line.rstrip()}")
    except Exception:
        pass


def _ensure_frontend_dependencies(frontend_dir: Path, npm_cmd: str) -> bool:
    """
    Ensure GRC frontend has local CLI binaries available.
    """
    vue_cli_bin = frontend_dir / "node_modules" / ".bin" / ("vue-cli-service.cmd" if os.name == "nt" else "vue-cli-service")
    if vue_cli_bin.exists():
        return True

    _log("[onprem_launcher] Missing vue-cli-service in grc_frontend/node_modules. Running npm install...")
    try:
        install_proc = subprocess.Popen(
            [npm_cmd, "install"],
            cwd=str(frontend_dir),
            env=os.environ.copy(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        _relay_output("frontend-install", install_proc)
        code = install_proc.wait()
        if code != 0:
            _log(f"[onprem_launcher] npm install failed with exit code {code}.")
            return False
    except Exception as exc:
        _log(f"[onprem_launcher] Failed to run npm install: {exc}")
        return False

    return vue_cli_bin.exists()


def _terminate_process(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    if os.name == "nt":
        # Ensure full subprocess trees (npm/node) are terminated on Windows.
        subprocess.run(
            ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return
    try:
        proc.terminate()
        proc.wait(timeout=10)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def main() -> int:
    parser = argparse.ArgumentParser(description="On-prem launcher for GRC frontend + backend dev stack")
    parser.add_argument("--host", default=os.environ.get("HOST", "0.0.0.0"))
    parser.add_argument("--port", default=os.environ.get("PORT", "8000"))
    parser.add_argument(
        "--env",
        default=os.environ.get("ENV_FILE", ".env"),
        help="Env file name/path (default: .env)",
    )
    args = parser.parse_args()

    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        candidates = [
            (exe_dir / "_internal" / "grc_backend", exe_dir / "_internal" / "grc_frontend"),
            (exe_dir / "grc_backend", exe_dir / "grc_frontend"),
        ]
        backend_dir, frontend_dir = next(
            ((b, f) for (b, f) in candidates if b.exists() and f.exists()),
            (exe_dir / "_internal" / "grc_backend", exe_dir / "_internal" / "grc_frontend"),
        )
    else:
        backend_dir = Path(__file__).resolve().parent  # grc_backend/
        frontend_dir = backend_dir.parent / "grc_frontend"

    # Load env (so SECRET_KEY/DB creds are present before Django settings import).
    # Priority:
    # 1) explicit --env absolute path
    # 2) external working directory: ./grc_backend/<env>
    # 3) packaged backend dir: <backend_dir>/<env>
    # 4) fallback names in both locations
    env_candidates: list[Path] = []
    requested = Path(args.env)
    if requested.is_absolute():
        env_candidates.append(requested)
    else:
        env_candidates.extend(
            [
                Path.cwd() / "grc_backend" / requested,
                backend_dir / requested,
                Path.cwd() / "grc_backend" / ".env",
                Path.cwd() / "grc_backend" / ".env.production",
                backend_dir / ".env",
                backend_dir / ".env.production",
            ]
        )

    loaded_env = None
    for candidate in env_candidates:
        if candidate.exists():
            load_env(candidate)
            loaded_env = candidate
            break

    if loaded_env:
        _log(f"[onprem_launcher] Loaded env from: {loaded_env}")
    else:
        _log("[onprem_launcher] No env file found in expected locations. Using process environment only.")

    # Your backend/settings.py hard-requires these keys.
    os.environ.setdefault("SESSION_TIMEOUT_ENABLED", "true")
    os.environ.setdefault("SESSION_TIMEOUT_SECONDS", os.environ.get("SESSION_TIMEOUT_SECONDS", "3600"))
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

    if not (backend_dir / "manage.py").exists():
        _log(f"[onprem_launcher] backend manage.py not found in: {backend_dir}")
        return 1
    if not frontend_dir.exists():
        _log(f"[onprem_launcher] grc_frontend folder not found in: {frontend_dir}")
        return 1

    # Use system python exactly like your manual command: `python manage.py runserver`.
    # In a frozen EXE, `sys.executable` points to the EXE itself (not desired here).
    python_cmd = os.environ.get("PYTHON_CMD", "python")
    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"

    backend_cmd = [python_cmd, "manage.py", "runserver", f"{args.host}:{args.port}", "--noreload"]
    frontend_grc_cmd = [npm_cmd, "run", "serve"]
    frontend_tprm_cmd = [npm_cmd, "--prefix", "./tprm_frontend", "run", "dev"]

    _log(f"[onprem_launcher] backend_dir={backend_dir}")
    _log(f"[onprem_launcher] frontend_dir={frontend_dir}")
    _log(f"[onprem_launcher] Starting backend: {' '.join(backend_cmd)}")
    _log(f"[onprem_launcher] Starting frontend (GRC): {' '.join(frontend_grc_cmd)}")
    _log(f"[onprem_launcher] Starting frontend (TPRM): {' '.join(frontend_tprm_cmd)}")

    if not _ensure_frontend_dependencies(frontend_dir, npm_cmd):
        _log("[onprem_launcher] GRC frontend dependencies are not ready. Aborting startup.")
        return 1

    procs: list[subprocess.Popen] = []
    try:
        backend_proc = subprocess.Popen(
            backend_cmd,
            cwd=str(backend_dir),
            env=os.environ.copy(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        procs.append(backend_proc)
        frontend_grc_proc = subprocess.Popen(
            frontend_grc_cmd,
            cwd=str(frontend_dir),
            env=os.environ.copy(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        procs.append(frontend_grc_proc)
        frontend_tprm_proc = subprocess.Popen(
            frontend_tprm_cmd,
            cwd=str(frontend_dir),
            env=os.environ.copy(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        procs.append(frontend_tprm_proc)
    except Exception as exc:
        _log(f"[onprem_launcher] Failed to start processes: {exc}")
        for p in procs:
            _terminate_process(p)
        return 1

    threading.Thread(target=_relay_output, args=("backend", backend_proc), daemon=True).start()
    threading.Thread(target=_relay_output, args=("frontend-grc", frontend_grc_proc), daemon=True).start()
    threading.Thread(target=_relay_output, args=("frontend-tprm", frontend_tprm_proc), daemon=True).start()

    def _shutdown(_signum=None, _frame=None):
        _log("[onprem_launcher] Shutting down frontend/backend...")
        for p in procs:
            _terminate_process(p)

    signal.signal(signal.SIGINT, _shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _shutdown)

    exit_code = 0
    try:
        while True:
            if backend_proc.poll() is not None:
                exit_code = backend_proc.returncode or 0
                _log(f"[onprem_launcher] Backend exited with code {exit_code}.")
                break
            if frontend_grc_proc.poll() is not None:
                exit_code = frontend_grc_proc.returncode or 0
                _log(f"[onprem_launcher] Frontend (GRC) exited with code {exit_code}.")
                break
            if frontend_tprm_proc.poll() is not None:
                exit_code = frontend_tprm_proc.returncode or 0
                _log(f"[onprem_launcher] Frontend (TPRM) exited with code {exit_code}.")
                break
            time.sleep(1)
    finally:
        _shutdown()

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

