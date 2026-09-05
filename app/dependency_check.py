
"""
AIIA CTMS - Dependency Checker

Checks requirements.txt before the backend starts.
If packages are missing, they are installed automatically.
The checker then verifies everything again.

requirements.txt is the single source of truth.
"""

import importlib
import re
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
REQUIREMENTS_FILE = PROJECT_ROOT / "requirements.txt"


def get_package_name(requirement: str) -> str | None:
    """
    Extract the package name from a requirements.txt line.

    Handles examples such as:
        fastapi
        fastapi==0.116.1
        sqlalchemy>=2.0
        passlib[bcrypt]
        python-jose[cryptography]
    """

    requirement = requirement.strip()

    # Ignore empty lines and comments
    if not requirement or requirement.startswith("#"):
        return None

    # Ignore options such as --extra-index-url
    if requirement.startswith("-"):
        return None

    # Remove environment markers
    requirement = requirement.split(";", 1)[0].strip()

    # Extract package name
    match = re.match(r"^([A-Za-z0-9_.-]+)", requirement)

    if not match:
        return None

    return match.group(1)


def get_import_name(package_name: str) -> str:
    """
    Convert common PyPI package names to import names.

    Most packages use the same name, but some don't.
    """

    import_names = {
    "psycopg2-binary": "psycopg2",
    "python-dotenv": "dotenv",
    "python-jose": "jose",
    "email-validator": "email_validator",
    "dnspython": "dns",
    "pyyaml": "yaml",
    "sqlalchemy": "sqlalchemy",
    "pyjwt": "jwt",
    "beautifulsoup4": "bs4",
    "scikit-learn": "sklearn",
    "opencv-python": "cv2",
    "pillow": "PIL",
}

    return import_names.get(package_name.lower(), package_name.replace("-", "_"))


def read_requirements() -> list[tuple[str, str]]:
    """
    Read requirements.txt and return:
        [(package_name, import_name), ...]
    """

    if not REQUIREMENTS_FILE.exists():
        print(f"ERROR: requirements.txt not found:")
        print(f"       {REQUIREMENTS_FILE}")
        return []

    packages = []

    with REQUIREMENTS_FILE.open("r", encoding="utf-8") as file:
        for line in file:
            package_name = get_package_name(line)

            if package_name:
                import_name = get_import_name(package_name)
                packages.append((package_name, import_name))

    return packages


def find_missing_packages(
    packages: list[tuple[str, str]]
) -> list[str]:
    """
    Check whether every required package can be imported.
    """

    missing = []

    for package_name, import_name in packages:
        try:
            importlib.import_module(import_name)
        except ImportError:
            missing.append(package_name)

    return missing


def install_requirements() -> bool:
    """
    Install all dependencies from requirements.txt.
    """

    print()
    print("=" * 60)
    print(" Installing missing dependencies")
    print("=" * 60)
    print()

    try:
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--upgrade",
                "pip",
            ]
        )

        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-r",
                str(REQUIREMENTS_FILE),
            ]
        )

        return True

    except subprocess.CalledProcessError as error:
        print()
        print("=" * 60)
        print(" ERROR: Dependency installation failed")
        print("=" * 60)
        print()
        print(f"pip exited with code: {error.returncode}")
        return False


def ensure_requirements() -> bool:
    """
    Main dependency verification function.

    Returns:
        True  -> all requirements are ready
        False -> dependency setup failed
    """

    print()
    print("=" * 60)
    print(" AIIA CTMS - Dependency Check")
    print("=" * 60)

    packages = read_requirements()

    if not packages:
        print()
        print("ERROR: No packages found in requirements.txt.")
        return False

    print()
    print(f"Checking {len(packages)} required packages...")

    missing = find_missing_packages(packages)

    if not missing:
        print()
        print("[OK] All required dependencies are installed.")
        print("=" * 60)
        print()
        return True

    print()
    print("Missing dependencies:")

    for package in missing:
        print(f"  - {package}")

    print()
    print("Installing missing dependencies...")

    if not install_requirements():
        return False

    print()
    print("Verifying installation...")

    missing_after_install = find_missing_packages(packages)

    if missing_after_install:
        print()
        print("ERROR: The following dependencies are still missing:")

        for package in missing_after_install:
            print(f"  - {package}")

        print()
        print("Backend startup cancelled.")
        return False

    print()
    print("[OK] All dependencies installed successfully.")
    print("=" * 60)
    print()

    return True

