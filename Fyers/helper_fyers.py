#DISCLAIMER:
#1) This sample code is for learning purposes only.
#2) Always be very careful when dealing with codes in which you can place orders in your account.
#3) The actual results may or may not be similar to backtested results. The historical results do not guarantee any profits or losses in the future.
#4) You are responsible for any losses/profits that occur in your account in case you plan to take trades in your account.
#5) TFU and Aseem Singhal do not take any responsibility of you running these codes on your account and the corresponding profits and losses that might occur.
#6) The running of the code properly is dependent on a lot of factors such as internet, broker, what changes you have made, etc. So it is always better to keep checking the trades as technology error can come anytime.
#7) This is NOT a tip providing service/code.
#8) This is NOT a software. Its a tool that works as per the inputs given by you.
#9) Slippage is dependent on market conditions.
#10) Option trading and automatic API trading are subject to market risks

from fyers_apiv3 import fyersModel
import datetime
import time
import requests
from datetime import timedelta
from pytz import timezone
import pandas as pd
import pytz
import json

######PIVOT POINTS##########################
####################__INPUT__#####################


def getNiftyExpiryDate_old():
    nifty_expiry = {
        datetime.datetime(2025, 1, 2).date(): '25102',
        datetime.datetime(2025, 1, 9).date(): '25109',
        datetime.datetime(2025, 1, 16).date(): '25116',
        datetime.datetime(2025, 1, 23).date(): '25123',
        datetime.datetime(2025, 1, 30).date(): '25JAN',
        datetime.datetime(2025, 2, 6).date(): '25206',
        datetime.datetime(2025, 2, 13).date(): '25213',
        datetime.datetime(2025, 2, 20).date(): '25220',
        datetime.datetime(2025, 2, 27).date(): '25FEB',
        datetime.datetime(2025, 3, 6).date(): '25306',
        datetime.datetime(2025, 3, 13).date(): '25313',
        datetime.datetime(2025, 3, 20).date(): '25320',
        datetime.datetime(2025, 3, 27).date(): '25MAR',
        datetime.datetime(2025, 4, 3).date(): '25403',
        datetime.datetime(2025, 4, 10).date(): '25409',
        datetime.datetime(2025, 4, 17).date(): '25417',
        datetime.datetime(2025, 4, 24).date(): '25APR',
        datetime.datetime(2025, 4, 30).date(): '25430',
        datetime.datetime(2025, 5, 8).date(): '25508',
        datetime.datetime(2025, 5, 15).date(): '25515',
        datetime.datetime(2025, 5, 22).date(): '25522',
        datetime.datetime(2025, 5, 29).date(): '25MAY',
        datetime.datetime(2025, 6, 5).date(): '25605',
        datetime.datetime(2025, 6, 12).date(): '25612',
        datetime.datetime(2025, 6, 19).date(): '25619',
        datetime.datetime(2025, 6, 26).date(): '25JUN',
        datetime.datetime(2025, 7, 3).date(): '25703',
        datetime.datetime(2025, 7, 10).date(): '25710',
        datetime.datetime(2025, 7, 17).date(): '25717',
        datetime.datetime(2025, 7, 24).date(): '25724',
        datetime.datetime(2025, 7, 31).date(): '25JUL',
        datetime.datetime(2025, 8, 7).date(): '25807',
        datetime.datetime(2025, 8, 14).date(): '25814',
        datetime.datetime(2025, 8, 21).date(): '25821',
        datetime.datetime(2025, 8, 28).date(): '25AUG',
        datetime.datetime(2025, 9, 2).date(): '25902',
        datetime.datetime(2025, 9, 9).date(): '25909',
        datetime.datetime(2025, 9, 16).date(): '25916',
        datetime.datetime(2025, 9, 23).date(): '25923',
        datetime.datetime(2025, 9, 30).date(): '25SEP',
        datetime.datetime(2025, 10, 7).date(): '25O07',
        datetime.datetime(2025, 10, 14).date(): '25O14',
        datetime.datetime(2025, 10, 21).date(): '25O20',
        datetime.datetime(2025, 10, 28).date(): '25OCT',
        datetime.datetime(2025, 11, 4).date(): '25N04',
        datetime.datetime(2025, 11, 11).date(): '25N11',
        datetime.datetime(2025, 11, 18).date(): '25N18',
        datetime.datetime(2025, 11, 25).date(): '25NOV',
        datetime.datetime(2025, 12, 2).date(): '25D02',
        datetime.datetime(2025, 12, 9).date(): '25D09',
        datetime.datetime(2025, 12, 16).date(): '25D16',
        datetime.datetime(2025, 12, 23).date(): '25D23',
        datetime.datetime(2025, 12, 30).date(): '25DEC',
    }


    today = datetime.datetime.now().date()

    for date_key, value in nifty_expiry.items():
        if today <= date_key:
            print(value)
            return value

