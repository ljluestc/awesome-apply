#!/usr/bin/env python3
"""
Health check endpoints for microservices
"""
import json
import time
import psutil
import clickhouse_connect
from flask import Flask, jsonify
from datetime import datetime
import os

app = Flask(__name__)

def check_database_connection():
    """Check ClickHouse database connection"""
    try:
        client = clickhouse_connect.get_client(
            host=os.getenv('CLICKHOUSE_HOST', 'localhost'),
            port=int(os.getenv('CLICKHOUSE_PORT', 8123)),
            username=os.getenv('CLICKHOUSE_USER', 'default'),
            password=os.getenv('CLICKHOUSE_PASSWORD', ''),
            database=os.getenv('CLICKHOUSE_DB', 'default')
        )

        # Test connection with a simple query
        result = client.query('SELECT 1 as test')
        return result.first_row[0] == 1
    except Exception as e:
        print(f"Database health check failed: {e}")
        return False

def check_system_resources():
    """Check system resource usage"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available_gb': round(memory.available / (1024**3), 2),
            'disk_percent': disk.percent,
            'disk_free_gb': round(disk.free / (1024**3), 2)
        }
    except Exception as e:
        print(f"System resource check failed: {e}")
        return None

@app.route('/health', methods=['GET'])
def health_check():
    """Main health check endpoint"""
    start_time = time.time()

    # Check database connection
    db_healthy = check_database_connection()

    # Check system resources
    system_resources = check_system_resources()

    # Calculate response time
    response_time = round((time.time() - start_time) * 1000, 2)  # ms

    # Determine overall health status
    is_healthy = db_healthy and system_resources is not None

    health_data = {
        'status': 'healthy' if is_healthy else 'unhealthy',
        'timestamp': datetime.utcnow().isoformat(),
        'response_time_ms': response_time,
        'checks': {
            'database': {
                'status': 'healthy' if db_healthy else 'unhealthy',
                'type': 'clickhouse'
            },
            'system_resources': {
                'status': 'healthy' if system_resources else 'unhealthy',
                'data': system_resources
            }
        },
        'service': {
            'name': os.getenv('SERVICE_NAME', 'job-automation'),
            'version': os.getenv('SERVICE_VERSION', '1.0.0')
        }
    }

    status_code = 200 if is_healthy else 503
    return jsonify(health_data), status_code

@app.route('/health/ready', methods=['GET'])
def readiness_check():
    """Kubernetes readiness probe endpoint"""
    # Check if service is ready to accept traffic
    db_healthy = check_database_connection()

    if db_healthy:
        return jsonify({
            'status': 'ready',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    else:
        return jsonify({
            'status': 'not_ready',
            'reason': 'database_unavailable',
            'timestamp': datetime.utcnow().isoformat()
        }), 503

@app.route('/health/live', methods=['GET'])
def liveness_check():
    """Kubernetes liveness probe endpoint"""
    # Simple check to ensure the service is alive
    return jsonify({
        'status': 'alive',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@app.route('/metrics', methods=['GET'])
def metrics():
    """Prometheus-style metrics endpoint"""
    try:
        system_resources = check_system_resources()
        if not system_resources:
            return "# Metrics unavailable\n", 503

        metrics_text = f"""# HELP cpu_usage_percent Current CPU usage percentage
# TYPE cpu_usage_percent gauge
cpu_usage_percent {system_resources['cpu_percent']}

# HELP memory_usage_percent Current memory usage percentage
# TYPE memory_usage_percent gauge
memory_usage_percent {system_resources['memory_percent']}

# HELP memory_available_bytes Available memory in bytes
# TYPE memory_available_bytes gauge
memory_available_bytes {system_resources['memory_available_gb'] * 1024**3}

# HELP disk_usage_percent Current disk usage percentage
# TYPE disk_usage_percent gauge
disk_usage_percent {system_resources['disk_percent']}

# HELP disk_free_bytes Free disk space in bytes
# TYPE disk_free_bytes gauge
disk_free_bytes {system_resources['disk_free_gb'] * 1024**3}

# HELP service_health_status Service health status (1 = healthy, 0 = unhealthy)
# TYPE service_health_status gauge
service_health_status {1 if check_database_connection() else 0}
"""

        return metrics_text, 200, {'Content-Type': 'text/plain; charset=utf-8'}
    except Exception as e:
        return f"# Error generating metrics: {e}\n", 500

if __name__ == '__main__':
    # Run health check server
    app.run(host='0.0.0.0', port=8080, debug=False)