"""
OMNI WEBHOOK RECEIVER (practice)
=================================
This mimics what YOUR server needs to do to receive deliveries from Omni.

Per Omni's docs, there are two very different request shapes to handle:

  1. LINK-ONLY delivery:
     Content-Type: application/json
     Body: {"url": "<dashboard_url>"}

  2. FILE delivery (CSV / PDF / PNG / XLSX / ZIP):
     Content-Type: the actual file's MIME type (e.g. text/csv, application/pdf)
     Content-Length: size in bytes
     X-Filename: original filename
     Body: the RAW FILE BYTES, not JSON — streamed directly

  Omni also explicitly says: you MUST return HTTP 200, or it will retry /
  mark the delivery as failed. There's no signature/secret verification
  documented (unlike Stripe/GitHub) — Omni instead expects you to
  restrict access via IP allowlisting on your firewall.

Run it with:
    uvicorn omni_receiver:app --reload --port 8000
"""

import json
from pathlib import Path

from fastapi import FastAPI, Header, Request, Response

app = FastAPI(title="Omni Webhook Receiver (practice)")

SAVE_DIR = Path(__file__).parent / "received_files"
SAVE_DIR.mkdir(exist_ok=True)

received_log = []


@app.post("/omni-webhook")
async def handle_omni_delivery(
    request: Request,
    content_type: str = Header(default=""),
    x_filename: str = Header(default=None),
):
    raw_body = await request.body()

    if content_type.startswith("application/json"):
        # --- Link-only delivery ---
        payload = json.loads(raw_body)
        dashboard_url = payload.get("url")
        print(f"🔗 Link-only delivery received: {dashboard_url}")
        received_log.append({"type": "link", "url": dashboard_url})

    else:
        # --- File delivery (csv, pdf, png, xlsx, zip, ...) ---
        filename = x_filename or "unnamed_file"
        save_path = SAVE_DIR / filename
        save_path.write_bytes(raw_body)

        print(f"📄 File delivery received: {filename}")
        print(f"    Content-Type: {content_type}")
        print(f"    Size: {len(raw_body)} bytes")
        print(f"    Saved to: {save_path}")

        received_log.append(
            {
                "type": "file",
                "filename": filename,
                "content_type": content_type,
                "size_bytes": len(raw_body),
            }
        )

    # IMPORTANT: Omni requires a 200 response or it will retry/fail the
    # delivery. FastAPI returns 200 by default for a normal return, but
    # being explicit here to underline why it matters.
    return Response(status_code=200, content="OK")


@app.get("/deliveries")
async def list_deliveries():
    """Peek at everything received so far."""
    return {"count": len(received_log), "deliveries": received_log}