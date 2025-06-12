import argparse
import json
from colorama import init
import os
from auth import get_token_from_credential
from config import DATASOURCE_MAX_AGE, YWH_PROGS_FILE
from utils import analyze_common_ids, banner, display_programs_info, display_programs_list, display_programs_scopes, get_data_from_ywh, get_date_from, get_expanded_path, load_json_files, display_collaborations, orange, red


if __name__ == "__main__":

    # Init colorama
    init()

    # Arguments
    parser = argparse.ArgumentParser(description='Retrieve all your YesWeHack private info in one place.')
    parser.add_argument('--silent', action='store_true', help='Do not print banner')
    parser.add_argument('--force-refresh', action='store_true', help='Force data refresh')

    auth_group = parser.add_mutually_exclusive_group(required=True)
    auth_group.add_argument('--token', help='Use the YesWeHack authorization bearer for auth')
    auth_group.add_argument('--local-auth', action='store_true', help='Use local credentials for auth')
    auth_group.add_argument('--no-auth', action='store_true', help='Do not authenticate to YWH')

    options_group = parser.add_mutually_exclusive_group(required=True)
    options_group.add_argument('--show', action='store_true', help='Display all programs info')
    options_group.add_argument('--collab-export-ids', action='store_true', help='Export all programs collaboration ids')
    options_group.add_argument('--collaborations', action='store_true', help='Show collaboration programs with other hunters')
    options_group.add_argument('--get-progs', action='store_true', help='Displays programs simple list with slugs')
    options_group.add_argument('--extract-scopes', action='store_true', help='Extract program scopes')

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
        else:
            with open(YWH_PROGS_FILE, 'r') as file:
                private_invitations = json.load(file)

    # Check if user has private programs
    if len(private_invitations) == 0:
        print(red(f"[>] You don't have any private invitations. Go on, bro!"))
        exit(1)

    # Export all programs collaboration ids
    if args.collab_export_ids:
        print(json.dumps({f"{private_invitations[0]['user']['username']}": [pi['program']['pid'] for pi in private_invitations if pi['program']['pid']]}))

    # Show collaboration programs with other hunters
    elif args.collaborations:

        if not args.ids_files:
            print(orange(f"[>] Please, provide other hunters collaboration ids list with option --ids-files \"./user-1.json, /tmp/user2.json\""))
            parser.print_usage()
            exit(1)

        paths = [path.strip() for path in args.ids_files.split(",")]

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

    # Displays programs simple list with slugs
    elif args.get_progs:
        display_programs_list(private_invitations, args.silent)

    # Extract program scopes
    elif args.extract_scopes:
        program = args.program if args.program else "ALL"
        display_programs_scopes(private_invitations, program, args)

    # Display all programs info
    elif args.show:
        display_programs_info(private_invitations, args.silent)

    else:
        print(red("[>] Options required !"))
        parser.print_usage()
