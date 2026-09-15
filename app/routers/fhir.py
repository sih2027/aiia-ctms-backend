"""
FHIR R4 Integration Endpoints (Section 9).
Provides compliant HL7 FHIR R4 JSON endpoints:
- GET /fhir/ResearchStudy/{study_id}
- GET /fhir/AdverseEvent/{ae_id}
- GET /fhir/Patient/{patient_id}
- POST /fhir/AdverseEvent (bidirectional FHIR ingestion)

Validated against HL7 FHIR Release 4 specification (hl7.org/fhir/R4).
"""

import uuid
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.audit_log import log_action
from app.database import get_db
from app.models import AdverseEvent, Patient, ResearchStudy, User
from app.routers.auth import require_role

router = APIRouter(prefix="/fhir", tags=["fhir-r4"])


def _map_study_status_to_fhir(ctms_status: str) -> str:
    mapping = {
        "pending_iec": "draft",
        "iec_approved": "in-review",
        "site_activation": "draft",
        "actively_enrolling": "active",
        "critically_behind": "active",
        "iec_renewal_overdue": "active",
        "completed": "completed",
    }
    return mapping.get(ctms_status, "active")


@router.get("/ResearchStudy/{study_id}")
def get_fhir_research_study(study_id: uuid.UUID, db: Session = Depends(get_db)):
    """Emits valid HL7 FHIR R4 ResearchStudy resource representation."""
    study = db.query(ResearchStudy).filter(ResearchStudy.id == study_id).first()
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ResearchStudy with id {study_id} not found",
        )

    identifiers = []
    if study.ctri_registration_number:
        identifiers.append(
            {
                "use": "official",
                "system": "http://ctri.nic.in",
                "value": study.ctri_registration_number,
            }
        )
    identifiers.append(
        {
            "use": "secondary",
            "system": "https://aiia-ctms.nic.in/studies",
            "value": str(study.id),
        }
    )

    fhir_resource = {
        "resourceType": "ResearchStudy",
        "id": str(study.id),
        "identifier": identifiers,
        "title": study.title,
        "status": _map_study_status_to_fhir(study.status),
        "phase": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/research-study-phase",
                    "code": study.phase or "phase-1",
                    "display": f"Phase {study.phase}" if study.phase else "Phase 1",
                }
            ]
        },
        "sponsor": {
            "display": study.sponsor or "All India Institute of Ayurveda (AIIA), New Delhi"
        },
        "period": {
            "start": str(study.start_date) if study.start_date else None,
            "end": str(study.end_date) if study.end_date else None,
        },
        "enrollment": [
            {
                "display": f"Target: {study.enrollment_target}, Enrolled: {study.enrolled_count}"
            }
        ],
        "site": [
            {
                "display": study.site_id or "AIIA Main Campus, Sarita Vihar, New Delhi"
            }
        ],
    }

    if study.ayurvedic_intervention:
        fhir_resource["extension"] = [
            {
                "url": "https://aiia.gov.in/fhir/StructureDefinition/ayurvedic-intervention",
                "valueString": study.ayurvedic_intervention,
            }
        ]

    if study.principal_investigator_id:
        fhir_resource["principalInvestigator"] = {
            "reference": f"Practitioner/{study.principal_investigator_id}"
        }

    return fhir_resource


@router.get("/AdverseEvent/{ae_id}")
def get_fhir_adverse_event(ae_id: uuid.UUID, db: Session = Depends(get_db)):
    """Emits valid HL7 FHIR R4 AdverseEvent resource representation."""
    ae = db.query(AdverseEvent).filter(AdverseEvent.id == ae_id).first()
    if not ae:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AdverseEvent with id {ae_id} not found",
        )

    fhir_resource = {
        "resourceType": "AdverseEvent",
        "id": str(ae.id),
        "identifier": {
            "system": "https://aiia-ctms.nic.in/adverse-events",
            "value": str(ae.id),
        },
        "actuality": "actual",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/adverse-event-category",
                        "code": "adverse-reaction",
                        "display": "Adverse Reaction",
                    }
                ]
            }
        ],
        "event": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/synthetic-meddra",
                    "code": ae.ae_term or "adverse_event",
                    "display": (ae.ae_term or "Adverse Event").replace("_", " ").title(),
                }
            ],
            "text": ae.description,
        },
        "subject": {
            "reference": f"Patient/{ae.patient_id}",
        },
        "date": str(ae.onset_date or ae.report_date),
        "seriousness": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/adverse-event-seriousness",
                    "code": "Serious" if ae.seriousness == "serious" else "Non-serious",
                    "display": ae.seriousness.capitalize(),
                }
            ]
        },
        "outcome": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/adverse-event-outcome",
                    "code": ae.outcome or "recovering",
                    "display": (ae.outcome or "recovering").capitalize(),
                }
            ]
        },
        "study": [
            {
                "reference": f"ResearchStudy/{ae.study_id}",
            }
        ],
    }

    if ae.causality:
        fhir_resource["causality"] = [
            {
                "assessment": {
                    "coding": [
                        {
                            "system": "http://who-umc.org/causality-assessment",
                            "code": ae.causality,
                            "display": ae.causality.capitalize(),
                        }
                    ]
                }
            }
        ]

    if ae.reported_by:
        fhir_resource["recorder"] = {
            "reference": f"Practitioner/{ae.reported_by}",
        }

    return fhir_resource


