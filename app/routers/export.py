"""
CDISC SDTM Data Export Router (Chunk 4).
Emits submission-ready CDISC SDTM v3.3 domain files:
- Demographics (DM) domain CSV
- Adverse Events (AE) domain CSV
- Inclusion / Exclusion (IE) domain CSV
- Define-XML 2.0 metadata stub package
"""

import csv
import hashlib
import io
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.audit_log import log_action
from app.database import get_db
from app.models import AdverseEvent, IECriteria, IEResult, Patient, ResearchStudy, User
from app.routers.auth import get_current_user, require_role

router = APIRouter(prefix="/export/sdtm", tags=["cdisc-export"])


def _sha256_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


@router.get("/dm/{study_id}")
@router.get("/dm")
def export_sdtm_dm_csv(
    study_id: Optional[uuid.UUID] = None,
    study_id_query: Optional[uuid.UUID] = Query(default=None, alias="study_id"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("pi", "admin", "regulator")),
):
    target_id = study_id or study_id_query
    if not target_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="study_id is required")

    study = db.query(ResearchStudy).filter(ResearchStudy.id == target_id).first()
    if not study:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Study not found")

    patients = (
        db.query(Patient)
        .filter(Patient.study_id == target_id)
        .order_by(Patient.created_at.asc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)

    # CDISC SDTM DM standard variable headers
    headers = [
        "STUDYID",
        "DOMAIN",
        "USUBJID",
        "SUBJID",
        "RFSTDTC",
        "RFENDTC",
        "SITEID",
        "AGE",
        "AGEU",
        "SEX",
        "ARMCD",
        "ARM",
        "COUNTRY",
    ]
    writer.writerow(headers)

    study_code = study.ctri_registration_number or f"AIIA-{str(study.id)[:8].upper()}"
    site_id = study.site_id or "AIIA-ND"

    for p in patients:
        usubjid = f"{study_code}-{p.screening_number}"
        subjid = p.screening_number
        rfstdtc = str(p.enrollment_date) if p.enrollment_date else ""
        rfendtc = str(study.end_date) if study.end_date else ""
        age = p.age if p.age is not None else ""
        sex = (p.sex or "U").upper()
        armcd = "AYUR-ACT" if p.status == "enrolled" else "SCRN"
        arm = (study.ayurvedic_intervention or "Active Ayurvedic Formulation") if p.status == "enrolled" else "Screening"

        writer.writerow(
            [study_code, "DM", usubjid, subjid, rfstdtc, rfendtc, site_id, age, "YEARS", sex, armcd, arm, "IND"]
        )

    csv_content = output.getvalue()
    file_hash = _sha256_hash(csv_content)
    filename = f"sdtm_dm_{study_code.replace('/', '_')}.csv"

    log_action(
        db,
        user_id=current_user.id,
        action="EXPORT",
        entity_type="research_study",
        entity_id=study.id,
        new_value={"format": "CDISC_SDTM_DM", "file_hash": file_hash},
    )

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "X-Export-SHA256": file_hash,
        },
    )


@router.get("/ae/{study_id}")
@router.get("/ae")
def export_sdtm_ae_csv(
    study_id: Optional[uuid.UUID] = None,
    study_id_query: Optional[uuid.UUID] = Query(default=None, alias="study_id"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("pi", "admin", "regulator", "pharmacovigilance")),
):
    target_id = study_id or study_id_query
    if not target_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="study_id is required")

    study = db.query(ResearchStudy).filter(ResearchStudy.id == target_id).first()
    if not study:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Study not found")

    events = (
        db.query(AdverseEvent)
        .filter(AdverseEvent.study_id == target_id)
        .order_by(AdverseEvent.report_date.asc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)

    # CDISC SDTM AE standard variable headers
    headers = [
        "STUDYID",
        "DOMAIN",
        "USUBJID",
        "AESEQ",
        "AETERM",
        "AEDECOD",
        "AESER",
        "AESEV",
        "AEREL",
        "AESTDTC",
        "AEENDTC",
        "AEOUT",
    ]
    writer.writerow(headers)

    study_code = study.ctri_registration_number or f"AIIA-{str(study.id)[:8].upper()}"

    for idx, e in enumerate(events, start=1):
        patient = db.query(Patient).filter(Patient.id == e.patient_id).first()
        screening_num = patient.screening_number if patient else "UNKNOWN"
        usubjid = f"{study_code}-{screening_num}"
        aeseq = idx
        aeterm = (e.ae_term or e.description).replace("_", " ").upper()
        aedecod = aeterm
        aeser = "Y" if e.seriousness == "serious" else "N"
        aesev = "SEVERE" if e.seriousness == "serious" else "MILD"
        aerel = (e.causality or "POSSIBLE").upper()
        aestdtc = str(e.onset_date) if e.onset_date else str(e.report_date)
        aeendtc = str(e.regulatory_deadline) if e.status == "resolved" else ""
        aeout = (e.outcome or "RECOVERING").upper()

        writer.writerow(
            [study_code, "AE", usubjid, aeseq, aeterm, aedecod, aeser, aesev, aerel, aestdtc, aeendtc, aeout]
        )

    csv_content = output.getvalue()
    file_hash = _sha256_hash(csv_content)
    filename = f"sdtm_ae_{study_code.replace('/', '_')}.csv"

    log_action(
        db,
        user_id=current_user.id,
        action="EXPORT",
        entity_type="research_study",
        entity_id=study.id,
        new_value={"format": "CDISC_SDTM_AE", "file_hash": file_hash},
    )

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "X-Export-SHA256": file_hash,
        },
    )


