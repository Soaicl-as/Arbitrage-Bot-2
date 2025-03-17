import requests
import logging
from bs4 import BeautifulSoup
import json
import time
import re
from fake_useragent import UserAgent
from concurrent.futures import ThreadPoolExecutor
import random
from datetime import datetime

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

# Proxy configuration - you would need to add your proxy service here
PROXIES = [
    # Add your proxies here, format: {"http": "http://user:pass@ip:port", "https": "https://user:pass@ip:port"}
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
        "DNT": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    }

def get_random_proxy():
    """Get a random proxy from the list"""
    if not PROXIES:
        return None
    return random.choice(PROXIES)

def make_request(url, max_retries=3):
    """Make a request with retries and rotating proxies"""
    for attempt in range(max_retries):
        try:
            headers = get_random_headers()
            proxy = get_random_proxy()
            
            # Add random delay to avoid detection
            time.sleep(random.uniform(1.0, 3.0))
            
            response = requests.get(
                url, 
                headers=headers, 
                proxies=proxy,
                timeout=10
            )
            
            if response.status_code == 200:
                return response
            
            logger.warning(f"Request failed with status {response.status_code}, retrying ({attempt+1}/{max_retries})")
        except Exception as e:
            logger.warning(f"Request error: {str(e)}, retrying ({attempt+1}/{max_retries})")
            
        # Increase delay on retry
        time.sleep(random.uniform(2.0, 5.0))
    
    logger.error(f"Failed to fetch {url} after {max_retries} attempts")
    return None

def fetch_bet365_odds():
    """Fetch odds from Bet365 for all sports"""
    logger.info("Fetching odds from Bet365")
    odds_data = []
    
    try:
        for sport in SPORTS:
            # Real implementation would use specific URLs for each sport
            url = f"https://www.bet365.ca/SportsBook.API/web?lid=1&zid=0&pd=0&cid=12&ctid=12&s={sport}"
            
            response = make_request(url)
            if not response:
                continue
                
            # Real parsing logic would go here
            # This is just a placeholder - you need to implement the actual parsing
            try:
                data = response.json()
                events = parse_bet365_json(data, sport)
                odds_data.extend(events)
            except json.JSONDecodeError:
                # Fallback to HTML parsing if JSON fails
                soup = BeautifulSoup(response.text, 'html.parser')
                events = parse_bet365_html(soup, sport)
                odds_data.extend(events)
                
            # Respect rate limits
            time.sleep(random.uniform(1.5, 3.0))
    except Exception as e:
        logger.error(f"Error fetching Bet365 odds: {str(e)}")
    
    return odds_data

def parse_bet365_json(data, sport):
    """Parse JSON response from Bet365"""
    events = []
    
    # Implement actual parsing logic here
    # This is just a placeholder, you need to adapt it to the actual response structure
    try:
        if 'events' in data:
            for event in data['events']:
                if 'markets' in event and len(event['markets']) > 0:
                    for market in event['markets']:
                        if market['type'] == 'moneyline' and 'selections' in market:
                            for selection in market['selections']:
                                events.append({
                                    "bookmaker": "bet365",
                                    "sport": sport,
                                    "event_id": event.get('id', ''),
                                    "event_name": event.get('name', ''),
                                    "market": market.get('type', 'moneyline'),
                                    "selection": selection.get('name', ''),
                                    "odds": float(selection.get('price', 0)),
                                    "timestamp": time.time()
                                })
    except Exception as e:
        logger.error(f"Error parsing Bet365 JSON: {str(e)}")
    
    return events

