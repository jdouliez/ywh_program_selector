import json
import time
import requests
from tqdm import tqdm
from prettytable import PrettyTable
from colorama import Fore, Style
from urllib.parse import urlparse
from datetime import datetime
from config import *


def banner():
    print(f"""
dP    dP dP   dP   dP dP     dP      888888ba                                                                               dP                     dP                     
Y8.  .8P 88   88   88 88     88      88    `8b                                                                              88                     88                     
 Y8aa8P  88  .8P  .8P 88aaaaa88a    a88aaaa8P' 88d888b. .d8888b. .d8888b. 88d888b. .d8888b. 88d8b.d8b.    .d8888b. .d8888b. 88 .d8888b. .d8888b. d8888P .d8888b. 88d888b. 
   88    88  d8'  d8' 88     88      88        88'  `88 88'  `88 88'  `88 88'  `88 88'  `88 88'`88'`88    Y8ooooo. 88ooood8 88 88ooood8 88'  `""   88   88'  `88 88'  `88 
   88    88.d8P8.d8P  88     88      88        88       88.  .88 88.  .88 88       88.  .88 88  88  88          88 88.  ... 88 88.  ... 88.  ...   88   88.  .88 88       
   dP    8888' Y88'   dP     dP      dP        dP       `88888P' `8888P88 dP       `88888P8 dP  dP  dP    `88888P' `88888P' dP `88888P' `88888P'   dP   `88888P' dP       
                                                                      .88                                                                                                 
                                                                  d8888P                                                                                                  
                                                                                    {Fore.CYAN}@_Ali4s_{Style.RESET_ALL}                                   
""")

def format_number(number):
    return f"{number:.0f}" if number == int(number) else f"{number:.1f}"
     
def red(input):
    return Fore.RED + str(input) + Style.RESET_ALL

def orange(input):
    return Fore.YELLOW + str(input) + Style.RESET_ALL

def green(input):
    return Fore.GREEN + str(input) + Style.RESET_ALL

def get_date_from(timestamp):
    return (time.time() - timestamp) / (24 * 3600)

def fetch_all(path, session, resultsPerPage=25):
    return fetch_all_v2(path, session, resultsPerPage) if "v2/" in path else fetch_all_v1(path, session, resultsPerPage)

def fetch_all_v1(path, session, resultsPerPage=25):
    all_items = []
    page = 0
    
    while True:
        res = session.get(f"{YWH_API}/{path}?resultsPerPage={resultsPerPage}&page={page}")
        if res.status_code != 200:
            break
            
        data = res.json()
        all_items.extend(data['items'])

        if "pagination" not in data or page + 1 >= data["pagination"]['nb_pages']:
            break
            
        page += 1
    
    return all_items

def fetch_all_v2(path, session, resultsPerPage=25):
    all_items = []
    page = 1
    
    while True:
        res = session.get(f"{YWH_API}/{path}?resultsPerPage={resultsPerPage}&page={page}")
        if res.status_code != 200:
            break
            
        data = res.json()
        all_items.extend(data['items'])

        if "pagination" not in data or page >= data["pagination"]['nb_pages']:
            break
            
        page += 1
    
    return all_items

def get_data_from_ywh():

    session = requests.Session()
    session.headers = {"Authorization": f"Bearer {YWH_BEARER}"}

    print(f"[>] Datasource file : {YWH_PROGS_FILE}...")

    res = session.get(f"{YWH_API}/user/members")
    if res.status_code == 200:
        private_invitations = [prog for prog in res.json()["items"] if "ROLE_PROGRAM_HUNTER" in prog['roles']]
        print(f"[>] Got {len(private_invitations)} private programs... ")

        reports = fetch_all(f"v2/hunter/reports", session, resultsPerPage=50)
        print(f"[>] Got {len(reports)} reports... ")

        print(f"[>] Gathering info about programs")
        for pi in tqdm(private_invitations):
            res = session.get(f"{YWH_API}/programs/{pi['program']['slug']}")
        
            if res.status_code == 200:
                pi['program'] = res.json()
                pi['program']['submissions'] = 0

                for report in reports:
                    if report['program']['slug'] == pi['program']['slug']:
                        if report["status"]['workflow_state'] not in ["out_of_scope", "rtfs", "auto_close", "duplicate"]:
                            pi['program']['submissions'] += 1
                
                if pi['program']['hall_of_fame']:
                    ranking = fetch_all(f"programs/{pi['program']['slug']}/ranking", session)
                    pi['program']['ranking'] = {'items': ranking} if ranking else {}
                else:
                    pi['program']['ranking'] = {}

                versions = fetch_all(f"programs/{pi['program']['slug']}/versions", session)                
                pi['program']['versions'] = versions

                credentials_pool = session.get(f"{YWH_API}/programs/{pi['program']['slug']}/credential-pools")
                pi['program']['credentials_pool'] = credentials_pool.json()['items']

                hacktivities = fetch_all(f"programs/{pi['program']['slug']}/hacktivity", session, resultsPerPage=100)
                pi['program']['hacktivities'] = hacktivities
            else:
                print(orange(f"[!] Program {pi['program']['name']} responded with status code {res.status_code}."))

        with open(YWH_PROGS_FILE, 'w') as file:
            json.dump(private_invitations, file, indent=4)

        return private_invitations
    
    elif res.status_code == 401:
        print(orange("[!] 401 NOT AUTHORIZED - The token seems outdated."))
        exit(1)
    else:
        print(red("[!] Data not reachable. Error"))
        exit(1)


