import ctypes
import json
import threading
import time
from modules.ui import Logger
from modules.utils import Utils
from modules.solver import Solver
import tls_client
import httpx
from colorama import Fore
import sys
import os

#check if data and output folder exists
if not os.path.exists("data"):
    os.mkdir("data")
if not os.path.exists("output"):
    os.mkdir("output")
    

#config of the generator
config = json.load(open("data/config.json", encoding="utf-8"))

if config['invite_code'] == "":
    invite = input(Fore.LIGHTMAGENTA_EX + '[>] ' + Fore.WHITE + 'Enter invite code: ' + Fore.RESET)
else:
    invite = config['invite_code']

threadcount  = int(config['threads'])

#global variables
genned = 0
errors = 0
solved = 0
genStartTime = time.time()
server_name = httpx.get(f"https://discord.com/api/v9/invites/{invite}?with_counts=true&with_expiration=true").json()["guild"]["name"]


#title worker
class Title():
    global genned
    global errors
    global solved

    def __init__(self):
        self.title = f"{server_name} | Genned : {genned} | Errors: {errors} | Solved: {solved} | Elapsed: {round(time.time() - genStartTime, 2)}s"
        if sys.platform != "linux" or sys.platform != "darwin":
            ctypes.windll.kernel32.SetConsoleTitleW(self.title)

        

def get_js() -> str: #obtaining the js version from the discord website cause it's easier than parsing the html file for it and it's more reliable - Switch
    try:
        response = httpx.get("https://discord.com/app")
        response.raise_for_status()
    except httpx.HTTPError as e:
        print(f"HTTP error occurred while fetching latest JS version: {e}")
        return ""

    try:
        js_version = response.text.split('"></script><script src="/assets/')[2].split('" integrity')[0]
        return js_version
    except IndexError:
        print("Failed to parse JS version from response.")
        return ""


def build_num() -> str:
    js_version = get_js() #Obtaining the latest js version from the discord website which was not done in ur code at all - Switch
    url = f"https://discord.com/assets/{js_version}"

    try:
        response = httpx.get(url)
        response.raise_for_status()
    except httpx.HTTPError as e:
        print(f"HTTP error occurred while fetching build number: {e}")
        return ""

    try:
        build_number = response.text.split('(t="')[1].split('")?t:"")')[0]
        return build_number
    except IndexError:
        print("Failed to parse build number from response.")
        return ""

 #Parsing the build number from the js file - Switch
build_number = int(build_num())
if build_number == "":
    Logger.Error("Failed to parse build number, please try again later.")
    exit()
else:
    
    Logger.Info(f"Build number: {build_number}")
    Utils.clear()

Title()
bal = Solver.get_capmonster_balance()
Logger.Info("Balance of Capmonster Key " + str(bal))#Getting the balance of the capmonster api key - Switch

class Main():
    def main():
        global genned, solved, errors
        proxy = Utils.getproxy()
        proxy_str = str(proxy).strip()
        kkproxy  = Utils.getformattedproxy(proxy_str)
        client = tls_client.Session(client_identifier='chrome_108')
        response = client.get("https://discord.com/api/v9/experiments", proxy=f'http://{kkproxy}') #Your code was actually making a request to get fingerprints but it didnt use it at all - Switch  
        fingerprint = response.json()['fingerprint']
        time_solve = time.time()
        key = Solver.solve_capmonster(site_key='4c672d35-0701-42b2-88c3-78380b0db560',page_url = 'https://discord.com/')
        time_solve = time.time() - time_solve
        Logger.Info(f"Solved {key[:25]} in {round(time_solve, 2)}s")
        solved += 1
        Title()

        payload={
            'fingerprint': fingerprint,
            'email': str(Utils.getemail()),
            'username': str(Utils.username()),
            'password': str(Utils.passw()),
            'invite': invite,
            'consent': True,
            'date_of_birth': Utils.getborndate(),
            "gift_code_sku_id": None,
            "captcha_key": key,
            "promotional_email_opt_in": True
        }

        headers={
            'origin': 'https://discord.com',
            'referer': f'https://discord.gg/{invite}',
            'x-discord-locale': 'en-US',
            'x-debug-options': 'bugReporterEnabled',
            'user-agent': config['useragent'],
            'x-fingerprint': fingerprint,
            'x-super-properties': Utils.getsuperproperties(build_number),
            'Content-Type': 'application/json'
        }

        response2 = client.post('https://discord.com/api/v9/auth/register',json = payload, headers = headers, proxy=f'http://{kkproxy}'
        )
        if response2.status_code == 201:
            token = response2.json()['token']
            Logger.Success(f"Generated | {token[:40]}.......")
            genned += 1
            Title()
            #save token in file
            with open(f"output/{invite}.txt", "a", encoding="utf-8") as f:
                f.write(f"{token}\n")
        
        elif response2.status_code == 429:
            Logger.Error("Rate limited | Passing to next proxy")
            errors += 1
            Title()
        
        elif 'captcha' in response2.text:
            Logger.Error("Invalid Captcha Data")
            errors += 1
            Title()
            
        else:
            Logger.Error("Unknown Error")
            errors += 1
            Title() 


def loop():
    global errors
    while True:
        try:
            Title()
            Main.main()
        except Exception as e:
            Logger.Error(f"Error: {e}")
            errors += 1
            Title()


#threading with max 50 threads
for i in range(threadcount):
    threading.Thread(target=loop).start()
