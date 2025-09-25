# ClickHouse database container with init scripts
FROM clickhouse/clickhouse-server:latest

# Copy initialization scripts
COPY docker/database/init/ /docker-entrypoint-initdb.d/

# Create data directories
RUN mkdir -p /var/lib/clickhouse/data /var/lib/clickhouse/metadata /var/lib/clickhouse/tmp

# Set proper permissions
RUN chown -R clickhouse:clickhouse /var/lib/clickhouse

# Environment variables
ENV CLICKHOUSE_DB=job_automation
ENV CLICKHOUSE_USER=automation_user
ENV CLICKHOUSE_PASSWORD=secure_password_123

EXPOSE 8123 9000

CMD ["clickhouse-server"]