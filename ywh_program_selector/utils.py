import ipaddress
import json
import re
import sys
import time
import requests
from collections import defaultdict
from datetime import datetime
from urllib.parse import urlparse
from colorama import Fore, Style
from tqdm import tqdm
from unidecode import unidecode

from .config import *


def banner():
    print(orange(f"""\n
dP    dP dP   dP   dP dP     dP      888888ba                                                                               dP                     dP                     
Y8.  .8P 88   88   88 88     88      88    `8b                                                                              88                     88                     
 Y8aa8P  88  .8P  .8P 88aaaaa88a    a88aaaa8P' 88d888b. .d8888b. .d8888b. 88d888b. .d8888b. 88d8b.d8b.    .d8888b. .d8888b. 88 .d8888b. .d8888b. d8888P .d8888b. 88d888b. 
   88    88  d8'  d8' 88     88      88        88'  `88 88'  `88 88'  `88 88'  `88 88'  `88 88'`88'`88    Y8ooooo. 88ooood8 88 88ooood8 88'  `""   88   88'  `88 88'  `88 
   88    88.d8P8.d8P  88     88      88        88       88.  .88 88.  .88 88       88.  .88 88  88  88          88 88.  ... 88 88.  ... 88.  ...   88   88.  .88 88       
   dP    8888' Y88'   dP     dP      dP        dP       `88888P' `8888P88 dP       `88888P8 dP  dP  dP    `88888P' `88888P' dP `88888P' `88888P'   dP   `88888P' dP       
                                                                      .88                                                                                                 
                                                                  d8888P                                                                                                  
                                                                                    {Fore.CYAN}@_Ali4s_{Style.RESET_ALL}                                   
"""), file=sys.stderr)


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


def get_name(title):
    return title.lower().replace("private bug bounty program", "").replace("bug bounty program", "").replace("private bugbounty", "").replace("bug bounty", "").replace("private program", "").strip().rstrip(' -').title()


def is_ip(ip_string):
    try:
        ipaddress.ip_address(ip_string)
        return True
    except ValueError:
        return False


def get_ips_from_subnet(subnet_string):
    try:
        # Check if it's a range notation (contains '-')
        if '-' in subnet_string:
            base_ip, range_end = subnet_string.rsplit('.', 1)
            start, end = range_end.split('-')

            start_num = int(start)
            end_num = int(end)

            if not (0 <= start_num <= 255 and 0 <= end_num <= 255):
                raise ValueError("IP range must be between 0 and 255")

            # Generate IPs in the range
            return {f"{base_ip}.{i}" for i in range(start_num, end_num + 1)}

        # Handle CIDR notation
        else:
            network = ipaddress.ip_network(subnet_string, strict=False)
            return {str(ip) for ip in network.hosts()}

    except ValueError as e:
        return set()  # Return empty set on invalid input


def convert_ids_to_slug(ids, private_invitations):
    results = []
    for id in ids:
        name = id
        for pi in private_invitations:
            if pi['program']['pid'] == id:
                name = get_name(pi['program']['title'])
        results.append(name)
    return results


def get_expanded_path(path):
    # Expand ~ to full home directory path if path starts with ~
    if path.startswith('~'):
        path = os.path.expanduser(path)
    return path


def is_valid_domain(url_string):
    # Add scheme if not present for urlparse
    if not url_string.startswith(('http://', 'https://')):
        url_string = 'https://' + url_string

    try:
        # Parse the URL
        parsed = urlparse(url_string)

        # Domain validation
        domain = parsed.netloc
        if not domain:
            return False

        # Basic domain format validation
        domain_pattern = r'^([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,}[:\d]*$'
        if not re.match(domain_pattern, domain, re.IGNORECASE):
            return False

        # Remove port
        domain = domain.split(":")[0]

        # Check domain parts
        parts = domain.split('.')
        if len(parts) < 2:  # Must have at least two parts (example.com)
            return False

        # Validate each domain part
        for part in parts:
            # Check length
            if len(part) > 63 or len(part) == 0:
                return False
            # Check for invalid characters
            if not all(c.isalnum() or c == '-' for c in part):
                return False
            # Check start/end characters
            if part.startswith('-') or part.endswith('-'):
                return False

        # Path validation (if exists)
        path = parsed.path
        if path:
            # Remove leading slash for empty paths
            if path == '/':
                path = ''
            # Check for invalid characters in path
            if not all(c.isalnum() or c in '-_.~/?' for c in path):
                return False

        return True

    except Exception:
        return False


