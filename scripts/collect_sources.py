"""Refresh discovery metadata across all dates. Never republish third-party summaries.
Requires a read-only clone of piyokango/SecurityIncidentArchive as first argument.
"""
import pathlib,json,re,hashlib,urllib.request,urllib.parse,sys,datetime,concurrent.futures,threading,subprocess
from lxml import html
ROOT=pathlib.Path(__file__).resolve().parents[1];P=ROOT/'source-cache/all-cache';P.mkdir(parents=True,exist_ok=True)
archive=pathlib.Path(sys.argv[1]);items={}
def get(url):
 req=urllib.request.Request(url,headers={'User-Agent':'IncidentAtlas-public-source-verification/1.0'})
 with urllib.request.urlopen(req,timeout=30) as r:return r.read(12000000)
def text(el):return re.sub(r'\s+',' ',el.text_content()).strip()
for f in archive.glob('20??/??/*.md'):
 rel=str(f.relative_to(archive));head=re.split(r'\n# ',f.read_text(),maxsplit=1)[0];bullets=re.findall(r'^\s*[-*]\s+(.+)',head,re.M)
 if len(bullets)<4:continue
 m=re.search(r'(\d{4})年(\d{1,2})月(?:(\d{1,2})日)?',bullets[1]);date=f'{m[1]}-{int(m[2]):02d}'+(f'-{int(m[3]):02d}' if m[3] else '') if m else rel[:7].replace('/','-')
 key='a-'+hashlib.sha256(rel.encode()).hexdigest()[:16];items[key]=dict(key=key,org=bullets[2],published=date,primaryUrls=re.findall(r'https?://[^\s)<>]+',head),discovery='https://github.com/piyokango/SecurityIncidentArchive/blob/main/'+urllib.parse.quote(rel),inventory='SecurityIncidentArchive',releaseType='公表索引日・初報続報未分離')
s=json.loads(get('https://incidents.seory.co.jp/incidents.json'))
for d in s['incidents']:
 key='s-'+d['id'];items[key]=dict(key=key,org=d['organization']['name'],published=d['dates'].get('first_published') or '',discovery=d['url'],inventory='Seory')
r=html.fromstring(get('https://radineer.asia/cyber/'))
for tr in r.xpath('//tbody[@id="records"]/tr'):
 a=tr.xpath('.//td[contains(@class,"c-org")]/a')[0];key='r-'+tr.get('data-id');dates=tr.xpath('.//time/@datetime');items[key]=dict(key=key,org=text(a),published=dates[0] if dates else '',discovery=urllib.parse.urljoin('https://radineer.asia',a.get('href')),inventory='Radineer')
# Retain disappeared listings as unresolved historical discovery evidence.
oldpath=ROOT/'dist/reconciliation.json'
if oldpath.exists():
 for d in json.loads(oldpath.read_text())['records']:
  if d['key'] not in items:items[d['key']]=dict(key=d['key'],org=d['organization'],published=d['published'],discovery=d['discovery'],primaryUrls=d['primaryUrls'],inventory=d['inventory'],removedFromCurrentIndex=True)
(P/'source-snapshots.json').write_text(json.dumps({'archiveSnapshot':subprocess.check_output(['git','rev-parse','HEAD'],cwd=archive,text=True).strip(),'seoryDataVersion':s.get('data_version'),'checked':datetime.datetime.now(datetime.timezone.utc).isoformat()}))
(P/'inventory.json').write_text(json.dumps(list(items.values()),ensure_ascii=False))
locks={};guard=threading.Lock()
def detail(d):
 if d['key'].startswith('a-') or d.get('removedFromCurrentIndex'):return d
 host=urllib.parse.urlsplit(d['discovery']).hostname
 with guard:sem=locks.setdefault(host,threading.Semaphore(4))
 try:
  with sem:raw=get(d['discovery'])
  doc=html.fromstring(raw);d=dict(d)
  if d['key'].startswith('s-'):urls=doc.xpath('//ol[contains(@class,"ii-sources")]//a[contains(@class,"ii-ext")]/@href')
  else:
   urls=doc.xpath('//aside[contains(@class,"sources")]/ol/li/a/@href')
   if not d['published']:
    m=re.search(r'初回公表\s*(\d{4}-\d{2}-\d{2})',' '.join(doc.xpath('//p[@class="dates"]/text()')))
    if m:d['published']=m[1]
  d['primaryUrls']=list(dict.fromkeys(u for u in urls if u.startswith(('https://','http://'))));return d
 except Exception as e:return {**d,'detailError':str(e)}
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
 for d in pool.map(detail,items.values()):results.append(d)
(P/'details.json').write_text(json.dumps(results,ensure_ascii=False));(P/'details-complete.json').write_text(json.dumps({'expected':len(items),'processed':len(results)}));print('discovered',len(items))
