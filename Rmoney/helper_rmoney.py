import datetime
import time
from datetime import timedelta
import json
import os

##############################################
# GLOBAL XTS CONNECTIONS (set by init)
##############################################
xt_md = None
xt_interactive = None
userid = None

# Search cache (same as rmoney_quotes_v2.py)
SEARCH_CACHE = {}

##############################################
# INITIALIZATION
##############################################
def initialize():
    """Initialize XTS connections - call this first!"""
    global xt_md, xt_interactive, userid

    from Connect import XTSConnect

    # Load tokens
    try:
        with open("rmoney_tokens.json", "r") as f:
            tokens = json.load(f)
            md_token = tokens["marketdata_token"]
            interactive_token = tokens["interactive_token"]
            userid = tokens["userID"]
    except:
        print("No token found. Run rmoney_login_v2.py first.")
        return False

    # Initialize Market Data API
    xt_md = XTSConnect(apiKey=os.environ["RMONEY_MARKETDATA_API_KEY"], secretKey=os.environ["RMONEY_MARKETDATA_SECRET"], source="WebAPI")
    xt_md.token = md_token

    # Initialize Interactive API
    xt_interactive = XTSConnect(apiKey=os.environ["RMONEY_INTERACTIVE_API_KEY"], secretKey=os.environ["RMONEY_INTERACTIVE_SECRET"], source="WEBAPI")
    xt_interactive.token = interactive_token

    print("API connected successfully")

    # Pre-cache option data for faster order placement
    search_and_cache_underlying("NIFTY", segment=2)
    search_and_cache_underlying("BANKNIFTY", segment=2)
    search_and_cache_underlying("FINNIFTY", segment=2)

    return True

##############################################
# SEARCH AND CACHE (same as rmoney_quotes_v2.py)
##############################################
def search_and_cache_underlying(underlying, segment=2):
    """Search for an underlying and cache all results"""
    global xt_md, SEARCH_CACHE

    cache_key = f"{underlying}_{segment}"

    if cache_key in SEARCH_CACHE:
        return SEARCH_CACHE[cache_key]

    try:
        response = xt_md.search_by_scriptname(searchString=underlying)

        if isinstance(response, list):
            items = response
        elif isinstance(response, dict) and response.get("type") == "success":
            items = response.get("result", [])
            if isinstance(items, dict):
                items = items.get("instruments", []) or items.get("values", []) or []
        else:
            items = []

        SEARCH_CACHE[cache_key] = items
        return items

    except:
        SEARCH_CACHE[cache_key] = []
        return []


def find_option_eid(underlying, strike, option_type, segment=2):
    """Find option instrument ID from cache"""
    global SEARCH_CACHE

    cache_key = f"{underlying}_{segment}"
    items = SEARCH_CACHE.get(cache_key, [])

    print(f"DEBUG find_option_eid: cache has {len(items)} items for {cache_key}")

    matches_found = 0
    for item in items:
        if item.get("ExchangeSegment") != segment:
            continue

        # Check strike (convert to int for comparison)
        item_strike = item.get("StrikePrice") or item.get("strikePrice")
        try:
            if int(float(item_strike)) == int(strike):
                matches_found += 1
                item_opt_type = item.get("OptionType") or item.get("optionType")
                print(f"DEBUG: Found strike match {strike}, option_type={item_opt_type}")
        except:
            continue

    print(f"DEBUG: Total strike matches = {matches_found}")

    # Now do the actual search
    for item in items:
        if item.get("ExchangeSegment") != segment:
            continue

        # Check strike (convert to int for comparison)
        item_strike = item.get("StrikePrice") or item.get("strikePrice")
        try:
            if int(float(item_strike)) != int(strike):
                continue
        except:
            continue

        # Check option type
        item_opt_type = item.get("OptionType") or item.get("optionType")

        if option_type == "CE":
            if item_opt_type not in (1, 3, "CE", "CALL", "Call"):
                continue
        elif option_type == "PE":
            if item_opt_type not in (2, 4, "PE", "PUT", "Put"):
                continue

        return item.get("ExchangeInstrumentID") or item.get("exchangeInstrumentID")

    return None


