import os
import json
from getpass import getpass
from .YesWeHackApi import YesWeHackApi
from .config import YWH_LOCAL_CONFIG_CREDZ
from .display import red


def get_credentials(file_path=None):
    """
    Load or create credentials for YesWeHack authentication.
    
    Args:
        file_path: Path to credentials file. Defaults to YWH_LOCAL_CONFIG_CREDZ.
    
    Returns:
        dict: Credentials dictionary with email, password, and otp_key.
    """
    credentials = {}
    
    # Default to standard config path if not provided
    if file_path is None:
        file_path = YWH_LOCAL_CONFIG_CREDZ

    # Load existing credentials
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                credentials = json.load(f)
            print(f"[*] Using credentials from {file_path}.")
            return credentials
        except json.JSONDecodeError as e:
            print(red(f"[!] Error parsing credentials JSON: {e}"))
            return None
        except IOError as e:
            print(red(f"[!] Error reading configuration: {e}"))
            return None

    # Create new credentials interactively
    email = input("Input your ywh email address (stored locally) : ")
    password = getpass("Input your ywh password (stored locally) : ")
    otp_key = getpass("Input your TOTP secret key (stored locally) : ")

    credentials = {"email": email, "password": password, "otp_key": otp_key}

    try:
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(credentials, f)
        os.chmod(file_path, 0o600)
        print(f"\n[*] Credentials have been stored in {file_path}.")
    except IOError as e:
        print(red(f"[!] Error saving configuration: {e}"))
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
    


