"""
Test receiver for "Call a URL" — run this to test both GET and POST from the Scheduler.

Run in a separate terminal:
  python test_receiver.py

Then in the Scheduler (http://localhost:8000) create schedules that call:
  http://localhost:5001/test

After the Scheduler runs a POST, open http://localhost:5001/last to see the last requests (including the POST body).
"""
from datetime import datetime

from fastapi import FastAPI, Request

app = FastAPI(title="Test Receiver")

# Store last 10 requests so you can see POST body in the browser
_last_requests = []


def _add(method: str, body=None):
    _last_requests.append({"method": method, "body": body, "when": datetime.now().isoformat()})
    if len(_last_requests) > 10:
        _last_requests.pop(0)


@app.get("/test")
def get_test():
    """Called when Scheduler uses 'Call a URL' with Send data? No (GET)."""
    _add("GET", None)
    msg = f"[{datetime.now().isoformat()}] GET /test received — no data sent"
    print(msg)
    return {"ok": True, "message": "GET received", "when": datetime.now().isoformat()}


@app.post("/test")
async def post_test(request: Request):
    """Called when Scheduler uses 'Call a URL' with Send data? Yes (POST + JSON)."""
    body = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
    _add("POST", body)
    msg = f"[{datetime.now().isoformat()}] POST /test received — body: {body}"
    print(msg)
    return {"ok": True, "message": "POST received", "body": body, "when": datetime.now().isoformat()}


@app.get("/last")
def last_requests():
    """Open this page in the browser after the Scheduler runs to see the last GET/POST requests (including POST body)."""
    return {"message": "Last requests to /test (refresh after Scheduler runs)", "requests": _last_requests}


if __name__ == "__main__":
    import uvicorn
    print("Test receiver running at http://localhost:5001")
    print("Scheduler should call: http://localhost:5001/test")
    print("Watch this terminal to see GET and POST requests.\n")
    uvicorn.run(app, host="127.0.0.1", port=5001)