def parse_bet365_html(soup, sport):
    """Parse HTML response from Bet365"""
    events = []
    
    # Implement actual HTML parsing logic here
    # This is just a placeholder - you need to adapt it to the actual HTML structure
    try:
        event_elements = soup.select('.event-container')
        for event_elem in event_elements:
            event_name_elem = event_elem.select_one('.event-name')
            event_name = event_name_elem.text.strip() if event_name_elem else "Unknown Event"
            
            market_elements = event_elem.select('.market')
            for market_elem in market_elements:
                market_type = 'moneyline'  # You would determine this from the actual element
                
                selection_elements = market_elem.select('.selection')
                for selection_elem in selection_elements:
                    selection_name_elem = selection_elem.select_one('.selection-name')
                    selection_name = selection_name_elem.text.strip() if selection_name_elem else "Unknown"
                    
                    odds_elem = selection_elem.select_one('.odds')
                    odds = float(odds_elem.text.strip()) if odds_elem else 0.0
                    
                    events.append({
                        "bookmaker": "bet365",
                        "sport": sport,
                        "event_id": f"bet365_{hash(event_name)}",
                        "event_name": event_name,
                        "market": market_type,
                        "selection": selection_name,
                        "odds": odds,
                        "timestamp": time.time()
                    })
    except Exception as e:
        logger.error(f"Error parsing Bet365 HTML: {str(e)}")
    
    return events

def fetch_betmgm_odds():
    """Fetch odds from BetMGM for all sports"""
    logger.info("Fetching odds from BetMGM")
    odds_data = []
    
    try:
        for sport in SPORTS:
            # Real implementation would use specific URLs for each sport
            url = f"https://sports.ca.betmgm.com/en/sports/{sport}"
            
            response = make_request(url)
            if not response:
                continue
            
            # Parse the response - this would be customized for BetMGM's format
            soup = BeautifulSoup(response.text, 'html.parser')
            events = parse_betmgm_html(soup, sport)
            odds_data.extend(events)
            
            # Respect rate limits
            time.sleep(random.uniform(1.5, 3.0))
    except Exception as e:
        logger.error(f"Error fetching BetMGM odds: {str(e)}")
    
    return odds_data

def parse_betmgm_html(soup, sport):
    """Parse HTML response from BetMGM"""
    events = []
    
    # Implement actual HTML parsing logic here
    # This is just a placeholder - you need to adapt it to the actual HTML structure
    try:
        event_elements = soup.select('.ms-event')
        for event_elem in event_elements:
            event_name_elem = event_elem.select_one('.event-description')
            event_name = event_name_elem.text.strip() if event_name_elem else "Unknown Event"
            
            market_elements = event_elem.select('.market-cell')
            for market_elem in market_elements:
                market_type = 'moneyline'  # You would determine this from the actual element
                
                selection_elements = market_elem.select('.option')
                for selection_elem in selection_elements:
                    selection_name_elem = selection_elem.select_one('.selection-name')
                    selection_name = selection_name_elem.text.strip() if selection_name_elem else "Unknown"
                    
                    odds_elem = selection_elem.select_one('.odds')
                    odds = float(odds_elem.text.strip()) if odds_elem else 0.0
                    
                    events.append({
                        "bookmaker": "betmgm",
                        "sport": sport,
                        "event_id": f"betmgm_{hash(event_name)}",
                        "event_name": event_name,
                        "market": market_type,
                        "selection": selection_name,
                        "odds": odds,
                        "timestamp": time.time()
                    })
    except Exception as e:
        logger.error(f"Error parsing BetMGM HTML: {str(e)}")
    
    return events

def fetch_stake_odds():
    """Fetch odds from Stake for all sports"""
    logger.info("Fetching odds from Stake")
    odds_data = []
    
    try:
        for sport in SPORTS:
            # Real implementation would use specific URLs for each sport
            url = f"https://stake.com/sports/{sport}"
            
            response = make_request(url)
            if not response:
                continue
            
            # Stake likely uses a React/SPA approach, so we might need to look for JSON data
            # within the page or make API calls directly
            try:
                # Try to find embedded JSON data
                json_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', response.text)
                if json_match:
                    json_data = json.loads(json_match.group(1))
                    events = parse_stake_json(json_data, sport)
                    odds_data.extend(events)
                else:
                    # Fallback to HTML parsing
                    soup = BeautifulSoup(response.text, 'html.parser')
                    events = parse_stake_html(soup, sport)
                    odds_data.extend(events)
            except Exception as e:
                logger.error(f"Error parsing Stake data: {str(e)}")
            
            # Respect rate limits
            time.sleep(random.uniform(1.5, 3.0))
    except Exception as e:
        logger.error(f"Error fetching Stake odds: {str(e)}")
    
    return odds_data