def display(private_invitations):
    
    data = []
    print()
    
    for pi in private_invitations:
        points = 0
        
        name = pi['program']['title'].lower().replace("private bug bounty program", "").replace("bug bounty program", "").replace("private bugbounty", "").replace("bug bounty", "").replace("private program", "").strip().rstrip(' -').title()
        
        if not pi['program']['disabled']:
            program = pi['program']

            # Program name            
            if len(name) > NAME_LENGTH:
                name = program['title'][0:NAME_LENGTH-3] + "..."    

            # Program scopes 
            scopes = set()
            for scope in pi['program']["scopes"]:
                try:
                    scopes.add(urlparse(scope['scope']).netloc)
                except:
                    if "|" in scope['scope']:
                        for s in scope['scope'].split("|"):
                            scopes.add(s)
                    else:
                        scopes.add(scope['scope'])
            
            if  len(scopes) <= SCOPE_COUNT_THRESHOLD_1:
                points += 1
                scope_count = red(len(scopes))
            elif len(scopes) <= SCOPE_COUNT_THRESHOLD_2:
                points += 2
                scope_count = orange(len(scopes))
            else:
                points += 3
                scope_count = green(len(scopes))

            # Wildcard            
            if any('*' in url for url in scopes):
                has_wildcard = green("✔️")
                points += 3
            else:
                has_wildcard = orange("X")
                points += 1

            # Program vpn
            if program['vpn_active']:
                vpn = green("✔️")
                points += 1
            else:
                vpn = orange("X")
                points += 0

            # Reports counts            
            reports_count_per_scope = program['reports_count'] / program['scopes_count'] if not any('*' in url for url in scopes) else "-"
            reports_count = program['reports_count']
                        
            if reports_count_per_scope == "-":
                points += 3
            elif reports_count_per_scope <= REPORT_COUNT_PER_SCOPE_THREDHOLD_1:
                points += 3
                reports_count_per_scope = green(format_number(reports_count_per_scope))
            elif reports_count_per_scope <= REPORT_COUNT_PER_SCOPE_THREDHOLD_2:
                points += 2
                reports_count_per_scope = orange(format_number(reports_count_per_scope))
            else:
                points += 1
                reports_count_per_scope = red(format_number(reports_count_per_scope))

            # Report (in last 24h) count
            total_reports_last24_hours = program['stats']['total_reports_last24_hours']
            if total_reports_last24_hours <= TOTAL_REPORT_LAST24H_THRESHOLD_1:
                points += 3
                total_reports_last24_hours = green(total_reports_last24_hours)
            elif total_reports_last24_hours <= TOTAL_REPORT_LAST24H_THRESHOLD_2:
                points += 2
                total_reports_last24_hours = orange(total_reports_last24_hours)
            else:
                points += 1
                total_reports_last24_hours = red(total_reports_last24_hours)
                        
            # Report (in last 7d) count
            total_reports_last7_days = program['stats']['total_reports_last7_days']
            if total_reports_last7_days <= TOTAL_REPORT_LAST7D_THRESHOLD_1:
                points += 3
                total_reports_last7_days = green(total_reports_last7_days)
            elif total_reports_last7_days <= TOTAL_REPORT_LAST7D_THRESHOLD_2:
                points += 2
                total_reports_last7_days = orange(total_reports_last7_days)
            else:
                points += 1
                total_reports_last7_days = red(total_reports_last7_days)


            # Report (in last month) count
            total_reports_current_month = program['stats']['total_reports_current_month']
            if total_reports_current_month <= TOTAL_REPORT_LAST1M_THRESHOLD_1:
                points += 3
                total_reports_current_month = green(total_reports_current_month)
            elif total_reports_current_month <= TOTAL_REPORT_LAST1M_THRESHOLD_2:
                points += 2
                total_reports_current_month = orange(total_reports_current_month)
            else:
                points += 1
                total_reports_current_month = red(total_reports_current_month)

         
            # Hall of fame
            if len(program["ranking"]) == 0:
                hof = "✖️"  
            else:
                hof = len(program["ranking"]['items'])
                if hof <= 3:
                    points += HAF_THRESHOLD_1
                    hof = green(hof)
                elif hof <= HAF_THRESHOLD_2:
                    points += 2
                    hof = orange(hof)
                else:
                    points += 1
                    hof = red(hof)                               
            
            # Creation & Update dates
            dates = [datetime.fromisoformat(item['accepted_at']) for item in program['versions']]

            creation_date = min(dates)
            age = get_date_from(creation_date.timestamp())
            if age <= CREATION_DATE_THRESHOLD_1:
                creation_date = green(creation_date.strftime(DATE_FORMAT))
                points += 5
            elif age <= CREATION_DATE_THRESHOLD_2:
                creation_date = orange(creation_date.strftime(DATE_FORMAT))
                points += 2
            else:
                points += 1
                creation_date = red(creation_date.strftime(DATE_FORMAT))
            
            last_update_date = max(dates)
            age = get_date_from(last_update_date.timestamp())
            if age <= UPDATE_DATE_THRESHOLD_1:
                last_update_date = green(last_update_date.strftime(DATE_FORMAT))
                points += 2
            elif age <= UPDATE_DATE_THRESHOLD_2:
                last_update_date = orange(last_update_date.strftime(DATE_FORMAT))
                points += 1
            else:
                last_update_date = red(last_update_date.strftime(DATE_FORMAT))
            
            # Prog seems fresh new (no update)
            if creation_date == last_update_date:
                points += 1


            # Program hacktivities
            if len(program["hacktivities"]) > 0:
                last_hacktivity_date = datetime.strptime(program["hacktivities"][0]["date"], "%Y-%m-%d")  
            
                # No one has hunt since the last prog update
                if  max(dates).replace(tzinfo=None) > last_hacktivity_date.replace(tzinfo=None):
                    points += 2

                age = get_date_from(last_hacktivity_date.timestamp())
                if age <= LAST_HACKTIVITY_DATE_THRESHOLD_1:
                    last_hacktivity_date = red(last_hacktivity_date.strftime(DATE_FORMAT))
                    points += 2
                elif age <= LAST_HACKTIVITY_DATE_THRESHOLD_2:
                    last_hacktivity_date = orange(last_hacktivity_date.strftime(DATE_FORMAT))
                    points += 1
                else:
                    last_hacktivity_date = green(last_hacktivity_date.strftime(DATE_FORMAT))
            else:
                last_hacktivity_date  = "-"


            # Program submissions
            submissions = program['submissions'] if program['submissions'] > 0 else "-"
            points += program['submissions']

            # Program credentials
            if len(program['credentials_pool']) > 0:
                credz = green("✔️")
                points += len(program['credentials_pool']) / 2
            else:
                credz = orange("X")
                points += 0
        

            data.append([   format_number(points),
                            name, 
                            creation_date,
                            last_update_date,
                            last_hacktivity_date,
                            vpn,
                            scope_count,
                            has_wildcard,
                            reports_count,
                            reports_count_per_scope, 
                            total_reports_last24_hours,
                            total_reports_last7_days, 
                            total_reports_current_month,
                            submissions,
                            hof,
                            credz])
        else:
            print(f"[>] Program {name} is now disabled")
            
    data.sort(key=lambda x: x[0], reverse=True)
    
    results = PrettyTable(field_names=["Pts", "Name", "Creation date", "Last update", "Last hacktivity", "VPN", "Scopes", "Wildcard", "Reports", "Reports/scope", "Last 24h reports", "Last 7d reports", "Last 1m reports", "My reports", "HoF", "Credz"])
    results.add_rows(data)
    results.align = "c"
    results.align["Name"] = "l"
    
    print("\n\n")
    print(results)

