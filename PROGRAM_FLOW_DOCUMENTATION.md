# 📊 OPTIONS TRADING BOT - COMPLETE PROGRAM FLOW

## 🏗️ **ARCHITECTURE OVERVIEW**

The program has **TWO MAIN VERSIONS**:
1. **Modular Bot** (`src/trading_bot.py` + `main.py`)
2. **Standalone Program** (`Straddle10PointswithSL-Limit.py`)

Both implement the **SAME CORE LOGIC** with identical functionality.

---

## 🚀 **ENTRY POINTS**

### **1. Modular Bot Entry Points**
```
main.py (CLI) → TradingBot.run()
app.py (Web UI) → start_bot() → TradingBot.run()
run_trading_bot.py → main.py → TradingBot.run()
```

### **2. Standalone Program Entry Point**
```
Straddle10PointswithSL-Limit.py → main() function
```

---

## 🔄 **COMPLETE PROGRAM FLOW**

### **PHASE 1: INITIALIZATION** 🏁

```
1. USER INPUT
   ├── Account Name
   ├── API Key
   ├── API Secret
   └── Request Token

2. KITE CONNECT SETUP
   ├── Initialize KiteConnect API
   ├── Set Access Token
   └── Validate Connection

3. LOGGING SETUP
   ├── Create Log File (Account_YYYY-MM-DD_trading_log.log)
   ├── Configure Console + File Logging
   └── Unicode-Safe Formatter

4. COMPONENT INITIALIZATION
   ├── KiteClient (API wrapper)
   ├── OptionsCalculator (strike finding, hedge logic)
   ├── VIXCalculator (India VIX fetching)
   ├── VIXDeltaManager (dynamic delta ranges)
   └── GreeksSentimentAnalyzer (sentiment analysis)
```

### **PHASE 2: MARKET ANALYSIS** 📈

```
5. VIX ANALYSIS
   ├── Fetch India VIX
   ├── Determine Strategy (Calendar vs Strangle)
   ├── Set Delta Range (0.29-0.35 or 0.15-0.25)
   ├── Set Hedge Points (4 or 6 points)
   └── Log VIX Configuration

6. GREEKS SENTIMENT ANALYSIS (Every 3 Minutes)
   ├── Create Master Copy (Once Daily at Market Open)
   ├── Fetch Live Greeks Data (Every 3 Minutes)
   ├── Calculate Sentiment Differences
   ├── Determine Bullish/Bearish/Neutral
   └── Display Color-Coded Sentiment Table
```

### **PHASE 3: TRADING EXECUTION** 💰

```
7. MARKET TIME VALIDATION
   ├── Check if Market is Open (9:15 AM - 3:30 PM)
   ├── Check Trading Start Time (9:30 AM)
   └── Exit if Market Closed

8. STRIKE SELECTION
   ├── Fetch Option Chain
   ├── Find Call Strike (Delta 0.29-0.35)
   ├── Find Put Strike (Delta 0.29-0.35)
   ├── Calculate Total Premium
   └── Log Strike Details

9. INITIAL ORDER PLACEMENT
   ├── Place Call Sell Order
   ├── Place Put Sell Order
   ├── Set Stop-Loss Orders
   └── Log Order Details

10. TRADE MONITORING LOOP
    ├── Check Market Close (14:45 PM) → EXIT
    ├── Check Profit Booking Conditions
    │   ├── Initial Profit (14 points) → EXIT
    │   └── Second Profit (28 points) → EXIT
    ├── Check Stop-Loss Triggers
    │   ├── Max Stop-Loss (3 triggers) → EXIT
    │   └── Individual Stop-Loss → Modify Orders
    ├── Check Hedge Conditions
    │   ├── Calendar Strategy → Next Week Expiry
    │   └── Strangle Strategy → Same Week Expiry
    └── Update Greeks Sentiment (Every 3 Minutes)
```

### **PHASE 4: HEDGE MANAGEMENT** 🛡️

```
11. HEDGE TRIGGER CONDITIONS
    ├── Calendar Strategy: 4 Points Loss
    └── Strangle Strategy: 6 Points Loss

12. HEDGE EXPIRY LOGIC
    ├── Calendar Strategy
    │   ├── Base Trade: Current Week Expiry
    │   └── Hedge Trade: Next Week Expiry
    └── Strangle Strategy
        ├── Base Trade: Current Week Expiry
        └── Hedge Trade: Same Week Expiry

13. HEDGE ORDER PLACEMENT
    ├── Find Hedge Strikes
    ├── Place Call Hedge Buy Order
    ├── Place Put Hedge Buy Order
    └── Set hedge_taken = True (Prevent Duplicates)
```

### **PHASE 5: EXIT CONDITIONS** 🚪

```
14. PROFIT BOOKING EXITS
    ├── Initial Profit (14 points)
    │   ├── Modify Stop-Loss Orders
    │   ├── Log Profit Booking
    │   └── GRACEFUL EXIT (No More Trades)
    └── Second Profit (28 points)
        ├── Modify Stop-Loss Orders
        ├── Log Profit Booking
        └── GRACEFUL EXIT (No More Trades)

15. STOP-LOSS EXITS
    ├── Individual Stop-Loss
    │   ├── Modify Stop-Loss Orders
    │   └── Continue Monitoring
    └── Max Stop-Loss (3 Triggers)
        ├── Log Max Stop-Loss Reached
        └── GRACEFUL EXIT (No More Trades)

16. MARKET CLOSE EXIT
    ├── Check Time >= 14:45 PM
    ├── Modify Stop-Loss Orders
    ├── Set market_closed = True
    └── GRACEFUL EXIT (No More Trades)
```

