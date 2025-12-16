import os
import requests
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request

app = FastAPI(title="web-ui", version="0.1.0")
templates = Jinja2Templates(directory="app/templates")

BOOKING_SERVICE_URL = os.getenv("BOOKING_SERVICE_URL", "http://booking:8000")


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/ui/bookings", response_class=HTMLResponse)
def create_booking_ui(
    facility_id: str = Form(...),
    date: str = Form(...),
    time: str = Form(...),
    user_id: str = Form(...),
):
    payload = {
        "facility_id": facility_id,
        "date": date,
        "time": time,
        "user_id": user_id,
    }

    try:
        r = requests.post(f"{BOOKING_SERVICE_URL}/bookings", json=payload, timeout=4)
        r.raise_for_status()
        data = r.json()
        return f"""
        <div class="card">
          ✅ Prenotazione creata<br/>
          booking_id: <code>{data.get("booking_id")}</code><br/>
          status: <code>{data.get("status")}</code>
        </div>
        """
    except Exception as e:
        return f"""
        <div class="card" style="border-color:#f5b5b5">
          ❌ Errore chiamando booking-service: <code>{str(e)}</code>
        </div>
        """
