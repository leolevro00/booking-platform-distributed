from fastapi import FastAPI

app = FastAPI(title="booking-service", version="0.1.0")

@app.get("/health")
def health():
    return {"status": "ok", "service": "booking"}
