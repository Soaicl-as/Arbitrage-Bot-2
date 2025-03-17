import requests
import logging
from bs4 import BeautifulSoup
import json
import time
from fake_useragent import UserAgent
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger("ArbitrageBot.OddsFetcher")

# Configure headers with rotating user agents to avoid detection
ua = UserAgent()

# List of bookmakers to check
BOOKMAKERS = ["bet365", "betmgm", "stake"]

# Sports to monitor
SPORTS = [
    "soccer", "basketball", "hockey", "baseball", "tennis", 
    "football", "mma", "boxing", "golf", "rugby"
]

def get_random_headers():
    """Generate random headers to avoid detection"""
    return {
        "User-Agent": ua.random,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
    }

def fetch_bet365_odds():
    """Fetch odds from Bet365 for all sports"""
    logger.info("Fetching odds from Bet365")
    odds_data = []
    
    try:
        # In a real implementation, you would use an API or scrape the website
        # This is a simplified example
        for sport in SPORTS:
            # Use proxies and rotate headers to avoid IP bans
            headers = get_random_headers()
            
            # Add proper URL and scraping logic here
            # For demonstration purposes, we're using mock data
            time.sleep(0.5)  # Avoid rate limiting
            
            # Mock data for demonstration
            # In real implementation, parse the actual response
            events_count = 5  # Mock number of events
            for i in range(events_count):
                odds_data.append({
                    "bookmaker": "bet365",
                    "sport": sport,
                    "event_id": f"bet365_{sport}_{i}",
                    "event_name": f"Team A vs Team B ({sport.capitalize()})",
                    "market": "moneyline",
                    "selection": "Team A",
                    "odds": 2.0 + (i * 0.1),
                    "timestamp": time.time()
                })
                odds_data.append({
                    "bookmaker": "bet365",
                    "sport": sport,
                    "event_id": f"bet365_{sport}_{i}",
                    "event_name": f"Team A vs Team B ({sport.capitalize()})",
                    "market": "moneyline",
                    "selection": "Team B",
                    "odds": 1.8 + (i * 0.1),
                    "timestamp": time.time()
                })
    except Exception as e:
        logger.error(f"Error fetching Bet365 odds: {str(e)}")
    
    return odds_data

def fetch_betmgm_odds():
    """Fetch odds from BetMGM for all sports"""
    logger.info("Fetching odds from BetMGM")
    odds_data = []
    
    try:
        # Similar implementation as fetch_bet365_odds
        for sport in SPORTS:
            headers = get_random_headers()
            time.sleep(0.5)
            
            events_count = 5
            for i in range(events_count):
                odds_data.append({
                    "bookmaker": "betmgm",
                    "sport": sport,
                    "event_id": f"betmgm_{sport}_{i}",
                    "event_name": f"Team A vs Team B ({sport.capitalize()})",
                    "market": "moneyline",
                    "selection": "Team A",
                    "odds": 1.95 + (i * 0.1),
                    "timestamp": time.time()
                })
                odds_data.append({
                    "bookmaker": "betmgm",
                    "sport": sport,
                    "event_id": f"betmgm_{sport}_{i}",
                    "event_name": f"Team A vs Team B ({sport.capitalize()})",
                    "market": "moneyline",
                    "selection": "Team B",
                    "odds": 1.85 + (i * 0.1),
                    "timestamp": time.time()
                })
    except Exception as e:
        logger.error(f"Error fetching BetMGM odds: {str(e)}")
    
    return odds_data

def fetch_stake_odds():
    """Fetch odds from Stake for all sports"""
    logger.info("Fetching odds from Stake")
    odds_data = []
    
    try:
        # Similar implementation as fetch_bet365_odds
        for sport in SPORTS:
            headers = get_random_headers()
            time.sleep(0.5)
            
            events_count = 5
            for i in range(events_count):
                odds_data.append({
                    "bookmaker": "stake",
                    "sport": sport,
                    "event_id": f"stake_{sport}_{i}",
                    "event_name": f"Team A vs Team B ({sport.capitalize()})",
                    "market": "moneyline",
                    "selection": "Team A",
                    "odds": 2.05 + (i * 0.1),
                    "timestamp": time.time()
                })
                odds_data.append({
                    "bookmaker": "stake",
                    "sport": sport,
                    "event_id": f"stake_{sport}_{i}",
                    "event_name": f"Team A vs Team B ({sport.capitalize()})",
                    "market": "moneyline",
                    "selection": "Team B",
                    "odds": 1.75 + (i * 0.1),
                    "timestamp": time.time()
                })
    except Exception as e:
        logger.error(f"Error fetching Stake odds: {str(e)}")
    
    return odds_data

def normalize_event_names(odds_data):
    """Normalize event names to match events across bookmakers"""
    # In a real implementation, you would need more sophisticated name matching
    # This is a simplified example
    for item in odds_data:
        # Remove bookmaker-specific formatting
        name = item["event_name"]
        # Standardize team order (alphabetical)
        if "vs" in name:
            teams = name.split("vs")
            teams = [t.strip() for t in teams]
            teams.sort()
            item["normalized_name"] = f"{teams[0]} vs {teams[1]} ({item['sport'].capitalize()})"
        else:
            item["normalized_name"] = name
    
    return odds_data

def fetch_all_odds():
    """Fetch odds from all bookmakers in parallel"""
    logger.info("Fetching odds from all bookmakers")
    
    # Use thread pool to fetch odds from all bookmakers concurrently
    with ThreadPoolExecutor(max_workers=len(BOOKMAKERS)) as executor:
        results = list(executor.map(
            lambda f: f(), 
            [fetch_bet365_odds, fetch_betmgm_odds, fetch_stake_odds]
        ))
    
    # Combine and normalize all odds data
    all_odds = []
    for result in results:
        all_odds.extend(result)
    
    return normalize_event_names(all_odds)
