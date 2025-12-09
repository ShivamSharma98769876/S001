from datetime import date, datetime, time, timedelta
import logging
from kiteconnect import KiteConnect
from scipy.stats import norm
import math
import time as time_module



global Input_account, Input_api_key, Input_api_secret, Input_request_token
# client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# client = openai.OpenAI(api_key="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")
# Input user account and API details
Input_account = input("Account: ").strip()
Input_api_key = input("Api_key: ").strip()
Input_api_secret = input("Api_Secret: ").strip()
Input_request_token = input("Request_Token: ").strip()

api_key = Input_api_key
api_secret = Input_api_secret
request_token = Input_request_token
account = Input_account

# Initialize Kite Connect API
kite = KiteConnect(api_key=api_key)
kite.set_access_token(request_token)

# Setup logging to file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'{Input_account} {date.today()}_trading_log.log'),
        logging.StreamHandler()
    ]
)

TARGET_DELTA_LOW = 0.29  # Lower bound for target delta
TARGET_DELTA_HIGH = 0.35  # Upper bound for target delta
stop_loss_trigger_count = 0  # Tracks stop-loss triggers
MAX_STOP_LOSS_TRIGGER = 3  # Max number of stop-loss triggers allowed

# VWAP Configuration
VWAP_MINUTES = 5  # Number of minutes to calculate VWAP
VWAP_ENABLED = True  # Enable/disable VWAP analysis
VWAP_PRIORITY = True  # Prioritize strikes below VWAP

last_vix_fetch_time = None  # Track last time VIX was fetched
last_hedge_fetch_time = None  # Track last time VIX was fetched
india_vix = None  # Store fetched VIX value for reuse


def fetch_option_chain():
    logging.info("Fetching option chain data")
    try:
        instrument = 'NIFTY'
        instruments = kite.instruments('NFO')  # Fetch instruments specifically for the options segment
        options = [i for i in instruments if i['segment'] == 'NFO-OPT' and i.get('name') == instrument]
        logging.info(f"Fetched {len(options)} options")
        return options
    except Exception as e:
        logging.error(f"Error fetching option chain: {e}")
        return []


def get_india_vix():
    global last_vix_fetch_time, india_vix
    current_time = datetime.now()

    # Fetch VIX only if 2 minutes have passed since the last fetch
    if last_vix_fetch_time is None or (current_time - last_vix_fetch_time).total_seconds() > 120:
        instrument_token = '264969'  # NIFTY VIX instrument token
        try:
            vix_data = kite.ltp(instrument_token)
            india_vix = vix_data[instrument_token]['last_price']
            last_vix_fetch_time = current_time
            logging.info(f"Fetched India VIX: {india_vix} at {last_vix_fetch_time}")
        except Exception as e:
            logging.error(f"Error fetching India VIX: {e}")
            time_module.sleep(45)
            return get_india_vix()

    return india_vix / 100  # Return the latest VIX divided by 100 for annual volatility


def get_instrument_token(symbol):
    """Get instrument token for a given symbol"""
    try:
        # Extract the instrument name from symbol
        if ':' in symbol:
            exchange, tradingsymbol = symbol.split(':', 1)
        else:
            tradingsymbol = symbol
            exchange = 'NFO'
        
        logging.debug(f"Looking for instrument token: {tradingsymbol} in exchange: {exchange}")
        
        # Get instruments for the exchange
        instruments = kite.instruments(exchange)
        
        # Find the matching instrument
        for instrument in instruments:
            if instrument['tradingsymbol'] == tradingsymbol:
                logging.debug(f"Found instrument token: {instrument['instrument_token']} for {tradingsymbol}")
                return instrument['instrument_token']
        
        logging.error(f"Instrument token not found for {symbol} (tradingsymbol: {tradingsymbol})")
        return None
        
    except Exception as e:
        logging.error(f"Error getting instrument token for {symbol}: {e}")
        return None


def calculate_vwap(symbol, minutes=None):
    """
    Calculate VWAP (Volume Weighted Average Price) for a given symbol
    
    Args:
        symbol (str): Trading symbol (e.g., 'NFO:NIFTY24JAN19000CE')
        minutes (int): Number of minutes to look back for VWAP calculation
        
    Returns:
        float: VWAP value or None if calculation fails
    """
    if minutes is None:
        minutes = VWAP_MINUTES
        
    try:
        # Get instrument token first
        instrument_token = get_instrument_token(symbol)
        if instrument_token is None:
            logging.warning(f"Could not get instrument token for {symbol}")
            return None
        
        # Calculate the time range for VWAP calculation
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=minutes)
        
        # Format times for API call
        from_date = start_time.strftime('%Y-%m-%d')
        to_date = end_time.strftime('%Y-%m-%d')
        
        logging.debug(f"Fetching historical data for {symbol} from {from_date} to {to_date}")
        
        # Get historical data
        historical_data = kite.historical_data(
            instrument_token=instrument_token,
            from_date=from_date,
            to_date=to_date,
            interval='minute'
        )
        
        if not historical_data:
            logging.warning(f"No historical data available for {symbol} (token: {instrument_token})")
            return None
        
        # Calculate VWAP
        total_volume_price = 0
        total_volume = 0
        
        for candle in historical_data:
            # Use typical price (high + low + close) / 3
            typical_price = (candle['high'] + candle['low'] + candle['close']) / 3
            volume = candle.get('volume', 0)
            
            total_volume_price += typical_price * volume
            total_volume += volume
        
        if total_volume == 0:
            logging.warning(f"No volume data available for {symbol}")
            return None
        
        vwap = total_volume_price / total_volume
        logging.info(f"VWAP for {symbol}: {vwap:.2f} (based on {len(historical_data)} candles)")
        return vwap
        
    except Exception as e:
        logging.error(f"Error calculating VWAP for {symbol}: {e}")
        return None


