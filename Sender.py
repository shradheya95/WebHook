"""
WEBHOOK SENDER
==============
This plays the role of "the external service" — the thing that notices
an event happened and pushes it to us. In real life this would be
Stripe noticing a payment succeeded, GitHub noticing a push happened, etc.

What it does:
  1. Builds a JSON payload describing "an event"
  2. Signs it with the SAME shared secret the receiver knows
  3. POSTs it to the receiver's /webhook URL with the signature in a header

Run the receiver first (uvicorn receiver:app --reload --port 8000),
then run this:
    python sender.py
"""

import hashlib
import hmac
import json
import time

import httpx

WEBHOOK_SECRET = "my-shared-secret-123"  # must match receiver.py
RECEIVER_URL = "http://127.0.0.1:8000/webhook"


def sign_payload(raw_body: bytes) -> str:
    return hmac.new(
        key=WEBHOOK_SECRET.encode(),
        msg=raw_body,
        digestmod=hashlib.sha256,
    ).hexdigest()


def send_event(event_type: str, data: dict):
    payload = {
        "event_type": event_type,
        "timestamp": time.time(),
        "data": data,
    }

    # IMPORTANT: sign the exact bytes we're about to send. If you sign a
    # Python dict and then json.dumps() it slightly differently later,
    # the signature won't match on the receiving end.
    raw_body = json.dumps(payload).encode()
    signature = sign_payload(raw_body)

    response = httpx.post(
        RECEIVER_URL,
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
        },
    )

    print(f"Sent '{event_type}' -> status {response.status_code}")
    print(response.json())


if __name__ == "__main__":
    # Simulate a couple of different events, like a real service would
    # send over time as different things happen.
    send_event("user.signed_up", {"user_id": 42, "email": "test@example.com"})
    send_event("payment.succeeded", {"order_id": 1001, "amount_usd": 29.99})

    # Let's also try sending one with a WRONG signature, to see the
    # receiver correctly reject it.
    print("\n--- Now sending a tampered/forged event ---")
    bad_payload = json.dumps({"event_type": "hacker.attempt", "data": {}}).encode()
    response = httpx.post(
        RECEIVER_URL,
        content=bad_payload,
        headers={
            "Content-Type": "application/json",
            "X-Webhook-Signature": "not-the-real-signature",
        },
    )
    print(f"Sent forged event -> status {response.status_code}")
    print(response.json())