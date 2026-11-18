import requests
import json
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import time
from datetime import datetime

##############################################
# XTS/RMoney API Configuration
##############################################

# Interactive API (for order placement)
INTERACTIVE_URL = "https://xts.rmoneyindia.co.in:3000/interactive"
INTERACTIVE_API_KEY = os.environ["RMONEY_INTERACTIVE_API_KEY"]
INTERACTIVE_SECRET = os.environ["RMONEY_INTERACTIVE_SECRET"]

# Market Data API (for quotes)
MARKETDATA_URL = "https://xts.rmoneyindia.co.in:3000/apimarketdata"
MARKETDATA_API_KEY = os.environ["RMONEY_MARKETDATA_API_KEY"]
MARKETDATA_SECRET = os.environ["RMONEY_MARKETDATA_SECRET"]

##############################################
# Login Functions
##############################################

def login_interactive():
    """Login to Interactive API and return token data"""
    try:
        url = f"{INTERACTIVE_URL}/user/session"

        headers = {
            'Content-Type': 'application/json',
            'Authorization': INTERACTIVE_API_KEY
        }

        payload = {
            "appKey": INTERACTIVE_API_KEY,
            "secretKey": INTERACTIVE_SECRET,
            "source": "WEBAPI"
        }

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            result = response.json()
            if result.get('type') == 'success':
                print("✅ Interactive API Login Successful!")
                return {
                    'token': result['result']['token'],
                    'userID': result['result']['userID'],
                    'url': INTERACTIVE_URL
                }
            else:
                print(f"❌ Interactive Login Failed: {result.get('description')}")
                return None
        else:
            print(f"❌ Interactive Login Failed with status {response.status_code}")
            return None

    except Exception as e:
        print(f"❌ Interactive Login Error: {str(e)}")
        return None


def login_marketdata():
    """Login to Market Data API and return token data"""
    try:
        url = f"{MARKETDATA_URL}/auth/login"

        payload = json.dumps({
            "appKey": MARKETDATA_API_KEY,
            "secretKey": MARKETDATA_SECRET,
            "source": "WebAPI"
        })

        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.post(url, headers=headers, data=payload)

        if response.status_code == 200:
            result = response.json()
            if result.get('type') == 'success':
                print("✅ Market Data API Login Successful!")
                return {
                    'token': result['result']['token'],
                    'userID': result['result'].get('userID', ''),
                    'url': "https://developers.symphonyfintech.in/apimarketdata"
                }
            else:
                print(f"❌ Market Data Login Failed: {result.get('description')}")
                return None
        else:
            print(f"❌ Market Data Login Failed: Status {response.status_code}")
            print(f"Response: {response.text}")
            return None

    except Exception as e:
        print(f"❌ Market Data Login Error: {str(e)}")
        return None


def get_all_tokens():
    """Main function - login and save tokens"""
    print("\n" + "="*50)
    print("RMoney/XTS Login")
    print("="*50 + "\n")

    # Get tokens
    interactive_token = login_interactive()
    marketdata_token = login_marketdata()

    # Prepare token data
    tokens = {}

    if interactive_token:
        tokens['interactive_token'] = interactive_token['token']
        tokens['interactive_url'] = interactive_token['url']
        tokens['userID'] = interactive_token['userID']

    if marketdata_token:
        tokens['marketdata_token'] = marketdata_token['token']
        tokens['marketdata_url'] = marketdata_token['url']

    # Save to file
    if tokens:
        tokens['login_time'] = datetime.now().isoformat()
        tokens['timestamp']  = time.time()   # v2.8: Unix seconds for bot token age check

        with open('rmoney_tokens.json', 'w') as f:
            json.dump(tokens, f, indent=2)

        print(f"\n✅ Tokens saved to rmoney_tokens.json")
        print(f"Keys saved: {list(tokens.keys())}")
        return tokens
    else:
        print("\n❌ No tokens to save - login failed")
        return None


def load_tokens():
    """Load tokens from file - use this in other scripts"""
    try:
        with open('rmoney_tokens.json', 'r') as f:
            return json.load(f)
    except:
        print("❌ Could not load rmoney_tokens.json")
        return None


if __name__ == "__main__":
    get_all_tokens()