def getNiftyExpiryDate():
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
            print(value)
            return value

def getSensexExpiryDate_old():
    sensex_expiry = {
        datetime.datetime(2025, 9, 18).date(): '25918',
        datetime.datetime(2025, 9, 25).date(): '25SEP',
        datetime.datetime(2025, 10, 2).date(): '25O01',
        datetime.datetime(2025, 10, 9).date(): '25O09',
        datetime.datetime(2025, 10, 16).date(): '25O16',
        datetime.datetime(2025, 10, 23).date(): '25O23',
        datetime.datetime(2025, 10, 30).date(): '25OCT',
        datetime.datetime(2025, 11, 6).date(): '25N06',
        datetime.datetime(2025, 11, 13).date(): '25N13',
        datetime.datetime(2025, 11, 20).date(): '25N20',
        datetime.datetime(2025, 11, 27).date(): '25NOV',
        datetime.datetime(2025, 12, 4).date(): '25D04',
        datetime.datetime(2025, 12, 11).date(): '25D11',
        datetime.datetime(2025, 12, 18).date(): '25D18',
        datetime.datetime(2025, 12, 25).date(): '25DEC',
    }


    today = datetime.datetime.now().date()

    for date_key, value in sensex_expiry.items():
        if today <= date_key:
            print(value)
            return value

def getSensexExpiryDate():
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
        datetime.datetime(2026, 3, 26).date(): '26MAR',
        datetime.datetime(2026, 4, 2).date(): '26402',
        datetime.datetime(2026, 4, 9).date(): '26409',
        datetime.datetime(2026, 4, 16).date(): '26416',
        datetime.datetime(2026, 4, 23).date(): '26423',
        datetime.datetime(2026, 4, 30).date(): '26APR',
        datetime.datetime(2026, 5, 7).date(): '26507',
        datetime.datetime(2026, 5, 14).date(): '26514',
        datetime.datetime(2026, 5, 21).date(): '26521',
        datetime.datetime(2026, 5, 28).date(): '26MAY',
        datetime.datetime(2026, 6, 4).date(): '26604',
        datetime.datetime(2026, 6, 11).date(): '26611',
        datetime.datetime(2026, 6, 18).date(): '26618',
        datetime.datetime(2026, 6, 25).date(): '26JUN',
        datetime.datetime(2026, 7, 2).date(): '26702',
        datetime.datetime(2026, 7, 9).date(): '26709',
        datetime.datetime(2026, 7, 16).date(): '26716',
        datetime.datetime(2026, 7, 23).date(): '26723',
        datetime.datetime(2026, 7, 30).date(): '26JUL',
        datetime.datetime(2026, 8, 6).date(): '26806',
        datetime.datetime(2026, 8, 13).date(): '26813',
        datetime.datetime(2026, 8, 20).date(): '26820',
        datetime.datetime(2026, 8, 27).date(): '26AUG',
        datetime.datetime(2026, 9, 3).date(): '26903',
        datetime.datetime(2026, 9, 10).date(): '26910',
        datetime.datetime(2026, 9, 17).date(): '26917',
        datetime.datetime(2026, 9, 24).date(): '26SEP',
        datetime.datetime(2026, 10, 1).date(): '26O01',
        datetime.datetime(2026, 10, 8).date(): '26O08',
        datetime.datetime(2026, 10, 15).date(): '26O15',
        datetime.datetime(2026, 10, 22).date(): '26O22',
        datetime.datetime(2026, 10, 29).date(): '26OCT',
        datetime.datetime(2026, 11, 5).date(): '26N05',
        datetime.datetime(2026, 11, 12).date(): '26N12',
        datetime.datetime(2026, 11, 19).date(): '26N19',
        datetime.datetime(2026, 11, 26).date(): '26NOV',
        datetime.datetime(2026, 12, 3).date(): '26D03',
        datetime.datetime(2026, 12, 10).date(): '26D10',
        datetime.datetime(2026, 12, 17).date(): '26D17',
        datetime.datetime(2026, 12, 24).date(): '26D24',
        datetime.datetime(2026, 12, 31).date(): '26DEC',
    }

    today = datetime.datetime.now().date()

    for date_key, value in sensex_expiry.items():
        if today <= date_key:
            print(value)
            return value

