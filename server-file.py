from flask import Flask, jsonify
import logging
import os

app = Flask(__name__)
logger = logging.getLogger("ArbitrageBot.Server")

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for heartbeat pings"""
    return jsonify({"status": "healthy", "service": "sports-arbitrage-bot"})

def start_server():
    """Start the Flask server for health checks"""
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    start_server()
