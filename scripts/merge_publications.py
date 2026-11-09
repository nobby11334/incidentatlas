"""Audit all publication records and merge proven copies, retaining source and date provenance.
An organization/date/title match alone is a review candidate, never a merge instruction.
Anonymous historical survey rows have no sufficient identity and remain separate.
"""
import collections,datetime,json,pathlib
from publication_identity import orgkey,urlkey
ROOT=pathlib.Path(__file__).resolve().parents[1]
read=lambda p:json.loads(p.read_text())
def apply():
 data=read(ROOT/'dist/data.json');ledger=read(ROOT/'dist/reconciliation.json');evidence=read(ROOT/'dist/primary-evidence.json')['urls'];rules=read(ROOT/'sources/publication-merges.json');byid={r['id']:r for r in data};parent={r['id']:r['id'] for r in data};reasons=[]
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 def union(a,b,reason):
  a,b=find(a),find(b)
  if a!=b:parent[b]=a;reasons.append(dict(ids=[a,b],reason=reason))
 for rule in rules:
  if rule['canonicalId'] not in byid:continue
  for old in rule['duplicateIds']:
   if old in byid:union(rule['canonicalId'],old,'個別本文確認済み：'+rule['reason'])
 indexed={}
 for r in data:
  if r.get('anonymous'):continue
  for _,u in r['sources']:
   keys=[('url',orgkey(r['org']),urlkey(u))];ev=evidence.get(u,{})
   # Byte-identical PDF mirrors are the same document. HTML home/error pages are excluded.
   if ev.get('status')=='retrieved' and ev.get('sha256') and 'pdf' in ev.get('contentType','').lower():keys.append(('pdf-sha256',orgkey(r['org']),ev['sha256']))
   for key in keys:
    if key in indexed:union(indexed[key],r['id'],'同一組織と'+('正規化URL一致' if key[0]=='url' else 'PDF SHA-256一致'))
    else:indexed[key]=r['id']
 groups=collections.defaultdict(list)
 for r in data:groups[find(r['id'])].append(r)
 aliases={};removed=[]
 forced={r['canonicalId'] for r in rules}
 for records in groups.values():
  if len(records)<2:continue
  # Prefer editorial records; otherwise keep the earliest indexed publication with stable ID.
  canonical=min(records,key=lambda r:(-1 if r['id'] in forced else 0 if r.get('reviewStage')=='curated' or not r['id'].startswith('pub-') else 1,r.get('published') or '9999',r['id']))
  others=[r for r in records if r['id']!=canonical['id']]
  for d in others:
   aliases[d['id']]=canonical['id'];removed.append(d['id'])
   snapshots=canonical.setdefault('mergedPublications',[])
   if d['id'] not in {s['id'] for s in snapshots}:snapshots.append(d)
  canonical['sources']=[list(x) for x in dict.fromkeys(tuple(s) for r in records for s in r['sources'])]
  canonical['discoverySources']=list(dict.fromkeys(u for r in records for u in r.get('discoverySources',[])))
  canonical['mergedRecordIds']=sorted(set(canonical.get('mergedRecordIds',[])+[r['id'] for r in others]))
  canonical['mergeChecked']=datetime.date.today().isoformat()
 data=[r for r in data if r['id'] not in aliases];byid={r['id']:r for r in data}
 # Remap all discovery inventories to canonical publications and link URL aliases.
 byurl=collections.defaultdict(set)
 for r in data:
  for _,u in r['sources']:byurl[(orgkey(r['org']),urlkey(u))].add(r['id'])
 for row in ledger['records']:
  for k in ('duplicateOfKey','discoveryAliases'):row.pop(k,None)
  ids={aliases.get(i,i) for i in row.get('recordIds',[])}
  for u in row.get('primaryUrls',[]):ids.update(byurl[(orgkey(row['organization']),urlkey(u))])
  if ids:
   if not row.get('recordIds'):row['result']='既存公表記録とURL照合（別表記を統合）'
   row['recordIds']=sorted(ids)
 # Explicitly reviewed index aliases retain their discovery rows, linked to the canonical record.
 for rule in rules:
  canonical=byid.get(rule['canonicalId'])
  if not canonical:continue
  for row in ledger['records']:
   if row['key'] in rule.get('discoveryKeys',[]):
    row['recordIds']=[canonical['id']];row['result']='索引の別名・再掲を当事者公表に個別照合';row['reviewNote']=rule.get('discoveryReason','')
    canonical['discoverySources']=list(dict.fromkeys(canonical.get('discoverySources',[])+[row['discovery']]))
 # Deduplicate unresolved index copies only by an explicit shared source URL and organization.
 pending={};pendingAliases=0
 for row in ledger['records']:
  if row.get('recordIds') or row['organization'].startswith('組織未特定'):continue
  keys=[(orgkey(row['organization']),urlkey(u)) for u in row.get('primaryUrls',[])] or [(orgkey(row['organization']),urlkey(row['discovery']))]
  target=next((pending[k] for k in keys if k in pending),None)
  if target:
   for k in keys:pending[k]=target
   row['duplicateOfKey']=target['key'];target.setdefault('discoveryAliases',[]).append(dict(key=row['key'],inventory=row['inventory'],url=row['discovery'],primaryUrls=row.get('primaryUrls',[])));pendingAliases+=1
  else:
   for k in keys:pending[k]=row
 # Same-title candidates require human review; generic PDF placeholder titles are included as warnings.
 suspicious=collections.defaultdict(list)
 for r in data:
  if not r.get('anonymous'):suspicious[(orgkey(r['org']),r.get('published',''),r['title'])].append(r)
 review=[dict(organization=rs[0]['org'],published=rs[0].get('published'),title=rs[0]['title'],recordIds=[r['id'] for r in rs],reason='同一組織・索引日・見出し。本文の同一性は未確認') for rs in suspicious.values() if len(rs)>1]
 oldAudit=read(ROOT/'dist/duplicate-audit.json') if (ROOT/'dist/duplicate-audit.json').exists() else {}
 history={tuple(sorted(x['recordIds'])):x for x in oldAudit.get('mergedGroups',[])}
 for rs in groups.values():
  if len(rs)>1:
   ids=[r['id'] for r in rs];canonical=next(aliases[i] for i in ids if i in aliases);history[tuple(sorted(ids))]=dict(organization=byid[canonical]['org'],canonicalId=canonical,recordIds=ids,reasons=[x['reason'] for x in reasons if set(x['ids'])&set(ids)])
 for rule in rules:
  if rule['canonicalId'] in byid:
   ids=[rule['canonicalId']]+rule['duplicateIds'];history.setdefault(tuple(sorted(ids)),dict(organization=rule['organization'],canonicalId=rule['canonicalId'],recordIds=ids,reasons=[rule['reason']]))
 manifest=read(ROOT/'dist/source-manifest.json');rows=ledger['records']
 manifest.update(linked=sum(bool(r.get('recordIds')) for r in rows),pending=sum(not r.get('recordIds') for r in rows),resultCounts=dict(collections.Counter(r['result'] for r in rows)))
 for item in manifest['sources']:
  rs=[r for r in rows if r['inventory']==item['name']];item.update(linked=sum(bool(r.get('recordIds')) for r in rs),pending=sum(not r.get('recordIds') for r in rs))
 for item in manifest['months']:
  rs=[r for r in rows if (r['published'][:7] or '日付未特定')==item['month']];item.update(linked=sum(bool(r.get('recordIds')) for r in rs),pending=sum(not r.get('recordIds') for r in rs))
 audit=dict(checked=datetime.date.today().isoformat(),publicRecords=len(data),removedThisRun=len(removed),pendingCopiesSuppressed=pendingAliases,mergedGroups=list(history.values()),reviewCandidates=review,anonymousRows='匿名調査個票は組織・事案の同定ができないため、実名資料との自動統合対象外。')
 for name,value in [('data.json',data),('reconciliation.json',ledger),('duplicate-audit.json',audit),('source-manifest.json',manifest)]:
  (ROOT/'dist'/name).write_text(json.dumps(value,ensure_ascii=False,separators=(',',':')))
 assert all(i in byid for row in ledger['records'] for i in row.get('recordIds',[]))
 for rule in rules:
  assert not any(r['id'] in rule['duplicateIds'] for r in data)
  assert set(rule['evidence']).issubset({u for r in data if r['id']==rule['canonicalId'] for _,u in r['sources']})
 print(json.dumps(dict(publicRecords=len(data),removed=len(removed),pendingCopiesSuppressed=pendingAliases,reviewCandidates=len(review)),ensure_ascii=False),flush=True)
if __name__=='__main__':apply()
