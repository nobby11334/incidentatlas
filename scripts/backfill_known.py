"""Retry every unresolved public primary URL from the durable discovery ledger.
Only identity-matched primary publications are added; existing editorial records are retained.
"""
import pathlib,json,subprocess,os,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[1];P=ROOT/'source-cache/all-cache';P.mkdir(parents=True,exist_ok=True)
read=lambda p:json.loads(p.read_text())
subprocess.run(['python','scripts/apply_reviewed_updates.py'],cwd=ROOT,check=True)
subprocess.run(['python','scripts/refresh_indexes.py'],cwd=ROOT,check=True)
subprocess.run(['python','scripts/merge_publications.py'],cwd=ROOT,check=True)
subprocess.run(['python','scripts/discover_more.py'],cwd=ROOT,check=True)
ledger=read(ROOT/'dist/reconciliation.json')['records'];items=[]
for r in ledger:
 items.append(dict(key=r['key'],org=r['organization'],published=r['published'],inventory=r['inventory'],discovery=r['discovery'],primaryUrls=r.get('primaryUrls',[]),**{k:r[k] for k in ['dateBasis','identityBasis','indexCause','indexQuantity'] if k in r}))
assert len(items)==len({x['key'] for x in items})
for name,value in [('inventory.json',items),('details.json',items),('details-complete.json',{'expected':len(items),'processed':len(items)})]:(P/name).write_text(json.dumps(value,ensure_ascii=False))
manifest=read(ROOT/'dist/source-manifest.json')
if manifest.get('sourceSnapshots') and not (P/'source-snapshots.json').exists():(P/'source-snapshots.json').write_text(json.dumps(manifest['sourceSnapshots']))
targets=sorted({u for r in ledger for u in r.get('primaryUrls',[])})
(P/'fetch-urls.json').write_text(json.dumps(targets));(P/'ledger-baseline.json').write_text(json.dumps(read(ROOT/'dist/reconciliation.json'),ensure_ascii=False));baseline=read(ROOT/'dist/data.json');(P/'baseline.json').write_text(json.dumps(baseline,ensure_ascii=False))
print('Known unresolved publications',sum(not r.get('recordIds') for r in ledger),'primary URLs to retry',len(targets),flush=True)
try:subprocess.run(['python','scripts/fetch_primary_sources.py'],cwd=ROOT,env={**os.environ,'INCIDENT_FETCH_URLS':str(P/'fetch-urls.json')},timeout=720,check=True)
except subprocess.TimeoutExpired:print('Retrieval budget reached; retaining completed checkpoints and all unresolved candidates.',flush=True)
old_evidence=read(ROOT/'dist/primary-evidence.json')['urls']
subprocess.run(['python','scripts/reconcile_sources.py'],cwd=ROOT,check=True)
current_evidence=read(ROOT/'dist/primary-evidence.json')['urls']
changes=[dict(url=u,previousSha256=old_evidence[u].get('sha256'),currentSha256=e.get('sha256'),checked=e.get('checked'),status='本文変更・続報精査待ち') for u,e in current_evidence.items() if u in old_evidence and e.get('sha256') and old_evidence[u].get('sha256') and e['sha256']!=old_evidence[u]['sha256']]
change_path=ROOT/'dist/source-changes.json'
prior=read(change_path) if change_path.exists() else {'changes':[]}
seen={(x['url'],x.get('currentSha256')) for x in prior['changes']}
prior['changes'] += [x for x in changes if (x['url'],x['currentSha256']) not in seen]
change_path.write_text(json.dumps(prior,ensure_ascii=False,separators=(',',':')))
print('Changed primary documents queued for review',len(changes),flush=True)
subprocess.run(['python','scripts/verify_sources.py',str(P/'baseline.json')],cwd=ROOT,check=True)
subprocess.run(['python','scripts/merge_publications.py'],cwd=ROOT,check=True)
subprocess.run(['python','scripts/verify_duplicates.py'],cwd=ROOT,check=True)
new=read(ROOT/'dist/data.json');print('Added public records',len(new)-len(baseline),flush=True)

subprocess.run(['python','scripts/prepare_backfill_commit.py'],cwd=ROOT,check=True)
