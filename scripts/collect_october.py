import pathlib,json,re,hashlib,urllib.request,urllib.parse,concurrent.futures,threading,time
from lxml import html
BASE=pathlib.Path(__file__).resolve().parents[1]/'source-cache';BASE.mkdir(exist_ok=True);CACHE=BASE/'oct-cache';CACHE.mkdir(exist_ok=True)
def clean(x):return re.sub(r'\s+',' ',x or '').strip()
def text(e):return clean(e.text_content())
for name,url in [('seory','https://incidents.seory.co.jp/monthly/2026-10/'),('radineer','https://radineer.asia/cyber/month/2026-10/')]:
 file=BASE/('oct-'+name+'.html')
 if not file.exists():
  with urllib.request.urlopen(url,timeout=45) as response:file.write_bytes(response.read())
items=[]
# Discovery metadata only; independent facts will be checked against the linked primary publications.
root=html.fromstring((BASE/'oct-seory.html').read_bytes())
for li in root.cssselect('li.ii-item') if False else root.xpath('//li[@class="ii-item"]'):
 a=li.xpath('.//h3/a')[0];date=li.xpath('.//time/@datetime')[0]
 items.append(dict(key='s-'+a.get('href').strip('/').split('/')[-1],discovery='https://incidents.seory.co.jp'+a.get('href'),org=text(a),published=date))
root=html.fromstring((BASE/'oct-radineer.html').read_bytes())
for tr in root.xpath('//tbody[@id="records"]/tr'):
 a=tr.xpath('.//td[contains(@class,"c-org")]/a')[0]
 items.append(dict(key='r-'+tr.get('data-id'),discovery='https://radineer.asia'+a.get('href'),org=text(a),published=tr.xpath('.//time/@datetime')[0]))
items=sorted(items,key=lambda d:(d['published'],d['key'][-6:],d['key'][0]))
(CACHE/'discovery.json').write_text(json.dumps(items,ensure_ascii=False,indent=2));print('discovered',len(items),flush=True)
locks={};lock=threading.Lock()
def fetch(url,path):
 if path.exists():return path.read_bytes(),None
 host=urllib.parse.urlsplit(url).hostname
 with lock:sem=locks.setdefault(host,threading.Semaphore(8))
 try:
  with sem:
   req=urllib.request.Request(url,headers={'User-Agent':'IncidentAtlas-public-source-verification/1.0'})
   with urllib.request.urlopen(req,timeout=30) as r:
    b=r.read(12_000_000)
   path.write_bytes(b);return b,None
 except Exception as e:return None,str(e)
def detail(item):
 b,error=fetch(item['discovery'],CACHE/(item['key']+'.html'));item=dict(item)
 if error:return {**item,'error':error}
 root=html.fromstring(b)
 if item['key'].startswith('s-'):
  links=root.xpath('//ol[contains(@class,"ii-sources")]//a[contains(@class,"ii-ext")]/@href')
  facts={text(x.xpath('./dt')[0]):text(x.xpath('./dd')[0]) for x in root.xpath('//dl[@class="ii-dl"]/div') if x.xpath('./dt') and x.xpath('./dd')}
  item['expected']=facts
 else:
  links=root.xpath('//aside[contains(@class,"sources")]/ol/li/a/@href')
  item['expectedNumbers']=[list(map(text,tr.xpath('./td'))) for tr in root.xpath('//div[@class="detail-grid"]/section/table/tbody/tr')]
 item['primaryUrls']=list(dict.fromkeys(u for u in links if u.startswith(('https://','http://'))))
 return item
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=32) as pool:
 for f in concurrent.futures.as_completed([pool.submit(detail,x) for x in items]):
  results.append(f.result())
  if len(results)%50==0:print('details',len(results),'sources',sum(bool(x.get('primaryUrls')) for x in results),'errors',sum('error' in x for x in results),flush=True);(CACHE/'details.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
(CACHE/'details.json').write_text(json.dumps(results,ensure_ascii=False,indent=2));print('details complete',len(results),flush=True)
