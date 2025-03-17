import os
import json
import pandas as pd
import sqlite3
from datetime import datetime
import logging

logger = logging.getLogger("ArbitrageBot.DataStorage")

class DataStorage:
    def __init__(self, db_path="arbitrage_data.db"):
        """Initialize the data storage with a SQLite database path"""
        self.db_path = db_path
        self._create_tables_if_needed()
        logger.info(f"Data storage initialized with database: {db_path}")
    
    def _create_tables_if_needed(self):
        """Create database tables if they don't exist"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create table for arbitrage opportunities
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS arbitrage_opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_name TEXT,
                sport TEXT,
                market TEXT,
                arbitrage_percentage REAL,
                guaranteed_profit REAL,
                timestamp TEXT,
                details TEXT,
                notified INTEGER DEFAULT 0
            )
            ''')
            
            # Create table for odds history
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS odds_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bookmaker TEXT,
                sport TEXT,
                event_name TEXT,
                market TEXT,
                selection TEXT,
                odds REAL,
                timestamp TEXT
            )
            ''')
            
            conn.commit()
            logger.info("Database tables created or already exist")
        except Exception as e:
            logger.error(f"Error creating database tables: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def save_arbitrage_opportunity(self, opportunity, notified=False):
        """Save an arbitrage opportunity to the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Convert selections list to JSON string
            details = json.dumps(opportunity["selections"])
            
            cursor.execute('''
            INSERT INTO arbitrage_opportunities 
            (event_name, sport, market, arbitrage_percentage, guaranteed_profit, timestamp, details, notified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                opportunity["event_name"],
                opportunity["sport"],
                opportunity["market"],
                opportunity["arbitrage_percentage"],
                opportunity["guaranteed_profit_per_100"],
                opportunity["timestamp"],
                details,
                1 if notified else 0
            ))
            
            conn.commit()
            logger.info(f"Saved arbitrage opportunity for {opportunity['event_name']}")
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error saving arbitrage opportunity: {str(e)}")
            return None
        finally:
            if conn:
                conn.close()
    
    def save_batch_odds(self, odds_data):
        """Save a batch of odds data to the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Prepare data for batch insertion
            odds_records = []
            for odd in odds_data:
                odds_records.append((
                    odd["bookmaker"],
                    odd["sport"],
                    odd["event_name"],
                    odd["market"],
                    odd["selection"],
                    odd["odds"],
                    datetime.fromtimestamp(odd["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
                ))
            
            # Batch insert
            cursor.executemany('''
            INSERT INTO odds_history 
            (bookmaker, sport, event_name, market, selection, odds, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', odds_records)
            
            conn.commit()
            logger.info(f"Saved {len(odds_records)} odds records to database")
        except Exception as e:
            logger.error(f"Error saving odds data: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def get_recent_opportunities(self, limit=10):
        """Get recent arbitrage opportunities"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT * FROM arbitrage_opportunities
            ORDER BY timestamp DESC
            LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            opportunities = []
            
            for row in rows:
                opp = dict(row)
                # Parse JSON details back to list
                opp["selections"] = json.loads(opp["details"])
                del opp["details"]
                opportunities.append(opp)
            
            return opportunities
        except Exception as e:
            logger.error(f"Error retrieving recent opportunities: {str(e)}")
            return []
        finally:
            if conn:
                conn.close()
    
    def export_opportunities_to_csv(self, filename="arbitrage_opportunities.csv"):
        """Export all arbitrage opportunities to a CSV file"""
        try:
            conn = sqlite3.connect(self.db_path)
            query = "SELECT * FROM arbitrage_opportunities ORDER BY timestamp DESC"
            df = pd.read_sql_query(query, conn)
            
            # Process the details column to make it readable
            df["details"] = df["details"].apply(lambda x: json.loads(x) if x else [])
            
            df.to_csv(filename, index=False)
            logger.info(f"Exported opportunities to {filename}")
            return True
        except Exception as e:
            logger.error(f"Error exporting opportunities to CSV: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()
    
    def get_opportunity_stats(self):
        """Get statistics about arbitrage opportunities"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total opportunities
            cursor.execute("SELECT COUNT(*) FROM arbitrage_opportunities")
            total = cursor.fetchone()[0]
            
            # Average arbitrage percentage
            cursor.execute("SELECT AVG(arbitrage_percentage) FROM arbitrage_opportunities")
            avg_percentage = cursor.fetchone()[0] or 0
            
            # Best opportunity
            cursor.execute("""
            SELECT event_name, arbitrage_percentage, guaranteed_profit, timestamp 
            FROM arbitrage_opportunities 
            ORDER BY arbitrage_percentage DESC LIMIT 1
            """)
            best = cursor.fetchone()
            
            # Opportunities by sport
            cursor.execute("""
            SELECT sport, COUNT(*) as count 
            FROM arbitrage_opportunities 
            GROUP BY sport 
            ORDER BY count DESC
            """)
            sports = {row[0]: row[1] for row in cursor.fetchall()}
            
            return {
                "total_opportunities": total,
                "average_arbitrage_percentage": avg_percentage,
                "best_opportunity": best,
                "opportunities_by_sport": sports
            }
        except Exception as e:
            logger.error(f"Error getting opportunity stats: {str(e)}")
            return {}
        finally:
            if conn:
                conn.close()
