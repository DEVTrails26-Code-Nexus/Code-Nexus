"""
Pydantic models for Nexurance AI API
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# --- Enums ---
class Platform(str, Enum):
    BLINKIT = "blinkit"
    ZEPTO = "zepto"
    INSTAMART = "instamart"


class PlanType(str, Enum):
    STARTER = "starter"
    SHIELD = "shield"
    MAX = "max"


class ClaimStatus(str, Enum):
    APPROVED = "APPROVED"
    PENDING = "PENDING"
    BLOCKED = "BLOCKED"
    HELD_2HR = "HELD_2HR"


class TrustTier(str, Enum):
    TRUSTED = "TRUSTED"
    VERIFY = "VERIFY"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"


# --- Worker ---
class WorkerCreate(BaseModel):
    phone: str
    name: str
    platform: Platform
    zone: str
    city: str = "Bengaluru"
    working_hours: List[str] = []
    upi_id: str


class WorkerResponse(BaseModel):
    id: str
    phone: str
    name: str
    platform: Platform
    zone: str
    city: str
    upi_id: str
    trust_score: float = 0.85
    consecutive_clean_weeks: int = 0
    fcm_token: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class WorkerUpdate(BaseModel):
    name: Optional[str] = None
    platform: Optional[Platform] = None
    zone: Optional[str] = None
    city: Optional[str] = None
    working_hours: Optional[List[str]] = None
    upi_id: Optional[str] = None
    fcm_token: Optional[str] = None


# --- Policy ---
class PolicyCreate(BaseModel):
    worker_id: str
    plan: PlanType
    premium_paid: float
    coverage_limit: float
    razorpay_payment_id: Optional[str] = None


class PolicyResponse(BaseModel):
    id: str
    worker_id: str
    plan: PlanType
    premium_paid: float
    coverage_limit: float
    week_start: datetime
    week_end: datetime
    active: bool = True
    razorpay_payment_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# --- Telemetry ---
class TelemetryData(BaseModel):
    accelerometer: List[float] = [0.0, 0.0, 9.8]
    gyroscope: List[float] = [0.0, 0.0, 0.0]
    barometer_hpa: float = 1013.25
    cell_towers: List[Dict[str, Any]] = []
    wifi_ssids: List[str] = []
    ip_address: str = "203.0.113.1"
    is_mock_location: bool = False
    network_available: bool = True
    device_integrity_token: str = ""
    gps_readings: List[Dict[str, float]] = []
    screen_state: str = "on"
    device_model: str = "unknown"


# --- Trust Score ---
class TrustScoreBreakdown(BaseModel):
    location_consistency: float
    motion_validity: float
    network_authenticity: float
    behavioural_history: float
    cluster_isolation: float
    forgiveness_applied: bool = False


class TrustScoreResponse(BaseModel):
    trust_score: float
    breakdown: TrustScoreBreakdown
    tier: TrustTier
    action: str


# --- Trigger ---
class TriggerCheckRequest(BaseModel):
    zone: str
    lat: float = 12.9716
    lng: float = 77.5946


class TriggerResult(BaseModel):
    trigger_level: int = 0
    rain_alert: bool = False
    rainfall_mm_hr: float = 0.0
    rainfall_mm: float = 0.0
    aqi_level: int = 0
    aqi_alert: bool = False
    flood_alert: bool = False
    curfew_alert: bool = False
    disruption_score: float = 0.0
    rain_confirmed: bool = False
    weather_data: Dict[str, Any] = {}
    disruption_duration_hours: float = 0.0


# --- Claims ---
class ClaimEvaluateRequest(BaseModel):
    worker_id: str
    zone: str
    lat: float = 12.9716
    lng: float = 77.5946
    telemetry: TelemetryData = TelemetryData()


class ClaimResponse(BaseModel):
    id: str
    worker_id: str
    zone: str
    disruption_type: str
    trust_score: float
    msts_breakdown: TrustScoreBreakdown
    payout_amount: float
    status: ClaimStatus
    razorpay_payout_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    reason: str = ""


class ClaimEvaluateResponse(BaseModel):
    decision: ClaimStatus
    trust_score: float
    payout_amount: float = 0.0
    reason: str
    payout_id: Optional[str] = None
    msts_breakdown: Optional[TrustScoreBreakdown] = None


# --- Premium ---
class PremiumCalculateRequest(BaseModel):
    worker_id: str
    zone: str
    platform: Platform = Platform.BLINKIT


class PremiumResult(BaseModel):
    recommended_plan: str = "shield"
    starter_price: float
    shield_price: float
    max_price: float
    zone_risk_score: float
    weather_factor: float
    trust_discount: float
    coverage_amounts: Dict[str, int] = {
        "starter": 500,
        "shield": 1200,
        "max": 2500
    }


# --- Payout ---
class PayoutProcessRequest(BaseModel):
    claim_id: str
    worker_id: str
    amount: float
    upi_id: str


class PayoutResponse(BaseModel):
    payout_id: str
    status: str
    upi_ref: Optional[str] = None
    amount: float
    worker_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


# --- Auth ---
class PhoneVerifyRequest(BaseModel):
    phone: str
    id_token: str = ""


class PhoneVerifyResponse(BaseModel):
    worker_id: str
    is_new_user: bool
    token: str = ""


# --- Admin ---
class AdminStats(BaseModel):
    total_workers: int
    active_policies: int
    total_payouts_this_week: float
    loss_ratio: float
    fraud_flags_count: int
    avg_trust_score: float


# --- Demo ---
class SimulateRainstormRequest(BaseModel):
    zone: str = "koramangala"
    rainfall_mm_hr: float = 75.0
    duration_hours: float = 2.0
