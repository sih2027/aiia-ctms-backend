"""
Writes rows to audit_trail with the SHA-256 hash chain required by
Section 7/8: each row's row_hash is SHA-256 of the previous row's
content, so the chain is what the Merkle anchor layer anchors. The
very first row in the table hashes SHA-256("GENESIS").

Drop in as app/audit_log.py. This is a utility, not a route — import
log_action() into any router that creates/updates/deletes data and
call it after each action.

Note: wiring this into every existing route (Section 13 Day 3's
"audit_trail writing on every action") is a separate task from the
blockchain anchor layer itself. This file only provides the correctly
hash-chained writer that the anchor layer depends on having real rows
to batch.
"""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models import AuditTrail

GENESIS_HASH = hashlib.sha256(b"GENESIS").hexdigest()


def _canonical(value) -> str:
    """Deterministic JSON so the same content always hashes the same way."""
    return json.dumps(value, sort_keys=True, default=str)


def log_action(
    db: Session,
    *,
    user_id: Optional[uuid.UUID],
    action: str,
    entity_type: str,
    entity_id: Optional[uuid.UUID] = None,
    old_value: Optional[dict] = None,
    new_value: Optional[dict] = None,
) -> AuditTrail:
    """
    Appends one row to audit_trail, chaining its hash to the previous row.

    action: CREATE, UPDATE, DELETE_ATTEMPT, LOGIN, LOGOUT, STATUS_CHANGE,
            EXPORT, or AE_REPORT (per schema.sql's comment).
    entity_type: research_study, patient, adverse_event, visit_log,
                 milestone, or user.
    """
    previous = db.query(AuditTrail).order_by(AuditTrail.timestamp.desc()).first()
    previous_hash = previous.row_hash if previous else GENESIS_HASH

    content = _canonical(
        {
            "previous_hash": previous_hash,
            "user_id": str(user_id) if user_id else None,
            "action": action,
            "entity_type": entity_type,
            "entity_id": str(entity_id) if entity_id else None,
            "old_value": old_value,
            "new_value": new_value,
        }
    )
    row_hash = hashlib.sha256(content.encode()).hexdigest()

    row = AuditTrail(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_value=old_value,
        new_value=new_value,
        row_hash=row_hash,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
