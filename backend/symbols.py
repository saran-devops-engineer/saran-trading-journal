from datetime import datetime, timedelta
import json

# NSE Stock Symbols - Major Indian Stocks
NSE_STOCKS = [
    {"symbol": "RELIANCE", "name": "Reliance Industries Ltd", "sector": "Oil & Gas"},
    {"symbol": "TCS", "name": "Tata Consultancy Services", "sector": "IT"},
    {"symbol": "HDFCBANK", "name": "HDFC Bank Ltd", "sector": "Banking"},
    {"symbol": "INFY", "name": "Infosys Ltd", "sector": "IT"},
    {"symbol": "ICICIBANK", "name": "ICICI Bank Ltd", "sector": "Banking"},
    {"symbol": "HINDUNILVR", "name": "Hindustan Unilever Ltd", "sector": "FMCG"},
    {"symbol": "SBIN", "name": "State Bank of India", "sector": "Banking"},
    {"symbol": "BHARTIARTL", "name": "Bharti Airtel Ltd", "sector": "Telecom"},
    {"symbol": "KOTAKBANK", "name": "Kotak Mahindra Bank", "sector": "Banking"},
    {"symbol": "ITC", "name": "ITC Ltd", "sector": "FMCG"},
    {"symbol": "LT", "name": "Larsen & Toubro Ltd", "sector": "Infrastructure"},
    {"symbol": "AXISBANK", "name": "Axis Bank Ltd", "sector": "Banking"},
    {"symbol": "ASIANPAINT", "name": "Asian Paints Ltd", "sector": "Consumer"},
    {"symbol": "MARUTI", "name": "Maruti Suzuki India Ltd", "sector": "Auto"},
    {"symbol": "SUNPHARMA", "name": "Sun Pharmaceutical Ltd", "sector": "Pharma"},
    {"symbol": "TATAMOTORS", "name": "Tata Motors Ltd", "sector": "Auto"},
    {"symbol": "WIPRO", "name": "Wipro Ltd", "sector": "IT"},
    {"symbol": "ULTRACEMCO", "name": "UltraTech Cement Ltd", "sector": "Cement"},
    {"symbol": "ONGC", "name": "Oil & Natural Gas Corp", "sector": "Oil & Gas"},
    {"symbol": "TITAN", "name": "Titan Company Ltd", "sector": "Consumer"},
    {"symbol": "BAJFINANCE", "name": "Bajaj Finance Ltd", "sector": "Finance"},
    {"symbol": "NESTLEIND", "name": "Nestle India Ltd", "sector": "FMCG"},
    {"symbol": "TATACONSUM", "name": "Tata Consumer Products", "sector": "FMCG"},
    {"symbol": "ADANIENT", "name": "Adani Enterprises Ltd", "sector": "Conglomerate"},
    {"symbol": "ADANIPORTS", "name": "Adani Ports & SEZ", "sector": "Infrastructure"},
    {"symbol": "TECHM", "name": "Tech Mahindra Ltd", "sector": "IT"},
    {"symbol": "HCLTECH", "name": "HCL Technologies Ltd", "sector": "IT"},
    {"symbol": "POWERGRID", "name": "Power Grid Corp", "sector": "Power"},
    {"symbol": "NTPC", "name": "NTPC Ltd", "sector": "Power"},
    {"symbol": "TATASTEEL", "name": "Tata Steel Ltd", "sector": "Metal"},
    {"symbol": "JSWSTEEL", "name": "JSW Steel Ltd", "sector": "Metal"},
    {"symbol": "HINDALCO", "name": "Hindalco Industries", "sector": "Metal"},
    {"symbol": "BAJAJFINSV", "name": "Bajaj Finserv Ltd", "sector": "Finance"},
    {"symbol": "DRREDDY", "name": "Dr. Reddy's Laboratories", "sector": "Pharma"},
    {"symbol": "CIPLA", "name": "Cipla Ltd", "sector": "Pharma"},
    {"symbol": "DIVISLAB", "name": "Divi's Laboratories", "sector": "Pharma"},
    {"symbol": "EICHERMOT", "name": "Eicher Motors Ltd", "sector": "Auto"},
    {"symbol": "HEROMOTOCO", "name": "Hero MotoCorp Ltd", "sector": "Auto"},
    {"symbol": "BAJAJ-AUTO", "name": "Bajaj Auto Ltd", "sector": "Auto"},
    {"symbol": "BRITANNIA", "name": "Britannia Industries", "sector": "FMCG"},
    {"symbol": "COALINDIA", "name": "Coal India Ltd", "sector": "Mining"},
    {"symbol": "GRASIM", "name": "Grasim Industries Ltd", "sector": "Cement"},
    {"symbol": "SBILIFE", "name": "SBI Life Insurance", "sector": "Insurance"},
    {"symbol": "HDFCLIFE", "name": "HDFC Life Insurance", "sector": "Insurance"},
    {"symbol": "APOLLOHOSP", "name": "Apollo Hospitals", "sector": "Healthcare"},
    {"symbol": "LTIM", "name": "LTIMindtree Ltd", "sector": "IT"},
    {"symbol": "BPCL", "name": "Bharat Petroleum Corp", "sector": "Oil & Gas"},
    {"symbol": "INDUSINDBK", "name": "IndusInd Bank Ltd", "sector": "Banking"},
    {"symbol": "HINDPETRO", "name": "Hindustan Petroleum", "sector": "Oil & Gas"},
    {"symbol": "COLPAL", "name": "Colgate-Palmolive India", "sector": "FMCG"},
    {"symbol": "PIDILITIND", "name": "Pidilite Industries", "sector": "Chemicals"},
    {"symbol": "DMART", "name": "Avenue Supermarts", "sector": "Retail"},
    {"symbol": "VEDL", "name": "Vedanta Ltd", "sector": "Metal"},
    {"symbol": "ZOMATO", "name": "Zomato Ltd", "sector": "Internet"},
    {"symbol": "PAYTM", "name": "One97 Communications", "sector": "Fintech"},
    {"symbol": "NYKAA", "name": "FSN E-Commerce Ventures", "sector": "E-Commerce"},
    {"symbol": "DELHIVERY", "name": "Delhivery Ltd", "sector": "Logistics"},
    {"symbol": "DEEPAKNTR", "name": "Deepak Nitrite Ltd", "sector": "Chemicals"},
    {"symbol": "AUROPHARMA", "name": "Aurobindo Pharma", "sector": "Pharma"},
    {"symbol": "MCDOWELL-N", "name": "United Spirits", "sector": "Beverages"},
    {"symbol": "DABUR", "name": "Dabur India Ltd", "sector": "FMCG"},
    {"symbol": "MARICO", "name": "Marico Ltd", "sector": "FMCG"},
    {"symbol": "GODREJCP", "name": "Godrej Consumer Products", "sector": "FMCG"},
    {"symbol": "BERGEPAINT", "name": "Berger Paints India", "sector": "Consumer"},
    {"symbol": "VOLTAS", "name": "Voltas Ltd", "sector": "Consumer Durables"},
    {"symbol": "BATAINDIA", "name": "Bata India Ltd", "sector": "Footwear"},
    {"symbol": "RECLTD", "name": "REC Ltd", "sector": "Finance"},
    {"symbol": "PFC", "name": "Power Finance Corp", "sector": "Finance"},
    {"symbol": "IRFC", "name": "Indian Railway Finance", "sector": "Finance"},
    {"symbol": "SIEMENS", "name": "Siemens Ltd", "sector": "Capital Goods"},
    {"symbol": "ABB", "name": "ABB India Ltd", "sector": "Capital Goods"},
    {"symbol": "BHEL", "name": "Bharat Heavy Electricals", "sector": "Capital Goods"},
    {"symbol": "HAL", "name": "Hindustan Aeronautics", "sector": "Defence"},
    {"symbol": "BEL", "name": "Bharat Electronics", "sector": "Defence"},
    {"symbol": "COCHINSHIP", "name": "Cochin Shipyard Ltd", "sector": "Defence"},
    {"symbol": "MAZAGONDOCK", "name": "Mazagon Dock Shipbuilders", "sector": "Defence"},
]

