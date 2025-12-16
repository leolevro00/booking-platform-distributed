FROM python:3.12-slim

WORKDIR /app

COPY services/booking/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/booking/app ./app
COPY shared ./shared

ENV PYTHONPATH=/app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