def find_option_eid_with_expiry(underlying, expiry_str, strike, option_type, segment=2):
    """Find option instrument ID from cache - WITH EXPIRY MATCHING"""
    global SEARCH_CACHE

    cache_key = f"{underlying}_{segment}"
    items = SEARCH_CACHE.get(cache_key, [])

    # Convert expiry string to date - handle ALL formats
    from datetime import datetime
    target_date = None

    try:
        if len(expiry_str) == 5:
            year = 2000 + int(expiry_str[:2])  # 26 -> 2026

            # Check what format it is
            if expiry_str[2:].isdigit():
                # Format 1: YYMDD (26120 = 2026-01-20)
                month = int(expiry_str[2:3])
                day = int(expiry_str[3:5])
                target_date = datetime(year, month, day).date()

            elif expiry_str[2] == 'O':
                # Format 2: YYODD (26O06 = 2026-10-06)
                month = 10  # October
                day = int(expiry_str[3:5])
                target_date = datetime(year, month, day).date()

            elif expiry_str[2] == 'N':
                # Format 3: YYNDD (26N03 = 2026-11-03)
                month = 11  # November
                day = int(expiry_str[3:5])
                target_date = datetime(year, month, day).date()

            elif expiry_str[2] == 'D':
                # Format 4: YYDDD (26D01 = 2026-12-01)
                month = 12  # December
                day = int(expiry_str[3:5])
                target_date = datetime(year, month, day).date()

            elif expiry_str[2:].isalpha():
                # Format 5: YYMON (26JAN = monthly expiry, last Thursday)
                monthly_expiries = {
                    '26JAN': datetime(2026, 1, 27).date(),
                    '26FEB': datetime(2026, 2, 24).date(),
                    '26MAR': datetime(2026, 3, 31).date(),
                    '26APR': datetime(2026, 4, 28).date(),
                    '26MAY': datetime(2026, 5, 26).date(),
                    '26JUN': datetime(2026, 6, 30).date(),
                    '26JUL': datetime(2026, 7, 28).date(),
                    '26AUG': datetime(2026, 8, 25).date(),
                    '26SEP': datetime(2026, 9, 29).date(),
                    '26OCT': datetime(2026, 10, 27).date(),
                    '26NOV': datetime(2026, 11, 24).date(),
                    '26DEC': datetime(2026, 12, 29).date(),
                }
                target_date = monthly_expiries.get(expiry_str)

    except Exception:
        pass

    if not target_date:
        return None

    # Search for matching instrument
    for item in items:
        if item.get("ExchangeSegment") != segment:
            continue

        # Check strike
        item_strike = item.get("StrikePrice") or item.get("strikePrice")
        try:
            if int(float(item_strike)) != int(strike):
                continue
        except:
            continue

        # Check option type
        item_opt_type = item.get("OptionType") or item.get("optionType")

        if option_type == "CE":
            if item_opt_type not in (1, 3, "CE", "CALL", "Call"):
                continue
        elif option_type == "PE":
            if item_opt_type not in (2, 4, "PE", "PUT", "Put"):
                continue

        # Check expiry date
        item_expiry_str = item.get("ContractExpiration") or item.get("ExpiryDate") or item.get("ContractExpirationString") or ""

        try:
            # Parse "2026-01-20T14:30:00" format
            if 'T' in str(item_expiry_str):
                item_date = datetime.fromisoformat(str(item_expiry_str).split('T')[0]).date()
            else:
                item_date = datetime.fromisoformat(str(item_expiry_str)).date()

            # Match dates
            if target_date and item_date == target_date:
                return item.get("ExchangeInstrumentID") or item.get("exchangeInstrumentID")
        except:
            pass

    return None

