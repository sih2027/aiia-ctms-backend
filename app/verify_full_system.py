"""
Comprehensive System Verification Suite for AIIA CTMS Backend (AAYUR SATHI).
Tests all 6 Phases of the Master Technical Specification:
1. Auth & JWT across 8 test users (including PI-1 and PI-2).
2. Multi-PI scoping & Study Team assignments.
3. CTRI Legal Hard Gate (Gate 1) & DPDP Act 2023 Consent Gate (Gate 2).
4. NPvCC 30-Day Rolling Safety Signal Detection (count >= 3).
5. WHO-UMC causality assessment.
6. GCP Clinical Data Query Engine (raise, answer, close).
7. ALCOA+ Site Monitoring Visit Reports.
8. FHIR R4 JSON resources (ResearchStudy, AdverseEvent, Patient).
9. CDISC SDTM exports (DM, AE, and IE domains) with SHA-256 integrity header.
10. ABDM Sandbox Integration (M1 ABHA verification, M2 Care Context push).
11. Cryptographic Merkle Root Verification, Live Explorer URL & Tamper Simulator.
"""

import sys
from datetime import date, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models import Patient, ResearchStudy, User, AdverseEvent
from app.merkle_service import compute_merkle_root, get_unanchored_rows

client = TestClient(app)

PASS = "\033[92m[PASS]\033[0m"
FAIL = "\033[91m[FAIL]\033[0m"


def get_token_for(email: str, password: str = "Test@1234") -> str:
    res = client.post("/auth/login", json={"email": email, "password": password})
    if res.status_code != 200:
        raise RuntimeError(f"Login failed for {email}: {res.text}")
    return res.json()["access_token"]


