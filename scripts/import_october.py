import pathlib,json,re,hashlib,unicodedata,urllib.parse,collections
from lxml import html
ROOT=pathlib.Path(__file__).resolve().parents[1];BASE=ROOT/'source-cache/oct-cache';CHECKED='2026-11-07'
def norm(s):return re.sub(r'\s+','',unicodedata.normalize('NFKC',s or ''))
def orgkey(s):
 s=norm(s).lower();s=re.sub(r'のファイルサーバ.*','',s);s=re.split('[（(／/]',s)[0];s=re.sub('株式会社|有限会社|国立大学法人|公立大学法人|学校法人|一般社団法人|公益財団法人|独立行政法人|国立研究開発法人|合同会社','',s);return re.sub(r'[・、,。)）]','',s).removesuffix('ec')
def urlkey(u):
 p=urllib.parse.urlsplit(u);q=urllib.parse.parse_qsl(p.query);q=[(a,b) for a,b in q if not a.lower().startswith(('utm_','fbclid','gclid'))];return p.hostname.removeprefix('www.')+urllib.parse.unquote(p.path).rstrip('/')+('?' +urllib.parse.urlencode(q) if q else '')
def number(s):
 s=norm(s).replace(',','');m=re.search(r'(\d+(?:\.\d+)?)(億|万)?(\d+(?:\.\d+)?)?(万)?(\d+)?\s*(人|名|件|アカウント|社|台|通)',s)
 if not m:return None
 a,b,c,d,e,unit=m.groups();value=float(a)*({'億':1e8,'万':1e4,None:1}[b]);
 if c:value+=float(c)*(1e4 if d else 1)
 if e:value+=float(e)
 return int(value),unit
numrx=re.compile(r'[\d,]+(?:\.\d+)?(?:億|万)?(?:[\d,]+(?:\.\d+)?)?(?:万)?[\d,]*(?:人|名|件|アカウント|社|台|通)')
def sector(org):
 for pat,label in [('大学|学園|学校|教育委員会','教育・研究'),('病院|医療|クリニック|健康.*センター','医療'),('銀行|証券|保険|信用金庫|信金|信用組合','金融'),('旅客鉄道|急便|運輸|レンタカー|航空|物流','交通・物流'),('ホテル|旅館|リゾート|観光','旅行・宿泊')]:
  if re.search(pat,org):return label
 if re.search(r'(市|区|町|村|県|府|都)$|^(北海道|東京都|大阪府|京都府)|市役所|区役所|水道局|市立|県立|県警|道警|県庁',org):return '自治体'
 return '業種未分類'
def type_of(body,title):
 heading=norm(title);body=norm(body)
 candidates=[('ランサムウェア','外部攻撃'),('誤送信','操作ミス'),('誤送付','操作ミス'),('誤配付','操作ミス'),('誤交付','操作ミス'),('紛失','紛失'),('盗難','盗難'),('誤廃棄','管理ミス'),('設定ミス','設定ミス'),('設定不備','設定ミス'),('不正アクセス','外部攻撃'),('サイバー攻撃','外部攻撃'),('内部不正','内部不正'),('不正持ち出し','内部不正'),('不正利用','不明')]
 for token,label in candidates:
  if token in heading:return label,token
 # An index label is not evidence; only use an affirmative occurrence in the primary text.
 for token,label in candidates:
  matches=list(re.finditer(token,body))
  if any(not re.search('確認されていません|受けていません|ありません|ございません',body[m.end():m.end()+35]) for m in matches):return label,token
 return '不明','原因は資料の項目抽出では未特定'
raw=json.loads((BASE/'details.json').read_text());statuses=json.loads((BASE/'primary-status.json').read_text());groups=[];seen={};bydate={}
for item in sorted(raw,key=lambda d:(d['published'],d['org'],d['key'])):
 urls=item.get('primaryUrls',[]);keyorg=orgkey(item['org']);matches={seen[(keyorg,urlkey(u))] for u in urls if (keyorg,urlkey(u)) in seen}
 if (keyorg,item['published']) in bydate:matches.add(bydate[(keyorg,item['published'])])
 if matches:
  idx=min(matches);g=groups[idx]
  for other in sorted(matches-{idx}):
   g['items']+=groups[other]['items'];g['urls']+=groups[other]['urls'];groups[other]['items']=[]
   seen={k:(idx if v==other else v) for k,v in seen.items()};bydate={k:(idx if v==other else v) for k,v in bydate.items()}
  g['items'].append(item);g['urls']=list(dict.fromkeys(g['urls']+urls))
  for u in urls:seen[(keyorg,urlkey(u))]=idx
 else:
  idx=len(groups);groups.append({'org':item['org'],'items':[item],'urls':urls})
  for u in urls:seen[(keyorg,urlkey(u))]=idx
 bydate[(keyorg,item['published'])]=idx