def getBankNiftyExpiryDate():
    return getStockExpiryDate()

def getFinNiftyExpiryDate():
    return getStockExpiryDate()

def getStockExpiryDate_old():
    stock_expiry = {
        datetime.datetime(2025, 1, 30).date(): "25JAN",
        datetime.datetime(2025, 2, 27).date(): "25FEB",
        datetime.datetime(2025, 3, 27).date(): "25MAR",
        datetime.datetime(2025, 4, 28).date(): "25APR",
        datetime.datetime(2025, 5, 29).date(): "25MAY",
        datetime.datetime(2025, 6, 26).date(): "25JUN",
        datetime.datetime(2025, 7, 31).date(): "25JUL",
        datetime.datetime(2025, 8, 28).date(): "25AUG",
        datetime.datetime(2025, 9, 30).date(): "25SEP",
        datetime.datetime(2025, 10, 28).date(): "25OCT",
        datetime.datetime(2025, 11, 25).date(): "25NOV",
        datetime.datetime(2025, 12, 30).date(): "25DEC",
    }

    today = datetime.datetime.now().date()

    for date_key, value in stock_expiry.items():
        if today <= date_key:
            print(value)
            return value

def getStockExpiryDate():
    stock_expiry = {
        datetime.datetime(2026, 1, 27).date(): "26JAN",
        datetime.datetime(2026, 2, 24).date(): "26FEB",
        datetime.datetime(2026, 3, 31).date(): "26MAR",
        datetime.datetime(2026, 4, 28).date(): "26APR",
        datetime.datetime(2026, 5, 26).date(): "26MAY",
        datetime.datetime(2026, 6, 30).date(): "26JUN",
        datetime.datetime(2026, 7, 28).date(): "26JUL",
        datetime.datetime(2026, 8, 25).date(): "26AUG",
        datetime.datetime(2026, 9, 29).date(): "26SEP",
        datetime.datetime(2026, 10, 27).date(): "26OCT",
        datetime.datetime(2026, 11, 24).date(): "26NOV",
        datetime.datetime(2026, 12, 29).date(): "26DEC",
    }

    today = datetime.datetime.now().date()

    for date_key, value in stock_expiry.items():
        if today <= date_key:
            print(value)
            return value

