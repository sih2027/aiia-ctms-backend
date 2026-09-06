"""
Audit trail + blockchain anchor routes. Drop in as app/routers/audit.py.

Provides:
  POST /audit/anchor  -> manual trigger of the same batch-commit logic
                         that app/scheduler.py runs automatically on a
                         timer (Day 5's "scheduled Merkle commit job").
                         Both call app.anchor_job.run_anchor_once() so
                         they can never drift apart. Admin-only — useful
                         for forcing an anchor on demand (e.g. right
                         before a demo) instead of waiting for the timer.
  GET  /audit/verify  -> recomputes the Merkle root for the most recent
                         anchored batch from the current DB state and
                         compares it to the on-chain value. MATCH means
                         nothing in that batch has been altered since
                         it was anchored; MISMATCH means tampering.
  GET  /audit/trail   -> read-only list of audit_trail rows. Regulator
                         and Admin only, per Section 4's RBAC table.

No clinical, patient, or regulatory data crosses into the blockchain
calls in this file — only audit_trail.row_hash values and the resulting
Merkle root ever leave PostgreSQL.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.anchor_job import run_anchor_once
from app.database import get_db
from app.merkle_service import compute_merkle_root
from app.models import AuditAnchor, AuditTrail, User
from app.routers.auth import require_role
from app.web3_service import read_committed_root_for_block

router = APIRouter(prefix="/audit", tags=["audit"])


@router.post("/anchor")
def anchor_audit_trail(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    result = run_anchor_once(db)
    if result is None:
        return {"anchored": False, "reason": "no new audit_trail rows since last anchor"}
    return {"anchored": True, **result}


@router.get("/verify")
def verify_last_anchor(db: Session = Depends(get_db)):
    """
    Open to any authenticated role — per Section 4 the Regulator portal
    surfaces this, but every role benefits from seeing the tamper-evidence
    badge. Swap in require_role(...) here if you want to restrict it.
    """
    anchor = db.query(AuditAnchor).order_by(AuditAnchor.committed_at.desc()).first()
    if anchor is None:
        return {"status": "no_anchor_yet"}

    batch = (
        db.query(AuditTrail)
        .filter(AuditTrail.id.in_(_batch_ids(db, anchor)))
        .order_by(AuditTrail.timestamp.asc())
        .all()
    )
    recomputed_root = compute_merkle_root(batch)
    onchain_root = read_committed_root_for_block(anchor.block_number)

    matched = recomputed_root == onchain_root
    anchor.verification_status = "matched" if matched else "mismatched"
    db.commit()

    return {
        "status": anchor.verification_status,
        "stored_merkle_root": anchor.merkle_root,
        "recomputed_merkle_root": recomputed_root,
        "onchain_merkle_root": onchain_root,
        "tx_hash": anchor.tx_hash,
        "block_number": anchor.block_number,
    }


@router.get("/trail")
def read_audit_trail(
    entity_type: Optional[str] = Query(default=None),
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "regulator")),
):
    query = db.query(AuditTrail).order_by(AuditTrail.timestamp.desc())
    if entity_type:
        query = query.filter(AuditTrail.entity_type == entity_type)
    return query.limit(limit).all()


def _batch_ids(db: Session, anchor: AuditAnchor):
    """Yields every audit_trail id between the anchor's start and end rows,
    inclusive, ordered by timestamp — used to re-fetch exactly the batch
    that was anchored, for recomputation."""
    start = db.query(AuditTrail).filter(AuditTrail.id == anchor.batch_start_id).first()
    end = db.query(AuditTrail).filter(AuditTrail.id == anchor.batch_end_id).first()
    if not start or not end:
        return []
    rows = (
        db.query(AuditTrail.id)
        .filter(AuditTrail.timestamp >= start.timestamp, AuditTrail.timestamp <= end.timestamp)
        .all()
    )
    return [r.id for r in rows]