##############################################
# QUOTE FUNCTIONS
##############################################
def getQuotes(symbol):
    """Get quote from JSON file (updated by rmoney_quotes_v2.py)"""
    try:
        with open("rmoney_data.json", "r") as f:
            data = json.load(f)
        return data.get(symbol)
    except:
        return None


def manualLTP(symbol):
    """Get LTP from JSON file - same as getQuotes"""
    return getQuotes(symbol)


def getHistorical(symbol, interval, duration):
    """Get historical data - like Fyers format"""
    global xt_md

    try:
        import pandas as pd
        import pytz
        from datetime import datetime, timedelta

        # Strip -EQ suffix if present
        search_symbol = symbol.replace("-EQ", "")

        eid = None
        segment = None

        # Check if it's an index (use known IDs)
        index_map = {
            "Nifty 50": 26000,
            "NIFTY": 26000,
            "Nifty Bank": 26001,
            "BANKNIFTY": 26001,
            "FINNIFTY": 26034,
        }

        if search_symbol in index_map:
            eid = index_map[search_symbol]
            segment = 1  # NSECM

        # Check if it's a future (ends with FUT)
        elif search_symbol.endswith("FUT"):
            # Index future - use cache
            if "NIFTY" in search_symbol and "BANK" not in search_symbol and "FIN" not in search_symbol:
                underlying = "NIFTY"
            elif "BANKNIFTY" in search_symbol:
                underlying = "BANKNIFTY"
            elif "FINNIFTY" in search_symbol:
                underlying = "FINNIFTY"
            else:
                underlying = None

            if underlying:
                eid = find_future_eid(underlying, segment=2)
                if eid:
                    segment = 2

        # Check if it's an option (contains CE or PE)
        elif "CE" in symbol or "PE" in symbol:
            import re

            # Determine underlying
            underlying = None
            if "BANKNIFTY" in symbol:
                underlying = "BANKNIFTY"
                prefix_len = len("BANKNIFTY")
            elif "FINNIFTY" in symbol:
                underlying = "FINNIFTY"
                prefix_len = len("FINNIFTY")
            elif "NIFTY" in symbol:
                underlying = "NIFTY"
                prefix_len = len("NIFTY")

            if underlying:
                # Extract expiry (5 chars after underlying: 26120)
                expiry_str = symbol[prefix_len:prefix_len+5]

                # Extract strike and type (last 4-6 digits + CE/PE)
                match = re.search(r'(\d{4,6})(CE|PE)$', symbol)
                if match:
                    strike = int(match.group(1))
                    opt_type = match.group(2)

                    # Use cached search with expiry filter
                    eid = find_option_eid_with_expiry(underlying, expiry_str, strike, opt_type, segment=2)
                    segment = 2  # NSEFO

        # If not option or option search failed, try direct search
        if not eid:
            response = xt_md.search_by_scriptname(searchString=search_symbol)
            items = response if isinstance(response, list) else response.get("result", [])

            # Find instrument
            for item in items:
                seg = item.get("ExchangeSegment")
                if seg == 2:  # F&O
                    eid = item.get("ExchangeInstrumentID")
                    segment = 2
                    break
                elif seg == 1 and item.get("Series") == "EQ":  # Equity
                    eid = item.get("ExchangeInstrumentID")
                    segment = 1
                    break

        if not eid:
            print(f"Symbol {symbol} not found")
            return None

        # Calculate date range
        end_time = datetime.now()
        start_date = (end_time - timedelta(days=duration)).date()

        # Start from 9:15 AM on the start date
        start_time = datetime.combine(start_date, datetime.strptime("09:15:00", "%H:%M:%S").time())

        start_time_str = start_time.strftime("%b %d %Y %H%M%S")
        end_time_str = end_time.strftime("%b %d %Y %H%M%S")

        # Always request 1-minute candles
        compression_value = str(60)  # 1 minute = 60 seconds

        # Get OHLC data
        response = xt_md.get_ohlc(
            exchangeSegment=segment,
            exchangeInstrumentID=eid,
            startTime=start_time_str,
            endTime=end_time_str,
            compressionValue=compression_value,
        )

        if not response or response.get("type") != "success":
            print(f"Failed to get historical data: {response}")
            return None

        # Parse data
        data_response = response["result"]["dataReponse"]
        data_lines = data_response.split(",")
        parsed_data = []

        for line in data_lines:
            if line.strip():
                parts = line.split("|")
                if len(parts) >= 5:
                    parsed_data.append({
                        "Timestamp": int(parts[0]),
                        "open": float(parts[1]),
                        "high": float(parts[2]),
                        "low": float(parts[3]),
                        "close": float(parts[4]),
                        "volume": int(parts[5]) if len(parts) > 5 and parts[5] else 0,
                    })

        if not parsed_data:
            return None

        # Create DataFrame
        df = pd.DataFrame(parsed_data)

        # XTS API returns timestamps in IST already, just localize to IST
        ist = pytz.timezone('Asia/Kolkata')
        df['Timestamp2'] = pd.to_datetime(df['Timestamp'], unit='s').dt.tz_localize(ist)

        # Filter rows before 15:30
        filtered_df = df[df['Timestamp2'].dt.time < pd.to_datetime('15:30').time()].copy()

        filtered_df['datetime2'] = filtered_df['Timestamp2'].copy()
        filtered_df.set_index('Timestamp2', inplace=True)

        # Resample to desired interval
        def get_daily_origin(date):
            return pytz.timezone('Asia/Kolkata').localize(datetime(date.year, date.month, date.day, 9, 15))

        resampled_df_list = []

        for date, group in filtered_df.groupby(filtered_df.index.date):
            origin = get_daily_origin(date)

            resampled_day = group.resample(f'{interval}min', label='left', origin=origin).agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum',
                'datetime2': 'first'
            })

            resampled_df_list.append(resampled_day)

        final_df = pd.concat(resampled_df_list)
        final_df = final_df.dropna(subset=['open'])

        return final_df

    except Exception as e:
        print(f"Error in getHistorical: {e}")
        return None

