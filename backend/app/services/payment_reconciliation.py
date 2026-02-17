"""
Payment Reconciliation Service
Handles stuck/orphaned payments due to webhook failures or network issues
Runs daily at 2 AM IST to reconcile payments stuck in 'authorized' state
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from typing import List, Dict, Any
import razorpay
from app.db.mongo import MongoDB
from app.core.config import settings
import structlog

logger = structlog.get_logger()


async def reconcile_stuck_payments():
    """
    Daily reconciliation job: Find payments stuck in 'authorized' or 'created' 
    state for >24 hours and verify actual status with Razorpay API.
    
    This prevents "ghost bookings" where users pay but don't get premium tier
    due to webhook failures or network issues.
    """
    db = MongoDB.get_database()
    payments_collection = db["payments"]
    
    # Find payments stuck for more than 24 hours
    cutoff = datetime.utcnow() - timedelta(hours=24)
    stuck_payments = await payments_collection.find({
        "status": {"$in": ["authorized", "created"]},
        "created_at": {"$lt": cutoff}
    }).to_list(None)
    
    if not stuck_payments:
        logger.info("Reconciliation: No stuck payments found")
        return
    
    logger.info(f"Reconciliation: Found {len(stuck_payments)} stuck payments")
    
    # Initialize Razorpay client
    client = razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))
    
    reconciled_count = 0
    failed_count = 0
    
    for payment in stuck_payments:
        try:
            payment_id = payment.get("payment_id")
            if not payment_id:
                logger.warning(f"Payment {payment.get('_id')} has no payment_id, skipping")
                continue
            
            # Fetch actual status from Razorpay
            razorpay_payment = client.payment.fetch(payment_id)
            actual_status = razorpay_payment.get("status")
            
            logger.info(
                f"Payment {payment_id}: DB status={payment['status']}, "
                f"Razorpay status={actual_status}"
            )
            
            if actual_status == "captured":
                # Payment was successful but webhook was missed
                from app.api.routes.webhooks import handle_payment_captured
                await handle_payment_captured({
                    "payment": {"entity": razorpay_payment}
                })
                reconciled_count += 1
                logger.info(f"[SUCCESS] Reconciled successful payment: {payment_id}")
            
            elif actual_status == "failed":
                # Mark as failed
                await payments_collection.update_one(
                    {"payment_id": payment_id},
                    {
                        "$set": {
                            "status": "failed",
                            "reconciled_at": datetime.utcnow(),
                            "error_description": razorpay_payment.get("error_description", "Unknown error")
                        }
                    }
                )
                failed_count += 1
                logger.info(f"[FAILED] Marked payment as failed: {payment_id}")
            
            elif actual_status == "refunded":
                # Handle refund
                await payments_collection.update_one(
                    {"payment_id": payment_id},
                    {
                        "$set": {
                            "status": "refunded",
                            "reconciled_at": datetime.utcnow()
                        }
                    }
                )
                logger.info(f"💰 Marked payment as refunded: {payment_id}")
            
            else:
                # Still pending or other status - log for manual review
                logger.warning(
                    f"Payment {payment_id} has unexpected status: {actual_status}. "
                    f"Manual review required."
                )
        
        except razorpay.errors.BadRequestError as e:
            # Payment ID doesn't exist in Razorpay
            logger.error(f"Payment {payment.get('payment_id')} not found in Razorpay: {e}")
        
        except Exception as e:
            logger.error(
                f"Reconciliation error for payment {payment.get('payment_id')}: {e}",
                exc_info=True
            )
    
    # Log summary
    logger.info(
        f"Reconciliation complete: {reconciled_count} reconciled, "
        f"{failed_count} marked failed, {len(stuck_payments)} total processed"
    )


def init_reconciliation_scheduler(app):
    """
    Initialize APScheduler for daily payment reconciliation.
    Runs at 2 AM IST every day to minimize impact on users.
    
    Args:
        app: FastAPI application instance
    """
    scheduler = AsyncIOScheduler()
    
    # Schedule daily reconciliation at 2 AM IST
    scheduler.add_job(
        reconcile_stuck_payments,
        'cron',
        hour=2,
        minute=0,
        timezone='Asia/Kolkata',
        id='payment_reconciliation',
        replace_existing=True,
        misfire_grace_time=3600  # Allow 1 hour grace period if server was down
    )
    
    scheduler.start()
    logger.info("[SCHEDULER] Payment reconciliation scheduler started (runs daily at 2 AM IST)")
    
    return scheduler
