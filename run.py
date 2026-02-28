import requests
import re
import urllib3
import time
import threading
import os
import ssl
from urllib.parse import urlparse, parse_qs, urljoin

# --- SSL ERROR FIX ---
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURATION ---
SUCCESS_CODES_FILE = "success.txt"
PING_INTERVAL = 0.5

# --- CLEAR SCREEN FUNCTION ---
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

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

# --- MENU 1: TEST SPECIFIC CODE ---
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
        
        # --- တိကျစွာစစ်ဆေးခြင်း (Response text တွင် "success":true ဟု ပါမှ ယူမည်) ---
        if v_res.status_code == 200 and "\"success\":true" in v_res.text:
            print(f"\n\033[92m✅ SUCCESS! Valid Code Found: {code_to_test}\033[0m")
            with open(SUCCESS_CODES_FILE, "a") as f:
                f.write(f"{code_to_test}\n")
        else:
            print(f"\n❌ FAIL! Invalid Code: {code_to_test}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    time.sleep(3)

# --- MENU 2: INTERNET ACCESS ---
def use_internet_access():
    print("\n🌐 Internet Access အတွက် Code စစ်ဆေးနေသည်...")
    
    if not os.path.exists(SUCCESS_CODES_FILE):
        print("❌ Success Codes များမရှိပါ။")
        time.sleep(2)
        return

    with open(SUCCESS_CODES_FILE, "r") as f:
        codes = [line.strip() for line in f.readlines() if line.strip()]
        if not codes:
            print("❌ Success Codes များမရှိပါ။")
            time.sleep(2)
            return
        code = codes[-1] # နောက်ဆုံးရတဲ့ code ကိုသုံးမယ်

    print(f"📡 သုံးစွဲမည့် Code ကို သုံးနေသည်...")
    
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
        # Code အသုံးပြုခြင်း
        v_res = session.post(voucher_api, json={'accessCode': code, 'sessionId': sid, 'apiVersion': 1}, timeout=5)
        
        # --- RESPONSE စစ်ဆေးခြင်း ---
        if v_res.status_code == 200 and "\"success\":true" in v_res.text:
            print(f"\n\033[92m✅ SUCCESS! Internet Access Connected.\033[0m")
        else:
            print(f"\n❌ FAIL! Cannot connect with code.")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    time.sleep(3)

# --- MENU SYSTEM ---
def show_menu():
    clear_screen()
    print("========================================")
    print("         🛠️  VOUCHER TOOLKIT           ")
    print("========================================")
    print("1. 🔍 Test Specific Code")
    print("2. 🌐 Internet Access (Use Saved Code)")
    print("========================================\n")
    choice = input("👉 ရွေးချယ်ပါ (1-2): ")
    return choice

if __name__ == "__main__":
    while True:
        choice = show_menu()
        if choice == '1':
            test_specific_code()
        elif choice == '2':
            use_internet_access()
        else:
            print("🚫 မှားယွင်းသော ရွေးချယ်မှု။")
            time.sleep(1)
            
