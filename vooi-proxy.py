import json
import time
import os
import random
from datetime import datetime
import urllib.parse
import cloudscraper
from colorama import Fore, init
from dateutil import parser
from dateutil.tz import tzutc
import requests

init(autoreset=True)

class VooiDC:
    def __init__(self):
        self.base_headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5",
            "Content-Type": "application/json",
            "Origin": "https://app.tg.vooi.io",
            "Referer": "https://app.tg.vooi.io/",
            "Sec-Ch-Ua": '"Not/A)Brand";v="99", "Google Chrome";v="118", "Chromium";v="118"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
        }
        self.scraper = None
        self.access_token = None
        self.current_proxy = None

    def set_proxy(self, proxy):
        self.current_proxy = proxy
        proxy_dict = {'http': proxy, 'https': proxy}
        self.scraper = cloudscraper.create_scraper()
        self.scraper.proxies.update(proxy_dict)

    def checkProxyIP(self):
        try:
            response = self.scraper.get('https://api.ipify.org?format=json', timeout=10)
            if response.status_code == 200:
                return response.json()['ip']
            else:
                return "Unknown"
        except Exception as e:
            self.log(f"Error checking proxy IP: {str(e)}", 'error')
            return "Error"

    def get_headers(self):
        headers = self.base_headers.copy()
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def log(self, msg, type='info'):
        timestamp = datetime.now().strftime("%H:%M:%S")
        if type == 'success':
            print(f"[{timestamp}] [t.me/scriptsharing] {Fore.GREEN}{msg}")
        elif type == 'custom':
            print(f"[{timestamp}] [t.me/scriptsharing] {Fore.MAGENTA}{msg}")
        elif type == 'error':
            print(f"[{timestamp}] [t.me/scriptsharing] {Fore.RED}{msg}")
        elif type == 'warning':
            print(f"[{timestamp}] [t.me/scriptsharing] {Fore.YELLOW}{msg}")
        else:
            print(f"[{timestamp}] [t.me/scriptsharing] {Fore.BLUE}{msg}")

    def countdown(self, seconds):
        for i in range(seconds, -1, -1):
            print(f"\r===== Wait {i} Second to continue =====", end="", flush=True)
            time.sleep(1)
        print()

    def login_new_api(self, init_data):
        url = "https://api-tg.vooi.io/api/v2/auth/login"
        payload = {
            "initData": init_data,
            "inviterTelegramId": ""
        }

        try:
            response = self.scraper.post(url, json=payload, headers=self.get_headers())
            time.sleep(1)
            if response.status_code == 201:
                self.access_token = response.json()['tokens']['access_token']
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": 'Unexpected response status'}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def check_autotrade(self):
        url = "https://api-tg.vooi.io/api/autotrade"
        try:
            response = self.scraper.get(url, headers=self.get_headers())
            time.sleep(1)
            if response.status_code in [200, 201]:
                return response.json()
            else:
                return None
        except Exception as e:
            self.log(f"Error checking autotrade: {str(e)}", 'error')
            return None

    def start_autotrade(self):
        url = "https://api-tg.vooi.io/api/autotrade/start"
        payload = {}
        try:
            response = self.scraper.post(url, json=payload, headers=self.get_headers())
            time.sleep(1)
            if response.status_code in [200, 201]:
                return response.json()
            else:
                return None
        except Exception as e:
            self.log(f"Error starting autotrade: {str(e)}", 'error')
            return None

    def claim_autotrade(self, auto_trade_id):
        url = "https://api-tg.vooi.io/api/autotrade/claim"
        payload = {"autoTradeId": auto_trade_id}
        try:
            response = self.scraper.post(url, json=payload, headers=self.get_headers())
            time.sleep(1)
            if response.status_code in [200, 201]:
                return response.json()
            else:
                return None
        except Exception as e:
            self.log(f"Error claiming autotrade: {str(e)}", 'error')
            return None

    def print_autotrade_info(self, data):
        end_time = parser.parse(data['endTime'])
        current_time = datetime.now(tzutc())
        time_left = end_time - current_time
        
        hours, remainder = divmod(time_left.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        rounded_time_left = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

        self.log(f"Autotrade Complete time: {end_time.strftime('%Y-%m-%d %H:%M:%S')} UTC", 'custom')
        self.log(f"Time left: {rounded_time_left}", 'custom')

    def handle_autotrade(self):
        autotrade_data = self.check_autotrade()
        time.sleep(1)
        if not autotrade_data:
            self.log("Start new AutoTrade...", 'warning')
            autotrade_data = self.start_autotrade()
            time.sleep(1)
            if autotrade_data:
                self.print_autotrade_info(autotrade_data)
            else:
                self.log("Start autotrade Failed.", 'error')
                return

        if autotrade_data['status'] == 'finished':
            self.log("Autotrade Completed. Get reward...", 'success')
            claim_result = self.claim_autotrade(autotrade_data['autoTradeId'])
            time.sleep(1)
            if claim_result:
                self.log(f"Claim autotrade Success. Reward {claim_result['reward']['virtMoney']} USD {claim_result['reward']['virtPoints']} VT", 'success')
                self.log(f"Total Balance {claim_result['balance']['virt_money']} USDT | {claim_result['balance']['virt_points']} VT", 'success')
            else:
                self.log("Claim Autotrade reward Failed.", 'error')

            self.log("Start new Autotrade...", 'warning')
            new_autotrade_data = self.start_autotrade()
            time.sleep(1)
            if new_autotrade_data:
                self.print_autotrade_info(new_autotrade_data)
            else:
                self.log("Start Autotrade Failed.", 'error')
        else:
            self.print_autotrade_info(autotrade_data)

    def start_tapping_session(self):
        url = "https://api-tg.vooi.io/api/tapping/start_session"
        payload = {}
        try:
            response = self.scraper.post(url, json=payload, headers=self.get_headers())
            time.sleep(1)
            if response.status_code in [200, 201]:
                return response.json()
            else:
                return None
        except Exception as e:
            self.log(f"Start Tap Failed: {str(e)}", 'error')
            return None

    def finish_tapping_session(self, session_id, virt_money, virt_points):
        url = "https://api-tg.vooi.io/api/tapping/finish"
        payload = {
            "sessionId": session_id,
            "tapped": {
                "virtMoney": virt_money,
                "virtPoints": virt_points
            }
        }
        try:
            response = self.scraper.post(url, json=payload, headers=self.get_headers())
            time.sleep(1)
            if response.status_code in [200, 201]:
                return response.json()
            else:
                self.log(f"Unexpected status code when finishing tapping session: {response.status_code}", 'warning')
                return None
        except Exception as e:
            self.log(f"Error finishing tapping session: {str(e)}", 'error')
            return None

    def play_tapping_game(self):
        for game_number in range(1, 5): 
            self.log(f"Start tap coin {game_number}/5", 'custom')
            session_data = self.start_tapping_session()
            time.sleep(2)
            if not session_data:
                self.log(f"Start Tap Coin {game_number} Failed. Skip this game.", 'warning')
                continue

            virt_money_limit = int(session_data['config']['virtMoneyLimit'])
            virt_points_limit = int(session_data['config']['virtPointsLimit'])

            self.log(f"Play game in 35 seconds...", 'custom')
            time.sleep(35)

            virt_money = random.randint(max(1, int(virt_money_limit * 0.5)), int(virt_money_limit * 0.8))
            virt_money = virt_money - (virt_money % 1)
            virt_points = virt_points_limit

            result = self.finish_tapping_session(session_data['sessionId'], virt_money, virt_points)
            time.sleep(1)
            if result:
                self.log(f"Tap Success, Reward {result['tapped']['virtMoney']} USD | {result['tapped']['virtPoints']} VT", 'success')
            else:
                self.log(f"Completing Game  {game_number} Failed | ", 'error')

            if game_number < 5:
                self.log("Wait 3 seconds...", 'custom')
                time.sleep(3)

    def get_tasks(self):
        url = "https://api-tg.vooi.io/api/tasks?limit=200&skip=0"
        try:
            response = self.scraper.get(url, headers=self.get_headers())
            time.sleep(1)
            if response.status_code == 200:
                return response.json()
            else:
                self.log(f"Unexpected status code when getting tasks: {response.status_code}", 'warning')
                return None
        except Exception as e:
            self.log(f"Error getting tasks: {str(e)}", 'error')
            return None

    def start_task(self, task_id):
        url = f"https://api-tg.vooi.io/api/tasks/start/{task_id}"
        try:
            response = self.scraper.post(url, json={}, headers=self.get_headers())
            time.sleep(2)
            if response.status_code in [200, 201]:
                return response.json()
            else:
                self.log(f"Unexpected status code when starting task: {response.status_code}", 'warning')
                return None
        except Exception as e:
            self.log(f"Error starting task: {str(e)}", 'error')
            return None

    def claim_task(self, task_id):
        url = f"https://api-tg.vooi.io/api/tasks/claim/{task_id}"
        try:
            response = self.scraper.post(url, json={}, headers=self.get_headers())
            time.sleep(2)
            if response.status_code in [200, 201]:
                return response.json()
            else:
                self.log(f"Unexpected status code when claiming task: {response.status_code}", 'warning')
                return None
        except Exception as e:
            self.log(f"Error claiming task: {str(e)}", 'error')
            return None

    def manage_tasks(self):
            tasks_data = self.get_tasks()
            time.sleep(2)
            if not tasks_data:
                self.log("Failed to get tasks data", 'error')
                return

            new_tasks = [task for task in tasks_data['nodes'] if task['status'] == 'new']
            for task in new_tasks:
                result = self.start_task(task['id'])
                time.sleep(2)
                if result and result['status'] == 'in_progress':
                    self.log(f"Perform task -  {task['description']} - Success", 'success')
                else:
                    self.log(f"Perform Task Failed - {task['description']}", 'error')

            completed_tasks = [task for task in tasks_data['nodes'] if task['status'] == 'done']
            for task in completed_tasks:
                result = self.claim_task(task['id'])
                time.sleep(2)
                if result and 'claimed' in result:
                    virt_money = result['claimed']['virt_money']
                    virt_points = result['claimed']['virt_points']
                    self.log(f"Perform Task - {task['description']} - Success | Reward {virt_money} USD | {virt_points} VT", 'success')
                else:
                    self.log(f"Không thể nhận thưởng cho nhiệm vụ {task['description']}", 'error')

    def main(self):
        data_file = os.path.join(os.path.dirname(__file__), 'data.txt')
        proxy_file = os.path.join(os.path.dirname(__file__), 'proxy.txt')
        
        with open(data_file, 'r', encoding='utf-8') as f:
            data = [line.strip() for line in f if line.strip()]
        
        with open(proxy_file, 'r', encoding='utf-8') as f:
            proxies = [line.strip() for line in f if line.strip()]

        while True:
            for i, (init_data, proxy) in enumerate(zip(data, proxies)):
                try:
                    self.set_proxy(proxy)
                    ip = self.checkProxyIP()
                    
                    user_data = json.loads(urllib.parse.unquote(init_data.split('user=')[1].split('&')[0]))
                    user_id = user_data['id']
                    first_name = user_data['first_name']

                    print(f"========== Account {i + 1} | {Fore.GREEN}{first_name} | ip: {ip} ==========")
                    
                    login_result = self.login_new_api(init_data)
                    time.sleep(2)
                    if login_result['success']:
                        self.log('Login Success!', 'success')
                        self.log(f"Name: {login_result['data']['name']}")
                        self.log(f"USD*: {login_result['data']['balances']['virt_money']}")
                        self.log(f"VT: {login_result['data']['balances']['virt_points']}")
                        self.log(f"Ref: {login_result['data']['frens']['count']}/{login_result['data']['frens']['max']}")
                        
                        self.handle_autotrade()
                        self.play_tapping_game()
                        self.manage_tasks()
                    else:
                        self.log(f"Login Failed! {login_result['error']}", 'error')

                except Exception as e:
                    self.log(f"Error with account {i + 1}: {str(e)}", 'error')
                self.log(f"Next account in 10 seconds")
                time.sleep(10) 

            self.countdown(30 * 60) 

if __name__ == "__main__":
    client = VooiDC()
    try:
        client.main()
    except Exception as e:
        client.log(str(e), 'error')
        exit(1)