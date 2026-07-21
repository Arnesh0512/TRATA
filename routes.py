from flask import Flask, jsonify, request

app = Flask(__name__)



@app.get("/")
def home():
    return jsonify({"message": "Cyber Resilience backend is running"})


VALID_API_KEYS = ["demo-key", "trata_live_8K9X_Q2N4_P7RM"]

@app.post("/api/auth/validate")
def validate_api_key(data=None):
    data = data if data is not None else (request.get_json(silent=True) or {})

    return jsonify({
        "valid": True,
        "org_name": "National Grid Operations Centre",
        "agent_id": "agent_44f2",
        "permissions": ["ingest:pcap", "ingest:logs", "read:config"],
        "min_poll_interval_minutes": 5,
        "max_poll_interval_minutes": 30
    }), 200



@app.get("/api/config")
def get_agent_config():
    return jsonify({
        "poll_interval_minutes": 10,
        "pcap_watch_dir": "/var/log/agent/pcaps",
        "log_watch_dir": "/var/log/agent/logs",
        "last_sync": "2026-07-19T10:32:00Z"
    }), 200


@app.get("/api/settings")
def get_settings():
    return jsonify({
        "pcap_watch_dir": "/var/log/agent/pcaps",
        "pcap_time_window_minutes": 10,
        "log_watch_dir": "/var/log/agent/logs",
        "log_time_window_minutes": 10,
        "api_key_expiry_days": 30
    }), 200


@app.post("/api/settings/pcap-dir")
def update_pcap_dir(data):
    return jsonify({"status": "ok", "pcap_watch_dir": data.get("value", "")}), 200


@app.post("/api/settings/log-dir")
def update_log_dir(data=None):
    data = data if data is not None else (request.get_json(silent=True) or {})
    return jsonify({"status": "ok", "log_watch_dir": data.get("value", "")}), 200


@app.post("/api/settings/pcap-time-window")
def update_pcap_time_window(data=None):
    data = data if data is not None else (request.get_json(silent=True) or {})
    return jsonify({"status": "ok", "pcap_time_window_minutes": data.get("value", 10)}), 200


@app.post("/api/settings/log-time-window")
def update_log_time_window(data=None):
    data = data if data is not None else (request.get_json(silent=True) or {})
    return jsonify({"status": "ok", "log_time_window_minutes": data.get("value", 10)}), 200


@app.post("/api/settings/api-expiry")
def update_api_expiry(data=None):
    data = data if data is not None else (request.get_json(silent=True) or {})
    return jsonify({"status": "ok", "api_key_expiry_days": data.get("value", 30)}), 200


@app.post("/api/connection/disconnect")
def disconnect():
    return jsonify({"status": "ok"}), 200


@app.post("/api/connection/pause")
def pause_connection():
    return jsonify({"status": "paused"}), 200


@app.post("/api/connection/resume")
def resume_connection():
    return jsonify({"status": "resumed"}), 200


@app.post("/api/api-key/delete")
def delete_api_key():
    return jsonify({"status": "deleted"}), 200


@app.post("/api/heartbeat")
def heartbeat():
    return jsonify({"status": "ok"}), 200


__all__ = [
    "app",
    "home",
    "validate_api_key",
    "get_agent_config",
    "get_settings",
    "update_pcap_dir",
    "update_log_dir",
    "update_pcap_time_window",
    "update_log_time_window",
    "update_api_expiry",
    "disconnect",
    "pause_connection",
    "resume_connection",
    "delete_api_key",
    "heartbeat",
]


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
