"""
Triggers Router for Nexurance AI
Weather/AQI/IMD trigger checks + demo simulation endpoint.
"""
import logging
import time
from datetime import datetime
from fastapi import APIRouter

from models.schemas import TriggerCheckRequest, TriggerResult, SimulateRainstormRequest
from models.db import db
from services import trigger_service
from services import notification_service
from services.fraud_engine import compute_trust_score
from services import payout_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Triggers"])


@router.post("/triggers/check", response_model=TriggerResult)
async def check_triggers(request: TriggerCheckRequest):
    """Check all disruption triggers for a zone."""
    result = await trigger_service.check_disruption(
        request.zone, request.lat, request.lng
    )
    return TriggerResult(**{k: v for k, v in result.items() if k in TriggerResult.model_fields})


@router.get("/triggers/zone/{zone_id}")
async def get_zone_trigger_status(zone_id: str):
    """Get current trigger status for a zone."""
    result = trigger_service.get_zone_status(zone_id)
    return result


@router.get("/triggers/overrides")
async def get_active_overrides():
    """Get all active trigger overrides (for admin dashboard)."""
    return trigger_service.get_active_overrides()


@router.delete("/triggers/overrides")
async def clear_all_overrides():
    """Clear all active trigger overrides so live APIs work again."""
    trigger_service._trigger_overrides.clear()
    return {"status": "cleared"}


@router.post("/demo/simulate-rainstorm")
async def simulate_rainstorm(request: SimulateRainstormRequest):
    """
    DEMO ENDPOINT: Simulate a rainstorm for hackathon presentation.
    Sets rainfall to specified mm/hr for a zone and triggers full claim
    evaluation for all active policy holders in that zone.
    """
    zone = request.zone
    logger.info(f"🌧️ === SIMULATING RAINSTORM === Zone: {zone}, Rainfall: {request.rainfall_mm_hr}mm/hr")
    
    # Step 1: Set trigger override
    trigger_service.set_trigger_override(zone, {
        "rainfall_mm_hr": request.rainfall_mm_hr,
        "aqi": 0,
        "flood_alert": request.rainfall_mm_hr > 100,
        "duration_hours": request.duration_hours,
        "duration_seconds": int(request.duration_hours * 3600),
    })
    
    # Step 2: Find all workers with active policies in this zone
    zone_key = zone.lower().replace(" ", "_")
    active_policies = await db.find_many("policies", {"active": True})
    
    results = []
    
    for policy in active_policies:
        worker = await db.find_one("workers", {"_id": policy["worker_id"]})
        if not worker:
            continue
        
        worker_zone = worker.get("zone", "").lower().replace(" ", "_")
        if worker_zone != zone_key:
            continue
        
        worker_id = worker["_id"]
        
        # Send disruption alert
        await notification_service.send_disruption_alert(
            worker.get("fcm_token", ""),
            zone,
            "Red Rain",
        )
        
        # Build telemetry (simulate real device data)
        telemetry = {
            "accelerometer": [0.3, -0.1, 9.7],
            "gyroscope": [0.02, -0.01, 0.05],
            "barometer_hpa": 1005.2,  # Low pressure = rain
            "cell_towers": [{"id": "40445"}],
            "wifi_ssids": ["JioFiber_5G", "ACT_Broad"],
            "ip_address": "203.122.45.67",
            "is_mock_location": False,
            "network_available": True,
            "device_integrity_token": "demo_integrity_ok",
            "gps_readings": [],
            "screen_state": "on",
            "device_model": worker.get("device_model", "Samsung Galaxy M31"),
        }
        
        # Compute MSTS trust score
        worker_history = worker.copy()
        worker_history["worker_id"] = worker_id
        
        event_submissions = await db.find_many(
            "claim_events", {"zone": zone}, limit=50,
        )
        
        trust_result = compute_trust_score(
            telemetry=telemetry,
            worker_history=worker_history,
            zone_context={
                "claimed_zone": zone,
                "weather_data": {
                    "rain_confirmed": True,
                    "rainfall_mm_hr": request.rainfall_mm_hr,
                },
                "event_window_submissions": event_submissions,
            },
        )
        
        score = trust_result["trust_score"]
        action = trust_result["action"]
        
        # Calculate payout
        hours_lost = min(request.duration_hours, 3)
        hourly_avg = worker.get("avg_hourly_earnings", 111)
        raw_payout = hours_lost * hourly_avg * 0.80
        payout_amount = round(min(raw_payout, policy["coverage_limit"]), 2)
        
        # Process based on trust tier
        import uuid
        claim_id = f"claim_{uuid.uuid4().hex[:12]}"
        
        if action == "INSTANT_PAYOUT":
            payout_id = await payout_service.process_payout(
                worker_id, payout_amount, worker.get("upi_id", ""),
                claim_id=claim_id,
            )
            
            await notification_service.send_payout_notification(
                worker.get("fcm_token", ""), payout_amount
            )
            
            await db.insert_one("claims", {
                "_id": claim_id,
                "worker_id": worker_id,
                "zone": zone,
                "disruption_type": "Heavy Rain",
                "trust_score": score,
                "msts_breakdown": trust_result["breakdown"],
                "payout_amount": payout_amount,
                "status": "APPROVED",
                "razorpay_payout_id": payout_id,
                "reason": "Simulated rainstorm — verified and approved",
                "created_at": datetime.utcnow(),
                "simulated": True,
            })
            
            results.append({
                "worker_id": worker_id,
                "worker_name": worker.get("name", "Unknown"),
                "decision": "APPROVED",
                "trust_score": score,
                "trust_tier": trust_result["tier"],
                "payout_amount": payout_amount,
                "payout_id": payout_id,
                "msts_breakdown": trust_result["breakdown"],
            })
        
        elif action == "HOLD_2HR":
            await db.insert_one("claims", {
                "_id": claim_id,
                "worker_id": worker_id,
                "zone": zone,
                "disruption_type": "Heavy Rain",
                "trust_score": score,
                "msts_breakdown": trust_result["breakdown"],
                "payout_amount": payout_amount,
                "status": "PENDING",
                "razorpay_payout_id": None,
                "reason": "Under review — trust score requires verification",
                "created_at": datetime.utcnow(),
                "simulated": True,
            })
            
            results.append({
                "worker_id": worker_id,
                "worker_name": worker.get("name", "Unknown"),
                "decision": "PENDING",
                "trust_score": score,
                "trust_tier": trust_result["tier"],
                "payout_amount": payout_amount,
            })
        
        else:
            results.append({
                "worker_id": worker_id,
                "worker_name": worker.get("name", "Unknown"),
                "decision": "BLOCKED",
                "trust_score": score,
                "trust_tier": trust_result["tier"],
                "payout_amount": 0,
            })
        
        # Update worker trust score
        await db.update_one("workers", {"_id": worker_id}, {
            "$set": {"trust_score": score}
        })
    
    logger.info(f"🌧️ Rainstorm simulation complete: {len(results)} workers processed")
    
    return {
        "status": "simulation_complete",
        "zone": zone,
        "rainfall_mm_hr": request.rainfall_mm_hr,
        "duration_hours": request.duration_hours,
        "workers_processed": len(results),
        "results": results,
        "timestamp": datetime.utcnow().isoformat(),
    }
