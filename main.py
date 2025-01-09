import json
from colorama import init
import os
from config import DATASOURCE_MAX_AGE, YWH_PROGS_FILE
from utils import banner, display, get_data_from_ywh, get_date_from


if __name__ == "__main__":

    banner()
    init()

    if not os.path.exists(YWH_PROGS_FILE):
        print("[!] Local datasource does not exist. Fetching data")
        private_invitations = get_data_from_ywh()
    else:
        file_mtime = os.path.getmtime(YWH_PROGS_FILE)
        age_in_days = get_date_from(file_mtime)
        if age_in_days > DATASOURCE_MAX_AGE:
            print("[!] Local datasource is outdated. Fetching fresh data")
            private_invitations = get_data_from_ywh()
        else:
            with open(YWH_PROGS_FILE, 'r') as file:
                private_invitations = json.load(file)

    display(private_invitations)