"""PFG Cravings - lightweight LAN ordering server."""
import os
import re
import json
import sqlite3
import secrets
import hashlib
import logging
from contextlib import asynccontextmanager
from urllib.parse import quote
from datetime import datetime,timezone,timedelta
from decimal import Decimal,InvalidOperation
from pathlib import Path
from typing import Optional
from fastapi import FastAPI,HTTPException,Depends,Request,Response,UploadFile,File
from fastapi.responses import FileResponse,StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel,Field
from app.db import connect,initialize,SEED,audit,get_open_session,current_session,lagos_date
from app.security import hash_secret,verify_secret,pin_fingerprint,secure_token,token_digest,pin_throttle,admin_throttle,timestamp
from app.config import ROOT,SECURE_COOKIES,PUBLIC_ORIGIN,CORS_ORIGINS,MDNS_ENABLED,PRODUCT_IMAGE_DIR
from app.mdns import MdnsAlias

mdns_alias=MdnsAlias()
@asynccontextmanager
async def lifespan(_app):
    if MDNS_ENABLED:
        try: mdns_alias.start()
        except Exception: logging.getLogger(__name__).warning('Could not start the local mDNS alias.',exc_info=True)
    try:
        yield
    finally:
        mdns_alias.stop()

initialize()
app=FastAPI(title='PFG Cravings',docs_url=None,redoc_url=None,openapi_url=None,lifespan=lifespan)
if CORS_ORIGINS:
    # Browser clients normally use the same origin.  Cross-origin access is
    # opt-in and restricted to an explicit allowlist; never use a wildcard with
    # credentialed administrator cookies.
    app.add_middleware(CORSMiddleware,allow_origins=list(CORS_ORIGINS),allow_credentials=True,
        allow_methods=['GET','POST','PUT','PATCH','DELETE','OPTIONS'],allow_headers=['Content-Type','X-CSRF-Token'],max_age=600)
ASSETS=ROOT/'web'/'assets'
app.mount('/assets',StaticFiles(directory=ASSETS),name='assets')
app.mount('/product-images',StaticFiles(directory=PRODUCT_IMAGE_DIR),name='product-images')

@app.middleware('http')
async def response_protection(request:Request,call_next):
    if request.url.path.startswith('/api/') and request.method not in ('GET','HEAD','OPTIONS') and PUBLIC_ORIGIN:
        origin=request.headers.get('origin','').rstrip('/')
        if origin!=PUBLIC_ORIGIN:
            return Response('Origin not permitted',status_code=403)
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='same-origin'
    response.headers['X-Frame-Options']='DENY'
    response.headers['Permissions-Policy']='camera=(), microphone=(), geolocation=()'
    response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
    if request.url.path.startswith('/api/'):
        response.headers['Cache-Control']='no-store'
    if SECURE_COOKIES:
        response.headers['Strict-Transport-Security']='max-age=31536000; includeSubDomains'
    return response

def get_db():
    db=connect()
    try:yield db
    finally:db.close()

def rowdict(row): return dict(row) if row else None

def require_admin(request:Request):
    token=request.cookies.get('pfg_admin','')
    if not token:raise HTTPException(401,'Please sign in as administrator.')
    db=connect()
    try:
        session=db.execute('SELECT s.*,a.username FROM admin_sessions s JOIN admins a ON a.id=s.admin_id WHERE token_hash=? AND expires_at>?',(token_digest(token),timestamp())).fetchone()
        if not session:raise HTTPException(401,'Administrator session has expired.')
        if request.method not in ('GET','HEAD') and request.headers.get('x-csrf-token')!=session['csrf']:
            raise HTTPException(403,'Security token missing or invalid. Refresh and try again.')
        return {'id':session['admin_id'],'username':session['username'],'csrf':session['csrf']}
    finally:db.close()

def valid_pin(pin): return isinstance(pin,str) and re.fullmatch(r'[0-9]{4}',pin) is not None

def confirm_staff(db,staff_id,pin,ip='unknown'):
    staff=db.execute('SELECT * FROM staff WHERE id=? AND active=1',(staff_id,)).fetchone()
    if not valid_pin(pin) or not staff:
        raise HTTPException(401,'Staff name or PIN is incorrect.')
    key=f'staff:{staff_id}'
    source=f'source:{ip}'
    try:
        pin_throttle.attempt(key,limit=5,window=600)
        pin_throttle.attempt(source,limit=150,window=600)
    except ValueError as e:raise HTTPException(429,str(e))
    if not verify_secret(pin,staff['pin_hash']):raise HTTPException(401,'Staff name or PIN is incorrect.')
    pin_throttle.reset(key)
    return staff

def public_url(path:str)->str:
    return f'{PUBLIC_ORIGIN}{path}' if PUBLIC_ORIGIN else path

def product_rows(db):
    products=[]
    for row in db.execute('SELECT p.*,c.name category FROM products p JOIN categories c ON c.id=p.category_id WHERE p.archived=0 ORDER BY c.sort_order,p.sort_order,p.name'):
        product=dict(row)
        # A server-generated filename is used below, never an administrator
        # supplied path. The static fallback keeps every card visually complete.
        product['image_url']=f"/product-images/{product['image_filename']}" if product.get('image_filename') else '/assets/image-not-available.svg'
        products.append(product)
    return products

def public_session(db):
    s=current_session(db)
    if not s:return {'id':None,'date':lagos_date(),'status':'closed','closes_at':None}
    status='open' if get_open_session(db) and get_open_session(db)['id']==s['id'] else 'closed'
    return {'id':s['id'],'date':s['session_date'],'status':status,'closes_at':s['closes_at']}

def settings(db):return {r['key']:r['value'] for r in db.execute('SELECT key,value FROM settings')}

def order_paid_kobo(db,order_id):
    return db.execute('SELECT COALESCE(SUM(amount_kobo),0) FROM payment_allocations WHERE order_id=?',(order_id,)).fetchone()[0]

