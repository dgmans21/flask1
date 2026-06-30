FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py

# ML 패키지 wheel 설치용 최소 도구
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY app.py db.py ./
COPY routes/ routes/
COPY ai_route/ ai_route/
COPY models/ models/
COPY templates/ templates/
COPY static/ static/

EXPOSE 5000

# DB 접속 정보는 실행 시 환경변수로 주입 (.env는 이미지에 넣지 않음)
# 예: DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "app:app"]
