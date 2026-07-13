"""
WEBHOOK RECEIVER
=================
This is the "server" side of a webhook. It sits and waits for another
service (our sender.py, or in real life: Stripe, GitHub, Slack, etc.)
to POST an event to it.

Three things a real-world receiver almost always has to do:
  1. Accept a POST request with a JSON body (the "payload")
  2. Verify the request is authentic (using a signature), so randoms
     on the internet can't fake events by hitting your URL
  3. Respond FAST with a 2xx status code, then do slow work later
     (senders usually retry aggressively if they don't get a quick 200)

Run it with:
    uvicorn receiver:app --reload --port 8000
"""

import hashlib
import hmac
import json

from fastapi import FastAPI, Header, HTTPException, Request

app = FastAPI(title="Webhook Receiver Demo")

# In real life, this secret is generated once and shared privately between
# you and the service sending the webhook (e.g. you paste it into their
# dashboard). Both sides use it to sign/verify payloads so an attacker
# who doesn't know the secret can't forge a fake event.
WEBHOOK_SECRET = "my-shared-secret-123"

# Just an in-memory list so we can see what arrived. A real app would
# write to a database or push to a queue instead.
received_events = []


def verify_signature(raw_body: bytes, signature_header: str) -> bool:
    """
    Recompute the HMAC signature ourselves from the raw request body
    and compare it to the one the sender attached in the header.
    If they match, we know:
      (a) the payload wasn't tampered with in transit, and
      (b) it was actually signed by someone who knows our shared secret
    """
    expected = hmac.new(
        key=WEBHOOK_SECRET.encode(),
        msg=raw_body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    # hmac.compare_digest avoids leaking timing info that could help
    # an attacker guess the correct signature byte-by-byte.
    return hmac.compare_digest(expected, signature_header or "")


@app.post("/webhook")
async def handle_webhook(
    request: Request,
    x_webhook_signature: str = Header(default=None),
):
    raw_body = await request.body()

    if not verify_signature(raw_body, x_webhook_signature):
        # 401 tells the sender "I got it, but I don't trust it" —
        # don't retry this one, something is wrong with the signature.
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = json.loads(raw_body)
    event_type = payload.get("event_type", "unknown")

    print(f"✅ Verified webhook received: {event_type}")
    print(json.dumps(payload, indent=2))

    # This is where you'd normally do something with the event, e.g.:
    #   if event_type == "payment.succeeded": mark_order_as_paid(payload)
    # Keep this part fast — if it's slow, hand off to a background task
    # / queue instead of doing it inline here.
    received_events.append(payload)

    # Any 2xx response tells the sender "got it, don't retry."
    return {"status": "received", "event_type": event_type}


@app.get("/events")
async def list_events():
    """Just a helper endpoint so we can peek at what's arrived so far."""
    return {"count": len(received_events), "events": received_events}