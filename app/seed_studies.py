"""
Synthetic Seed Data Generation (Section 10 Dataset Strategy).
Populates 7 Ayurvedic clinical trials at the 7 required lifecycle stages:
1. Pending IEC
2. IEC approved, pending CTRI
3. Site activation (CTRI registered, 0 enrolled)
4. Actively enrolling (60% target enrolled)
5. Critically behind (20% target enrolled)
6. IEC renewal overdue (past renewal due date)
7. Completed (100% target enrolled)

Also seeds:
- Real CTRI registration numbers and realistic AYUSH formulations.
- Milestones (with overdue alerts).
- Synthetic CDISC SDTM shaped patients.
- Visit logs and protocol deviations.
- The 6 prescribed AE/SAE records per Section 10:
  * 2 non-serious resolved
  * 2 non-serious open
  * 1 serious resolved
  * 1 serious open with regulatory deadline 3 days away.
- Hash-chained audit trail entries.
"""

import sys
from datetime import date, timedelta
from app.audit_log import log_action
from app.database import SessionLocal
from app.models import (
    AdverseEvent,
    Milestone,
    Patient,
    ProtocolDeviation,
    ResearchStudy,
    User,
    VisitLog,
)


def seed_all_data():
    db = SessionLocal()
    try:
        pi_user = db.query(User).filter(User.role == "pi").first()
        coord_user = db.query(User).filter(User.role == "coordinator").first()
        pv_user = db.query(User).filter(User.role == "pharmacovigilance").first()
        admin_user = db.query(User).filter(User.role == "admin").first()

        if not pi_user:
            print("ERROR: Test users not found. Run python -m app.seed_test_users first.")
            sys.exit(1)

        today = date.today()

        # Check if already seeded
        existing_study = db.query(ResearchStudy).filter(
            ResearchStudy.title.like("%Guduchi Ghanvati%")
        ).first()
        if existing_study:
            print("Seed studies already present in database. Skipping seeding.")
            return

        print("Seeding 7 Ayurvedic Clinical Trials across all 7 lifecycle stages...")

        # 1. Stage 1: Pending IEC
        s1 = ResearchStudy(
            title="Efficacy of Guduchi Ghanvati (Tinospora cordifolia) in Chronic Allergic Rhinitis",
            status="pending_iec",
            phase="Phase 2",
            sponsor="All India Institute of Ayurveda (AIIA)",
            ctri_registration_number=None,
            ctri_status="not_registered",
            iec_approval_status="pending",
            enrollment_target=60,
            enrolled_count=0,
            site_id="AIIA-DELHI-01",
            principal_investigator_id=pi_user.id,
            start_date=today + timedelta(days=60),
            end_date=today + timedelta(days=240),
        )
        db.add(s1)
        db.flush()
        db.add(Milestone(study_id=s1.id, milestone_type="iec_approval", due_date=today + timedelta(days=15), status="pending"))

        # 2. Stage 2: IEC Approved, Pending CTRI
        s2 = ResearchStudy(
            title="Evaluation of Ashwagandha Lehyam (Withania somnifera) in Subclinical Hypothyroidism",
            status="iec_approved",
            phase="Phase 2",
            sponsor="Ministry of AYUSH",
            ctri_registration_number=None,
            ctri_status="pending",
            iec_approval_status="approved",
            iec_approval_date=today - timedelta(days=30),
            iec_renewal_due=today + timedelta(days=335),
            enrollment_target=80,
            enrolled_count=0,
            site_id="AIIA-DELHI-01",
            principal_investigator_id=pi_user.id,
            start_date=today + timedelta(days=30),
            end_date=today + timedelta(days=210),
        )
        db.add(s2)
        db.flush()
        db.add(Milestone(study_id=s2.id, milestone_type="iec_approval", due_date=today - timedelta(days=30), completed_date=today - timedelta(days=30), status="completed"))
        db.add(Milestone(study_id=s2.id, milestone_type="ctri_registration", due_date=today + timedelta(days=10), status="pending"))

        # 3. Stage 3: Site Activation (CTRI Registered, 0 enrolled)
        s3 = ResearchStudy(
            title="Standardized Curcumin Longa Extract in Primary Knee Osteoarthritis (Sandhigatavata)",
            status="site_activation",
            phase="Phase 3",
            sponsor="All India Institute of Ayurveda (AIIA)",
            ctri_registration_number="CTRI/2024/01/061234",
            ctri_status="registered",
            iec_approval_status="approved",
            iec_approval_date=today - timedelta(days=60),
            iec_renewal_due=today + timedelta(days=305),
            enrollment_target=100,
            enrolled_count=0,
            site_id="AIIA-DELHI-02",
            principal_investigator_id=pi_user.id,
            start_date=today,
            end_date=today + timedelta(days=365),
        )
        db.add(s3)
        db.flush()
        db.add(Milestone(study_id=s3.id, milestone_type="site_activation", due_date=today + timedelta(days=7), status="pending"))

        # 4. Stage 4: Actively Enrolling (60% of Target Enrolled)
        s4 = ResearchStudy(
            title="Multicenter Evaluation of Ayush-64 in Mild to Moderate Upper Respiratory Tract Infections",
            status="actively_enrolling",
            phase="Phase 3",
            sponsor="CCRAS & AIIA",
            ctri_registration_number="CTRI/2023/11/059871",
            ctri_status="registered",
            iec_approval_status="approved",
            iec_approval_date=today - timedelta(days=180),
            iec_renewal_due=today + timedelta(days=185),
            enrollment_target=100,
            enrolled_count=60,
            site_id="AIIA-DELHI-01",
            principal_investigator_id=pi_user.id,
            start_date=today - timedelta(days=120),
            end_date=today + timedelta(days=180),
        )
        db.add(s4)
        db.flush()
        db.add(Milestone(study_id=s4.id, milestone_type="first_patient_enrolled", due_date=today - timedelta(days=100), completed_date=today - timedelta(days=100), status="completed"))
        db.add(Milestone(study_id=s4.id, milestone_type="last_patient_enrolled", due_date=today + timedelta(days=60), status="pending"))

        # 5. Stage 5: Critically Behind (20% of Target Enrolled)
        s5 = ResearchStudy(
            title="Double-Blind Clinical Trial of Brahmi Ghrita in Mild Cognitive Impairment (Smritibhramsha)",
            status="critically_behind",
            phase="Phase 2",
            sponsor="AIIA Research Directorate",
            ctri_registration_number="CTRI/2023/08/056412",
            ctri_status="registered",
            iec_approval_status="approved",
            iec_approval_date=today - timedelta(days=240),
            iec_renewal_due=today + timedelta(days=125),
            enrollment_target=120,
            enrolled_count=24,
            site_id="AIIA-DELHI-03",
            principal_investigator_id=pi_user.id,
            start_date=today - timedelta(days=180),
            end_date=today + timedelta(days=90),
        )
        db.add(s5)
        db.flush()
        # Overdue milestone to demonstrate KPI alerts
        db.add(Milestone(study_id=s5.id, milestone_type="last_patient_enrolled", due_date=today - timedelta(days=15), status="pending"))

        # 6. Stage 6: IEC Renewal Overdue
        s6 = ResearchStudy(
            title="Therapeutic Potential of Pippali Rasayana in Chronic Bronchial Asthma (Tamaka Shwasa)",
            status="iec_renewal_overdue",
            phase="Phase 2",
            sponsor="Ministry of AYUSH",
            ctri_registration_number="CTRI/2022/10/047812",
            ctri_status="registered",
            iec_approval_status="approved",
            iec_approval_date=today - timedelta(days=400),
            iec_renewal_due=today - timedelta(days=35),  # OVERDUE
            enrollment_target=50,
            enrolled_count=35,
            site_id="AIIA-DELHI-01",
            principal_investigator_id=pi_user.id,
            start_date=today - timedelta(days=360),
            end_date=today + timedelta(days=60),
        )
        db.add(s6)
        db.flush()
        db.add(Milestone(study_id=s6.id, milestone_type="iec_renewal", due_date=today - timedelta(days=35), status="overdue"))

        # 7. Stage 7: Completed (100% target enrolled and closed)
        s7 = ResearchStudy(
            title="Clinical Investigation of Triphala Churna Formulations in Functional Constipation (Vibandha)",
            status="completed",
            phase="Phase 4",
            sponsor="All India Institute of Ayurveda (AIIA)",
            ctri_registration_number="CTRI/2022/04/041982",
            ctri_status="registered",
            iec_approval_status="approved",
            iec_approval_date=today - timedelta(days=500),
            enrollment_target=80,
            enrolled_count=80,
            site_id="AIIA-DELHI-01",
            principal_investigator_id=pi_user.id,
            start_date=today - timedelta(days=450),
            end_date=today - timedelta(days=30),
        )
        db.add(s7)
        db.flush()
        db.add(Milestone(study_id=s7.id, milestone_type="database_lock", due_date=today - timedelta(days=40), completed_date=today - timedelta(days=40), status="completed"))
        db.add(Milestone(study_id=s7.id, milestone_type="study_closeout", due_date=today - timedelta(days=30), completed_date=today - timedelta(days=30), status="completed"))

        db.commit()

        # Seed Synthetic Patients for Study 4 (Actively Enrolling) and Study 5
        print("Seeding synthetic patient records...")
        patients = []
        for i in range(1, 11):
            p = Patient(
                study_id=s4.id,
                screening_number=f"SCR-AIIA-{i:03d}",
                randomization_number=f"RND-AIIA-{i:03d}",
                enrollment_date=today - timedelta(days=90 - i * 5),
                status="enrolled",
                age=28 + (i * 3) % 40,
                sex="M" if i % 2 == 0 else "F",
            )
            db.add(p)
            patients.append(p)

        # Add 1 screened patient awaiting enrollment
        p_screened = Patient(
            study_id=s4.id,
            screening_number="SCR-AIIA-011",
            status="screened",
            age=45,
            sex="F",
        )
        db.add(p_screened)

        # Add 1 screened patient on unregistered Study 1 (to test CTRI gate)
        p_blocked = Patient(
            study_id=s1.id,
            screening_number="SCR-S1-001",
            status="screened",
            age=34,
            sex="M",
        )
        db.add(p_blocked)

        db.commit()
        for p in patients:
            db.refresh(p)
        db.refresh(p_screened)
        db.refresh(p_blocked)

        # Seed Visit Logs
        print("Seeding visit logs and protocol deviations...")
        for idx, p in enumerate(patients[:5]):
            v1 = VisitLog(
                study_id=s4.id,
                patient_id=p.id,
                visit_number=1,
                scheduled_date=p.enrollment_date,
                actual_date=p.enrollment_date,
                status="completed",
                deviation_flag=False,
            )
            v2 = VisitLog(
                study_id=s4.id,
                patient_id=p.id,
                visit_number=2,
                scheduled_date=p.enrollment_date + timedelta(days=14),
                actual_date=p.enrollment_date + timedelta(days=16) if idx == 0 else p.enrollment_date + timedelta(days=14),
                status="completed",
                deviation_flag=(idx == 0),
            )
            db.add_all([v1, v2])

            if idx == 0:
                db.flush()
                # Protocol deviation for 2 days late visit window
                dev = ProtocolDeviation(
                    study_id=s4.id,
                    patient_id=p.id,
                    visit_log_id=v2.id,
                    description="Visit 2 conducted outside +/- 1 day protocol permissible window (2 days delay)",
                    severity="minor",
                    reported_by=coord_user.id if coord_user else None,
                )
                db.add(dev)

        db.commit()

        # Seed the 6 prescribed synthetic AE/SAE records (Section 10)
        print("Seeding AE/SAE records matching Section 10 rules...")
        # 1. Non-serious resolved
        ae1 = AdverseEvent(
            study_id=s4.id,
            patient_id=patients[0].id,
            description="Mild nausea after oral administration of tablet on empty stomach",
            seriousness="non_serious",
            outcome="resolved",
            onset_date=today - timedelta(days=40),
            report_date=today - timedelta(days=38),
            regulatory_deadline=today - timedelta(days=8),
            status="resolved",
            ae_term="nausea",
            reported_by=coord_user.id if coord_user else None,
        )

        # 2. Non-serious resolved
        ae2 = AdverseEvent(
            study_id=s4.id,
            patient_id=patients[1].id,
            description="Transient headache following morning dose, resolved without intervention",
            seriousness="non_serious",
            outcome="resolved",
            onset_date=today - timedelta(days=35),
            report_date=today - timedelta(days=33),
            regulatory_deadline=today - timedelta(days=3),
            status="resolved",
            ae_term="headache",
            reported_by=coord_user.id if coord_user else None,
        )

        # 3. Non-serious open
        ae3 = AdverseEvent(
            study_id=s4.id,
            patient_id=patients[2].id,
            description="Mild pruritus over flexor aspect of forearms",
            seriousness="non_serious",
            outcome="recovering",
            onset_date=today - timedelta(days=10),
            report_date=today - timedelta(days=9),
            regulatory_deadline=today + timedelta(days=21),  # report_date + 30 days
            status="open",
            ae_term="pruritus",
            reported_by=coord_user.id if coord_user else None,
        )

        # 4. Non-serious open
        ae4 = AdverseEvent(
            study_id=s4.id,
            patient_id=patients[3].id,
            description="Mild fatigue reported at week 4 follow-up visit",
            seriousness="non_serious",
            outcome="unchanged",
            onset_date=today - timedelta(days=5),
            report_date=today - timedelta(days=4),
            regulatory_deadline=today + timedelta(days=26),  # report_date + 30 days
            status="open",
            ae_term="fatigue",
            reported_by=coord_user.id if coord_user else None,
        )

        # 5. Serious resolved
        ae5 = AdverseEvent(
            study_id=s4.id,
            patient_id=patients[4].id,
            description="Acute severe vomiting requiring outpatient intravenous fluid hydration",
            seriousness="serious",
            outcome="recovered",
            onset_date=today - timedelta(days=25),
            report_date=today - timedelta(days=24),
            regulatory_deadline=today - timedelta(days=9),  # serious = report_date + 15
            status="reported",
            ae_term="vomiting",
            reported_by=pv_user.id if pv_user else None,
        )

        # 6. Serious open with deadline 3 days away (CRITICAL DEMO HIGHLIGHT)
        ae6 = AdverseEvent(
            study_id=s4.id,
            patient_id=patients[5].id,
            description="Severe allergic erythematous urticaria requiring urgent clinical evaluation",
            seriousness="serious",
            outcome="recovering",
            onset_date=today - timedelta(days=13),
            report_date=today - timedelta(days=12),
            regulatory_deadline=today + timedelta(days=3),  # Exactly 3 days away!
            status="open",
            ae_term="urticaria",
            reported_by=pv_user.id if pv_user else None,
        )

        db.add_all([ae1, ae2, ae3, ae4, ae5, ae6])
        db.commit()

        # Write audit trail entries for seed actions
        log_action(
            db,
            user_id=admin_user.id if admin_user else None,
            action="CREATE",
            entity_type="research_study",
            entity_id=s4.id,
            new_value={"title": s4.title, "enrolled_count": s4.enrolled_count},
        )
        log_action(
            db,
            user_id=pv_user.id if pv_user else None,
            action="AE_REPORT",
            entity_type="adverse_event",
            entity_id=ae6.id,
            new_value={"seriousness": "serious", "deadline": str(ae6.regulatory_deadline)},
        )

        print("Synthetic seed dataset populated successfully!")
        print("  - 7 Studies created covering all 7 lifecycle stages")
        print("  - Real CTRI numbers and AYUSH trial titles applied")
        print("  - Milestones seeded (including 1 overdue for KPI alert demonstration)")
        print("  - 10 enrolled patients + 2 screened patients created")
        print("  - 6 AE records seeded (including 1 serious with deadline in 3 days)")
        print("  - Audit trail hash chained")
    finally:
        db.close()


if __name__ == "__main__":
    seed_all_data()
