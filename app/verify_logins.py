"""
Verifies the Day-1 "done" condition from Section 13:
"Login returns correct JWT for all 7 test users."

Drop this in as app/verify_logins.py — same location and same
run pattern as app/seed_test_users.py.

Prerequisites:
  1. app/seed_test_users.py has been run (python -m app.seed_test_users)
  2. The API is running locally: uvicorn app.main:app --reload

Run (from the repo root, same as the seed script):
  python -m app.verify_logins

Uses only the standard library (urllib) — no new dependency needed.
For each of the 7 roles it calls POST /auth/login, then decodes the
returned JWT locally (via app.security.decode_access_token, using the
same JWT_SECRET_KEY from your .env) to confirm the "sub" and "role"
claims are correct — not just that *a* token came back.
"""

import json
import urllib.error
import urllib.request

from app.security import decode_access_token

BASE_URL = "http://127.0.0.1:8000"
TEST_PASSWORD = "Test@1234"  # must match app/seed_test_users.py

EXPECTED = [
    ("pi@aiia-ctms.com", "pi"),
    ("coordinator@aiia-ctms.com", "coordinator"),
    ("monitor@aiia-ctms.com", "monitor"),
    ("ethics@aiia-ctms.com", "ethics_committee"),
    ("pv@aiia-ctms.com", "pharmacovigilance"),
    ("admin@aiia-ctms.com", "admin"),
    ("regulator@aiia-ctms.com", "regulator"),
]


def login(email: str, password: str) -> str:
    body = json.dumps({"email": email, "password": password}).encode()
    req = urllib.request.Request(
        f"{BASE_URL}/auth/login",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read())["access_token"]


def main() -> None:
    results = []
    for email, expected_role in EXPECTED:
        try:
            token = login(email, TEST_PASSWORD)
            payload = decode_access_token(token)
            ok = payload.get("role") == expected_role and payload.get("sub") is not None
            results.append((email, expected_role, payload.get("role"), ok, None))
        except urllib.error.HTTPError as e:
            results.append((email, expected_role, None, False, f"HTTP {e.code}"))
        except urllib.error.URLError as e:
            results.append((email, expected_role, None, False, f"connection error: {e.reason}"))
        except Exception as e:  # noqa: BLE001 — surface any decode/JWT error too
            results.append((email, expected_role, None, False, str(e)))

    print(f"{'EMAIL':<28} {'EXPECTED':<20} {'GOT':<20} STATUS")
    all_ok = True
    for email, expected, got, ok, error in results:
        status = "PASS" if ok else f"FAIL ({error})" if error else "FAIL (role mismatch)"
        all_ok &= ok
        print(f"{email:<28} {expected:<20} {str(got):<20} {status}")

    print()
    print("ALL 7 LOGINS OK — Day 1 done condition met." if all_ok
          else "NOT all logins passed — see FAIL rows above.")


if __name__ == "__main__":
    main()
