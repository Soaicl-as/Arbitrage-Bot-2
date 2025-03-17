# Sports Arbitrage Bot

A bot that scans Bet365, BetMGM, and Stake for arbitrage betting opportunities across all sports in the Canadian region. The bot runs 24/7 on Render, checks for opportunities every 2 minutes, and sends email notifications when profitable arbitrage situations are found.

## Features

- Scans multiple bookmakers (Bet365, BetMGM, Stake) for odds
- Monitors all available sports in the Canadian region
- Automatically identifies arbitrage opportunities
- Calculates optimal bet allocation to guarantee profit
- Sends detailed email notifications when opportunities are found
- Includes a heartbeat mechanism to keep the service running on Render
- Self-monitoring with error notifications

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/sports-arbitrage-bot.git
cd sports-arbitrage-bot
```

### 2. Configure Environment Variables

Copy the example env file and fill in your details:

```bash
cp .env.example .env
```

Edit the `.env` file with your email settings:

```
# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password
RECIPIENT_EMAIL=your-email@gmail.com

# Application URL for heartbeat (Set this in Render)
APP_URL=https://your-app-name.onrender.com

# Port for the health check server
PORT=10000
```

**Note:** For Gmail, you'll need to use an "App Password" rather than your regular password. See [Google's documentation](https://support.google.com/accounts/answer/185833) for instructions.

### 3. Deploy to Render

1. Push your code to GitHub
2. Create a new Web Service on Render
3. Connect your GitHub repository
4. Set the following:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn --workers=1 --threads=2 --timeout=120 "server:app" & python main.py`
5. Add your environment variables in the Render dashboard
6. Deploy the service

### 4. Local Testing (Optional)

To test locally before deploying:

```bash
pip install -r requirements.txt
python main.py
```

## How It Works

1. The bot fetches odds from multiple bookmakers every 2 minutes
2. It matches events across bookmakers and normalizes the data
3. For each market, it finds the best available odds for each outcome
4. It calculates the arbitrage percentage and potential profit
5. If an opportunity is found, it sends a detailed email with betting instructions
6. A heartbeat ping runs every 3 minutes to keep the service active on Render

## Customization

- Add more bookmakers in `odds_fetcher.py`
- Adjust the arbitrage threshold in `arbitrage_finder.py`
- Modify email templates in `email_sender.py`
- Change the checking frequency in `main.py`

## Troubleshooting

- **Bot not sending emails**: Check SMTP settings and password
- **Missing opportunities**: Adjust the normalization algorithm for event names
- **Service shutting down**: Ensure the heartbeat URL is correctly set
- **Bookmaker blocking requests**: Modify the request headers and implement proxies

## License

MIT License
