"""
Payout Service for Nexurance AI
Razorpay Payout API integration with mock fallback for demo.
"""
import os
import time
import logging
from datetime import datetime
from typing import Optional

from models.db import db

logger = logging.getLogger(__name__)

DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
_razorpay_client = None


def _get_razorpay_client():
    """Lazy-initialize Razorpay client."""
    global _razorpay_client
    if _razorpay_client is not None:
        return _razorpay_client
    
    if DEMO_MODE:
        return None
    
    try:
        import razorpay
        key_id = os.getenv("RAZORPAY_KEY_ID", "")
        key_secret = os.getenv("RAZORPAY_KEY_SECRET", "")
        if key_id and key_secret and not key_id.startswith("rzp_test_demo"):
            _razorpay_client = razorpay.Client(auth=(key_id, key_secret))
            logger.info("✅ Razorpay client initialized")
            return _razorpay_client
    except ImportError:
        logger.warning("razorpay package not installed")
    except Exception as e:
        logger.warning(f"Razorpay init failed: {e}")
    
    return None


async def process_payout(
    worker_id: str,
    amount: float,
    upi_id: str,
    claim_id: str = ""
) -> str:
    """
    Process UPI payout via Razorpay (sandbox) or mock.
    amount is in Rs.
    """
    client = _get_razorpay_client()
    
    if client is not None:
        try:
            payout = client.payout.create({
                "account_number": os.getenv("RAZORPAY_ACCOUNT_NUMBER", ""),
                "fund_account": {
                    "account_type": "vpa",
                    "vpa": {"address": upi_id},
                    "contact": {
                        "name": worker_id,
                        "type": "vendor",
                    },
                },
                "amount": int(amount * 100),  # Convert to paise
                "currency": "INR",
                "mode": "UPI",
                "purpose": "payout",
                "queue_if_low_balance": True,
                "narration": "Nexurance AI Income Protection Payout",
            })
            
            payout_id = payout["id"]
            
            await db.insert_one("payouts", {
                "worker_id": worker_id,
                "claim_id": claim_id,
                "amount": amount,
                "razorpay_payout_id": payout_id,
                "status": payout.get("status", "processing"),
                "upi_id": upi_id,
                "created_at": datetime.utcnow(),
                "mock": False,
            })
            
            logger.info(f"💰 Razorpay payout processed: {payout_id} for ₹{amount}")
            return payout_id
            
        except Exception as e:
            logger.warning(f"Razorpay payout failed, using mock: {e}")
    
    # Mock payout for demo
    mock_id = f"mock_payout_{worker_id}_{int(time.time())}"
    
    await db.insert_one("payouts", {
        "_id": mock_id,
        "worker_id": worker_id,
        "claim_id": claim_id,
        "amount": amount,
        "razorpay_payout_id": mock_id,
        "status": "processed",
        "upi_id": upi_id,
        "created_at": datetime.utcnow(),
        "mock": True,
    })
    
    logger.info(f"💰 Mock payout processed: {mock_id} for ₹{amount}")
    return mock_id


async def get_payout_history(worker_id: str, limit: int = 20):
    """Get payout history for a worker."""
    return await db.find_many(
        "payouts",
        {"worker_id": worker_id},
        limit=limit,
        sort_field="created_at",
        sort_order=-1,
    )
