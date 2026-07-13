# Webhook Demo (FastAPI)

Two tiny scripts that show both sides of a webhook: a **receiver** (server
that listens for events) and a **sender** (simulates a service firing
events at it), with HMAC signature verification like Stripe/GitHub use.

## 1. Install dependencies

```bash
pip install fastapi uvicorn httpx
```

## 2. Start the receiver (Terminal 1)

```bash
uvicorn receiver:app --reload --port 8000
```

Leave this running. You should see:
```
Uvicorn running on http://127.0.0.1:8000
```

You can also open http://127.0.0.1:8000/docs in a browser to see FastAPI's
auto-generated interactive API docs for the `/webhook` endpoint.

## 3. Run the sender (Terminal 2, separate window)

```bash
python sender.py
```

Watch Terminal 1 — you'll see the receiver print each event as it arrives,
verify its signature, and log it. The sender also fires one *forged*
request with a bad signature at the end, and you'll see the receiver
reject it with 401.

## 4. Poke around

- Visit http://127.0.0.1:8000/events in your browser to see everything
  the receiver has logged so far.
- Try changing `WEBHOOK_SECRET` in `sender.py` only (not `receiver.py`) —
  rerun `sender.py` and watch every event get rejected as unauthorized.
- Try removing the `X-Webhook-Signature` header entirely in `sender.py`
  and see how the receiver handles a missing signature.

## 5. Going further: expose it to the real internet

To have a *real* external service (GitHub, Stripe, etc.) send webhooks to
your local receiver, your `localhost` needs a public URL. Use a tunnel:

```bash
# install ngrok, then:
ngrok http 8000
```

It'll give you a URL like `https://abcd1234.ngrok-free.app` — paste
`https://abcd1234.ngrok-free.app/webhook` into the webhook settings of
whatever service you want to receive real events from.