@router.get("/ie/{study_id}")
@router.get("/ie")
def export_sdtm_ie_csv(
    study_id: Optional[uuid.UUID] = None,
    study_id_query: Optional[uuid.UUID] = Query(default=None, alias="study_id"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("pi", "admin", "regulator")),
):
    target_id = study_id or study_id_query
    if not target_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="study_id is required")

    study = db.query(ResearchStudy).filter(ResearchStudy.id == target_id).first()
    if not study:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Study not found")

    study_code = study.ctri_registration_number or f"AIIA-{str(study.id)[:8].upper()}"

    # Query all IE results for patients in this study
    results = (
        db.query(IEResult, IECriteria, Patient)
        .join(IECriteria, IEResult.criterion_id == IECriteria.id)
        .join(Patient, IEResult.patient_id == Patient.id)
        .filter(IECriteria.study_id == target_id)
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)

    # CDISC SDTM IE standard variable headers
    headers = [
        "STUDYID",
        "DOMAIN",
        "USUBJID",
        "IESEQ",
        "IETESTCD",
        "IETEST",
        "IECAT",
        "IEORRES",
        "IESTRESC",
    ]
    writer.writerow(headers)

    for idx, (res, crit, pat) in enumerate(results, start=1):
        usubjid = f"{study_code}-{pat.screening_number}"
        ietestcd = f"{crit.criterion_type[:3].upper()}{crit.criterion_number:02d}"
        ietest = crit.description[:40]
        iecat = crit.criterion_type.upper()
        ieorres = "Y" if res.met else "N"
        iestresc = ieorres

        writer.writerow([study_code, "IE", usubjid, idx, ietestcd, ietest, iecat, ieorres, iestresc])

    csv_content = output.getvalue()
    file_hash = _sha256_hash(csv_content)
    filename = f"sdtm_ie_{study_code.replace('/', '_')}.csv"

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "X-Export-SHA256": file_hash,
        },
    )


@router.get("/define/{study_id}")
def export_define_xml(
    study_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("pi", "admin", "regulator")),
):
    """
    Generates CDISC Define-XML 2.0 metadata stub for study regulatory package.
    """
    study = db.query(ResearchStudy).filter(ResearchStudy.id == study_id).first()
    if not study:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Study not found")

    study_code = study.ctri_registration_number or f"AIIA-{str(study.id)[:8].upper()}"

    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<ODM xmlns="http://www.cdisc.org/ns/odm/v1.3"
     xmlns:def="http://www.cdisc.org/ns/def/v2.0"
     FileType="Snapshot"
     FileOID="DEFINE_XML_{study_code}"
     CreationDateTime="{study.created_at.isoformat()}">
  <Study OID="{study_code}">
    <GlobalVariables>
      <StudyName>{study.title}</StudyName>
      <StudyDescription>All India Institute of Ayurveda Clinical Trial Submission Package</StudyDescription>
      <ProtocolName>{study.phase or 'Phase 1/2'} Clinical Investigation Protocol</ProtocolName>
    </GlobalVariables>
    <MetaDataVersion OID="MDV.{study_code}" Name="CDISC SDTM v3.3 / Define-XML v2.0">
      <def:Standard Name="CDISC SDTM" Version="3.3" Status="Final"/>
      <ItemGroupDef OID="IG.DM" Name="DM" Repeating="No" Domain="DM" Purpose="Tabulation">
        <Description>Demographics Domain</Description>
      </ItemGroupDef>
      <ItemGroupDef OID="IG.AE" Name="AE" Repeating="Yes" Domain="AE" Purpose="Tabulation">
        <Description>Adverse Events Domain</Description>
      </ItemGroupDef>
      <ItemGroupDef OID="IG.IE" Name="IE" Repeating="Yes" Domain="IE" Purpose="Tabulation">
        <Description>Inclusion/Exclusion Criteria Domain</Description>
      </ItemGroupDef>
    </MetaDataVersion>
  </Study>
</ODM>"""

    return Response(
        content=xml_content,
        media_type="application/xml",
        headers={"Content-Disposition": f"attachment; filename=define_{study_code.replace('/', '_')}.xml"},
    )
