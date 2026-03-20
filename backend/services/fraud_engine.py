"""
MSTS (Multi-Signal Trust Score) Fraud Detection Engine for Nexurance AI.
Trust_Score = 0.25×L + 0.25×M + 0.20×N + 0.20×B + 0.10×C
"""
import logging
import time
import math
import hashlib
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

try:
    import networkx as nx
    from networkx.algorithms import community
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    logger.warning("networkx not available — Louvain clustering disabled")


def compute_trust_score(
    telemetry: Dict[str, Any],
    worker_history: Dict[str, Any],
    zone_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compute the full MSTS trust score with 5 signals.
    Trust_Score = 0.25×L + 0.25×M + 0.20×N + 0.20×B + 0.10×C
    """
    # --- Signal 1: Location Consistency (L) ---
    cell_match = _check_cell_tower_zone_match(
        telemetry.get("cell_towers", []),
        zone_context.get("claimed_zone", "")
    )
    wifi_match = _check_wifi_fingerprint(
        telemetry.get("wifi_ssids", []),
        zone_context.get("claimed_zone", "")
    )
    gps_drift = _evaluate_gps_drift_naturalness(
        telemetry.get("gps_readings", [])
    )
    ip_match = _check_ip_geolocation(
        telemetry.get("ip_address", ""),
        zone_context.get("claimed_zone", "")
    )
    L = (cell_match * 0.40 + wifi_match * 0.30 +
         gps_drift * 0.20 + ip_match * 0.10)

    # --- Signal 2: Motion Validity (M) ---
    accel_score = _analyze_accelerometer_pattern(
        telemetry.get("accelerometer", [0, 0, 9.8])
    )
    baro_score = _check_barometer_rain_correlation(
        telemetry.get("barometer_hpa", 1013.25),
        zone_context.get("weather_data", {})
    )
    gyro_score = _analyze_gyroscope_pattern(
        telemetry.get("gyroscope", [0, 0, 0])
    )
    screen_score = _check_screen_state(
        telemetry.get("screen_state", "unknown")
    )
    M = (accel_score * 0.35 + baro_score * 0.35 +
         gyro_score * 0.20 + screen_score * 0.10)

    # --- Signal 3: Network Authenticity (N) ---
    vpn_clean = 0.0 if _detect_vpn(telemetry.get("ip_address", "")) else 1.0
    mock_clean = 0.0 if telemetry.get("is_mock_location", False) else 1.0
    integrity_score = _verify_play_integrity(
        telemetry.get("device_integrity_token", "")
    )
    N = (vpn_clean * 0.40 + mock_clean * 0.40 + integrity_score * 0.20)

    # --- Signal 4: Behavioural History (B) ---
    zone_familiarity = _compute_zone_familiarity(
        worker_history, zone_context.get("claimed_zone", "")
    )
    claim_freq_ok = _check_claim_frequency(worker_history)
    earnings_aligned = _check_earnings_alignment(
        worker_history,
        zone_context.get("claimed_payout", 0)
    )
    B = (zone_familiarity * 0.40 + claim_freq_ok * 0.35 +
         earnings_aligned * 0.25)

    # --- Signal 5: Cluster Isolation (C) ---
    cluster_score = _louvain_cluster_check(
        worker_history.get("worker_id", worker_history.get("_id", "")),
        zone_context.get("event_window_submissions", [])
    )
    C = cluster_score

    # --- Network Forgiveness Buffer ---
    network_down = not telemetry.get("network_available", True)
    rain_confirmed = zone_context.get("weather_data", {}).get("rain_confirmed", False)
    forgiveness = 0.08 if (network_down and rain_confirmed) else 0.0

    # --- Composite Score ---
    raw_score = (0.25 * L + 0.25 * M + 0.20 * N + 0.20 * B + 0.10 * C)
    final_score = min(1.0, raw_score + forgiveness)

    return {
        "trust_score": round(final_score, 3),
        "breakdown": {
            "location_consistency": round(L, 3),
            "motion_validity": round(M, 3),
            "network_authenticity": round(N, 3),
            "behavioural_history": round(B, 3),
            "cluster_isolation": round(C, 3),
            "forgiveness_applied": forgiveness > 0,
        },
        "tier": _get_tier(final_score),
        "action": _get_action(final_score),
    }


# ---- Tier / Action mapping ----

def _get_tier(score: float) -> str:
    if score >= 0.80:
        return "TRUSTED"
    if score >= 0.60:
        return "VERIFY"
    if score >= 0.40:
        return "REVIEW"
    return "BLOCK"


def _get_action(score: float) -> str:
    if score >= 0.80:
        return "INSTANT_PAYOUT"
    if score >= 0.60:
        return "HOLD_2HR"
    if score >= 0.40:
        return "HOLD_24HR"
    return "BLOCKED"


# ---- Signal 1: Location Consistency helpers ----

def _check_cell_tower_zone_match(cell_towers: List, claimed_zone: str) -> float:
    """Check if cell tower IDs are consistent with the claimed zone."""
    if not cell_towers:
        return 0.75  # No data — moderate confidence (demo default)
    
    # In production, cross-reference cell tower IDs with zone database
    # For demo: simulate based on whether towers are provided
    known_zone_towers = {
        "koramangala": ["40445", "40446", "40447"],
        "hsr_layout": ["40450", "40451"],
        "whitefield": ["40460", "40461"],
    }
    zone_key = claimed_zone.lower().replace(" ", "_")
    expected = known_zone_towers.get(zone_key, [])
    
    if not expected:
        return 0.80
    
    tower_ids = [str(t.get("id", t)) if isinstance(t, dict) else str(t) for t in cell_towers]
    matches = sum(1 for t in tower_ids if any(e in t for e in expected))
    return min(1.0, 0.5 + (matches / max(len(expected), 1)) * 0.5)


def _check_wifi_fingerprint(wifi_ssids: List[str], claimed_zone: str) -> float:
    """Check if WiFi SSIDs are consistent with the claimed zone."""
    if not wifi_ssids:
        return 0.70  # No WiFi data — slightly lower confidence
    
    # Commercial/known SSIDs expected in Bengaluru delivery zones
    known_ssids = {"JioFiber", "Airtel_", "ACT_", "BSNL_", "Tata_Play"}
    matches = sum(1 for ssid in wifi_ssids
                  if any(k in ssid for k in known_ssids))
    return min(1.0, 0.5 + (matches / max(len(wifi_ssids), 1)) * 0.5)


def _evaluate_gps_drift_naturalness(gps_readings: List) -> float:
    """Evaluate if GPS drift pattern looks natural (human movement)."""
    if not gps_readings or len(gps_readings) < 2:
        return 0.80  # Not enough data, default moderate
    
    # Check for unnatural jumps (teleportation)
    max_speed_kmh = 0
    for i in range(1, len(gps_readings)):
        prev = gps_readings[i - 1]
        curr = gps_readings[i]
        if isinstance(prev, dict) and isinstance(curr, dict):
            dlat = abs(curr.get("lat", 0) - prev.get("lat", 0))
            dlng = abs(curr.get("lng", 0) - prev.get("lng", 0))
            dist_km = math.sqrt(dlat ** 2 + dlng ** 2) * 111  # rough km
            dt = curr.get("ts", 1) - prev.get("ts", 0)
            if dt > 0:
                speed = dist_km / (dt / 3600)
                max_speed_kmh = max(max_speed_kmh, speed)
    
    # Delivery riders shouldn't exceed ~80 km/h
    if max_speed_kmh > 200:
        return 0.1  # Teleportation detected
    if max_speed_kmh > 80:
        return 0.5  # Suspicious speed
    return 0.90  # Natural movement


def _check_ip_geolocation(ip_address: str, claimed_zone: str) -> float:
    """Check if IP geolocation matches claimed zone."""
    if not ip_address:
        return 0.60
    
    # In production, use IP geolocation API
    # For demo: check if it's a local Indian IP
    if ip_address.startswith("10.") or ip_address.startswith("192.168."):
        return 0.85  # Private IP, likely local
    if ip_address.startswith("203.") or ip_address.startswith("103."):
        return 0.90  # Common Indian IP ranges
    return 0.70


# ---- Signal 2: Motion Validity helpers ----

def _analyze_accelerometer_pattern(accel: List[float]) -> float:
    """Check if accelerometer data shows natural motion/stillness patterns."""
    if not accel or len(accel) < 3:
        return 0.75
    
    x, y, z = accel[0], accel[1], accel[2]
    magnitude = math.sqrt(x ** 2 + y ** 2 + z ** 2)
    
    # At rest, magnitude ≈ 9.8 m/s² (gravity)
    # Walking/riding: 9.0-12.0 typical
    if 8.0 <= magnitude <= 15.0:
        return 0.90  # Normal range
    if 5.0 <= magnitude <= 20.0:
        return 0.60  # Unusual but possible
    return 0.20  # Very suspicious


def _check_barometer_rain_correlation(barometer_hpa: float, weather_data: Dict) -> float:
    """Check if barometric pressure correlates with claimed rain event."""
    rain_claimed = weather_data.get("rain_confirmed", False)
    
    # During heavy rain, atmospheric pressure typically drops
    # Normal: 1013.25 hPa, Rain: typically 1000-1010 hPa
    if rain_claimed:
        if barometer_hpa < 1010:
            return 0.95  # Low pressure matches rain claim
        if barometer_hpa < 1015:
            return 0.75  # Marginal — could be rain
        return 0.40  # High pressure but claiming rain — suspicious
    else:
        return 0.85  # No rain claim, pressure doesn't matter as much


def _analyze_gyroscope_pattern(gyro: List[float]) -> float:
    """Check if gyroscope shows natural device movement."""
    if not gyro or len(gyro) < 3:
        return 0.75
    
    x, y, z = gyro[0], gyro[1], gyro[2]
    total_rotation = math.sqrt(x ** 2 + y ** 2 + z ** 2)
    
    # Natural movement has some rotation
    if 0.01 <= total_rotation <= 5.0:
        return 0.90  # Natural
    if total_rotation == 0.0:
        return 0.50  # Perfectly still — could be emulated
    return 0.60  # Very high rotation — unusual


def _check_screen_state(screen_state: str) -> float:
    """Check if screen state is consistent with a real user."""
    states = {"on": 0.90, "off": 0.70, "unknown": 0.60}
    return states.get(screen_state, 0.60)


# ---- Signal 3: Network Authenticity helpers ----

def _detect_vpn(ip_address: str) -> bool:
    """Detect if the IP is from a known VPN provider."""
    if not ip_address:
        return False
    
    # In production, use VPN detection API
    # For demo: check known VPN IP ranges
    vpn_prefixes = ["104.238.", "45.76.", "198.54.", "185.220."]
    return any(ip_address.startswith(p) for p in vpn_prefixes)


def _verify_play_integrity(token: str) -> float:
    """Verify Google Play Integrity token."""
    if not token:
        return 0.70  # No token — moderate score
    
    # In demo/production: verify with Google Play Integrity API
    # For now, accept any non-empty token
    if token.startswith("demo_") or token.startswith("mock_"):
        return 0.85
    return 0.90


# ---- Signal 4: Behavioural History helpers ----

def _compute_zone_familiarity(worker_history: Dict, claimed_zone: str) -> float:
    """Check if worker regularly works in the claimed zone."""
    zone = worker_history.get("zone", "")
    if zone.lower().replace(" ", "_") == claimed_zone.lower().replace(" ", "_"):
        return 0.95  # Worker's registered zone
    
    active_days = worker_history.get("active_days", 0)
    if active_days > 30:
        return 0.80  # Established worker, maybe roaming
    if active_days > 7:
        return 0.60
    return 0.40  # New worker in unfamiliar zone


def _check_claim_frequency(worker_history: Dict) -> float:
    """Check if claim frequency is within normal bounds."""
    total_claims = worker_history.get("total_claims", 0)
    active_days = max(worker_history.get("active_days", 1), 1)
    
    claims_per_week = (total_claims / active_days) * 7
    
    if claims_per_week <= 1:
        return 0.95  # Normal frequency
    if claims_per_week <= 2:
        return 0.75  # Slightly elevated
    if claims_per_week <= 3:
        return 0.50  # Suspicious
    return 0.20  # Very suspicious — possible fraud


def _check_earnings_alignment(worker_history: Dict, claimed_payout: float) -> float:
    """Check if claimed payout aligns with worker's typical earnings."""
    avg_hourly = worker_history.get("avg_hourly_earnings", 111)
    
    if claimed_payout <= 0:
        return 0.85  # No payout to check
    
    # Typical payout should be 1-4 hours * avg_hourly * 0.80
    max_reasonable = avg_hourly * 4 * 0.80
    
    if claimed_payout <= max_reasonable:
        return 0.90
    if claimed_payout <= max_reasonable * 1.5:
        return 0.60
    return 0.30  # Claiming much more than reasonable


# ---- Signal 5: Cluster Isolation (Louvain) ----

def _louvain_cluster_check(worker_id: str, recent_submissions: List) -> float:
    """
    Build claim event graph and detect synchronized burst clusters.
    Returns 1.0 (isolated/normal) to 0.0 (in detected fraud cluster).
    """
    if not recent_submissions or len(recent_submissions) < 5:
        return 1.0  # Not enough data to detect rings
    
    if not HAS_NETWORKX:
        return 0.90  # Can't check, give benefit of doubt
    
    try:
        G = nx.Graph()
        for sub in recent_submissions:
            G.add_node(sub.get("worker_id", ""))
        
        # Add edges for shared characteristics
        for i, s1 in enumerate(recent_submissions):
            for s2 in recent_submissions[i + 1:]:
                shared = 0
                # Same /24 IP subnet
                if _same_subnet(s1.get("ip_subnet", ""), s2.get("ip_subnet", "")):
                    shared += 1
                # Same device model
                if s1.get("device_model") == s2.get("device_model"):
                    shared += 1
                # Within 3-minute window
                ts1 = s1.get("timestamp", 0)
                ts2 = s2.get("timestamp", 0)
                if isinstance(ts1, (int, float)) and isinstance(ts2, (int, float)):
                    if abs(ts1 - ts2) < 180:
                        shared += 1
                if shared >= 2:
                    G.add_edge(
                        s1.get("worker_id", ""),
                        s2.get("worker_id", "")
                    )
        
        if G.number_of_edges() == 0:
            return 1.0
        
        # Louvain community detection
        communities = list(community.louvain_communities(G))
        
        for comm in communities:
            if worker_id in comm:
                # Check if community is suspiciously synchronized
                comm_subs = [
                    s for s in recent_submissions
                    if s.get("worker_id") in comm
                ]
                if len(comm_subs) >= 2:
                    timestamps = [s.get("timestamp", 0) for s in comm_subs]
                    burst_window = max(timestamps) - min(timestamps)
                    
                    if len(comm) > 15 and burst_window < 480:  # 8 minutes
                        return 0.0  # Fraud ring detected
                    if len(comm) > 8 and burst_window < 300:  # 5 minutes
                        return 0.3  # Suspicious cluster
                    if len(comm) > 5 and burst_window < 120:  # 2 minutes
                        return 0.5  # Moderately suspicious
        
        return 1.0  # Looks legitimate
    
    except Exception as e:
        logger.error(f"Louvain clustering error: {e}")
        return 0.85  # Error — give benefit of doubt


def _same_subnet(ip1: str, ip2: str) -> bool:
    """Check if two IPs are on the same /24 subnet."""
    if not ip1 or not ip2:
        return False
    parts1 = ip1.split(".")
    parts2 = ip2.split(".")
    if len(parts1) >= 3 and len(parts2) >= 3:
        return parts1[:3] == parts2[:3]
    return False
