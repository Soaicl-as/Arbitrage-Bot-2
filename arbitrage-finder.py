import logging
from datetime import datetime
from itertools import combinations
import pandas as pd

logger = logging.getLogger("ArbitrageBot.ArbitrageFinder")

def calculate_arbitrage(odds_list):
    """
    Calculate if there's an arbitrage opportunity in the given odds
    Returns the arbitrage percentage and optimal stake allocation if opportunity exists
    """
    # Convert decimal odds to implied probabilities
    implied_probs = [1/odd for odd in odds_list]
    total_implied_prob = sum(implied_probs)
    
    # If total implied probability is less than 1, there's an arbitrage opportunity
    # The lower the total, the better the opportunity
    if total_implied_prob < 0.98:  # Allow for a small margin for better opportunities
        arbitrage_pct = (1 - total_implied_prob) * 100
        
        # Calculate optimal stake allocation
        total_stake = 100  # Assuming a $100 total stake
        stakes = [(prob / total_implied_prob) * total_stake for prob in implied_probs]
        
        # Calculate profit
        guaranteed_profit = (stakes[0] * (odds_list[0] - 1)) - sum(stakes[1:])
        
        return {
            "arbitrage_exists": True,
            "arbitrage_percentage": arbitrage_pct,
            "total_implied_probability": total_implied_prob,
            "optimal_stakes": stakes,
            "guaranteed_profit_per_100": guaranteed_profit
        }
    
    return {
        "arbitrage_exists": False,
        "total_implied_probability": total_implied_prob
    }

def find_matching_events(odds_data):
    """Group events that match across different bookmakers"""
    matched_events = {}
    
    # Group by normalized event name
    for item in odds_data:
        event_key = f"{item['normalized_name']}_{item['market']}"
        if event_key not in matched_events:
            matched_events[event_key] = []
        matched_events[event_key].append(item)
    
    return matched_events

def find_arbitrage_opportunities(odds_data):
    """Find all arbitrage opportunities in the given odds data"""
    logger.info("Searching for arbitrage opportunities")
    
    opportunities = []
    
    # Match events across bookmakers
    matched_events = find_matching_events(odds_data)
    
    # For each event, look for arbitrage opportunities
    for event_key, event_odds in matched_events.items():
        # Group by selection (e.g., Team A, Team B, Draw)
        selection_map = {}
        for odd in event_odds:
            selection = odd["selection"]
            if selection not in selection_map:
                selection_map[selection] = []
            selection_map[selection].append(odd)
        
        # For each selection, find the best odds across bookmakers
        best_odds = {}
        for selection, odds_list in selection_map.items():
            # Find the best odds for this selection
            best_odd = max(odds_list, key=lambda x: x["odds"])
            best_odds[selection] = best_odd
        
        # We need at least 2 outcomes (usually home/away) to check for arbitrage
        if len(best_odds) >= 2:
            # Extract decimal odds for each outcome
            odds_values = [odd["odds"] for odd in best_odds.values()]
            
            # Calculate if there's an arbitrage opportunity
            arb_result = calculate_arbitrage(odds_values)
            
            if arb_result["arbitrage_exists"]:
                # Format the opportunity details
                opportunity = {
                    "type": "arbitrage",
                    "event_name": event_odds[0]["event_name"],
                    "sport": event_odds[0]["sport"],
                    "market": event_odds[0]["market"],
                    "arbitrage_percentage": arb_result["arbitrage_percentage"],
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "selections": []
                }
                
                # Add details for each selection
                for i, (selection, odd) in enumerate(best_odds.items()):
                    opportunity["selections"].append({
                        "selection": selection,
                        "bookmaker": odd["bookmaker"],
                        "odds": odd["odds"],
                        "recommended_stake": arb_result["optimal_stakes"][i]
                    })
                
                # Calculate guaranteed profit
                opportunity["guaranteed_profit_per_100"] = arb_result["guaranteed_profit_per_100"]
                
                opportunities.append(opportunity)
                logger.info(f"Found arbitrage opportunity: {opportunity['event_name']} - {opportunity['arbitrage_percentage']:.2f}%")
    
    # Sort opportunities by arbitrage percentage (best first)
    opportunities.sort(key=lambda x: x["arbitrage_percentage"], reverse=True)
    
    return opportunities