def staff_account(db,staff_id):
    staff=db.execute('SELECT id,full_name,active FROM staff WHERE id=?',(staff_id,)).fetchone()
    if not staff: raise HTTPException(404,'Staff member not found.')
    rows=db.execute('''SELECT o.*,COALESCE(SUM(pa.amount_kobo),0) paid_kobo
        FROM orders o LEFT JOIN payment_allocations pa ON pa.order_id=o.id
        WHERE o.staff_id=? AND o.fulfilment_status!='cancelled'
        GROUP BY o.id ORDER BY o.created_at,o.id''',(staff_id,)).fetchall()
    purchases=sum(row['total_kobo'] for row in rows)
    paid=sum(row['paid_kobo'] for row in rows)
    outstanding=purchases-paid
    return {'staff_id':staff['id'],'staff_name':staff['full_name'],'active':bool(staff['active']),
        'total_orders':len(rows),'total_purchases_kobo':purchases,'verified_payments_kobo':paid,
        'outstanding_kobo':outstanding,'last_order_at':rows[-1]['created_at'] if rows else None,
        'orders':[{'id':row['id'],'reference':row['reference'],'total_kobo':row['total_kobo'],'paid_kobo':row['paid_kobo'],'outstanding_kobo':row['total_kobo']-row['paid_kobo'],'payment_status':row['payment_status'],'created_at':row['created_at']} for row in rows]}

def refresh_order_payment_state(db,order_id,admin_id=None):
    order=db.execute('SELECT * FROM orders WHERE id=?',(order_id,)).fetchone()
    paid=order_paid_kobo(db,order_id)
    if paid>order['total_kobo']: raise HTTPException(409,'Recorded payments exceed this order total.')
    if paid==order['total_kobo']:
        db.execute('UPDATE orders SET payment_status=?,verified_at=?,verified_by=?,payment_reverification_required=0,updated_at=? WHERE id=?',('verified',timestamp(),admin_id,timestamp(),order_id))
    elif paid:
        db.execute('UPDATE orders SET payment_status=?,verified_at=NULL,verified_by=NULL,updated_at=? WHERE id=?',('claimed',timestamp(),order_id))
    return paid

def record_payment(db,staff_id,amount_kobo,admin_id,notes='',target_order_id=None,request_key=None):
    if request_key:
        existing=db.execute('SELECT id,staff_id FROM payment_ledger WHERE request_key=?',(request_key,)).fetchone()
        if existing:
            if existing['staff_id']!=staff_id: raise HTTPException(409,'This payment request belongs to another staff member.')
            return existing['id'],[],staff_account(db,staff_id)
    account=staff_account(db,staff_id)
    if amount_kobo<=0 or amount_kobo>account['outstanding_kobo']:
        raise HTTPException(422,'Payment must be greater than zero and no more than the outstanding balance.')
    outstanding=[order for order in account['orders'] if order['outstanding_kobo']>0]
    if target_order_id is not None:
        outstanding=[order for order in outstanding if order['id']==target_order_id]
        if not outstanding: raise HTTPException(422,'The selected order has no outstanding balance for this staff member.')
        if amount_kobo>outstanding[0]['outstanding_kobo']:
            raise HTTPException(422,'A payment targeted to one order cannot exceed that order balance.')
    remaining=amount_kobo;allocations=[]
    for order in outstanding:
        allocated=min(remaining,order['outstanding_kobo'])
        if allocated:
            allocations.append((order['id'],allocated));remaining-=allocated
        if not remaining: break
    if remaining: raise HTTPException(409,'Could not allocate the confirmed payment safely.')
    now=timestamp()
    cur=db.execute('INSERT INTO payment_ledger(staff_id,amount_kobo,verified_by,verified_at,notes,created_at,request_key) VALUES(?,?,?,?,?,?,?)',(staff_id,amount_kobo,admin_id,now,notes.strip(),now,request_key))
    db.executemany('INSERT INTO payment_allocations(payment_id,order_id,amount_kobo) VALUES(?,?,?)',[(cur.lastrowid,order_id,amount) for order_id,amount in allocations])
    for order_id,_ in allocations: refresh_order_payment_state(db,order_id,admin_id)
    audit(db,f'admin:{admin_id}','debt-payment-recorded','staff',staff_id,json.dumps({'payment_id':cur.lastrowid,'amount_kobo':amount_kobo,'allocations':allocations},separators=(',',':')))
    return cur.lastrowid,allocations,staff_account(db,staff_id)

@app.get('/api/health')
def health():return {'ok':True,'application':'PFG Cravings','version':'1.0.0'}

@app.get('/api/public/bootstrap')
def bootstrap(db=Depends(get_db)):
    return {'products':product_rows(db),'categories':[dict(r) for r in db.execute('SELECT * FROM categories ORDER BY sort_order,name')],'staff':[{'id':r['id'],'full_name':r['full_name']} for r in db.execute('SELECT id,full_name FROM staff WHERE active=1 ORDER BY full_name')], 'session':public_session(db),'payment':settings(db),'urls':{'buyer':public_url('/'),'admin':public_url('/admin')}}

class Item(BaseModel):
    product_id:int=Field(ge=1)
    quantity:int=Field(ge=1,le=99)
class OrderRequest(BaseModel):
    staff_id:int=Field(ge=1)
    pin:str
    items:list[Item]=Field(min_length=1,max_length=60)
    notes:str=Field(default='',max_length=400)
    paid_claimed:bool=False
    request_key:str=Field(min_length=8,max_length=90)
class Identity(BaseModel):
    staff_id:int
    pin:str

@app.post('/api/public/verify-identity')
def verify_identity(p:Identity,request:Request,db=Depends(get_db)):
    """Verify a buyer before the browser is allowed to show the catalogue."""
    staff=confirm_staff(db,p.staff_id,p.pin,request.client.host if request.client else 'unknown')
    return {'staff_id':staff['id'],'staff_name':staff['full_name']}

class OrderUpdate(OrderRequest):
    reference:str
class CancelRequest(Identity):
    reference:str


