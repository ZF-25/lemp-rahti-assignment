from flask import Flask, jsonify, request
import os
import mysql.connector
import redis
import json
import logging
import time

app = Flask(__name__)


# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s"
)
logger = logging.getLogger(__name__)


# Database configuration
DB_HOST = os.getenv("DB_HOST", "db")
DB_USER = os.getenv("DB_USER", "appuser")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME", "appdb")

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "redis")

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=6379,
    decode_responses=True
)


def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )


# Request logging
@app.before_request
def start_request_timer():
    request.start_time = time.perf_counter()


@app.after_request
def log_request(response):
    duration_ms = round(
        (time.perf_counter() - request.start_time) * 1000,
        2
    )

    logger.info(json.dumps({
        "event": "http_request",
        "method": request.method,
        "path": request.path,
        "status": response.status_code,
        "duration_ms": duration_ms
    }))

    return response


# Kubernetes liveness probe
@app.get("/healthz")
def healthz():
    return jsonify({"status": "ok"}), 200


# Kubernetes readiness probe
@app.get("/readyz")
def readyz():
    try:
        conn = get_db_connection()
        conn.close()

        return jsonify({"status": "ready"}), 200

    except Exception:
        return jsonify({"status": "not ready"}), 503


# Existing Week 5 health endpoint
@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/api/messages")
def get_messages():
    cached_messages = redis_client.get("messages")

    if cached_messages:
        return jsonify(json.loads(cached_messages))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT id, message, created_at
        FROM messages
        ORDER BY id DESC
        """
    )

    messages = cursor.fetchall()

    redis_client.set(
        "messages",
        json.dumps(messages, default=str)
    )

    cursor.close()
    conn.close()

    return jsonify(messages)


@app.post("/api/messages")
def create_message():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"error": "Message cannot be empty"}), 400

    if len(message) > 255:
        return jsonify({"error": "Message is too long"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO messages (message) VALUES (%s)",
        (message,)
    )

    conn.commit()

    redis_client.delete("messages")

    new_id = cursor.lastrowid

    cursor.close()
    conn.close()

    return jsonify({
        "id": new_id,
        "message": message
    }), 201


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8000,
        debug=True
    )