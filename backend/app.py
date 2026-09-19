from flask import Flask, jsonify, request
import os
import mysql.connector

app = Flask(__name__)


DB_HOST = os.getenv("DB_HOST", "db")
DB_USER = os.getenv("DB_USER", "appuser")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME", "appdb")


def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/api/messages")
def get_messages():
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

    new_id = cursor.lastrowid

    cursor.close()
    conn.close()

    return jsonify({
        "id": new_id,
        "message": message
    }), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)