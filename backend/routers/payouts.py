"""
Payouts Router for Nexurance AI
"""
import logging
from fastapi import APIRouter

from models.schemas import PayoutProcessRequest, PayoutResponse
from models.db import db
from services import payout_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/payouts", tags=["Payouts"])


@router.post("/process", response_model=PayoutResponse)
async def process_payout(request: PayoutProcessRequest):
    """Process a manual payout."""
    payout_id = await payout_service.process_payout(
        worker_id=request.worker_id,
        amount=request.amount,
        upi_id=request.upi_id,
        claim_id=request.claim_id,
    )
    
    return PayoutResponse(
        payout_id=payout_id,
        status="processed",
        amount=request.amount,
        worker_id=request.worker_id,
    )


@router.get("/{worker_id}/history")
async def get_payout_history(worker_id: str, limit: int = 20):
    """Get payout history for a worker."""
    payouts = await payout_service.get_payout_history(worker_id, limit)
    return payouts
