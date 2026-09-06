import os
import sys
import secrets
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
ENV_FILE = PROJECT_ROOT / ".env"


def create_env_file():
    """Create .env automatically if it does not exist."""

    if ENV_FILE.exists():
        print("[OK] .env file found.")
        return True

    print("[INFO] .env file not found.")
    print("[INFO] Creating .env file...")

    # Generate a fresh random secret for THIS install, rather than a
    # fixed string baked into the script. A hardcoded literal here would
    # mean every teammate's first-run .env gets the identical secret —
    # anyone reading this file's source could forge valid JWTs for any
    # deployment created from it. token_urlsafe(64) gives ~512 bits of
    # entropy, generated fresh each time create_env_file() actually runs.
    jwt_secret = secrets.token_urlsafe(64)

    env_content = f"""# AIIA CTMS Environment Configuration

# Supabase PostgreSQL connection string
DATABASE_URL=YOUR_SUPABASE_DATABASE_URL_HERE

# JWT secret key (randomly generated for this install — do not share
# or commit this value; each clone/environment should have its own)
JWT_SECRET_KEY={jwt_secret}
"""

    ENV_FILE.write_text(env_content, encoding="utf-8")

    print(f"[OK] Created: {ENV_FILE}")
    print()
    print("[ACTION REQUIRED]")
    print("Open .env and replace:")
    print("DATABASE_URL=YOUR_SUPABASE_DATABASE_URL_HERE")
    print("with your actual Supabase PostgreSQL connection string.")
    print()

    return False


def main():
    print()
    print("=" * 50)
    print("       AIIA CTMS BACKEND")
    print("=" * 50)
    print()

    # -------------------------------------------------
    # Step 1: Create .env automatically
    # -------------------------------------------------
    if not create_env_file():
        print("[STOP] Backend will not start until DATABASE_URL is configured.")
        print()
        input("Press Enter to exit...")
        return

    # -------------------------------------------------
    # Step 2: Check dependencies
    # -------------------------------------------------
    from app.dependency_check import ensure_requirements

    print("Dependency Check")
    print("-" * 50)

    if not ensure_requirements():
        print()
        print("[ERROR] Dependency installation/check failed.")
        input("Press Enter to exit...")
        return

    print()
    print("Starting FastAPI backend...")
    print("API: http://127.0.0.1:8000")
    print("Swagger: http://127.0.0.1:8000/docs")
    print("Press CTRL+C to stop the server.")
    print()

    # -------------------------------------------------
    # Step 3: Start FastAPI
    # -------------------------------------------------
    subprocess.run(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--reload",
            "--app-dir",
            str(PROJECT_ROOT),
        ],
        cwd=str(PROJECT_ROOT),
        check=True,
    )


if __name__ == "__main__":
    main()