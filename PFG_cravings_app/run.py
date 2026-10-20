"""Start PFG Cravings on the configured local interface and port."""
import os
import uvicorn
from app.config import load_env,FORWARDED_ALLOW_IPS
load_env()
if __name__=='__main__':
    host=os.getenv('PFG_HOST','0.0.0.0')
    port=int(os.getenv('PFG_PORT','8000'))
    uvicorn.run('app.main:app',host=host,port=port,log_level='info',proxy_headers=True,forwarded_allow_ips=FORWARDED_ALLOW_IPS)
