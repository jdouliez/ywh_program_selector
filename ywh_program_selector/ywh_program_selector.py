#!/usr/bin/env python3
"""
YWH Program Selector - CLI tool for managing YesWeHack private programs.

This tool helps bug hunters analyze and prioritize their YesWeHack programs,
find collaboration opportunities, and extract scope information.
"""

import argparse
import json
import os
import sys
from pathlib import Path

from colorama import init
from prettytable import PrettyTable

from ywh_program_selector.auth import get_token_from_credential
from ywh_program_selector.config import DATASOURCE_MAX_AGE, YWH_LOCAL_CONFIG_CREDZ, YWH_PROGS_FILE
from ywh_program_selector.utils import (
    analyze_common_ids,
    banner,
    display_collaborations,
    extract_programs_info,
    extract_programs_list,
    extract_programs_scopes,
    find_program_by_scope,
    get_data_from_ywh,
    get_date_from,
    get_expanded_path,
    green,
    load_json_files,
    orange,
    red,
)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='CLI tool to help bug hunters manage and prioritize their YesWeHack (YWH) private programs.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ywh-program-selector --local-auth --show
  ywh-program-selector --token <TOKEN> --extract-scopes -o scopes.json -f json
  ywh-program-selector --local-auth --collaborations --ids-files "user1.json,user2.json"
  ywh-program-selector --local-auth --find-by-scope "example.com"
        """
    )
    
    parser.add_argument('--silent', action='store_true', help='Do not print banner')
    parser.add_argument('--force-refresh', action='store_true', help='Force data refresh')

    # Authentication options
    auth_group = parser.add_mutually_exclusive_group(required=True)
    auth_group.add_argument('--token', help='Use the YesWeHack authorization bearer for auth')
    auth_group.add_argument('--local-auth', action='store_true', help='Use local credentials for auth')
    auth_group.add_argument('--auth-file', help='Path to credentials file for auth')
    auth_group.add_argument('--no-auth', action='store_true', help='Do not authenticate to YWH')

    # Action options
    options_group = parser.add_mutually_exclusive_group(required=True)
    options_group.add_argument('--show', action='store_true', help='Display all programs info with scoring')
    options_group.add_argument('--collab-export-ids', action='store_true', help='Export all programs collaboration IDs')
    options_group.add_argument('--collaborations', action='store_true', help='Show collaboration programs with other hunters')
    options_group.add_argument('--get-progs', action='store_true', help='Display programs simple list with slugs')
    options_group.add_argument('--extract-scopes', action='store_true', help='Extract program scopes')
    options_group.add_argument('--find-by-scope', metavar='SCOPE', help='Find a program by one of its scopes')

    # Additional options
    parser.add_argument('--ids-files', help='Comma separated list of paths to other hunter IDs. Ex: user1.json,user2.json')
    parser.add_argument('--program', help='Program slug (for --extract-scopes)')
    parser.add_argument('-o', '--output', help='Output file/directory path')
    parser.add_argument('-f', '--format', choices=['json', 'plain'], default='plain', help='Output format (default: plain)')

    return parser.parse_args()


def get_auth_file(args) -> Path:
    """Determine which auth file to use."""
    if args.auth_file:
        if not os.path.exists(args.auth_file):
            print(red(f"[>] Provided authentication file {args.auth_file} does not exist."))
            sys.exit(1)
        return Path(args.auth_file)
    
    if not os.path.exists(YWH_LOCAL_CONFIG_CREDZ):
        print(orange(f"[>] Default authentication file {YWH_LOCAL_CONFIG_CREDZ} does not exist."))
        os.makedirs(YWH_LOCAL_CONFIG_CREDZ.parent, exist_ok=True)
    
    return YWH_LOCAL_CONFIG_CREDZ


def load_or_fetch_data(args, auth_file):
    """Load data from cache or fetch from API."""
    # No local data exists
    if not os.path.exists(YWH_PROGS_FILE):
        if args.no_auth:
            print(red("[>] Local datasource does not exist and no authentication provided. Exiting."))
            sys.exit(1)
        
        token = args.token if args.token else get_token_from_credential(auth_file)
        print(orange("[>] Local datasource does not exist. Fetching data..."))
        return get_data_from_ywh(token, YWH_PROGS_FILE)

    # Force refresh requested
    if args.force_refresh:
        if args.no_auth:
            print(red("[>] Local datasource cannot be refreshed without authentication. Use --token or --local-auth."))
            sys.exit(1)
        
        token = args.token if args.token else get_token_from_credential(auth_file)
        print(orange("[>] Local datasource cache refresh. Fetching data..."))
        return get_data_from_ywh(token, YWH_PROGS_FILE)

    # Check if cache is outdated
    file_mtime = os.path.getmtime(YWH_PROGS_FILE)
    age_in_days = get_date_from(file_mtime)
    
    if age_in_days > DATASOURCE_MAX_AGE:
        if args.no_auth:
            print(red("[>] Local datasource is outdated but no authentication provided. Skipping refresh."))
            return None
        
        token = args.token if args.token else get_token_from_credential(auth_file)
        print(orange("[>] Local datasource is outdated. Fetching fresh data..."))
        return get_data_from_ywh(token, YWH_PROGS_FILE)

    # Load from cache
    with open(YWH_PROGS_FILE, 'r') as file:
        return json.load(file)


def cmd_collab_export_ids(private_invitations, args):
    """Export collaboration IDs."""
    username = private_invitations[0]['user']['username']
    pids = [pi['program']['pid'] for pi in private_invitations if pi['program'].get('pid')]
    data = json.dumps({username: pids}, indent=2)

    if args.output:
        with open(args.output, "w") as f:
            f.write(data)
        print(green(f"[!] Result saved to {args.output}"))
    else:
        print(data)


def cmd_collaborations(private_invitations, args, parser):
    """Find collaboration opportunities with other hunters."""
    if not args.ids_files:
        print(orange("[>] Please provide other hunters' collaboration IDs with --ids-files \"user1.json,user2.json\""))
        parser.print_usage()
        sys.exit(1)

    paths = [path.strip() for path in args.ids_files.split(",")]
    existing_files = [get_expanded_path(p) for p in paths if os.path.exists(get_expanded_path(p))]
    missing_files = [get_expanded_path(p) for p in paths if not os.path.exists(get_expanded_path(p))]

    for path in missing_files:
        print(red(f"[!] File {path} not found. Skipping."))

    if len(existing_files) == 0:
        print(red("[!] No valid collaboration ID files provided."))
        sys.exit(1)

    if len(existing_files) == 1:
        print(red("[!] IDs from at least 2 hunters are required for collaboration analysis."))
        sys.exit(1)

    try:
        data = load_json_files(existing_files)
        results, total_users = analyze_common_ids(data)
        display_collaborations(results, total_users, private_invitations)
    except json.JSONDecodeError as e:
        print(red(f"Error: Invalid JSON in one of the files: {e}"))
        sys.exit(1)
    except Exception as e:
        print(red(f"Error: {e}"))
        sys.exit(1)


def cmd_get_progs(private_invitations, args):
    """Display programs list with slugs."""
    data = extract_programs_list(private_invitations, args.silent)

    results = PrettyTable(field_names=["Name", "Slug"])
    results.add_rows(data)
    results.align = "l"
    print("\n")
    print(results)


def cmd_extract_scopes(private_invitations, args):
    """Extract program scopes."""
    program = args.program if args.program else "ALL"
    scope_data = extract_programs_scopes(private_invitations, program, args.silent)

    if args.format == "json":
        output_file = args.output if args.output else "scopes.json"
        with open(output_file, "w") as f:
            json.dump(scope_data, f, indent=4)
        print(green(f"[+] Data saved to {output_file}"))

    elif args.format == "plain":
        # Determine output directory
        output_dir = Path(args.output) if args.output else Path(".")
        if args.output and not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)
        
        # Write each scope category to its own file
        scope_files = {
            'web': 'scope_web.txt',
            'wildcard': 'scope_wildcard.txt',
            'ip': 'scope_ip.txt',
            'mobile': 'scope_mobile.txt',
            'misc': 'scope_misc.txt'
        }
        
        for category, filename in scope_files.items():
            filepath = output_dir / filename
            scopes = scope_data.get(category, [])
            print(orange(f" * {category.capitalize()} scope: {len(scopes)}"))
            with open(filepath, "w") as f:
                f.write("\n".join(scopes))
        
        print(green(f"[+] Scope files saved to {output_dir}/"))


def cmd_show(private_invitations, args):
    """Display all programs info with scoring."""
    data = extract_programs_info(private_invitations, args.silent)

    columns = [
        "Pts", "Name", "Creation date", "Last update", "Last hacktivity",
        "VPN", "Scopes", "Wildcard", "Reports", "Reports/scope",
        "Last 24h reports", "Last 7d reports", "Last 1m reports",
        "My reports", "HoF", "Credz"
    ]
    
    results = PrettyTable(field_names=columns)
    results.add_rows(data)
    results.align = "c"
    results.align["Name"] = "l"

    print("\n\n")
    print(results)


def cmd_find_by_scope(private_invitations, args):
    """Find programs by scope URL."""
    search_scope = args.find_by_scope
    matches = find_program_by_scope(private_invitations, search_scope, args.silent)
    
    if not matches:
        print(orange(f"[>] No programs found matching scope: {search_scope}"))
        return
    
    print(green(f"[+] Found {len(matches)} program(s) matching '{search_scope}':\n"))
    
    results = PrettyTable(field_names=["Program Name", "Slug", "Matching Scope", "Match Type"])
    for match in matches:
        results.add_row([
            match['name'],
            match['slug'],
            match['scope'],
            match['match_type']
        ])
    
    results.align = "l"
    print(results)


def main():
    """Main entry point."""
    # Initialize colorama
    init()

    args = parse_args()

    if not args.silent:
        banner()

    # Get authentication file path
    auth_file = get_auth_file(args)

    # Load or fetch program data
    private_invitations = load_or_fetch_data(args, auth_file)

    # Check if we have data to work with
    if not private_invitations or len(private_invitations) == 0:
        print(red("[>] You don't have any private invitations. Go get some!"))
        sys.exit(1)

    # Execute requested command
    if args.collab_export_ids:
        cmd_collab_export_ids(private_invitations, args)

    elif args.collaborations:
        parser = argparse.ArgumentParser()  # Recreate for print_usage
        cmd_collaborations(private_invitations, args, parser)

    elif args.get_progs:
        cmd_get_progs(private_invitations, args)

    elif args.extract_scopes:
        cmd_extract_scopes(private_invitations, args)

    elif args.show:
        cmd_show(private_invitations, args)

    elif args.find_by_scope:
        cmd_find_by_scope(private_invitations, args)

    else:
        print(red("[>] No action specified!"))
        sys.exit(1)


if __name__ == "__main__":
    main()