def validated_items(db,items):
    seen=set(); out=[];total=0
    for item in items:
        if item.product_id in seen:raise HTTPException(422,'Remove duplicate product entries.')
        seen.add(item.product_id)
        row=db.execute('SELECT * FROM products WHERE id=? AND archived=0 AND available=1',(item.product_id,)).fetchone()
        if not row:raise HTTPException(409,'One or more products are no longer available.')
        if row['price_kobo'] is None:raise HTTPException(409,'A selected product does not have a price yet.')
        line=row['price_kobo']*item.quantity
        total+=line
        if total>1_000_000_000_00:raise HTTPException(422,'Order amount exceeds the allowed limit.')
        out.append((row['id'],row['name'],row['price_kobo'],item.quantity,line))
    return out,total

def order_details(db,row):
    record=dict(row)
    record['items']=[dict(r) for r in db.execute('SELECT product_id,name_snapshot,unit_kobo,quantity,line_kobo FROM order_items WHERE order_id=? ORDER BY id',(row['id'],))]
    record['staff_name']=db.execute('SELECT full_name FROM staff WHERE id=?',(row['staff_id'],)).fetchone()['full_name']
    record['paid_kobo']=order_paid_kobo(db,row['id'])
    record['outstanding_kobo']=0 if row['fulfilment_status']=='cancelled' else row['total_kobo']-record['paid_kobo']
    # A payment claim is not a receipt.  A buyer receives a receipt only when
    # the full amount has a confirmed ledger allocation.
    record['document_type']='receipt' if (
        row['fulfilment_status']!='cancelled'
        and row['payment_status']=='verified'
        and record['paid_kobo']>=row['total_kobo']
    ) else 'invoice'
    record['receipt_url']=public_url('/order/'+quote(record['reference'],safe=''))
    return record

def order_snapshot(db,row):
    """Return the immutable before-image used for controlled admin amendments."""
    record=dict(row)
    record['items']=[dict(r) for r in db.execute('SELECT product_id,name_snapshot,unit_kobo,quantity,line_kobo FROM order_items WHERE order_id=? ORDER BY id',(row['id'],))]
    return record

@app.post('/api/public/orders',status_code=201)
def submit_order(p:OrderRequest,request:Request,db=Depends(get_db)):
    confirm_staff(db,p.staff_id,p.pin,request.client.host if request.client else 'unknown')
    db.execute('BEGIN IMMEDIATE')
    try:
        past=db.execute('SELECT * FROM orders WHERE request_key=? AND staff_id=?',(p.request_key,p.staff_id)).fetchone()
        if past:
            db.commit();return order_details(db,past)
        previous_outstanding=staff_account(db,p.staff_id)['outstanding_kobo']
        s=get_open_session(db)
        if not s:raise HTTPException(409,'Ordering is currently closed.')
        existing=db.execute("SELECT reference FROM orders WHERE session_id=? AND staff_id=? AND fulfilment_status!='cancelled'",(s['id'],p.staff_id)).fetchone()
        if existing:raise HTTPException(409,f'You already have an order for this session ({existing["reference"]}). Use My Orders to update it.')
        lines,total=validated_items(db,p.items)
        now=timestamp()
        ref='PFG-'+datetime.now(timezone.utc).strftime('%y%m%d')+'-'+secrets.token_hex(3).upper()
        pay='claimed' if p.paid_claimed else 'unpaid'
        cur=db.execute('INSERT INTO orders(reference,session_id,staff_id,request_key,total_kobo,payment_status,fulfilment_status,notes,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)',(ref,s['id'],p.staff_id,p.request_key,total,pay,'submitted',p.notes.strip(),now,now))
        oid=cur.lastrowid
        db.executemany('INSERT INTO order_items(order_id,product_id,name_snapshot,unit_kobo,quantity,line_kobo) VALUES(?,?,?,?,?,?)',[(oid,*line) for line in lines])
        audit(db,'staff:'+str(p.staff_id),'order-created','order',oid)
        db.commit()
        result=order_details(db,db.execute('SELECT * FROM orders WHERE id=?',(oid,)).fetchone())
        result['debt_summary']={'previous_outstanding_kobo':previous_outstanding,'current_order_kobo':total,'outstanding_after_kobo':staff_account(db,p.staff_id)['outstanding_kobo']}
        return result
    except Exception:
        db.rollback();raise

@app.post('/api/public/my-orders')
def my_orders(p:Identity,request:Request,db=Depends(get_db)):
    confirm_staff(db,p.staff_id,p.pin,request.client.host if request.client else 'unknown')
    rows=db.execute('SELECT * FROM orders WHERE staff_id=? ORDER BY id DESC LIMIT 100',(p.staff_id,)).fetchall()
    return [order_details(db,r) for r in rows]

@app.post('/api/public/receipt')
def receipt(p:CancelRequest,request:Request,db=Depends(get_db)):
    confirm_staff(db,p.staff_id,p.pin,request.client.host if request.client else 'unknown')
    row=db.execute('SELECT * FROM orders WHERE reference=? AND staff_id=?',(p.reference,p.staff_id)).fetchone()
    if not row:raise HTTPException(404,'Order not found.')
    result=order_details(db,row)
    account=staff_account(db,p.staff_id)
    result['debt_summary']={'previous_outstanding_kobo':max(0,account['outstanding_kobo']-result['outstanding_kobo']),'current_order_kobo':result['total_kobo'],'outstanding_after_kobo':account['outstanding_kobo']}
    return result

@app.post('/api/public/account-summary')
def account_summary(p:Identity,request:Request,db=Depends(get_db)):
    staff=confirm_staff(db,p.staff_id,p.pin,request.client.host if request.client else 'unknown')
    return staff_account(db,staff['id'])

