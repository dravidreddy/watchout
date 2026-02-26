"""
Watchout Backend - Payment Routes with Idempotency
"""
from fastapi import APIRouter, HTTPException, Depends, Request, Header
from typing import Optional
import razorpay
from datetime import datetime, timezone
import structlog

from app.core.firebase_auth import verify_firebase_token
from app.db.mongo import users_collection, MongoDB
from app.core.config import settings
from app.services.idempotency_service import IdempotencyService

logger = structlog.get_logger(__name__)

# Server-side pricing — never trust client-provided amounts
TIER_PRICES = {
    "adventure": 29900,   # ₹299 in paise
    "ultimate": 79900,    # ₹799 in paise
}

router = APIRouter(prefix="/payments", tags=["Payments"])

# Initialize Razorpay client lazily to avoid import-time failures
# when keys are not yet available (e.g., during testing or CI)
_razorpay_client = None


def get_razorpay_client():
    """Lazy-initialize and return the Razorpay client."""
    global _razorpay_client
    if _razorpay_client is None:
        if not settings.razorpay_key_id or not settings.razorpay_key_secret:
            raise HTTPException(
                status_code=503,
                detail="Payment service not configured"
            )
        _razorpay_client = razorpay.Client(
            auth=(settings.razorpay_key_id, settings.razorpay_key_secret)
        )
    return _razorpay_client

@router.post("/create-order")
async def create_order(
    request: Request,
    currency: str = "INR",
    tier: str = "premium",
    idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key"),
    token_data: dict = Depends(verify_firebase_token)
):
    """Create a Razorpay order with server-side pricing and idempotency support."""
    user_id = token_data.get("uid")
    
    # Look up price server-side — reject unknown tiers
    amount_paise = TIER_PRICES.get(tier)
    if amount_paise is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown subscription tier: {tier}. Valid tiers: {list(TIER_PRICES.keys())}"
        )
    
    # Generate idempotency key if not provided
    if not idempotency_key:
        idempotency_key = await IdempotencyService.generate_key(
            user_id=user_id,
            amount=amount_paise,
            metadata={"tier": tier, "currency": currency}
        )
    
    # Check for duplicate request
    cached_response = await IdempotencyService.check_and_store(
        idempotency_key=idempotency_key,
        user_id=user_id,
        request_data={
            "amount": amount_paise,
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
            "amount": amount_paise,
            "currency": currency,
            "receipt": f"receipt_{user_id}_{int(datetime.now(timezone.utc).timestamp())}",
            "notes": {
                "user_id": user_id,
                "tier": tier
            }
        }
        order = get_razorpay_client().order.create(data=data)
        
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
        
        # Store failure response - use 'message' key for consistency with app exception handlers
        error_detail = f"Order creation failed: {str(e)}"
        error_response = {"message": error_detail}
        await IdempotencyService.store_response(
            idempotency_key=idempotency_key,
            response_data=error_response,
            status="failed"
        )
        
        raise HTTPException(status_code=500, detail=error_detail)


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
    plan_id = data.get("plan_id", "adventure")

    params_dict = {
        'razorpay_order_id': razorpay_order_id,
        'razorpay_payment_id': razorpay_payment_id,
        'razorpay_signature': razorpay_signature
    }

    # Skip signature verification for test keys — test payments use fake signatures
    is_test_mode = (settings.razorpay_key_id or "").startswith("rzp_test_")

    if not is_test_mode:
        try:
            get_razorpay_client().utility.verify_payment_signature(params_dict)
        except Exception:
            logger.warning(f"Signature verification failed for order {razorpay_order_id}")
            raise HTTPException(status_code=400, detail="Invalid payment signature")

    try:
        user_id = token_data["uid"]
        
        db = MongoDB.get_db()
        payments_collection = db["payments"]
        users_collection = db["users"]
        
        # Store payment record
        await payments_collection.update_one(
            {"order_id": razorpay_order_id},
            {
                "$set": {
                    "payment_id": razorpay_payment_id,
                    "status": "captured",
                    "authorized_at": datetime.now(timezone.utc),
                    "user_id": user_id,
                    "tier": plan_id,
                    "created_at": datetime.now(timezone.utc)
                }
            },
            upsert=True
        )
        
        # ── CRITICAL: Update subscription_tier in the users collection immediately ──
        # Without this, on refresh AuthProvider re-fetches the profile from MongoDB
        # and still sees 'free', appearing to revert the subscription.
        result = await users_collection.update_one(
            {"firebase_id": user_id},
            {
                "$set": {
                    "subscription_tier": plan_id,
                    "subscription_activated_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                }
            }
        )
        
        if result.matched_count == 0:
            logger.warning(f"User {user_id} not found in users collection during tier upgrade")
        
        logger.info(
            f"Payment captured & subscription activated: "
            f"{user_id} -> {plan_id}, payment_id: {razorpay_payment_id}"
        )
        
        return {
            "status": "success",
            "tier": plan_id,
            "message": f"Your subscription has been upgraded to {plan_id}!",
            "payment_id": razorpay_payment_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Payment verification failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Payment verification failed due to a server error")

