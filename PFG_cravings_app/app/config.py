import os
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent

def load_env():
    file = ROOT / '.env'
    if file.exists():
        for line in file.read_text(encoding='utf-8').splitlines():
            line=line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            name,value=line.split('=',1)
            os.environ.setdefault(name.strip(), value.strip().strip('"').strip("'"))

load_env()

ENVIRONMENT=os.getenv('PFG_ENV','development').strip().lower()
if ENVIRONMENT not in ('development','production'):
    raise RuntimeError('PFG_ENV must be development or production.')

def normalize_origin(value:str)->str:
    """Validate one browser origin; paths and credentials are never valid here."""
    value=value.strip().rstrip('/')
    if not value:
        return ''
    parsed=urlparse(value)
    if parsed.scheme not in ('http','https') or not parsed.netloc or parsed.path or parsed.params or parsed.query or parsed.fragment or parsed.username or parsed.password:
        raise RuntimeError('PFG_PUBLIC_ORIGIN must be an origin such as https://pfgcravings.com.')
    return value

PUBLIC_ORIGIN=normalize_origin(os.getenv('PFG_PUBLIC_ORIGIN',''))
SECURE_COOKIES=os.getenv('PFG_SECURE_COOKIES','1' if ENVIRONMENT=='production' else '0')=='1'
CORS_ORIGINS=tuple(normalize_origin(origin) for origin in os.getenv('PFG_CORS_ORIGINS','').split(',') if origin.strip())
FORWARDED_ALLOW_IPS=os.getenv('PFG_FORWARDED_ALLOW_IPS','127.0.0.1')
MDNS_ENABLED=os.getenv('PFG_MDNS_ENABLED','0')=='1'
MDNS_HOSTNAME=os.getenv('PFG_MDNS_HOSTNAME','pfgcravings.local').strip().lower().rstrip('.')
MDNS_ADDRESS=os.getenv('PFG_MDNS_ADDRESS','').strip()

if ENVIRONMENT=='production':
    if PUBLIC_ORIGIN!='https://pfgcravings.com':
        raise RuntimeError('Production requires PFG_PUBLIC_ORIGIN=https://pfgcravings.com.')
    if not SECURE_COOKIES:
        raise RuntimeError('Production requires PFG_SECURE_COOKIES=1.')
    if PUBLIC_ORIGIN not in CORS_ORIGINS:
        raise RuntimeError('Production requires PFG_CORS_ORIGINS to include PFG_PUBLIC_ORIGIN.')

DATA_DIR = Path(os.getenv('PFG_DATA_DIR', str(ROOT / 'PFG_CRAVINGS_DATA'))).expanduser().resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)
for folder in ('database','backups','reports','logs'):
    (DATA_DIR / folder).mkdir(parents=True, exist_ok=True)
DB_FILE=DATA_DIR / 'database' / 'cravings.sqlite3'
SECRET_FILE=DATA_DIR / '.server_key'
if not SECRET_FILE.exists():
    import secrets
    try:
        with SECRET_FILE.open('x',encoding='utf-8') as file:
            file.write(secrets.token_hex(32))
        try: SECRET_FILE.chmod(0o600)
        except OSError: pass
    except FileExistsError: pass
SECRET=bytes.fromhex(SECRET_FILE.read_text(encoding='utf-8').strip())
