"""
Core "commit one Merkle batch" logic, shared by the manual POST /audit/anchor
endpoint (app/routers/audit.py) and the scheduled job (app/scheduler.py) —
written once here so the two never drift apart. Drop in as app/anchor_job.py.
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.merkle_service import compute_merkle_root, get_unanchored_rows
from app.models import AuditAnchor
from app.web3_service import commit_merkle_root


def run_anchor_once(db: Session) -> Optional[dict]:
    """
    Batches unanchored audit_trail rows, computes a Merkle root, commits
    it on-chain, and records the result in audit_anchor.

    Returns a dict describing what happened, or None if there was
    nothing new to anchor (callers should treat None as a normal,
    expected no-op — not an error).
    """
    rows = get_unanchored_rows(db)
    merkle_root = compute_merkle_root(rows)

    if merkle_root is None:
        return None

    chain_result = commit_merkle_root(merkle_root)

    anchor = AuditAnchor(
        batch_start_id=rows[0].id,
        batch_end_id=rows[-1].id,
        row_count=len(rows),
        merkle_root=merkle_root,
        chain="polygon-amoy-testnet",
        tx_hash=chain_result["tx_hash"],
        block_number=chain_result["block_number"],
        verification_status="pending",
    )
    db.add(anchor)
    db.commit()
    db.refresh(anchor)

    return {
        "row_count": anchor.row_count,
        "merkle_root": anchor.merkle_root,
        "tx_hash": anchor.tx_hash,
        "block_number": anchor.block_number,
    }
