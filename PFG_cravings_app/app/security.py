"""Local authentication helpers. PINs are only a low-assurance anti-impersonation measure."""
import base64
import hashlib
import hmac
import secrets
import time
from collections import defaultdict,deque
from threading import Lock
from app.config import SECRET

N_ITER=260_000

def hash_secret(value: str) -> str:
    salt=secrets.token_bytes(16)
    digest=hashlib.pbkdf2_hmac('sha256',value.encode('utf-8')+SECRET,salt,N_ITER)
    return f'pbkdf2_sha256${N_ITER}${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}'

def verify_secret(value: str, saved: str) -> bool:
    try:
        method,iterations,salt64,digest64=saved.split('$')
        if method!='pbkdf2_sha256': return False
        candidate=hashlib.pbkdf2_hmac('sha256',value.encode('utf-8')+SECRET,base64.b64decode(salt64),int(iterations))
        return hmac.compare_digest(candidate,base64.b64decode(digest64))
    except (ValueError,TypeError):
        return False

def pin_fingerprint(pin: str) -> str:
    return hmac.new(SECRET,b'pfg-pin:'+pin.encode(),hashlib.sha256).hexdigest()

class Throttle:
    def __init__(self):
        self.lock=Lock()
        self.events=defaultdict(deque)
    def attempt(self,key,limit=5,window=900):
        with self.lock:
            now=time.monotonic()
            q=self.events[key]
            while q and q[0] <= now-window: q.popleft()
            if len(q)>=limit:
                raise ValueError('Too many attempts. Try again in a few minutes.')
            q.append(now)
    def reset(self,key):
        with self.lock: self.events.pop(key,None)

pin_throttle=Throttle()
admin_throttle=Throttle()

def secure_token(): return secrets.token_urlsafe(32)
def token_digest(token): return hashlib.sha256(token.encode()).hexdigest()
def timestamp():
    from datetime import datetime,timezone
    return datetime.now(timezone.utc).isoformat(timespec='seconds')