# Indian Market Indices (Updated Jan 2026 - NSE Revised Lot Sizes)
INDICES = [
    {"symbol": "NIFTY50", "name": "Nifty 50", "exchange": "NSE", "lot_size": 65},
    {"symbol": "SENSEX", "name": "BSE Sensex", "exchange": "BSE", "lot_size": 10},
    {"symbol": "BANKNIFTY", "name": "Bank Nifty", "exchange": "NSE", "lot_size": 30},
    {"symbol": "NIFTY BANK", "name": "Nifty Bank", "exchange": "NSE", "lot_size": 30},
    {"symbol": "NIFTY IT", "name": "Nifty IT", "exchange": "NSE", "lot_size": 50},
    {"symbol": "NIFTY FINANCIAL SERVICES", "name": "Nifty Financial Services (FINNIFTY)", "exchange": "NSE", "lot_size": 60},
    {"symbol": "NIFTY MIDCAP SELECT", "name": "Nifty Midcap Select (MIDCPNIFTY)", "exchange": "NSE", "lot_size": 120},
    {"symbol": "NIFTY AUTO", "name": "Nifty Auto", "exchange": "NSE", "lot_size": 50},
    {"symbol": "NIFTY PHARMA", "name": "Nifty Pharma", "exchange": "NSE", "lot_size": 50},
    {"symbol": "NIFTY FMCG", "name": "Nifty FMCG", "exchange": "NSE", "lot_size": 30},
    {"symbol": "NIFTY METAL", "name": "Nifty Metal", "exchange": "NSE", "lot_size": 50},
    {"symbol": "NIFTY ENERGY", "name": "Nifty Energy", "exchange": "NSE", "lot_size": 50},
    {"symbol": "NIFTY REALTY", "name": "Nifty Realty", "exchange": "NSE", "lot_size": 50},
    {"symbol": "NIFTY MEDIA", "name": "Nifty Media", "exchange": "NSE", "lot_size": 50},
    {"symbol": "NIFTY PVT BANK", "name": "Nifty Private Bank", "exchange": "NSE", "lot_size": 50},
    {"symbol": "NIFTY PSU BANK", "name": "Nifty PSU Bank", "exchange": "NSE", "lot_size": 50},
    {"symbol": "NIFTY COMMODITIES", "name": "Nifty Commodities", "exchange": "NSE", "lot_size": 50},
    {"symbol": "NIFTY CONSUMPTION", "name": "Nifty Consumption", "exchange": "NSE", "lot_size": 50},
]

