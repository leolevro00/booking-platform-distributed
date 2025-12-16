FROM python:3.12-slim

WORKDIR /app

COPY services/web-ui/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/web-ui/app ./app
ENV PYTHONPATH=/app

EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
