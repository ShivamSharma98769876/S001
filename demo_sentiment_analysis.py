"""
Demo Script for Greeks Sentiment Analysis
This script demonstrates the sentiment analysis functionality
"""
import json
import os
from datetime import datetime, date
from src.greeks_sentiment_analyzer import GreeksSentimentAnalyzer, Sentiment

def create_sample_data():
    """Create sample data for demonstration"""
    
    # Sample Master Copy Data
    master_data = {
        "date": "2025-09-12",
        "timestamp": "2025-09-12T09:30:00",
        "data": {
            "NIFTY": {
                "call": {"vega": -0.85, "theta": -11.26, "delta": 0.00},
                "put": {"vega": 2.23, "theta": 31.05, "delta": 0.16}
            },
            "BANKNIFTY": {
                "call": {"vega": 6.11, "theta": -41.28, "delta": 1.08},
                "put": {"vega": -6.41, "theta": 25.06, "delta": -0.64}
            },
            "FINNIFTY": {
                "call": {"vega": 0.32, "theta": 0.23, "delta": 1.08},
                "put": {"vega": -14.26, "theta": 13.18, "delta": -0.94}
            }
        }
    }
    
    # Sample Live Data
    live_data = {
        "timestamp": "2025-09-12T10:51:40",
        "data": {
            "NIFTY": {
                "call": {"vega": -0.85, "theta": -11.26, "delta": 0.02},
                "put": {"vega": 2.03, "theta": 32.05, "delta": 0.26}
            },
            "BANKNIFTY": {
                "call": {"vega": 6.11, "theta": -41.18, "delta": 1.00},
                "put": {"vega": -6.42, "theta": 25.16, "delta": -0.61}
            },
            "FINNIFTY": {
                "call": {"vega": 0.31, "theta": 0.21, "delta": 1.02},
                "put": {"vega": -14.21, "theta": 13.11, "delta": -0.24}
            }
        }
    }
    
    # Save sample data
    os.makedirs("data", exist_ok=True)
    
    with open("data/greeks_master_copy.json", "w") as f:
        json.dump(master_data, f, indent=2)
    
    with open("data/greeks_live_data.json", "w") as f:
        json.dump(live_data, f, indent=2)
    
    print("Sample data created successfully!")

def demonstrate_sentiment_calculation():
    """Demonstrate sentiment calculation logic"""
    
    print("\n" + "="*80)
    print("GREEKS SENTIMENT ANALYSIS DEMONSTRATION")
    print("="*80)
    
    # Load sample data
    with open("data/greeks_master_copy.json", "r") as f:
        master_data = json.load(f)
    
    with open("data/greeks_live_data.json", "r") as f:
        live_data = json.load(f)
    
    print(f"Master Copy Date: {master_data['date']}")
    print(f"Live Data Time: {live_data['timestamp']}")
    print("="*80)
    
    # Create analyzer instance (without KiteClient for demo)
    analyzer = GreeksSentimentAnalyzer(None)
    
    # Calculate sentiment for each index
    sentiment_results = {}
    
    for index_name in ["NIFTY", "BANKNIFTY", "FINNIFTY"]:
        print(f"\n{index_name} Analysis:")
        print("-" * 40)
        
        master_index = master_data["data"][index_name]
        live_index = live_data["data"][index_name]
        
        for option_type in ["call", "put"]:
            print(f"\n{option_type.upper()}:")
            
            master_option = master_index[option_type]
            live_option = live_index[option_type]
            
            # Calculate differences
            vega_diff = live_option["vega"] - master_option["vega"]
            theta_diff = live_option["theta"] - master_option["theta"]
            delta_diff = live_option["delta"] - master_option["delta"]
            
            # Calculate sentiments
            vega_sentiment = analyzer.calculate_sentiment(vega_diff)
            theta_sentiment = analyzer.calculate_sentiment(theta_diff)
            delta_sentiment = analyzer.calculate_sentiment(delta_diff)
            
            # Determine final sentiment
            sentiments = [vega_sentiment, theta_sentiment, delta_sentiment]
            final_sentiment = analyzer._determine_final_sentiment(sentiments)
            
            print(f"  Vega: {live_option['vega']:.2f} (Diff: {vega_diff:.2f}) -> {vega_sentiment.value}")
            print(f"  Theta: {live_option['theta']:.2f} (Diff: {theta_diff:.2f}) -> {theta_sentiment.value}")
            print(f"  Delta: {live_option['delta']:.2f} (Diff: {delta_diff:.2f}) -> {delta_sentiment.value}")
            print(f"  Final Sentiment: {final_sentiment.value}")
            
            # Store results
            if index_name not in sentiment_results:
                sentiment_results[index_name] = {}
            
            sentiment_results[index_name][option_type] = {
                "vega": {"value": live_option["vega"], "diff": vega_diff, "sentiment": vega_sentiment.value},
                "theta": {"value": live_option["theta"], "diff": theta_diff, "sentiment": theta_sentiment.value},
                "delta": {"value": live_option["delta"], "diff": delta_diff, "sentiment": delta_sentiment.value},
                "final_sentiment": final_sentiment.value
            }
    
    # Display final sentiment table
    print("\n" + "="*80)
    print("FINAL SENTIMENT TABLE")
    print("="*80)
    print(f"{'Index':<15} {'Vega':<8} {'Theta':<8} {'Delta':<8} {'Sentiment':<10}")
    print("-" * 60)
    
    for index_name, data in sentiment_results.items():
        for option_type in ["call", "put"]:
            option_data = data[option_type]
            print(f"{index_name} {option_type.upper():<8} "
                  f"{option_data['vega']['value']:<8.2f} "
                  f"{option_data['theta']['value']:<8.2f} "
                  f"{option_data['delta']['value']:<8.2f} "
                  f"{option_data['final_sentiment']:<10}")
    
    print("="*80)
    
    # Explain sentiment rules
    print("\nSENTIMENT RULES:")
    print("- If difference > +5: Bullish (Green)")
    print("- If difference between -5 and +5: Neutral (White)")
    print("- If difference < -5: Bearish (Red)")
    print("- If multiple sentiments in a row: Final sentiment = Neutral")
    
    return sentiment_results

def main():
    """Main demonstration function"""
    print("Creating sample data...")
    create_sample_data()
    
    print("Demonstrating sentiment calculation...")
    results = demonstrate_sentiment_calculation()
    
    print("\nDemo completed successfully!")
    print("To integrate with your trading system:")
    print("1. Initialize KiteClient with your credentials")
    print("2. Create GreeksSentimentAnalyzer instance")
    print("3. Call analyzer.run_analysis() every 3 minutes during market hours")

if __name__ == "__main__":
    main()
