# syntax=docker/dockerfile:1
# Build com contexto na raiz do monorepo (ver local-apps/docker-compose.yml).

FROM python:3.12-slim

# tzdata: o core grava horarios com o offset do fuso do processo; sem isso o
# container usaria UTC e o "dia" viraria as 21h (horario de Brasilia).
RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY packages/time-tracker-core ./packages/time-tracker-core
COPY packages/time-tracker-api ./packages/time-tracker-api
RUN pip install --no-cache-dir ./packages/time-tracker-core ./packages/time-tracker-api

# Banco SQLite num volume (/data), pertencente ao usuario nao-root.
RUN useradd --uid 1000 --create-home app && mkdir /data && chown app /data
USER app

ENV TZ=America/Sao_Paulo \
    TIMETRACKER_DB=/data/time_tracker.db \
    TIMETRACKER_API_HOST=0.0.0.0 \
    TIMETRACKER_API_PORT=8000

VOLUME /data
EXPOSE 8000
CMD ["time-tracker-api"]
