import time
import json
import traceback
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))

import helper_rmoney as helper

# Import XTS SDK
try:
    from Connect import XTSConnect
    print("✅ Using XTS SDK from Connect.py")
except ImportError:
    print("❌ XTS SDK not found. Please ensure Connect.py is in your project directory.")
    sys.exit(1)

##############################################
# ⭐ CONFIGURATION - ADD YOUR SYMBOLS HERE ⭐
##############################################

# Equities to track
EQUITIES = [
    "SBIN",
    "RELIANCE",
    "TCS",
]

# Index Futures to track (automatically finds current month)
INDEX_FUTURES = [
    "NIFTY",
    "BANKNIFTY",
    "FINNIFTY",
]

# Commodity Futures to track
COMMODITY_FUTURES = [
    {"symbol": "GOLD", "segment": 51},
    {"symbol": "SILVER", "segment": 51},
]

# Option strikes configuration
NIFTY_STRIKES_RANGE = (-6, 7)      # -3 to +3 = 7 strikes = 14 options
BANKNIFTY_STRIKES_RANGE = (-1, 1)  # -2 to +2 = 5 strikes = 10 options
FINNIFTY_STRIKES_RANGE = (-1, 1)   # -2 to +2 = 5 strikes = 10 options

##############################################
# API CREDENTIALS
##############################################

INTERACTIVE_API_KEY = os.environ["RMONEY_QUOTES2_INTERACTIVE_API_KEY"]
INTERACTIVE_SECRET = os.environ["RMONEY_QUOTES2_INTERACTIVE_SECRET"]
MARKETDATA_API_KEY = os.environ["RMONEY_QUOTES2_MARKETDATA_API_KEY"]
MARKETDATA_SECRET = os.environ["RMONEY_QUOTES2_MARKETDATA_SECRET"]

##############################################
# EXCHANGE SEGMENT MAPPINGS
##############################################

EXCHANGE_SEGMENTS = {
    "NSECM": 1,   # NSE Cash
    "NSEFO": 2,   # NSE F&O
    "BSECM": 11,  # BSE Cash
    "BSEFO": 12,  # BSE F&O
    "MCXFO": 51,  # MCX F&O
}

INDEX_IDS = {
    "NIFTY": {"segment": 1, "id": 26000, "name": "Nifty 50"},
    "BANKNIFTY": {"segment": 1, "id": 26001, "name": "Nifty Bank"},
    "FINNIFTY": {"segment": 1, "id": 26034, "name": "FINNIFTY"},
}

##############################################
# FEED MONITORING VARIABLES
##############################################
last_api_success_time = 0
last_json_update_time = 0
last_prices_snapshot = {}
STALE_API_AFTER = 20
STALE_JSON_AFTER = 25

##############################################
# INITIALIZE XTS CONNECTIONS
##############################################

def initialize_xts():
    """Initialize XTS connections"""
    global xt_md

    print("\n" + "="*60)
    print("Initializing XTS Market Data API...")
    print("="*60)

    if not os.path.exists("rmoney_tokens.json"):
        print("❌ rmoney_tokens.json not found. Please run rmoney_login_v2.py first.")
        sys.exit(1)

    with open("rmoney_tokens.json", "r") as f:
        tokens = json.load(f)

    xt_md = XTSConnect(
        apiKey=MARKETDATA_API_KEY,
        secretKey=MARKETDATA_SECRET,
        source="WebAPI"
    )

    xt_md.token = tokens["marketdata_token"]
    if hasattr(xt_md, "sessionToken"):
        xt_md.sessionToken = tokens["marketdata_token"]

    print("✅ XTS Market Data API initialized\n")
    return xt_md

##############################################
# SUPER ROBUST GET QUOTES FUNCTION
##############################################

