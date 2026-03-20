"""
Authentication Router for Nexurance AI
Firebase Phone OTP verification with demo fallback.
"""
import uuid
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException

from models.schemas import PhoneVerifyRequest, PhoneVerifyResponse, WorkerCreate, WorkerResponse
from models.db import db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/verify-phone", response_model=PhoneVerifyResponse)
async def verify_phone(request: PhoneVerifyRequest):
    """
    Verify Firebase phone auth ID token.
    In demo mode: accepts any phone number and creates/fetches worker.
    """
    phone = request.phone
    if not phone:
        raise HTTPException(status_code=400, detail="Phone number required")
    
    # Normalize phone
    if not phone.startswith("+"):
        phone = "+91" + phone
    
    # Check if worker exists
    worker = await db.find_one("workers", {"phone": phone})
    
    if worker:
        return PhoneVerifyResponse(
            worker_id=worker["_id"],
            is_new_user=False,
            token=f"demo_token_{worker['_id']}",
        )
    
    # New user — create minimal record
    worker_id = f"worker_{uuid.uuid4().hex[:8]}"
    await db.insert_one("workers", {
        "_id": worker_id,
        "phone": phone,
        "name": "",
        "platform": "blinkit",
        "zone": "",
        "city": "Bengaluru",
        "upi_id": "",
        "fcm_token": "",
        "trust_score": 0.85,
        "consecutive_clean_weeks": 0,
        "avg_hourly_earnings": 111,
        "total_claims": 0,
        "total_payouts": 0,
        "working_hours": [],
        "created_at": datetime.utcnow(),
        "active_days": 0,
    })
    
    return PhoneVerifyResponse(
        worker_id=worker_id,
        is_new_user=True,
        token=f"demo_token_{worker_id}",
    )


@router.post("/workers", response_model=WorkerResponse)
async def create_worker(worker: WorkerCreate):
    """Create or update worker profile."""
    # Check if phone exists
    existing = await db.find_one("workers", {"phone": worker.phone})
    
    if existing:
        # Update existing worker
        await db.update_one("workers", {"_id": existing["_id"]}, {"$set": {
            "name": worker.name,
            "platform": worker.platform.value,
            "zone": worker.zone,
            "city": worker.city,
            "upi_id": worker.upi_id,
            "working_hours": worker.working_hours,
        }})
        updated = await db.find_one("workers", {"_id": existing["_id"]})
        return _worker_to_response(updated)
    
    # Create new worker
    worker_id = f"worker_{uuid.uuid4().hex[:8]}"
    doc = {
        "_id": worker_id,
        "phone": worker.phone,
        "name": worker.name,
        "platform": worker.platform.value,
        "zone": worker.zone,
        "city": worker.city,
        "upi_id": worker.upi_id,
        "fcm_token": "",
        "trust_score": 0.85,
        "consecutive_clean_weeks": 0,
        "avg_hourly_earnings": 111,
        "total_claims": 0,
        "total_payouts": 0,
        "working_hours": worker.working_hours,
        "created_at": datetime.utcnow(),
        "active_days": 0,
    }
    await db.insert_one("workers", doc)
    return _worker_to_response(doc)


@router.get("/workers/{worker_id}", response_model=WorkerResponse)
async def get_worker(worker_id: str):
    """Get worker profile by ID."""
    worker = await db.find_one("workers", {"_id": worker_id})
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    return _worker_to_response(worker)


@router.put("/workers/{worker_id}", response_model=WorkerResponse)
async def update_worker(worker_id: str, update: dict):
    """Update worker profile."""
    worker = await db.find_one("workers", {"_id": worker_id})
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    
    await db.update_one("workers", {"_id": worker_id}, {"$set": update})
    updated = await db.find_one("workers", {"_id": worker_id})
    return _worker_to_response(updated)


def _worker_to_response(doc: dict) -> WorkerResponse:
    """Convert worker document to response model."""
    return WorkerResponse(
        id=doc["_id"],
        phone=doc.get("phone", ""),
        name=doc.get("name", ""),
        platform=doc.get("platform", "blinkit"),
        zone=doc.get("zone", ""),
        city=doc.get("city", "Bengaluru"),
        upi_id=doc.get("upi_id", ""),
        trust_score=doc.get("trust_score", 0.85),
        consecutive_clean_weeks=doc.get("consecutive_clean_weeks", 0),
        fcm_token=doc.get("fcm_token"),
        created_at=doc.get("created_at", datetime.utcnow()),
    )