def get_strike_vwap_data(strike):
    """
    Get VWAP data for a strike option
    
    Args:
        strike (dict): Strike option data
        
    Returns:
        dict: Dictionary containing LTP and VWAP data
    """
    symbol = f"NFO:{strike['tradingsymbol']}"
    
    try:
        ltp = kite.ltp(symbol)[symbol]['last_price']
        vwap = calculate_vwap(symbol, minutes=VWAP_MINUTES)
        
        return {
            'symbol': symbol,
            'ltp': ltp,
            'vwap': vwap,
            'strike_price': strike['strike'],
            'instrument_type': strike['instrument_type']
        }
    except Exception as e:
        logging.error(f"Error getting VWAP data for {symbol}: {e}")
        return {
            'symbol': symbol,
            'ltp': None,
            'vwap': None,
            'strike_price': strike['strike'],
            'instrument_type': strike['instrument_type']
        }


def calculate_delta(option, underlying_price, risk_free_rate=0.05):
    try:
        strike_price = option['strike']
        expiry = option['expiry']
        today = datetime.now().date()
        if isinstance(expiry, str):
            expiry = datetime.strptime(expiry, '%Y-%m-%d').date()
        days_to_expiry = (expiry - today).days / 365.0
        if days_to_expiry <= 0:
            logging.error(f"Invalid days to expiry: {days_to_expiry} for option {option['tradingsymbol']}")
            return None

        # Get the volatility (VIX)
        volatility = get_india_vix()

        # Black-Scholes d1 calculation for delta
        d1 = (math.log(underlying_price / strike_price) + (risk_free_rate + (volatility ** 2) / 2) * days_to_expiry) / (
                volatility * math.sqrt(days_to_expiry))
        if option['instrument_type'] == 'CE':  # Call Option
            delta = norm.cdf(d1)
        else:  # Put Option
            delta = -norm.cdf(-d1)

        return abs(delta)  # Absolute value of delta for comparison
    except Exception as e:
        if "Too many requests" in str(e):
            logging.error("Too many requests - waiting before retrying...")
            time_module.sleep(45)
            return calculate_delta(option, underlying_price, risk_free_rate)
        else:
            logging.error(f"Error calculating delta: {e}")
            return None