def getNiftyNextExpiryDate_old():
    nifty_expiry = {
        datetime.datetime(2025, 1, 2).date(): '25109',
        datetime.datetime(2025, 1, 9).date(): '25116',
        datetime.datetime(2025, 1, 16).date(): '25123',
        datetime.datetime(2025, 1, 23).date(): '25JAN',
        datetime.datetime(2025, 1, 30).date(): '25206',
        datetime.datetime(2025, 2, 6).date(): '25213',
        datetime.datetime(2025, 2, 13).date(): '25220',
        datetime.datetime(2025, 2, 20).date(): '25FEB',
        datetime.datetime(2025, 2, 27).date(): '25306',
        datetime.datetime(2025, 3, 6).date(): '25313',
        datetime.datetime(2025, 3, 13).date(): '25320',
        datetime.datetime(2025, 3, 20).date(): '25MAR',
        datetime.datetime(2025, 3, 27).date(): '25403',
        datetime.datetime(2025, 4, 3).date(): '25410',
        datetime.datetime(2025, 4, 10).date(): '25417',
        datetime.datetime(2025, 4, 17).date(): '25APR',
        datetime.datetime(2025, 4, 24).date(): '25430',
        datetime.datetime(2025, 4, 30).date(): '25508',
        datetime.datetime(2025, 5, 8).date(): '25515',
        datetime.datetime(2025, 5, 15).date(): '25522',
        datetime.datetime(2025, 5, 22).date(): '25MAY',
        datetime.datetime(2025, 5, 29).date(): '25605',
        datetime.datetime(2025, 6, 5).date(): '25612',
        datetime.datetime(2025, 6, 12).date(): '25619',
        datetime.datetime(2025, 6, 19).date(): '25JUN',
        datetime.datetime(2025, 6, 26).date(): '25703',
        datetime.datetime(2025, 7, 3).date(): '25710',
        datetime.datetime(2025, 7, 10).date(): '25717',
        datetime.datetime(2025, 7, 17).date(): '25724',
        datetime.datetime(2025, 7, 24).date(): '25JUL',
        datetime.datetime(2025, 7, 31).date(): '25807',
        datetime.datetime(2025, 8, 7).date(): '25814',
        datetime.datetime(2025, 8, 14).date(): '25821',
        datetime.datetime(2025, 8, 21).date(): '25AUG',
        datetime.datetime(2025, 8, 28).date(): '25902',
        datetime.datetime(2025, 9, 2).date(): '25909',
        datetime.datetime(2025, 9, 9).date(): '25916',
        datetime.datetime(2025, 9, 16).date(): '25923',
        datetime.datetime(2025, 9, 23).date(): '25SEP',
        datetime.datetime(2025, 9, 30).date(): '25O07',
        datetime.datetime(2025, 10, 7).date(): '25O14',
        datetime.datetime(2025, 10, 14).date(): '25O20',
        datetime.datetime(2025, 10, 21).date(): '25OCT',
        datetime.datetime(2025, 10, 28).date(): '25N04',
        datetime.datetime(2025, 11, 4).date(): '25N11',
        datetime.datetime(2025, 11, 11).date(): '25N18',
        datetime.datetime(2025, 11, 18).date(): '25NOV',
        datetime.datetime(2025, 11, 25).date(): '25D02',
        datetime.datetime(2025, 12, 2).date(): '25D09',
        datetime.datetime(2025, 12, 9).date(): '25D16',
        datetime.datetime(2025, 12, 16).date(): '25D23',
        datetime.datetime(2025, 12, 23).date(): '25DEC',
        datetime.datetime(2025, 12, 30).date(): '25DEC',
    }


    today = datetime.datetime.now().date()

    for date_key, value in nifty_expiry.items():
        if today <= date_key:
            print(value)
            return value

