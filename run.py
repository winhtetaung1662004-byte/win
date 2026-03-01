import requests
import re
import urllib3
import time
import threading
import os
import ssl
import random
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs, urljoin

# --- SSL ERROR FIX ---
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURATION ---
CACHE_FILE = "device_cache.txt"
# <--- ဒီနေရာမှာ သင့် keys.txt ရဲ့ Raw လင့်ခ်ကို ထည့်ပါ --->
GITHUB_TOKEN_URL = "YOUR_GITHUB_RAW_FILE_LINK_HERE"
PING_THREADS = 5
PING_INTERVAL = 0.1 # Turbo
TOKEN_DURATION_HOURS = 1 # <--- Token သက်တမ်း (နာရီ)

# --- CLEAR SCREEN FUNCTION ---
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# --- GITHUB TOKEN CHECK ---
def get_latest_token():
    """GitHub ကနေ နောက်ဆုံး Token ကိုယူခြင်း"""
    try:
        response = requests.get(GITHUB_TOKEN_URL, timeout=10)
        if response.status_code == 200:
            return response.text.strip()
    except Exception as e:
        print(f"❌ GitHub ကနေ Token ယူမရပါ။ Error: {e}")
    return None

# --- CACHE MANAGEMENT ---
def check_cache():
    """Cached Token ရှိမရှိစစ်ခြင်း"""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            data = f.read().strip()
            if data:
                return data
    return None

def save_cache(token):
    with open(CACHE_FILE, "w") as f:
        f.write(token)

# --- PORTAL AUTO DETECT ---
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

# --- COUNTDOWN TIMER ---
def countdown_timer(end_time):
    """အချိန်နောက်ပြန်ရေတွက်ခြင်း"""
    while True:
        remaining = end_time - datetime.now()
        if remaining.total_seconds() <= 0:
            print("\n⏳ Token သက်တမ်းကုန်ဆုံးသွားပါပြီ။")
            os._exit(0)
        
        # Header မှာ အချိန်ပြပေးခြင်း
        print(f"\r[⏱️] သက်တမ်းကုန်ရန် ကျန်ရှိချိန်: {remaining}", end="", flush=True)
        time.sleep(1)

# --- MENU: TURBO TOKEN ACCESS ---
def turbo_token_access():
    print("\n🌐 Turbo Token Access စတင်ပြီ...")
    
    # 1. GitHub ကနေ Token ယူခြင်း
    latest_token = get_latest_token()
    if not latest_token:
        print("❌ Token မရရှိပါ။ (GitHub လင့်ခ်စစ်ပါ)")
        time.sleep(2)
        return

    # 2. Cache စစ်ခြင်း
    cached_token = check_cache()
    if cached_token and cached_token == latest_token:
        print(f"✅ Cached Token က နောက်ဆုံးပေါ်ဖြစ်နေသည်: {latest_token}")
        token = cached_token
    else:
        print(f"🔄 Token အသစ်တွေ့ရှိသည်: {latest_token}")
        token = latest_token
        save_cache(token)

    # 3. Portal နှင့် Session ID ယူခြင်း
    portal_host, portal_url = get_portal_info()
    if not portal_host:
        print("❌ Captive Portal ကို ရှာမတွေ့ပါ။")
        time.sleep(2)
        return

    session = requests.Session()
    sid = get_session_id(session, portal_url)
    if not sid:
        print("❌ Session ID ယူမရပါ။")
        time.sleep(2)
        return
        
    print(f"📡 Session Found: {sid}")

    # 4. Token API သုံးပြီး Activation
    voucher_api = f"{portal_host}/api/auth/voucher/"
    
    print(f"📡 Token ချိတ်ဆက်နေသည်: {token}")
    try:
        v_res = session.post(voucher_api, json={'accessCode': token, 'sessionId': sid, 'apiVersion': 1}, timeout=5)
        if v_res.status_code == 200 and "\"success\":true" in v_res.text:
            print(f"\033[92m✅ SUCCESS! Token Activated.\033[0m")
        else:
            print(f"❌ Token Activation Failed. Token အမှားဖြစ်နိုင်သည်")
            return
    except Exception as e:
        print(f"❌ Error during activation: {e}")
        return

    # 5. Turbo Pinging Threads များ (Gateway Auth Link)
    parsed_portal = urlparse(portal_url)
    params = parse_qs(parsed_portal.query)
    gw_addr = params.get('gw_address', ['192.168.60.1'])[0]
    gw_port = params.get('gw_port', ['2060'])[0]
    auth_link = f"http://{gw_addr}:{gw_port}/wifidog/auth?token={sid}&phonenumber=12345"

    def high_speed_ping():
        """Auth Link ကို အဆက်မပြတ် Request ပို့ပေးခြင်း"""
        while True:
            try:
                res = session.get(auth_link, timeout=5)
            except:
                pass
            time.sleep(PING_INTERVAL)

    print(f"[*] Starting {PING_THREADS} Turbo Pinging Threads...")
    for _ in range(PING_THREADS):
        threading.Thread(target=high_speed_ping, daemon=True).start()

    # 6. Countdown Timer Thread စတင်ခြင်း
    end_time = datetime.now() + timedelta(hours=TOKEN_DURATION_HOURS)
    threading.Thread(target=countdown_timer, args=(end_time,), daemon=True).start()

    # Internet လိုင်းတောက်လျှောက်ရနေအောင် ထိန်းထားခြင်း
    while True:
        try:
            requests.get("http://www.google.com", timeout=3)
            time.sleep(5)
        except:
            print("\n❌ Internet Disconnected. Trying to reconnect...")
            break

# --- MENU SYSTEM ---
def show_menu():
    clear_screen()
    print("========================================")
    print("         🛠️  VOUCHER TOOLKIT           ")
    print("========================================")
    print("1. 🌐 Turbo Token Access (GitHub)")
    print("2. 🔄 Reset Cache (Force Check)")
    print("========================================\n")
    choice = input("👉 ရွေးချယ်ပါ (1-2): ")
    return choice

if __name__ == "__main__":
    while True:
        choice = show_menu()
        if choice == '1':
            turbo_token_access()
        elif choice == '2':
            if os.path.exists(CACHE_FILE): os.remove(CACHE_FILE)
            print("✅ Cache ဖျက်ပြီးပါပြီ။")
            time.sleep(1)
        else:
            print("🚫 မှားယွင်းသော ရွေးချယ်မှု။")
            time.sleep(1)
            