# def find_strikes(options, underlying_price, target_delta_low, target_delta_high):
#     atm_strike = round(underlying_price / 50) * 50
#     logging.info(f"ATM strike: {atm_strike}")
#     global call_sl_to_be_placed
#     global put_sl_to_be_placed
#
#     logging.info(f"Finding strikes with delta between {target_delta_low} and {target_delta_high} within {atm_strike - 500} to {atm_strike + 500}")
#     try:
#         call_strikes = []
#         put_strikes = []
#         for o in options:
#             if atm_strike - 500 <= o['strike'] <= atm_strike + 500:
#                 delta = calculate_delta(o, underlying_price)
#                 if delta is None:
#                     continue
#                 if target_delta_low <= delta <= target_delta_high:
#                     if o['instrument_type'] == 'CE':
#                         call_strikes.append(o)
#                     elif o['instrument_type'] == 'PE':
#                         put_strikes.append(o)
#         if not call_strikes or not put_strikes:
#             logging.warning("No strikes found with the desired delta range.")
#             return None
#         call_strikes.sort(key=lambda x: x['strike'])
#         put_strikes.sort(key=lambda x: x['strike'])
#         best_pair = None
#         min_price_diff = float('inf')
#         for call in call_strikes:
#             for put in put_strikes:
#                 try:
#                     call_price = kite.ltp(call['exchange'] + ':' + call['tradingsymbol'])[call['exchange'] + ':' + call['tradingsymbol']]['last_price']
#                     put_price = kite.ltp(put['exchange'] + ':' + put['tradingsymbol'])[put['exchange'] + ':' + put['tradingsymbol']]['last_price']
#                     price_diff = abs(call_price - put_price)
#                     price_diff_percentage = price_diff / ((call_price + put_price) / 2) * 100
#                     logging.info(f"Pair found: Call {call['tradingsymbol']}, Put {put['tradingsymbol']}, call_delta {calculate_delta(call, underlying_price)}, put_delta {calculate_delta(put, underlying_price)}")
#                     logging.info(f"call_price: {call_price}, put_price: {put_price}, price_diff: {price_diff}, price_diff_percentage {price_diff_percentage}, today_sl  {today_sl}")
#                     if abs(price_diff_percentage) <= 1.5:
#                         min_price_diff = price_diff
#                         best_pair = (call, put)
#                         call_sl_to_be_placed = round((call_price * today_sl) / 100)
#                         put_sl_to_be_placed = round((put_price * today_sl) / 100)
#                         logging.info(f"call_price: {call_price}, put_price: {put_price}, min_price_diff: {min_price_diff}, price_diff_percentage {price_diff_percentage}, today_sl  {today_sl} ,call_sl_to_be_placed {call_sl_to_be_placed}, put_sl_to_be_placed  {put_sl_to_be_placed}")
#                 except Exception as e:
#                     logging.error(f"Error fetching LTP or calculating price diff: {e}")
#                     time_module.sleep(30)
#         if best_pair:
#             logging.info(f"Best pair found: Call {best_pair[0]['tradingsymbol']} Put {best_pair[1]['tradingsymbol']} with price difference {min_price_diff:.2f}")
#         else:
#             logging.warning("No suitable pairs found.")
#         return best_pair
#     except Exception as e:
#         logging.error(f"Error finding strikes: {e}")
#         return None
def find_strikes(options, underlying_price, target_delta_low, target_delta_high):
    import openai  # Ensure your API key is configured
    atm_strike = round(underlying_price / 50) * 50
    logging.info(f"ATM strike: {atm_strike}")
    global call_sl_to_be_placed
    global put_sl_to_be_placed

    logging.info(f"Finding strikes with delta between {target_delta_low} and {target_delta_high} within {atm_strike - 500} to {atm_strike + 500}")
    if VWAP_ENABLED:
        logging.info(f"VWAP analysis enabled (Priority: {VWAP_PRIORITY}, Minutes: {VWAP_MINUTES})")

    try:
        call_strikes = []
        put_strikes = []
        option_summary = []

        for o in options:
            if atm_strike - 500 <= o['strike'] <= atm_strike + 500:
                delta = calculate_delta(o, underlying_price)
                if delta is None:
                    continue
                o['delta'] = delta
                if target_delta_low <= delta <= target_delta_high:
                    if o['instrument_type'] == 'CE':
                        call_strikes.append(o)
                    elif o['instrument_type'] == 'PE':
                        put_strikes.append(o)
                option_summary.append(o)

        if not call_strikes or not put_strikes:
            logging.warning("No strikes found with the desired delta range.")
            return None

        call_strikes.sort(key=lambda x: x['strike'])
        put_strikes.sort(key=lambda x: x['strike'])

        best_pair = None
        min_price_diff = float('inf')
        suitable_pairs = []
        all_pairs = []  # Store all pairs for analysis

        for call in call_strikes:
            for put in put_strikes:
                try:
                    if VWAP_ENABLED:
                        # Get VWAP data for both strikes
                        call_vwap_data = get_strike_vwap_data(call)
                        put_vwap_data = get_strike_vwap_data(put)
                        
                        call_price = call_vwap_data['ltp']
                        put_price = put_vwap_data['ltp']
                        call_vwap = call_vwap_data['vwap']
                        put_vwap = put_vwap_data['vwap']
                    else:
                        # Fallback to simple LTP without VWAP
                        call_price = kite.ltp(call['exchange'] + ':' + call['tradingsymbol'])[call['exchange'] + ':' + call['tradingsymbol']]['last_price']
                        put_price = kite.ltp(put['exchange'] + ':' + put['tradingsymbol'])[put['exchange'] + ':' + put['tradingsymbol']]['last_price']
                        call_vwap = None
                        put_vwap = None
                    
                    if call_price is None or put_price is None:
                        continue
                        
                    price_diff = abs(call_price - put_price)
                    price_diff_percentage = price_diff / ((call_price + put_price) / 2) * 100
                    
                    # Check VWAP conditions
                    call_below_vwap = call_vwap is not None and call_price < call_vwap
                    put_below_vwap = put_vwap is not None and put_price < put_vwap
                    both_below_vwap = call_below_vwap and put_below_vwap
                    
                    # Log detailed information for each pair
                    logging.info(f"\n{'='*60}")
                    logging.info(f"ANALYZING STRIKE PAIR:")
                    call_vwap_str = f"{call_vwap:.2f}" if call_vwap is not None else "N/A"
                    put_vwap_str = f"{put_vwap:.2f}" if put_vwap is not None else "N/A"
                    logging.info(f"Call: {call['tradingsymbol']} | Price: {call_price:.2f} | VWAP: {call_vwap_str} | Delta: {call['delta']:.3f}")
                    logging.info(f"Put:  {put['tradingsymbol']} | Price: {put_price:.2f} | VWAP: {put_vwap_str} | Delta: {put['delta']:.3f}")
                    logging.info(f"Price Difference: {price_diff:.2f} ({price_diff_percentage:.2f}%)")
                    if VWAP_ENABLED:
                        logging.info(f"Call below VWAP: {call_below_vwap}")
                        logging.info(f"Put below VWAP: {put_below_vwap}")
                        logging.info(f"Both below VWAP: {both_below_vwap}")
                    
                    # Store all pairs for analysis
                    pair_info = {
                        'call': call,
                        'put': put,
                        'call_price': call_price,
                        'put_price': put_price,
                        'call_vwap': call_vwap,
                        'put_vwap': put_vwap,
                        'call_delta': call['delta'],
                        'put_delta': put['delta'],
                        'price_diff': price_diff,
                        'price_diff_percentage': price_diff_percentage,
                        'both_below_vwap': both_below_vwap,
                        'within_price_limit': abs(price_diff_percentage) <= 1.5
                    }
                    
                    all_pairs.append(pair_info)
                    
                    # Check if price difference is within acceptable range
                    if abs(price_diff_percentage) <= 1.5:
                        suitable_pairs.append(pair_info)
                        
                        # Prioritize pairs where both strikes are below VWAP
                        if VWAP_ENABLED and VWAP_PRIORITY and both_below_vwap:
                            if price_diff < min_price_diff:
                                min_price_diff = price_diff
                                best_pair = (call, put)
                                call_sl_to_be_placed = round((call_price * today_sl) / 100)
                                put_sl_to_be_placed = round((put_price * today_sl) / 100)
                                logging.info(f"[OK] NEW BEST PAIR (Both below VWAP): {call['tradingsymbol']} and {put['tradingsymbol']}")
                                logging.info(f"call_price: {call_price}, put_price: {put_price}, min_price_diff: {min_price_diff}, price_diff_percentage {price_diff_percentage}, today_sl {today_sl}")
                                logging.info(f"call_sl_to_be_placed {call_sl_to_be_placed}, put_sl_to_be_placed {put_sl_to_be_placed}")
                        elif best_pair is None:  # If no VWAP-suitable pair found, use price difference
                            if price_diff < min_price_diff:
                                min_price_diff = price_diff
                                best_pair = (call, put)
                                call_sl_to_be_placed = round((call_price * today_sl) / 100)
                                put_sl_to_be_placed = round((put_price * today_sl) / 100)
                                if VWAP_ENABLED and VWAP_PRIORITY:
                                    logging.info(f"[!] FALLBACK BEST PAIR (Price-based): {call['tradingsymbol']} and {put['tradingsymbol']}")
                                else:
                                    logging.info(f"[OK] BEST PAIR (Price-based): {call['tradingsymbol']} and {put['tradingsymbol']}")
                                logging.info(f"call_price: {call_price}, put_price: {put_price}, min_price_diff: {min_price_diff}, price_diff_percentage {price_diff_percentage}, today_sl {today_sl}")
                                logging.info(f"call_sl_to_be_placed {call_sl_to_be_placed}, put_sl_to_be_placed {put_sl_to_be_placed}")
                                
                except Exception as e:
                    logging.error(f"Error analyzing strike pair {call['tradingsymbol']} - {put['tradingsymbol']}: {e}")
                    time_module.sleep(30)

        # Log summary of all pairs analyzed
        if all_pairs:
            logging.info(f"\n{'='*60}")
            logging.info(f"ALL PAIRS ANALYSIS SUMMARY:")
            logging.info(f"Total pairs analyzed: {len(all_pairs)}")
            logging.info(f"Pairs within price limit (1.5%): {len(suitable_pairs)}")
            
            if VWAP_ENABLED:
                vwap_suitable_pairs = [p for p in all_pairs if p['both_below_vwap']]
                logging.info(f"Pairs with both strikes below VWAP: {len(vwap_suitable_pairs)}")
                
                # Show all pairs with their status
                for i, pair in enumerate(all_pairs, 1):
                    price_status = "[OK] WITHIN LIMIT" if pair['within_price_limit'] else "[X] EXCEEDS LIMIT"
                    vwap_status = "[OK] VWAP-SUITABLE" if pair['both_below_vwap'] else "[!] VWAP-NOT-SUITABLE"
                    logging.info(f"{i}. {price_status} | {vwap_status} | Call: {pair['call']['tradingsymbol']} | Put: {pair['put']['tradingsymbol']} | Diff: {pair['price_diff_percentage']:.2f}%")
            else:
                # Show all pairs with price status only
                for i, pair in enumerate(all_pairs, 1):
                    price_status = "[OK] WITHIN LIMIT" if pair['within_price_limit'] else "[X] EXCEEDS LIMIT"
                    logging.info(f"{i}. {price_status} | Call: {pair['call']['tradingsymbol']} | Put: {pair['put']['tradingsymbol']} | Diff: {pair['price_diff_percentage']:.2f}%")

        if best_pair:
            call, put = best_pair
            # Find the pair info for the best pair
            best_pair_info = next((p for p in all_pairs 
                             if p['call']['tradingsymbol'] == call['tradingsymbol'] 
                             and p['put']['tradingsymbol'] == put['tradingsymbol']), None)
            
            if best_pair_info:
                if VWAP_ENABLED and best_pair_info['both_below_vwap']:
                    logging.info(f"\n[TARGET] FINAL SELECTION - VWAP OPTIMAL:")
                    call_vwap_str = f"{best_pair_info['call_vwap']:.2f}" if best_pair_info['call_vwap'] is not None else "N/A"
                    put_vwap_str = f"{best_pair_info['put_vwap']:.2f}" if best_pair_info['put_vwap'] is not None else "N/A"
                    logging.info(f"Call: {call['tradingsymbol']} | Price: {best_pair_info['call_price']:.2f} | VWAP: {call_vwap_str} | Delta: {best_pair_info['call_delta']:.3f}")
                    logging.info(f"Put:  {put['tradingsymbol']} | Price: {best_pair_info['put_price']:.2f} | VWAP: {put_vwap_str} | Delta: {best_pair_info['put_delta']:.3f}")
                    logging.info(f"Price Difference: {best_pair_info['price_diff']:.2f} ({best_pair_info['price_diff_percentage']:.2f}%)")
                    logging.info(f"[OK] BOTH STRIKES BELOW VWAP - SUITABLE FOR ENTRY")
                elif VWAP_ENABLED and VWAP_PRIORITY:
                    logging.info(f"\n[!] FINAL SELECTION - PRICE-BASED (VWAP not optimal):")
                    call_vwap_str = f"{best_pair_info['call_vwap']:.2f}" if best_pair_info['call_vwap'] is not None else "N/A"
                    put_vwap_str = f"{best_pair_info['put_vwap']:.2f}" if best_pair_info['put_vwap'] is not None else "N/A"
                    logging.info(f"Call: {call['tradingsymbol']} | Price: {best_pair_info['call_price']:.2f} | VWAP: {call_vwap_str} | Delta: {best_pair_info['call_delta']:.3f}")
                    logging.info(f"Put:  {put['tradingsymbol']} | Price: {best_pair_info['put_price']:.2f} | VWAP: {put_vwap_str} | Delta: {best_pair_info['put_delta']:.3f}")
                    logging.info(f"Price Difference: {best_pair_info['price_diff']:.2f} ({best_pair_info['price_diff_percentage']:.2f}%)")
                    logging.info(f"[!] NOT BOTH BELOW VWAP - CONSIDER WAITING FOR BETTER ENTRY")
                else:
                    logging.info(f"\n[OK] FINAL SELECTION - PRICE-BASED:")
                    logging.info(f"Call: {call['tradingsymbol']} | Price: {best_pair_info['call_price']:.2f} | Delta: {best_pair_info['call_delta']:.3f}")
                    logging.info(f"Put:  {put['tradingsymbol']} | Price: {best_pair_info['put_price']:.2f} | Delta: {best_pair_info['put_delta']:.3f}")
                    logging.info(f"Price Difference: {best_pair_info['price_diff']:.2f} ({best_pair_info['price_diff_percentage']:.2f}%)")
                    logging.info(f"[OK] SUITABLE FOR ENTRY")
            else:
                logging.info(f"[OK] Best pair selected for trading: {call['tradingsymbol']} and {put['tradingsymbol']}")
        else:
            logging.warning("No suitable trading pair found.")
            
        return best_pair

    except Exception as e:
        logging.error(f"Error in find_strikes: {e}")
        return None


