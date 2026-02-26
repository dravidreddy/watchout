"""
Razorpay Webhook Handler
Handles payment lifecycle events asynchronously
"""
from fastapi import APIRouter, HTTPException, Request, Header
from typing import Optional
import hmac
import hashlib
from datetime import datetime, timezone
from app.core.config import settings
from app.db.mongo import MongoDB
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


async def verify_razorpay_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Verify Razorpay webhook signature
    
    Args:
        payload: Raw request body
        signature: X-Razorpay-Signature header
        secret: Webhook secret from Razorpay dashboard
        
    Returns:
        True if signature is valid
    """
    expected_signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, signature)


@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None)
):
    """
    Handle Razorpay webhook events
    
    Supported events:
    - payment.authorized
    - payment.captured
    - payment.failed
    - order.paid
    - refund.created
    """
    # Get raw body for signature verification
    body = await request.body()
    
    # Verify webhook signature
    webhook_secret = getattr(settings, 'razorpay_webhook_secret', None)
    if webhook_secret and x_razorpay_signature:
        is_valid = await verify_razorpay_signature(
            body, 
            x_razorpay_signature, 
            webhook_secret
        )
        if not is_valid:
            logger.error("Invalid webhook signature")
            raise HTTPException(status_code=400, detail="Invalid signature")
    elif settings.app_env != "development":
        # In production, signature verification is mandatory
        logger.error("Webhook signature verification skipped — missing secret or signature in production")
        raise HTTPException(status_code=400, detail="Webhook signature required in production")
    
    # Parse event
    event_data = await request.json()
    event_type = event_data.get("event")
    payload = event_data.get("payload", {})
    
    logger.info(f"Received webhook: {event_type}", event_data=event_data)
    
    # Route to appropriate handler
    try:
        if event_type == "payment.captured":
            await handle_payment_captured(payload)
        elif event_type == "payment.failed":
            await handle_payment_failed(payload)
        elif event_type == "payment.authorized":
            await handle_payment_authorized(payload)
        elif event_type == "order.paid":
            await handle_order_paid(payload)
        elif event_type == "refund.created":
            await handle_refund_created(payload)
        else:
            logger.warning(f"Unhandled webhook event: {event_type}")
    
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}", exc_info=True)
        # Return 200 to prevent Razorpay retries for processing errors
        # Log the error for manual review
        await log_webhook_error(event_type, event_data, str(e))
    
    return {"status": "ok"}


async def handle_payment_captured(payload: dict):
    """Handle successful payment capture"""
    payment = payload.get("payment", {}).get("entity", {})
    payment_id = payment.get("id")
    order_id = payment.get("order_id")
    amount = payment.get("amount")
    user_id = payment.get("notes", {}).get("user_id")
    tier = payment.get("notes", {}).get("tier", "premium")
    
    logger.info(f"Payment captured: {payment_id} for order: {order_id}")
    
    db = MongoDB.get_db()
    users_collection = db["users"]
    payments_collection = db["payments"]
    
    # Update payment record
    await payments_collection.update_one(
        {"order_id": order_id},
        {
            "$set": {
                "payment_id": payment_id,
                "status": "captured",
                "captured_at": datetime.now(timezone.utc),
                "amount": amount
            }
        },
        upsert=True
    )
    
    # Update user subscription
    if user_id:
        await users_collection.update_one(
            {"firebase_id": user_id},
            {
                "$set": {
                    "subscription_tier": tier,
                    "subscription_status": "active",
                    "subscription_updated_at": datetime.now(timezone.utc)
                }
            }
        )
        logger.info(f"Updated subscription for user: {user_id} to tier: {tier}")


async def handle_payment_failed(payload: dict):
    """Handle failed payment"""
    payment = payload.get("payment", {}).get("entity", {})
    payment_id = payment.get("id")
    order_id = payment.get("order_id")
    error_code = payment.get("error_code")
    error_description = payment.get("error_description")
    
    logger.warning(f"Payment failed: {payment_id}, Error: {error_code} - {error_description}")
    
    db = MongoDB.get_db()
    payments_collection = db["payments"]
    
    # Update payment record
    await payments_collection.update_one(
        {"order_id": order_id},
        {
            "$set": {
                "payment_id": payment_id,
                "status": "failed",
                "failed_at": datetime.now(timezone.utc),
                "error_code": error_code,
                "error_description": error_description
            }
        },
        upsert=True
    )


async def handle_payment_authorized(payload: dict):
    """Handle payment authorization (before capture)"""
    payment = payload.get("payment", {}).get("entity", {})
    payment_id = payment.get("id")
    order_id = payment.get("order_id")
    
    logger.info(f"Payment authorized: {payment_id}")
    
    db = MongoDB.get_db()
    payments_collection = db["payments"]
    
    await payments_collection.update_one(
        {"order_id": order_id},
        {
            "$set": {
                "payment_id": payment_id,
                "status": "authorized",
                "authorized_at": datetime.now(timezone.utc)
            }
        },
        upsert=True
    )


async def handle_order_paid(payload: dict):
    """Handle order paid event"""
    order = payload.get("order", {}).get("entity", {})
    order_id = order.get("id")
    
    logger.info(f"Order paid: {order_id}")
    
    db = MongoDB.get_db()
    payments_collection = db["payments"]
    
    await payments_collection.update_one(
        {"order_id": order_id},
        {
            "$set": {
                "status": "paid",
                "paid_at": datetime.now(timezone.utc)
            }
        },
        upsert=True
    )


async def handle_refund_created(payload: dict):
    """Handle refund creation"""
    refund = payload.get("refund", {}).get("entity", {})
    refund_id = refund.get("id")
    payment_id = refund.get("payment_id")
    amount = refund.get("amount")
    
    logger.info(f"Refund created: {refund_id} for payment: {payment_id}")
    
    db = MongoDB.get_db()
    payments_collection = db["payments"]
    
    await payments_collection.update_one(
        {"payment_id": payment_id},
        {
            "$set": {
                "refund_id": refund_id,
                "refund_amount": amount,
                "refund_status": "processed",
                "refunded_at": datetime.now(timezone.utc)
            }
        }
    )


async def log_webhook_error(event_type: str, event_data: dict, error: str):
    """Log webhook processing errors for manual review"""
    db = MongoDB.get_db()
    webhook_errors = db["webhook_errors"]
    
    await webhook_errors.insert_one({
        "event_type": event_type,
        "event_data": event_data,
        "error": error,
        "created_at": datetime.now(timezone.utc),
        "resolved": False
    })
