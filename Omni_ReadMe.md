# Omni Webhook Practice

Mimics the exact request shapes Omni's webhook deliveries send, based on
their published docs, so you can build and test your receiver before the
client sends you anything real.

## Install

```bash
pip install fastapi uvicorn httpx
```

## Run

Terminal 1 — start your receiver:
```bash
uvicorn omni_receiver:app --reload --port 8000
```

Terminal 2 — simulate Omni sending you deliveries:
```bash
python omni_sender.py
```

Check `received_files/` afterward — the CSV and PNG will show up there,
saved from the raw request body exactly like a real Omni delivery would
arrive.

## Key things to remember for the real integration

- **Branch on `Content-Type`.** `application/json` → parse `{"url": ...}`.
  Anything else → treat the whole body as raw binary file content.
- **Use `X-Filename`** to know what to name the saved file — Omni doesn't
  put this in the URL or JSON, only in that header.
- **Always return HTTP 200.** Any other status makes Omni retry or mark
  the delivery failed — don't do slow processing before responding;
  save the file / queue the work, then return 200.
- **Multi-query CSV dashboards arrive as ZIP** (`Content-Type:
  application/zip`) — if the client's dashboard has multiple charts,
  expect a zip, not a single CSV.
- **No signature verification is documented.** Unlike Stripe/GitHub,
  Omni relies on you allowlisting its IP addresses at your firewall, not
  on a shared-secret signature. Ask the client which IPs to allow (found
  in their Omni Settings > Connections page) once you're ready to go live.
- **Get a public URL before going live.** Use `ngrok http 8000` (or
  deploy it somewhere) so Omni's servers can actually reach your local
  machine during testing with the client.

## Next step once you have client details

Ask the client:
1. Is it a **schedule** or **alert** delivery?
2. What **format**? (link-only, CSV, PDF, PNG, XLSX)
3. Single dashboard/chart, or multi-query (→ expect a ZIP)?

That tells you exactly which branch of `omni_receiver.py` will actually
get exercised in production.