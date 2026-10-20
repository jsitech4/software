"""API integration checks use an isolated temporary database."""
import os
import tempfile
import subprocess
import sys
from pathlib import Path
os.environ['PFG_DATA_DIR']=tempfile.mkdtemp(prefix='pfg-cravings-test-')
os.environ['PFG_MDNS_ENABLED']='0'
from fastapi.testclient import TestClient
from app.main import app
from app.db import connect
from app.reports import fetch_orders
from app.security import hash_secret,timestamp

client=TestClient(app)

def run():
    boot=client.get('/api/public/bootstrap').json()
    assert len(boot['products'])==19
    assert any(category['name']=='Others' for category in boot['categories'])
    assert boot['staff']==[]
    assert boot['session']['status']=='closed'
    assert client.get('/api/admin/orders').status_code==401
    db=connect()
    db.execute('INSERT INTO admins(username,password_hash,created_at) VALUES(?,?,?)',('manager',hash_secret('VeryLongTestPassword!'),timestamp()))
    db.close()
    assert client.post('/api/admin/login',json={'username':'manager','password':'bad'}).status_code==401
    login=client.post('/api/admin/login',json={'username':'manager','password':'VeryLongTestPassword!'})
    assert login.status_code==200,login.text
    csrf=login.json()['csrf'];h={'x-csrf-token':csrf}
    assert client.get('/api/admin/me').status_code==200
    assert client.post('/api/admin/staff',json={'full_name':'Raymond','pin':'0007'}).status_code==403
    staff=client.post('/api/admin/staff',headers=h,json={'full_name':'Raymond','pin':'0007'})
    assert staff.status_code==200,staff.text
    sid=staff.json()['id'];assert staff.json()['issued_pin']=='0007'
    assert client.get('/api/public/bootstrap').json()['staff'][0]['full_name']=='Raymond'
    assert client.post('/api/public/verify-identity',json={'staff_id':sid,'pin':'0008'}).status_code==401
    verified=client.post('/api/public/verify-identity',json={'staff_id':sid,'pin':'0007'})
    assert verified.status_code==200 and verified.json()['staff_name']=='Raymond'
    p=boot['products'][0]
    product={'name':p['name'],'category_id':p['category_id'],'price_naira':'400.00','available':True}
    changed=client.patch(f'/api/admin/products/{p["id"]}',headers=h,json=product)
    assert changed.status_code==200,changed.text
    assert client.post('/api/admin/sessions',headers=h,json={}).status_code==200
    request={'staff_id':sid,'pin':'0007','items':[{'product_id':p['id'],'quantity':2}],'notes':'Cold please','paid_claimed':True,'request_key':'stable-request-00000001'}
    bad=client.post('/api/public/orders',json={**request,'pin':'0008','request_key':'stable-000002'})
    assert bad.status_code==401
    created=client.post('/api/public/orders',json=request)
    assert created.status_code==201,created.text
    o=created.json();assert o['total_kobo']==80000;assert o['payment_status']=='claimed';assert o['staff_name']=='Raymond';assert o['receipt_url']==f'/order/{o["reference"]}'
    assert o['document_type']=='invoice'
    assert len(o['items'])==1
    idem=client.post('/api/public/orders',json=request)
    assert idem.status_code==201 and idem.json()['reference']==o['reference']
    duplicate=client.post('/api/public/orders',json={**request,'request_key':'stable-request-00000002'})
    assert duplicate.status_code==409
    private=client.post('/api/public/my-orders',json={'staff_id':sid,'pin':'0007'})
    assert private.status_code==200 and private.json()[0]['reference']==o['reference']
    receipt=client.post('/api/public/receipt',json={'staff_id':sid,'pin':'0007','reference':o['reference']})
    assert receipt.status_code==200
    assert receipt.json()['document_type']=='invoice'
    assert client.post('/api/public/receipt',json={'staff_id':sid,'pin':'0007','reference':'fake'}).status_code==404
    changed=client.patch(f'/api/admin/products/{p["id"]}',headers=h,json={**product,'price_naira':'500'})
    assert changed.status_code==200
    assert client.post('/api/public/my-orders',json={'staff_id':sid,'pin':'0007'}).json()[0]['total_kobo']==80000
    orders=client.get('/api/admin/orders').json();assert orders['total']==1
    assert client.patch(f'/api/admin/orders/{o["id"]}/payment',headers=h,json={'status':'verified'}).status_code==200
    assert client.post('/api/public/receipt',json={'staff_id':sid,'pin':'0007','reference':o['reference']}).json()['document_type']=='receipt'
    assert client.get('/api/admin/overview').json()['stats']['verified_kobo']==80000
    amend={'items':[{'product_id':p['id'],'quantity':3}],'notes':'Seller correction','reason':'Quantity corrected after review'}
    assert client.put(f'/api/admin/orders/{o["id"]}',headers=h,json=amend).status_code==409
    amended=client.put(f'/api/admin/orders/{o["id"]}',headers=h,json={**amend,'reverify_payment':True})
    assert amended.status_code==200,amended.text
    assert amended.json()['total_kobo']==150000 and amended.json()['payment_status']=='claimed'
    revisions=client.get(f'/api/admin/orders/{o["id"]}/revisions').json()
    assert len(revisions)==1 and '80000' in revisions[0]['snapshot_json']
    assert client.post('/api/public/orders/update',json={**request,'reference':o['reference'],'request_key':'stable-request-00000003'}).status_code==409
    pdf=client.get('/api/admin/reports/orders.pdf')
    assert pdf.status_code==200, pdf.text[:200] if pdf.status_code!=200 else ''
    assert pdf.content.startswith(b'%PDF') and len(pdf.content)>1500
    shopping=client.get('/api/admin/reports/shopping.pdf')
    assert shopping.status_code==200 and shopping.content.startswith(b'%PDF')
    catalogue=client.get('/api/admin/products',headers=h).json()
    assert any(category['name']=='Others' for category in catalogue['categories'])
    extra_staff=client.post('/api/admin/staff',headers=h,json={'full_name':'Cancelled Order','pin':'1234'}).json()
    cancelled=client.post('/api/public/orders',json={**request,'staff_id':extra_staff['id'],'pin':'1234','request_key':'stable-request-cancelled'}).json()
    assert client.patch(f'/api/admin/orders/{cancelled["id"]}/fulfilment',headers=h,json={'status':'cancelled'}).status_code==200
    db=connect()
    assert all(row['fulfilment_status']!='cancelled' for row in fetch_orders(db))
    assert [row['id'] for row in fetch_orders(db,fulfilment_status='cancelled')]==[cancelled['id']]
    db.close()
    db=connect();session=db.execute('SELECT id FROM order_sessions ORDER BY id DESC LIMIT 1').fetchone()['id'];db.close()
    assert client.patch(f'/api/admin/sessions/{session}',headers=h,json={'status':'closed'}).status_code==200
    assert client.get('/api/public/bootstrap').json()['session']['status']=='closed'
    assert client.post('/api/public/orders',json={**request,'request_key':'stable-request-00000004'}).status_code==409
    assert client.post('/api/admin/logout',headers=h).status_code==200
    assert client.get('/api/admin/overview').status_code==401