def getNiftyNextExpiryDate():
    nifty_expiry = {
        datetime.datetime(2026, 1, 6).date(): '26113',
        datetime.datetime(2026, 1, 13).date(): '26120',
        datetime.datetime(2026, 1, 20).date(): '26JAN',
        datetime.datetime(2026, 1, 27).date(): '26203',
        datetime.datetime(2026, 2, 3).date(): '26210',
        datetime.datetime(2026, 2, 10).date(): '26217',
        datetime.datetime(2026, 2, 17).date(): '26FEB',
        datetime.datetime(2026, 2, 24).date(): '26302',
        datetime.datetime(2026, 3, 3).date(): '26310',
        datetime.datetime(2026, 3, 10).date(): '26317',
        datetime.datetime(2026, 3, 17).date(): '26324',
        datetime.datetime(2026, 3, 24).date(): '26MAR',
        datetime.datetime(2026, 3, 31).date(): '26407',
        datetime.datetime(2026, 4, 7).date(): '26413',
        datetime.datetime(2026, 4, 14).date(): '26421',
        datetime.datetime(2026, 4, 21).date(): '26APR',
        datetime.datetime(2026, 4, 28).date(): '26505',
        datetime.datetime(2026, 5, 5).date(): '26512',
        datetime.datetime(2026, 5, 12).date(): '26519',
        datetime.datetime(2026, 5, 19).date(): '26MAY',
        datetime.datetime(2026, 5, 26).date(): '26602',
        datetime.datetime(2026, 6, 2).date(): '26609',
        datetime.datetime(2026, 6, 9).date(): '26616',
        datetime.datetime(2026, 6, 16).date(): '26623',
        datetime.datetime(2026, 6, 23).date(): '26JUN',
        datetime.datetime(2026, 6, 30).date(): '26707',
        datetime.datetime(2026, 7, 7).date(): '26714',
        datetime.datetime(2026, 7, 14).date(): '26721',
        datetime.datetime(2026, 7, 21).date(): '26JUL',
        datetime.datetime(2026, 7, 28).date(): '26804',
        datetime.datetime(2026, 8, 4).date(): '26811',
        datetime.datetime(2026, 8, 11).date(): '26818',
        datetime.datetime(2026, 8, 18).date(): '26AUG',
        datetime.datetime(2026, 8, 25).date(): '26901',
        datetime.datetime(2026, 9, 1).date(): '26908',
        datetime.datetime(2026, 9, 8).date(): '26915',
        datetime.datetime(2026, 9, 15).date(): '26922',
        datetime.datetime(2026, 9, 22).date(): '26SEP',
        datetime.datetime(2026, 9, 29).date(): '26O06',
        datetime.datetime(2026, 10, 6).date(): '26O13',
        datetime.datetime(2026, 10, 13).date(): '26O19',
        datetime.datetime(2026, 10, 20).date(): '26OCT',
        datetime.datetime(2026, 10, 27).date(): '26N03',
        datetime.datetime(2026, 11, 3).date(): '26N09',
        datetime.datetime(2026, 11, 10).date(): '26N17',
        datetime.datetime(2026, 11, 17).date(): '26NOV',
        datetime.datetime(2026, 11, 24).date(): '26D01',
        datetime.datetime(2026, 12, 1).date(): '26D08',
        datetime.datetime(2026, 12, 8).date(): '26D15',
        datetime.datetime(2026, 12, 15).date(): '26D22',
        datetime.datetime(2026, 12, 22).date(): '26DEC',
        datetime.datetime(2026, 12, 29).date(): '26DEC',
    }

    today = datetime.datetime.now().date()

    for date_key, value in nifty_expiry.items():
        if today <= date_key:
            print(value)
            return value

def getExpiryFormat(year, month, day, monthly):
    if monthly == 0:
        day1 = day
        if month == "JAN":
            month1 = 1
        elif month == "FEB":
            month1 = 2
        elif month == "MAR":
            month1 = 3
        elif month == "APR":
            month1 = 4
        elif month == "MAY":
            month1 = 5
        elif month == "JUN":
            month1 = 6
        elif month == "JUL":
            month1 = 7
        elif month == "AUG":
            month1 = 8
        elif month == "SEP":
            month1 = 9
        elif month == "OCT":
            month1 = "O"
        elif month == "NOV":
            month1 = "N"
        elif month == "DEC":
            month1 = "D"
    elif monthly == 1:
        day1 = ""
        month1 = month

    return str(year)+str(month1)+str(day1)

def getIndexSpot(stock):
    if stock == "BANKNIFTY":
        name = "NSE:NIFTYBANK-INDEX"
    elif stock == "NIFTY":
        name = "NSE:NIFTY50-INDEX"
    elif stock == "FINNIFTY":
        name = "NSE:FINNIFTY-INDEX"
    elif stock == "SENSEX":
        name = "BSE:SENSEX-INDEX"

    return name

def getOptionFormat(stock, intExpiry, strike, ce_pe):
    return "NSE:" + str(stock) + str(intExpiry)+str(strike)+str(ce_pe)

def getOptionFormat_bse(stock, intExpiry, strike, ce_pe):
    return "BSE:" + str(stock) + str(intExpiry)+str(strike)+str(ce_pe)

def getLTP(instrument):
    url = "http://localhost:4001/ltp?instrument=" + instrument
    try:
        resp = requests.get(url)
    except Exception as e:
        print(e)
    data = resp.json()
    return data