groups=[g for g in groups if g['items']]
records=[];audit=[]
for g in groups:
 verified=[]
 for u in g['urls']:
  st=statuses.get(u,{})
  if st.get('status')=='retrieved':
   p=BASE/'primary'/st['textFile']
   if p.exists():verified.append((u,p.read_text(),st))
 if not verified:
  audit.append({'organization':g['org'],'discoveryUrls':[d['discovery'] for d in g['items']],'primaryUrls':g['urls'],'result':'本文確認待ち'});continue
 # Prefer sources that actually name this organization over third-party links listed on a discovery page.
 key=orgkey(g['org']);own=[]
 for u,body,st in verified:
  identity=st.get('title','')+' '+body
  binary=BASE/'primary'/st['textFile'].replace('.txt','.bin')
  if binary.exists() and 'html' in st.get('contentType',''):
   try:
    doc=html.fromstring(binary.read_bytes());identity+=' '+doc.text_content()+' '+' '.join(doc.xpath('//@alt'))
   except Exception:pass
  normalized=re.sub(r'[・、,。()（）/]', '', norm(identity).lower())
  if key and (key in normalized or (len(key)>8 and key[:8] in normalized) or any(len(part)>=5 and re.sub(r'[・、,。()（）/]', '',norm(part).lower()) in normalized for part in re.split(r'[ 　（(]',g['org']) if not re.search('株式会社|委託先|運営会社',part))):own.append((u,body,st))
 if own:verified=own
 else:
  audit.append({'organization':g['org'],'discoveryUrls':[d['discovery'] for d in g['items']],'primaryUrls':g['urls'],'result':'組織と原文の照合待ち'});continue
 combined='\n'.join(x[1] for x in verified);compact=norm(combined);org=g['org'];published=min(d['published'] for d in g['items'])
 title=next((re.split(r'\s*[|｜]\s*',st['title'])[0].strip() for u,b,st in verified if st.get('title') and re.search('漏えい|漏洩|不正|紛失|誤|流出|ランサム',st['title'])),None)
 typ,method=type_of(combined,title or '')
 # No prose from discovery sites is copied. Fields below are re-extracted from retrieved primary documents.
 info=[w for w in ['氏名','住所','電話番号','メールアドレス','生年月日','パスワード','口座番号','クレジットカード','マイナンバー','健康情報','診療情報','従業員情報'] if w in compact]
 data='原文に登場する情報項目：'+ '、'.join(info)+'。対象／対象外の別は各出典参照。' if info else '対象情報の項目は本版では未特定。'
 scope='委託先・外部サービス' if re.search('委託先|再委託|外部サービス|提供元|提供事業者',combined) else '自社・自組織（範囲未分離）'
 vectors=[(r'ランサムウェア','ランサムウェア'),(r'SQLインジェクション','SQLインジェクション'),(r'フィッシング','フィッシング'),(r'認証情報|資格情報','認証情報の不正利用等'),(r'脆弱性','脆弱性の悪用等'),(r'キャッシュ.*設定','キャッシュ設定'),(r'BCC|ＢＣＣ','メール宛先設定')]
 entry=next((label for pat,label in vectors if re.search(pat,combined)),method)
 expected=[]
 for item in g['items']:
  for row in item.get('expectedNumbers',[]):
   if len(row)==3:expected.append((row[0],row[1],row[2]))
  rawcount=item.get('expected',{}).get('件数','')
  if rawcount and '発表に記載なし' not in rawcount:
   for token in re.split(r'[、,](?=[^\d])',rawcount):expected.append(('公表資料の対象規模',token,'未分離'))
 primary_numbers=[]
 for m in numrx.finditer(compact):
  z=number(m.group())
  if z:primary_numbers.append((z,m.start(),m.group()))
 quantities=[];qseen=set()
 for label,rawvalue,certainty in expected:
  z=number(rawvalue)
  if not z:continue
  value,_=z
  found=[(unit,pos,rawnum) for (v,unit),pos,rawnum in primary_numbers if v==value]
  if not found:continue
  # Preserve the unit found in the original, not a normalized unit on an index.
  unit,pos,rawnum=found[0]
  if (value,unit,label) in qseen:continue
  qseen.add((value,unit,label));quantities.append({'value':value,'unit':unit,'label':{'人':'人数（対象・内数は未分離）','名':'人数（対象・内数は未分離）','件':'件数（定義は原資料参照）','アカウント':'アカウント数','社':'影響組織数等','台':'端末・媒体数等','通':'送受信メール数等'}.get(unit,'原文の数量'),'certainty':'確認状況は原資料参照','sourceValue':rawnum,'kind':'mail' if re.search('メール.*送信|なりすましメール|不審メール|送信.*メール|受信',label) or unit=='通' else 'organizations' if re.search('医療機関|利用企業|施設数',label) or unit=='社' else 'subset' if re.search('うち|退職|別のお客様.*表示',label) else 'scope'})
 quantities=list({(q['value'],q['unit']):q for q in quantities}.values())
 leakq=[q for q in quantities if q['unit'] in ['人','名','件','アカウント'] and q['kind']=='scope' and not re.search('退職|職員のみ|従業員のみ|不正.*メール|メール.*送信|受信|表示され.*別|下記|うち|影響.*利用企業',q['label'])]
 values={(q['value'],q['unit']) for q in leakq};reported,unit=next(iter(values)) if len(values)==1 else (None,'件')
 # Automatic matching does not establish whether a number is confirmed exfiltration or a possible scope.
 if not title:title={'外部攻撃':'不正アクセス・サイバー攻撃に関する公表','操作ミス':'誤送信・誤送付等に関する公表','設定ミス':'設定不備に関する公表','紛失':'媒体・資料の紛失に関する公表','盗難':'盗難に関する公表'}.get(typ,'情報管理・セキュリティ事案に関する公表')
 identifier='oct26-'+hashlib.sha256((key+'|'+min(urlkey(u) for u,b,st in verified)).encode()).hexdigest()[:12]
 relationship=[]
 for token,groupid in [('アルカディア','arcadia-raiden-2026'),('アララ','arara-message-2026'),('Securitize','securitize-2026'),('スカラ','scala-iask-2026'),('Studio','studio-forms-2026'),('IDCフロンティア','idcf-2026'),('コミューン','commune-2026'),('TEMAIRAZU','temairazu-2026')]:
  if token in combined:relationship.append(groupid)
 r=dict(id=identifier,org=org,title=title,published=published,publicationKind='公表索引日（初報・続報の別は未分離）',date=None,asof=CHECKED,checked=CHECKED,sector=sector(org),type=typ,method=method,entry=entry,scope=scope,cia=['機密性'],confirmed=None,potential=None,reportedCount=reported,unit=unit,status='公表対象規模・確認状況未分離' if reported is not None else '公表本文確認・規模未分離',data=data,impact='当事者の公表本文を取得。業務影響・復旧状況の詳細は原資料参照。',note='一次資料の本文取得と項目の機械照合を実施。日付は月次索引の公表記録日で初報とは限りません。数量は本文に同値がある項目のみ採用し、実流出確認・対象範囲・内数を未分離のものは確認済み欄へ算入していません。関連する提供元事故や他の影響先との重複は未統合。',sources=[['当事者公表資料',u] for u,b,st in verified],anonymous=False,recordKind='当事者公表記録',collectionBatch='2026-10-reconciliation',verification='一次資料の機械照合・詳細精査前',publicQuantities=quantities,relatedIncidentGroups=relationship,discoverySources=[d['discovery'] for d in g['items']])
 records.append(r);audit.append({'id':identifier,'organization':org,'discoveryUrls':r['discoverySources'],'primaryUrls':g['urls'],'retrievedPrimaryUrls':[u for u,b,st in verified],'result':'本文取得・機械照合済み'})
