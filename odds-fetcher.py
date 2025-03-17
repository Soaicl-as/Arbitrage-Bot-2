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

# Proxy configuration - replace with your actual proxies
PROXIES = [
    {"http": "http://proxy1.example.com:8080", "https": "https://proxy1.example.com:8080"},
    {"http": "http://proxy2.example.com:8080", "https": "https://proxy2.example.com:8080"},
    {"http": "http://proxy3.example.com:8080", "https": "https://proxy3.example.com:8080"}
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

def make_request(url, max_retries=3, json_response=False):
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
                if json_response:
                    return response.json()
                return response
            
            logger.warning(f"Request failed with status {response.status_code}, retrying ({attempt+1}/{max_retries})")
        except Exception as e:
            logger.warning(f"Request error: {str(e)}, retrying ({attempt+1}/{max_retries})")
            
        # Increase delay on retry
        time.sleep(random.uniform(2.0, 5.0))
    
    logger.error(f"Failed to fetch {url} after {max_retries} attempts")
    return None

# BET365 IMPLEMENTATION
def fetch_bet365_odds():
    """Fetch odds from Bet365 for all sports"""
    logger.info("Fetching odds from Bet365")
    odds_data = []
    
    try:
        for sport in SPORTS:
            # Bet365 typically uses an API endpoint for odds
            api_url = f"https://www.bet365.com/SportsBook.API/web?sport={sport}&lid=1&zid=0"
            
            # First try the API endpoint
            json_response = make_request(api_url, json_response=True)
            if json_response:
                events = parse_bet365_json(json_response, sport)
                odds_data.extend(events)
            else:
                # Fall back to HTML scraping if API fails
                html_url = f"https://www.bet365.com/#{sport}/main"
                response = make_request(html_url)
                if response:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    events = parse_bet365_html(soup, sport)
                    odds_data.extend(events)
                    
            # Respect rate limits
            time.sleep(random.uniform(2.5, 4.0))
    except Exception as e:
        logger.error(f"Error fetching Bet365 odds: {str(e)}")
    
    return odds_data

def parse_bet365_json(data, sport):
    """Parse JSON response from Bet365"""
    events = []
    
    try:
        # Actual Bet365 API structure - this will need adaptation to their real API
        if isinstance(data, dict) and 'events' in data:
            for event in data['events']:
                event_name = event.get('name', 'Unknown Event')
                event_id = event.get('id', f'bet365_{hash(event_name)}')
                
                # Process markets - common structure in betting APIs
                if 'markets' in event:
                    for market in event['markets']:
                        market_type = market.get('type', 'moneyline')
                        
                        # Skip markets other than moneyline for simplicity
                        if market_type.lower() != 'moneyline':
                            continue
                        
                        # Process selections within market
                        if 'selections' in market:
                            for selection in market['selections']:
                                selection_name = selection.get('name', 'Unknown')
                                odds_value = selection.get('odds', 0.0)
                                
                                # Convert fractional odds to decimal if needed
                                if isinstance(odds_value, str) and '/' in odds_value:
                                    numerator, denominator = map(int, odds_value.split('/'))
                                    odds_value = round(numerator / denominator + 1, 2)
                                
                                events.append({
                                    "bookmaker": "bet365",
                                    "sport": sport,
                                    "event_id": event_id,
                                    "event_name": event_name,
                                    "market": market_type,
                                    "selection": selection_name,
                                    "odds": float(odds_value),
                                    "timestamp": time.time(),
                                    "normalized_name": ""  # Will be populated later
                                })
    except Exception as e:
        logger.error(f"Error parsing Bet365 JSON: {str(e)}")
    
    return events

def parse_bet365_html(soup, sport):
    """Parse HTML response from Bet365"""
    events = []
    
    try:
        # Bet365 specific selectors - these need to be updated based on their actual HTML structure
        event_containers = soup.select('.gl-Market_Container')
        
        for container in event_containers:
            # Extract event name
            event_header = container.select_one('.rcl-MarketHeaderLabel')
            event_name = event_header.text.strip() if event_header else "Unknown Event"
            event_id = f'bet365_{hash(event_name)}'
            
            # Find moneyline market
            market_groups = container.select('.gl-MarketGroup')
            for market_group in market_groups:
                market_header = market_group.select_one('.gl-MarketGroupButton_Text')
                market_type = 'moneyline'
                
                # Check if this is a moneyline market
                if market_header and ('money line' in market_header.text.lower() or 
                                     'match winner' in market_header.text.lower() or
                                     'winner' in market_header.text.lower()):
                    
                    # Get selections
                    selection_elements = market_group.select('.gl-Participant')
                    for selection_elem in selection_elements:
                        selection_name_elem = selection_elem.select_one('.gl-Participant_Name')
                        selection_name = selection_name_elem.text.strip() if selection_name_elem else "Unknown"
                        
                        odds_elem = selection_elem.select_one('.gl-Participant_Odds')
                        odds_text = odds_elem.text.strip() if odds_elem else "0.0"
                        
                        # Convert odds to decimal format
                        try:
                            if '/' in odds_text:
                                # Convert fractional odds
                                numerator, denominator = map(int, odds_text.split('/'))
                                odds = round(numerator / denominator + 1, 2)
                            else:
                                odds = float(odds_text)
                        except (ValueError, ZeroDivisionError):
                            odds = 0.0
                        
                        events.append({
                            "bookmaker": "bet365",
                            "sport": sport,
                            "event_id": event_id,
                            "event_name": event_name,
                            "market": market_type,
                            "selection": selection_name,
                            "odds": odds,
                            "timestamp": time.time(),
                            "normalized_name": ""  # Will be populated later
                        })
    except Exception as e:
        logger.error(f"Error parsing Bet365 HTML: {str(e)}")
    
    return events

# BETMGM IMPLEMENTATION
def fetch_betmgm_odds():
    """Fetch odds from BetMGM for all sports"""
    logger.info("Fetching odds from BetMGM")
    odds_data = []
    
    try:
        for sport in SPORTS:
            # BetMGM might use different URLs based on region
            url = f"https://sports.betmgm.com/en/sports/{sport}"
            api_url = f"https://sports.betmgm.com/cds-api/bettingoffer/fixtures?x-bwin-accessid=NTIxOTgxNzA&lang=en&country=US&userCountry=US&fixtureTypes=Standard&sportIds={get_betmgm_sport_id(sport)}&offerMapping=Filtered&offerCategories=Gridable"
            
            # Try API first
            json_response = make_request(api_url, json_response=True)
            if json_response:
                events = parse_betmgm_json(json_response, sport)
                odds_data.extend(events)
            else:
                # Fall back to HTML scraping
                response = make_request(url)
                if response:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    events = parse_betmgm_html(soup, sport)
                    odds_data.extend(events)
            
            # Respect rate limits
            time.sleep(random.uniform(2.0, 4.0))
    except Exception as e:
        logger.error(f"Error fetching BetMGM odds: {str(e)}")
    
    return odds_data

def get_betmgm_sport_id(sport):
    """Map sport name to BetMGM sport ID"""
    sport_map = {
        "soccer": "1",
        "basketball": "7",
        "hockey": "19",
        "baseball": "5",
        "tennis": "31",
        "football": "16",
        "mma": "45",
        "boxing": "9",
        "golf": "18",
        "rugby": "29"
    }
    return sport_map.get(sport.lower(), "1")  # Default to soccer if not found

def parse_betmgm_json(data, sport):
    """Parse JSON response from BetMGM API"""
    events = []
    
    try:
        # Process fixtures from BetMGM API
        if isinstance(data, dict) and 'fixtures' in data:
            for fixture in data['fixtures']:
                event_name = fixture.get('name', 'Unknown Event')
                event_id = fixture.get('id', f'betmgm_{hash(event_name)}')
                
                # Find moneyline markets
                for market in fixture.get('markets', []):
                    market_type = market.get('name', '')
                    
                    # Only consider moneyline markets
                    if 'money line' in market_type.lower() or 'match winner' in market_type.lower():
                        for selection in market.get('selections', []):
                            selection_name = selection.get('name', 'Unknown')
                            odds_value = selection.get('price', {}).get('decimal', 0.0)
                            
                            events.append({
                                "bookmaker": "betmgm",
                                "sport": sport,
                                "event_id": event_id,
                                "event_name": event_name,
                                "market": "moneyline",
                                "selection": selection_name,
                                "odds": float(odds_value),
                                "timestamp": time.time(),
                                "normalized_name": ""  # Will be populated later
                            })
    except Exception as e:
        logger.error(f"Error parsing BetMGM JSON: {str(e)}")
    
    return events

def parse_betmgm_html(soup, sport):
    """Parse HTML response from BetMGM"""
    events = []
    
    try:
        # BetMGM specific selectors
        event_containers = soup.select('.option-group')
        
        for container in event_containers:
            # Extract event details
            event_header = container.select_one('.event-header-description')
            event_name = event_header.text.strip() if event_header else "Unknown Event"
            event_id = f'betmgm_{hash(event_name)}'
            
            # Find moneyline options
            market_options = container.select('.market-option')
            
            for i, option in enumerate(market_options):
                # Determine selection name based on position or content
                if i == 0:
                    selection_name = "Home"
                elif i == 1:
                    selection_name = "Away"
                else:
                    selection_name = "Draw"
                
                # Extract custom selection name if available
                selection_elem = option.select_one('.option-name')
                if selection_elem:
                    selection_name = selection_elem.text.strip()
                
                # Extract odds
                odds_elem = option.select_one('.option-price')
                if odds_elem:
                    try:
                        odds = float(odds_elem.text.strip())
                    except ValueError:
                        odds = 0.0
                    
                    events.append({
                        "bookmaker": "betmgm",
                        "sport": sport,
                        "event_id": event_id,
                        "event_name": event_name,
                        "market": "moneyline",
                        "selection": selection_name,
                        "odds": odds,
                        "timestamp": time.time(),
                        "normalized_name": ""  # Will be populated later
                    })
    except Exception as e:
        logger.error(f"Error parsing BetMGM HTML: {str(e)}")
    
    return events

# STAKE IMPLEMENTATION
def fetch_stake_odds():
    """Fetch odds from Stake for all sports"""
    logger.info("Fetching odds from Stake")
    odds_data = []
    
    try:
        for sport in SPORTS:
            # Stake likely uses a GraphQL API
            api_url = f"https://api.stake.com/graphql"
            
            # GraphQL query for sports data
            graphql_query = {
                "operationName": "SportsList",
                "variables": {
                    "sport": sport,
                    "limit": 50,
                    "offset": 0
                },
                "query": """
                query SportsList($sport: String!, $limit: Int!, $offset: Int!) {
                    sport(slug: $sport) {
                        id
                        name
                        matches(limit: $limit, offset: $offset) {
                            id
                            name
                            markets {
                                id
                                name
                                selections {
                                    id
                                    name
                                    odds
                                }
                            }
                        }
                    }
                }
                """
            }
            
            # Make POST request for GraphQL
            try:
                headers = get_random_headers()
                headers["Content-Type"] = "application/json"
                proxy = get_random_proxy()
                
                response = requests.post(
                    api_url,
                    json=graphql_query,
                    headers=headers,
                    proxies=proxy,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    events = parse_stake_graphql(data, sport)
                    odds_data.extend(events)
                else:
                    # Fall back to HTML scraping
                    html_url = f"https://stake.com/sports/{sport}"
                    response = make_request(html_url)
                    if response:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        events = parse_stake_html(soup, sport)
                        odds_data.extend(events)
            except Exception as e:
                logger.error(f"Error with Stake GraphQL request: {str(e)}")
                
                # Fall back to HTML scraping
                html_url = f"https://stake.com/sports/{sport}"
                response = make_request(html_url)
                if response:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    events = parse_stake_html(soup, sport)
                    odds_data.extend(events)
            
            # Respect rate limits
            time.sleep(random.uniform(2.0, 4.0))
    except Exception as e:
        logger.error(f"Error fetching Stake odds: {str(e)}")
    
    return odds_data

def parse_stake_graphql(data, sport):
    """Parse GraphQL response from Stake"""
    events = []
    
    try:
        # Navigate the GraphQL response structure
        if 'data' in data and 'sport' in data['data'] and data['data']['sport']:
            sport_data = data['data']['sport']
            matches = sport_data.get('matches', [])
            
            for match in matches:
                event_name = match.get('name', 'Unknown Event')
                event_id = match.get('id', f'stake_{hash(event_name)}')
                
                for market in match.get('markets', []):
                    market_name = market.get('name', '').lower()
                    
                    # Only process moneyline markets
                    if 'money line' in market_name or 'match winner' in market_name or 'winner' in market_name:
                        market_type = 'moneyline'
                        
                        for selection in market.get('selections', []):
                            selection_name = selection.get('name', 'Unknown')
                            odds_value = selection.get('odds', 0.0)
                            
                            events.append({
                                "bookmaker": "stake",
                                "sport": sport,
                                "event_id": event_id,
                                "event_name": event_name,
                                "market": market_type,
                                "selection": selection_name,
                                "odds": float(odds_value),
                                "timestamp": time.time(),
                                "normalized_name": ""  # Will be populated later
                            })
    except Exception as e:
        logger.error(f"Error parsing Stake GraphQL: {str(e)}")
    
    return events

def parse_stake_html(soup, sport):
    """Parse HTML response from Stake"""
    events = []
    
    try:
        # Look for embedded JSON data that Stake might use
        scripts = soup.select('script[type="application/json"]')
        
        for script in scripts:
            try:
                json_data = json.loads(script.string)
                
                # Look for sports data in the JSON
                if 'props' in json_data and 'pageProps' in json_data['props']:
                    props = json_data['props']['pageProps']
                    
                    if 'matches' in props:
                        matches = props['matches']
                        
                        for match in matches:
                            event_name = match.get('name', 'Unknown Event')
                            event_id = match.get('id', f'stake_{hash(event_name)}')
                            
                            for market in match.get('markets', []):
                                market_name = market.get('name', '').lower()
                                
                                # Only process moneyline markets
                                if 'money line' in market_name or 'match winner' in market_name:
                                    market_type = 'moneyline'
                                    
                                    for selection in market.get('selections', []):
                                        selection_name = selection.get('name', 'Unknown')
                                        odds_value = selection.get('price', 0.0)
                                        
                                        events.append({
                                            "bookmaker": "stake",
                                            "sport": sport,
                                            "event_id": event_id,
                                            "event_name": event_name,
                                            "market": market_type,
                                            "selection": selection_name,
                                            "odds": float(odds_value),
                                            "timestamp": time.time(),
                                            "normalized_name": ""  # Will be populated later
                                        })
            except json.JSONDecodeError:
                continue
        
        # If no embedded JSON found, try HTML parsing
        if not events:
            event_containers = soup.select('.sport-event')
            
            for container in event_containers:
                event_header = container.select_one('.event-header')
                event_name = event_header.text.strip() if event_header else "Unknown Event"
                event_id = f'stake_{hash(event_name)}'
                
                market_containers = container.select('.market-container')
                for market in market_containers:
                    market_header = market.select_one('.market-header')
                    
                    # Check if this is a moneyline market
                    if market_header and ('money line' in market_header.text.lower() or 
                                         'match winner' in market_header.text.lower()):
                        
                        selection_elements = market.select('.selection')
                        for selection in selection_elements:
                            name_elem = selection.select_one('.selection-name')
                            selection_name = name_elem.text.strip() if name_elem else "Unknown"
                            
                            odds_elem = selection.select_one('.odds-value')
                            odds_text = odds_elem.text.strip() if odds_elem else "0.0"
                            
                            try:
                                odds = float(odds_text)
                            except ValueError:
                                odds = 0.0
                            
                            events.append({
                                "bookmaker": "stake",
                                "sport": sport,
                                "event_id": event_id,
                                "event_name": event_name,
                                "market": "moneyline",
                                "selection": selection_name,
                                "odds": odds,
                                "timestamp": time.time(),
                                "normalized_name": ""  # Will be populated later
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
        name = re.sub(r' v ', ' vs ', name)  # Another common separator
        name = re.sub(r' - ', ' vs ', name)  # Another common separator
        
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
    
    # Log detailed summary
    bookmaker_counts = {}
    sport_counts = {}
    for item in normalized_odds:
        bookmaker = item['bookmaker']
        sport = item['sport']
        
        if bookmaker not in bookmaker_counts:
            bookmaker_counts[bookmaker] = 0
        bookmaker_counts[bookmaker] += 1
        
        if sport not in sport_counts:
            sport_counts[sport] = 0
        sport_counts[sport] += 1
    
    # Log summary statistics
    logger.info(f"Fetched {len(normalized_odds)} total odds from all bookmakers")
    for bookmaker, count in bookmaker_counts.items():
        logger.info(f"  {bookmaker}: {count} odds")
    for sport, count in sport_counts.items():
        logger.info(f"  {sport}: {count} odds")
    
    return normalized_odds
