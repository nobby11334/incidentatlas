"""Account for every discovery item; only primary-body identity matches enter the dashboard.
No discovery-site prose or guessed incident dates/counts are imported. Curated data is immutable.
"""
import pathlib,json,re,hashlib,collections,datetime,sys
from lxml import html
ROOT=pathlib.Path(__file__).resolve().parents[1]
CACHE=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'source-cache/all-cache'
PRIMARY=pathlib.Path(sys.argv[2]) if len(sys.argv)>2 else CACHE/'primary'
ns={"__file__":str(ROOT/"scripts/import_october.py")};exec((ROOT/'scripts/import_october.py').read_text().split('raw=json.loads')[0],ns)
norm,orgkey,urlkey,sector,type_of=[ns[x] for x in ['norm','orgkey','urlkey','sector','type_of']]
from publication_identity import urlkey
checked=datetime.datetime.now(datetime.timezone.utc).date().isoformat()
read=lambda p:json.loads(p.read_text())
items=read(CACHE/'inventory.json');details={d['key']:d for d in read(CACHE/'details.json')}
# Per-URL files are atomic cache checkpoints and may be newer than the progress manifest.
statuses={u:{"url":u,**s} for u,s in read(ROOT/"dist/primary-evidence.json").get("urls",{}).items()} if (ROOT/"dist/primary-evidence.json").exists() else {}
for p in PRIMARY.glob('*.json'):
 try:
  s=read(p);statuses[s['url']]=s
 except (ValueError,KeyError):pass
records=read(ROOT/'dist/data.json');original={d['id']:json.dumps(d,sort_keys=True,ensure_ascii=False) for d in records}
byurl=collections.defaultdict(list)
for d in records:
 for label,u in d['sources']:byurl[urlkey(u)].append(d)
audit=[];added=0
for item in sorted(items,key=lambda d:d['key']):
 d=details.get(item['key'],item);org=d['org'];urls=d.get('primaryUrls',[]);a=dict(key=d['key'],organization=org,published=d.get('published',''),inventory=d['inventory'],discovery=d['discovery'],primaryUrls=urls,**{k:d[k] for k in ['dateBasis','identityBasis','indexCause','indexQuantity'] if k in d})
 matches={r['id'] for u in urls for r in byurl[urlkey(u)] if orgkey(org)==orgkey(r['org'])}
 if matches:a.update(result='既存公表記録と照合',recordIds=sorted(matches));audit.append(a);continue
 if not d.get('published') or not re.fullmatch(r'\d{4}-\d{2}(?:-\d{2})?',d['published']):a['result']='公表日確認待ち';audit.append(a);continue
 own=[]
 for u in urls:
  if 'github.com/piyokango/SecurityIncidentArchive/' in u:continue # discovery archive is not a primary statement
  st=statuses.get(u,{})
  if st.get('status')!='retrieved' or not st.get('textFile'):continue
  txt=PRIMARY/st['textFile']
  if not txt.exists():continue
  body=txt.read_text();identity=st.get('title','')+' '+body;binary=PRIMARY/st['textFile'].replace('.txt','.bin')
  if binary.exists() and 'html' in st.get('contentType',''):
   try:
    doc=html.fromstring(binary.read_bytes());identity+=' '+doc.text_content()+' '+' '.join(doc.xpath('//@alt'))
   except Exception:pass
  key=orgkey(org);identity=re.sub(r'[・、,。()（）/]','',norm(identity).lower())
  if len(key)>=3 and key in identity:own.append((u,body,st))
 if not own:a['result']='組織・一次資料本文の確認待ち';audit.append(a);continue
 body='\n'.join(x[1] for x in own)
 headings=' '.join(x[2].get('title','') for x in own)
 generic=re.search('プライバシー|個人情報保護方針|個人情報の取り扱い|漏えい防止|漏洩防止|セミナー|利用規約',headings)
 statement=re.search(r'(?:不正アクセス|サイバー攻撃|ランサムウェア|誤送信|紛失|漏えい|漏洩).{0,80}(?:発生|判明|確認|受け|可能性|おそれ|お詫び|お知らせ|ご報告)|(?:発生|判明|確認|お詫び|お知らせ).{0,80}(?:不正アクセス|誤送信|紛失|漏えい|漏洩)',norm(headings+' '+body[:12000]))
 if generic or not statement:
  a['result']='原資料の事案性の精査待ち';audit.append(a);continue
 # Keep announcements denying compromise and generic notices in the review queue.
 if re.search(r'(?:不正アクセス|情報漏[え洩]い).{0,15}(?:はありません|確認されていません|事実はない)',norm(body)) and not re.search('漏えいした|漏洩した|流出した|誤送信し|紛失し',norm(body)):
  a['result']='被害有無・否定表現の精査待ち';audit.append(a);continue
 title=next((re.split(r'\s*[|｜]\s*',s.get('title',''))[0].strip() for u,b,s in own if re.search('漏えい|漏洩|不正|紛失|誤|流出|ランサム|障害|ウイルス|サイバー',s.get('title',''))),'情報管理・セキュリティに関する公表')
 typ,method=type_of(body,title)
 identifier='pub-'+hashlib.sha256((orgkey(org)+'|'+min(urlkey(u) for u,b,s in own)).encode()).hexdigest()[:16]
 # URL + organization identify a publication, never an independent underlying incident.
 r=dict(id=identifier,org=org,title=title,published=d['published'],publicationKind=d.get('dateBasis') or d.get('releaseType') or '公表索引日（初報・続報は未分離）',date=None,asof=checked,checked=checked,sector=sector(org),type=typ,method=method,entry='侵入経路・原因の詳細は未精査',scope='影響範囲は未精査',cia=[],confirmed=None,potential=None,reportedCount=None,unit='件',status='本文取得・数量と被害有無は精査前',data='対象情報・対象外情報の区別は未精査。原資料をご確認ください。',impact='当事者本文と組織名を機械照合。被害有無・業務影響・復旧状況は精査前。',note='発見資料の要約は転載せず原資料本文を取得。日付は公表索引の記録で発生日ではありません。続報・関連公表・被害否定を含む可能性があり、独立事故数・確認済み漏えい件数には読み替えられません。分類は本文の語句による暫定値です。',sources=[['当事者公表資料',u] for u,b,s in own],anonymous=False,recordKind='当事者公表記録',collectionBatch='full-source-reconciliation',verification='一次資料の機械照合・詳細精査前',publicQuantities=[],discoverySources=[d['discovery']])
 records.append(r);added+=1
 for label,u in r['sources']:byurl[urlkey(u)].append(r)
 a.update(result='本文取得・組織照合済み／詳細精査前',recordIds=[identifier]);audit.append(a)
