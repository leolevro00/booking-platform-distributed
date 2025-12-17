FROM python:3.12-slim

WORKDIR /app

COPY services/availability/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/availability/app ./app
COPY shared ./shared

ENV PYTHONPATH=/app

CMD ["python", "app/main.py"]
