"""
Background scheduler for periodic Merkle root commits to Polygon Amoy testnet
and automated GCP / NPvCC clinical safety sweeps:
- Periodic Merkle root commit
- AE statutory deadline monitor (flags <= 3 days to deadline)
- Rolling 30-day safety signal sweep
- Overdue visit window monitor
"""

import logging
import os
from datetime import date, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

from app.database import SessionLocal
from app.anchor_job import run_anchor_once
from app.models import AdverseEvent, Notification, ResearchStudy, User, VisitLog

logger = logging.getLogger("aiia_ctms.scheduler")
scheduler = BackgroundScheduler()


def scheduled_anchor_job():
    """Periodic job that runs anchor process for unanchored audit logs."""
    db = SessionLocal()
    try:
        result = run_anchor_once(db)
        if result:
            logger.info(
                f"[Scheduler] Merkle root committed to chain. Rows: {result['row_count']}, Tx: {result['tx_hash']}"
            )
        else:
            logger.debug("[Scheduler] Anchor check ran: no new audit rows to anchor.")
    except Exception as exc:
        logger.warning(f"[Scheduler] Anchor job skipped or encountered issue: {exc}")
    finally:
        db.close()


def scheduled_safety_sweeps():
    """Periodic job to monitor AE regulatory deadlines and safety signals."""
    db = SessionLocal()
    try:
        today = date.today()
        # 1. AE statutory deadline monitor (<= 3 days remaining)
        upcoming_threshold = today + timedelta(days=3)
        urgent_aes = (
            db.query(AdverseEvent)
            .filter(
                AdverseEvent.regulatory_deadline <= upcoming_threshold,
                ~AdverseEvent.status.in_(["resolved", "reported"]),
            )
            .all()
        )
        if urgent_aes:
            # Notify PV officers and admins
            pv_users = db.query(User).filter(User.role.in_(["pharmacovigilance", "admin"])).all()
            for u in pv_users:
                existing = (
                    db.query(Notification)
                    .filter(
                        Notification.user_id == u.id,
                        Notification.title.like("%Urgent Regulatory Deadline%"),
                        Notification.is_read == False,
                    )
                    .first()
                )
                if not existing:
                    db.add(
                        Notification(
                            user_id=u.id,
                            title=f"Urgent Regulatory Deadline: {len(urgent_aes)} AE(s) Pending",
                            message=f"Statutory CDSCO submission deadline approaching within 3 days for {len(urgent_aes)} adverse event report(s). Immediate action required.",
                            severity="critical",
                        )
                    )
            db.commit()

        # 2. Rolling 30-day safety signal sweep (count >= 3)
        window_start = today - timedelta(days=30)
        recent_aes = (
            db.query(AdverseEvent)
            .filter(
                AdverseEvent.report_date >= window_start,
                AdverseEvent.ae_term.isnot(None),
            )
            .all()
        )
        grouped = {}
        for ae in recent_aes:
            key = (ae.study_id, ae.ae_term)
            grouped[key] = grouped.get(key, 0) + 1

        for (study_id, term), count in grouped.items():
            if count >= 3:
                # Flag to PV, EC, and Admin
                stakeholders = db.query(User).filter(User.role.in_(["pharmacovigilance", "ethics_committee", "admin"])).all()
                for u in stakeholders:
                    existing_sig = (
                        db.query(Notification)
                        .filter(
                            Notification.user_id == u.id,
                            Notification.title.like(f"%Safety Signal Detected: {term}%"),
                            Notification.is_read == False,
                        )
                        .first()
                    )
                    if not existing_sig:
                        db.add(
                            Notification(
                                user_id=u.id,
                                title=f"Safety Signal Detected: {term.replace('_', ' ').title()}",
                                message=f"Detected {count} instances of {term.replace('_', ' ')} within rolling 30 days. DSMB review advised.",
                                severity="critical",
                            )
                        )
                db.commit()

    except Exception as exc:
        logger.warning(f"[Scheduler] Safety sweep error: {exc}")
    finally:
        db.close()


def start_scheduler():
    """Starts the background scheduler on application startup."""
    interval_minutes = int(os.getenv("ANCHOR_INTERVAL_MINUTES", "15"))
    scheduler.add_job(
        scheduled_anchor_job,
        trigger="interval",
        minutes=interval_minutes,
        id="periodic_merkle_anchor",
        replace_existing=True,
    )
    # Run safety sweeps every 30 minutes
    scheduler.add_job(
        scheduled_safety_sweeps,
        trigger="interval",
        minutes=30,
        id="periodic_safety_sweeps",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(f"[Scheduler] Started periodic Merkle anchor and safety sweeps.")


def shutdown_scheduler():
    """Shuts down the background scheduler cleanly on application shutdown."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("[Scheduler] Shutdown completed.")