def place_order(strike, transaction_type, is_amo, quantity):
    order_variety = kite.VARIETY_AMO if is_amo else kite.VARIETY_REGULAR
    logging.info(f"Placing {'AMO' if is_amo else 'market'} order for {strike['tradingsymbol']} with transaction type {transaction_type}")
    try:
        ltp = kite.ltp(strike['exchange'] + ':' + strike['tradingsymbol'])[strike['exchange'] + ':' + strike['tradingsymbol']]['last_price']
        limit_price = ltp
        order_id = kite.place_order(
            variety=order_variety,
            exchange=kite.EXCHANGE_NFO,
            tradingsymbol=strike['tradingsymbol'],
            transaction_type=transaction_type,
            quantity=quantity,
            order_type=kite.ORDER_TYPE_MARKET,
            price=limit_price,
            product=kite.PRODUCT_NRML,
            tag="Automation"
        )
        logging.info(f"Order placed successfully. ID: {order_id}, LTP : {ltp}")
        return order_id
    except Exception as e:
        logging.error(f"Error placing order: {e}")
        time_module.sleep(3)
        return None


def place_stop_loss_order(strike, transaction_type, stop_loss_price, quantity):
    logging.info(f"Placing stop-loss order for {strike['tradingsymbol']} with transaction type {transaction_type} and SL price {stop_loss_price}")
    try:
        order_id = kite.place_order(
            variety=kite.VARIETY_REGULAR,
            exchange=kite.EXCHANGE_NFO,
            tradingsymbol=strike['tradingsymbol'],
            transaction_type=kite.TRANSACTION_TYPE_BUY if transaction_type == kite.TRANSACTION_TYPE_SELL else kite.TRANSACTION_TYPE_SELL,
            quantity=quantity,
            price=stop_loss_price + 1,
            order_type=kite.ORDER_TYPE_SL,
            trigger_price=stop_loss_price,
            product=kite.PRODUCT_NRML,
            tag="Automation"
        )
        logging.info(f"Stop-loss order placed successfully. ID: {order_id}")
        return order_id
    except Exception as e:
        logging.error(f"Error placing stop-loss order: {e}")
        time_module.sleep(3)
        return None


