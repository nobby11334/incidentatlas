"""Fetch public primary statements; retry failed URLs on the next run date."""
import pathlib,json,re,hashlib,urllib.request,urllib.parse,concurrent.futures,threading,time,subprocess,datetime
from lxml import html
BASE=pathlib.Path(__file__).resolve().parents[1]/'source-cache/all-cache';P=BASE/'primary';P.mkdir(parents=True,exist_ok=True)
CHECKED=datetime.datetime.now(datetime.timezone.utc).date().isoformat()
locks={};lock=threading.Lock(); results={};pending={};queued={}
def fetch(url):
 key=hashlib.sha256(url.encode()).hexdigest()[:24];meta=P/(key+'.json');body=P/(key+'.bin');txt=P/(key+'.txt')
 if meta.exists():
  try:
   cached=json.loads(meta.read_text())
   if cached.get('checked')==CHECKED:return url,cached
  except ValueError:pass
 with lock:sem=locks.setdefault(urllib.parse.urlsplit(url).hostname,threading.Semaphore(2))
 try:
  with sem:
   req=urllib.request.Request(url,headers={'User-Agent':'IncidentAtlas-public-source-verification/1.0'})
   with urllib.request.urlopen(req,timeout=25) as r:b=r.read(8_000_000);ct=r.headers.get('content-type','');final=r.url
  body.write_bytes(b)
  if b.startswith(b'%PDF'):
   subprocess.run(['pdftotext','-layout','-nopgbrk',str(body),str(txt)],capture_output=True,timeout=25,check=True);content=txt.read_text();title=''
  elif 'html' in ct or b.lstrip().startswith((b'<',b'<!')):
   doc=html.fromstring(b);titles=doc.xpath('//title/text()');title=titles[0].strip() if titles else ''
   for el in doc.xpath('//script|//style|//nav|//header|//footer|//noscript|//form'):el.drop_tree()
   mains=doc.xpath('//main|//article|//*[@id="main"]|//*[@id="contents"]|//*[@id="content"]');node=max(mains,key=lambda e:len(e.text_content())) if mains else doc
   content=node.text_content();content=re.sub(r'[\t\r ]+',' ',content);txt.write_text(content)
  else:content='';title=''
  valid=len(content)>80 and bool(re.search('不正アクセス|誤送信|誤送付|誤配|漏えい|漏洩|流出|紛失|ランサム|サイバー攻撃|誤廃棄|不正侵入|誤表示|誤掲載|システム障害|サービス停止|マルウェア|ウイルス|改ざん',content))
  result={'url':url,'finalUrl':final,'status':'retrieved' if valid else 'content_unverified','contentType':ct,'sha256':hashlib.sha256(b).hexdigest(),'textFile':txt.name,'title':title,'characters':len(content),'checked':CHECKED}
 except Exception as e:result={'url':url,'status':'failed','error':str(e),'checked':CHECKED}
 tmp=meta.with_suffix('.tmp');tmp.write_text(json.dumps(result,ensure_ascii=False));tmp.replace(meta);return url,result
with concurrent.futures.ThreadPoolExecutor(max_workers=32) as pool:
 while True:
  source=BASE/'details.json'
  try:details=json.loads(source.read_text()) if source.exists() else []
  except json.JSONDecodeError:details=[]
  for d in details:
   for u in d.get('primaryUrls',[]):
    if u not in results and u not in pending:queued[u]=None
  active={}
  for u in pending:
   h=urllib.parse.urlsplit(u).hostname;active[h]=active.get(h,0)+1
  for u in list(queued):
   h=urllib.parse.urlsplit(u).hostname
   if len(pending)<32 and active.get(h,0)<2:
    pending[u]=pool.submit(fetch,u);active[h]=active.get(h,0)+1;queued.pop(u)
  done=[u for u,f in pending.items() if f.done()]
  for u in done:
   url,result=pending.pop(u).result();results[url]=result
  if done:
   (BASE/'primary-status.json').write_text(json.dumps(results,ensure_ascii=False,indent=2));print('primary',len(results),'verified',sum(r['status']=='retrieved' for r in results.values()),'pending',len(pending),'detailPages',len(details),flush=True)
  complete=BASE/'details-complete.json'
  if complete.exists() and len(details)==json.loads(complete.read_text())['expected'] and not pending and not queued:break
  time.sleep(2)
print('primary complete',len(results),flush=True)
