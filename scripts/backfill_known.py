"""Retry every unresolved public primary URL from the durable discovery ledger.
Only identity-matched primary publications are added; existing editorial records are retained.
"""
import pathlib,json,subprocess,os,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[1];P=ROOT/'source-cache/all-cache';P.mkdir(parents=True,exist_ok=True)
read=lambda p:json.loads(p.read_text())
subprocess.run(['python','scripts/discover_more.py'],cwd=ROOT,check=True)
ledger=read(ROOT/'dist/reconciliation.json')['records'];items=[]
for r in ledger:
 items.append(dict(key=r['key'],org=r['organization'],published=r['published'],inventory=r['inventory'],discovery=r['discovery'],primaryUrls=r.get('primaryUrls',[]),**{k:r[k] for k in ['dateBasis','identityBasis','indexCause','indexQuantity'] if k in r}))
assert len(items)==len({x['key'] for x in items})
for name,value in [('inventory.json',items),('details.json',items),('details-complete.json',{'expected':len(items),'processed':len(items)})]:(P/name).write_text(json.dumps(value,ensure_ascii=False))
manifest=read(ROOT/'dist/source-manifest.json')
if manifest.get('sourceSnapshots'):(P/'source-snapshots.json').write_text(json.dumps(manifest['sourceSnapshots']))
targets=sorted({u for r in ledger if not r.get('recordIds') for u in r.get('primaryUrls',[])})
(P/'fetch-urls.json').write_text(json.dumps(targets));baseline=read(ROOT/'dist/data.json');(P/'baseline.json').write_text(json.dumps(baseline,ensure_ascii=False))
print('Known unresolved publications',sum(not r.get('recordIds') for r in ledger),'primary URLs to retry',len(targets),flush=True)
try:subprocess.run(['python','scripts/fetch_primary_sources.py'],cwd=ROOT,env={**os.environ,'INCIDENT_FETCH_URLS':str(P/'fetch-urls.json')},timeout=720,check=True)
except subprocess.TimeoutExpired:print('Retrieval budget reached; retaining completed checkpoints and all unresolved candidates.',flush=True)
subprocess.run(['python','scripts/reconcile_sources.py'],cwd=ROOT,check=True)
subprocess.run(['python','scripts/verify_sources.py',str(P/'baseline.json')],cwd=ROOT,check=True)
new=read(ROOT/'dist/data.json');print('Added public records',len(new)-len(baseline),flush=True)