def exit_trade(order_id, strike):
    """Cancels an active order based on the order_id."""
    try:
        kite.cancel_order(variety=kite.VARIETY_REGULAR, order_id=order_id)
        logging.info(f"Exited trade for {strike['tradingsymbol']} with order ID: {order_id}")
    except Exception as e:
        logging.error(f"Error exiting trade for {strike['tradingsymbol']}: {e}")
        time_module.sleep(5)


def modify_stop_loss_order(order_id, new_trigger_price, new_limit_price):
    """Modifies the stop-loss order with new trigger and limit prices."""
    try:
        modified_order_id = kite.modify_order(
            variety=kite.VARIETY_REGULAR,
            order_id=order_id,
            trigger_price=new_trigger_price,
            price=new_limit_price
        )
        logging.info(f"Modified stop-loss order. New trigger price: {new_trigger_price}, limit price: {new_limit_price}, Order ID: {modified_order_id}")
        return modified_order_id
    except Exception as e:
        try:
            logging.error(f"Error modifying stop-loss order: {e}")
            modify_stop_loss_order(order_id, new_trigger_price+1, new_limit_price+2)
        except Exception as e:
            logging.error(f"Error modifying stop-loss order Second times : {e}")
    return None


def monitor_trades(call_order_id, put_order_id, call_strike, put_strike, call_sl_order_id, put_sl_order_id, target_delta_high):
    end_time = time(14, 50)
    loss_taken = 0
    hedge_taken = False
    global stop_loss_trigger_count

    try:
        call_initial_price = kite.ltp(f"NFO:{call_strike['tradingsymbol']}")[f"NFO:{call_strike['tradingsymbol']}"]["last_price"]
        put_initial_price = kite.ltp(f"NFO:{put_strike['tradingsymbol']}")[f"NFO:{put_strike['tradingsymbol']}"]["last_price"]
        initial_total_premium = call_initial_price + put_initial_price
        logging.info(f"Initial Total Premium Received: {initial_total_premium}")
    except Exception as e:
        logging.error(f"Error calculating initial total premium: {e}")
        return

    adjusted_for_14_points = False
    adjusted_for_28_points = False
    New_trade_taken = False

    while True:
        now = datetime.now().time()

        # Stop trades if stop-loss has been triggered three times
        if stop_loss_trigger_count >= MAX_STOP_LOSS_TRIGGER:
            logging.info("Stop-loss triggered three times. No more trades will be taken.")
            modify_stop_loss_order(call_sl_order_id, call_ltp + 1, call_ltp + 2)
            modify_stop_loss_order(put_sl_order_id, put_ltp + 1, put_ltp + 2)
            break

        # Exit trades and modify stop-loss at market close
        if now >= end_time:
            logging.info("Market is closing, modifying stop-loss orders.")
            modify_stop_loss_order(call_sl_order_id, call_ltp + 1, call_ltp + 2)
            modify_stop_loss_order(put_sl_order_id, put_ltp + 1, put_ltp + 2)
            break

        try:
            underlying_price = kite.ltp("NSE:NIFTY 50")["NSE:NIFTY 50"]["last_price"]
            call_ltp = kite.ltp(f"NFO:{call_strike['tradingsymbol']}")[f"NFO:{call_strike['tradingsymbol']}"]["last_price"]
            put_ltp = kite.ltp(f"NFO:{put_strike['tradingsymbol']}")[f"NFO:{put_strike['tradingsymbol']}"]["last_price"]
            current_total_premium = call_ltp + put_ltp

            if New_trade_taken:
                initial_total_premium = current_total_premium
                current_total_premium = current_total_premium + loss_taken
                New_trade_taken = False

            logging.info(f" Initial Total Premium Received: {initial_total_premium} , Current Total Premium: {current_total_premium} , loss_taken: {loss_taken}")
            Tpl=initial_total_premium-current_total_premium-loss_taken
            # logging.info(
            #     f" Total Profit and Loss: {Tpl} ")
            logging.info(
                f"\033[92mTotal Profit and Loss: {Tpl:.2f}\033[0m" if Tpl >= 0 else f"\033[91mTotal Profit and Loss: {Tpl:.2f}\033[0m")

            # Adjust stop-loss orders if premium reduces
            if not adjusted_for_14_points and initial_total_premium - current_total_premium >= loss_taken + 14:
                logging.info(f"Total premium reduced by {initial_total_premium - current_total_premium} points, modifying stop-loss orders.")
                modify_stop_loss_order(call_sl_order_id, call_ltp + 1, call_ltp + 2)
                modify_stop_loss_order(put_sl_order_id, put_ltp + 1, put_ltp + 2)
                adjusted_for_14_points = True

            if not adjusted_for_28_points and initial_total_premium - current_total_premium >= loss_taken + 28:
                logging.info("Total premium reduced by 24 points, modifying stop-loss orders.")
                modify_stop_loss_order(call_sl_order_id, call_ltp + 1, call_ltp + 2)
                modify_stop_loss_order(put_sl_order_id, put_ltp + 1, put_ltp + 2)
                adjusted_for_28_points = True

            # Take Hedges when 10 points recieved
            if not hedge_taken and initial_total_premium - current_total_premium >= loss_taken + 10:
                logging.info(
                    f"Total premium reduced by {initial_total_premium - current_total_premium- loss_taken } points, Taking Hedges .")

                try:
                    call_hedge, put_hedge = find_hedges(call_strike, put_strike)
                    # Place hedge buy orders
                    if call_hedge:
                        place_order(call_hedge, kite.TRANSACTION_TYPE_BUY, False, call_quantity)
                    if put_hedge:
                        place_order(put_hedge, kite.TRANSACTION_TYPE_BUY, False , put_quantity)
                    hedge_taken = True
                except Exception as e:
                    logging.error(f"Error placing Hedge orders: {e}")
            else:
                logging.info(f"Waiting for Hedges : {now}")

        except Exception as e:
            logging.error(f"Error monitoring trades: {e}")

        call_delta = calculate_delta(call_strike, underlying_price)
        put_delta = calculate_delta(put_strike, underlying_price)
        logging.info(f"Call Strike Delta:  {call_delta}, Put Strike Delta:  {put_delta}, underlying_price: {underlying_price}")

        if abs(call_delta) > target_delta_high + 0.1 or abs(put_delta) > target_delta_high + 0.1:
            logging.info("Delta exceeded the limit, exiting trades and re-entering")
            exit_trade(call_order_id, call_strike)
            exit_trade(put_order_id, put_strike)
            time_module.sleep(10)
            execute_trade(TARGET_DELTA_LOW, TARGET_DELTA_HIGH)
            break

        try:
            call_order_status = kite.order_history(call_sl_order_id)[-1]['status']
            put_order_status = kite.order_history(put_sl_order_id)[-1]['status']
            logging.info(f"call_order_status: {call_order_status}, put_order_status: {put_order_status}")
            if call_order_status == 'COMPLETE':
                logging.info(f"Call stop-loss order {call_sl_order_id} triggered, finding new call strike")
                stop_loss_trigger_count += 1
                if stop_loss_trigger_count < MAX_STOP_LOSS_TRIGGER:
                    time_module.sleep(5)
                    new_strike = find_new_strike(underlying_price, call_strike, 'CE')
                    if new_strike and not adjusted_for_14_points:
                        new_order_id = place_order(new_strike, kite.TRANSACTION_TYPE_SELL, False, call_quantity)
                        if new_order_id:
                            # Place new stop-loss order
                            call_ltp = kite.ltp(f"NFO:{new_strike['tradingsymbol']}")[f"NFO:{new_strike['tradingsymbol']}"]['last_price']
                            sl_price = call_ltp + call_sl_to_be_placed
                            new_sl_order_id = place_stop_loss_order(new_strike, kite.TRANSACTION_TYPE_SELL, sl_price, call_quantity)
                            call_order_id, call_sl_order_id, call_strike = new_order_id, new_sl_order_id, new_strike
                            loss_taken += (current_total_premium - initial_total_premium)
                            logging.info(f"Loss_taken- {loss_taken}")
                            New_trade_taken = True

            if put_order_status == 'COMPLETE':
                logging.info(f"Put stop-loss order {put_sl_order_id} triggered, finding new put strike")
                stop_loss_trigger_count += 1
                if stop_loss_trigger_count < MAX_STOP_LOSS_TRIGGER:
                    new_strike = find_new_strike(underlying_price, put_strike, 'PE')
                    time_module.sleep(15)
                    if new_strike and not adjusted_for_14_points:
                        new_order_id = place_order(new_strike, kite.TRANSACTION_TYPE_SELL, False, put_quantity)
                        if new_order_id:
                            # Place new stop-loss order
                            put_ltp = kite.ltp(f"NFO:{new_strike['tradingsymbol']}")[f"NFO:{new_strike['tradingsymbol']}"]['last_price']
                            sl_price = put_ltp + put_sl_to_be_placed
                            new_sl_order_id = place_stop_loss_order(new_strike, kite.TRANSACTION_TYPE_SELL, sl_price, put_quantity)
                            put_order_id, put_sl_order_id, put_strike = new_order_id, new_sl_order_id, new_strike
                            loss_taken += (current_total_premium - initial_total_premium)
                            logging.info(f"Loss_taken- {loss_taken}")
                            New_trade_taken = True

        except Exception as e:
            logging.error(f"Error checking stop-loss orders: {e}")

        time_module.sleep(3)