# Option strikes for indices (relative to current price)
NIFTY50_STRIKES = list(range(22000, 26001, 50))
SENSEX_STRIKES = list(range(72000, 82001, 100))
BANKNIFTY_STRIKES = list(range(48000, 56001, 100))


def get_next_expiry():
    today = datetime.now()
    days_until_thursday = (3 - today.weekday()) % 7
    if days_until_thursday == 0:
        days_until_thursday = 7
    expiry = today + timedelta(days=days_until_thursday)
    return expiry.strftime('%Y-%m-%d')


def get_monthly_expiry():
    today = datetime.now()
    if today.month == 12:
        next_month = today.replace(year=today.year + 1, month=1, day=1)
    else:
        next_month = today.replace(month=today.month + 1, day=1)

    days_until_thursday = (3 - next_month.weekday()) % 7
    if days_until_thursday == 0:
        days_until_thursday = 7
    expiry = next_month + timedelta(days=days_until_thursday - 1)
    return expiry.strftime('%Y-%m-%d')


def get_option_expiries():
    expiries = []
    today = datetime.now()

    for i in range(8):
        weeks_later = today + timedelta(weeks=i)
        days_until_thursday = (3 - weeks_later.weekday()) % 7
        if days_until_thursday == 0 and i == 0:
            days_until_thursday = 7
        expiry = weeks_later + timedelta(days=days_until_thursday)
        if expiry > today:
            expiries.append(expiry.strftime('%d-%b-%Y').upper())

    monthly = get_monthly_expiry()
    if monthly not in [e.replace('-', ' ').replace('.', '') for e in expiries]:
        expiries.append(datetime.strptime(monthly, '%Y-%m-%d').strftime('%d-%b-%Y').upper())

    return expiries[:8]


def get_option_chain(symbol):
    symbol = symbol.upper()
    expiries = get_option_expiries()

    if symbol in ['NIFTY50', 'NIFTY 50', 'NIFTY']:
        strikes = NIFTY50_STRIKES
        lot_size = 65
        current_price = 24500
    elif symbol in ['SENSEX']:
        strikes = SENSEX_STRIKES
        lot_size = 10
        current_price = 80000
    elif symbol in ['BANKNIFTY', 'BANK NIFTY']:
        strikes = BANKNIFTY_STRIKES
        lot_size = 30
        current_price = 52000
    else:
        return None

    chain = {
        "symbol": symbol,
        "current_price": current_price,
        "lot_size": lot_size,
        "expiries": expiries,
        "strikes": strikes,
        "options": {}
    }

    for expiry in expiries:
        chain["options"][expiry] = []
        for strike in strikes:
            moneyness = current_price - strike
            chain["options"][expiry].append({
                "strike": strike,
                "call_ltp": max(1, abs(moneyness) + 100),
                "call_change": 0,
                "put_ltp": max(1, abs(moneyness) + 100),
                "put_change": 0,
                "call_oi": 0,
                "put_oi": 0
            })

    return chain


def search_symbols(query):
    query = query.upper().strip()
    results = []

    for stock in NSE_STOCKS:
        if query in stock["symbol"] or query in stock["name"].upper():
            results.append({
                "symbol": stock["symbol"],
                "name": stock["name"],
                "type": "stock",
                "sector": stock["sector"]
            })

    for index in INDICES:
        if query in index["symbol"] or query in index["name"].upper():
            results.append({
                "symbol": index["symbol"],
                "name": index["name"],
                "type": "index",
                "exchange": index["exchange"],
                "lot_size": index["lot_size"]
            })

    return results[:20]


def get_all_symbols():
    symbols = []
    for stock in NSE_STOCKS:
        symbols.append({
            "symbol": stock["symbol"],
            "name": stock["name"],
            "type": "stock",
            "sector": stock["sector"]
        })
    for index in INDICES:
        symbols.append({
            "symbol": index["symbol"],
            "name": index["name"],
            "type": "index",
            "exchange": index["exchange"],
            "lot_size": index["lot_size"]
        })
    return symbols
