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
SUCCESS_CODES_FILE = "success.txt"
CODE_TO_TEST = "536884" # --- စစ်ဆေးမည့် Code ---

# --- CLEAR SCREEN FUNCTION ---
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# --- CACHE MANAGEMENT ---
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
    print(f"2. 🔍 Test Specific Code: {CODE_TO_TEST}")
    print("3. 📋 View Success Codes")
    print("========================================\n")
    choice = input("👉 ရွေးချယ်ပါ (1-3): ")
    return choice

# --- SPECIFIC CODE TESTER ---
def test_specific_code():
    print(f"\n🔍 စမ်းသပ်နေသည်: {CODE_TO_TEST} ...")
    
    # Example placeholders - !! Portal အစစ်မှ ယူရမည် !!
    portal_host = "http://192.168.60.1" 
    sid = "example_session_id"
    session = requests.Session()
    
    voucher_api = f"{portal_host}/api/auth/voucher/"
    
    try:
        # --- API CALL စမ်းသပ်ခြင်း ---
        v_res = session.post(voucher_api, json={'accessCode': CODE_TO_TEST, 'sessionId': sid, 'apiVersion': 1}, timeout=5)
        
        if v_res.status_code == 200 and "success" in v_res.text.lower():
            # SUCCESS အစိမ်းရောင်
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
            test_specific_code()
        elif choice == '
        