def find_new_strike(underlying_price, old_strike, option_type):
    try:
        options = fetch_option_chain()
        if not options:
            logging.error("No options fetched.")
            return None

        new_strikes = [o for o in options if o['instrument_type'] == option_type and o['expiry'] == old_strike['expiry']]
        # TARGET_DELTA_HIGH=0.35
        for strike in new_strikes:
            delta = calculate_delta(strike, underlying_price)
            if delta and TARGET_DELTA_LOW <= delta <= TARGET_DELTA_HIGH:
                return strike
        return None
    except Exception as e:
        logging.error(f"Error finding new strike: {e}")
        return None


def get_next_week_expiry(options):
    expiries = sorted(set(o['expiry'] for o in options))
    today = date.today() + timedelta(days=2)  # Add one day to today's date
    for expiry in expiries:
        if isinstance(expiry, str):
            expiry_date = datetime.strptime(expiry, '%Y-%m-%d').date()
        else:
            expiry_date = expiry
        if expiry_date > today:
            return expiry_date
    return None


def is_expiry_within_2_days(expiry_date):
    today = date.today()
    return (expiry_date - today).days <= 2


def execute_trade(target_delta_low, target_delta_high):
    global last_hedge_fetch_time
    current_time = datetime.now()

    while True:
        options = fetch_option_chain()
        if not options:
            logging.error("No options fetched.")
            time_module.sleep(30)
            continue

        current_expiry = options[0]['expiry']
        if isinstance(current_expiry, str):
            current_expiry = datetime.strptime(current_expiry, '%Y-%m-%d').date()

        if is_expiry_within_2_days(current_expiry):
            logging.info("Current expiry is within 2 days, finding next week's expiry")
            next_expiry = get_next_week_expiry(options)
            options = [o for o in options if o['expiry'] == next_expiry]
            logging.info(f"Next week's expiry: {next_expiry}")
        else:
            options = [o for o in options if o['expiry'] == current_expiry]

        try:
            underlying_price = kite.ltp("NSE:NIFTY 50")["NSE:NIFTY 50"]["last_price"]
        except Exception as e:
            logging.error(f"Error fetching underlying price: {e}")
            time_module.sleep(30)
            continue

        strikes = find_strikes(options, underlying_price, target_delta_low, target_delta_high)
        if not strikes:
            logging.warning("No suitable strikes found. Retrying...")
            time_module.sleep(10)
            continue

        call_strike, put_strike = strikes

        now = datetime.now().time()
        market_start = time(9, 15)
        market_end = time(14, 50)
        is_amo = not (market_start <= now <= market_end)
        logging.info(f"Script call_sl_to_be_placed, {call_sl_to_be_placed}")
        logging.info(f"Script put_sl_to_be_placed, {put_sl_to_be_placed}")

        # Place main orders
        call_order_id = place_order(call_strike, kite.TRANSACTION_TYPE_SELL, is_amo, call_quantity)
        put_order_id = place_order(put_strike, kite.TRANSACTION_TYPE_SELL, is_amo, put_quantity)

        if call_order_id and put_order_id:
            # Now place stop-loss orders
            try:
                # Get LTPs
                call_ltp = kite.ltp(f"NFO:{call_strike['tradingsymbol']}")[f"NFO:{call_strike['tradingsymbol']}"]['last_price']
                put_ltp = kite.ltp(f"NFO:{put_strike['tradingsymbol']}")[f"NFO:{put_strike['tradingsymbol']}"]['last_price']

                # Calculate stop-loss prices
                call_sl_price = call_ltp + call_sl_to_be_placed  # Assuming transaction_type is SELL
                put_sl_price = put_ltp + put_sl_to_be_placed     # Assuming transaction_type is SELL

                # Place stop-loss orders
                call_sl_order_id = place_stop_loss_order(call_strike, kite.TRANSACTION_TYPE_SELL, call_sl_price, call_quantity)
                put_sl_order_id = place_stop_loss_order(put_strike, kite.TRANSACTION_TYPE_SELL, put_sl_price, put_quantity)

                if call_sl_order_id and put_sl_order_id:
                    # Proceed to monitor trades
                    monitor_trades(call_order_id, put_order_id, call_strike, put_strike, call_sl_order_id, put_sl_order_id, target_delta_high)
                    break
                else:
                    logging.error("Failed to place stop-loss orders.")
                    # Handle accordingly
            except Exception as e:
                logging.error(f"Error placing stop-loss orders: {e}")
                # Handle accordingly
        else:
            logging.error("Failed to place main orders.")
            # Handle accordingly


