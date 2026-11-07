"""Discover public index facts across years; never turn secondary claims into confirmed incidents.
Only dates, organization identifiers and source links are retained, not article prose.
Pagination failures and unparsed sources remain visible in the durable coverage ledger.
"""
import urllib.error
import concurrent.futures,datetime,hashlib,json,pathlib,re,threading,time,urllib.request,urllib.parse,urllib.robotparser
from lxml import html
ROOT=pathlib.Path(__file__).resolve().parents[1]
CHECKED=datetime.datetime.now(datetime.timezone.utc).isoformat()
P=ROOT/'source-cache/discovery';P.mkdir(parents=True,exist_ok=True)
read=lambda p:json.loads(p.read_text())
ledger=read(ROOT/'dist/reconciliation.json');known={r['key']:r for r in ledger['records']}
catalog=read(ROOT/'sources/discovery-catalog.json');coverage=[];locks={};guard=threading.Lock();robots={}
DATE=re.compile(r'((?:19|20)\d{2})[年/\.\-](\d{1,2})[月/\.\-](\d{1,2})')
SIGNAL=re.compile('漏[洩え]|流出|誤送|紛失|不正アクセス|サイバー攻撃|ランサム|誤配|盗難|情報持ち出し|個人情報|ウイルス|マルウェア')
MEDIA={urllib.parse.urlsplit(s['url']).hostname for s in catalog}
AGENT='IncidentAtlas-public-index-discovery/1.0'
def clean(s):return re.sub(r'\s+',' ',s).strip()
def date(s):
 m=DATE.search(s)
 if not m:return ''
 try:return datetime.date(*map(int,m.groups())).isoformat()
 except ValueError:return ''
def fetch(url):
 host=urllib.parse.urlsplit(url).netloc
 with guard:sem=locks.setdefault(host,threading.Semaphore(2))
 with sem:
  time.sleep(.15)
  req=urllib.request.Request(url,headers={'User-Agent':AGENT})
  with urllib.request.urlopen(req,timeout=20) as r:
   b=r.read(8_000_000);ct=r.headers.get('Content-Type','');final=r.url
  if 'html' not in ct and not b.lstrip().startswith(b'<'):raise ValueError('HTML index unavailable')
  return html.fromstring(b,base_url=final)
def permitted(url):
 origin=urllib.parse.urlsplit(url);base=origin.scheme+'://'+origin.netloc
 if base not in robots:
  rp=urllib.robotparser.RobotFileParser(base+'/robots.txt')
  try:
   with urllib.request.urlopen(urllib.request.Request(base+'/robots.txt',headers={'User-Agent':AGENT}),timeout=10) as rr:rp.parse(rr.read(500000).decode('utf-8','replace').splitlines())
   robots[base]=rp
  except urllib.error.HTTPError as e:
   rp.parse(['User-agent: *','Disallow: /'] if e.code in (401,403) else []);robots[base]=rp
  except Exception:robots[base]=None
 rp=robots[base]
 return rp is None or rp.can_fetch(AGENT,url)
def source_links(node,url):
 result=[]
 for a in node.xpath('.//a[@href]'):
  u=urllib.parse.urljoin(url,a.get('href'));host=urllib.parse.urlsplit(u).hostname
  if host and host not in MEDIA and host not in {'twitter.com','x.com','facebook.com','www.facebook.com','www.youtube.com','www.google.com','amzn.to'} and u.startswith(('http://','https://')) and not re.search('google|amazon|doubleclick|affiliate',host):result.append(u.split('#')[0])
 return sorted(set(result))
def add(source,page,org,day,article='',cause='',quantity='',basis='索引記載日（公表・発生・報道の別は未照合）',identity='索引の組織欄'):
 org=clean(org)
 if not org or len(org)>150:return
 discovery=article or page
 key='search-'+hashlib.sha256((source['name']+'|'+org+'|'+day+'|'+discovery+'|'+cause+'|'+quantity).encode()).hexdigest()[:24]
 r=known.get(key,{})
 r.update(key=key,organization=org,published=day,inventory=source['name'],discovery=discovery,primaryUrls=r.get('primaryUrls',[]),dateBasis=basis,identityBasis=identity,result=r.get('result','追加索引発見・一次資料本文の確認待ち'))
 if cause:r['indexCause']=clean(cause)[:100]
 if quantity:r['indexQuantity']=clean(quantity)[:150]
 known[key]=r
 return r

def tables(source,page,doc):
 n=0
 for table in doc.xpath('//table'):
  rows=table.xpath('.//tr');heads=[]
  for row in rows:
   cells=row.xpath('./th|./td');texts=[clean(c.text_content()) for c in cells]
   if any(re.search('法人|団体名|組織名|企業・事件|企業・事故|企業名|会社名|事業者|^事案$',t) for t in texts):heads=texts;continue
   if not heads or len(cells)<2:continue
   find=lambda pat:next((i for i,t in enumerate(heads) if re.search(pat,t)),None)
   oi=find('法人|団体名|組織名|企業・事件|企業・事故|企業名|会社名|事業者|^事案$');di=find('日付|公表日|発表日|発生日');qi=find('件数|人数');ci=find('原因|手口')
   if oi is None or oi>=len(cells):continue
   oc=cells[oi];org=clean(oc.text_content())
   # Combined incident columns often have a separate first organization element.
   if heads[oi] in ('企業・事件','企業・事故','事案'):
    full=clean(oc.text_content());links=oc.xpath('.//a')
    if links:
     headline=clean(links[0].text_content());rest=clean(full.replace(headline,'',1))
     if rest:org=re.split(r'\s*[·・]\s*',rest)[0]
     else:
      children=links[0].xpath('./*[1]')
      org=clean(children[0].text_content()) if children else '組織未特定（索引記事との照合待ち）'
   day=date(texts[di]) if di is not None and di<len(texts) else ''
   if not day and not SIGNAL.search(' '.join(texts)):continue
   r=add(source,page,org,day,cause=texts[ci] if ci is not None and ci<len(texts) else '',quantity=texts[qi] if qi is not None and qi<len(texts) else '')
   if r:
    r['primaryUrls']=sorted(set(r['primaryUrls']+source_links(row,page)));n+=1
 return n

