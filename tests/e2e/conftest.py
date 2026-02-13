import logging
import subprocess
import time
import pytest
import requests
from pathlib import Path

logger = logging.getLogger()


def wait_for_url(url, timeout=30):
    """Helper to wait for a local server to be responsive."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                logger.info(f"Service at {url} responded with 200 OK.")
                return True
        except requests.ConnectionError:
            time.sleep(1)
    return False


@pytest.fixture(scope="session", autouse=True)
def start_full_stack():
    # Set up paths for frontend and API directory
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent
    frontend_dir = project_root / "frontend"

    logger.info("--- Starting Full Stack Environment ---")
    logger.info("Project Root: %s", project_root)
    logger.info("Frontend Directory: %s", frontend_dir)

    processes = []

    try:
        # Start API server
        logger.info("Launching API server via pipenv...")
        api_proc = subprocess.Popen(
            [
                "pipenv",
                "run",
                "uvicorn",
                "api.main:app",
                "--host",
                "localhost",
                "--port",
                "8000",
            ],
            cwd=project_root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        processes.append(api_proc)

        if not wait_for_url("http://localhost:8000/docs"):
            logger.error("API health check failed!")
            pytest.exit("API server failed to start.")

        logger.info("Successfully launched API server")

        # Start React dev server
        logger.info("Launching React dev server via npm...")
        frontend_proc = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=frontend_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        processes.append(frontend_proc)

        if not wait_for_url("http://localhost:5173"):
            pytest.exit("React server failed to start.")

        logger.info("Successfully launched React server")

        yield  # --- TESTS RUN HERE ---

    finally:
        logger.info("--- Shutting down services ---")
        # Cleanup: Kill all processes in reverse order
        for proc in reversed(processes):
            pid = proc.pid
            logger.info(f"Terminating process with PID: {pid}")
            proc.terminate()
            try:
                proc.wait(timeout=5)
                logger.info(f"Process {pid} exited gracefully.")
            except subprocess.TimeoutExpired:
                logger.warning(f"Process {pid} did not exit. Force killing...")
                proc.kill()  # Force kill if it doesn't close gracefully
