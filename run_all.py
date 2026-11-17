"""Lance les 3 microservices, le registry et le catalog. Ctrl+C pour tout arrêter."""
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent

SERVICES = [
    ("backend/merchandising", ["-m", "uvicorn", "app.main:app", "--port", "8001"]),
    ("backend/fulfillment", ["-m", "uvicorn", "app.main:app", "--port", "8002"]),
    ("backend/customer_finance", ["-m", "uvicorn", "app.main:app", "--port", "8003"]),
    ("governance", ["-m", "uvicorn", "registry_api:app", "--port", "8000"]),
    ("catalog", ["manage.py", "runserver", "8080", "--noreload"]),
]

if __name__ == "__main__":
    procs = [
        subprocess.Popen([sys.executable, *args], cwd=ROOT_DIR / folder)
        for folder, args in SERVICES
    ]
    print("Catalog : http://localhost:8080   Registry : http://localhost:8000/docs")
    try:
        for p in procs:
            p.wait()
    except KeyboardInterrupt:
        for p in procs:
            p.terminate()
