"""Coverage accounting, uncertainty and protected curated records."""
import pathlib,json,collections,re,sys
root=pathlib.Path(__file__).resolve().parents[1];read=lambda p:json.loads(p.read_text())
a=read(root/'dist/reconciliation.json')['records'];m=read(root/'dist/source-manifest.json');data=read(root/'dist/data.json');byid={d['id']:d for d in data}
assert len({x['key'] for x in a})==len(a)==m['discovered']==m['accounted']
assert m['complete'] is False
assert m['linked']+m['pending']==len(a)
assert sum(s['discovered'] for s in m['sources'])==len(a)
assert sum(s['pending'] for s in m['sources'])==m['pending']
assert sum(s['discovered'] for s in m['months'])==len(a)
assert all(x in byid for r in a for x in r.get('recordIds',[]))
assert all(d['id'] in {x for r in a for x in r.get('recordIds',[])} for d in data if d.get('collectionBatch')=='full-source-reconciliation')
for d in data:
 if d.get('collectionBatch')=='full-source-reconciliation':
  assert d['confirmed'] is d['potential'] is d['reportedCount'] is None
  assert d['date'] is None and d.get('loss') is None
  assert d['cia']==[] and d['verification']=='一次資料の機械照合・詳細精査前'
  assert re.fullmatch(r'\d{4}-\d{2}(?:-\d{2})?',d['published'])
  assert all(u.startswith(('https://','http://')) for label,u in d['sources'])
if len(sys.argv)>1:
 baseline=read(pathlib.Path(sys.argv[1]));assert all(byid[d['id']]==d for d in baseline),'Existing records were overwritten'
print(f'All {len(a)} discovery publications accounted for; linked {m["linked"]}, pending {m["pending"]}; unknowns and existing records preserved.')
