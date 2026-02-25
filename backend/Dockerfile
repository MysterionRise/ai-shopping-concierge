FROM python:3.13-slim-bookworm

WORKDIR /app
ENV PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies only (cached unless pyproject.toml changes)
COPY pyproject.toml .
RUN python -c "\
import tomllib;\
data = tomllib.load(open('pyproject.toml', 'rb'));\
open('requirements.txt', 'w').write('\n'.join(data['project']['dependencies']))\
" && pip install --no-cache-dir -r requirements.txt && rm requirements.txt

# Create non-root user
RUN addgroup --system appuser && adduser --system --ingroup appuser appuser

# Copy application code
COPY . .

RUN chmod +x entrypoint.sh && chown -R appuser:appuser /app

EXPOSE 8080

USER appuser

ENTRYPOINT ["./entrypoint.sh"]
