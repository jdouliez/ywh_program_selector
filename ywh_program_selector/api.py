"""API utilities for fetching data from YesWeHack."""

import json
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

import requests
from tqdm import tqdm

from ywh_program_selector.config import API_PARALLEL_WORKERS, YWH_API
from ywh_program_selector.display import green, orange, red


def fetch_all(path: str, session: requests.Session, resultsPerPage: int = 25) -> List[Dict]:
    """Fetch all paginated results from API endpoint."""
    if "v2/" in path:
        return fetch_all_v2(path, session, resultsPerPage)
    return fetch_all_v1(path, session, resultsPerPage)


def fetch_all_v1(path: str, session: requests.Session, resultsPerPage: int = 25) -> List[Dict]:
    """Fetch all results using v1 API pagination (0-indexed)."""
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


def fetch_all_v2(path: str, session: requests.Session, resultsPerPage: int = 25) -> List[Dict]:
    """Fetch all results using v2 API pagination (1-indexed)."""
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


def _fetch_program_details(
    pi: Dict,
    session: requests.Session,
    reports_by_slug: Dict[str, List[Dict]]
) -> Optional[Dict]:
    """
    Fetch detailed information for a single program.
    
    This function is designed to be called in parallel.
    """
    slug = pi['program']['slug']
    
    try:
        res = session.get(f"{YWH_API}/programs/{slug}")
        if res.status_code != 200:
            print(orange(f"[!] Program {pi['program'].get('name', slug)} responded with status code {res.status_code}."))
            return None

        program = res.json()
        
        # Count valid submissions from pre-grouped reports (O(1) lookup)
        program['submissions'] = sum(
            1 for report in reports_by_slug.get(slug, [])
            if report["status"]['workflow_state'] not in ["out_of_scope", "rtfs", "auto_close", "duplicate"]
        )

        # Fetch ranking if hall of fame exists
        if program.get('hall_of_fame'):
            ranking = fetch_all(f"programs/{slug}/ranking", session)
            program['ranking'] = {'items': ranking} if ranking else {}
        else:
            program['ranking'] = {}

        # Fetch versions
        program['versions'] = fetch_all(f"programs/{slug}/versions", session)

        # Fetch credentials pool
        creds_res = session.get(f"{YWH_API}/programs/{slug}/credential-pools")
        program['credentials_pool'] = creds_res.json().get('items', []) if creds_res.status_code == 200 else []

        # Fetch hacktivities
        program['hacktivities'] = fetch_all(f"programs/{slug}/hacktivity", session, resultsPerPage=100)

        return program

    except Exception as e:
        print(orange(f"[!] Error fetching program {slug}: {e}"))
        return None


def get_data_from_ywh(token: str, output_file: str) -> Optional[List[Dict]]:
    """
    Fetch all program data from YesWeHack API.
    
    Uses parallel requests for improved performance.
    """
    session = requests.Session()
    session.headers = {"Authorization": f"Bearer {token}"}

    print(f"[*] Datasource file : {output_file}...")

    res = session.get(f"{YWH_API}/user/members")
    
    if res.status_code == 401:
        print(orange("[!] 401 NOT AUTHORIZED - The token seems outdated."))
        exit(1)
    elif res.status_code != 200:
        print(red("[!] Data not reachable. Error"))
        exit(1)

    private_invitations = [
        prog for prog in res.json()["items"]
        if "ROLE_PROGRAM_HUNTER" in prog['roles']
    ]
    print(green(f"[+] Got {len(private_invitations)} private programs... "))

    # Fetch all reports once
    reports = fetch_all("v2/hunter/reports", session, resultsPerPage=50)
    print(green(f"[+] Got {len(reports)} reports... "))

    # Pre-group reports by slug for O(1) lookups (instead of O(n) per program)
    reports_by_slug: Dict[str, List[Dict]] = defaultdict(list)
    for report in reports:
        reports_by_slug[report['program']['slug']].append(report)

    print(f"[>] Gathering info about programs (parallel workers: {API_PARALLEL_WORKERS})")
    
    # Fetch program details in parallel
    with ThreadPoolExecutor(max_workers=API_PARALLEL_WORKERS) as executor:
        future_to_pi = {
            executor.submit(_fetch_program_details, pi, session, reports_by_slug): pi
            for pi in private_invitations
        }
        
        for future in tqdm(as_completed(future_to_pi), total=len(private_invitations)):
            pi = future_to_pi[future]
            try:
                program = future.result()
                if program:
                    pi['program'] = program
            except Exception as e:
                print(orange(f"[!] Error processing program: {e}"))

    with open(output_file, 'w') as file:
        json.dump(private_invitations, file, indent=4)

    return private_invitations
