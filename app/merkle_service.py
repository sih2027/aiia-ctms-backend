"""
Computes a Merkle root over a batch of audit_trail.row_hash values, per
Section 8's "Python Merkle Layer" spec. Drop in as app/merkle_service.py.

Only ever reads audit_trail.row_hash — no clinical or patient data ever
touches this module or ends up on-chain.
"""

from typing import List, Optional

from pymerkle import InmemoryTree
from sqlalchemy.orm import Session

from app.models import AuditAnchor, AuditTrail


def get_unanchored_rows(db: Session) -> List[AuditTrail]:
    """
    Rows created since the last anchor commit, oldest first. Uses the
    previous anchor's batch_end_id (a FK into audit_trail) as the
    watermark — if no anchor exists yet, every row is unanchored.
    """
    last_anchor = (
        db.query(AuditAnchor).order_by(AuditAnchor.committed_at.desc()).first()
    )
    query = db.query(AuditTrail).order_by(AuditTrail.timestamp.asc())

    if last_anchor and last_anchor.batch_end_id:
        watermark = (
            db.query(AuditTrail)
            .filter(AuditTrail.id == last_anchor.batch_end_id)
            .first()
        )
        if watermark:
            query = query.filter(AuditTrail.timestamp > watermark.timestamp)

    return query.all()


def compute_merkle_root(rows: List[AuditTrail]) -> Optional[str]:
    """
    Builds an in-memory Merkle tree over row_hash values, returns the
    root as a hex string (no 0x prefix). Returns None for an empty batch
    — callers should skip committing when there's nothing new to anchor.
    """
    if not rows:
        return None
    tree = InmemoryTree(algorithm="sha256")
    for row in rows:
        tree.append_entry(row.row_hash.encode())
    return tree.get_state().hex()
