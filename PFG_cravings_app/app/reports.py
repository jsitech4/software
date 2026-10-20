"""True A4 PDF reports generated from persisted orders (not screenshots)."""
from io import BytesIO
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
from collections import defaultdict
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER,TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate,Paragraph,Table,TableStyle,Spacer,KeepTogether
from app.config import DATA_DIR

NAVY=colors.HexColor('#181F63');INK=colors.HexColor('#252B39');SUB=colors.HexColor('#667085');LIGHT=colors.HexColor('#F3F5F9')
def money(kobo):return f'NGN {kobo/100:,.2f}'
def local_time(value):
    try:return datetime.fromisoformat(value).astimezone(ZoneInfo('Africa/Lagos')).strftime('%d %b %Y, %I:%M %p')
    except Exception:return str(value)

def fetch_orders(db,session_id=None,start=None,end=None,payment_status=None,fulfilment_status='active'):
    clauses=['1=1'];args=[]
    if session_id is not None:
        clauses.append('o.session_id=?');args.append(session_id)
    if start:
        clauses.append("date(o.created_at,'+01:00')>=?");args.append(start)
    if end:
        clauses.append("date(o.created_at,'+01:00')<=?");args.append(end)
    if payment_status:
        clauses.append('o.payment_status=?');args.append(payment_status)
    if fulfilment_status=='active':
        clauses.append("o.fulfilment_status!='cancelled'")
    elif fulfilment_status!='all':
        clauses.append('o.fulfilment_status=?');args.append(fulfilment_status)
    rows=db.execute('SELECT o.*,s.full_name staff_name,os.session_date FROM orders o JOIN staff s ON s.id=o.staff_id JOIN order_sessions os ON os.id=o.session_id WHERE '+' AND '.join(clauses)+' ORDER BY o.created_at,o.id',args).fetchall()
    result=[]
    for r in rows:
        data=dict(r)
        data['items']=[dict(i) for i in db.execute('SELECT name_snapshot,quantity,unit_kobo,line_kobo FROM order_items WHERE order_id=? ORDER BY id',(r['id'],))]
        result.append(data)
    return result

