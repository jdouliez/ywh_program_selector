"""Program extraction and analysis utilities."""

import re
from datetime import datetime
from typing import Any, Dict, List, Set
from urllib.parse import urlparse

from unidecode import unidecode

from ywh_program_selector.config import (
    CREATION_DATE_THRESHOLD_1,
    CREATION_DATE_THRESHOLD_2,
    HOF_THRESHOLD_1,
    HOF_THRESHOLD_2,
    LAST_HACKTIVITY_DATE_THRESHOLD_1,
    LAST_HACKTIVITY_DATE_THRESHOLD_2,
    NAME_LENGTH,
    REPORT_COUNT_PER_SCOPE_THRESHOLD_1,
    REPORT_COUNT_PER_SCOPE_THRESHOLD_2,
    SCOPE_COUNT_THRESHOLD_1,
    SCOPE_COUNT_THRESHOLD_2,
    TOTAL_REPORT_LAST1M_THRESHOLD_1,
    TOTAL_REPORT_LAST1M_THRESHOLD_2,
    TOTAL_REPORT_LAST24H_THRESHOLD_1,
    TOTAL_REPORT_LAST24H_THRESHOLD_2,
    TOTAL_REPORT_LAST7D_THRESHOLD_1,
    TOTAL_REPORT_LAST7D_THRESHOLD_2,
    UPDATE_DATE_THRESHOLD_1,
    UPDATE_DATE_THRESHOLD_2,
)
from ywh_program_selector.display import format_number, green, orange
from ywh_program_selector.parsing import get_ips_from_subnet, get_name, is_ip, is_valid_domain
from ywh_program_selector.scoring import score_and_colorize, score_date


def extract_programs_list(private_invitations: List[Dict], silent_mode: bool) -> List[List[str]]:
    """Extract simple list of program names and slugs."""
    data = []

    for pi in private_invitations:
        name = get_name(pi['program']['title'])
        
        if not pi['program']['disabled']:
            program = pi['program']
            name = get_name(program['title'])[:60]
            slug = program['slug'][:60]
            data.append([name, slug])
        elif not silent_mode:
            print(f"[>] Program {name} is now disabled")

    return data