def getQuotes(instrument):
    try:
        with open("fyers_data.json", "r") as f:
            result = json.load(f)
        return float(result.get(instrument, None))
    except (FileNotFoundError, ValueError, TypeError):
        return -1

def manualLTP(symbol, fyers):
    data = {'symbols' : symbol}
    temp = fyers.quotes(data=data)
    #print(temp['d'][0]['v']['lp'])
    return float(temp['d'][0]['v']['lp'])

def placeOrder(inst ,t_type,qty,order_type,price,variety,fyers,papertrading=0,productType="intraday_eq"):
    exch = inst[:3]
    symb = inst[4:]
    dt = datetime.datetime.now()
    #papertrading = 0 #if this is 1, then actual trades will get placed
    print(dt.hour,":",dt.minute,":",dt.second ," => ",t_type," ",symb," ",qty," ",order_type)
    if(order_type=="MARKET"):
        type1 = 2
        price = 0
    elif(order_type=="LIMIT"):
        type1 = 1

    if(t_type=="BUY"):
        side1=1
    elif(t_type=="SELL"):
        side1=-1

    if variety == "regular":
        variety = False
    else:
        variety = True

    if productType == "intraday_eq":
        productType = "INTRADAY"
    elif productType == "positional_eq":
        productType = "CNC"
    elif productType == "intraday_fno":
        productType = "INTRADAY"
    elif productType == "positional_fno":
        productType = "MARGIN"
    else:
        productType = "INTRADAY"

    print(price)
    data =  {
        "symbol":inst,
        "qty":qty,
        "type":type1,
        "side":side1,
        "productType":productType,   #MARGIN
        "limitPrice":float(price),
        "stopPrice":0,
        "validity":"DAY",
        "disclosedQty":0,
        "offlineOrder":variety,
        "stopLoss":0,
        "takeProfit":0
    }
    try:
        if (papertrading == 1):
            orderid = fyers.place_order(data)
            print(dt.hour,":",dt.minute,":",dt.second ," ==> ", symb , orderid)
            return orderid
        else:
            return 0


    except Exception as e:
        print(dt.hour,":",dt.minute,":",dt.second ," => ", symb , "Failed : {} ".format(e))

def getHistorical(ticker,interval,duration,fyers):
    range_from = datetime.datetime.today()-timedelta(duration)
    range_to = datetime.datetime.today()

    from_date_string = range_from.strftime("%Y-%m-%d")
    to_date_string = range_to.strftime("%Y-%m-%d")
    data = {
        "symbol":ticker,
        "resolution":1,
        "date_format":"1",
        "range_from":from_date_string,
        "range_to":to_date_string,
        "cont_flag":"1"
    }

    response = fyers.history(data=data)['candles']

    # Create a DataFrame
    columns = ['Timestamp','open','high','low','close','volume']
    df = pd.DataFrame(response, columns=columns)

    # Convert Timestamp to datetime in UTC
    df['Timestamp2'] = pd.to_datetime(df['Timestamp'],unit='s').dt.tz_localize(pytz.utc)

    # Convert Timestamp to IST
    ist = pytz.timezone('Asia/Kolkata')
    df['Timestamp2'] = df['Timestamp2'].dt.tz_convert(ist)
    # Filter rows where 'Timestamp2' is less than 15:30
    filtered_df = df[df['Timestamp2'].dt.time < pd.to_datetime('15:30').time()]

    filtered_df['datetime2'] = filtered_df['Timestamp2'].copy()
    # Set 'Timestamp2' as the index
    filtered_df.set_index('Timestamp2', inplace=True)

    # Function to calculate dynamic origin based on the date
    def get_daily_origin(date):
        return pytz.timezone('Asia/Kolkata').localize(datetime.datetime(date.year, date.month, date.day, 9, 15))

    # Apply resampling with dynamic origin for each day
    resampled_df_list = []

    for date, group in filtered_df.groupby(filtered_df.index.date):
        # Get the dynamic origin for the current day
        origin = get_daily_origin(date)

        # Resample each day's group based on the 'interval' you want
        resampled_day = group.resample(f'{interval}min', label='left', origin=origin).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum',
            'datetime2': 'first'
        })

        # Append to list
        resampled_df_list.append(resampled_day)

    # Combine the resampled data from all days
    final_resampled_df = pd.concat(resampled_df_list)

    # Drop rows with missing data
    final_resampled_df = final_resampled_df.dropna(subset=['open'])

    return final_resampled_df