def find_future_eid(underlying, segment=2):
    """Find future instrument ID from cache"""
    cache_key = f"{underlying}_{segment}"
    items = SEARCH_CACHE.get(cache_key, [])

    from datetime import datetime

    monthly_expiries = {
        'NIFTY': datetime(2026, 1, 27).date(),
        'BANKNIFTY': datetime(2026, 1, 27).date(),
        'FINNIFTY': datetime(2026, 1, 27).date(),
    }

    target_date = monthly_expiries.get(underlying)
    if not target_date:
        return None

    for item in items:
        if item.get("ExchangeSegment") != segment:
            continue

        opt_type = item.get("OptionType") or item.get("optionType")
        if opt_type not in (0, None, ""):
            continue

        name = item.get("Name") or item.get("DisplayName") or ""
        if name != underlying:
            continue

        expiry_str = item.get("ContractExpiration") or item.get("ExpiryDate") or ""
        try:
            if 'T' in str(expiry_str):
                item_date = datetime.fromisoformat(str(expiry_str).split('T')[0]).date()
            else:
                item_date = datetime.fromisoformat(str(expiry_str)).date()

            if item_date == target_date:
                eid = item.get("ExchangeInstrumentID")
                return eid
        except:
            continue

    return None

##############################################
# ORDER FUNCTIONS
##############################################
def placeOrder(symbol, side, qty, ordertype, price, variety, papertrading=0, product="intraday_"):
    """Place order"""
    global xt_md, xt_interactive, userid

    if papertrading == 0:
        print(f"PAPER TRADE: {side} {qty} {symbol} {ordertype} @ {price}")
        return f"PAPER_TRADE_{int(time.time())}"

    eid = None
    segment = None

    # Segment mapping: number to name
    segment_map = {
        1: "NSECM",   # NSE Cash
        2: "NSEFO",   # NSE F&O
        11: "BSECM",  # BSE Cash
        12: "BSEFO",  # BSE F&O
        51: "MCXFO",  # MCX F&O
    }

    # Check if it's an option (contains CE or PE)
    if "CE" in symbol or "PE" in symbol:
        # Parse option symbol: NIFTY2612024900CE
        # Format: UNDERLYING + EXPIRY(5) + STRIKE + CE/PE
        import re

        # Determine underlying
        underlying = None
        if "BANKNIFTY" in symbol:
            underlying = "BANKNIFTY"
            prefix_len = len("BANKNIFTY")
        elif "FINNIFTY" in symbol:
            underlying = "FINNIFTY"
            prefix_len = len("FINNIFTY")
        elif "NIFTY" in symbol:
            underlying = "NIFTY"
            prefix_len = len("NIFTY")

        if underlying:
            # Extract expiry (5 chars after underlying: 26120)
            expiry_str = symbol[prefix_len:prefix_len+5]

            # Extract strike and type (last 4-6 digits + CE/PE)
            match = re.search(r'(\d{4,6})(CE|PE)$', symbol)
            if match:
                strike = int(match.group(1))
                opt_type = match.group(2)

                # Use cached search with expiry filter
                eid = find_option_eid_with_expiry(underlying, expiry_str, strike, opt_type, segment=2)

                if eid:
                    segment = segment_map.get(2, "NSEFO")

    # If not option or option search failed, try direct search
    if not eid:
        response = xt_md.search_by_scriptname(searchString=symbol)
        items = response if isinstance(response, list) else response.get("result", [])

        for item in items:
            seg = item.get("ExchangeSegment")
            if seg == 2:  # F&O
                eid = item.get("ExchangeInstrumentID")
                segment = segment_map.get(2, "NSEFO")
                break
            elif seg == 1 and item.get("Series") == "EQ":  # Equity
                eid = item.get("ExchangeInstrumentID")
                segment = segment_map.get(1, "NSECM")
                break

    if not eid:
        return "Symbol not found"

    if product == "intraday_eq" or product == "intraday_fno":
        product = "MIS"
    elif product == "positional_eq":
        product = "CNC"
    elif product == "positional_fno":
        product = "NRML"

    # Place order
    response = xt_interactive.place_order(
        exchangeSegment=segment,
        exchangeInstrumentID=eid,
        productType=product,
        orderType=ordertype,
        orderSide=side,
        timeInForce="DAY",
        disclosedQuantity=0,
        orderQuantity=qty,
        limitPrice=price if ordertype == "LIMIT" else 0,
        stopPrice=0,
        orderUniqueIdentifier=f"ORDER_{int(time.time())}",
        clientID=userid
    )

    if response and response.get("type") == "success":
        return response["result"]["AppOrderID"]
    return f"Failed: {response.get('description', 'Unknown error')}"

