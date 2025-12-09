"""
Test script to verify Greeks Sentiment Analyzer integration
"""
import logging
import os
from datetime import datetime
from src.greeks_sentiment_analyzer import GreeksSentimentAnalyzer

def setup_logging():
    """Setup logging for testing"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def test_sentiment_analyzer():
    """Test the sentiment analyzer functionality"""
    
    print("="*60)
    print("TESTING GREEKS SENTIMENT ANALYZER INTEGRATION")
    print("="*60)
    
    # Test 1: Check if analyzer can be imported
    print("\n1. Testing Import...")
    try:
        from src.greeks_sentiment_analyzer import GreeksSentimentAnalyzer
        print("✅ GreeksSentimentAnalyzer imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import GreeksSentimentAnalyzer: {e}")
        return False
    
    # Test 2: Check configuration
    print("\n2. Testing Configuration...")
    try:
        from config import GREEKS_ANALYSIS_ENABLED, GREEKS_ANALYSIS_INTERVAL
        print(f"✅ Configuration loaded:")
        print(f"   - GREEKS_ANALYSIS_ENABLED: {GREEKS_ANALYSIS_ENABLED}")
        print(f"   - GREEKS_ANALYSIS_INTERVAL: {GREEKS_ANALYSIS_INTERVAL} seconds")
    except ImportError as e:
        print(f"❌ Failed to load configuration: {e}")
        return False
    
    # Test 3: Check data directory
    print("\n3. Testing Data Directory...")
    data_dir = "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"✅ Created data directory: {data_dir}")
    else:
        print(f"✅ Data directory exists: {data_dir}")
    
    # Test 4: Test sentiment calculation logic
    print("\n4. Testing Sentiment Calculation Logic...")
    try:
        # Create a mock analyzer instance
        analyzer = GreeksSentimentAnalyzer(None)
        
        # Test sentiment calculation
        test_values = [10.5, 3.2, -2.1, -8.7, 0.0]
        expected_sentiments = ["Bullish", "Neutral", "Neutral", "Bearish", "Neutral"]
        
        for value, expected in zip(test_values, expected_sentiments):
            sentiment = analyzer.calculate_sentiment(value)
            if sentiment.value == expected:
                print(f"✅ Value {value} -> {sentiment.value} (Expected: {expected})")
            else:
                print(f"❌ Value {value} -> {sentiment.value} (Expected: {expected})")
                return False
                
    except Exception as e:
        print(f"❌ Failed to test sentiment calculation: {e}")
        return False
    
    # Test 5: Test final sentiment determination
    print("\n5. Testing Final Sentiment Determination...")
    try:
        from src.greeks_sentiment_analyzer import Sentiment
        
        # Test cases
        test_cases = [
            ([Sentiment.BULLISH, Sentiment.BULLISH, Sentiment.BULLISH], Sentiment.BULLISH),
            ([Sentiment.BEARISH, Sentiment.BEARISH, Sentiment.BEARISH], Sentiment.BEARISH),
            ([Sentiment.NEUTRAL, Sentiment.NEUTRAL, Sentiment.NEUTRAL], Sentiment.NEUTRAL),
            ([Sentiment.BULLISH, Sentiment.BEARISH, Sentiment.NEUTRAL], Sentiment.NEUTRAL),
            ([Sentiment.BULLISH, Sentiment.BULLISH, Sentiment.BEARISH], Sentiment.NEUTRAL),
        ]
        
        for sentiments, expected in test_cases:
            result = analyzer._determine_final_sentiment(sentiments)
            if result == expected:
                sentiment_names = [s.value for s in sentiments]
                print(f"✅ {sentiment_names} -> {result.value} (Expected: {expected.value})")
            else:
                sentiment_names = [s.value for s in sentiments]
                print(f"❌ {sentiment_names} -> {result.value} (Expected: {expected.value})")
                return False
                
    except Exception as e:
        print(f"❌ Failed to test final sentiment determination: {e}")
        return False
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED - INTEGRATION READY")
    print("="*60)
    
    return True

def test_standalone_integration():
    """Test standalone program integration"""
    print("\n" + "="*60)
    print("TESTING STANDALONE PROGRAM INTEGRATION")
    print("="*60)
    
    # Test if standalone program can import sentiment analyzer
    try:
        # Simulate the import that happens in standalone program
        try:
            from src.greeks_sentiment_analyzer import GreeksSentimentAnalyzer
            SENTIMENT_ANALYZER_AVAILABLE = True
            print("✅ Standalone program can import GreeksSentimentAnalyzer")
        except ImportError:
            SENTIMENT_ANALYZER_AVAILABLE = False
            print("❌ Standalone program cannot import GreeksSentimentAnalyzer")
            return False
        
        # Test configuration import
        try:
            from config import GREEKS_ANALYSIS_ENABLED
            print(f"✅ Standalone program can import GREEKS_ANALYSIS_ENABLED: {GREEKS_ANALYSIS_ENABLED}")
        except ImportError:
            print("❌ Standalone program cannot import GREEKS_ANALYSIS_ENABLED")
            return False
        
        print("✅ Standalone program integration test passed")
        return True
        
    except Exception as e:
        print(f"❌ Standalone program integration test failed: {e}")
        return False

def test_modular_integration():
    """Test modular bot integration"""
    print("\n" + "="*60)
    print("TESTING MODULAR BOT INTEGRATION")
    print("="*60)
    
    try:
        # Test if modular bot can import sentiment analyzer
        try:
            from src.greeks_sentiment_analyzer import GreeksSentimentAnalyzer
            SENTIMENT_ANALYZER_AVAILABLE = True
            print("✅ Modular bot can import GreeksSentimentAnalyzer")
        except ImportError:
            SENTIMENT_ANALYZER_AVAILABLE = False
            print("❌ Modular bot cannot import GreeksSentimentAnalyzer")
            return False
        
        # Test TradingBot import
        try:
            from src.trading_bot import TradingBot
            print("✅ Modular bot can import TradingBot")
        except ImportError:
            print("❌ Modular bot cannot import TradingBot")
            return False
        
        print("✅ Modular bot integration test passed")
        return True
        
    except Exception as e:
        print(f"❌ Modular bot integration test failed: {e}")
        return False

def main():
    """Main test function"""
    setup_logging()
    
    print("Starting Greeks Sentiment Analyzer Integration Tests...")
    
    # Run all tests
    tests_passed = 0
    total_tests = 3
    
    if test_sentiment_analyzer():
        tests_passed += 1
    
    if test_standalone_integration():
        tests_passed += 1
    
    if test_modular_integration():
        tests_passed += 1
    
    print("\n" + "="*60)
    print(f"INTEGRATION TEST RESULTS: {tests_passed}/{total_tests} TESTS PASSED")
    print("="*60)
    
    if tests_passed == total_tests:
        print("🎉 ALL INTEGRATION TESTS PASSED!")
        print("\nThe Greeks Sentiment Analyzer is ready to use with:")
        print("1. Standalone program (Straddle10PointswithSL-Limit.py)")
        print("2. Modular bot program (src/trading_bot.py)")
        print("\nTo enable sentiment analysis, set GREEKS_ANALYSIS_ENABLED = True in config.py")
    else:
        print("❌ Some integration tests failed. Please check the errors above.")
    
    return tests_passed == total_tests

if __name__ == "__main__":
    main()