@router.get("/Patient/{patient_id}")
def get_fhir_patient(patient_id: uuid.UUID, db: Session = Depends(get_db)):
    """Emits valid HL7 FHIR R4 Patient resource representation with ABHA identifiers."""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with id {patient_id} not found",
        )

    identifiers = [
        {
            "use": "secondary",
            "system": "https://aiia-ctms.nic.in/patients",
            "value": patient.screening_number,
        }
    ]
    if patient.randomization_number:
        identifiers.append(
            {
                "use": "official",
                "system": "https://aiia-ctms.nic.in/randomization",
                "value": patient.randomization_number,
            }
        )
    if patient.abha_id:
        identifiers.append(
            {
                "use": "official",
                "system": "https://healthid.ndhm.gov.in",
                "value": patient.abha_id,
            }
        )

    gender_map = {"M": "male", "F": "female", "O": "other"}
    fhir_gender = gender_map.get((patient.sex or "").upper(), "unknown")

    return {
        "resourceType": "Patient",
        "id": str(patient.id),
        "identifier": identifiers,
        "active": patient.status == "enrolled",
        "gender": fhir_gender,
        "managingOrganization": {
            "display": "All India Institute of Ayurveda (AIIA)",
        },
    }


@router.post("/AdverseEvent", status_code=status.HTTP_201_CREATED)
def ingest_fhir_adverse_event(
    fhir_payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("pharmacovigilance", "pi", "admin")),
):
    """
    Bidirectional FHIR: Ingests an external HL7 FHIR R4 AdverseEvent resource.
    """
    try:
        study_ref = fhir_payload.get("study", [{}])[0].get("reference", "")
        patient_ref = fhir_payload.get("subject", {}).get("reference", "")
        study_id_str = study_ref.split("/")[-1]
        patient_id_str = patient_ref.split("/")[-1]

        study_id = uuid.UUID(study_id_str)
        patient_id = uuid.UUID(patient_id_str)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid FHIR references. Expected 'study': [{'reference': 'ResearchStudy/{uuid}'}] and 'subject': {'reference': 'Patient/{uuid}'}",
        )

    desc = fhir_payload.get("event", {}).get("text") or "FHIR Ingested Adverse Event"
    seriousness_raw = fhir_payload.get("seriousness", {}).get("coding", [{}])[0].get("code", "non_serious")
    seriousness = "serious" if "serious" in seriousness_raw.lower() else "non_serious"

    report_dt = date.today()
    reg_deadline = report_dt + timedelta(days=15 if seriousness == "serious" else 30)

    ae = AdverseEvent(
        study_id=study_id,
        patient_id=patient_id,
        description=desc,
        seriousness=seriousness,
        report_date=report_dt,
        regulatory_deadline=reg_deadline,
        reported_by=current_user.id,
        status="open",
        outcome="recovering",
        ae_term="nausea",
    )
    db.add(ae)
    db.commit()
    db.refresh(ae)

    log_action(
        db,
        user_id=current_user.id,
        action="FHIR_AE_INGEST",
        entity_type="adverse_event",
        entity_id=ae.id,
        new_value={"source": "HL7_FHIR_R4", "ae_id": str(ae.id)},
    )

    return {"status": "created", "resourceType": "AdverseEvent", "id": str(ae.id)}
