"""Web Push (VAPID). Phase 3."""
import json

from pywebpush import WebPushException, webpush

from app.core.config import settings


def send_push(subscription: dict, title: str, body: str, url: str = "/") -> bool:
    try:
        webpush(
            subscription_info=subscription,
            data=json.dumps({"title": title, "body": body, "url": url}),
            vapid_private_key=settings.VAPID_PRIVATE,
            vapid_claims={"sub": settings.VAPID_SUBJECT},
        )
        return True
    except WebPushException:
        return False
