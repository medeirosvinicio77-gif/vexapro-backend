FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-prod.txt .
RUN pip install --no-cache-dir -r requirements-prod.txt

COPY . .

RUN mkdir -p uploads outputs

EXPOSE 8000

CMD ["sh", "-c", "python init_database.py && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]