##############################################
# EXPIRY DATE FUNCTIONS
##############################################

def getNiftyExpiryDate():
    """Get nearest Nifty expiry date"""
    nifty_expiry = {
        datetime.datetime(2026, 1, 6).date(): '26106',
        datetime.datetime(2026, 1, 13).date(): '26113',
        datetime.datetime(2026, 1, 20).date(): '26120',
        datetime.datetime(2026, 1, 27).date(): '26JAN',
        datetime.datetime(2026, 2, 3).date(): '26203',
        datetime.datetime(2026, 2, 10).date(): '26210',
        datetime.datetime(2026, 2, 17).date(): '26217',
        datetime.datetime(2026, 2, 24).date(): '26FEB',
        datetime.datetime(2026, 3, 3).date(): '26302',
        datetime.datetime(2026, 3, 10).date(): '26310',
        datetime.datetime(2026, 3, 17).date(): '26317',
        datetime.datetime(2026, 3, 24).date(): '26324',
        datetime.datetime(2026, 3, 31).date(): '26MAR',
        datetime.datetime(2026, 4, 7).date(): '26407',
        datetime.datetime(2026, 4, 14).date(): '26413',
        datetime.datetime(2026, 4, 21).date(): '26421',
        datetime.datetime(2026, 4, 28).date(): '26APR',
        datetime.datetime(2026, 5, 5).date(): '26505',
        datetime.datetime(2026, 5, 12).date(): '26512',
        datetime.datetime(2026, 5, 19).date(): '26519',
        datetime.datetime(2026, 5, 26).date(): '26MAY',
        datetime.datetime(2026, 6, 2).date(): '26602',
        datetime.datetime(2026, 6, 9).date(): '26609',
        datetime.datetime(2026, 6, 16).date(): '26616',
        datetime.datetime(2026, 6, 23).date(): '26623',
        datetime.datetime(2026, 6, 30).date(): '26JUN',
        datetime.datetime(2026, 7, 7).date(): '26707',
        datetime.datetime(2026, 7, 14).date(): '26714',
        datetime.datetime(2026, 7, 21).date(): '26721',
        datetime.datetime(2026, 7, 28).date(): '26JUL',
        datetime.datetime(2026, 8, 4).date(): '26804',
        datetime.datetime(2026, 8, 11).date(): '26811',
        datetime.datetime(2026, 8, 18).date(): '26818',
        datetime.datetime(2026, 8, 25).date(): '26AUG',
        datetime.datetime(2026, 9, 1).date(): '26901',
        datetime.datetime(2026, 9, 8).date(): '26908',
        datetime.datetime(2026, 9, 15).date(): '26915',
        datetime.datetime(2026, 9, 22).date(): '26922',
        datetime.datetime(2026, 9, 29).date(): '26SEP',
        datetime.datetime(2026, 10, 6).date(): '26O06',
        datetime.datetime(2026, 10, 13).date(): '26O13',
        datetime.datetime(2026, 10, 20).date(): '26O19',
        datetime.datetime(2026, 10, 27).date(): '26OCT',
        datetime.datetime(2026, 11, 3).date(): '26N03',
        datetime.datetime(2026, 11, 10).date(): '26N09',
        datetime.datetime(2026, 11, 17).date(): '26N17',
        datetime.datetime(2026, 11, 24).date(): '26NOV',
        datetime.datetime(2026, 12, 1).date(): '26D01',
        datetime.datetime(2026, 12, 8).date(): '26D08',
        datetime.datetime(2026, 12, 15).date(): '26D15',
        datetime.datetime(2026, 12, 22).date(): '26D22',
        datetime.datetime(2026, 12, 29).date(): '26DEC',
    }

    today = datetime.datetime.now().date()
    for date_key, value in nifty_expiry.items():
        if today <= date_key:
            return value
    return None