@app.post('/api/public/orders/update')
def update_order(p:OrderUpdate,request:Request,db=Depends(get_db)):
    confirm_staff(db,p.staff_id,p.pin,request.client.host if request.client else 'unknown')
    db.execute('BEGIN IMMEDIATE')
    try:
        order=db.execute('SELECT * FROM orders WHERE reference=? AND staff_id=?',(p.reference,p.staff_id)).fetchone()
        if not order:raise HTTPException(404,'Order not found.')
        s=get_open_session(db)
        if not s or s['id']!=order['session_id']:raise HTTPException(409,'This ordering session is closed.')
        if order['fulfilment_status'] in ('ready','collected','cancelled') or order['payment_status']=='verified' or order['payment_reverification_required'] or order_paid_kobo(db,order['id']):
            raise HTTPException(409,'This order requires administrator assistance to change.')
        lines,total=validated_items(db,p.items)
        db.execute('DELETE FROM order_items WHERE order_id=?',(order['id'],))
        db.executemany('INSERT INTO order_items(order_id,product_id,name_snapshot,unit_kobo,quantity,line_kobo) VALUES(?,?,?,?,?,?)',[(order['id'],*line) for line in lines])
        db.execute('UPDATE orders SET total_kobo=?,payment_status=?,notes=?,updated_at=? WHERE id=?',(total,'claimed' if p.paid_claimed else 'unpaid',p.notes.strip(),timestamp(),order['id']))
        audit(db,'staff:'+str(p.staff_id),'order-updated','order',order['id'])
        db.commit()
        return order_details(db,db.execute('SELECT * FROM orders WHERE id=?',(order['id'],)).fetchone())
    except Exception:
        db.rollback();raise

@app.post('/api/public/orders/cancel')
def cancel_order(p:CancelRequest,request:Request,db=Depends(get_db)):
    confirm_staff(db,p.staff_id,p.pin,request.client.host if request.client else 'unknown')
    db.execute('BEGIN IMMEDIATE')
    try:
        order=db.execute('SELECT * FROM orders WHERE reference=? AND staff_id=?',(p.reference,p.staff_id)).fetchone()
        s=get_open_session(db)
        if not order:raise HTTPException(404,'Order not found.')
        if not s or s['id']!=order['session_id'] or order['payment_status']=='verified' or order['payment_reverification_required'] or order_paid_kobo(db,order['id']) or order['fulfilment_status']!='submitted':
            raise HTTPException(409,'Contact the administrator to cancel this order.')
        db.execute("UPDATE orders SET fulfilment_status='cancelled',updated_at=? WHERE id=?",(timestamp(),order['id']))
        audit(db,'staff:'+str(p.staff_id),'order-cancelled','order',order['id'])
        db.commit();return {'ok':True}
    except Exception:db.rollback();raise

class Login(BaseModel):
    username:str
    password:str

@app.post('/api/admin/login')
def admin_login(p:Login,request:Request,response:Response,db=Depends(get_db)):
    source=request.client.host if request.client else 'unknown'
    try:admin_throttle.attempt(f'admin:{source}',limit=12,window=600)
    except ValueError as e:raise HTTPException(429,str(e))
    user=db.execute('SELECT * FROM admins WHERE username=?',(p.username.strip(),)).fetchone()
    if not user or not verify_secret(p.password,user['password_hash']):raise HTTPException(401,'Invalid username or password.')
    admin_throttle.reset(f'admin:{source}')
    session_token=secure_token();csrf=secure_token();expire=(datetime.now(timezone.utc)+timedelta(hours=10)).isoformat(timespec='seconds')
    db.execute('DELETE FROM admin_sessions WHERE expires_at<?',(timestamp(),))
    db.execute('INSERT INTO admin_sessions(token_hash,admin_id,csrf,expires_at) VALUES(?,?,?,?)',(token_digest(session_token),user['id'],csrf,expire))
    response.set_cookie('pfg_admin',session_token,max_age=36000,httponly=True,secure=SECURE_COOKIES,samesite='lax',path='/')
    return {'username':user['username'],'csrf':csrf,'admin_url':public_url('/admin')}

@app.get('/api/admin/me')
def admin_me(user=Depends(require_admin)):
    return {'username':user['username'],'csrf':user['csrf']}

@app.post('/api/admin/logout')
def logout(request:Request,response:Response,user=Depends(require_admin),db=Depends(get_db)):
    db.execute('DELETE FROM admin_sessions WHERE token_hash=?',(token_digest(request.cookies.get('pfg_admin','')),))
    response.delete_cookie('pfg_admin',path='/')
    return {'ok':True}

@app.get('/api/admin/overview')
def overview(user=Depends(require_admin),db=Depends(get_db)):
    s=current_session(db);sid=s['id'] if s else -1
    rows=db.execute("SELECT * FROM orders WHERE session_id=? AND fulfilment_status!='cancelled' ORDER BY id DESC",(sid,)).fetchall()
    accounts=[staff_account(db,row['id']) for row in db.execute('SELECT id FROM staff')]
    return {'session':public_session(db),'recent':[order_details(db,r) for r in rows[:12]],
        'stats':{'orders':len(rows),'items':sum(sum(x['quantity'] for x in db.execute('SELECT quantity FROM order_items WHERE order_id=?',(r['id'],))) for r in rows),'expected_kobo':sum(r['total_kobo'] for r in rows),'verified_kobo':sum(r['total_kobo'] for r in rows if r['payment_status']=='verified'),'claimed':sum(r['payment_status']=='claimed' for r in rows),'unpaid':sum(r['payment_status']=='unpaid' for r in rows),'collected':sum(r['fulfilment_status']=='collected' for r in rows),'total_debt_kobo':sum(account['outstanding_kobo'] for account in accounts),'staff_owing':sum(account['outstanding_kobo']>0 for account in accounts)}}

