FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY api/ ./api/

ENV DB_PATH=/data/trades.db
ENV PYTHONUNBUFFERED=1

EXPOSE 5000

CMD ["python", "backend/app.py"]
