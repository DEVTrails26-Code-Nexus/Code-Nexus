"""
FCM Push Notification Service for Nexurance AI
Firebase Cloud Messaging with mock fallback for demo.
"""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
_firebase_initialized = False


def _init_firebase():
    """Initialize Firebase Admin SDK."""
    global _firebase_initialized
    if _firebase_initialized:
        return True
    
    if DEMO_MODE:
        logger.info("📱 FCM running in demo mode (notifications logged only)")
        return False
    
    try:
        import firebase_admin
        from firebase_admin import credentials
        
        cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY", "")
        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            _firebase_initialized = True
            logger.info("✅ Firebase Admin SDK initialized")
            return True
    except Exception as e:
        logger.warning(f"Firebase init failed: {e}")
    
    return False


async def send_payout_notification(fcm_token: str, amount: float):
    """Send payout approval push notification."""
    title = "Income Protected ✓"
    body = f"Rs.{amount:.0f} credited to your UPI. Stay safe!"
    
    if _init_firebase() and fcm_token and not fcm_token.startswith("demo_"):
        try:
            from firebase_admin import messaging
            
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data={
                    "type": "PAYOUT_APPROVED",
                    "amount": str(amount),
                    "click_action": "OPEN_CLAIM_HISTORY",
                },
                android=messaging.AndroidConfig(
                    priority="high",
                    notification=messaging.AndroidNotification(
                        color="#00B496",
                        sound="default",
                    ),
                ),
                token=fcm_token,
            )
            messaging.send(message)
            logger.info(f"📱 FCM notification sent: {title}")
            return
        except Exception as e:
            logger.warning(f"FCM send failed: {e}")
    
    # Log notification for demo
    logger.info(f"📱 [DEMO FCM] {title} — {body} (token: {fcm_token[:20]}...)")


async def send_disruption_alert(fcm_token: str, zone: str, alert_type: str):
    """Send disruption alert push notification."""
    title = f"⚠️ {alert_type} Alert in your zone"
    body = "Nexurance AI is monitoring your zone. You're covered."
    
    if _init_firebase() and fcm_token and not fcm_token.startswith("demo_"):
        try:
            from firebase_admin import messaging
            
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data={
                    "type": "DISRUPTION_ALERT",
                    "zone": zone,
                    "alert_type": alert_type,
                },
                android=messaging.AndroidConfig(priority="high"),
                token=fcm_token,
            )
            messaging.send(message)
            logger.info(f"📱 FCM disruption alert sent for zone '{zone}'")
            return
        except Exception as e:
            logger.warning(f"FCM send failed: {e}")
    
    # Log for demo
    logger.info(f"📱 [DEMO FCM] {title} — {body} (zone: {zone})")


async def send_eligibility_check(fcm_token: str, zone: str):
    """Send eligibility check notification."""
    title = "🔍 Verifying your eligibility..."
    body = f"Disruption detected in {zone}. Checking your coverage now."
    
    logger.info(f"📱 [DEMO FCM] {title} — {body}")
