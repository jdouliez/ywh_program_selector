import argparse
import json
from colorama import init
import os
from config import DATASOURCE_MAX_AGE, YWH_PROGS_FILE
from utils import banner, display, get_data_from_ywh, get_date_from


if __name__ == "__main__":

    # Init colorama
    init()

    # Arguments
    parser = argparse.ArgumentParser(description='Retrieve all your YesWeHack private info in one place.')
    parser.add_argument('--token', help='The YesWeHack authorization bearer', required=True)
    parser.add_argument('--silent', action='store_true', help='Do not print banner')
    parser.add_argument('--collab-export-ids', action='store_true', help='Export all program collaboration ids')

    
    args = parser.parse_args()


    if not args.silent:
        # Print banner because it's cool
        banner()

    if not os.path.exists(YWH_PROGS_FILE):
        print("[!] Local datasource does not exist. Fetching data")
        private_invitations = get_data_from_ywh(args.token)
    else:
        file_mtime = os.path.getmtime(YWH_PROGS_FILE)
        age_in_days = get_date_from(file_mtime)
        if age_in_days > DATASOURCE_MAX_AGE:
            print("[!] Local datasource is outdated. Fetching fresh data")
            private_invitations = get_data_from_ywh(args.token)
        else:
            with open(YWH_PROGS_FILE, 'r') as file:
                private_invitations = json.load(file)

    if len(private_invitations) == 0:
            print(f"[>] You don't have any private invitation. Keep going bro !")
            exit(1)

    if args.collab_export_ids:
        print(json.dumps({f"{private_invitations[0]['user']['username']}": [pi['program']['pid'] for pi in private_invitations if pi['program']['pid']]}))
    else:
        # Display programs info
        display(private_invitations)