@app.get('/api/admin/orders')
def admin_orders(session_id:Optional[int]=None,start:Optional[str]=None,end:Optional[str]=None,status:Optional[str]=None,q:Optional[str]=None,page:int=1,user=Depends(require_admin),db=Depends(get_db)):
    where=['1=1'];args=[]
    if session_id is not None:where.append('o.session_id=?');args.append(session_id)
    if start:where.append('date(o.created_at,\'+01:00\')>=?');args.append(start)
    if end:where.append('date(o.created_at,\'+01:00\')<=?');args.append(end)
    if status:where.append('(o.payment_status=? OR o.fulfilment_status=?)');args.extend([status,status])
    if q:where.append('(o.reference LIKE ? OR s.full_name LIKE ?)');args.extend(['%'+q+'%']*2)
    sql=' FROM orders o JOIN staff s ON s.id=o.staff_id WHERE '+' AND '.join(where)
    total=db.execute('SELECT COUNT(*)'+sql,args).fetchone()[0]
    rows=db.execute('SELECT o.*'+sql+' ORDER BY o.id DESC LIMIT 25 OFFSET ?',args+[max(0,page-1)*25]).fetchall()
    return {'total':total,'page':max(1,page),'pages':max(1,(total+24)//25),'rows':[order_details(db,r) for r in rows]}

class PaymentChange(BaseModel):
    status:str
    notes:str=Field(default='',max_length=400)
@app.patch('/api/admin/orders/{order_id}/payment')
def admin_payment(order_id:int,p:PaymentChange,user=Depends(require_admin),db=Depends(get_db)):
    if p.status not in ('unpaid','claimed','verified'):raise HTTPException(422,'Invalid payment status.')
    row=db.execute('SELECT * FROM orders WHERE id=?',(order_id,)).fetchone()
    if not row:raise HTTPException(404,'Order not found.')
    if row['fulfilment_status']=='cancelled' and p.status=='verified':raise HTTPException(409,'Cannot verify a cancelled order.')
    paid=order_paid_kobo(db,order_id)
    if paid and p.status!='verified':raise HTTPException(409,'This order has confirmed payment records and cannot be returned to unpaid.')
    if p.status=='verified' and paid<row['total_kobo']:
        db.execute('BEGIN IMMEDIATE')
        try:
            record_payment(db,row['staff_id'],row['total_kobo']-paid,user['id'],p.notes,target_order_id=order_id)
            db.commit()
        except Exception: db.rollback();raise
        return {'ok':True,'message':'Full payment confirmed and allocated to this order.'}
    db.execute('UPDATE orders SET payment_status=?,verified_at=?,verified_by=?,payment_reverification_required=?,updated_at=? WHERE id=?',(p.status,timestamp() if p.status=='verified' else None,user['id'] if p.status=='verified' else None,0 if p.status=='verified' else row['payment_reverification_required'],timestamp(),order_id))
    audit(db,'admin:'+str(user['id']),'payment-'+p.status,'order',order_id,p.notes)
    return {'ok':True}

class FulfilmentChange(BaseModel):status:str
@app.patch('/api/admin/orders/{order_id}/fulfilment')
def admin_fulfilment(order_id:int,p:FulfilmentChange,user=Depends(require_admin),db=Depends(get_db)):
    if p.status not in ('submitted','preparing','ready','collected','cancelled'):raise HTTPException(422,'Invalid fulfilment status.')
    order=db.execute('SELECT * FROM orders WHERE id=?',(order_id,)).fetchone()
    if not order:raise HTTPException(404,'Order not found.')
    if p.status=='cancelled' and order_paid_kobo(db,order_id):raise HTTPException(409,'This order has confirmed payment. Record a refund or reconciliation before cancelling it.')
    if order['fulfilment_status']=='cancelled' and p.status!='cancelled':raise HTTPException(409,'Cancelled orders cannot be restored. Ask staff to submit a new order.')
    db.execute('UPDATE orders SET fulfilment_status=?,updated_at=? WHERE id=?',(p.status,timestamp(),order_id))
    audit(db,'admin:'+str(user['id']),'fulfilment-'+p.status,'order',order_id)
    return {'ok':True}

class AdminOrderEdit(BaseModel):
    items:list[Item]=Field(min_length=1,max_length=60)
    notes:str=Field(default='',max_length=400)
    reverify_payment:bool=False
    reason:str=Field(default='',max_length=300)

@app.put('/api/admin/orders/{order_id}')
def admin_edit_order(order_id:int,p:AdminOrderEdit,user=Depends(require_admin),db=Depends(get_db)):
    """Apply a controlled correction while preserving the former order state.

    If a verified total changes, an explicit acknowledgement is required and
    the payment is returned to ``claimed`` for a fresh seller verification.
    """
    db.execute('BEGIN IMMEDIATE')
    try:
        order=db.execute('SELECT * FROM orders WHERE id=?',(order_id,)).fetchone()
        if not order: raise HTTPException(404,'Order not found.')
        if order['fulfilment_status'] in ('cancelled','collected'):
            raise HTTPException(409,'Cancelled or collected orders cannot be amended.')
        lines,total=validated_items(db,p.items)
        if total<order_paid_kobo(db,order_id):
            raise HTTPException(409,'The amended total cannot be less than payments already confirmed for this order.')
        total_changed=total!=order['total_kobo']
        if order['payment_status']=='verified' and total_changed and not p.reverify_payment:
            raise HTTPException(409,'This order has a verified payment. Confirm that payment must be re-verified before changing its total.')
        previous=order_snapshot(db,order)
        db.execute('INSERT INTO order_revisions(order_id,actor,reason,snapshot_json,created_at) VALUES(?,?,?,?,?)',(
            order_id,f'admin:{user["id"]}',p.reason.strip(),json.dumps(previous,separators=(',',':')),timestamp()))
        db.execute('DELETE FROM order_items WHERE order_id=?',(order_id,))
        db.executemany('INSERT INTO order_items(order_id,product_id,name_snapshot,unit_kobo,quantity,line_kobo) VALUES(?,?,?,?,?,?)',[(order_id,*line) for line in lines])
        payment='claimed' if order['payment_status']=='verified' and total_changed else order['payment_status']
        verified_at=None if payment!='verified' else order['verified_at']
        verified_by=None if payment!='verified' else order['verified_by']
        db.execute('UPDATE orders SET total_kobo=?,notes=?,payment_status=?,verified_at=?,verified_by=?,payment_reverification_required=?,updated_at=? WHERE id=?',(
            total,p.notes.strip(),payment,verified_at,verified_by,1 if payment=='claimed' and order['payment_status']=='verified' and total_changed else order['payment_reverification_required'],timestamp(),order_id))
        action='order-amended-reverification-required' if payment=='claimed' and order['payment_status']=='verified' and total_changed else 'order-amended'
        audit(db,f'admin:{user["id"]}',action,'order',order_id,p.reason)
        db.commit()
        return order_details(db,db.execute('SELECT * FROM orders WHERE id=?',(order_id,)).fetchone())
    except Exception:
        db.rollback()
        raise

@app.get('/api/admin/orders/{order_id}/revisions')
def admin_order_revisions(order_id:int,user=Depends(require_admin),db=Depends(get_db)):
    if not db.execute('SELECT 1 FROM orders WHERE id=?',(order_id,)).fetchone():
        raise HTTPException(404,'Order not found.')
    return [dict(row) for row in db.execute('SELECT id,actor,reason,snapshot_json,created_at FROM order_revisions WHERE order_id=? ORDER BY id DESC',(order_id,))]

@app.get('/api/admin/products')
def all_products(user=Depends(require_admin),db=Depends(get_db)):
    return {'products':product_rows(db),'categories':[dict(r) for r in db.execute('SELECT * FROM categories ORDER BY sort_order')]}

class ProductUpdate(BaseModel):
    name:str=Field(min_length=1,max_length=100)
    category_id:int
    price_naira:Optional[str]=None
    available:bool=True
    sort_order:int=0

MAX_PRODUCT_IMAGE_BYTES=5*1024*1024
IMAGE_TYPES=(
    (b'\x89PNG\r\n\x1a\n','png'),
    (b'\xff\xd8\xff','jpg'),
    (b'RIFF', 'webp'),
)

def product_image_extension(data:bytes):
    """Accept only small, browser-safe raster formats based on file bytes."""
    if data.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'png'
    if data.startswith(b'\xff\xd8\xff'):
        return 'jpg'
    if len(data)>=12 and data.startswith(b'RIFF') and data[8:12]==b'WEBP':
        return 'webp'
    raise HTTPException(415,'Upload a PNG, JPEG, or WebP image.')

def remove_product_image(filename):
    if not filename or not re.fullmatch(r'[a-f0-9]{32}\.(?:png|jpg|webp)',filename):
        return
    try:(PRODUCT_IMAGE_DIR/filename).unlink(missing_ok=True)
    except OSError:logging.getLogger(__name__).warning('Could not remove old product image %s',filename)

def parse_price(text):
    if text is None or text=='':return None
    try:
        d=Decimal(str(text))
        if not d.is_finite() or d<0 or d>Decimal('1000000') or d.as_tuple().exponent < -2:raise ValueError()
        return int(d*100)
    except (InvalidOperation,ValueError,TypeError):raise HTTPException(422,'Provide a valid non-negative price with no more than two decimal places.')

@app.post('/api/admin/products')
def create_product(p:ProductUpdate,user=Depends(require_admin),db=Depends(get_db)):
    if not db.execute('SELECT 1 FROM categories WHERE id=?',(p.category_id,)).fetchone():raise HTTPException(422,'Invalid category.')
    try:
        cur=db.execute('INSERT INTO products(category_id,name,price_kobo,available,sort_order) VALUES(?,?,?,?,?)',(p.category_id,p.name.strip(),parse_price(p.price_naira),int(p.available),p.sort_order))
    except sqlite3.IntegrityError:raise HTTPException(409,'Product already exists in that category.')
    audit(db,'admin:'+str(user['id']),'product-created','product',cur.lastrowid)
    return {'id':cur.lastrowid}

@app.patch('/api/admin/products/{product_id}')
def edit_product(product_id:int,p:ProductUpdate,user=Depends(require_admin),db=Depends(get_db)):
    if not db.execute('SELECT 1 FROM products WHERE id=? AND archived=0',(product_id,)).fetchone():raise HTTPException(404,'Product not found.')
    if not db.execute('SELECT 1 FROM categories WHERE id=?',(p.category_id,)).fetchone():raise HTTPException(422,'Invalid category.')
    try:
        db.execute('UPDATE products SET name=?,category_id=?,price_kobo=?,available=?,sort_order=? WHERE id=?',(p.name.strip(),p.category_id,parse_price(p.price_naira),int(p.available),p.sort_order,product_id))
    except sqlite3.IntegrityError:raise HTTPException(409,'Product name already exists in that category.')
    audit(db,'admin:'+str(user['id']),'product-edited','product',product_id)
    return {'ok':True}

@app.post('/api/admin/products/{product_id}/image')
async def upload_product_image(product_id:int,image:UploadFile=File(...),user=Depends(require_admin),db=Depends(get_db)):
    product=db.execute('SELECT image_filename FROM products WHERE id=? AND archived=0',(product_id,)).fetchone()
    if not product:raise HTTPException(404,'Product not found.')
    data=await image.read(MAX_PRODUCT_IMAGE_BYTES+1)
    if not data:raise HTTPException(422,'Choose an image to upload.')
    if len(data)>MAX_PRODUCT_IMAGE_BYTES:raise HTTPException(413,'Image must be 5 MB or smaller.')
    extension=product_image_extension(data)
    filename=f'{secrets.token_hex(16)}.{extension}'
    temporary=PRODUCT_IMAGE_DIR/f'.{filename}.uploading'
    final=PRODUCT_IMAGE_DIR/filename
    try:
        temporary.write_bytes(data)
        temporary.replace(final)
        db.execute('UPDATE products SET image_filename=? WHERE id=?',(filename,product_id))
    except OSError as exc:
        remove_product_image(filename)
        raise HTTPException(500,'The image could not be saved. Please try again.') from exc
    finally:
        temporary.unlink(missing_ok=True)
        await image.close()
    remove_product_image(product['image_filename'])
    audit(db,'admin:'+str(user['id']),'product-image-uploaded','product',product_id)
    return {'ok':True,'image_url':f'/product-images/{filename}'}

@app.delete('/api/admin/products/{product_id}/image')
def remove_assigned_product_image(product_id:int,user=Depends(require_admin),db=Depends(get_db)):
    product=db.execute('SELECT image_filename FROM products WHERE id=? AND archived=0',(product_id,)).fetchone()
    if not product:raise HTTPException(404,'Product not found.')
    db.execute('UPDATE products SET image_filename=NULL WHERE id=?',(product_id,))
    remove_product_image(product['image_filename'])
    audit(db,'admin:'+str(user['id']),'product-image-removed','product',product_id)
    return {'ok':True,'image_url':'/assets/image-not-available.svg'}

@app.delete('/api/admin/products/{product_id}')
def archive_product(product_id:int,user=Depends(require_admin),db=Depends(get_db)):
    db.execute('UPDATE products SET archived=1,available=0 WHERE id=?',(product_id,))
    audit(db,'admin:'+str(user['id']),'product-archived','product',product_id)
    return {'ok':True}

@app.get('/api/admin/staff')
def admin_staff(user=Depends(require_admin),db=Depends(get_db)):
    return [{'id':r['id'],'full_name':r['full_name'],'active':bool(r['active']),'created_at':r['created_at']} for r in db.execute('SELECT * FROM staff ORDER BY full_name')]

class StaffCreate(BaseModel):
    full_name:str=Field(min_length=2,max_length=100)
    pin:Optional[str]=None

def assign_pin(db,pin,except_staff=None):
    if pin is None:
        for _ in range(60):
            candidate=f'{secrets.randbelow(10000):04d}'
            found=db.execute('SELECT id FROM staff WHERE pin_fingerprint=?',(pin_fingerprint(candidate),)).fetchone()
            if not found or found['id']==except_staff:return candidate
        raise HTTPException(409,'Unable to issue a unique PIN. Try again.')
    if not valid_pin(pin):raise HTTPException(422,'PIN must be exactly four digits.')
    found=db.execute('SELECT id FROM staff WHERE pin_fingerprint=?',(pin_fingerprint(pin),)).fetchone()
    if found and found['id']!=except_staff:raise HTTPException(409,'PIN is already assigned. Choose another.')
    return pin

@app.post('/api/admin/staff')
def create_staff(p:StaffCreate,user=Depends(require_admin),db=Depends(get_db)):
    pin=assign_pin(db,p.pin)
    now=timestamp()
    try:cur=db.execute('INSERT INTO staff(full_name,pin_hash,pin_fingerprint,created_at,updated_at) VALUES(?,?,?,?,?)',(p.full_name.strip(),hash_secret(pin),pin_fingerprint(pin),now,now))
    except sqlite3.IntegrityError:raise HTTPException(409,'Staff name already exists.')
    audit(db,'admin:'+str(user['id']),'staff-created','staff',cur.lastrowid)
    return {'id':cur.lastrowid,'issued_pin':pin}

class ResetPin(BaseModel):pin:Optional[str]=None
@app.post('/api/admin/staff/{staff_id}/reset-pin')
def reset_pin(staff_id:int,p:ResetPin,user=Depends(require_admin),db=Depends(get_db)):
    if not db.execute('SELECT 1 FROM staff WHERE id=?',(staff_id,)).fetchone():raise HTTPException(404,'Staff not found.')
    pin=assign_pin(db,p.pin,staff_id)
    db.execute('UPDATE staff SET pin_hash=?,pin_fingerprint=?,updated_at=? WHERE id=?',(hash_secret(pin),pin_fingerprint(pin),timestamp(),staff_id))
    audit(db,'admin:'+str(user['id']),'pin-reset','staff',staff_id)
    return {'issued_pin':pin}

class StaffStatus(BaseModel):active:bool
@app.patch('/api/admin/staff/{staff_id}')
def set_staff_status(staff_id:int,p:StaffStatus,user=Depends(require_admin),db=Depends(get_db)):
    db.execute('UPDATE staff SET active=?,updated_at=? WHERE id=?',(int(p.active),timestamp(),staff_id))
    audit(db,'admin:'+str(user['id']),'staff-activated' if p.active else 'staff-deactivated','staff',staff_id)
    return {'ok':True}

@app.get('/api/admin/debts')
def admin_debts(q:str='',user=Depends(require_admin),db=Depends(get_db)):
    rows=[]
    for staff in db.execute('SELECT id FROM staff ORDER BY full_name'):
        account=staff_account(db,staff['id'])
        if not q or q.lower() in account['staff_name'].lower(): rows.append(account)
    total=sum(row['outstanding_kobo'] for row in rows)
    claims=db.execute("SELECT COUNT(*) FROM orders WHERE payment_status='claimed' AND fulfilment_status!='cancelled'").fetchone()[0]
    return {'rows':rows,'summary':{'outstanding_kobo':total,'staff_owing':sum(row['outstanding_kobo']>0 for row in rows),'payment_claims':claims,'verified_kobo':sum(row['verified_payments_kobo'] for row in rows),'settled_staff':sum(row['total_orders']>0 and row['outstanding_kobo']==0 for row in rows)}}

@app.get('/api/admin/debts/{staff_id}')
def admin_debt_detail(staff_id:int,user=Depends(require_admin),db=Depends(get_db)):
    account=staff_account(db,staff_id)
    payments=[]
    for payment in db.execute('SELECT * FROM payment_ledger WHERE staff_id=? ORDER BY verified_at DESC,id DESC',(staff_id,)):
        entry=dict(payment)
        entry['allocations']=[dict(row) for row in db.execute('SELECT pa.amount_kobo,o.reference FROM payment_allocations pa JOIN orders o ON o.id=pa.order_id WHERE pa.payment_id=? ORDER BY o.created_at,o.id',(payment['id'],))]
        payments.append(entry)
    account['payments']=payments
    return account

class DebtPayment(BaseModel):
    amount_naira:Optional[str]=None
    settle_all:bool=False
    order_id:Optional[int]=None
    notes:str=Field(default='',max_length=400)
    request_key:Optional[str]=Field(default=None,min_length=8,max_length=90)

@app.post('/api/admin/debts/{staff_id}/payments')
def confirm_debt_payment(staff_id:int,p:DebtPayment,user=Depends(require_admin),db=Depends(get_db)):
    db.execute('BEGIN IMMEDIATE')
    try:
        account=staff_account(db,staff_id)
        amount=account['outstanding_kobo'] if p.settle_all else parse_price(p.amount_naira)
        if amount is None: raise HTTPException(422,'Enter a payment amount or choose settle all.')
        payment_id,allocations,updated=record_payment(db,staff_id,amount,user['id'],p.notes,p.order_id,p.request_key)
        db.commit()
        return {'payment_id':payment_id,'allocations':[{'order_id':order_id,'amount_kobo':allocated} for order_id,allocated in allocations],'account':updated}
    except Exception: db.rollback();raise

@app.get('/api/admin/sessions')
def sessions(user=Depends(require_admin),db=Depends(get_db)):
    return [dict(r) for r in db.execute('SELECT * FROM order_sessions ORDER BY id DESC LIMIT 100')]

class NewSession(BaseModel):
    closes_at:Optional[str]=None
    notes:str=Field(default='',max_length=250)

def validate_deadline(value):
    if not value:return None
    try:
        dt=datetime.fromisoformat(value.replace('Z','+00:00'))
        if dt.tzinfo is None:raise ValueError()
        normalized=dt.astimezone(timezone.utc)
        if normalized<=datetime.now(timezone.utc):raise ValueError()
        return normalized.isoformat(timespec='seconds')
    except ValueError:raise HTTPException(422,'Closing time must be a future date and include its time zone.')

@app.post('/api/admin/sessions')
def create_session(p:NewSession,user=Depends(require_admin),db=Depends(get_db)):
    db.execute('BEGIN IMMEDIATE')
    try:
        db.execute("UPDATE order_sessions SET status='closed' WHERE status='open'")
        now=timestamp()
        cur=db.execute('INSERT INTO order_sessions(session_date,status,closes_at,notes,created_at) VALUES(?,?,?,?,?)',(lagos_date(),'open',validate_deadline(p.closes_at),p.notes.strip(),now))
        audit(db,'admin:'+str(user['id']),'session-created','session',cur.lastrowid)
        db.commit();return {'id':cur.lastrowid}
    except Exception:db.rollback();raise

class SessionUpdate(BaseModel):
    status:str
    closes_at:Optional[str]=None
@app.patch('/api/admin/sessions/{session_id}')
def update_session(session_id:int,p:SessionUpdate,user=Depends(require_admin),db=Depends(get_db)):
    if p.status not in ('open','closed'):raise HTTPException(422,'Invalid session status.')
    if not db.execute('SELECT 1 FROM order_sessions WHERE id=?',(session_id,)).fetchone():raise HTTPException(404,'Session not found.')
    if p.status=='open':
        latest=current_session(db)
        if latest and latest['id']!=session_id:raise HTTPException(409,'Only the latest session can be reopened.')
        active=get_open_session(db)
        if active and active['id']!=session_id:raise HTTPException(409,'Close the active session first.')
    deadline=validate_deadline(p.closes_at) if p.status=='open' and p.closes_at else None
    db.execute('UPDATE order_sessions SET status=?,closes_at=? WHERE id=?',(p.status,deadline,session_id))
    audit(db,'admin:'+str(user['id']),'session-'+p.status,'session',session_id)
    return {'ok':True}

@app.get('/api/admin/settings')
def get_settings(user=Depends(require_admin),db=Depends(get_db)):
    return settings(db)

class SettingsEdit(BaseModel):
    bank_name:str=Field(default='',max_length=100)
    account_name:str=Field(default='',max_length=120)
    account_number:str=Field(default='',max_length=30)
    payment_instructions:str=Field(default='',max_length=500)
    app_subtitle:str=Field(default='Order. Pay. Enjoy.',max_length=120)
@app.put('/api/admin/settings')
def set_settings(p:SettingsEdit,user=Depends(require_admin),db=Depends(get_db)):
    for key,value in p.model_dump().items():
        db.execute('INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',(key,value.strip()))
    audit(db,'admin:'+str(user['id']),'settings-updated','settings','app')
    return {'ok':True}

class ChangePassword(BaseModel):
    current_password:str
    new_password:str=Field(min_length=12,max_length=128)
@app.post('/api/admin/change-password')
def change_password(p:ChangePassword,user=Depends(require_admin),db=Depends(get_db)):
    adm=db.execute('SELECT * FROM admins WHERE id=?',(user['id'],)).fetchone()
    if not verify_secret(p.current_password,adm['password_hash']):raise HTTPException(401,'Current password is incorrect.')
    db.execute('UPDATE admins SET password_hash=? WHERE id=?',(hash_secret(p.new_password),user['id']))
    db.execute('DELETE FROM admin_sessions WHERE admin_id=? AND csrf!=?',(user['id'],user['csrf']))
    audit(db,'admin:'+str(user['id']),'password-changed','admin',user['id'])
    return {'ok':True}

@app.get('/api/admin/reports/{kind}.pdf')
def download_report(kind:str,session_id:Optional[int]=None,start:Optional[str]=None,end:Optional[str]=None,payment_status:Optional[str]=None,fulfilment_status:str='active',staff_id:Optional[int]=None,user=Depends(require_admin),db=Depends(get_db)):
    if kind not in ('orders','shopping','debts','statement'):raise HTTPException(404,'Invalid report type.')
    if kind=='statement' and staff_id is None:raise HTTPException(422,'Choose a staff member for an individual debt statement.')
    if payment_status not in (None,'unpaid','claimed','verified'):raise HTTPException(422,'Invalid payment filter.')
    if fulfilment_status not in ('active','all','submitted','preparing','ready','collected','cancelled'):raise HTTPException(422,'Invalid fulfilment filter.')
    from app.reports import generate_report
    if kind in ('debts','statement'):
        from app.reports import generate_debt_report
        binary,filename=generate_debt_report(db,staff_id if kind=='statement' else None)
    else: binary,filename=generate_report(db,kind,session_id,start,end,payment_status,fulfilment_status)
    return StreamingResponse(iter([binary]),media_type='application/pdf',headers={'Content-Disposition':f'attachment; filename="{filename}"'})

@app.get('/api/admin/audit')
def audit_records(page:int=1,user=Depends(require_admin),db=Depends(get_db)):
    page=max(1,page)
    return [dict(r) for r in db.execute('SELECT * FROM audit ORDER BY id DESC LIMIT 50 OFFSET ?',((page-1)*50,))]

@app.get('/{route:path}',include_in_schema=False)
def webapp(route:str):
    if route.startswith('api/') or route.startswith('assets/'):
        raise HTTPException(404)
    return FileResponse(ROOT/'web'/'index.html',media_type='text/html')
