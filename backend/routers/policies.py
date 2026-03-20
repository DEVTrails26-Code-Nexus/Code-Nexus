"""
Policies Router for Nexurance AI
CRUD for insurance policies + premium calculation.
"""
import uuid
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException

from models.schemas import (
    PolicyCreate, PolicyResponse, PremiumCalculateRequest, PremiumResult
)
from models.db import db
from services.premium_engine import calculate_premium, COVERAGE_AMOUNTS
from services.trigger_service import get_weather_forecast

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Policies"])


@router.post("/premium/calculate", response_model=PremiumResult)
async def calculate_premium_endpoint(request: PremiumCalculateRequest):
    """Calculate personalized premium for a worker."""
    # Get worker history
    worker = await db.find_one("workers", {"_id": request.worker_id})
    if not worker:
        # Use defaults for new/unknown workers
        worker = {
            "consecutive_clean_weeks": 0,
            "avg_hourly_earnings": 111,
            "total_claims": 0,
        }
    
    # Get weather forecast for the zone
    forecast = get_weather_forecast(request.zone)
    
    # Calculate premium
    result = calculate_premium(
        zone=request.zone,
        worker_history=worker,
        weather_forecast=forecast,
    )
    
    return PremiumResult(
        recommended_plan=result["recommended"],
        starter_price=result["starter"],
        shield_price=result["shield"],
        max_price=result["max"],
        zone_risk_score=result["zone_risk"],
        weather_factor=result["weather_factor"],
        trust_discount=result["trust_discount"],
        coverage_amounts=COVERAGE_AMOUNTS,
    )


@router.post("/policies/", response_model=PolicyResponse)
async def create_policy(policy: PolicyCreate):
    """Create a new weekly policy after payment."""
    # Calculate week boundaries
    now = datetime.utcnow()
    week_start = now - timedelta(days=now.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
    
    # Deactivate any existing active policies
    existing = await db.find_many("policies", {
        "worker_id": policy.worker_id,
        "active": True,
    })
    for p in existing:
        await db.update_one("policies", {"_id": p["_id"]}, {"$set": {"active": False}})
    
    # Create new policy
    policy_id = f"policy_{uuid.uuid4().hex[:12]}"
    doc = {
        "_id": policy_id,
        "worker_id": policy.worker_id,
        "plan": policy.plan.value,
        "premium_paid": policy.premium_paid,
        "coverage_limit": policy.coverage_limit,
        "week_start": week_start,
        "week_end": week_end,
        "active": True,
        "razorpay_payment_id": policy.razorpay_payment_id or f"pay_demo_{uuid.uuid4().hex[:8]}",
        "created_at": now,
    }
    await db.insert_one("policies", doc)
    
    logger.info(f"📋 Policy created: {policy_id} ({policy.plan.value}) for worker {policy.worker_id}")
    
    return _policy_to_response(doc)


@router.get("/policies/{worker_id}/active", response_model=PolicyResponse)
async def get_active_policy(worker_id: str):
    """Get the active policy for a worker."""
    policy = await db.find_one("policies", {
        "worker_id": worker_id,
        "active": True,
    })
    if not policy:
        raise HTTPException(status_code=404, detail="No active policy found")
    return _policy_to_response(policy)


@router.get("/policies/{worker_id}/history")
async def get_policy_history(worker_id: str):
    """Get all policies for a worker."""
    policies = await db.find_many(
        "policies",
        {"worker_id": worker_id},
        sort_field="created_at",
        sort_order=-1,
    )
    return [_policy_to_response(p) for p in policies]


def _policy_to_response(doc: dict) -> PolicyResponse:
    """Convert policy document to response model."""
    return PolicyResponse(
        id=doc["_id"],
        worker_id=doc["worker_id"],
        plan=doc["plan"],
        premium_paid=doc["premium_paid"],
        coverage_limit=doc["coverage_limit"],
        week_start=doc["week_start"],
        week_end=doc["week_end"],
        active=doc.get("active", True),
        razorpay_payment_id=doc.get("razorpay_payment_id"),
        created_at=doc.get("created_at", datetime.utcnow()),
    )
