FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml requirements.txt ./
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080
ENV PORT=8080

# Create startup script
RUN echo '#!/bin/bash\n\
echo "Starting backend container..."\n\
\n\
# Run migrations\n\
echo "Running database migrations..."\n\
alembic upgrade head || echo "⚠️ Migration failed, continuing..."\n\
\n\
echo "Starting application..."\n\
uvicorn app.main:app --host 0.0.0.0 --port 8080 --loop uvloop' > /app/start.sh \
    && chmod +x /app/start.sh

CMD ["/app/start.sh"]
