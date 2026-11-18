import time
from urllib import response
from fyers_apiv3.FyersWebsocket import data_ws
from fyers_apiv3 import fyersModel
from pprint import pprint
from flask import Flask, request
import threading
import json
import helper_fyers as helper
import traceback
import os
import sys

##############################################
#                   INPUT's
##############################################
app_id = open("fyers_client_id.txt", "r").read()
access_token = open("fyers_access_token.txt", "r").read()
fyers = fyersModel.FyersModel(token=access_token, is_async=False, client_id=app_id)

##############################################
# FEED MONITORING VARIABLES
##############################################
last_api_success_time = 0
last_json_update_time = 0
last_prices_snapshot = {}
STALE_API_AFTER = 20  # If API doesn't respond for 20 seconds, restart
STALE_JSON_AFTER = 25  # If JSON file not updated for 25 seconds, restart
# FROZEN_PRICE_AFTER removed - same data after market hours is normal

##############################################
# SUPER ROBUST GET QUOTES FUNCTION
##############################################
def safe_get_quotes(quotes_list, retry_delay=5):
    global fyers, last_api_success_time

    while True:
        try:
            resp = fyers.quotes(quotes_list)

            if not isinstance(resp, dict):
                raise ValueError("Non-JSON response from Fyers")

            if resp.get("s") == "error":
                raise ValueError(f"Fyers API Error: {resp.get('message')}")

            if "d" not in resp or not isinstance(resp["d"], list):
                raise ValueError("Missing/invalid 'd' in Fyers response")
            
            # If 'd' is empty or all items are malformed, that means NO data is coming - RETRY
            valid_items = [item for item in resp["d"] if isinstance(item, dict) and 'v' in item and 'lp' in item.get('v', {})]
            
            if not valid_items:
                raise ValueError("No valid data in response - likely internet/API issue")

            last_api_success_time = time.time()
            return resp

        except Exception as e:
            print("\n❌ ERROR fetching quotes:", e)
            traceback.print_exc()

            try:
                print("🔁 Reinitializing Fyers client...")
                fyers = fyersModel.FyersModel(
                    token=access_token, is_async=False, client_id=app_id
                )
            except:
                print("⚠️ Failed reinitializing Fyers client")

            print(f"⏳ Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)


##############################################
# AUTO RESTART LOGIC
##############################################
def should_restart_feed(current_prices):
    global last_json_update_time, last_prices_snapshot

    now = time.time()

    # 1) API not responding for too long
    if last_api_success_time and (now - last_api_success_time > STALE_API_AFTER):
        print(f"❗ RESTART TRIGGERED — NO API SUCCESS FOR {now - last_api_success_time:.0f}s")
        return True

    # 2) JSON file not updating (write errors)
    if last_json_update_time and (now - last_json_update_time > STALE_JSON_AFTER):
        print(f"❗ RESTART TRIGGERED — JSON NOT UPDATED FOR {now - last_json_update_time:.0f}s")
        return True

    # 3) Prices frozen - but ONLY if we have significant number of instruments
    # After market hours, same data is NORMAL and EXPECTED - so we DON'T restart
    # We only check if prices are literally stuck during market hours
    # This check is now REMOVED because same data after market close is valid
    
    # Update snapshot for future comparison
    last_prices_snapshot = current_prices.copy()
    return False


def full_restart():
    print("🔄 FULL API RESTART...")
    os.execv(sys.executable, ['python3'] + sys.argv)


##############################################
# EXPIRY SETUP
##############################################
intExpiry = helper.getNiftyExpiryDate()
intExpiry_Sensex = helper.getSensexExpiryDate()
intExpiry_BN = helper.getBankNiftyExpiryDate()
intExpiry_Fin = helper.getFinNiftyExpiryDate()
intExpiryNext = helper.getNiftyNextExpiryDate()
strikeList = []
instrumentList = []

##############################################
# INSTRUMENT GENERATION SAME AS ORIGINAL
##############################################
data = {"symbols": "NSE:NIFTY50-INDEX"}
ltp = safe_get_quotes(data)
a = ltp["d"][0]["v"]["lp"]
print(a)

for i in range(-5, 5):
    strike = (int(a / 100) + i) * 100
    strikeList.append(strike)
    strikeList.append(strike + 50)

instrumentList.append("NSE:NIFTY50-INDEX")

# Add CE
for strike in strikeList:
    ltp_option = "NSE:NIFTY" + str(intExpiry) + str(strike) + "CE"
    instrumentList.append(ltp_option)

# Add PE
for strike in strikeList:
    ltp_option = "NSE:NIFTY" + str(intExpiry) + str(strike) + "PE"
    instrumentList.append(ltp_option)

# Add CE
for strike in strikeList:
    ltp_option = "NSE:NIFTY" + str(intExpiryNext) + str(strike) + "CE"
    instrumentList.append(ltp_option)

# Add PE
for strike in strikeList:
    ltp_option = "NSE:NIFTY" + str(intExpiryNext) + str(strike) + "PE"
    instrumentList.append(ltp_option)

strikeList = []
data = {"symbols": "BSE:SENSEX-INDEX"}
ltp = safe_get_quotes(data)
a = ltp["d"][0]["v"]["lp"]

for i in range(-10, 10):
    strike = (int(a / 100) + i) * 100
    strikeList.append(strike)

instrumentList.append("BSE:SENSEX-INDEX")

# Add CE
for strike in strikeList:
    ltp_option = "BSE:SENSEX" + str(intExpiry_Sensex) + str(strike) + "CE"
    instrumentList.append(ltp_option)

# Add PE
for strike in strikeList:
    ltp_option = "BSE:SENSEX" + str(intExpiry_Sensex) + str(strike) + "PE"
    instrumentList.append(ltp_option)

strikeList = []
data = {"symbols": "NSE:NIFTYBANK-INDEX"}
ltp = safe_get_quotes(data)
a = ltp["d"][0]["v"]["lp"]

for i in range(-10, 10):
    strike = (int(a / 100) + i) * 100
    strikeList.append(strike)

instrumentList.append("NSE:NIFTYBANK-INDEX")

# Add CE
for strike in strikeList:
    ltp_option = "NSE:BANKNIFTY" + str(intExpiry_BN) + str(strike) + "CE"
    instrumentList.append(ltp_option)

# Add PE
for strike in strikeList:
    ltp_option = "NSE:BANKNIFTY" + str(intExpiry_BN) + str(strike) + "PE"
    instrumentList.append(ltp_option)

strikeList = []
data = {"symbols": "NSE:FINNIFTY-INDEX"}
ltp = safe_get_quotes(data)
a = ltp["d"][0]["v"]["lp"]
print(a)

for i in range(-5, 5):
    strike = (int(a / 100) + i) * 100
    strikeList.append(strike)
    strikeList.append(strike + 50)

instrumentList.append("NSE:FINNIFTY-INDEX")

# Add CE
for strike in strikeList:
    ltp_option = "NSE:FINNIFTY" + str(intExpiry_Fin) + str(strike) + "CE"
    instrumentList.append(ltp_option)

# Add PE
for strike in strikeList:
    ltp_option = "NSE:FINNIFTY" + str(intExpiry_Fin) + str(strike) + "PE"
    instrumentList.append(ltp_option)


instrumentList1 = [
    "NSE:NIFTY50-INDEX",
    "NSE:NIFTYBANK-INDEX",
    "NSE:FINNIFTY-INDEX",
    "NSE:SBIN-EQ",
    "NSE:NIFTY25OCTFUT",
    "MCX:GOLD25DECFUT",
]

instrumentList = instrumentList + instrumentList1

print("BELOW IS THE COMPLETE INSTRUMENT LIST")
print(instrumentList)
print("!! Started getltpDict.py with AUTO-RECOVERY + STUCK FEED DETECTION !!")

quotes_list = {"symbols": ",".join(instrumentList)}

##############################################
# MAIN LOOP WITH STUCK-FEED DETECTION
##############################################
while True:
    try:
        all_quotes = safe_get_quotes(quotes_list)
        # Filter out malformed items, just like the original code
        result = {item['n']: item['v']['lp'] for item in all_quotes['d'] if 'v' in item and 'lp' in item['v']}
        print(result)

        try:
            with open("fyers_data.json", "w") as f:
                json.dump(result, f)
            last_json_update_time = time.time()
            print("updated json at " + time.strftime("%Y-%m-%d %H:%M:%S"))
        except:
            print("❌ File Write Error")

        if should_restart_feed(result):
            full_restart()

        time.sleep(5)

    except Exception:
        traceback.print_exc()
        time.sleep(5)
        continue
