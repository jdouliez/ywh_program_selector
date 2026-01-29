import datetime
import logging
import time
from typing import Dict

import pyotp
import requests

from ywh_program_selector.config import YWH_API
from ywh_program_selector.utils import green

logger = logging.getLogger(__name__)


def singleton(class_):
    """Decorator to implement singleton pattern."""
    instances = {}

    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]

    return getinstance


@singleton
class YesWeHackApi:
    """Client for YesWeHack API authentication."""

    def __init__(self, credentials: Dict[str, str]):
        """
        Initialize the API client.
        
        Args:
            credentials: Dict with 'email', 'password', and 'otp_key' keys
        """
        self.host = YWH_API
        self.sess = requests.Session()
        self.sess.headers.update({"User-Agent": "Hunter is hunting..."})
        self.ttl = 300
        self.username = credentials['email']
        self.password = credentials['password']
        self.otp_key = credentials['otp_key']
        self.token = None

    def _get_otp(self) -> str:
        """Generate current TOTP code."""
        totp = pyotp.TOTP(self.otp_key)
        return totp.now()

    def login_totp(self) -> None:
        """Authenticate using username/password and TOTP."""
        r_login = self.sess.post(
            f"{self.host}/login",
            json={"email": self.username, "password": self.password}
        )
        if r_login.status_code != 200:
            raise Exception("Login with username/password error")

        print(green("[*] Auth with login/password successful"))
        login = r_login.json()
        
        login_otp = self.sess.post(
            f"{self.host}/account/totp",
            json={"code": self._get_otp(), "token": login.get("totp_token")}
        ).json()

        # Retry if TOTP code is invalid (may be expired)
        while login_otp.get("message") == 'Invalid TOTP code':
            logger.warning("Waiting for new TOTP token")
            time.sleep(10)
            login_otp = self.sess.post(
                f"{self.host}/account/totp",
                json={"code": self._get_otp(), "token": login.get("totp_token")}
            ).json()

        print(green("[*] Auth with OTP successful"))
        self.token = login_otp.get("token")

        if not self.token:
            raise Exception("Login with totp error")

        self.ttl = datetime.datetime.now() + datetime.timedelta(seconds=login_otp.get("ttl", 300))
        self.sess.headers.update({"Authorization": f"Bearer {self.token}"})
        print(green("[*] Connected"))

    def login(self) -> None:
        """Authenticate using username/password only (no TOTP)."""
        r_login = self.sess.post(
            f"{self.host}/login",
            json={"email": self.username, "password": self.password}
        )
        if r_login.status_code != 200:
            raise Exception("Login error")

        print(green("[*] Auth with login/password successful"))
        login = r_login.json()
        self.token = login.get("token")
        self.ttl = datetime.datetime.now() + datetime.timedelta(seconds=self.ttl)
        self.sess.headers.update({"Authorization": f"Bearer {self.token}"})
        print(green("[*] Connected"))

 