import requests
import re
import urllib3
import time
import threading
import os
import ssl
import sys
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs, urljoin

# --- TERMUX SSL & HTTPS FIX ---
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURATION ---
# Cache ဖိုင်လမ်းကြောင်းကို သေချာအောင် folder တိုက်ရိုက်သတ်မှတ်ပေးနိုင်သည်
CACHE_FILE = "device_cache.txt"
# <--- သင့် Raw Link ကို ဒီမှာ ထည့်ပါ --->
GITHUB_TOKEN_URL = "https://raw.githubusercontent.com/winhtetaung1662004-byte/win/main/keys.txt"
PING_THREADS = 5
PING_INTERVAL = 0.5 
TOKEN_DURATION_HOURS = 1 

# --- FUNCTIONS ---
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_all_tokens():
    """GitHub ကနေ Token စာရင်းအားလုံးကိုယူခြင်း"""
    try:
        response = requests.get(GITHUB_TOKEN_URL, timeout=10, verify=False) 
        if response.status_code == 200:
            tokens = []
            for line in response.text.strip().split('\n'):
                token = line.split('|')[0].strip()
                if token:
                    tokens.append(token)
            return tokens
    except Exception as e:
        print(f"❌ GitHub ကနေ Token ယူမရပါ။ Error: {e}")
    return []

def check_cache():
    """Cached Token ရှိမရှိနှင့် သက်တမ်းစစ်ခြင်း"""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                data = f.read().split('|')
                if len(data) == 2:
                    token, expiry_str = data[0], data[1]
                    expiry_time = datetime.fromisoformat(expiry_str)
                    
                    # သက်တမ်းရှိသေးရင် return ပြန်
                    if datetime.now() < expiry_time:
                        return token
        except:
            pass
    return None

def save_cache(token):
    """Token ကို သက်တမ်းနဲ့တကွ ဖိုင်တွင်သိမ်းဆည်းခြင်း"""
    expiry_time = datetime.now() + timedelta(hours=TOKEN_DURATION_HOURS)
    try:
        with open(CACHE_FILE, "w") as f:
            f.write(f"{token}|{expiry_time.isoformat()}")
    except:
        pass

def get_portal_info():
    """Captive Portal URL ကို အလိုအလျောက်ရှာဖွေခြင်း"""
    test_url = "http://connectivitycheck.gstatic.com/generate_204"
    try:
        r = requests.get(test_url, allow_redirects=True, timeout=5)
        if r.url != test_url:
            parsed = urlparse(r.url)
            return f"{parsed.scheme}://{parsed.netloc}", r.url
    except:
        pass
    return None, None

def get_session_id(session, portal_url):
    """Session ID ယူခြင်း"""
    try:
        r1 = session.get(portal_url, verify=False, timeout=10)
        path_match = re.search(r"location\.href\s*=\s*['\"]([^'\"]+)['\"]", r1.text)
        next_url = urljoin(portal_url, path_match.group(1)) if path_match else portal_url
        r2 = session.get(next_url, verify=False, timeout=10)
        
        sid = parse_qs(urlparse(r2.url).query).get('sessionId', [None])[0]
        if not sid:
            sid_match = re.search(r'sessionId=([a-zA-Z0-9]+)', r2.text)
            sid = sid_match.group(1) if sid_match else None
        return sid
    except:
        return None

def countdown_timer(end_time):
    """အချိန်နောက်ပြန်ရေတွက်ခြင်း"""
    while True:
        remaining = end_time - datetime.now()
        if remaining.total_seconds() <= 0:
            print("\n⏳ Cache သက်တမ်းကုန်ဆုံးသွားပါပြီ။")
            if os.path.exists(CACHE_FILE): os.remove(CACHE_FILE)
            os._exit(0)
        print(f"\r[⏱️] သက်တမ်း: {remaining}", end="", flush=True)
        time.sleep(1)

# --- MENU FUNCTION ---
def turbo_token_access():
    """Token Access ပြုလုပ်ခြင်း"""
    clear_screen()
    print("========================================")
    print("         🌐 TURBO TOKEN ACCESS         ")
    print("========================================\n")
    
    # 1. Cache စစ်ခြင်း (အရင်ဝင်ထားပြီးသားလား)
    token = check_cache()
    if token:
        print(f"✅ Cached Token တွေ့ရှိသည်: {token}")
    else:
        # 2. Token ရိုက်ခိုင်းခြင်း
        user_token = input("👉 Activation Token ထည့်ပါ: ").strip()
        if not user_token:
            print("❌ Token ထည့်ပေးရန်လိုအပ်သည်။")
            time.sleep(2)
            return
        
        # 3. Token ကို Github နဲ့ စစ်ခြင်း
        valid_tokens = get_all
        
