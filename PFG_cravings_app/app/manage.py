"""Commands: python -m app.manage setup-admin | backup | check."""
import sys
import getpass
from datetime import datetime,timezone
from app.db import connect,initialize
from app.security import hash_secret,timestamp
from app.config import DATA_DIR,DB_FILE

def main():
    initialize()
    command=sys.argv[1] if len(sys.argv)>1 else ''
    if command=='setup-admin':
        db=connect()
        try:
            if db.execute('SELECT COUNT(*) FROM admins').fetchone()[0]:
                print('Administrator already exists. Change password through the admin settings page.');return
            username=input('Administrator username: ').strip()
            if len(username)<3:raise ValueError('Username must contain at least 3 characters.')
            password=getpass.getpass('Choose administrator password (12+ characters): ')
            confirm=getpass.getpass('Confirm password: ')
            if password!=confirm or len(password)<12:raise ValueError('Passwords must match and contain at least 12 characters.')
            db.execute('INSERT INTO admins(username,password_hash,created_at) VALUES(?,?,?)',(username,hash_secret(password),timestamp()))
            print('Administrator created. Sign in at /admin/login.')
        finally:db.close()
    elif command=='backup':
        db=connect();path=DATA_DIR/'backups'/('cravings-'+datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')+'.sqlite3')
        dest=__import__('sqlite3').connect(path)
        try:
            db.backup(dest)
            print('Database safely backed up to:',path)
        finally:dest.close();db.close()
    elif command=='check':
        db=connect()
        try:
            print('Database:',DB_FILE)
            print('Integrity:',db.execute('PRAGMA integrity_check').fetchone()[0])
            print('Products:',db.execute('SELECT COUNT(*) FROM products').fetchone()[0])
        finally:db.close()
    else:
        print('Usage: python -m app.manage setup-admin | backup | check')
        sys.exit(2)

if __name__=='__main__':main()
