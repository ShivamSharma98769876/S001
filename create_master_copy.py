"""
Script to manually create master copy for Greeks Sentiment Analyzer
Run this script to create the initial master copy
"""
import logging
import sys
from datetime import datetime
from src.greeks_sentiment_analyzer import GreeksSentimentAnalyzer

def setup_logging():
    """Setup logging for the script"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'master_copy_creation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def create_master_copy():
    """Create master copy manually"""
    print("="*60)
    print("GREEKS SENTIMENT ANALYZER - MASTER COPY CREATION")
    print("="*60)
    
    # You'll need to provide your KiteConnect credentials here
    print("\nNote: This script requires KiteConnect credentials.")
    print("Please modify this script to include your API credentials.")
    print("\nFor now, this will create a demo master copy...")
    
    try:
        # Create a mock KiteClient for demonstration
        class MockKiteClient:
            def get_ltp(self, symbol):
                # Return mock prices for demonstration
                mock_prices = {
                    "NSE:NIFTY 50": 19500.0,
                    "NSE:NIFTY BANK": 45000.0,
                    "NSE:NIFTY FINANCIAL SERVICES": 21000.0
                }
                return mock_prices.get(symbol, 1000.0)
        
        # Initialize analyzer with mock client
        mock_client = MockKiteClient()
        analyzer = GreeksSentimentAnalyzer(mock_client)
        
        print("\nCreating master copy...")
        success = analyzer.force_create_master_copy()
        
        if success:
            print("✅ Master copy created successfully!")
            print(f"📁 File saved to: {analyzer.master_copy_file}")
            
            # Display the created data
            import json
            try:
                with open(analyzer.master_copy_file, 'r') as f:
                    data = json.load(f)
                
                print("\n📊 Master Copy Data:")
                print("-" * 40)
                for index_name, index_data in data.get("data", {}).items():
                    print(f"\n{index_name}:")
                    for option_type in ["call", "put"]:
                        option_data = index_data.get(option_type, {})
                        print(f"  {option_type.upper()}:")
                        print(f"    Delta: {option_data.get('delta', 0):.3f}")
                        print(f"    Theta: {option_data.get('theta', 0):.3f}")
                        print(f"    Vega: {option_data.get('vega', 0):.3f}")
                
            except Exception as e:
                print(f"❌ Error reading master copy file: {e}")
        else:
            print("❌ Failed to create master copy")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        logging.error(f"Error creating master copy: {e}")

def main():
    """Main function"""
    setup_logging()
    
    print("Starting master copy creation...")
    create_master_copy()
    
    print("\n" + "="*60)
    print("MASTER COPY CREATION COMPLETED")
    print("="*60)
    
    print("\nNext steps:")
    print("1. Run your trading bot to see sentiment analysis in action")
    print("2. Check the logs for sentiment analysis results")
    print("3. The master copy will be used as baseline for sentiment calculation")

if __name__ == "__main__":
    main()
