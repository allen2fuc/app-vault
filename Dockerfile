FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
COPY templates/ .
COPY static/ .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ .
COPY apps.json .

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
