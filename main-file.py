import os
import time
import schedule
import threading
from datetime import datetime
from dotenv import load_dotenv
import logging
from odds_fetcher import fetch_all_odds
from arbitrage_finder import find_arbitrage_opportunities
from email_sender import send_email, send_test_email
from heartbeat import ping_heartbeat
from server import start_server

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("arbitrage_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ArbitrageBot")

# Track if we've sent the initial test email
test_email_sent = False

def check_for_arbitrage():
    """Main function to check for arbitrage opportunities"""
    global test_email_sent
    
    try:
        logger.info("Starting arbitrage check")
        
        # Send test email the first time the bot runs
        if not test_email_sent:
            send_test_email()
            test_email_sent = True
            logger.info("Test email sent successfully")
        
        # Fetch odds from all bookmakers
        all_odds = fetch_all_odds()
        logger.info(f"Fetched odds for {len(all_odds)} events")
        
        # Find arbitrage opportunities
        opportunities = find_arbitrage_opportunities(all_odds)
        
        # Send email if opportunities found
        if opportunities:
            logger.info(f"Found {len(opportunities)} arbitrage opportunities!")
            for opp in opportunities:
                send_email(opp)
        else:
            logger.info("No arbitrage opportunities found")
            
    except Exception as e:
        error_message = f"Error in arbitrage check: {str(e)}"
        logger.error(error_message)
        
        # Send error notification email
        try:
            send_email({
                "type": "error",
                "message": error_message,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        except Exception as email_error:
            logger.error(f"Failed to send error email: {str(email_error)}")

def start_flask_server():
    """Start the Flask server in a separate thread"""
    thread = threading.Thread(target=start_server)
    thread.daemon = True  # This ensures the thread will exit when the main program exits
    thread.start()
    logger.info("Flask server started in background thread")

def main():
    """Main entry point for the arbitrage bot"""
    logger.info("Starting Sports Arbitrage Bot")
    
    # Start the Flask server for health checks
    start_flask_server()
    
    # Run immediately on startup
    check_for_arbitrage()
    
    # Schedule regular checks
    schedule.every(2).minutes.do(check_for_arbitrage)
    schedule.every(3).minutes.do(ping_heartbeat)
    
    logger.info("Scheduled tasks have been set up")
    
    # Keep the script running
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {str(e)}")
        
        # Attempt to send error notification
        try:
            send_email({
                "type": "error",
                "message": f"Bot crashed with error: {str(e)}",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        except:
            pass
        
        raise

if __name__ == "__main__":
    main()