def safe_get_quotes(instruments, retry_delay=5):
    """Fetch quotes with automatic retry on failure"""
    global xt_md, last_api_success_time

    while True:
        try:
            response = xt_md.get_quote(
                Instruments=instruments,
                xtsMessageCode=1502,
                publishFormat="JSON"
            )

            if not isinstance(response, dict):
                raise ValueError("Non-JSON response from XTS")

            if response.get("type") != "success":
                raise ValueError(f"XTS API Error: {response.get('description')}")

            if "result" not in response:
                raise ValueError("Missing 'result' in XTS response")

            quotes = response["result"].get("listQuotes", [])
            if not quotes:
                raise ValueError("No quotes in response")

            last_api_success_time = time.time()
            return response

        except Exception as e:
            print(f"\n❌ ERROR fetching quotes: {e}")
            try:
                print("🔄 Reinitializing XTS client...")
                initialize_xts()
            except:
                pass

            print(f"⏳ Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)

##############################################
# AUTO RESTART LOGIC
##############################################

def should_restart_feed(current_prices):
    """Check if feed should be restarted"""
    global last_json_update_time, last_prices_snapshot

    now = time.time()

    if last_api_success_time and (now - last_api_success_time > STALE_API_AFTER):
        print(f"⚠️ RESTART TRIGGERED – NO API SUCCESS FOR {now - last_api_success_time:.0f}s")
        return True

    if last_json_update_time and (now - last_json_update_time > STALE_JSON_AFTER):
        print(f"⚠️ RESTART TRIGGERED – JSON NOT UPDATED FOR {now - last_json_update_time:.0f}s")
        return True

    last_prices_snapshot = current_prices.copy()
    return False

def full_restart():
    """Full restart of the script"""
    print("🔄 FULL API RESTART...")
    os.execv(sys.executable, ['python3'] + sys.argv)

##############################################
# EXPIRY DATES
##############################################

intExpiry = helper.getNiftyExpiryDate()
intExpiry_BN = helper.getBankNiftyExpiryDate()
intExpiry_Fin = helper.getFinNiftyExpiryDate()

print(f"📅 Expiry Dates:")
print(f"   Nifty: {intExpiry}")
print(f"   Bank Nifty: {intExpiry_BN}")
print(f"   Fin Nifty: {intExpiry_Fin}\n")

##############################################
# BUILD INSTRUMENT LIST
##############################################

def build_instrument_list():
    """Build list of instruments to fetch quotes for"""
    instrumentList = []

    xt_md_temp = initialize_xts()

    print("Building instrument list...\n")

    # ========== NIFTY OPTIONS ==========
    print("📊 NIFTY Options...")
    nifty_instr = [{"exchangeSegment": 1, "exchangeInstrumentID": 26000}]
    nifty_quote = safe_get_quotes(nifty_instr)
    nifty_ltp = json.loads(nifty_quote["result"]["listQuotes"][0])["Touchline"]["LastTradedPrice"]
    print(f"   Nifty LTP: {nifty_ltp}")

    strikeList = []
    for i in range(*NIFTY_STRIKES_RANGE):
        strike = (int(nifty_ltp / 50) + i) * 50
        strikeList.append(strike)

    instrumentList.append({"exchangeSegment": 1, "exchangeInstrumentID": 26000, "name": "Nifty 50"})

    for strike in strikeList:
        symbol = f"NIFTY{intExpiry}{strike}CE"
        instrumentList.append({"exchangeSegment": 2, "strike": strike, "expiry": intExpiry, "type": "CE", "name": symbol})
        symbol = f"NIFTY{intExpiry}{strike}PE"
        instrumentList.append({"exchangeSegment": 2, "strike": strike, "expiry": intExpiry, "type": "PE", "name": symbol})

    print(f"   Added {len(strikeList)*2} Nifty options")

    # ========== BANK NIFTY OPTIONS ==========
    print("\n📊 BANK NIFTY Options...")
    bn_instr = [{"exchangeSegment": 1, "exchangeInstrumentID": 26001}]
    bn_quote = safe_get_quotes(bn_instr)
    bn_ltp = json.loads(bn_quote["result"]["listQuotes"][0])["Touchline"]["LastTradedPrice"]
    print(f"   Bank Nifty LTP: {bn_ltp}")

    strikeList = []
    for i in range(*BANKNIFTY_STRIKES_RANGE):
        strike = (int(bn_ltp / 100) + i) * 100
        strikeList.append(strike)

    instrumentList.append({"exchangeSegment": 1, "exchangeInstrumentID": 26001, "name": "Nifty Bank"})

    for strike in strikeList:
        symbol = f"BANKNIFTY{intExpiry_BN}{strike}CE"
        instrumentList.append({"exchangeSegment": 2, "strike": strike, "expiry": intExpiry_BN, "type": "CE", "name": symbol})
        symbol = f"BANKNIFTY{intExpiry_BN}{strike}PE"
        instrumentList.append({"exchangeSegment": 2, "strike": strike, "expiry": intExpiry_BN, "type": "PE", "name": symbol})

    print(f"   Added {len(strikeList)*2} Bank Nifty options")

    # ========== FIN NIFTY OPTIONS ==========
    print("\n📊 FIN NIFTY Options...")
    fn_instr = [{"exchangeSegment": 1, "exchangeInstrumentID": 26034}]
    fn_quote = safe_get_quotes(fn_instr)
    fn_ltp = json.loads(fn_quote["result"]["listQuotes"][0])["Touchline"]["LastTradedPrice"]
    print(f"   Fin Nifty LTP: {fn_ltp}")

    strikeList = []
    for i in range(*FINNIFTY_STRIKES_RANGE):
        strike = (int(fn_ltp / 100) + i) * 100
        strikeList.append(strike)

    instrumentList.append({"exchangeSegment": 1, "exchangeInstrumentID": 26034, "name": "FINNIFTY"})

    for strike in strikeList:
        symbol = f"FINNIFTY{intExpiry_Fin}{strike}CE"
        instrumentList.append({"exchangeSegment": 2, "strike": strike, "expiry": intExpiry_Fin, "type": "CE", "name": symbol})
        symbol = f"FINNIFTY{intExpiry_Fin}{strike}PE"
        instrumentList.append({"exchangeSegment": 2, "strike": strike, "expiry": intExpiry_Fin, "type": "PE", "name": symbol})

    print(f"   Added {len(strikeList)*2} Fin Nifty options")

    # ========== EQUITIES ==========
    print("\n📊 Equities...")
    for equity in EQUITIES:
        instrumentList.append({"exchangeSegment": 1, "search": equity, "name": f"{equity}-EQ"})
    print(f"   Added {len(EQUITIES)} equities")

    # ========== INDEX FUTURES ==========
    print("\n📊 Index Futures...")
    for future in INDEX_FUTURES:
        instrumentList.append({"exchangeSegment": 2, "search": f"{future}26JAN", "name": f"{future}26JANFUT", "future": future})
    print(f"   Added {len(INDEX_FUTURES)} index futures")

    # ========== COMMODITY FUTURES ==========
    print("\n📊 Commodity Futures...")
    for future in COMMODITY_FUTURES:
        instrumentList.append({"exchangeSegment": future["segment"], "search": future["symbol"], "name": f"{future['symbol']}27JAN26FUT"})
    print(f"   Added {len(COMMODITY_FUTURES)} commodity futures")

    total_instruments = len(instrumentList)
    print(f"\n✅ Total instruments: {total_instruments}")
    if total_instruments > 50:
        print(f"   ❌ WARNING: {total_instruments} > 50 - will need batching!")
    else:
        print(f"   ✅ Under limit: {total_instruments} < 50")
    print()

    return instrumentList

##############################################
# SEARCH FUNCTIONS
##############################################

SEARCH_CACHE = {}

def search_and_cache_underlying(underlying, segment=2):
    """Search for an underlying and cache all results"""
    cache_key = f"{underlying}_{segment}"

    if cache_key in SEARCH_CACHE:
        return SEARCH_CACHE[cache_key]

    print(f"   🔍 Searching for {underlying} instruments...")

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
        print(f"   ✅ Cached {len(items)} {underlying} instruments")
        return items

    except Exception as e:
        print(f"   ❌ Search failed for {underlying}: {e}")
        SEARCH_CACHE[cache_key] = []
        return []

def find_option_eid(underlying, expiry, strike, option_type, segment=2):
    """Find option instrument ID from cache - WITH EXPIRY MATCHING"""
    from datetime import datetime

    cache_key = f"{underlying}_{segment}"
    items = SEARCH_CACHE.get(cache_key, [])

    # Convert expiry string to date
    target_date = None

    try:
        if len(expiry) == 5:
            year = 2000 + int(expiry[:2])

            # Format 1: YYMDD (26106 = 2026-01-06)
            if expiry[2:].isdigit():
                month = int(expiry[2:3])  # Single digit month
                day = int(expiry[3:5])
                target_date = datetime(year, month, day).date()

            # Format 2: YYODD (26O06 = 2026-10-06)
            elif expiry[2] == 'O':
                month = 10  # October
                day = int(expiry[3:5])
                target_date = datetime(year, month, day).date()

            # Format 3: YYNDD (26N03 = 2026-11-03)
            elif expiry[2] == 'N':
                month = 11  # November
                day = int(expiry[3:5])
                target_date = datetime(year, month, day).date()

            # Format 4: YYDDD (26D01 = 2026-12-01)
            elif expiry[2] == 'D':
                month = 12  # December
                day = int(expiry[3:5])
                target_date = datetime(year, month, day).date()

            # Format 5: YYMON (26JAN = 2026-01-27 monthly expiry)
            elif expiry[2:].isalpha():
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
                target_date = monthly_expiries.get(expiry)

    except Exception:
        pass

    if not target_date:
        print(f"❌ Could not parse expiry: {expiry}")
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

        # ✅ Check expiry date
        expiry_str = item.get("ContractExpiration") or item.get("ExpiryDate") or ""
        try:
            if 'T' in str(expiry_str):
                item_date = datetime.fromisoformat(str(expiry_str).split('T')[0]).date()
            else:
                item_date = datetime.fromisoformat(str(expiry_str)).date()

            if item_date != target_date:
                continue
        except:
            continue

        return item.get("ExchangeInstrumentID") or item.get("exchangeInstrumentID")

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

def search_instrument(symbol, segment=1):
    """Search for a single instrument (for equity/futures)"""
    try:
        response = xt_md.search_by_scriptname(searchString=symbol)

        if isinstance(response, list):
            items = response
        elif isinstance(response, dict) and response.get("type") == "success":
            items = response.get("result", [])
            if isinstance(items, dict):
                items = items.get("instruments", []) or items.get("values", []) or []
        else:
            return None

        for item in items:
            if item.get("ExchangeSegment") == segment:
                if segment == 1 and item.get("Series") != "EQ":
                    continue
                return item.get("ExchangeInstrumentID")

        return None
    except:
        return None

##############################################
# MAIN LOOP
##############################################

def run_quotes_loop():
    """Main loop to fetch and update quotes"""
    global last_json_update_time

    print("\n" + "="*60)
    print("🚀 Starting RMoney Quotes Loop")
    print("="*60 + "\n")

    instrument_list = build_instrument_list()

    print("🔍 Caching option data...")
    search_and_cache_underlying("NIFTY", segment=2)
    search_and_cache_underlying("BANKNIFTY", segment=2)
    search_and_cache_underlying("FINNIFTY", segment=2)
    print()

    print("🔍 Resolving instrument IDs...")
    resolved_instruments = []
    eid_to_name = {}

    for item in instrument_list:
        if "exchangeInstrumentID" in item:
            eid = item["exchangeInstrumentID"]
            resolved_instruments.append({
                "exchangeSegment": item["exchangeSegment"],
                "exchangeInstrumentID": eid
            })
            eid_to_name[eid] = item.get("name", "Unknown")

        elif "search" in item:
            if item["exchangeSegment"] == 2 and "future" in item:
                eid = find_future_eid(item["future"], segment=2)
            else:
                eid = search_instrument(item["search"], item["exchangeSegment"])

            if eid:
                resolved_instruments.append({
                    "exchangeSegment": item["exchangeSegment"],
                    "exchangeInstrumentID": eid
                })
                eid_to_name[eid] = item.get("name", item["search"])

        elif "strike" in item:
            underlying = "NIFTY" if "NIFTY" in item["name"] and "BANK" not in item["name"] and "FIN" not in item["name"] else \
                "BANKNIFTY" if "BANKNIFTY" in item["name"] else "FINNIFTY"

            eid = find_option_eid(underlying, item['expiry'], item['strike'], item['type'], segment=2)

            if eid:
                resolved_instruments.append({
                    "exchangeSegment": 2,
                    "exchangeInstrumentID": eid
                })
                eid_to_name[eid] = item["name"]

    print(f"✅ Resolved {len(resolved_instruments)} instruments\n")
    print("!! Started rmoney_quotes_v2.py with AUTO-RECOVERY + MONITORING !!\n")

    while True:
        try:
            all_quotes = safe_get_quotes(resolved_instruments)

            result = {}
            for quote_str in all_quotes["result"].get("listQuotes", []):
                try:
                    quote = json.loads(quote_str) if isinstance(quote_str, str) else quote_str
                    eid = quote.get("ExchangeInstrumentID")
                    ltp = quote.get("Touchline", {}).get("LastTradedPrice")

                    name = eid_to_name.get(eid)

                    if name and ltp is not None:
                        result[name] = ltp
                except:
                    continue

            # Print results
            print(f"\r[{time.strftime('%H:%M:%S')}] Updated {len(result)} quotes", end="", flush=True)
            print(result)

            try:
                with open("rmoney_data.json", "w") as f:
                    json.dump(result, f)
                last_json_update_time = time.time()
            except:
                pass

            if should_restart_feed(result):
                full_restart()

            time.sleep(5)

        except KeyboardInterrupt:
            print("\n\n⏹️ Stopped by user")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            time.sleep(5)
            continue

##############################################
# ENTRY POINT
##############################################

if __name__ == "__main__":
    xt_md = initialize_xts()
    run_quotes_loop()