---

## 🎯 **KEY STRATEGY LOGIC**

### **VIX-Based Strategy Selection**
```
India VIX < 20: Calendar Strategy
├── Delta Range: 0.15-0.25
├── Hedge Points: 4
└── Hedge Expiry: Next Week

India VIX >= 20: Strangle Strategy
├── Delta Range: 0.29-0.35
├── Hedge Points: 6
└── Hedge Expiry: Same Week
```

### **Greeks Sentiment Analysis**
```
Master Copy Creation (Once Daily)
├── Market Open: 9:15 AM
├── Fetch NIFTY, BANKNIFTY, FINNIFTY Options
├── Calculate Greeks (Delta, Vega, Theta)
├── Store in data/greeks_master_copy.json
└── Use as Baseline

Live Copy Creation (Every 3 Minutes)
├── Fetch Current Greeks Data
├── Calculate Differences vs Master Copy
├── Determine Sentiment:
│   ├── > +5: Bullish (Green)
│   ├── -5 to +5: Neutral (White)
│   └── < -5: Bearish (Red)
└── Display Sentiment Table
```

---

## 🔧 **CONFIGURATION PARAMETERS**

### **Market Timing**
- **Market Start**: 9:15 AM
- **Trading Start**: 9:30 AM
- **Market End**: 3:30 PM
- **Trading End**: 14:45 PM

### **Trading Parameters**
- **Default Delta Range**: 0.29-0.35
- **VIX Low Delta Range**: 0.15-0.25
- **Call/Put Quantity**: 50 (configurable)
- **Max Stop-Loss Triggers**: 3

### **Profit Booking**
- **Initial Profit**: 14 points
- **Second Profit**: 28 points

### **Hedge Points**
- **Calendar Strategy**: 4 points
- **Strangle Strategy**: 6 points

---

## 📁 **FILE STRUCTURE**

```
├── main.py (CLI Entry Point)
├── app.py (Web UI Entry Point)
├── run_trading_bot.py (Bot Runner)
├── Straddle10PointswithSL-Limit.py (Standalone Program)
├── config.py (Configuration)
├── src/
│   ├── trading_bot.py (Main Bot Class)
│   ├── kite_client.py (API Wrapper)
│   ├── options_calculator.py (Strike & Hedge Logic)
│   ├── vix_calculator.py (VIX Analysis)
│   ├── vix_delta_manager.py (Dynamic Delta Management)
│   └── greeks_sentiment_analyzer.py (Sentiment Analysis)
├── data/
│   ├── greeks_master_copy.json (Daily Baseline)
│   └── greeks_live_data.json (Live Data)
└── Log/ (Trading Logs)
```

---

## 🚨 **ERROR HANDLING & SAFETY**

### **Market Close Protection**
- **Race Condition Fix**: Check market close before placing orders
- **Early Exit**: Exit at 14:45 PM regardless of other conditions
- **Order Validation**: Validate market hours before API calls

### **Hedge Duplication Prevention**
- **Single Hedge**: Set `hedge_taken = True` after first attempt
- **Error Handling**: Continue even if hedge placement fails
- **Logging**: Clear indication of hedge status

### **API Error Handling**
- **Connection Retry**: Automatic retry on API failures
- **Graceful Degradation**: Continue operation with limited functionality
- **Error Logging**: Comprehensive error tracking

---

## 📊 **LOGGING & MONITORING**

### **Log Files**
- **Format**: `Account_YYYY-MM-DD_trading_log.log`
- **Location**: `Log/` directory
- **Content**: All trading activities, errors, and sentiment analysis

### **Console Output**
- **Real-time Updates**: Live trading status
- **Sentiment Tables**: Color-coded Greeks analysis
- **Error Messages**: Immediate feedback
- **Progress Indicators**: Clear status updates

---

## 🎯 **EXECUTION SUMMARY**

The program follows a **systematic approach**:

1. **Initialize** → Setup API, logging, components
2. **Analyze** → VIX analysis, Greeks sentiment
3. **Execute** → Place initial trades, set stop-losses
4. **Monitor** → Continuous monitoring loop
5. **Hedge** → Place hedges when conditions met
6. **Exit** → Graceful exit on profit/loss/market close

**Key Features**:
- ✅ **VIX-Based Strategy Selection**
- ✅ **Dynamic Delta Ranges**
- ✅ **Calendar vs Strangle Logic**
- ✅ **Greeks Sentiment Analysis**
- ✅ **Comprehensive Error Handling**
- ✅ **Market Close Protection**
- ✅ **Profit Booking Automation**
- ✅ **Stop-Loss Management**
- ✅ **Hedge Duplication Prevention**

This creates a **robust, automated options trading system** that adapts to market conditions and provides comprehensive risk management.
