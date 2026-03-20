"""
Database connection and in-memory fallback for Nexurance AI.
Uses MongoDB if available, otherwise falls back to in-memory storage for demo.
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import uuid

logger = logging.getLogger(__name__)

# In-memory storage for demo mode
_in_memory_db: Dict[str, List[Dict[str, Any]]] = {
    "workers": [],
    "policies": [],
    "claims": [],
    "payouts": [],
    "telemetry_events": [],
    "claim_events": [],
    "trigger_overrides": [],
}

# MongoDB client (optional)
_mongo_client = None
_mongo_db = None


async def init_db():
    """Initialize database connection. Falls back to in-memory if MongoDB unavailable."""
    global _mongo_client, _mongo_db
    
    mongo_uri = os.getenv("MONGODB_URI", "")
    demo_mode = os.getenv("DEMO_MODE", "true").lower() == "true"
    
    if not demo_mode and mongo_uri:
        try:
            from motor.motor_asyncio import AsyncIOMotorClient
            _mongo_client = AsyncIOMotorClient(mongo_uri, serverSelectionTimeoutMS=3000)
            # Test connection
            await _mongo_client.admin.command('ping')
            _mongo_db = _mongo_client.nexurance_ai
            logger.info("✅ Connected to MongoDB")
            return
        except Exception as e:
            logger.warning(f"⚠️ MongoDB unavailable ({e}), using in-memory storage")
    
    logger.info("🧪 Running in DEMO MODE with in-memory storage")
    _seed_demo_data()


async def close_db():
    """Close database connection."""
    global _mongo_client
    if _mongo_client:
        _mongo_client.close()
        logger.info("MongoDB connection closed")


def _seed_demo_data():
    """Seed in-memory database with demo data for hackathon presentation."""
    now = datetime.utcnow()
    week_start = now - timedelta(days=now.weekday())
    week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
    
    # Demo worker: Ravi the Blinkit rider
    demo_worker = {
        "_id": "worker_ravi_001",
        "phone": "+919876543210",
        "name": "Ravi Kumar",
        "platform": "blinkit",
        "zone": "koramangala",
        "city": "Bengaluru",
        "upi_id": "ravi@upi",
        "fcm_token": "demo_fcm_token_ravi",
        "trust_score": 0.91,
        "consecutive_clean_weeks": 6,
        "avg_hourly_earnings": 111,
        "total_claims": 3,
        "total_payouts": 1240,
        "working_hours": ["7-10AM", "6-10PM"],
        "created_at": now - timedelta(days=45),
        "active_days": 38,
    }
    
    # Second demo worker
    demo_worker_2 = {
        "_id": "worker_priya_002",
        "phone": "+919876543211",
        "name": "Priya Sharma",
        "platform": "zepto",
        "zone": "hsr_layout",
        "city": "Bengaluru",
        "upi_id": "priya@upi",
        "fcm_token": "demo_fcm_token_priya",
        "trust_score": 0.78,
        "consecutive_clean_weeks": 3,
        "avg_hourly_earnings": 95,
        "total_claims": 5,
        "total_payouts": 2100,
        "working_hours": ["6-10PM"],
        "created_at": now - timedelta(days=30),
        "active_days": 25,
    }
    
    # Third demo worker
    demo_worker_3 = {
        "_id": "worker_arjun_003",
        "phone": "+919876543212",
        "name": "Arjun Patel",
        "platform": "instamart",
        "zone": "whitefield",
        "city": "Bengaluru",
        "upi_id": "arjun@upi",
        "fcm_token": "demo_fcm_token_arjun",
        "trust_score": 0.45,
        "consecutive_clean_weeks": 0,
        "avg_hourly_earnings": 105,
        "total_claims": 8,
        "total_payouts": 3800,
        "working_hours": ["7-10AM", "6-10PM", "custom"],
        "created_at": now - timedelta(days=60),
        "active_days": 52,
    }
    
    _in_memory_db["workers"] = [demo_worker, demo_worker_2, demo_worker_3]
    
    # Demo policy for Ravi
    demo_policy = {
        "_id": "policy_ravi_shield_001",
        "worker_id": "worker_ravi_001",
        "plan": "shield",
        "premium_paid": 33,
        "coverage_limit": 1200,
        "week_start": week_start,
        "week_end": week_end,
        "active": True,
        "razorpay_payment_id": "pay_demo_001",
        "created_at": week_start,
    }
    
    demo_policy_2 = {
        "_id": "policy_priya_starter_001",
        "worker_id": "worker_priya_002",
        "plan": "starter",
        "premium_paid": 22,
        "coverage_limit": 500,
        "week_start": week_start,
        "week_end": week_end,
        "active": True,
        "razorpay_payment_id": "pay_demo_002",
        "created_at": week_start,
    }
    
    _in_memory_db["policies"] = [demo_policy, demo_policy_2]
    
    # Demo past claims
    past_claims = [
        {
            "_id": "claim_001",
            "worker_id": "worker_ravi_001",
            "zone": "koramangala",
            "disruption_type": "Heavy Rain",
            "trust_score": 0.92,
            "msts_breakdown": {
                "location_consistency": 0.95,
                "motion_validity": 0.88,
                "network_authenticity": 1.0,
                "behavioural_history": 0.85,
                "cluster_isolation": 1.0,
                "forgiveness_applied": False,
            },
            "payout_amount": 480,
            "status": "APPROVED",
            "razorpay_payout_id": "pout_demo_001",
            "created_at": now - timedelta(days=7),
            "reason": "Verified heavy rainfall disruption",
        },
        {
            "_id": "claim_002",
            "worker_id": "worker_ravi_001",
            "zone": "koramangala",
            "disruption_type": "AQI Spike",
            "trust_score": 0.89,
            "msts_breakdown": {
                "location_consistency": 0.90,
                "motion_validity": 0.85,
                "network_authenticity": 1.0,
                "behavioural_history": 0.82,
                "cluster_isolation": 1.0,
                "forgiveness_applied": False,
            },
            "payout_amount": 360,
            "status": "APPROVED",
            "razorpay_payout_id": "pout_demo_002",
            "created_at": now - timedelta(days=14),
            "reason": "Verified AQI disruption",
        },
        {
            "_id": "claim_003",
            "worker_id": "worker_ravi_001",
            "zone": "koramangala",
            "disruption_type": "Heavy Rain",
            "trust_score": 0.90,
            "msts_breakdown": {
                "location_consistency": 0.92,
                "motion_validity": 0.87,
                "network_authenticity": 1.0,
                "behavioural_history": 0.80,
                "cluster_isolation": 1.0,
                "forgiveness_applied": False,
            },
            "payout_amount": 400,
            "status": "APPROVED",
            "razorpay_payout_id": "pout_demo_003",
            "created_at": now - timedelta(days=21),
            "reason": "Verified heavy rainfall disruption",
        },
    ]
    _in_memory_db["claims"] = past_claims
    
    # Demo payouts
    _in_memory_db["payouts"] = [
        {
            "_id": f"pout_demo_{i+1:03d}",
            "worker_id": c["worker_id"],
            "amount": c["payout_amount"],
            "razorpay_payout_id": c["razorpay_payout_id"],
            "status": "processed",
            "upi_id": "ravi@upi",
            "created_at": c["created_at"],
            "mock": True,
        }
        for i, c in enumerate(past_claims)
    ]
    
    logger.info(f"📦 Seeded demo data: {len(_in_memory_db['workers'])} workers, "
                f"{len(_in_memory_db['policies'])} policies, "
                f"{len(_in_memory_db['claims'])} claims")


class Database:
    """Unified database interface that works with both MongoDB and in-memory storage."""
    
    def __init__(self):
        pass
    
    def _get_collection(self, name: str):
        if _mongo_db is not None:
            return _mongo_db[name]
        return None
    
    def _get_memory(self, name: str) -> List[Dict]:
        return _in_memory_db.setdefault(name, [])
    
    # --- Generic Operations ---
    async def find_one(self, collection: str, query: Dict) -> Optional[Dict]:
        mongo_col = self._get_collection(collection)
        if mongo_col is not None:
            return await mongo_col.find_one(query)
        
        items = self._get_memory(collection)
        for item in items:
            if all(item.get(k) == v for k, v in query.items()):
                return item.copy()
        return None
    
    async def find_many(self, collection: str, query: Dict = None, 
                        limit: int = 100, sort_field: str = None,
                        sort_order: int = -1) -> List[Dict]:
        mongo_col = self._get_collection(collection)
        if mongo_col is not None:
            cursor = mongo_col.find(query or {})
            if sort_field:
                cursor = cursor.sort(sort_field, sort_order)
            cursor = cursor.limit(limit)
            return await cursor.to_list(length=limit)
        
        items = self._get_memory(collection)
        if query:
            items = [
                item for item in items
                if all(item.get(k) == v for k, v in query.items())
            ]
        if sort_field:
            items = sorted(
                items,
                key=lambda x: x.get(sort_field, datetime.min),
                reverse=(sort_order == -1)
            )
        return [item.copy() for item in items[:limit]]
    
    async def insert_one(self, collection: str, document: Dict) -> str:
        if "_id" not in document:
            document["_id"] = str(uuid.uuid4())
        
        mongo_col = self._get_collection(collection)
        if mongo_col is not None:
            result = await mongo_col.insert_one(document)
            return str(result.inserted_id)
        
        self._get_memory(collection).append(document.copy())
        return document["_id"]
    
    async def update_one(self, collection: str, query: Dict, update: Dict) -> bool:
        mongo_col = self._get_collection(collection)
        if mongo_col is not None:
            result = await mongo_col.update_one(query, update)
            return result.modified_count > 0
        
        items = self._get_memory(collection)
        for item in items:
            if all(item.get(k) == v for k, v in query.items()):
                if "$set" in update:
                    item.update(update["$set"])
                else:
                    item.update(update)
                return True
        return False
    
    async def count(self, collection: str, query: Dict = None) -> int:
        mongo_col = self._get_collection(collection)
        if mongo_col is not None:
            return await mongo_col.count_documents(query or {})
        
        items = self._get_memory(collection)
        if query:
            return len([i for i in items if all(i.get(k) == v for k, v in query.items())])
        return len(items)
    
    async def aggregate_sum(self, collection: str, query: Dict, field: str) -> float:
        items = await self.find_many(collection, query, limit=10000)
        return sum(item.get(field, 0) for item in items)


# Singleton database instance
db = Database()
