"""
FAKE OMNI SENDER (practice)
============================
Mimics the requests Omni's servers will actually send you, based on
their published webhook docs — so you can build/test your receiver
without needing a live Omni account yet.

Simulates 3 deliveries:
  1. A link-only dashboard delivery
  2. A CSV file delivery (single query)
  3. A PNG file delivery (chart export)

Run the receiver first (uvicorn omni_receiver:app --reload --port 8000),
then:
    python omni_sender.py
"""

import json

import httpx

RECEIVER_URL = "http://127.0.0.1:8000/omni-webhook"


def send_link_only():
    payload = {"url": "https://your-company.omniapp.co/dashboards/abc123"}
    response = httpx.post(
        RECEIVER_URL,
        content=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    print(f"[link-only] -> status {response.status_code}")


def send_csv_file():
    # Simulate a small CSV export, exactly like Omni would stream raw
    # file bytes as the body with metadata in headers.
    csv_content = (
        "order_id,customer,total\n"
        "1001,Alice,29.99\n"
        "1002,Bob,49.50\n"
        "1003,Carol,15.00\n"
    ).encode()

    response = httpx.post(
        RECEIVER_URL,
        content=csv_content,
        headers={
            "Content-Type": "text/csv",
            "Content-Length": str(len(csv_content)),
            "X-Filename": "sales_report.csv",
        },
    )
    print(f"[csv file]  -> status {response.status_code}")


def send_png_file():
    # We don't have a real chart image handy, so we fake some bytes to
    # stand in for "PNG content" — the point is exercising the same
    # raw-body-streaming code path your receiver needs to handle.
    fake_png_bytes = b"\x89PNG\r\n\x1a\n" + b"FAKE_IMAGE_DATA_FOR_PRACTICE" * 20

    response = httpx.post(
        RECEIVER_URL,
        content=fake_png_bytes,
        headers={
            "Content-Type": "image/png",
            "Content-Length": str(len(fake_png_bytes)),
            "X-Filename": "quarterly_revenue_chart.png",
        },
    )
    print(f"[png file]  -> status {response.status_code}")


if __name__ == "__main__":
    send_link_only()
    send_csv_file()
    send_png_file()