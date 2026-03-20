"""
Claims Router for Nexurance AI
Core payout decision engine with MSTS trust scoring.
"""
import uuid
import time
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException

from models.schemas import (
    ClaimEvaluateRequest, ClaimEvaluateResponse, ClaimResponse,
    ClaimStatus, TrustScoreBreakdown
)
from models.db import db
from services.fraud_engine import compute_trust_score
from services import trigger_service
from services import payout_service
from services import notification_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/claims", tags=["Claims"])


@router.post("/evaluate", response_model=ClaimEvaluateResponse)
async def evaluate_claim(request: ClaimEvaluateRequest):
    """
    Core payout decision engine.
    1. Check external triggers (MANDATORY)
    2. Compute MSTS trust score
    3. Calculate payout amount
    4. Route based on trust score
    """
    worker_id = request.worker_id
    zone = request.zone
    telemetry = request.telemetry.model_dump() if request.telemetry else {}
    
    # Step 1: Check external triggers
    trigger_result = await trigger_service.check_disruption(zone, request.lat, request.lng)
    
    if trigger_result["trigger_level"] == 0:
        return ClaimEvaluateResponse(
            decision=ClaimStatus.BLOCKED,
            trust_score=0.0,
            payout_amount=0.0,
            reason="No external disruption verified in your zone",
        )
    
    # Step 2: Get worker info
    worker = await db.find_one("workers", {"_id": worker_id})
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    
    # Step 3: Compute MSTS trust score
    worker_history = worker.copy()
    worker_history["worker_id"] = worker_id
    
    # Get recent zone submissions for Louvain clustering
    event_submissions = await db.find_many(
        "claim_events",
        {"zone": zone},
        limit=50,
        sort_field="timestamp",
        sort_order=-1,
    )
    
    trust_result = compute_trust_score(
        telemetry=telemetry,
        worker_history=worker_history,
        zone_context={
            "claimed_zone": zone,
            "weather_data": trigger_result.get("weather_data", {}),
            "event_window_submissions": event_submissions,
            "claimed_payout": 0,
        },
    )
    
    score = trust_result["trust_score"]
    action = trust_result["action"]
    
    # Step 4: Check active policy
    policy = await db.find_one("policies", {"worker_id": worker_id, "active": True})
    if not policy:
        return ClaimEvaluateResponse(
            decision=ClaimStatus.BLOCKED,
            trust_score=score,
            payout_amount=0.0,
            reason="No active policy. Subscribe to get coverage.",
            msts_breakdown=TrustScoreBreakdown(**trust_result["breakdown"]),
        )
    
    # Step 5: Calculate payout amount
    hours_lost = min(trigger_result.get("disruption_duration_hours", 2), 3)
    hourly_avg = worker.get("avg_hourly_earnings", 111)
    raw_payout = hours_lost * hourly_avg * 0.80  # 80% coverage factor
    payout_amount = round(min(raw_payout, policy["coverage_limit"]), 2)
    
    # Determine disruption type
    disruption_type = "Unknown"
    if trigger_result.get("rain_alert"):
        disruption_type = "Heavy Rain"
    elif trigger_result.get("aqi_alert"):
        disruption_type = "AQI Spike"
    elif trigger_result.get("flood_alert"):
        disruption_type = "Flood Warning"
    elif trigger_result.get("curfew_alert"):
        disruption_type = "Curfew"
    
    # Step 6: Route based on trust score
    claim_id = f"claim_{uuid.uuid4().hex[:12]}"
    
    if action == "INSTANT_PAYOUT":
        # Process instant payout
        payout_id = await payout_service.process_payout(
            worker_id, payout_amount, worker.get("upi_id", ""),
            claim_id=claim_id,
        )
        
        # Send FCM notification
        await notification_service.send_payout_notification(
            worker.get("fcm_token", ""), payout_amount
        )
        
        # Store claim
        await _store_claim(
            claim_id, worker_id, zone, disruption_type,
            score, trust_result["breakdown"], payout_amount,
            ClaimStatus.APPROVED, payout_id,
            "Verified disruption — instant payout approved",
        )
        
        # Store claim event for Louvain clustering
        await _store_claim_event(worker_id, zone, telemetry)
        
        # Update worker trust score
        await db.update_one("workers", {"_id": worker_id}, {
            "$set": {"trust_score": score}
        })
        
        return ClaimEvaluateResponse(
            decision=ClaimStatus.APPROVED,
            trust_score=score,
            payout_amount=payout_amount,
            payout_id=payout_id,
            reason=f"Verified {disruption_type.lower()} disruption — Rs.{payout_amount:.0f} credited",
            msts_breakdown=TrustScoreBreakdown(**trust_result["breakdown"]),
        )
    
    elif action == "HOLD_2HR":
        await _store_claim(
            claim_id, worker_id, zone, disruption_type,
            score, trust_result["breakdown"], payout_amount,
            ClaimStatus.PENDING, None,
            "Under review — usually processed within 2 hours",
        )
        await _store_claim_event(worker_id, zone, telemetry)
        
        return ClaimEvaluateResponse(
            decision=ClaimStatus.PENDING,
            trust_score=score,
            payout_amount=payout_amount,
            reason="Processing — usually within 2 hours",
            msts_breakdown=TrustScoreBreakdown(**trust_result["breakdown"]),
        )
    
    else:
        await _store_claim(
            claim_id, worker_id, zone, disruption_type,
            score, trust_result["breakdown"], 0,
            ClaimStatus.BLOCKED, None,
            "Verification failed — trust score below threshold",
        )
        await _store_claim_event(worker_id, zone, telemetry)
        
        return ClaimEvaluateResponse(
            decision=ClaimStatus.BLOCKED,
            trust_score=score,
            payout_amount=0,
            reason="Verification failed",
            msts_breakdown=TrustScoreBreakdown(**trust_result["breakdown"]),
        )


@router.get("/{worker_id}/history")
async def get_claim_history(worker_id: str, limit: int = 20):
    """Get claim history for a worker."""
    claims = await db.find_many(
        "claims",
        {"worker_id": worker_id},
        limit=limit,
        sort_field="created_at",
        sort_order=-1,
    )
    return claims


async def _store_claim(
    claim_id, worker_id, zone, disruption_type,
    trust_score, breakdown, payout_amount,
    status, payout_id, reason
):
    """Store claim in database."""
    await db.insert_one("claims", {
        "_id": claim_id,
        "worker_id": worker_id,
        "zone": zone,
        "disruption_type": disruption_type,
        "trust_score": trust_score,
        "msts_breakdown": breakdown,
        "payout_amount": payout_amount,
        "status": status.value if hasattr(status, 'value') else status,
        "razorpay_payout_id": payout_id,
        "reason": reason,
        "created_at": datetime.utcnow(),
    })


async def _store_claim_event(worker_id, zone, telemetry):
    """Store claim event for Louvain clustering analysis."""
    await db.insert_one("claim_events", {
        "worker_id": worker_id,
        "zone": zone,
        "timestamp": time.time(),
        "ip_subnet": _get_subnet(telemetry.get("ip_address", "")),
        "device_model": telemetry.get("device_model", "unknown"),
    })


def _get_subnet(ip: str) -> str:
    """Extract /24 subnet from IP address."""
    parts = ip.split(".")
    if len(parts) >= 3:
        return ".".join(parts[:3])
    return ""
