import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

logger = logging.getLogger("ArbitrageBot.EmailSender")

def create_html_for_opportunity(opportunity):
    """Create HTML content for an arbitrage opportunity email"""
    
    if opportunity["type"] == "error":
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .error {{ color: red; font-weight: bold; }}
                .container {{ padding: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2 class="error">Sports Arbitrage Bot Error</h2>
                <p><strong>Time:</strong> {opportunity["timestamp"]}</p>
                <p><strong>Error Message:</strong> {opportunity["message"]}</p>
                <p>Please check the logs and fix the issue.</p>
            </div>
        </body>
        </html>
        """
        return html
    
    # Format the selections table
    selections_html = ""
    for selection in opportunity["selections"]:
        selections_html += f"""
        <tr>
            <td>{selection["selection"]}</td>
            <td>{selection["bookmaker"]}</td>
            <td>{selection["odds"]}</td>
            <td>${selection["recommended_stake"]:.2f}</td>
        </tr>
        """
    
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            .container {{ padding: 20px; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .highlight {{ background-color: #e6f7ff; }}
            .profit {{ color: green; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Sports Arbitrage Opportunity Found!</h2>
            
            <p><strong>Event:</strong> {opportunity["event_name"]}</p>
            <p><strong>Sport:</strong> {opportunity["sport"].capitalize()}</p>
            <p><strong>Market:</strong> {opportunity["market"].capitalize()}</p>
            <p><strong>Arbitrage Percentage:</strong> {opportunity["arbitrage_percentage"]:.2f}%</p>
            <p><strong>Guaranteed Profit (per $100):</strong> <span class="profit">${opportunity["guaranteed_profit_per_100"]:.2f}</span></p>
            <p><strong>Time Found:</strong> {opportunity["timestamp"]}</p>
            
            <h3>Betting Details:</h3>
            <table>
                <tr>
                    <th>Selection</th>
                    <th>Bookmaker</th>
                    <th>Odds</th>
                    <th>Recommended Stake</th>
                </tr>
                {selections_html}
            </table>
            
            <p><em>This is an automated message from your Sports Arbitrage Bot. Act quickly as odds may change!</em></p>
        </div>
    </body>
    </html>
    """
    
    return html

def send_email(opportunity):
    """Send email notification about an arbitrage opportunity"""
    try:
        # Get email configuration from environment variables
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        sender_email = os.getenv("SENDER_EMAIL")
        sender_password = os.getenv("SENDER_PASSWORD")
        recipient_email = os.getenv("RECIPIENT_EMAIL")
        
        # Ensure we have the necessary configuration
        if not all([sender_email, sender_password, recipient_email]):
            logger.error("Missing email configuration. Check your environment variables.")
            return False
        
        # Create email message
        msg = MIMEMultipart("alternative")
        
        if opportunity["type"] == "error":
            msg["Subject"] = f"ALERT: Sports Arbitrage Bot Error - {opportunity['timestamp']}"
        else:
            arb_pct = opportunity["arbitrage_percentage"]
            sport = opportunity["sport"].capitalize()
            msg["Subject"] = f"ARBITRAGE: {arb_pct:.2f}% opportunity in {sport} - Act Now!"
        
        msg["From"] = sender_email
        msg["To"] = recipient_email
        
        # Create HTML content
        html_content = create_html_for_opportunity(opportunity)
        html_part = MIMEText(html_content, "html")
        msg.attach(html_part)
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
            
        logger.info(f"Email sent successfully to {recipient_email}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return False

def send_test_email():
    """Send a test email when the bot first starts"""
    test_opportunity = {
        "type": "test",
        "event_name": "Bot Activation Test",
        "sport": "system",
        "market": "test",
        "arbitrage_percentage": 0.0,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "selections": [
            {
                "selection": "Test Selection",
                "bookmaker": "Test Bookmaker",
                "odds": 2.0,
                "recommended_stake": 100.0
            }
        ],
        "guaranteed_profit_per_100": 0.0
    }
    
    # Override the subject for the test email
    original_subject = MIMEMultipart.get_unixfrom
    
    try:
        MIMEMultipart.__setitem__ = lambda self, name, val: super(MIMEMultipart, self).__setitem__(
            name, 
            "Sports Arbitrage Bot Activated! 🚀" if name == "Subject" else val
        )
        
        return send_email(test_opportunity)
    finally:
        MIMEMultipart.__setitem__ = original_subject