def extract_programs_info(private_invitations: List[Dict], silent_mode: bool) -> List[List[Any]]:
    """
    Extract and score all program information.
    
    Returns sorted list of program data with scoring.
    """
    data = []
    
    for pi in private_invitations:
        points = 0
        name = get_name(pi['program']['title'])
        
        if pi['program']['disabled']:
            if not silent_mode:
                print(f"[>] Program {name} is now disabled")
            continue

        program = pi['program']

        # Program name
        if len(name) > NAME_LENGTH:
            name = program['title'][:NAME_LENGTH - 3] + "..."

        # Parse scopes
        scopes: Set[str] = set()
        for scope in program.get("scopes", []):
            try:
                netloc = urlparse(scope['scope']).netloc
                if netloc:
                    scopes.add(netloc)
                else:
                    raise ValueError("No netloc")
            except (ValueError, KeyError):
                scope_val = scope.get('scope', '')
                if "|" in scope_val:
                    for s in scope_val.split("|"):
                        scopes.add(s)
                else:
                    scopes.add(scope_val)

        # Score scope count
        pts, scope_count = score_and_colorize(
            len(scopes),
            SCOPE_COUNT_THRESHOLD_1,
            SCOPE_COUNT_THRESHOLD_2,
            points_high=1, points_mid=2, points_low=3,
            reverse=True
        )
        points += pts

        # Check wildcard (compute once, reuse)
        has_wildcard_bool = any('*' in url for url in scopes)
        if has_wildcard_bool:
            has_wildcard = green("X")
            points += 3
        else:
            has_wildcard = orange("-")
            points += 1

        # VPN
        if program.get('vpn_active'):
            vpn = green("X")
            points += 1
        else:
            vpn = orange("-")

        # Reports count per scope
        reports_count = program.get('reports_count', 0)
        scopes_count = program.get('scopes_count', 1) or 1
        
        if has_wildcard_bool:
            reports_count_per_scope: Any = "-"
            points += 3
        else:
            rps = reports_count / scopes_count
            pts, reports_count_per_scope = score_and_colorize(
                rps,
                REPORT_COUNT_PER_SCOPE_THRESHOLD_1,
                REPORT_COUNT_PER_SCOPE_THRESHOLD_2
            )
            points += pts

        # Stats-based scoring
        stats = program.get('stats', {})
        
        # Reports in last 24h
        pts, total_reports_last24_hours = score_and_colorize(
            stats.get('total_reports_last24_hours', 0),
            TOTAL_REPORT_LAST24H_THRESHOLD_1,
            TOTAL_REPORT_LAST24H_THRESHOLD_2
        )
        points += pts

        # Reports in last 7 days
        pts, total_reports_last7_days = score_and_colorize(
            stats.get('total_reports_last7_days', 0),
            TOTAL_REPORT_LAST7D_THRESHOLD_1,
            TOTAL_REPORT_LAST7D_THRESHOLD_2
        )
        points += pts

        # Reports in current month
        pts, total_reports_current_month = score_and_colorize(
            stats.get('total_reports_current_month', 0),
            TOTAL_REPORT_LAST1M_THRESHOLD_1,
            TOTAL_REPORT_LAST1M_THRESHOLD_2
        )
        points += pts

        # Hall of Fame scoring
        ranking = program.get("ranking", {})
        if not ranking:
            hof: Any = "✖️"
        else:
            hof_count = len(ranking.get('items', []))
            pts, hof = score_and_colorize(
                hof_count,
                HOF_THRESHOLD_1,
                HOF_THRESHOLD_2
            )
            points += pts

        # Parse version dates (store raw dates for comparison)
        versions = program.get('versions', [])
        if versions:
            dates = [datetime.fromisoformat(item['accepted_at']) for item in versions]
            creation_date_raw = min(dates)
            last_update_date_raw = max(dates)
        else:
            creation_date_raw = datetime.now()
            last_update_date_raw = datetime.now()

        # Score creation date (newer is better)
        pts, creation_date, _ = score_date(
            creation_date_raw,
            CREATION_DATE_THRESHOLD_1,
            CREATION_DATE_THRESHOLD_2,
            points_high=5, points_mid=2, points_low=1
        )
        points += pts

        # Score last update date (newer is better)
        pts, last_update_date, _ = score_date(
            last_update_date_raw,
            UPDATE_DATE_THRESHOLD_1,
            UPDATE_DATE_THRESHOLD_2,
            points_high=2, points_mid=1, points_low=0
        )
        points += pts

        # Bonus if program is fresh (no updates since creation)
        if creation_date_raw == last_update_date_raw:
            points += 1

        # Hacktivity scoring
        hacktivities = program.get("hacktivities", [])
        last_hacktivity_date: Any
        if hacktivities:
            last_hacktivity_date_raw = datetime.strptime(hacktivities[0]["date"], "%Y-%m-%d")
            
            # Bonus: No one has hunted since last program update
            if last_update_date_raw.replace(tzinfo=None) > last_hacktivity_date_raw.replace(tzinfo=None):
                points += 2

            # Score hacktivity date (older is better - less competition)
            pts, last_hacktivity_date, _ = score_date(
                last_hacktivity_date_raw,
                LAST_HACKTIVITY_DATE_THRESHOLD_1,
                LAST_HACKTIVITY_DATE_THRESHOLD_2,
                points_high=2, points_mid=1, points_low=0,
                fresh_is_good=False
            )
            points += pts
        else:
            last_hacktivity_date = "-"

        # Submissions scoring
        submissions = program.get('submissions', 0)
        submissions_display: Any = submissions if submissions > 0 else "-"
        points += submissions

        # Credentials scoring
        creds_pool = program.get('credentials_pool', [])
        if creds_pool:
            credz = green("X")
            points += len(creds_pool) / 2
        else:
            credz = orange("-")

        data.append([
            format_number(points),
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
            submissions_display,
            hof,
            credz
        ])

    # Sort by points descending
    data.sort(key=lambda x: float(x[0]), reverse=True)
    return data


