import requests
import os
import logging
from datetime import datetime

logger = logging.getLogger("ArbitrageBot.Heartbeat")

def ping_heartbeat():
    """Send a heartbeat ping to keep the service alive on Render"""
    try:
        # Get the application URL from environment variables
        app_url = os.getenv("APP_URL")
        
        if not app_url:
            logger.warning("APP_URL environment variable not set for heartbeat")
            return False
        
        # Ping the service itself
        response = requests.get(f"{app_url}/health", timeout=10)
        
        if response.status_code == 200:
            logger.info(f"Heartbeat ping successful at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            return True
        else:
            logger.warning(f"Heartbeat ping failed with status code: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending heartbeat ping: {str(e)}")
        return False