def articles(source,page,doc):
 n=0;seen=set()
 for a in doc.xpath('//a[@href]'):
  title=clean(a.text_content());u=urllib.parse.urljoin(page,a.get('href'))
  if u in seen or not SIGNAL.search(title) or len(title)<8:continue
  if re.search('とは|対策|防止|解説|選び方|セミナー|おすすめ|相談窓口',title):continue
  if urllib.parse.urlsplit(u).hostname!=urllib.parse.urlsplit(page).hostname:continue
  if re.search(r'/category/|/tag/|/page/|#|\?s=',u):continue
  node=a
  for _ in range(4):
   if node.getparent() is None:break
   node=node.getparent()
   if date(node.text_content()):break
  day=date(node.text_content())
  if source.get('adapter')=='security-next':
   day=next((date(t) for t in reversed(a.xpath('preceding::text()')[-50:]) if date(t)),'')
  if not day:continue
  # Secondary article headings identify a candidate only; no headline prose is stored.
  parts=re.split(r'\s+[－—–-]\s+',title)
  org=parts[-1] if len(parts)>1 and not SIGNAL.search(parts[-1]) else '組織未特定（索引記事との照合待ち）'
  if len(org)>80:org='組織未特定（索引記事との照合待ち）'
  r=add(source,page,org,day,article=u,identity='記事見出しから抽出・未照合' if not org.startswith('組織未特定') else '未特定')
  if r:n+=1;seen.add(u)
 return n

def scan(source):
 start=time.monotonic();report=dict(name=source['name'],url=source['url'],checked=CHECKED,pagesAttempted=0,pagesRetrieved=0,rowsParsed=0,errors=[],paginationComplete=False)
 queue=[source['url']];done=set();blocked=False
 while queue:
  batch=[u for u in queue if u not in done];queue=[]
  if not batch:break
  with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
   futures={}
   for u in batch:
    if not permitted(u):report['errors'].append(dict(url=u,error='robots.txt disallows retrieval'));blocked=True;continue
    futures[pool.submit(fetch,u)]=u
   for future in concurrent.futures.as_completed(futures):
    u=futures[future];done.add(u);report['pagesAttempted']+=1
    try:doc=future.result();report['pagesRetrieved']+=1
    except Exception as e:
     report['errors'].append(dict(url=u,error=str(e)[:250]));continue
    got=tables(source,u,doc)
    if not got:got=articles(source,u,doc)
    report['rowsParsed']+=got
    for a in doc.xpath('//a[@href]'):
     dest=urllib.parse.urljoin(u,a.get('href')).split('#')[0]
     if urllib.parse.urlsplit(dest).hostname!=urllib.parse.urlsplit(source['url']).hostname:continue
     if source.get('adapter')!='security-next' and re.search(r'/page/\d+/?(?:\?.*)?$|[?&](?:page|paged)=\d+',dest) and dest not in done:queue.append(dest)
    if source.get('adapter')=='security-next':
     m=re.search(r'全\s*([\d,]+)\s*ページ',doc.text_content())
     if m:
      count=int(m.group(1).replace(',',''));report['expectedPages']=count
      queue.extend(source['url'].rstrip('/')+'/page/'+str(i) for i in range(2,count+1) if source['url'].rstrip('/')+'/page/'+str(i) not in done)
  queue=list(dict.fromkeys(queue))
  print(source['name'],report['pagesRetrieved'],'pages',report['rowsParsed'],'index rows',len(queue),'pages pending',flush=True)
  if report['pagesRetrieved']==0 or blocked:break
 report['paginationComplete']=not queue and not report['errors'] and report['rowsParsed']>0
 report['status']='parsed' if report['rowsParsed'] else 'retrieved_but_unparsed' if report['pagesRetrieved'] else 'retrieval_failed'
 report['durationSeconds']=round(time.monotonic()-start,1)
 report['recordsInLedger']=sum(r['inventory']==source['name'] for r in known.values())
 return report

for source in catalog:
 try:coverage.append(scan(source))
 except Exception as e:coverage.append(dict(name=source['name'],url=source['url'],checked=CHECKED,status='failed',errors=[str(e)]))
 # Save metadata progress after every source. Raw third-party documents are not published.
 (ROOT/'dist/reconciliation.json').write_text(json.dumps(dict(checked=CHECKED[:10],records=list(known.values())),ensure_ascii=False,separators=(',',':')))
 (ROOT/'dist/search-coverage.json').write_text(json.dumps(dict(checked=CHECKED,sources=coverage,catalogSources=len(catalog),searchedQueries=read(ROOT/'sources/search-queries.json')),ensure_ascii=False,separators=(',',':')))
print('Discovery total',len(known),flush=True)