def extract_programs_scopes(
    private_invitations: List[Dict],
    program_slug: str,
    silent: bool = True
) -> Dict[str, List[str]]:
    """
    Extract and categorize scopes from programs.
    
    Categories: web, wildcard, ip, mobile, misc
    """
    scope_web: Set[str] = set()
    scope_wildcard: Set[str] = set()
    scope_mobile: Set[str] = set()
    scope_ip: Set[str] = set()
    scope_misc: Set[str] = set()

    for pi in private_invitations:
        if pi['program']['disabled']:
            if not silent:
                print(f"[>] Program {get_name(pi['program']['title'])} is now disabled")
            continue

        if program_slug != "ALL" and program_slug.lower() != pi['program']['slug'].lower():
            continue

        for scope_item in pi['program'].get("scopes", []):
            # Clean and normalize scope
            scope = unidecode(scope_item['scope']).split()[0].rstrip("/*").replace(":443", "").lower()

            # Wildcard patterns
            if scope.replace("https://", "").startswith("*."):
                if "|" in scope and "(" in scope and ")" in scope:
                    match = re.search(r'\((.*?)\)\.?(.*)|(.+?)\((.*?)\)', scope.replace("https://", "").replace("*.", ""))
                    if match:
                        if match.group(1):
                            extensions = match.group(1).split('|')
                            base_domain = match.group(2)
                            domains = [f"*.{ext}.{base_domain}" for ext in extensions]
                        else:
                            base_domain = match.group(3)
                            extensions = match.group(4).split('|')
                            domains = [f"*.{base_domain}{ext.strip()}" for ext in extensions]
                    else:
                        domains = [scope]
                else:
                    domains = [scope]

                for s in domains:
                    scope_wildcard.add(s.replace("https://", ""))

            elif ".*." in scope.replace("https://", ""):
                scope_wildcard.add(scope)
            elif "-*." in scope.replace("https://", ""):
                scope_wildcard.add(scope)
            elif "*" in scope:
                scope_misc.add(scope)

            # Mobile apps
            elif "apps.apple.com" in scope or "play.google.com" in scope or ".apk" in scope or ".ipa" in scope:
                scope_mobile.add(scope)

            # IP addresses
            elif is_ip(scope):
                scope_ip.add(scope)

            # IP subnets/ranges
            elif not re.search(r'[a-zA-Z]', scope) and ("-" in scope or ("/" in scope and re.search(r'\/\d{1,2}$', scope))):
                for s in get_ips_from_subnet(scope):
                    scope_ip.add(s)

            # Grouped domains with () syntax
            elif "|" in scope and "(" in scope and ")" in scope:
                match = re.search(r'\((.*?)\)\.?(.*)|(.+?)\((.*?)\)', scope)
                if match:
                    if match.group(1):
                        extensions = match.group(1).split('|')
                        base_domain = match.group(2)
                        domains = [f"{ext}.{base_domain}" for ext in extensions]
                    else:
                        base_domain = match.group(3)
                        extensions = match.group(4).split('|')
                        domains = [f"{base_domain}{ext.strip()}" for ext in extensions]

                    for s in domains:
                        scope_web.add(s if s.startswith("http") else f"https://{s}")
                else:
                    scope_misc.add(scope)

            # Grouped domains with {} syntax
            elif "|" in scope and "{" in scope and "}" in scope:
                match = re.search(r'(.*)\{(.*?)\}(.*)', scope)
                if match:
                    base_prefix = match.group(1) if match.group(1).endswith(".") else f"{match.group(1)}."
                    variations = match.group(2).split('|')
                    base_suffix = match.group(3)
                    domains = [f"{base_prefix}{variation}{base_suffix}" for variation in variations]
                    for s in domains:
                        scope_web.add(s)
                else:
                    scope_misc.add(scope)

            # Grouped domains with [] syntax
            elif "|" in scope and "[" in scope and "]" in scope:
                match = re.search(r'(.*)\[(.*?)\](.*)', scope)
                if match:
                    base_prefix = match.group(1) if match.group(1).endswith(".") else f"{match.group(1)}."
                    variations = match.group(2).split('|')
                    base_suffix = match.group(3)
                    domains = [f"{base_prefix}{variation}{base_suffix}" for variation in variations]
                    for s in domains:
                        scope_web.add(s)
                else:
                    scope_misc.add(scope)

            # Valid domain
            elif is_valid_domain(scope):
                scope_web.add(scope if scope.startswith("http") else f"https://{scope}")

            # Fallback to misc
            else:
                scope_misc.add(scope)

    return {
        "web": list(scope_web),
        "wildcard": list(scope_wildcard),
        "ip": list(scope_ip),
        "mobile": list(scope_mobile),
        "misc": list(scope_misc)
    }


def find_program_by_scope(
    private_invitations: List[Dict],
    search_scope: str,
    silent: bool = True
) -> List[Dict]:
    """
    Find programs that include the given scope.
    
    Args:
        private_invitations: List of program invitations
        search_scope: The scope URL/domain to search for
        silent: If False, print disabled program messages
    
    Returns:
        List of matching programs with their details
    """
    search_scope = search_scope.lower().strip()
    # Remove protocol for comparison
    search_normalized = search_scope.replace("https://", "").replace("http://", "").rstrip("/")
    
    matches = []
    
    for pi in private_invitations:
        if pi['program']['disabled']:
            if not silent:
                print(f"[>] Program {get_name(pi['program']['title'])} is now disabled")
            continue
        
        program = pi['program']
        program_scopes = program.get("scopes", [])
        
        for scope_item in program_scopes:
            scope = scope_item.get('scope', '').lower()
            scope_normalized = scope.replace("https://", "").replace("http://", "").rstrip("/")
            
            # Direct match
            if search_normalized == scope_normalized:
                matches.append({
                    'name': get_name(program['title']),
                    'slug': program['slug'],
                    'scope': scope,
                    'match_type': 'exact'
                })
                break
            
            # Wildcard match (*.example.com matches sub.example.com)
            if scope_normalized.startswith("*."):
                pattern = scope_normalized[2:]  # Remove *.
                if search_normalized.endswith(pattern) or search_normalized == pattern:
                    matches.append({
                        'name': get_name(program['title']),
                        'slug': program['slug'],
                        'scope': scope,
                        'match_type': 'wildcard'
                    })
                    break
            
            # Partial/contains match
            if search_normalized in scope_normalized or scope_normalized in search_normalized:
                matches.append({
                    'name': get_name(program['title']),
                    'slug': program['slug'],
                    'scope': scope,
                    'match_type': 'partial'
                })
                break
    
    return matches