# Preserve existing curated records and attach new references instead of adding duplicate October records.
base=json.loads((ROOT/'dist/data.json').read_text());base=[d for d in base if d.get('collectionBatch')!='2026-10-reconciliation'];added=[];merged=[]
for r in records:
 matches=[d for d in base if d['published'].startswith('2026-10') and (orgkey(d['org'])==orgkey(r['org']) or {urlkey(s[1]) for s in d['sources']} & {urlkey(s[1]) for s in r['sources']})]
 if matches:
  d=matches[0];d['sources']=list({u:label for label,u in d['sources']+r['sources']}.items());d['sources']=[[label,u] for u,label in d['sources']];merged.append({'new':r['id'],'existing':d['id']});continue
 added.append(r)
output=base+added
(ROOT/'dist/data.json').write_text(json.dumps(output,ensure_ascii=False,indent=2))
audit_doc={'month':'2026-10','checked':CHECKED,'discoveryRecords':len(raw),'discoveryPagesExpected':922,'discoveryGroupsAfterUrlOrgMatch':len(groups),'addedRecords':len(added),'mergedIntoExisting':merged,'recordsWithRetrievedPrimary':len(records),'pendingGroups':sum(x['result']!='本文取得・機械照合済み' for x in audit),'method':'月次索引は発見にのみ利用。要約は転載せず当事者原文を取得し項目を機械照合。公表記録と独立事故数を区別。本文到達は事実認定の保証ではなく精査前。','discoveryIndexes':['https://incidents.seory.co.jp/monthly/2026-10/','https://radineer.asia/cyber/month/2026-10/'],'primaryRetrievalSummary':dict(collections.Counter(v['status'] for v in statuses.values())),'records':audit}
(ROOT/'dist/october-2026-audit.json').write_text(json.dumps(audit_doc,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in audit_doc.items() if k not in ['records','method']},ensure_ascii=False));print('total',len(output),'classified',dict(collections.Counter(d['type'] for d in added)),'withNumbers',sum(bool(d['publicQuantities']) for d in added))
