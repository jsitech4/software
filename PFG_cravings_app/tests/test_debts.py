"""Debt ledger integration checks run against an isolated SQLite database."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

def test_debt_carryover_partial_settlement_and_reports():
    data_dir=tempfile.mkdtemp(prefix='pfg-cravings-debt-test-')
    code='''
from fastapi.testclient import TestClient
from app.main import app
from app.db import connect
from app.security import hash_secret,timestamp
client=TestClient(app)
db=connect();db.execute("INSERT INTO admins(username,password_hash,created_at) VALUES(?,?,?)",('seller',hash_secret('VeryLongTestPassword!'),timestamp()));db.close()
login=client.post('/api/admin/login',json={'username':'seller','password':'VeryLongTestPassword!'});assert login.status_code==200
h={'x-csrf-token':login.json()['csrf']}
staff=client.post('/api/admin/staff',headers=h,json={'full_name':'Debt Staff','pin':'0001'}).json();sid=staff['id']
product=client.get('/api/public/bootstrap').json()['products'][0]
assert client.patch('/api/admin/products/'+str(product['id']),headers=h,json={'name':product['name'],'category_id':product['category_id'],'price_naira':'10.00','available':True}).status_code==200
assert client.post('/api/admin/sessions',headers=h,json={}).status_code==200
first=client.post('/api/public/orders',json={'staff_id':sid,'pin':'0001','items':[{'product_id':product['id'],'quantity':1}],'request_key':'debt-order-first'}).json()
assert first['debt_summary']['previous_outstanding_kobo']==0 and first['debt_summary']['outstanding_after_kobo']==1000
assert client.post('/api/public/account-summary',json={'staff_id':sid,'pin':'9999'}).status_code==401
assert client.post('/api/public/account-summary',json={'staff_id':sid,'pin':'0001'}).json()['outstanding_kobo']==1000
session=client.get('/api/admin/sessions').json()[0]['id'];assert client.patch('/api/admin/sessions/'+str(session),headers=h,json={'status':'closed'}).status_code==200
assert client.post('/api/admin/sessions',headers=h,json={}).status_code==200
second=client.post('/api/public/orders',json={'staff_id':sid,'pin':'0001','items':[{'product_id':product['id'],'quantity':2}],'paid_claimed':True,'request_key':'debt-order-second'}).json()
assert second['debt_summary']['previous_outstanding_kobo']==1000 and second['debt_summary']['outstanding_after_kobo']==3000
debts=client.get('/api/admin/debts',headers=h).json();assert debts['summary']['outstanding_kobo']==3000 and debts['summary']['payment_claims']==1
assert client.patch('/api/admin/orders/'+str(second['id'])+'/payment',headers=h,json={'status':'unpaid','notes':'Claim not received'}).status_code==200
assert client.get('/api/admin/debts/'+str(sid),headers=h).json()['outstanding_kobo']==3000
assert client.patch('/api/admin/orders/'+str(second['id'])+'/payment',headers=h,json={'status':'claimed'}).status_code==200
payment={'amount_naira':'15.00','request_key':'payment-request-01','notes':'Part payment'}
part=client.post('/api/admin/debts/'+str(sid)+'/payments',headers=h,json=payment);assert part.status_code==200 and part.json()['account']['outstanding_kobo']==1500
again=client.post('/api/admin/debts/'+str(sid)+'/payments',headers=h,json=payment);assert again.status_code==200 and again.json()['account']['outstanding_kobo']==1500
detail=client.get('/api/admin/debts/'+str(sid),headers=h).json();assert detail['orders'][0]['outstanding_kobo']==0 and detail['orders'][1]['outstanding_kobo']==1500
settled=client.post('/api/admin/debts/'+str(sid)+'/payments',headers=h,json={'settle_all':True,'request_key':'payment-request-02'});assert settled.status_code==200 and settled.json()['account']['outstanding_kobo']==0
assert client.get('/api/admin/reports/debts.pdf',headers=h).content.startswith(b'%PDF')
assert client.get('/api/admin/reports/statement.pdf?staff_id='+str(sid),headers=h).content.startswith(b'%PDF')
assert client.patch('/api/admin/orders/'+str(first['id'])+'/fulfilment',headers=h,json={'status':'cancelled'}).status_code==409
'''
    env=os.environ.copy();env['PFG_DATA_DIR']=data_dir;env['PFG_ENV']='development'
    result=subprocess.run([sys.executable,'-c',code],cwd=Path(__file__).resolve().parents[1],env=env,capture_output=True,text=True)
    assert result.returncode==0,result.stderr or result.stdout