def generate_report(db,kind,session_id=None,start=None,end=None,payment_status=None,fulfilment_status='active'):
    rows=fetch_orders(db,session_id,start,end,payment_status,fulfilment_status)
    active=[o for o in rows if o['fulfilment_status']!='cancelled']
    now=datetime.now(ZoneInfo('Africa/Lagos'))
    date_text=f'Session #{session_id}' if session_id else (' to '.join(filter(None,[start,end])) if start or end else 'All dates')
    filters=[date_text]
    if payment_status: filters.append('Payment: '+payment_status.title())
    filters.append('Orders: '+({'active':'Active only (cancelled excluded)','all':'All statuses'}.get(fulfilment_status,fulfilment_status.title())))
    stamp=now.strftime('%Y-%m-%d')
    filename=f'PFG_Cravings_{"Orders" if kind=="orders" else "Shopping_List"}_{stamp}.pdf'
    stream=BytesIO()
    doc=SimpleDocTemplate(stream,pagesize=A4,leftMargin=16*mm,rightMargin=16*mm,topMargin=19*mm,bottomMargin=17*mm,title='PFG Cravings report',author='PFG Cravings')
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Brand',parent=styles['Heading1'],fontName='Helvetica-Bold',fontSize=19,leading=24,textColor=NAVY,spaceAfter=3))
    styles.add(ParagraphStyle(name='ReportTitle',fontName='Helvetica-Bold',fontSize=11,leading=15,textColor=INK,spaceAfter=7))
    styles.add(ParagraphStyle(name='SmallPFG',fontName='Helvetica',fontSize=8,leading=11,textColor=INK))
    styles.add(ParagraphStyle(name='TinyPFG',fontName='Helvetica',fontSize=7,leading=9,textColor=INK,wordWrap='CJK'))
    styles.add(ParagraphStyle(name='SmallWhitePFG',fontName='Helvetica-Bold',fontSize=8,leading=11,textColor=colors.white))
    styles.add(ParagraphStyle(name='SectionPFG',fontName='Helvetica-Bold',fontSize=11,leading=15,textColor=NAVY,spaceBefore=14,spaceAfter=7))
    P=lambda v,style='SmallPFG':Paragraph(escape(str(v)),styles[style])
    story=[P('PFG CRAVINGS','Brand'),P('STAFF ORDER REPORT' if kind=='orders' else 'CONSOLIDATED SHOPPING LIST','ReportTitle'),
           P('Report filter: '+' · '.join(filters)),P('Generated: '+now.strftime('%d %B %Y, %I:%M %p')+' (WAT)'),Spacer(1,10)]
    verified=sum(o['total_kobo'] for o in active if o['payment_status']=='verified')
    total=sum(o['total_kobo'] for o in active)
    qty=sum(i['quantity'] for o in active for i in o['items'])
    summary=[['ACTIVE ORDERS',str(len(active)),'TOTAL ITEMS',str(qty)],['EXPECTED AMOUNT',money(total),'VERIFIED PAYMENT',money(verified)],['OUTSTANDING',money(total-verified),'PENDING CLAIMS',str(sum(o['payment_status']=='claimed' for o in active))]]
    s_table=Table([[P(cell) for cell in r] for r in summary],colWidths=[34*mm,52*mm,38*mm,54*mm],hAlign='LEFT')
    s_table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),LIGHT),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('BOTTOMPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),8),('LINEBELOW',(0,0),(-1,-2),0.5,colors.HexColor('#DCE2EA'))]))
    story.extend([s_table,Spacer(1,12)])
    if kind=='orders':
        head=['#','Staff / Reference','Items / quantities','Total','Payment','Date']
        tabledata=[[P(x,'SmallWhitePFG') for x in head]]
        for idx,o in enumerate(rows,1):
            items='\n'.join(f"{i['name_snapshot']} x{i['quantity']} @ {money(i['unit_kobo'])}" for i in o['items'])
            item_html='<br/>'.join(escape(f"{i['name_snapshot']} x{i['quantity']} @ {money(i['unit_kobo'])}") for i in o['items'])
            tabledata.append([P(idx,'TinyPFG'),Paragraph(escape(o['staff_name'])+'<br/><font color="#667085">'+escape(o['reference'])+'</font>',styles['TinyPFG']),Paragraph(item_html,styles['TinyPFG']),P(money(o['total_kobo']),'TinyPFG'),P(('CANCELLED' if o['fulfilment_status']=='cancelled' else {'verified':'Verified','claimed':'Claimed','unpaid':'Unpaid'}[o['payment_status']]),'TinyPFG'),P(local_time(o['created_at']),'TinyPFG')])
        if not rows:tabledata.append([P('No orders found.'),P(''),P(''),P(''),P(''),P('')])
        widths=[9*mm,42*mm,57*mm,27*mm,19*mm,24*mm]
        story.append(make_table(tabledata,widths))
    else:
        shopping=defaultdict(lambda:{'qty':0,'cost':0})
        for o in active:
            for item in o['items']:
                rec=shopping[item['name_snapshot']];rec['qty']+=item['quantity'];rec['cost']+=item['line_kobo']
        tabledata=[[P(x,'SmallWhitePFG') for x in ['#','Product','Total quantity','Total value']]]
        for i,(name,rec) in enumerate(sorted(shopping.items()),1):
            tabledata.append([P(i),P(name),P(rec['qty']),P(money(rec['cost']))])
        if not shopping:tabledata.append([P('—'),P('No products ordered'),P('0'),P('NGN 0.00')])
        story.append(make_table(tabledata,[16*mm,82*mm,38*mm,42*mm]))
        story.extend([Spacer(1,12),P('Cancelled orders are excluded from this purchasing list.')])
    story.extend([Spacer(1,10),P('Payment declaration is not payment verification. Confirm receipts in the seller dashboard.')])
    def footer(canvas,doc):
        canvas.saveState();w,h=A4
        canvas.setStrokeColor(colors.HexColor('#DCE2EA'));canvas.line(16*mm,14*mm,w-16*mm,14*mm)
        canvas.setFont('Helvetica',7);canvas.setFillColor(SUB)
        canvas.drawString(16*mm,10*mm,'PFG Cravings • Internal report')
        canvas.drawRightString(w-16*mm,10*mm,f'Page {doc.page}')
        canvas.restoreState()
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    raw=stream.getvalue()
    archive=DATA_DIR/'reports'/stamp
    archive.mkdir(parents=True,exist_ok=True)
    (archive/filename).write_bytes(raw)
    return raw,filename

def generate_debt_report(db,staff_id=None):
    """A debt report derives balances from purchases minus ledger allocations."""
    now=datetime.now(ZoneInfo('Africa/Lagos'));stream=BytesIO()
    doc=SimpleDocTemplate(stream,pagesize=A4,leftMargin=16*mm,rightMargin=16*mm,topMargin=19*mm,bottomMargin=17*mm,title='PFG Cravings debt report',author='PFG Cravings')
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='DebtBrand',parent=styles['Heading1'],fontName='Helvetica-Bold',fontSize=19,leading=24,textColor=NAVY,spaceAfter=3))
    styles.add(ParagraphStyle(name='DebtSmall',fontName='Helvetica',fontSize=8,leading=10,textColor=INK))
    styles.add(ParagraphStyle(name='DebtWhite',fontName='Helvetica-Bold',fontSize=8,leading=10,textColor=colors.white))
    P=lambda value,style='DebtSmall':Paragraph(escape(str(value)),styles[style])
    where='AND s.id=?' if staff_id else ''
    args=[staff_id] if staff_id else []
    rows=db.execute('''WITH paid AS (SELECT order_id,SUM(amount_kobo) paid FROM payment_allocations GROUP BY order_id)
        SELECT s.id,s.full_name,COUNT(o.id) orders,COALESCE(SUM(o.total_kobo),0) purchases,COALESCE(SUM(paid.paid),0) payments,MAX(o.created_at) last_order
        FROM staff s LEFT JOIN orders o ON o.staff_id=s.id AND o.fulfilment_status!='cancelled'
        LEFT JOIN paid ON paid.order_id=o.id WHERE 1=1 '''+where+''' GROUP BY s.id ORDER BY s.full_name''',args).fetchall()
    title='STAFF DEBT STATEMENT' if staff_id else 'STAFF OUTSTANDING PAYMENT REPORT'
    story=[P('PFG CRAVINGS','DebtBrand'),P(title,'DebtSmall'),P('Generated: '+now.strftime('%d %B %Y, %I:%M %p')+' (WAT)'),Spacer(1,10)]
    total=sum(row['purchases']-row['payments'] for row in rows)
    story.extend([P('Total outstanding debt: '+money(total),'DebtSmall'),Spacer(1,9)])
    data=[[P(x,'DebtWhite') for x in ['Staff','Orders','Purchases','Verified payments','Outstanding','Last order']]]
    for row in rows:
        data.append([P(row['full_name']),P(row['orders']),P(money(row['purchases'])),P(money(row['payments'])),P(money(row['purchases']-row['payments'])),P(local_time(row['last_order']) if row['last_order'] else '—')])
    if not rows:data.append([P('No staff records found.'),P(''),P(''),P(''),P(''),P('')])
    story.append(make_table(data,[37*mm,16*mm,34*mm,36*mm,31*mm,34*mm]))
    if staff_id:
        orders=db.execute('''WITH paid AS (SELECT order_id,SUM(amount_kobo) paid FROM payment_allocations GROUP BY order_id)
            SELECT o.reference,o.total_kobo,COALESCE(paid.paid,0) paid,o.created_at FROM orders o LEFT JOIN paid ON paid.order_id=o.id WHERE o.staff_id=? AND o.fulfilment_status!='cancelled' ORDER BY o.created_at,o.id''',(staff_id,)).fetchall()
        story.extend([Spacer(1,12),P('Order activity','DebtSmall')])
        activity=[[P(x,'DebtWhite') for x in ['Reference','Order','Verified paid','Remaining','Date']]]
        for row in orders:activity.append([P(row['reference']),P(money(row['total_kobo'])),P(money(row['paid'])),P(money(row['total_kobo']-row['paid'])),P(local_time(row['created_at']))])
        story.append(make_table(activity,[37*mm,35*mm,35*mm,35*mm,46*mm]))
    doc.build(story)
    raw=stream.getvalue();stamp=now.strftime('%Y-%m-%d');filename=f'PFG_Cravings_{"Debt_Statement" if staff_id else "Debt_Report"}_{stamp}.pdf'
    archive=DATA_DIR/'reports'/stamp;archive.mkdir(parents=True,exist_ok=True);(archive/filename).write_bytes(raw)
    return raw,filename

def make_table(data,widths):
    t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('VALIGN',(0,0),(-1,-1),'TOP'),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F7F8FB')]),('LINEBELOW',(0,0),(-1,-1),0.35,colors.HexColor('#E2E5ED')),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
    return t
