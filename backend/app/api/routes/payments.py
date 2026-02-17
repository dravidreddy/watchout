"""
Watchout Backend - Payment Routes with Idempotency
"""
from fastapi import APIRouter, HTTPException, Depends, Request, Header
from typing import Optional
import razorpay
from datetime import datetime
import structlog

from app.core.firebase_auth import verify_firebase_token
from app.db.mongo import users_collection, MongoDB
from app.core.config import settings
from app.services.idempotency_service import IdempotencyService

logger = structlog.get_logger()

router = APIRouter(prefix="/payments", tags=["Payments"])

# Initialize Razorpay client using settings (NO FALLBACKS for security)
# If keys are missing, app will fail at startup (see main.py validation)
client = razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))

@router.post("/create-order")
async def create_order(
    amount: int,
    currency: str = "INR",
    tier: str = "premium",
    idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key"),
    token_data: dict = Depends(verify_firebase_token)
):
    """
    Create Razorpay order with idempotency support
    
    Args:
        amount: Amount in paise (e.g., 50000 for ₹500)
        currency: Currency code (default: INR)
        tier: Subscription tier
        idempotency_key: Optional client-provided idempotency key
        
    Returns:
        Razorpay order details or cached response for duplicate requests
    """
    user_id = token_data.get("uid")
    
    # Generate idempotency key if not provided
    if not idempotency_key:
        idempotency_key = await IdempotencyService.generate_key(
            user_id=user_id,
            amount=amount * 100,  # Convert to paise
            metadata={"tier": tier, "currency": currency}
        )
    
    # Check for duplicate request
    cached_response = await IdempotencyService.check_and_store(
        idempotency_key=idempotency_key,
        user_id=user_id,
        request_data={
            "amount": amount,
            "currency": currency,
            "tier": tier
        }
    )
    
    if cached_response:
        logger.info(f"Returning cached order for idempotency key: {idempotency_key}")
        return cached_response
    
    # Create new order
    try:
        data = {
            "amount": amount * 100,  # Amount in paise
            "currency": currency,
            "receipt": f"receipt_{user_id}_{int(datetime.utcnow().timestamp())}",
            "notes": {
                "user_id": user_id,
                "tier": tier
            }
        }
        order = client.order.create(data=data)
        
        response_data = {
            "order_id": order["id"],
            "amount": order["amount"],
            "currency": order["currency"],
            "key_id": settings.razorpay_key_id,
            "tier": tier
        }
        
        # Store response for future duplicate requests
        await IdempotencyService.store_response(
            idempotency_key=idempotency_key,
            response_data=response_data,
            status="success"
        )
        
        logger.info(f"Created new order: {order['id']} with idempotency key: {idempotency_key}")
        return response_data
        
    except Exception as e:
        logger.error(f"Order creation failed: {str(e)}")
        
        # Store failure response
        error_response = {"error": str(e)}
        await IdempotencyService.store_response(
            idempotency_key=idempotency_key,
            response_data=error_response,
            status="failed"
        )
        
        raise HTTPException(status_code=500, detail=f"Order creation failed: {str(e)}")


@router.post("/verify")
async def verify_payment(
    request: Request,
    token_data: dict = Depends(verify_firebase_token)
):
    """
    Fire-and-forget payment verification endpoint.
    
    CRITICAL: This endpoint returns immediately to prevent ghost bookings
    caused by network failures. The actual verification happens via webhooks
    and the reconciliation cron job.
    
    Flow:
    1. Client calls this endpoint after payment
    2. We queue the payment for background processing
    3. Return "processing" status immediately
    4. Webhook handler (payment.captured) or reconciliation job completes the update
    """
    data = await request.json()
    
    razorpay_order_id = data.get("razorpay_order_id")
    razorpay_payment_id = data.get("razorpay_payment_id")
    razorpay_signature = data.get("razorpay_signature")
    plan_id = data.get("plan_id", "premium")

    params_dict = {
        'razorpay_order_id': razorpay_order_id,
        'razorpay_payment_id': razorpay_payment_id,
        'razorpay_signature': razorpay_signature
    }

    try:
        # Quick signature verification (fast, local operation)
        client.utility.verify_payment_signature(params_dict)
        
        user_id = token_data["uid"]
        
        # Store payment as 'authorized' - webhook will update to 'captured'
        db = MongoDB.get_database()
        payments_collection = db["payments"]
        
        await payments_collection.update_one(
            {"order_id": razorpay_order_id},
            {
                "$set": {
                    "payment_id": razorpay_payment_id,
                    "status": "authorized",  # Webhook will change to 'captured'
                    "authorized_at": datetime.utcnow(),
                    "user_id": user_id,
                    "tier": plan_id,
                    "created_at": datetime.utcnow()
                }
            },
            upsert=True
        )
        
        logger.info(
            f"Payment authorized (pending webhook/reconciliation): "
            f"{user_id} -> {plan_id}, payment_id: {razorpay_payment_id}"
        )
        
        # Return immediately - don't wait for tier update
        return {
            "status": "processing",
            "message": "Payment verification in progress. Your subscription will be activated shortly.",
            "payment_id": razorpay_payment_id
        }
        
    except Exception as e:
        logger.error(f"Payment verification failed: {str(e)}")
        raise HTTPException(status_code=400, detail="Payment verification failed")