def load_json_files(file_paths):
    """Load and merge all JSON files into a single dictionary."""
    all_data = {}
    for file_path in file_paths:
        with open(file_path, 'r') as f:
            data = json.load(f)
            all_data.update(data)
    return all_data


def analyze_common_ids(data):
    """Analyze which IDs are common across different numbers of users."""
    # Count how many users have each ID
    id_counts = defaultdict(set)
    for username, ids in data.items():
        for id_ in ids:
            id_counts[id_].add(username)

    # Get total number of users
    total_users = len(data)

    # Organize IDs by how many users have them
    results = defaultdict(list)
    for id_, users in id_counts.items():
        results[len(users)].append({'id': id_,'users': list(users)})
    return results, total_users


def display_collaborations(results, total_users, private_invitations):
    """Print the analysis results in a formatted way."""

    print(green(f"[>] Total number of hunters: {total_users}"))
    data = defaultdict(list)

    for num_users in range(total_users, 1, -1):
        ids = results.get(num_users, [])
        print(green(f"[*] Possible collaborations for {num_users} hunters : {len(ids)}"))

        for item in ids:
            hunters = ', '.join(sorted(item['users']))
            data[hunters].append(item['id'])

    results = PrettyTable()
    max_length = max(len(value) for _, value in data.items())

    for key,value in data.items():
        value.extend([""] * (max_length - len(value)))
        results.add_column(orange(key.replace(", ", " & ")), convert_ids_to_slug(list(value), private_invitations))

    results.align = "c"

    print()
    print(results)


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


def get_data_from_ywh(token):

    session = requests.Session()
    session.headers = {"Authorization": f"Bearer {token}"}

    print(f"[*] Datasource file : {YWH_PROGS_FILE}...")

    res = session.get(f"{YWH_API}/user/members")
    if res.status_code == 200:
        private_invitations = [prog for prog in res.json()["items"] if "ROLE_PROGRAM_HUNTER" in prog['roles']]
        print(green(f"[+] Got {len(private_invitations)} private programs... "))

        reports = fetch_all(f"v2/hunter/reports", session, resultsPerPage=50)
        print(green(f"[+] Got {len(reports)} reports... "))

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


def extract_programs_list(private_invitations, silent_mode):
    data = []

    for pi in private_invitations:
        name = get_name(pi['program']['title'])
        
        if not pi['program']['disabled']:
            program = pi['program']
            name = get_name(program['title'])[0:60]
            slug = program['slug'][0:60]
            data.append([f'{name}', f'{slug}'])
        else:
            if not silent_mode:
                print(f"[>] Program {name} is now disabled")

    return data        



def extract_programs_info(private_invitations, silent_mode):
    
    data = []
    
    for pi in private_invitations:
        points = 0
        
        name = get_name(pi['program']['title'])
        
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
                has_wildcard = green("X")
                points += 3
            else:
                has_wildcard = orange("-")
                points += 1

            # Program vpn
            if program['vpn_active']:
                vpn = green("X")
                points += 1
            else:
                vpn = orange("-")
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
                credz = green("X")
                points += len(program['credentials_pool']) / 2
            else:
                credz = orange("-")
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
            if not silent_mode:
                print(f"[>] Program {name} is now disabled")
            
    data.sort(key=lambda x: x[0], reverse=True)
    
    return data