def test_full_order_to_pdf_workflow():run()

def test_production_domain_configuration_is_https_aware():
    data_dir=tempfile.mkdtemp(prefix='pfg-cravings-production-test-')
    code='''
from fastapi.testclient import TestClient
from app.main import app
from app.db import connect
from app.security import hash_secret, timestamp
client=TestClient(app, base_url="https://pfgcravings.com")
boot=client.get("/api/public/bootstrap").json()
assert boot["urls"]=={"buyer":"https://pfgcravings.com/","admin":"https://pfgcravings.com/admin"}
assert client.get("/").status_code==200
assert client.get("/admin").status_code==200
allowed=client.get("/api/health",headers={"Origin":"https://pfgcravings.com"})
assert allowed.headers["access-control-allow-origin"]=="https://pfgcravings.com"
assert client.post("/api/public/orders",headers={"Origin":"https://invalid.example"},json={}).status_code==403
db=connect()
db.execute("INSERT INTO admins(username,password_hash,created_at) VALUES(?,?,?)",("domain-admin",hash_secret("VeryLongTestPassword!"),timestamp()))
db.close()
login=client.post("/api/admin/login",headers={"Origin":"https://pfgcravings.com"},json={"username":"domain-admin","password":"VeryLongTestPassword!"})
assert login.status_code==200
cookie=login.headers["set-cookie"].lower()
assert "secure" in cookie and "httponly" in cookie and "samesite=lax" in cookie
assert "max-age=31536000" in login.headers["strict-transport-security"]
assert login.json()["admin_url"]=="https://pfgcravings.com/admin"
'''
    env=os.environ.copy()
    env.update({'PFG_ENV':'production','PFG_DATA_DIR':data_dir,'PFG_PUBLIC_ORIGIN':'https://pfgcravings.com','PFG_CORS_ORIGINS':'https://pfgcravings.com','PFG_SECURE_COOKIES':'1'})
    completed=subprocess.run([sys.executable,'-c',code],cwd=Path(__file__).resolve().parents[1],env=env,capture_output=True,text=True)
    assert completed.returncode==0,completed.stderr or completed.stdout
