"""fetch_index_1min_fyers_v2.py -- download 1-min index bars from Fyers for any date range.

Put this file in the SAME folder as your Fyers bot (it needs fyers_client_id.txt and a
fresh fyers_access_token.txt -- log in as you do every morning first). Read-only: it only
calls fyers.history(), no orders.

Examples:
    python fetch_index_1min_fyers_v2.py NIFTY  2024-12-20 2025-12-31
        -> nifty_spot_1min_2024-12-20_2025-12-31.csv and india_vix_1min_2024-12-20_2025-12-31.csv
    python fetch_index_1min_fyers_v2.py SENSEX 2024-12-20 2026-10-31
        -> sensex_spot_1min_2024-12-20_2026-10-31.csv

No arguments (e.g. run from PyCharm): uses the DEFAULT_... values below.
Start a few trading days BEFORE the first test day (the bot looks back at earlier days).
Fyers allows about 100 days of 1-min data per request, so it asks in 30-day pieces.
"""
import sys, time, csv
from datetime import date, datetime, timedelta
from fyers_apiv3 import fyersModel

import os
# ---- EDIT HERE if you run it from PyCharm / an IDE with no arguments ----------
DEFAULT_WHICH, DEFAULT_START, DEFAULT_END = "NIFTY", "2024-12-20", "2025-12-31"
#   for Sensex change to:  "SENSEX", "2024-12-20", "2026-10-31"
# -------------------------------------------------------------------------------
os.chdir(os.path.dirname(os.path.abspath(__file__)))   # token files + output next to this script
args = sys.argv[1:] or [DEFAULT_WHICH, DEFAULT_START, DEFAULT_END]
if len(args) != 3 or args[0].upper() not in ("NIFTY", "SENSEX"):
    sys.exit("usage: python fetch_index_1min_fyers_v2.py NIFTY|SENSEX YYYY-MM-DD YYYY-MM-DD")
WHICH = args[0].upper()
START, END = date.fromisoformat(args[1]), date.fromisoformat(args[2])
print(f"Fetching {WHICH} 1-min bars {START} .. {END} into {os.getcwd()}")
tag = f"{START.isoformat()}_{END.isoformat()}"
if WHICH == "NIFTY":
    SYMBOLS = {"NSE:NIFTY50-INDEX": f"nifty_spot_1min_{tag}.csv", "NSE:INDIAVIX-INDEX": f"india_vix_1min_{tag}.csv"}
else:
    SYMBOLS = {"BSE:SENSEX-INDEX": f"sensex_spot_1min_{tag}.csv"}

APP_ID = open("fyers_client_id.txt", encoding="utf-8").read().strip()
TOKEN = open("fyers_access_token.txt", encoding="utf-8").read().strip()
fyers = fyersModel.FyersModel(token=TOKEN, is_async=False, client_id=APP_ID, log_path="")

for sym, out in SYMBOLS.items():
    seen, n = set(), 0
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "time", "open", "high", "low", "close", "volume"])
        a = START
        while a <= END:
            b = min(a + timedelta(days=29), END)
            r = fyers.history(data={"symbol": sym, "resolution": "1", "date_format": "1",
                                    "range_from": a.isoformat(), "range_to": b.isoformat(), "cont_flag": "1"})
            candles = (r or {}).get("candles") or []
            if not candles:
                print(f"  {sym} {a}..{b}: no data ({(r or {}).get('message', r)})")
            for c in candles:
                t = datetime(1970, 1, 1) + timedelta(seconds=int(c[0]), hours=5, minutes=30)   # UTC -> IST
                if t in seen:
                    continue
                seen.add(t)
                w.writerow([t.strftime("%Y-%m-%d"), t.strftime("%H:%M"), c[1], c[2], c[3], c[4], c[5] if len(c) > 5 else 0])
                n += 1
            print(f"  {sym} {a}..{b}: {len(candles)} bars")
            a = b + timedelta(days=1)
            time.sleep(0.5)
    print(f"{sym}: {n:,} bars -> {out}")
print("Done. Attach the CSV file(s) to the chat.")
