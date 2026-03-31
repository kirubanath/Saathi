"""Saathi CLI — single command to launch the full demo.

Usage:
    python cli.py demo          # start MinIO + FastAPI + seed + Streamlit
    python cli.py seed          # seed DB + preprocess into MinIO (MinIO must be running)
    python cli.py reset         # reset DB + re-preprocess

If installed via pip install -e .:
    saathi demo
    saathi seed
    saathi reset
"""

import os
import signal
import socket
import subprocess
import sys
import time

import click

def _resolve_project_root() -> str:
    """Walk up from cwd to find the directory containing pyproject.toml."""
    path = os.getcwd()
    while True:
        if os.path.isfile(os.path.join(path, "pyproject.toml")):
            return path
        parent = os.path.dirname(path)
        if parent == path:
            break
        path = parent
    return os.getcwd()


PROJECT_ROOT = _resolve_project_root()
DOCKER_COMPOSE = os.path.join(PROJECT_ROOT, "docker-compose.yml")

DEFAULT_API_PORT = 8000
DEFAULT_STREAMLIT_PORT = 8501
PORT_SCAN_RANGE = 20


def _find_free_port(start: int, max_attempts: int = PORT_SCAN_RANGE) -> int:
    """Return the first available port starting from *start*."""
    for offset in range(max_attempts):
        port = start + offset
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("0.0.0.0", port))
                return port
        except OSError:
            continue
    raise click.ClickException(
        f"No free port found in range {start}–{start + max_attempts - 1}"
    )


def _minio_is_running() -> bool:
    try:
        result = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Running}}", "saathi-minio"],
            capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip() == "true"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _docker_available() -> bool:
    try:
        subprocess.run(["docker", "version"], capture_output=True, timeout=5)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _wait_for_minio(max_wait: int = 30):
    click.echo("  Waiting for MinIO to be ready...", nl=False)
    for _ in range(max_wait):
        try:
            with socket.create_connection(("localhost", 9000), timeout=1):
                click.echo(" ready.")
                return
        except OSError:
            click.echo(".", nl=False)
            time.sleep(1)
    click.echo(" timeout!")
    click.secho("  MinIO did not become ready. Check docker logs saathi-minio", fg="yellow")


def _wait_for_fastapi(port: int = DEFAULT_API_PORT, max_wait: int = 15):
    import httpx
    click.echo("  Waiting for FastAPI to be ready...", nl=False)
    for _ in range(max_wait):
        try:
            resp = httpx.get(f"http://localhost:{port}/health", timeout=1)
            if resp.status_code == 200:
                click.echo(" ready.")
                return
        except (httpx.ConnectError, httpx.TimeoutException):
            pass
        click.echo(".", nl=False)
        time.sleep(1)
    click.echo(" timeout!")
    click.secho("  FastAPI did not become ready.", fg="yellow")


def _ensure_minio():
    if _minio_is_running():
        click.echo("  MinIO container already running.")
        return

    if not _docker_available():
        click.secho("Error: docker is not available. MinIO requires Docker.", fg="red")
        click.echo("Install Docker: https://docs.docker.com/get-docker/")
        sys.exit(1)

    click.echo("  Starting MinIO via docker compose...")
    subprocess.run(
        ["docker", "compose", "-f", DOCKER_COMPOSE, "up", "-d"],
        cwd=PROJECT_ROOT, check=True,
    )
    _wait_for_minio()


def _ensure_seeded():
    seed_db_path = os.path.join(PROJECT_ROOT, "saathi_seed.db")
    live_db_path = os.path.join(PROJECT_ROOT, "saathi.db")

    if os.path.exists(seed_db_path) and os.path.exists(live_db_path):
        click.echo("  Seed database exists — skipping DB seed.")
    else:
        click.echo("  Running initial DB seed...")
        _seed_db_only()

    click.echo("  Checking MinIO artifacts...")
    _ensure_preprocessed()


def _seed_db_only():
    from data.seed_db import seed as seed_db
    seed_db()


def _ensure_preprocessed(force: bool = False):
    from preprocessing.pipeline import preprocess_all
    results = preprocess_all(force=force)
    if results:
        click.echo(f"  Preprocessed {len(results)} video(s).")
    else:
        click.echo("  All artifacts already exist — nothing to preprocess.")


@click.group()
def cli():
    """Saathi — AI learning companion demo."""
    pass


@cli.command()
def demo():
    """Start MinIO, FastAPI, and launch the Streamlit demo."""
    click.secho("Saathi Demo", fg="cyan", bold=True)
    click.echo()

    click.echo("[1/4] MinIO")
    _ensure_minio()

    click.echo("[2/4] Database & artifacts")
    _ensure_seeded()

    click.echo("[3/4] FastAPI server")
    api_port = _find_free_port(DEFAULT_API_PORT)
    if api_port != DEFAULT_API_PORT:
        click.secho(f"  Port {DEFAULT_API_PORT} in use — using {api_port}", fg="yellow")
    click.echo(f"  Starting FastAPI at http://localhost:{api_port}")
    fastapi_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.app:app",
         "--host", "0.0.0.0", "--port", str(api_port),
         "--log-level", "warning"],
        cwd=PROJECT_ROOT,
        start_new_session=True,
    )
    _wait_for_fastapi(port=api_port)

    click.echo("[4/4] Streamlit")
    st_port = _find_free_port(DEFAULT_STREAMLIT_PORT)
    if st_port != DEFAULT_STREAMLIT_PORT:
        click.secho(f"  Port {DEFAULT_STREAMLIT_PORT} in use — using {st_port}", fg="yellow")
    click.echo(f"  Launching demo...")

    st_env = os.environ.copy()
    st_env["SAATHI_API_URL"] = f"http://localhost:{api_port}"
    streamlit_proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run",
         os.path.join(PROJECT_ROOT, "demo", "app.py"),
         "--server.headless", "true",
         "--server.port", str(st_port),
         "--browser.gatherUsageStats", "false"],
        cwd=PROJECT_ROOT,
        env=st_env,
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    click.echo(f"  Demo running at http://localhost:{st_port}")
    click.echo("  Press Ctrl+C to stop.\n")

    def _kill_proc(proc):
        """Kill entire process group immediately."""
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except (ProcessLookupError, OSError):
            pass
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            pass

    def _shutdown(sig, frame):
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        click.echo("\nShutting down...")
        _kill_proc(streamlit_proc)
        _kill_proc(fastapi_proc)
        click.echo("Done.")
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    streamlit_proc.wait()
    _kill_proc(fastapi_proc, "FastAPI")


@cli.command()
@click.option("--force-preprocess", is_flag=True, help="Re-run preprocessing even if artifacts exist in MinIO.")
def seed(force_preprocess):
    """Seed the database and preprocess all aspiration videos.

    MinIO must be running (use `saathi demo` or `docker compose up -d`).
    Skips preprocessing for videos whose artifacts already exist unless --force-preprocess is given.
    """
    click.secho("Seeding Saathi", fg="cyan", bold=True)
    _seed_db_only()
    _ensure_preprocessed(force=force_preprocess)
    click.echo("Seed complete.")


@cli.command()
@click.option("--force-preprocess", is_flag=True, help="Re-run preprocessing even if artifacts exist in MinIO.")
def reset(force_preprocess):
    """Reset DB to seed state and re-run preprocessing.

    MinIO must be running.
    """
    click.secho("Resetting Saathi", fg="cyan", bold=True)
    from data.reset_db import reset as reset_db
    reset_db()
    _ensure_preprocessed(force=force_preprocess)
    click.echo("Reset complete.")


if __name__ == "__main__":
    cli()