def extract_programs_scopes(private_invitations, program_slug, silent=True):

    scope_web = set()
    scope_wildcard = set()
    scope_mobile = set()
    scope_ip = set()
    scope_misc = set()

    for pi in private_invitations:
        if not pi['program']['disabled']:
            if program_slug == "ALL" or program_slug.lower() == pi['program']['slug'].lower():
                for scope in pi['program']["scopes"]:

                    scope = unidecode(scope['scope']).split()[0].rstrip("/*").replace(":443","")

                    if scope.replace("https://","").startswith("*."):
                        if "|" in scope and "(" in scope and ")" in scope:
                            match = re.search(r'\((.*?)\)\.?(.*)|(.+?)\((.*?)\)', scope.replace("https://","").replace("*.",""))
                            if match.group(1):  # Extensions are at the start of the string
                                extensions = match.group(1).split('|')
                                base_domain = match.group(2)
                                domains = [f"{ext}.{base_domain}" for ext in extensions]
                            else:  # Extensions are at the end of the string
                                base_domain = match.group(3)
                                extensions = match.group(4).split('|')
                                domains = [f"{base_domain}{ext.strip()}" for ext in extensions]
                        else:
                            domains = [scope]

                        for s in domains:
                            scope_wildcard.add(s.replace("https://","").replace("*.",""))
                    elif "*" in scope:
                        scope_misc.add(scope)
                    elif "apps.apple.com" in scope or "play.google.com" in scope or ".apk" in scope or ".ipa" in scope:
                        scope_mobile.add(scope)
                    elif is_ip(scope):
                        scope_ip.add(scope)
                    elif "-" in scope or ("/" in scope and re.search(r'\/\d{1,2}$', scope)):
                        for s in get_ips_from_subnet(scope):
                            scope_ip.add(s)
                    elif "|" in scope and "(" in scope and ")" in scope:
                        match = re.search(r'\((.*?)\)\.?(.*)|(.+?)\((.*?)\)', scope)

                        if match.group(1):  # Extensions are ate the start of the string
                            extensions = match.group(1).split('|')
                            base_domain = match.group(2)
                            domains = [f"{ext}.{base_domain}" for ext in extensions]
                        else:  # Extensions are at the end of the string
                            base_domain = match.group(3)
                            extensions = match.group(4).split('|')
                            domains = [f"{base_domain}{ext.strip()}" for ext in extensions]

                        for scope in domains:
                            scope_web.add(scope if scope.startswith("http") else f"https://{scope}")
                    elif "|" in scope and "{" in scope and "}" in scope:
                         match = re.search(r'(.*)\{(.*?)\}(.*)', scope)
                         if not match:
                             scope_misc.add(scope)
                         else:
                             base_prefix = match.group(1) if match.group(1).endswith(".") else f"{match.group(1)}."  # Part before the curly braces
                             variations = match.group(2).split('|')  # The variations inside curly braces
                             base_suffix = match.group(3)  # Part after the curly braces

                             domains = [f"{base_prefix}{variation}{base_suffix}" for variation in variations]

                             for s in domains:
                                 scope_web.add(s)
                    elif "|" in scope and "[" in scope and "]" in scope:
                         match = re.search(r'(.*)\[(.*?)\](.*)', scope)
                         if not match:
                             scope_misc.add(scope)
                         else:
                             base_prefix = match.group(1) if match.group(1).endswith(".") else f"{match.group(1)}."  # P>
                             variations = match.group(2).split('|')  # The variations inside curly braces
                             base_suffix = match.group(3)  # Part after the curly braces
                             domains = [f"{base_prefix}{variation}{base_suffix}" for variation in variations]
                             for s in domains:
                                 scope_web.add(s)

                    elif is_valid_domain(scope):
                        scope_web.add(scope if scope.startswith("http") else f"https://{scope}")
                    elif "." not in scope:
                        pass
                    else:
                        scope_misc.add(scope)
        else:
            if not silent:
                print(f"[>] Program {get_name(pi['program']['title'])} is now disabled")

    print(green("\n\n[*] All scopes extracted"))   

    data = {
        "web": list(scope_web),
        "wildcard": list(scope_wildcard),
        "ip": list(scope_ip),
        "mobile": list(scope_mobile),
        "misc": list(scope_misc)
    }

    return data
