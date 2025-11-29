import os
import json
from getpass import getpass
from YesWeHackApi import YesWeHackApi
from config import YWH_LOCAL_CONFIG, YWH_LOCAL_CONFIG_CREDZ
from utils import red


def get_credentials(file_path = None):
    
    credentials = {}

    ## Provided path
    if file_path and os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                credentials = json.load(f)
            print(f"[*] Using credentials from {file_path}.")            
        except Exception as e:
            print(red(f"[!] Error reading configuration : {e}"))
            return None

    ## No local file
    else:
        
        email = input("Input your ywh email address (stored locally) : ")
        password = getpass("Input your ywh password (stored locally) : ")
        otp_key = getpass("Input your TOTP secret key (stored locally) : ")

        credentials = {"email": email, "password": password, "otp_key": otp_key}

        try:
            with open(file_path, 'w') as f:
                json.dump(credentials, f)
            os.chmod(file_path, 0o600)
            print(f"\n[*] Credentials have been stored in {file_path}.")
        except Exception as e:
            print(red(f"[!] Error saving configuration : {e}"))
            return None

    return credentials


def get_token_from_credential(file_path):
    credentials = get_credentials(file_path)

    if not credentials:
        print(red(f"[!] Error, no credentials found"))
        exit(1)

    api = YesWeHackApi(credentials)

    try:
        if len(credentials['otp_key']) > 0:
            api.login_totp()
            return api.token
        else:
            api.login()
            return api.token
    except Exception as e:
        print(red(f"[!] Error, failed to authenticate : {e}"))
        exit(1)
    


