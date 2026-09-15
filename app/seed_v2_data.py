"""
Comprehensive V2 Seed Data script for AIIA CTMS (AAYUR SATHI).
Ensures:
1. Multi-PI scoping via study_team (PI-1 vs PI-2).
2. Coordinator and Monitor assignments in study_team.
3. NPvCC Signal Detection: 3x 'elevated_alt' within the last 20 days on Study 4.
4. DPDP Act 2023 Informed Consent records for enrolled patients.
5. Study 4 inclusion/exclusion criteria & patient IE evaluation results.
6. GCP Data Query on Study 4 (open query for demo).
7. ALCOA+ Monitoring visit report on Study 4.
8. Ayush formulation metadata and classical references.
"""

from datetime import date, datetime, timedelta
import uuid
from app.database import SessionLocal
from app.models import (
    AdverseEvent,
    DataQuery,
    IECriteria,
    IEResult,
    InformedConsent,
    MonitoringVisit,
    Patient,
    ResearchStudy,
    StudyTeam,
    User,
    VisitLog,
)


def seed_v2():
    db = SessionLocal()
    try:
        today = date.today()

        pi1 = db.query(User).filter(User.email == "pi@aiia-ctms.com").first()
        pi2 = db.query(User).filter(User.email == "pi2@aiia-ctms.com").first()
        coord = db.query(User).filter(User.email == "coordinator@aiia-ctms.com").first()
        cra = db.query(User).filter(User.email == "monitor@aiia-ctms.com").first()
        pv = db.query(User).filter(User.email == "pv@aiia-ctms.com").first()
        admin = db.query(User).filter(User.email == "admin@aiia-ctms.com").first()

        studies = db.query(ResearchStudy).order_by(ResearchStudy.created_at.asc()).all()
        if not studies:
            print("No studies found. Please run seed_studies.py first.")
            return

        print(f"Found {len(studies)} studies. Applying V2 Master Specification data...")

        # 1. Update formulation metadata & PI assignments
        for idx, s in enumerate(studies, start=1):
            if "Guduchi" in s.title:
                s.ayurvedic_intervention = "Guduchi Ghanvati (Tinospora cordifolia, 500mg BD)"
                s.ayush_system = "Ayurveda"
                s.classical_reference = "Charaka Samhita, Chikitsa Sthana 1/2"
                s.principal_investigator_id = pi1.id
            elif "Ashwagandha" in s.title:
                s.ayurvedic_intervention = "Ashwagandha Lehyam (Withania somnifera, 10g BD with milk)"
                s.ayush_system = "Ayurveda"
                s.classical_reference = "Ashtanga Hridaya, Uttara Sthana 39"
                s.principal_investigator_id = pi1.id
            elif "Curcumin" in s.title:
                s.ayurvedic_intervention = "Standardized Curcumin Longa (95% Curcuminoids, 500mg)"
                s.ayush_system = "Ayurveda"
                s.classical_reference = "Dhanvantari Nighantu, Haritakyadi Varga"
                s.principal_investigator_id = pi1.id
            elif "Ayush-64" in s.title:
                s.ayurvedic_intervention = "Ayush-64 (Alstonia, Picrorhiza, Swertia, Caesalpinia 500mg QID)"
                s.ayush_system = "Ayurveda"
                s.classical_reference = "CCRAS Standard Ayurvedic Formulations / Bhaishajya Ratnavali"
                s.principal_investigator_id = pi1.id
            elif "Brahmi" in s.title:
                s.ayurvedic_intervention = "Brahmi Ghrita (Bacopa monnieri in Go-Ghrita, 10ml BD)"
                s.ayush_system = "Ayurveda"
                s.classical_reference = "Charaka Samhita, Chikitsa Sthana 10/25"
                s.principal_investigator_id = pi1.id
            elif "Pippali" in s.title:
                # Assign Study 6 to PI-2 (Dr. Sunita Rao) to demonstrate multi-PI isolation!
                s.ayurvedic_intervention = "Pippali Vardhamana Rasayana (Piper longum gradual titration)"
                s.ayush_system = "Ayurveda"
                s.classical_reference = "Charaka Samhita, Chikitsa Sthana 1/3"
                if pi2:
                    s.principal_investigator_id = pi2.id
            elif "Triphala" in s.title:
                s.ayurvedic_intervention = "Triphala Churna (Haritaki, Bibhitaki, Amalaki 1:1:1, 5g at bedtime)"
                s.ayush_system = "Ayurveda"
                s.classical_reference = "Sushruta Samhita, Chikitsa Sthana 46"
                s.principal_investigator_id = pi1.id

        db.commit()

        # 2. Team Assignments
        s4 = db.query(ResearchStudy).filter(ResearchStudy.title.like("%Ayush-64%")).first()
        s6 = db.query(ResearchStudy).filter(ResearchStudy.title.like("%Pippali%")).first()

        def add_team_member(study_id, user_id, role):
            existing = db.query(StudyTeam).filter(
                StudyTeam.study_id == study_id,
                StudyTeam.user_id == user_id,
                StudyTeam.role == role,
            ).first()
            if not existing:
                db.add(StudyTeam(study_id=study_id, user_id=user_id, role=role, assigned_by=admin.id if admin else None))

        # PI1 on studies
        for s in studies:
            if s.id != s6.id:
                add_team_member(s.id, pi1.id, "pi")
        # PI2 on study 6
        if pi2 and s6:
            add_team_member(s6.id, pi2.id, "pi")
        # Coordinator on Study 3, 4, 5
        if coord:
            for s in studies:
                if "Curcumin" in s.title or "Ayush-64" in s.title or "Brahmi" in s.title:
                    add_team_member(s.id, coord.id, "coordinator")
        # CRA / Monitor on Study 4, 5
        if cra:
            for s in studies:
                if "Ayush-64" in s.title or "Brahmi" in s.title:
                    add_team_member(s.id, cra.id, "monitor")

        db.commit()
        print("Study teams populated for multi-PI scoping demo.")

        # 3. Seed NPvCC 30-Day Signal: 3x 'elevated_alt' on Study 4
        if s4:
            s4_patients = db.query(Patient).filter(Patient.study_id == s4.id, Patient.status == "enrolled").all()
            if len(s4_patients) >= 3:
                existing_signals = db.query(AdverseEvent).filter(
                    AdverseEvent.study_id == s4.id,
                    AdverseEvent.ae_term == "elevated_alt",
                ).all()
                if len(existing_signals) < 3:
                    # Clear any single alt event and insert the canonical 3 events
                    for e in existing_signals:
                        db.delete(e)
                    db.commit()

                    alt_dates = [today - timedelta(days=18), today - timedelta(days=12), today - timedelta(days=5)]
                    alt_descriptions = [
                        "Routine liver function panel shows asymptomatic elevated ALT (98 U/L, >2x ULN)",
                        "Elevated serum ALT (115 U/L) noted during week 2 safety biochemistry follow-up",
                        "Asymptomatic elevation of ALT (142 U/L, ~3x ULN) and AST (88 U/L) on safety panel",
                    ]
                    for idx in range(3):
                        p = s4_patients[idx]
                        report_d = alt_dates[idx]
                        reg_d = report_d + timedelta(days=30)
                        ae = AdverseEvent(
                            study_id=s4.id,
                            patient_id=p.id,
                            description=alt_descriptions[idx],
                            seriousness="non_serious",
                            outcome="under_evaluation",
                            onset_date=report_d - timedelta(days=1),
                            report_date=report_d,
                            regulatory_deadline=reg_d,
                            reported_by=coord.id if coord else None,
                            status="open",
                            ae_term="elevated_alt",
                            causality="possible",
                            action_taken="Temporary dose hold, repeat LFT ordered within 7 days",
                            reporter_role="coordinator",
                        )
                        db.add(ae)
                    db.commit()
                    print("Seeded 3x 'elevated_alt' AEs on Study 4 for NPvCC 30-Day Signal Detection demo.")

        # 4. Seed Informed Consent records for enrolled patients (and omit for screened)
        if s4:
            s4_patients = db.query(Patient).filter(Patient.study_id == s4.id).all()
            for p in s4_patients:
                if p.status == "enrolled":
                    # Check consent
                    existing_c = db.query(InformedConsent).filter(
                        InformedConsent.patient_id == p.id,
                        InformedConsent.withdrawn_at.is_(None),
                    ).first()
                    if not existing_c:
                        doc_ref = f"ICF-SIG-{str(p.id)[:8].upper()}-AIIA-v1.0.pdf"
                        db.add(
                            InformedConsent(
                                patient_id=p.id,
                                study_id=s4.id,
                                consent_version="v1.0",
                                consented_at=datetime.utcnow() - timedelta(days=60),
                                consent_document_ref=doc_ref,
                                witnessed_by=coord.id if coord else None,
                            )
                        )
                    p.abha_id = f"91-4921-3829-{str(p.id)[-4:]}"
                    p.abha_status = "verified"
            db.commit()
            print("Seeded Informed Consent records (Gate 2) and ABHA IDs.")

        # 5. Inclusion / Exclusion Criteria & Assessments on Study 4
        if s4:
            ie_defs = [
                ("inclusion", 1, "Age between 18 and 65 years inclusive"),
                ("inclusion", 2, "Confirmed mild to moderate URTI symptoms for <= 48 hours"),
                ("inclusion", 3, "Willingness to comply with trial procedures and sign ICF"),
                ("exclusion", 1, "Severe acute respiratory distress or SpO2 < 94%"),
                ("exclusion", 2, "History of severe hepatic impairment or AST/ALT > 3x ULN at baseline"),
            ]
            crit_objs = []
            for c_type, c_num, desc in ie_defs:
                crit = db.query(IECriteria).filter(
                    IECriteria.study_id == s4.id,
                    IECriteria.criterion_type == c_type,
                    IECriteria.criterion_number == c_num,
                ).first()
                if not crit:
                    crit = IECriteria(
                        study_id=s4.id,
                        criterion_type=c_type,
                        criterion_number=c_num,
                        description=desc,
                    )
                    db.add(crit)
                    db.flush()
                crit_objs.append(crit)
            db.commit()

            # Record IE evaluations for enrolled patients
            enrolled_pts = db.query(Patient).filter(Patient.study_id == s4.id, Patient.status == "enrolled").limit(5).all()
            for p in enrolled_pts:
                for c in crit_objs:
                    existing_res = db.query(IEResult).filter(
                        IEResult.patient_id == p.id,
                        IEResult.criterion_id == c.id,
                    ).first()
                    if not existing_res:
                        # For inclusion: met=True; for exclusion: met=False (meaning did not meet exclusion, so eligible)
                        met_val = True if c.criterion_type == "inclusion" else False
                        db.add(
                            IEResult(
                                patient_id=p.id,
                                criterion_id=c.id,
                                met=met_val,
                                evaluated_by=coord.id if coord else None,
                            )
                        )
            db.commit()
            print("Seeded Inclusion/Exclusion criteria and results for SDTM IE domain.")

        # 6. Seed Data Query on Study 4
        if s4 and cra and coord:
            sample_pt = db.query(Patient).filter(Patient.study_id == s4.id, Patient.status == "enrolled").first()
            sample_visit = db.query(VisitLog).filter(VisitLog.study_id == s4.id).first()
            existing_q = db.query(DataQuery).filter(DataQuery.study_id == s4.id).first()
            if not existing_q:
                db.add(
                    DataQuery(
                        study_id=s4.id,
                        patient_id=sample_pt.id if sample_pt else None,
                        visit_log_id=sample_visit.id if sample_visit else None,
                        raised_by=cra.id,
                        field_name="visit_log.actual_date",
                        query_text="Visit 2 was logged 2 days after protocol window. Please confirm source documentation and upload justification.",
                        status="open",
                    )
                )
                db.commit()
                print("Seeded open GCP Data Query for Monitor/Coordinator workflow.")

        # 7. Seed Monitoring Visit on Study 4
        if s4 and cra:
            existing_mv = db.query(MonitoringVisit).filter(MonitoringVisit.study_id == s4.id).first()
            if not existing_mv:
                db.add(
                    MonitoringVisit(
                        study_id=s4.id,
                        monitor_id=cra.id,
                        visit_date=today - timedelta(days=7),
                        visit_type="routine",
                        findings="100% Informed Consent forms verified in physical binder. 20% Source Data Verification (SDV) completed. Drug accountability logs reconciled.",
                        issues_identified="1 minor visit window deviation identified. Query issued in electronic CRF.",
                        follow_up_required=True,
                    )
                )
                db.commit()
                print("Seeded ALCOA+ Routine Monitoring Visit report.")

        print("\nAll V2 seed data successfully populated!")
    finally:
        db.close()


if __name__ == "__main__":
    seed_v2()
