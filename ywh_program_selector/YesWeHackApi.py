from logging import Logger, getLogger
import requests, pyotp, datetime, time
from .config import YWH_API
from .utils import green

logger: Logger = getLogger(__name__)    
 
def singleton(class_):
    instances = {}
    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]
    return getinstance
 
 
@singleton
class YesWeHackApi:
 
    def __init__(self, credentials):
        self.host = YWH_API
        self.sess = requests.Session()
        self.sess.headers.update({"User-Agent": "Hunter is hunting..."})
        self.ttl = 300
        self.username = credentials['email']
        self.password = credentials['password']
        self.otp_key = credentials['otp_key']      
 

    def _get_otp(self):
        totp = pyotp.TOTP(self.otp_key)
        return totp.now()
 

    def login_totp(self):
        r_login = self.sess.post(f"{self.host}/login", json={"email": self.username, "password": self.password})
        if r_login.status_code != 200:
            raise Exception("Login with username/password error")
            
        print(green("[*] Auth with login/password successful"))
        login = r_login.json()
        login_otp = self.sess.post(f"{self.host}/account/totp", json={"code": self._get_otp(), "token": login.get("totp_token")}).json()
 
        if login_otp.get("message") == 'Invalid TOTP code':
            while login_otp.get("message") == 'Invalid TOTP code':
                logger.warn("Waiting new token")
                time.sleep(10)
                login_otp = self.sess.post(f"{self.host}/account/totp", json={"code": self._get_otp(), "token": login.get("totp_token")}).json()
 
 
        print(green("[*] Auth with OTP successful"))
        self.token = login_otp.get("token")
        
        if not self.token:
            raise Exception("Login with totp error")
 
        self.ttl = datetime.datetime.now() + datetime.timedelta(seconds=login_otp.get("ttl"))
        self.sess.headers.update({"Authorization": f"Bearer {self.token}"})
        print(green("[*] Connected"))
 

    def login(self):
        r_login = self.sess.post(f"{self.host}/login", json={"email": self.username, "password": self.password})
        if r_login.status_code != 200:
            raise Exception("Login error")
 
        print(green("[*] Auth with login/password successful"))
        login = r_login.json()
        self.token = login.get("token")
        self.ttl = datetime.datetime.now() + datetime.timedelta(seconds=self.ttl)
        self.sess.headers.update({"Authorization": f"Bearer {self.token}"})
        print(green("[*] Connected"))

 