import os
import json
from getpass import getpass
from .YesWeHackApi import YesWeHackApi
from .config import YWH_LOCAL_CONFIG, YWH_LOCAL_CONFIG_CREDZ
from .utils import red


def get_credentials():
    
    credentials = {}

    if not YWH_LOCAL_CONFIG_CREDZ.exists():
        YWH_LOCAL_CONFIG.mkdir(parents=True, exist_ok=True)
        
        email = input("Input your ywh email address (stored locally) : ")
        password = getpass("Input your ywh password (stored locally) : ")
        otp_key = getpass("Input your TOTP secret key (stored locally) : ")

        credentials = {"email": email, "password": password, "otp_key": otp_key}

        try:
            with open(YWH_LOCAL_CONFIG_CREDZ, 'w') as f:
                json.dump(credentials, f)
            os.chmod(YWH_LOCAL_CONFIG_CREDZ, 0o600)
            print(f"\n[*] Credentials have been stored in {YWH_LOCAL_CONFIG_CREDZ}.")
        except Exception as e:
            print(red(f"[!] Error saving configuration : {e}"))
            return None

    else:
        try:
            with open(YWH_LOCAL_CONFIG_CREDZ, 'r') as f:
                credentials = json.load(f)
            print(f"[*] Using credentials from {YWH_LOCAL_CONFIG_CREDZ}.")
        except Exception as e:
            print(red(f"[!] Error reading configuration : {e}"))
            return None

    return credentials


def get_token_from_credential():
    credentials = get_credentials()

    if not credentials:
        exit(1)

    api = YesWeHackApi(credentials)

    if len(credentials['otp_key']) > 0:
        api.login_totp()
    else:
        api.login()
    
    return api.token