def getNiftyNextExpiryDate():
    """Get next Nifty expiry date (skip nearest)"""
    nifty_expiry = {
        datetime.datetime(2026, 1, 6).date(): '26106',
        datetime.datetime(2026, 1, 13).date(): '26113',
        datetime.datetime(2026, 1, 20).date(): '26120',
        datetime.datetime(2026, 1, 27).date(): '26JAN',
        datetime.datetime(2026, 2, 3).date(): '26203',
        datetime.datetime(2026, 2, 10).date(): '26210',
        datetime.datetime(2026, 2, 17).date(): '26217',
        datetime.datetime(2026, 2, 24).date(): '26FEB',
        datetime.datetime(2026, 3, 3).date(): '26302',
        datetime.datetime(2026, 3, 10).date(): '26310',
        datetime.datetime(2026, 3, 17).date(): '26317',
        datetime.datetime(2026, 3, 24).date(): '26324',
        datetime.datetime(2026, 3, 31).date(): '26MAR',
        datetime.datetime(2026, 4, 7).date(): '26407',
        datetime.datetime(2026, 4, 14).date(): '26413',
        datetime.datetime(2026, 4, 21).date(): '26421',
        datetime.datetime(2026, 4, 28).date(): '26APR',
        datetime.datetime(2026, 5, 5).date(): '26505',
        datetime.datetime(2026, 5, 12).date(): '26512',
        datetime.datetime(2026, 5, 19).date(): '26519',
        datetime.datetime(2026, 5, 26).date(): '26MAY',
        datetime.datetime(2026, 6, 2).date(): '26602',
        datetime.datetime(2026, 6, 9).date(): '26609',
        datetime.datetime(2026, 6, 16).date(): '26616',
        datetime.datetime(2026, 6, 23).date(): '26623',
        datetime.datetime(2026, 6, 30).date(): '26JUN',
        datetime.datetime(2026, 7, 7).date(): '26707',
        datetime.datetime(2026, 7, 14).date(): '26714',
        datetime.datetime(2026, 7, 21).date(): '26721',
        datetime.datetime(2026, 7, 28).date(): '26JUL',
        datetime.datetime(2026, 8, 4).date(): '26804',
        datetime.datetime(2026, 8, 11).date(): '26811',
        datetime.datetime(2026, 8, 18).date(): '26818',
        datetime.datetime(2026, 8, 25).date(): '26AUG',
        datetime.datetime(2026, 9, 1).date(): '26901',
        datetime.datetime(2026, 9, 8).date(): '26908',
        datetime.datetime(2026, 9, 15).date(): '26915',
        datetime.datetime(2026, 9, 22).date(): '26922',
        datetime.datetime(2026, 9, 29).date(): '26SEP',
        datetime.datetime(2026, 10, 6).date(): '26O06',
        datetime.datetime(2026, 10, 13).date(): '26O13',
        datetime.datetime(2026, 10, 20).date(): '26O19',
        datetime.datetime(2026, 10, 27).date(): '26OCT',
        datetime.datetime(2026, 11, 3).date(): '26N03',
        datetime.datetime(2026, 11, 10).date(): '26N09',
        datetime.datetime(2026, 11, 17).date(): '26N17',
        datetime.datetime(2026, 11, 24).date(): '26NOV',
        datetime.datetime(2026, 12, 1).date(): '26D01',
        datetime.datetime(2026, 12, 8).date(): '26D08',
        datetime.datetime(2026, 12, 15).date(): '26D15',
        datetime.datetime(2026, 12, 22).date(): '26D22',
        datetime.datetime(2026, 12, 29).date(): '26DEC',
    }

    today = datetime.datetime.now().date()
    found_first = False
    for date_key, value in nifty_expiry.items():
        if today <= date_key:
            if found_first:
                return value
            found_first = True
    return None


