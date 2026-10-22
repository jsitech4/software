"""SQLite connection, idempotent setup and initial unpriced catalogue."""
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo
from app.config import DB_FILE

SEED={
'Drinks':['Pepsi','7Up','Teem','Fanta','Coca-Cola','American Cola','Maltina','Zobo','Nutrimilk','Table Water'],
'Snacks':['Buns','Egg Buns','Chin Chin','Plantain'],
'Biscuits':['Fab','Coaster','Top','Shortbread','Munchit'],
'Others':[]}

def connect():
    conn=sqlite3.connect(str(DB_FILE), timeout=15, isolation_level=None)
    conn.row_factory=sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA busy_timeout=15000')
    return conn

def initialize():
    db=connect()
    # Keep upgrades explicit.  The initial CREATE statements remain idempotent so
    # installations from earlier preview builds are brought up safely as well.
    db.execute('CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)')
    db.executescript('''
    CREATE TABLE IF NOT EXISTS admins (id INTEGER PRIMARY KEY,username TEXT NOT NULL UNIQUE,password_hash TEXT NOT NULL,created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS admin_sessions(token_hash TEXT PRIMARY KEY,admin_id INTEGER NOT NULL REFERENCES admins(id) ON DELETE CASCADE,csrf TEXT NOT NULL,expires_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS staff (id INTEGER PRIMARY KEY,full_name TEXT NOT NULL COLLATE NOCASE UNIQUE,pin_hash TEXT NOT NULL,pin_fingerprint TEXT NOT NULL UNIQUE,active INTEGER NOT NULL DEFAULT 1,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY,name TEXT NOT NULL UNIQUE,sort_order INTEGER NOT NULL DEFAULT 0);
    CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY,category_id INTEGER NOT NULL REFERENCES categories(id),name TEXT NOT NULL,price_kobo INTEGER CHECK(price_kobo IS NULL OR price_kobo>=0),available INTEGER NOT NULL DEFAULT 1,sort_order INTEGER NOT NULL DEFAULT 0,archived INTEGER NOT NULL DEFAULT 0,UNIQUE(category_id,name));
    CREATE TABLE IF NOT EXISTS order_sessions (id INTEGER PRIMARY KEY,session_date TEXT NOT NULL,status TEXT NOT NULL CHECK(status IN ('open','closed')),closes_at TEXT,notes TEXT NOT NULL DEFAULT '',created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY,reference TEXT NOT NULL UNIQUE,session_id INTEGER NOT NULL REFERENCES order_sessions(id),staff_id INTEGER NOT NULL REFERENCES staff(id),request_key TEXT NOT NULL UNIQUE,total_kobo INTEGER NOT NULL,payment_status TEXT NOT NULL CHECK(payment_status IN ('unpaid','claimed','verified')),fulfilment_status TEXT NOT NULL CHECK(fulfilment_status IN ('submitted','preparing','ready','collected','cancelled')),notes TEXT NOT NULL DEFAULT '',created_at TEXT NOT NULL,updated_at TEXT NOT NULL,verified_at TEXT,verified_by INTEGER REFERENCES admins(id));
    CREATE UNIQUE INDEX IF NOT EXISTS idx_one_active_order ON orders(session_id,staff_id) WHERE fulfilment_status!='cancelled';
    CREATE INDEX IF NOT EXISTS idx_orders_created ON orders(created_at);
    CREATE TABLE IF NOT EXISTS order_items(id INTEGER PRIMARY KEY,order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,product_id INTEGER REFERENCES products(id),name_snapshot TEXT NOT NULL,unit_kobo INTEGER NOT NULL,quantity INTEGER NOT NULL CHECK(quantity>0),line_kobo INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS audit (id INTEGER PRIMARY KEY,actor TEXT NOT NULL,action TEXT NOT NULL,entity TEXT NOT NULL,entity_id TEXT NOT NULL,details TEXT NOT NULL DEFAULT '',created_at TEXT NOT NULL);
    ''')
    if not db.execute('SELECT 1 FROM schema_migrations WHERE version=1').fetchone():
        from app.security import timestamp
        db.execute('INSERT INTO schema_migrations(version,applied_at) VALUES(?,?)',(1,timestamp()))
    # Version 2 preserves an immutable before-image whenever an administrator
    # amends an order.  It is deliberately separate from the compact audit log
    # so historic line-item snapshots can be reviewed without changing orders.
    if not db.execute('SELECT 1 FROM schema_migrations WHERE version=2').fetchone():
        db.execute('''CREATE TABLE IF NOT EXISTS order_revisions (
            id INTEGER PRIMARY KEY,
            order_id INTEGER NOT NULL REFERENCES orders(id),
            actor TEXT NOT NULL,
            reason TEXT NOT NULL DEFAULT '',
            snapshot_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )''')
        db.execute('CREATE INDEX IF NOT EXISTS idx_order_revisions_order ON order_revisions(order_id,id DESC)')
        from app.security import timestamp
        db.execute('INSERT INTO schema_migrations(version,applied_at) VALUES(?,?)',(2,timestamp()))
    if not db.execute('SELECT 1 FROM schema_migrations WHERE version=3').fetchone():
        # A seller amendment of a verified order remains seller-controlled until
        # the revised amount is verified; staff must not undo that safeguard.
        db.execute('ALTER TABLE orders ADD COLUMN payment_reverification_required INTEGER NOT NULL DEFAULT 0')
        from app.security import timestamp
        db.execute('INSERT INTO schema_migrations(version,applied_at) VALUES(?,?)',(3,timestamp()))
    if not db.execute('SELECT 1 FROM schema_migrations WHERE version=4').fetchone():
        # Debt is derived from immutable purchases less ledger allocations.  No
        # editable balance is stored, so a new session can never double-count it.
        db.executescript('''
        CREATE TABLE payment_ledger (
            id INTEGER PRIMARY KEY,
            staff_id INTEGER NOT NULL REFERENCES staff(id),
            amount_kobo INTEGER NOT NULL CHECK(amount_kobo>0),
            source_order_id INTEGER REFERENCES orders(id),
            verified_by INTEGER NOT NULL REFERENCES admins(id),
            verified_at TEXT NOT NULL,
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            UNIQUE(source_order_id)
        );
        CREATE TABLE payment_allocations (
            id INTEGER PRIMARY KEY,
            payment_id INTEGER NOT NULL REFERENCES payment_ledger(id) ON DELETE RESTRICT,
            order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE RESTRICT,
            amount_kobo INTEGER NOT NULL CHECK(amount_kobo>0),
            UNIQUE(payment_id,order_id)
        );
        CREATE INDEX idx_payment_ledger_staff ON payment_ledger(staff_id,verified_at DESC);
        CREATE INDEX idx_payment_allocations_order ON payment_allocations(order_id);
        ''')
        # Previous releases represented a full confirmed order using only its
        # status. Convert those records once so they retain their settled state.
        verified=db.execute("SELECT id,staff_id,total_kobo,verified_by,verified_at,created_at FROM orders WHERE payment_status='verified'").fetchall()
        for order in verified:
            if not order['verified_by']:
                continue
            cur=db.execute('INSERT INTO payment_ledger(staff_id,amount_kobo,source_order_id,verified_by,verified_at,notes,created_at) VALUES(?,?,?,?,?,?,?)',(
                order['staff_id'],order['total_kobo'],order['id'],order['verified_by'],order['verified_at'] or order['created_at'],'Migrated confirmed order payment',order['created_at']))
            db.execute('INSERT INTO payment_allocations(payment_id,order_id,amount_kobo) VALUES(?,?,?)',(cur.lastrowid,order['id'],order['total_kobo']))
        from app.security import timestamp
        db.execute('INSERT INTO schema_migrations(version,applied_at) VALUES(?,?)',(4,timestamp()))
    if not db.execute('SELECT 1 FROM schema_migrations WHERE version=5').fetchone():
        db.execute('ALTER TABLE payment_ledger ADD COLUMN request_key TEXT')
        db.execute('CREATE UNIQUE INDEX idx_payment_ledger_request_key ON payment_ledger(request_key) WHERE request_key IS NOT NULL')
        from app.security import timestamp
        db.execute('INSERT INTO schema_migrations(version,applied_at) VALUES(?,?)',(5,timestamp()))
    if not db.execute('SELECT 1 FROM schema_migrations WHERE version=6').fetchone():
        # Keep the image reference with the product; files themselves live in
        # the persistent data directory rather than inside the deployed source.
        db.execute('ALTER TABLE products ADD COLUMN image_filename TEXT')
        from app.security import timestamp
        db.execute('INSERT INTO schema_migrations(version,applied_at) VALUES(?,?)',(6,timestamp()))
    for index,(category,names) in enumerate(SEED.items()):
        db.execute('INSERT OR IGNORE INTO categories(name,sort_order) VALUES (?,?)',(category,index))
        cat_id=db.execute('SELECT id FROM categories WHERE name=?',(category,)).fetchone()['id']
        for order,name in enumerate(names):
            db.execute('INSERT OR IGNORE INTO products(category_id,name,sort_order) VALUES(?,?,?)',(cat_id,name,order))
    default={'bank_name':'','account_name':'','account_number':'','payment_instructions':'','app_subtitle':'Order. Pay. Enjoy.'}
    for k,v in default.items():db.execute('INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)',(k,v))
    db.close()

def audit(db,actor,action,entity,entity_id,details=''):
    from app.security import timestamp
    db.execute('INSERT INTO audit(actor,action,entity,entity_id,details,created_at) VALUES(?,?,?,?,?,?)',(actor,action,entity,str(entity_id),details[:1000],timestamp()))

def get_open_session(db):
    from app.security import timestamp
    return db.execute("SELECT * FROM order_sessions WHERE status='open' AND (closes_at IS NULL OR closes_at>?) ORDER BY id DESC LIMIT 1",(timestamp(),)).fetchone()

def current_session(db):
    return db.execute('SELECT * FROM order_sessions ORDER BY id DESC LIMIT 1').fetchone()

def lagos_date():return datetime.now(ZoneInfo('Africa/Lagos')).date().isoformat()