assert len({a['key'] for a in audit})==len(items)==len(audit)
assert len({r['id'] for r in records})==len(records)
assert all(original[r['id']]==json.dumps(r,sort_keys=True,ensure_ascii=False) for r in records if r['id'] in original)
counts=collections.Counter(a['result'] for a in audit);linked=sum(bool(a.get('recordIds')) for a in audit)
sources=[]
for name in sorted({d['inventory'] for d in items}):
 aa=[a for a in audit if a['inventory']==name];dates=[a['published'] for a in aa if a['published']]
 sources.append(dict(name=name,discovered=len(aa),accounted=len(aa),linked=sum(bool(a.get('recordIds')) for a in aa),pending=sum(not a.get('recordIds') for a in aa),first=min(dates) if dates else None,last=max(dates) if dates else None))
months=[]
for month in sorted({a['published'][:7] or '日付未特定' for a in audit}):
 aa=[a for a in audit if (a['published'][:7] or '日付未特定')==month];months.append(dict(month=month,discovered=len(aa),linked=sum(bool(a.get('recordIds')) for a in aa),pending=sum(not a.get('recordIds') for a in aa)))
manifest=dict(checked=checked,complete=False,completeness='国内の公表全体は母集団不明。下記の情報源の取得済み一覧内の照合状況。独立事故の網羅率ではありません。',discovered=len(items),accounted=len(audit),linked=linked,pending=len(audit)-linked,resultCounts=dict(counts),sources=sources,months=months,primaryRetrieval=dict(collections.Counter(statuses.get(u,{'status':'not_attempted'})['status'] for u in {u for d in details.values() for u in d.get('primaryUrls',[])})),sourceSnapshots=read(CACHE/'source-snapshots.json') if (CACHE/'source-snapshots.json').exists() else {'archiveSnapshot':'cc3cc93c1f191d7bc85a96883452ca176af6e705','checked':'2026-11-07','seoryDataVersion':'2026-11-07T02:20:01.255Z-296518a6404f'})
evidence={u:{k:v for k,v in statuses.get(u,{'status':'not_attempted'}).items() if k in ['status','sha256','checked','finalUrl','contentType','characters','error']} for u in sorted({u for d in details.values() for u in d.get('primaryUrls',[])})}
for name,value in [('primary-evidence.json',dict(checked=checked,urls=evidence)),('data.json',records),('source-manifest.json',manifest),('reconciliation.json',dict(checked=checked,records=audit))]:
 (ROOT/'dist'/name).write_text(json.dumps(value,ensure_ascii=False,separators=(',',':')))
print(json.dumps(dict(added=added,total=len(records),**{k:manifest[k] for k in ['discovered','linked','pending','resultCounts']}),ensure_ascii=False))