def getBankNiftyExpiryDate():
    """Get nearest Bank Nifty expiry date (weekly)"""
    banknifty_expiry = {
        datetime.datetime(2026, 1, 7).date(): '26107',
        datetime.datetime(2026, 1, 14).date(): '26114',
        datetime.datetime(2026, 1, 21).date(): '26121',
        datetime.datetime(2026, 1, 27).date(): '26JAN',
        datetime.datetime(2026, 2, 4).date(): '26204',
        datetime.datetime(2026, 2, 11).date(): '26211',
        datetime.datetime(2026, 2, 18).date(): '26218',
        datetime.datetime(2026, 2, 24).date(): '26FEB',
        datetime.datetime(2026, 3, 4).date(): '26304',
        datetime.datetime(2026, 3, 11).date(): '26311',
        datetime.datetime(2026, 3, 18).date(): '26318',
        datetime.datetime(2026, 3, 25).date(): '26325',
        datetime.datetime(2026, 3, 31).date(): '26MAR',
        datetime.datetime(2026, 4, 1).date(): '26401',
        datetime.datetime(2026, 4, 8).date(): '26408',
        datetime.datetime(2026, 4, 15).date(): '26415',
        datetime.datetime(2026, 4, 22).date(): '26422',
        datetime.datetime(2026, 4, 28).date(): '26APR',
        datetime.datetime(2026, 5, 6).date(): '26506',
        datetime.datetime(2026, 5, 13).date(): '26513',
        datetime.datetime(2026, 5, 20).date(): '26520',
        datetime.datetime(2026, 5, 26).date(): '26MAY',
        datetime.datetime(2026, 6, 3).date(): '26603',
        datetime.datetime(2026, 6, 10).date(): '26610',
        datetime.datetime(2026, 6, 17).date(): '26617',
        datetime.datetime(2026, 6, 24).date(): '26624',
        datetime.datetime(2026, 6, 30).date(): '26JUN',
    }

    today = datetime.datetime.now().date()
    for date_key, value in banknifty_expiry.items():
        if today <= date_key:
            return value
    return None


