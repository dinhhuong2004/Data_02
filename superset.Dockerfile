FROM apache/superset:latest

USER root
RUN uv pip install --system --python /app/.venv/bin/python clickhouse-connect
USER superset