def getHistorical_second(ticker,interval,duration,fyers):
    range_from = datetime.datetime.today()-timedelta(duration)
    range_to = datetime.datetime.today()

    from_date_string = range_from.strftime("%Y-%m-%d")
    to_date_string = range_to.strftime("%Y-%m-%d")
    data = {
        "symbol":ticker,
        "resolution":"5S",
        "date_format":"1",
        "range_from":from_date_string,
        "range_to":to_date_string,
        "cont_flag":"1"
    }

    response = fyers.history(data=data)['candles']

    # Create a DataFrame
    columns = ['Timestamp','open','high','low','close','volume']
    df = pd.DataFrame(response, columns=columns)

    # Convert Timestamp to datetime in UTC
    df['Timestamp2'] = pd.to_datetime(df['Timestamp'],unit='s').dt.tz_localize(pytz.utc)

    # Convert Timestamp to IST
    ist = pytz.timezone('Asia/Kolkata')
    df['Timestamp2'] = df['Timestamp2'].dt.tz_convert(ist)
    # Filter rows where 'Timestamp2' is less than 15:30
    filtered_df = df[df['Timestamp2'].dt.time < pd.to_datetime('15:30').time()]

    filtered_df['datetime2'] = filtered_df['Timestamp2'].copy()
    # Set 'Timestamp2' as the index
    filtered_df.set_index('Timestamp2', inplace=True)
    filtered_df.drop(columns=['datetime2'], inplace=True)
    filtered_df.drop(columns=['Timestamp'], inplace=True)

    return filtered_df


def getHistorical_mcx(ticker,interval,duration,fyers):
    range_from = datetime.datetime.today()-timedelta(duration)
    range_to = datetime.datetime.today()

    from_date_string = range_from.strftime("%Y-%m-%d")
    to_date_string = range_to.strftime("%Y-%m-%d")
    data = {
        "symbol":ticker,
        "resolution":1,
        "date_format":"1",
        "range_from":from_date_string,
        "range_to":to_date_string,
        "cont_flag":"1"
    }

    response = fyers.history(data=data)['candles']

    # Create a DataFrame
    columns = ['Timestamp','open','high','low','close','volume']
    df = pd.DataFrame(response, columns=columns)

    # Convert Timestamp to datetime in UTC
    df['Timestamp2'] = pd.to_datetime(df['Timestamp'],unit='s').dt.tz_localize(pytz.utc)

    # Convert Timestamp to IST
    ist = pytz.timezone('Asia/Kolkata')
    df['Timestamp2'] = df['Timestamp2'].dt.tz_convert(ist)
    # Filter rows where 'Timestamp2' is less than 15:30
    filtered_df = df[df['Timestamp2'].dt.time < pd.to_datetime('23:55').time()]

    filtered_df['datetime2'] = filtered_df['Timestamp2'].copy()
    # Set 'Timestamp2' as the index
    filtered_df.set_index('Timestamp2', inplace=True)

    # Function to calculate dynamic origin based on the date
    def get_daily_origin(date):
        return pytz.timezone('Asia/Kolkata').localize(datetime.datetime(date.year, date.month, date.day, 9, 00))

    # Apply resampling with dynamic origin for each day
    resampled_df_list = []

    for date, group in filtered_df.groupby(filtered_df.index.date):
        # Get the dynamic origin for the current day
        origin = get_daily_origin(date)

        # Resample each day's group based on the 'interval' you want
        resampled_day = group.resample(f'{interval}min', label='left', origin=origin).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum',
            'datetime2': 'first'
        })

        # Append to list
        resampled_df_list.append(resampled_day)

    # Combine the resampled data from all days
    final_resampled_df = pd.concat(resampled_df_list)

    # Drop rows with missing data
    final_resampled_df = final_resampled_df.dropna(subset=['open'])

    return final_resampled_df