def getFinNiftyExpiryDate():
    """Get nearest Fin Nifty expiry date (weekly)"""
    finnifty_expiry = {
        datetime.datetime(2026, 1, 6).date(): '26106',
        datetime.datetime(2026, 1, 13).date(): '26113',
        datetime.datetime(2026, 1, 20).date(): '26120',
        datetime.datetime(2026, 1, 27).date(): '26JAN',
        datetime.datetime(2026, 2, 3).date(): '26203',
        datetime.datetime(2026, 2, 10).date(): '26210',
        datetime.datetime(2026, 2, 17).date(): '26217',
        datetime.datetime(2026, 2, 24).date(): '26FEB',
        datetime.datetime(2026, 3, 3).date(): '26302',
        datetime.datetime(2026, 3, 10).date(): '26310',
        datetime.datetime(2026, 3, 17).date(): '26317',
        datetime.datetime(2026, 3, 24).date(): '26324',
        datetime.datetime(2026, 3, 31).date(): '26MAR',
        datetime.datetime(2026, 4, 7).date(): '26407',
        datetime.datetime(2026, 4, 14).date(): '26413',
        datetime.datetime(2026, 4, 21).date(): '26421',
        datetime.datetime(2026, 4, 28).date(): '26APR',
    }

    today = datetime.datetime.now().date()
    for date_key, value in finnifty_expiry.items():
        if today <= date_key:
            return value
    return None


def getSensexExpiryDate():
    """Get nearest Sensex expiry date (weekly)"""
    sensex_expiry = {
        datetime.datetime(2026, 1, 1).date(): '26101',
        datetime.datetime(2026, 1, 8).date(): '26108',
        datetime.datetime(2026, 1, 15).date(): '26115',
        datetime.datetime(2026, 1, 22).date(): '26122',
        datetime.datetime(2026, 1, 29).date(): '26JAN',
        datetime.datetime(2026, 2, 5).date(): '26205',
        datetime.datetime(2026, 2, 12).date(): '26212',
        datetime.datetime(2026, 2, 19).date(): '26219',
        datetime.datetime(2026, 2, 26).date(): '26FEB',
        datetime.datetime(2026, 3, 5).date(): '26305',
        datetime.datetime(2026, 3, 12).date(): '26312',
        datetime.datetime(2026, 3, 19).date(): '26319',
        datetime.datetime(2026, 3, 26).date(): '26326',
        datetime.datetime(2026, 3, 31).date(): '26MAR',
    }

    today = datetime.datetime.now().date()
    for date_key, value in sensex_expiry.items():
        if today <= date_key:
            return value
    return None

def getIndexSpot(stock):
    if stock == "BANKNIFTY":
        name = "Nifty Bank"
    elif stock == "NIFTY":
        name = "Nifty 50"
    elif stock == "FINNIFTY":
        name = "FINNIFTY"

    return name

def getOptionFormat(stock, intExpiry, strike, ce_pe):
    return str(stock) + str(intExpiry)+str(strike)+str(ce_pe)