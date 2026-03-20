"""
Nexurance AI — FastAPI Backend
Team Code Nexus | Guidewire DEVTrails 2026

Parametric income protection for India's Q-commerce gig workers.
"We don't trust location. We verify reality."
"""
import os
import sys
import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from models.db import init_db, close_db
from routers import auth, policies, claims, triggers, payouts

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("nexurance")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    logger.info("🚀 Nexurance AI Backend starting...")
    logger.info(f"   Demo Mode: {os.getenv('DEMO_MODE', 'true')}")
    await init_db()
    logger.info("✅ Nexurance AI Backend ready!")
    yield
    await close_db()
    logger.info("👋 Nexurance AI Backend shutting down")


app = FastAPI(
    title="Nexurance AI",
    description="Parametric Income Protection for India's Gig Workers — API Backend",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(policies.router)
app.include_router(claims.router)
app.include_router(triggers.router)
app.include_router(payouts.router)


# --- Admin Dashboard APIs ---

from models.db import db
from datetime import datetime, timedelta
from services.premium_engine import get_all_zone_risks


@app.get("/api/admin/stats")
async def admin_stats():
    """Get aggregated stats for admin dashboard."""
    total_workers = await db.count("workers")
    active_policies = await db.count("policies", {"active": True})
    
    # Get payouts this week
    now = datetime.utcnow()
    week_start = now - timedelta(days=now.weekday())
    all_payouts = await db.find_many("payouts", {}, limit=1000)
    week_payouts = [
        p for p in all_payouts
        if p.get("created_at", datetime.min) >= week_start
    ]
    total_payouts_this_week = sum(p.get("amount", 0) for p in week_payouts)
    
    # Loss ratio
    all_policies = await db.find_many("policies", {}, limit=1000)
    total_premiums = sum(p.get("premium_paid", 0) for p in all_policies)
    all_payouts_total = sum(p.get("amount", 0) for p in all_payouts)
    loss_ratio = (all_payouts_total / max(total_premiums, 1)) * 100
    
    # Fraud flags
    all_claims = await db.find_many("claims", {}, limit=1000)
    fraud_flags = len([c for c in all_claims if c.get("trust_score", 1) < 0.60])
    
    # Avg trust score
    workers = await db.find_many("workers", {}, limit=1000)
    trust_scores = [w.get("trust_score", 0.85) for w in workers]
    avg_trust = sum(trust_scores) / max(len(trust_scores), 1)
    
    return {
        "total_workers": total_workers,
        "active_policies": active_policies,
        "total_payouts_this_week": round(total_payouts_this_week, 2),
        "loss_ratio": round(loss_ratio, 1),
        "fraud_flags_count": fraud_flags,
        "avg_trust_score": round(avg_trust, 3),
    }


@app.get("/api/admin/claims/recent")
async def admin_recent_claims(limit: int = 50):
    """Get recent claims for admin dashboard."""
    claims = await db.find_many(
        "claims", {}, limit=limit,
        sort_field="created_at", sort_order=-1,
    )
    # Enrich with worker info
    for claim in claims:
        worker = await db.find_one("workers", {"_id": claim.get("worker_id")})
        if worker:
            claim["worker_name"] = worker.get("name", "Unknown")
            claim["worker_platform"] = worker.get("platform", "")
    return claims


@app.get("/api/admin/fraud/clusters")
async def admin_fraud_clusters():
    """Get Louvain cluster analysis for fraud radar."""
    claim_events = await db.find_many("claim_events", {}, limit=500)
    
    # Group by zone and time window
    clusters = []
    if len(claim_events) >= 5:
        try:
            import networkx as nx
            from networkx.algorithms import community
            
            G = nx.Graph()
            for event in claim_events:
                G.add_node(event.get("worker_id", ""))
            
            for i, s1 in enumerate(claim_events):
                for s2 in claim_events[i + 1:]:
                    shared = 0
                    if s1.get("ip_subnet") == s2.get("ip_subnet") and s1.get("ip_subnet"):
                        shared += 1
                    if s1.get("device_model") == s2.get("device_model"):
                        shared += 1
                    ts1 = s1.get("timestamp", 0)
                    ts2 = s2.get("timestamp", 0)
                    if isinstance(ts1, (int, float)) and isinstance(ts2, (int, float)):
                        if abs(ts1 - ts2) < 180:
                            shared += 1
                    if shared >= 2:
                        G.add_edge(s1.get("worker_id"), s2.get("worker_id"))
            
            if G.number_of_edges() > 0:
                communities_list = list(community.louvain_communities(G))
                for i, comm in enumerate(communities_list):
                    if len(comm) > 2:
                        clusters.append({
                            "cluster_id": i + 1,
                            "size": len(comm),
                            "workers": list(comm),
                            "risk_level": "high" if len(comm) > 10 else "medium",
                        })
        except Exception as e:
            logger.error(f"Cluster analysis error: {e}")
    
    return {
        "clusters": clusters,
        "total_events_analyzed": len(claim_events),
    }


@app.get("/api/admin/zones/risk-map")
async def admin_zone_risk_map():
    """Get zone risk scores for heatmap."""
    zone_risks = get_all_zone_risks()
    
    # Enrich with claim counts
    claims = await db.find_many("claims", {}, limit=1000)
    zone_claims = {}
    for c in claims:
        z = c.get("zone", "unknown")
        zone_claims[z] = zone_claims.get(z, 0) + 1
    
    zones = []
    for zone, risk in zone_risks.items():
        zones.append({
            "zone": zone,
            "risk_score": risk,
            "claim_count": zone_claims.get(zone, 0),
            "risk_level": "high" if risk > 1.2 else "medium" if risk > 0.9 else "low",
        })
    
    return {"zones": sorted(zones, key=lambda x: x["risk_score"], reverse=True)}


@app.get("/api/admin/predictions/weekly")
async def admin_weekly_predictions():
    """Get predicted claims for next week (simplified forecasting)."""
    zone_risks = get_all_zone_risks()
    from services.trigger_service import get_weather_forecast
    
    predictions = []
    for zone, risk in zone_risks.items():
        forecast = get_weather_forecast(zone)
        rain_prob = forecast.get("rain_probability_7day", 0.3)
        predicted_claims = round(risk * rain_prob * 10, 1)
        
        predictions.append({
            "zone": zone,
            "predicted_claims": predicted_claims,
            "rain_probability": rain_prob,
            "risk_score": risk,
        })
    
    return {
        "predictions": sorted(predictions, key=lambda x: x["predicted_claims"], reverse=True),
        "week": "next",
    }


# --- Health Check ---

@app.get("/")
async def root():
    return {
        "name": "Nexurance AI",
        "tagline": "We don't trust location. We verify reality.",
        "version": "1.0.0",
        "team": "Code Nexus",
        "event": "Guidewire DEVTrails 2026",
        "status": "running",
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "demo_mode": os.getenv("DEMO_MODE", "true")}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
