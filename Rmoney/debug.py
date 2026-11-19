import os
import json

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from helper_rmoney import RMoneyXTSHelper

def setup_helper():
    token_file = "rmoney_tokens.json"
    with open(token_file, "r") as f:
        tokens = json.load(f)
    return RMoneyXTSHelper(tokens)

def find_index_instruments(helper):
    """Find correct instrument IDs for indices"""
    
    print("\n" + "="*60)
    print("🔍 SEARCHING FOR INDEX INSTRUMENTS")
    print("="*60)
    
    # Method 1: Try get_index_list API
    print("\n📋 Method 1: Using get_index_list API...")
    try:
        for seg_name, seg_id in [("NSECM", 1), ("BSECM", 11)]:
            print(f"\n  Segment: {seg_name} ({seg_id})")
            response = helper.xt_md.get_index_list(seg_id)
            
            # Save response
            with open(f"debug_index_list_{seg_name}.json", "w") as f:
                json.dump(response, f, indent=2, default=str)
            print(f"  Saved to debug_index_list_{seg_name}.json")
            
            if response and response.get("type") == "success":
                result = response.get("result", {})
                indices = result.get("indexList", []) or result.get("values", []) or result
                
                if isinstance(indices, list):
                    print(f"  Found {len(indices)} indices")
                    for idx in indices[:20]:  # Show first 20
                        name = idx.get("Name") or idx.get("IndexName") or idx.get("DisplayName") or "?"
                        eid = idx.get("ExchangeInstrumentID") or idx.get("exchangeInstrumentID") or "?"
                        print(f"    - {name}: ID={eid}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Method 2: Search for specific indices
    print("\n📋 Method 2: Searching for specific indices...")
    search_terms = ["NIFTY 50", "NIFTY BANK", "NIFTY", "BANKNIFTY", "FINNIFTY", "SENSEX"]
    
    for term in search_terms:
        print(f"\n  Searching: '{term}'")
        try:
            # Search in NSECM
            response = helper.xt_md.search_by_scriptname(searchString=term)
            
            # Save response
            safe_name = term.replace(" ", "_")
            with open(f"debug_search_{safe_name}.json", "w") as f:
                json.dump(response, f, indent=2, default=str)
            
            if isinstance(response, list):
                items = response
            elif isinstance(response, dict) and response.get("type") == "success":
                items = response.get("result", [])
                if isinstance(items, dict):
                    items = items.get("instruments", []) or items.get("values", []) or []
            else:
                items = []
            
            # Filter for indices (NSECM segment, Series = "SPOT" or "INDEX")
            for item in items:
                seg = item.get("ExchangeSegment")
                series = item.get("Series", "")
                name = item.get("Name") or item.get("DisplayName") or item.get("TradingSymbol") or ""
                eid = item.get("ExchangeInstrumentID")
                is_index = item.get("IsIndex")
                
                # Show relevant entries
                if seg in (1, 11) and (series in ("SPOT", "INDEX", "") or is_index):
                    print(f"    ✅ Segment={seg}, Name={name}, Series={series}, ID={eid}, IsIndex={is_index}")
                    
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    # Method 3: Try known instrument IDs
    print("\n📋 Method 3: Testing known instrument IDs...")
    test_ids = [
        {"segment": 1, "id": 26000, "name": "NIFTY 50 (26000)"},
        {"segment": 1, "id": 26001, "name": "NIFTY BANK (26001)"},
        {"segment": 1, "id": 26034, "name": "FINNIFTY (26034)"},
        {"segment": 1, "id": 26037, "name": "NIFTY 50 alt (26037)"},
        {"segment": 1, "id": 26009, "name": "NIFTY BANK alt (26009)"},
        {"segment": 1, "id": 26074, "name": "MIDCAP (26074)"},
        {"segment": 11, "id": 1, "name": "SENSEX (1)"},
        {"segment": 11, "id": 999901, "name": "SENSEX alt (999901)"},
    ]
    
    for test in test_ids:
        try:
            instruments = [{"exchangeSegment": test["segment"], "exchangeInstrumentID": test["id"]}]
            response = helper.xt_md.get_quote(
                Instruments=instruments,
                xtsMessageCode=1502,
                publishFormat="JSON"
            )
            
            if response and response.get("type") == "success":
                quotes = response["result"].get("listQuotes", [])
                if quotes:
                    q = quotes[0]
                    if isinstance(q, str):
                        q = json.loads(q)
                    ltp = q.get("Touchline", {}).get("LastTradedPrice")
                    actual_name = q.get("Name") or q.get("TradingSymbol") or "?"
                    print(f"  ✅ {test['name']}: LTP={ltp}, ActualName={actual_name}")
                else:
                    print(f"  ❌ {test['name']}: No quotes returned")
            else:
                print(f"  ❌ {test['name']}: Failed - {response}")
        except Exception as e:
            print(f"  ❌ {test['name']}: Error - {e}")
    
    # Method 4: Get master data for indices
    print("\n📋 Method 4: Checking master instruments...")
    try:
        # Try to get master for NSECM
        if hasattr(helper.xt_md, 'get_master'):
            response = helper.xt_md.get_master(exchangeSegmentList=[1])
            with open("debug_master_nsecm.json", "w") as f:
                json.dump(response, f, indent=2, default=str)
            print("  Saved master data to debug_master_nsecm.json")
    except Exception as e:
        print(f"  ❌ Error getting master: {e}")
    
    print("\n" + "="*60)
    print("✅ Debug complete! Check the debug_*.json files for details")
    print("="*60)


if __name__ == "__main__":
    helper = setup_helper()
    find_index_instruments(helper)