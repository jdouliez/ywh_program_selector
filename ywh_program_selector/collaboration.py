"""Collaboration analysis utilities."""

from collections import defaultdict
from typing import Dict, List, Tuple

from prettytable import PrettyTable

from ywh_program_selector.display import green, orange
from ywh_program_selector.parsing import get_name


def build_pid_to_name_map(private_invitations: List[Dict]) -> Dict[str, str]:
    """Build a mapping from program ID to program name for O(1) lookups."""
    return {
        pi['program']['pid']: get_name(pi['program']['title'])
        for pi in private_invitations
        if pi['program'].get('pid')
    }


def convert_ids_to_slug(ids: List[str], private_invitations: List[Dict]) -> List[str]:
    """Convert program IDs to names using pre-built mapping."""
    pid_to_name = build_pid_to_name_map(private_invitations)
    return [pid_to_name.get(id_, id_) for id_ in ids]


def analyze_common_ids(data: Dict[str, List[str]]) -> Tuple[Dict[int, List], int]:
    """
    Analyze which IDs are common across different numbers of users.
    
    Returns:
        Tuple of (results dict keyed by user count, total user count)
    """
    id_counts = defaultdict(set)
    for username, ids in data.items():
        for id_ in ids:
            id_counts[id_].add(username)

    total_users = len(data)

    results = defaultdict(list)
    for id_, users in id_counts.items():
        results[len(users)].append({'id': id_, 'users': list(users)})
    
    return results, total_users


def display_collaborations(results: Dict, total_users: int, private_invitations: List[Dict]):
    """Print collaboration analysis results in formatted table."""
    print(green(f"[>] Total number of hunters: {total_users}"))
    data = defaultdict(list)

    for num_users in range(total_users, 1, -1):
        ids = results.get(num_users, [])
        print(green(f"[*] Possible collaborations for {num_users} hunters : {len(ids)}"))

        for item in ids:
            hunters = ', '.join(sorted(item['users']))
            data[hunters].append(item['id'])

    results_table = PrettyTable()
    max_length = max(len(value) for value in data.values()) if data else 0

    for key, value in data.items():
        value.extend([""] * (max_length - len(value)))
        results_table.add_column(
            orange(key.replace(", ", " & ")),
            convert_ids_to_slug(list(value), private_invitations)
        )

    results_table.align = "c"
    print()
    print(results_table)
