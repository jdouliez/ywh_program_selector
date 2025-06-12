import argparse
import json
import os

from colorama import init
from prettytable import PrettyTable

from .auth import get_token_from_credential
from .config import DATASOURCE_MAX_AGE, YWH_PROGS_FILE
from .utils import (
    analyze_common_ids,
    banner,
    extract_programs_info,
    extract_programs_list,
    extract_programs_scopes,
    get_data_from_ywh,
    get_date_from,
    get_expanded_path,
    green,
    load_json_files,
    display_collaborations,
    orange,
    red,
)


def main():
    # Init colorama
    init()

    # Arguments
    parser = argparse.ArgumentParser(description='The ywh_program_selector project is a tool designed to help users manage and prioritize their YesWeHack (YWH) private programs.')
    parser.add_argument('--silent', action='store_true', help='Do not print banner')
    parser.add_argument('--force-refresh', action='store_true', help='Force data refresh')

    auth_group = parser.add_mutually_exclusive_group(required=True)
    auth_group.add_argument('--token', help='Use the YesWeHack authorization bearer for auth')
    auth_group.add_argument('--local-auth', action='store_true', help='Use local credentials for auth')
    auth_group.add_argument('--no-auth', action='store_true', help='Do not authenticate to YWH')

    options_group = parser.add_mutually_exclusive_group(required=True)
    options_group.add_argument('--show', action='store_true', help='Display all programs info')
    options_group.add_argument('--collab-export-ids', action='store_true', help='Export all programs collaboration ids')
    options_group.add_argument('--find-collaborations', action='store_true', help='Show collaboration programs with other hunters')
    options_group.add_argument('--get-progs', action='store_true', help='Displays programs simple list with slugs')
    options_group.add_argument('--extract-scopes', action='store_true', help='Extract program scopes')
    options_group.add_argument('--find-by-scope', help='Find a program by one of its scope')

    parser.add_argument('--ids-files', help='Comma separated list of paths to other hunter IDs. Ex. user1.json,user2.json')
    parser.add_argument('--program', help='Program slug')
    parser.add_argument('-o', '--output', help='Output file path')
    parser.add_argument('-f', '--format', choices=['json', 'plain'], default='plain', help='Output format (json, plain)')
    
    args = parser.parse_args()

    if not args.silent:
        # Print banner because it's cool
        banner()

    if not os.path.exists(YWH_PROGS_FILE):
        if not args.no_auth:
            token = get_token_from_credential() if not args.token else args.token
            print(orange("[>] Local datasource does not exist. Fetching data.."))
            private_invitations = get_data_from_ywh(token)
        else:
            print(red("[>] Local datasource does not exist and no authentication provided. Exiting.."))
            exit(1)
    elif args.force_refresh:
        if not args.no_auth:
            token = get_token_from_credential() if not args.token else args.token
            print(orange("[>] Local datasource cache refresh. Fetching data.."))
            private_invitations = get_data_from_ywh(token)
        else:
            print(red("[>] Local datasource cannot be refreshed without authentication method. Use --token or --local-auth. Exiting..."))
            exit(1)
    else:
        file_mtime = os.path.getmtime(YWH_PROGS_FILE)
        age_in_days = get_date_from(file_mtime)
        if age_in_days > DATASOURCE_MAX_AGE:
            if not args.no_auth:
                token = get_token_from_credential() if not args.token else args.token
                print(orange("[>] Local datasource is outdated. Fetching fresh data"))
                private_invitations = get_data_from_ywh(token)
            else:
                print(red("[>] Local datasource is outdated but no authentication provided. Skipping refresh"))
                private_invitations = None
        else:
            with open(YWH_PROGS_FILE, 'r') as file:
                private_invitations = json.load(file)

    # Check if user has private programs
    if not private_invitations or len(private_invitations) == 0:
        print(red(f"[>] You don't have any private invitations. Go on, bro!"))
        exit(1)

    # Export all programs collaboration ids
    if args.collab_export_ids:
        data = json.dumps({f"{private_invitations[0]['user']['username']}": [pi['program']['pid'] for pi in private_invitations if pi['program']['pid']]})

        if args.output:
            with open(args.output, "w") as f:
                f.write(data)
            print(green(f"[!] Result saved in {args.output}"))
        else:
            print(data)

    # Show collaboration programs with other hunters
    elif args.find_collaborations:

        if not args.ids_files:
            print(orange(f"[>] Please, provide other hunters collaboration ids list with option --ids-files \"./user-1.json, /tmp/user2.json\""))
            parser.print_usage()
            exit(1)

        existing_files = [get_expanded_path(path.strip()) for path in args.ids_files.split(",") if os.path.exists(get_expanded_path(path.strip()))]
        missing_files = [get_expanded_path(path.strip()) for path in args.ids_files.split(",") if not os.path.exists(get_expanded_path(path.strip()))]

        for path in missing_files:
            print(red(f"[!] File {path} not found. Skipping"))

        if len(existing_files) == 0:
            print(red("[!] No collaboration ids file path provided"))
            exit(1)

        if len(existing_files) == 1:
            print(red("[!] Ids from at least 2 hunters are mandatory"))
            exit(1)

        try:
            data = load_json_files(existing_files)
            results, total_users = analyze_common_ids(data)
            display_collaborations(results, total_users, private_invitations)
        except json.JSONDecodeError as e:
            print(red(f"Error: Invalid JSON in one of the files: {e}"))
            exit(1)
        except Exception as e:
            print(red(f"Error: {e}"))
            exit(1)

    # Displays programs name & slugs as table
    elif args.get_progs:
        data = extract_programs_list(private_invitations, args.silent)

        print()
        results = PrettyTable(field_names=["Name", "Slug"])
        results.add_rows(data)
        results.align = "l"
        print("\n")
        print(results)

    # Extract program scopes to files (json or plain text)
    elif args.extract_scopes:
        program = args.program if args.program else "ALL"
        scope_data = extract_programs_scopes(private_invitations, program, args.silent)

        output_file = args.output if args.output else "data.json"
        if args.format == "json":
            with open(output_file, "w") as f:
                json.dump(scope_data, f, indent=4)
            print(green(f"[+] Data saved to {output_file}"))
            
        elif args.format == "plain":
            print(orange(f" * Web scope : {len(scope_data['web'])}"))
            with open("scope_web.txt", "w") as f:
                f.write("\n".join(scope_data['web'])) 

            print(orange(f" * Wildcards scope : {len(scope_data['wildcard'])}"))
            with open("scope_wildcard.txt", "w") as f:
                f.write("\n".join(scope_data['wildcard'])) 

            print(orange(f" * IPs scope : {len(scope_data['ip'])}"))
            with open("scope_ip.txt", "w") as f:
                f.write("\n".join(scope_data['ip']))

            print(orange(f" * Mobile scope : {len(scope_data['mobile'])}"))
            with open("scope_mobile.txt", "w") as f:
                f.write("\n".join(scope_data['mobile']))

            print(orange(f" * Misc scope : {len(scope_data['misc'])}"))
            with open("scope_misc.txt", "w") as f:
                f.write("\n".join(scope_data['misc']))

    # Display all programs info as table
    elif args.show:
        data = extract_programs_info(private_invitations, args.silent)

        results = PrettyTable(field_names=["Pts", "Name", "Creation date", "Last update", "Last hacktivity", "VPN", "Scopes", "Wildcard", "Reports", "Reports/scope", "Last 24h reports", "Last 7d reports", "Last 1m reports", "My reports", "HoF", "Credz"])
        results.add_rows(data)
        results.align = "c"
        results.align["Name"] = "l"
        
        print("\n\n")
        print(results)

    elif args.find_by_scope:
        pass

    else:
        print(red("[>] Options required !"))
        parser.print_usage()


if __name__ == "__main__":
    main()
