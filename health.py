"""Minimal Flask HTTP endpoint for Render and UptimeRobot health checks."""
import os

from flask import Flask, jsonify

app = Flask(__name__)


@app.get("/")
def home():
    return jsonify(status="ok", service="restaurant-bot"), 200


@app.get("/health")
def health():
    return jsonify(status="healthy"), 200


def run_health_server() -> None:
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