def main():
    logging.info("Script started")
    target_time = time(9, 45)
    end_time = time(14, 50)

    while True:
        now = datetime.now().time()
        try:
            underlying_price = kite.ltp('NSE:NIFTY 50')['NSE:NIFTY 50']['last_price']
            logging.info(f"Underlying price: {underlying_price}")
        except Exception as e:
            logging.error(f"Error fetching underlying price: {e}")
        if now >= target_time:
            logging.info("Executing trade")
            execute_trade(TARGET_DELTA_LOW, TARGET_DELTA_HIGH)
            break

        time_module.sleep(30)

# ------------------------------
# FIND HEDGE STRIKES
# ------------------------------
def find_hedges(call_strike, put_strike):
    """
    For sold Call -> Buy hedge 100 points lower.
    For sold Put  -> Buy hedge 100 points higher.
    """
    options = fetch_option_chain()
    if not options:
        logging.error("No options fetched.")
        return None

    # call_hedge = next((o for o in options if o['strike'] == call_strike['strike'] - 100 and o['instrument_type'] == 'CE'), None)
    # put_hedge = next((o for o in options if o['strike'] == put_strike['strike'] + 100 and o['instrument_type'] == 'PE'), None)
    call_hedge = next(
        (o for o in options
         if o['strike'] == call_strike['strike'] - 100
         and o['instrument_type'] == 'CE'
         and o['expiry'] == call_strike['expiry']),
        None
    )
    put_hedge = next(
        (o for o in options
         if o['strike'] == put_strike['strike'] + 100
         and o['instrument_type'] == 'PE'
         and o['expiry'] == put_strike['expiry']),
        None
    )
    if not call_hedge:
        logging.warning(f"No hedge found 100 points below {call_strike['strike']} CE")
    if not put_hedge:
        logging.warning(f"No hedge found 100 points above {put_strike['strike']} PE")

    return call_hedge, put_hedge

if __name__ == "__main__":
    today_sl = 0
    call_sl_to_be_placed = 0
    put_sl_to_be_placed = 0
    loss_taken = 0

    call_quantity = int(input("Enter Call Quantity: ").strip())
    put_quantity = int(input("Enter Put Quantity: ").strip())

    logging.info(f"api_key : {Input_api_key}")
    logging.info(f"api_secret : {Input_api_secret}")
    logging.info(f"request_token : {Input_request_token}")
    logging.info(f"Account : {Input_account}")

    current_day = datetime.now().strftime('%A')

    if current_day == "Thursday":
        today_sl = 25
    elif current_day == "Friday":
        today_sl = 27
    elif current_day == "Monday":
        today_sl = 30
    elif current_day == "Tuesday":
        today_sl = 32
    elif current_day == "Wednesday":
        today_sl = 25
    else:
        today_sl = 35

    logging.info(f"today_sl: {today_sl}, {current_day}")

    main()
