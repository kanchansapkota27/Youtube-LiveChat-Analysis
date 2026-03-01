FROM apache/superset:latest

USER root

# psycopg2-binary lets Superset talk to PostgreSQL
RUN pip install --no-cache-dir psycopg2-binary

COPY init.sh /app/init.sh
# Strip Windows CRLF line endings so the script runs cleanly in Linux
RUN tr -d '\r' < /app/init.sh > /tmp/init_clean.sh && mv /tmp/init_clean.sh /app/init.sh && chmod +x /app/init.sh

USER superset

ENTRYPOINT []
CMD ["bash", "/app/init.sh"]
