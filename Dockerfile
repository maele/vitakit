# VitaKit — open-source CV studio
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Non-root runtime user (uid 1000 matches the default Linux Mint user)
RUN useradd -u 1000 -m vitakit \
    && mkdir -p /app/data \
    && chown -R vitakit:vitakit /app
USER vitakit

EXPOSE 5050

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5050/healthz')" || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:5050", "--workers", "2", "app:app"]