def parse_stake_json(data, sport):
    """Parse JSON data from Stake"""
    events = []
    
    # Implement actual JSON parsing logic here
    # This is just a placeholder, you need to adapt it to the actual data structure
    try:
        if 'sports' in data and sport in data['sports']:
            sport_data = data['sports'][sport]
            if 'events' in sport_data:
                for event_id, event in sport_data['events'].items():
                    event_name = event.get('name', 'Unknown Event')
                    
                    if 'markets' in event:
                        for market_id, market in event['markets'].items():
                            market_type = market.get('type', 'moneyline')
                            
                            if 'outcomes' in market:
                                for outcome_id, outcome in market['outcomes'].items():
                                    selection_name = outcome.get('name', 'Unknown')
                                    odds = float(outcome.get('price', 0))
                                    
                                    events.append({
                                        "bookmaker": "stake",
                                        "sport": sport,
                                        "event_id": event_id,
                                        "event_name": event_name,
                                        "market": market_type,
                                        "selection": selection_name,
                                        "odds": odds,
                                        "timestamp": time.time()
                                    })
    except Exception as e:
        logger.error(f"Error parsing Stake JSON: {str(e)}")
    
    return events

def parse_stake_html(soup, sport):
    """Parse HTML response from Stake"""
    events = []
    
    # Implement actual HTML parsing logic here
    # This is just a placeholder - you need to adapt it to the actual HTML structure
    try:
        event_elements = soup.select('.event-row')
        for event_elem in event_elements:
            event_name_elem = event_elem.select_one('.event-name')
            event_name = event_name_elem.text.strip() if event_name_elem else "Unknown Event"
            
            market_elements = event_elem.select('.market')
            for market_elem in market_elements:
                market_type = 'moneyline'  # You would determine this from the actual element
                
                selection_elements = market_elem.select('.selection')
                for selection_elem in selection_elements:
                    selection_name_elem = selection_elem.select_one('.selection-name')
                    selection_name = selection_name_elem.text.strip() if selection_name_elem else "Unknown"
                    
                    odds_elem = selection_elem.select_one('.odds')
                    odds = float(odds_elem.text.strip()) if odds_elem else 0.0
                    
                    events.append({
                        "bookmaker": "stake",
                        "sport": sport,
                        "event_id": f"stake_{hash(event_name)}",
                        "event_name": event_name,
                        "market": market_type,
                        "selection": selection_name,
                        "odds": odds,
                        "timestamp": time.time()
                    })
    except Exception as e:
        logger.error(f"Error parsing Stake HTML: {str(e)}")
    
    return events

def normalize_event_names(odds_data):
    """Normalize event names to match events across bookmakers"""
    for item in odds_data:
        name = item["event_name"]
        sport = item["sport"]
        
        # Remove common formatting differences
        name = re.sub(r'\s+', ' ', name).strip()  # Normalize whitespace
        name = re.sub(r'\([^)]*\)', '', name).strip()  # Remove parentheses
        name = re.sub(r'@', 'vs', name)  # Standardize team separator
        
        # Extract teams
        if "vs" in name.lower():
            parts = re.split(r'\s+vs\s+', name, flags=re.IGNORECASE)
            teams = [p.strip() for p in parts if p.strip()]
            
            # Sort teams alphabetically for consistency
            if len(teams) >= 2:
                teams = sorted(teams[:2])
                normalized_name = f"{teams[0]} vs {teams[1]}"
            else:
                normalized_name = name
        else:
            normalized_name = name
        
        # Add sport for further disambiguation
        item["normalized_name"] = f"{normalized_name} ({sport})"
    
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
    
    # Combine all odds data
    all_odds = []
    for result in results:
        all_odds.extend(result)
    
    # Normalize event names to match across bookmakers
    normalized_odds = normalize_event_names(all_odds)
    
    # Log summary
    logger.info(f"Fetched {len(normalized_odds)} total odds from all bookmakers")
    
    return normalized_odds