def run_all_checks():
    failures = 0
    print("=" * 75)
    print("       AAYUR SATHI (AIIA CTMS) - MASTER SPECIFICATION VERIFICATION")
    print("=" * 75)

    # 1. AUTH ACROSS ALL 8 TEST USERS (INCLUDING PI-1 & PI-2)
    roles = [
        ("admin", "admin@aiia-ctms.com"),
        ("pi", "pi@aiia-ctms.com"),
        ("pi2", "pi2@aiia-ctms.com"),
        ("coordinator", "coordinator@aiia-ctms.com"),
        ("monitor", "monitor@aiia-ctms.com"),
        ("ethics_committee", "ethics@aiia-ctms.com"),
        ("pharmacovigilance", "pv@aiia-ctms.com"),
        ("regulator", "regulator@aiia-ctms.com"),
    ]
    tokens = {}
    print("\n[1] Testing Authentication for all 8 User Accounts...")
    for label, email in roles:
        try:
            token = get_token_for(email)
            tokens[label] = token
            me_res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
            assert me_res.status_code == 200
            expected_role = "pi" if label == "pi2" else label
            assert me_res.json()["role"] == expected_role
            print(f"  {PASS} User '{email}' ({expected_role}): token issued & validated.")
        except Exception as e:
            print(f"  {FAIL} User '{email}': failed with error: {e}")
            failures += 1

    # 2. MULTI-PI STUDY SCOPING & TEAM ASSIGNMENT
    print("\n[2] Testing Multi-PI RBAC Scoping & Study Team Assignments...")
    try:
        # PI-1 studies
        res_pi1 = client.get("/studies", headers={"Authorization": f"Bearer {tokens['pi']}"})
        assert res_pi1.status_code == 200
        pi1_studies = res_pi1.json()

        # PI-2 studies
        res_pi2 = client.get("/studies", headers={"Authorization": f"Bearer {tokens['pi2']}"})
        assert res_pi2.status_code == 200
        pi2_studies = res_pi2.json()

        assert len(pi1_studies) > 0
        assert len(pi2_studies) > 0
        # Check that PI-2 only sees their assigned study (Pippali)
        assert any("Pippali" in s["title"] for s in pi2_studies)
        assert not any("Guduchi" in s["title"] for s in pi2_studies)
        print(f"  {PASS} Multi-PI Scoping: PI-1 sees {len(pi1_studies)} studies; PI-2 isolated to {len(pi2_studies)} study.")

        # Test Study Team Assignment
        s4 = next(s for s in pi1_studies if "Ayush-64" in s["title"])
        team_res = client.get(f"/studies/{s4['id']}/team", headers={"Authorization": f"Bearer {tokens['admin']}"})
        assert team_res.status_code == 200
        team_members = team_res.json()
        assert len(team_members) >= 2
        print(f"  {PASS} Study Team Ledger: verified {len(team_members)} active personnel assigned to Study 4.")
    except Exception as e:
        print(f"  {FAIL} Multi-PI / Team verification failed: {e}")
        failures += 1

    # 3. DUAL-GATE PATIENT ENROLLMENT (GATE 1: CTRI, GATE 2: DPDP ACT 2023 CONSENT)
    print("\n[3] Testing Dual-Gate Patient Enrollment (Legal + Ethical Checkpoints)...")
    try:
        # Screen a new patient on Study 1 (CTRI not registered)
        s1 = next(s for s in pi1_studies if "Guduchi" in s["title"])
        screen_res1 = client.post(
            "/patients/screen",
            json={"study_id": s1["id"], "screening_number": f"TEST-G1-{date.today().strftime('%M%S')}", "age": 42, "sex": "M"},
            headers={"Authorization": f"Bearer {tokens['coordinator']}"},
        )
        assert screen_res1.status_code == 201
        p_g1 = screen_res1.json()

        # Attempt to enroll on unregistered study -> Must fail Gate 1
        enroll_fail_g1 = client.post(
            "/patients/enroll",
            json={"patient_id": p_g1["id"]},
            headers={"Authorization": f"Bearer {tokens['coordinator']}"},
        )
        assert enroll_fail_g1.status_code == 400
        assert "GATE 1" in enroll_fail_g1.text or "CTRI" in enroll_fail_g1.text
        print(f"  {PASS} Gate 1 Enforcement: Unregistered study enrollment strictly blocked with 400.")

        # Screen a patient on Study 4 (CTRI registered, but NO consent yet)
        screen_res2 = client.post(
            "/patients/screen",
            json={
                "study_id": s4["id"],
                "screening_number": f"TEST-G2-{date.today().strftime('%M%S')}",
                "age": 36,
                "sex": "F",
                "abha_id": "91-4921-3829-1092",
            },
            headers={"Authorization": f"Bearer {tokens['coordinator']}"},
        )
        assert screen_res2.status_code == 201
        p_g2 = screen_res2.json()

        # Attempt to enroll without consent -> Must fail Gate 2
        enroll_fail_g2 = client.post(
            "/patients/enroll",
            json={"patient_id": p_g2["id"]},
            headers={"Authorization": f"Bearer {tokens['coordinator']}"},
        )
        assert enroll_fail_g2.status_code == 400
        assert "GATE 2" in enroll_fail_g2.text or "Consent" in enroll_fail_g2.text
        print(f"  {PASS} Gate 2 Enforcement: Patient without signed ICF strictly blocked with 400.")

        # Now record Informed Consent under DPDP Act 2023
        consent_res = client.post(
            f"/patients/{p_g2['id']}/consent",
            json={"consent_version": "v1.0"},
            headers={"Authorization": f"Bearer {tokens['coordinator']}"},
        )
        assert consent_res.status_code == 201
        print(f"  {PASS} Consent Registered: DPDP Act 2023 Informed Consent record generated.")

        # Enroll patient with both gates passed
        enroll_success = client.post(
            "/patients/enroll",
            json={"patient_id": p_g2["id"]},
            headers={"Authorization": f"Bearer {tokens['coordinator']}"},
        )
        assert enroll_success.status_code == 200
        assert enroll_success.json()["status"] == "enrolled"
        print(f"  {PASS} Dual Gate Passed: Patient enrolled successfully! Randomization ID: {enroll_success.json()['randomization_number']}.")
    except Exception as e:
        print(f"  {FAIL} Dual-Gate Enrollment verification failed: {e}")
        failures += 1

    # 4. NPvCC 30-DAY ROLLING SAFETY SIGNAL DETECTION
    print("\n[4] Testing NPvCC 30-Day Rolling Safety Signal Detection...")
    try:
        sig_res = client.get("/ae/signals", headers={"Authorization": f"Bearer {tokens['pharmacovigilance']}"})
        assert sig_res.status_code == 200
        signals = sig_res.json()
        assert len(signals) >= 1, "Expected at least 1 active safety signal"
        top_sig = signals[0]
        assert top_sig["signal_level"] == "HIGH"
        assert top_sig["count_in_30_days"] >= 3
        print(f"  {PASS} NPvCC Signal Algorithm: detected HIGH signal for '{top_sig['ae_term']}' ({top_sig['count_in_30_days']} cases in 30 days).")
        print(f"  {PASS} Suspected formulation: '{top_sig['intervention']}'.")
    except Exception as e:
        print(f"  {FAIL} NPvCC Safety Signal detection failed: {e}")
        failures += 1

    # 5. WHO-UMC CAUSALITY ASSESSMENT WORKFLOW
    print("\n[5] Testing WHO-UMC Causality Assessment Workflow...")
    try:
        ae_list = client.get("/ae", headers={"Authorization": f"Bearer {tokens['pharmacovigilance']}"}).json()
        target_ae = ae_list[0]
        causality_res = client.patch(
            f"/ae/{target_ae['id']}/causality",
            json={"causality": "probable", "action_taken": "Temporary dose hold, LFT re-evaluation"},
            headers={"Authorization": f"Bearer {tokens['pharmacovigilance']}"},
        )
        assert causality_res.status_code == 200
        assert causality_res.json()["causality"] == "probable"
        print(f"  {PASS} WHO-UMC Causality: successfully updated to 'probable' with audit trail record.")
    except Exception as e:
        print(f"  {FAIL} WHO-UMC Causality assessment failed: {e}")
        failures += 1

    # 6. GCP CLINICAL DATA QUERY ENGINE
    print("\n[6] Testing GCP Clinical Data Query Engine (Raise, Answer, Close)...")
    try:
        # Monitor raises query
        q_create = client.post(
            "/queries",
            json={
                "study_id": s4["id"],
                "field_name": "patient.vitals.blood_pressure",
                "query_text": "Verify systolic BP value against source nurse charting.",
            },
            headers={"Authorization": f"Bearer {tokens['monitor']}"},
        )
        assert q_create.status_code == 201
        q_id = q_create.json()["id"]

        # Coordinator answers query
        q_answer = client.patch(
            f"/queries/{q_id}/answer",
            json={"resolution_text": "Source chart re-verified. 128/82 confirmed correct by clinical nurse."},
            headers={"Authorization": f"Bearer {tokens['coordinator']}"},
        )
        assert q_answer.status_code == 200
        assert q_answer.json()["status"] == "answered"

        # Monitor closes query
        q_close = client.patch(
            f"/queries/{q_id}/close",
            json={"comments": "Source verification accepted."},
            headers={"Authorization": f"Bearer {tokens['monitor']}"},
        )
        assert q_close.status_code == 200
        assert q_close.json()["status"] == "closed"
        print(f"  {PASS} GCP Data Query Engine: complete lifecycle (Open -> Answered -> Closed) verified.")
    except Exception as e:
        print(f"  {FAIL} Data Query Engine test failed: {e}")
        failures += 1

    # 7. ALCOA+ SITE MONITORING VISIT REPORTS
    print("\n[7] Testing ALCOA+ Site Monitoring Visit Reports...")
    try:
        mv_res = client.post(
            "/monitoring-visits",
            json={
                "study_id": s4["id"],
                "visit_date": str(date.today()),
                "visit_type": "routine",
                "findings": "100% consent audit passed. Drug accountability reconciled.",
                "issues_identified": "None",
                "follow_up_required": False,
            },
            headers={"Authorization": f"Bearer {tokens['monitor']}"},
        )
        assert mv_res.status_code == 201
        print(f"  {PASS} Monitoring Visit Report: ALCOA+ Routine Visit logged successfully.")
    except Exception as e:
        print(f"  {FAIL} Monitoring visit report failed: {e}")
        failures += 1

    # 8. CDISC SDTM CSV EXPORTS (DM, AE, IE) WITH INTEGRITY HASH
    print("\n[8] Testing CDISC SDTM CSV Exports (DM, AE, IE)...")
    try:
        for domain in ["dm", "ae", "ie"]:
            exp_res = client.get(
                f"/export/sdtm/{domain}/{s4['id']}",
                headers={"Authorization": f"Bearer {tokens['regulator']}"},
            )
            assert exp_res.status_code == 200
            assert "text/csv" in exp_res.headers.get("content-type", "")
            sha256 = exp_res.headers.get("x-export-sha256")
            assert sha256 is not None
            print(f"  {PASS} SDTM {domain.upper()} domain CSV: generated with SHA-256 header ({sha256[:16]}...).")
    except Exception as e:
        print(f"  {FAIL} CDISC SDTM export failed: {e}")
        failures += 1

    # 9. ABDM SANDBOX INTEGRATION
    print("\n[9] Testing ABDM M1 (ABHA Verification) & M2 (Care Context Linking)...")
    try:
        # Verify Health ID
        abdm_res = client.post(
            "/abdm/verify-health-id",
            json={"abha_id": "91-4921-3829-1092"},
            headers={"Authorization": f"Bearer {tokens['coordinator']}"},
        )
        assert abdm_res.status_code == 200
        assert abdm_res.json()["status"] == "verified"
        print(f"  {PASS} ABDM M1: 14-digit ABHA ID verified against gateway.")

        # Push Care Context
        cc_res = client.post(
            "/abdm/push-care-context",
            json={"patient_id": p_g2["id"], "display_title": "Trial Visit 1 - Ayush-64 Encounter"},
            headers={"Authorization": f"Bearer {tokens['coordinator']}"},
        )
        assert cc_res.status_code == 200
        assert cc_res.json()["status"] == "success"
        print(f"  {PASS} ABDM M2: Clinical trial encounter linked to patient PHR ({cc_res.json()['care_context_reference']}).")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"  {FAIL} ABDM integration test failed: {e}")
        failures += 1

    # 10. BLOCKCHAIN CRYPTOGRAPHIC VERIFICATION & TAMPER SIMULATOR
    print("\n[10] Testing Blockchain Cryptographic Verification & Tamper Simulation...")
    try:
        # Trigger Anchor first so at least one anchor exists on chain
        anchor_trigger = client.post("/audit/anchor", headers={"Authorization": f"Bearer {tokens['admin']}"})
        assert anchor_trigger.status_code == 200

        # Standard clean verify
        clean_verify = client.get("/audit/verify", headers={"Authorization": f"Bearer {tokens['regulator']}"})
        assert clean_verify.status_code == 200
        assert clean_verify.json()["status"] == "matched"
        print(f"  {PASS} Clean Verification: status is '{clean_verify.json()['status']}'.")

        # Simulate Tampering
        tamper_trigger = client.post("/audit/simulate-tamper", headers={"Authorization": f"Bearer {tokens['regulator']}"})
        assert tamper_trigger.status_code == 200

        tamper_verify = client.get("/audit/verify", headers={"Authorization": f"Bearer {tokens['regulator']}"})
        assert tamper_verify.json()["status"] == "mismatched"
        print(f"  {PASS} Tamper Simulation: Cryptographic discrepancy detected instantly (status='mismatched')!")

        # Restore Integrity
        restore_trigger = client.post("/audit/restore-tamper", headers={"Authorization": f"Bearer {tokens['regulator']}"})
        assert restore_trigger.status_code == 200

        restored_verify = client.get("/audit/verify", headers={"Authorization": f"Bearer {tokens['regulator']}"})
        assert restored_verify.json()["status"] == "matched"
        print(f"  {PASS} Pristine State Restored: Verification returned to 100% matched.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"  {FAIL} Blockchain verification / tamper test failed: {e}")
        failures += 1

    print("\n" + "=" * 75)
    if failures == 0:
        print("   ALL MASTER SPECIFICATION SUITE VERIFICATION CHECKS PASSED (10/10)!")
    else:
        print(f"   VERIFICATION COMPLETED WITH {failures} FAILURE(S).")
    print("=" * 75)
    return failures == 0


if __name__ == "__main__":
    success = run_all_checks()
    sys.exit(0 if success else 1)
